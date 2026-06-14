from datetime import datetime, timezone

from sqlalchemy import create_engine, text


class PgVectorStore:
    def __init__(self, database_url: str, embedding_dimension: int):
        self.database_url = database_url
        self.embedding_dimension = embedding_dimension
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)
        self.store_name = "pgvector"

    def initialize(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS knowledge_documents (
                        id TEXT PRIMARY KEY,
                        job_id TEXT UNIQUE NOT NULL,
                        tenant_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        artifact_uri TEXT,
                        text_content TEXT NOT NULL,
                        chunk_count INTEGER NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS document_chunks (
                        id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                        chunk_index INTEGER NOT NULL,
                        content TEXT NOT NULL,
                        char_count INTEGER NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL,
                        UNIQUE (document_id, chunk_index)
                    )
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS chunk_embeddings (
                        id TEXT PRIMARY KEY,
                        chunk_id TEXT UNIQUE NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
                        embedding vector({self.embedding_dimension}) NOT NULL,
                        dimension INTEGER NOT NULL,
                        provider TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
            )

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def store_document(
        self,
        *,
        job_id: str,
        tenant_id: str,
        source: str,
        artifact_uri: str | None,
        text_content: str,
        chunks: list[str],
        embeddings: list[list[float]],
        provider_name: str,
    ) -> dict:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        now = datetime.now(timezone.utc)
        document_id = job_id

        with self.engine.begin() as connection:
            connection.execute(
                text("DELETE FROM knowledge_documents WHERE id = :document_id"),
                {"document_id": document_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO knowledge_documents (
                        id, job_id, tenant_id, source, artifact_uri, text_content, chunk_count, created_at, updated_at
                    ) VALUES (
                        :id, :job_id, :tenant_id, :source, :artifact_uri, :text_content, :chunk_count, :created_at, :updated_at
                    )
                    """
                ),
                {
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

            for index, chunk in enumerate(chunks):
                embedding = embeddings[index]
                chunk_id = f"{document_id}:chunk:{index}"
                embedding_id = f"{chunk_id}:embedding"
                connection.execute(
                    text(
                        """
                        INSERT INTO document_chunks (
                            id, document_id, chunk_index, content, char_count, created_at
                        ) VALUES (
                            :id, :document_id, :chunk_index, :content, :char_count, :created_at
                        )
                        """
                    ),
                    {
                        "id": chunk_id,
                        "document_id": document_id,
                        "chunk_index": index,
                        "content": chunk,
                        "char_count": len(chunk),
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

        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "embedding_count": len(embeddings),
            "vector_store": self.store_name,
            "provider": provider_name,
        }

    def close(self) -> None:
        self.engine.dispose()

    @staticmethod
    def _format_vector(values: list[float]) -> str:
        return "[" + ",".join(f"{value:.6f}" for value in values) + "]"
