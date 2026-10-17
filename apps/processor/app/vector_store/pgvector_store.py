from datetime import datetime, timezone
from pathlib import Path
import json
import uuid
import math

from sqlalchemy import create_engine, text

from app.core.runtime_secrets import StartupError
from app.db.migration_runner import MigrationRunner


_UNGUARDED = object()


class StalePublication(RuntimeError):
    """A newer complete version was published while this operation was preparing."""


class PgVectorStore:
    def __init__(self, database_url: str, embedding_dimension: int):
        if embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be greater than zero")
        self.database_url = database_url
        self.embedding_dimension = embedding_dimension
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)
        self.store_name = "pgvector"

    def initialize(self) -> None:
        runner = MigrationRunner(
            self.engine,
            "app.vector_store.migrations",
            Path(__file__).with_name("migrations"),
            version_table="vector_schema_migrations",
            migration_kwargs={"001": {"embedding_dimension": self.embedding_dimension}},
        )
        runner.run()
        with self.engine.connect() as connection:
            dimension = connection.execute(text("""
                SELECT atttypmod FROM pg_attribute
                WHERE attrelid = 'chunk_embeddings'::regclass
                  AND attname = 'embedding' AND NOT attisdropped
            """)).scalar_one()
        if dimension != self.embedding_dimension:
            raise StartupError(
                "Configured embedding dimension differs from the stored vector schema; "
                "restore the matching configuration or reindex into a new database."
            )

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def publication(self, document_id: str, tenant_id: str) -> str | None:
        with self.engine.connect() as connection:
            row = connection.execute(text('SELECT tenant_id, metadata FROM knowledge_documents WHERE id=:id'),
                                     {'id':document_id}).first()
        if row is None:
            return None
        if row.tenant_id != tenant_id:
            raise PermissionError('Document read rejected.')
        return (row.metadata or {}).get('publication_id', 'legacy')

    def store_document(
        self,
        *,
        job_id: str,
        tenant_id: str,
        source: str,
        artifact_uri: str | None,
        text_content: str,
        chunks: list[str] | list[dict],
        embeddings: list[list[float]],
        provider_name: str,
        document_metadata: dict | None = None,
        expected_publication=_UNGUARDED,
        prepared_index=None,
    ) -> dict:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if any(len(embedding) != self.embedding_dimension for embedding in embeddings):
            raise ValueError("Every embedding must match the configured dimension")

        if any(any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v)
                   for v in vector) for vector in embeddings):
            raise ValueError('Embeddings must contain finite numbers')
        structured = document_metadata is not None
        if structured:
            manifest = document_metadata.get('chunking', {})
            generation = manifest.get('fingerprint')
            if not generation or manifest.get('chunk_count') != len(chunks):
                raise ValueError('Invalid document chunking manifest')
            for index, chunk in enumerate(chunks):
                from app.embeddings.contracts import chunk_identity
                if (not isinstance(chunk, dict) or chunk.get('document_id') != job_id
                        or chunk.get('chunk_index') != index
                        or chunk.get('chunk_id') != chunk_identity(job_id, generation, index)
                        or chunk.get('metadata', {}).get('chunking_fingerprint') != generation):
                    raise ValueError('Mixed or incomplete chunk generation')
        elif any(not isinstance(chunk, str) for chunk in chunks):
            raise ValueError('Structured chunks require their parent manifest')
        metadata = dict(document_metadata or {})
        metadata['publication_id'] = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        document_id = job_id

        with self.engine.begin() as connection:
            from app.vector_store.generations import lock_head
            index_head = lock_head(connection, tenant_id)
            if index_head['generation_id'] is not None and prepared_index is None:
                raise StalePublication('An active verified generation requires a prepared index publication')
            if prepared_index is not None and (index_head['generation_id'] != prepared_index['generation_id']
                    or index_head['version'] != prepared_index['version']):
                raise StalePublication('The active verified generation changed during preparation')
            # A placeholder insert serializes simultaneous first publications too.
            inserted = connection.execute(text("""INSERT INTO knowledge_documents
                (id,job_id,tenant_id,source,text_content,chunk_count,created_at,updated_at)
                VALUES(:id,:id,:tenant,:source,'',0,:now,:now) ON CONFLICT(id) DO NOTHING"""),
                {'id':document_id,'tenant':tenant_id,'source':source,'now':now}).rowcount == 1
            prior = connection.execute(text('SELECT tenant_id, job_id, metadata FROM knowledge_documents WHERE id=:id FOR UPDATE'),
                                       {'id':document_id}).first()
            if prior.tenant_id != tenant_id or prior.job_id != job_id:
                raise PermissionError('Document write rejected.')
            previous_metadata = prior.metadata or {}
            previous = previous_metadata.get('publication_id')
            if previous is None:
                previous = None if inserted else 'legacy'
            if expected_publication is not _UNGUARDED and previous != expected_publication:
                raise StalePublication('A newer document publication already exists')
            # The conditional upsert locks ownership, including concurrent retries.
            saved = connection.execute(
                text(
                    """
                    INSERT INTO knowledge_documents (
                        id, job_id, tenant_id, source, artifact_uri, text_content, chunk_count, created_at, updated_at, metadata
                    ) VALUES (
                        :id, :job_id, :tenant_id, :source, :artifact_uri, :text_content, :chunk_count, :created_at, :updated_at, CAST(:metadata AS jsonb)
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        source = excluded.source,
                        artifact_uri = excluded.artifact_uri,
                        text_content = excluded.text_content,
                        chunk_count = excluded.chunk_count,
                        updated_at = excluded.updated_at,
                        metadata = excluded.metadata
                    WHERE knowledge_documents.tenant_id = excluded.tenant_id
                      AND knowledge_documents.job_id = excluded.job_id
                    """
                ),
                {
                    "metadata": json.dumps(metadata, ensure_ascii=False),
                    "id": document_id,
                    "job_id": job_id,
                    "tenant_id": tenant_id,
                    "source": source,
                    "artifact_uri": artifact_uri,
                    "text_content": text_content,
                    "chunk_count": len(chunks),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            if saved.rowcount != 1:
                raise PermissionError("Document write rejected.")
            connection.execute(
                text("""
                    DELETE FROM document_chunks WHERE document_id = :document_id
                    AND EXISTS (
                        SELECT 1 FROM knowledge_documents
                        WHERE id = :document_id AND tenant_id = :tenant_id AND job_id = :job_id
                    )
                """),
                {"document_id": document_id, "tenant_id": tenant_id, "job_id": job_id},
            )

            for index, chunk in enumerate(chunks):
                embedding = embeddings[index]
                content = chunk['content'] if structured else chunk
                chunk_metadata = chunk['metadata'] if structured else {}
                chunk_id = chunk['chunk_id'] if structured else f"{document_id}:chunk:{index}"
                embedding_id = f"{chunk_id}:embedding"
                connection.execute(
                    text(
                        """
                        INSERT INTO document_chunks (
                            id, document_id, chunk_index, content, char_count, created_at, metadata
                        ) VALUES (
                            :id, :document_id, :chunk_index, :content, :char_count, :created_at, CAST(:metadata AS jsonb)
                        )
                        """
                    ),
                    {
                        "id": chunk_id,
                        "document_id": document_id,
                        "chunk_index": index,
                        "content": content,
                        "char_count": len(content),
                        "metadata": json.dumps(chunk_metadata, ensure_ascii=False),
                        "created_at": now,
                    },
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO chunk_embeddings (
                            id, chunk_id, embedding, dimension, provider, created_at
                        ) VALUES (
                            :id, :chunk_id, CAST(:embedding AS vector), :dimension, :provider, :created_at
                        )
                        """
                    ),
                    {
                        "id": embedding_id,
                        "chunk_id": chunk_id,
                        "embedding": self._format_vector(embedding),
                        "dimension": len(embedding),
                        "provider": provider_name,
                        "created_at": now,
                    },
                )

            index_generation = None
            if index_head['generation_id'] is not None:
                from app.vector_store.generations import GenerationStore, publication_chunks
                index_generation = GenerationStore(self.engine).publish_prepared(connection, tenant_id, index_head,
                    {'tenant_id': tenant_id, 'id': document_id, 'source': source, 'content': text_content,
                     'metadata': metadata, 'publication_id': metadata['publication_id']},
                    publication_chunks(document_id, chunks), prepared_index)
            connection.execute(text('UPDATE tenant_rag_head SET catalog_revision=catalog_revision+1 WHERE tenant_id=:tenant'),
                               {'tenant': tenant_id})

        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "embedding_count": len(embeddings),
            "vector_store": self.store_name,
            "provider": provider_name,
            "publication_id": metadata["publication_id"],
            "index_generation_id": index_generation,
        }

    def prepare_index_publication(self, *, tenant_id, job_id, source, text_content, chunks, document_metadata, provider):
        from app.embeddings.tokenization import EmbeddingTokenCounter
        from app.vector_store.generations import GenerationStore
        # Lazy resource load preserves the legacy/mock path until an index is active.
        store = GenerationStore(self.engine)
        if store.active_plan(tenant_id)['generation_id'] is None:
            return None
        store.counter = EmbeddingTokenCounter()
        return store.prepare_publication(tenant_id, job_id, source, text_content, chunks, document_metadata, provider)

    def close(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _format_vector(values: list[float]) -> str:
        return "[" + ",".join(f"{value:.6f}" for value in values) + "]"
