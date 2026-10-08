import math

import structlog
from sqlalchemy import bindparam, create_engine, text

from app.core.runtime_secrets import StartupError
from app.services.citations import DocumentCitations

MAX_TOP_K = 20
logger = structlog.get_logger("vector_store")
MAX_COSINE_DISTANCE = 2.0


class EmbeddingDimensionMismatch(StartupError):
    """The stored vectors cannot be compared with the vectors of the configured provider."""

    def __init__(self):
        super().__init__(
            "The stored embeddings have a different dimension than the configured provider; "
            "re-index the corpus into a new collection before starting the backend."
        )


class PgVectorQueryStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)

    def search_chunks(
        self, tenant_id: str, query_embedding: list[float], top_k: int = 4, max_distance: float | None = None,
        provider: str | None = None,
    ) -> list[dict]:
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= MAX_TOP_K:
            raise ValueError(f"top_k must be an integer between 1 and {MAX_TOP_K}")
        if max_distance is not None and (
            isinstance(max_distance, bool) or not isinstance(max_distance, (int, float))
            or not math.isfinite(max_distance) or not 0 < max_distance <= MAX_COSINE_DISTANCE
        ):
            raise ValueError("max_distance must be greater than 0 and at most 2")
        vector = "[" + ",".join(f"{value:.6f}" for value in query_embedding) + "]"
        threshold = "WHERE distance <= :max_distance" if max_distance is not None else ""
        provider_filter = "AND ce.provider = :provider" if provider is not None else ""
        parameters = {"tenant_id": tenant_id, "query_embedding": vector, "top_k": top_k}
        if provider is not None:
            parameters["provider"] = provider
        if max_distance is not None:
            parameters["max_distance"] = float(max_distance)
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
            rows = connection.execute(
                text(
                    f"""
                    SELECT chunk_id, document_id, tenant_id, chunk_index, source, content, distance
                    FROM (
                        SELECT
                            dc.id AS chunk_id,
                            kd.id AS document_id,
                            kd.tenant_id AS tenant_id,
                            dc.chunk_index AS chunk_index,
                            kd.source AS source,
                            dc.content AS content,
                            (ce.embedding <=> CAST(:query_embedding AS vector)) AS distance
                        FROM knowledge_documents kd
                        JOIN document_chunks dc ON dc.document_id = kd.id
                        JOIN chunk_embeddings ce ON ce.chunk_id = dc.id
                        WHERE kd.tenant_id = :tenant_id
                        {provider_filter}
                    ) ranked
                    {threshold}
                    ORDER BY distance, chunk_id
                    LIMIT :top_k
                    """
                ),
                parameters,
            ).all()
            if not rows:
                return []
            # Fetch each source document once, scoped to the same tenant and
            # transaction snapshot as retrieval (including concurrent reingestion).
            documents = connection.execute(
                text("""
                    SELECT id, text_content FROM knowledge_documents
                    WHERE tenant_id = :tenant_id AND id IN :document_ids
                """).bindparams(bindparam("document_ids", expanding=True)),
                {"tenant_id": tenant_id, "document_ids": list({row.document_id for row in rows})},
            )
            locations = {row.id: DocumentCitations(row.text_content) for row in documents}
            return [
                {
                    "chunk_id": row.chunk_id,
                    "document_id": row.document_id,
                    "tenant_id": row.tenant_id,
                    "title": locations[row.document_id].title or row.source.strip(),
                    "chunk_index": row.chunk_index,
                    "section": locations[row.document_id].section(row.content),
                    "source": row.source,
                    "content": row.content,
                    "distance": float(row.distance),
                }
                for row in rows
            ]

    def embedding_column_dimension(self) -> int | None:
        """Dimension declared by chunk_embeddings.embedding, or None while the table does not exist yet."""
        with self.engine.connect() as connection:
            value = connection.execute(text(
                "SELECT atttypmod FROM pg_attribute "
                "WHERE attrelid = to_regclass('chunk_embeddings') AND attname = 'embedding'"
            )).scalar()
        return value if isinstance(value, int) and value > 0 else None

    def verify_dimension(self, expected: int) -> None:
        try:
            column = self.embedding_column_dimension()
        except Exception:
            logger.warning("embedding_dimension_check_skipped", reason="query_failed")
            return
        if column is None:
            logger.info("embedding_dimension_check_skipped", reason="table_missing")
            return
        if column != expected:
            raise EmbeddingDimensionMismatch()

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def close(self) -> None:
        self.engine.dispose()
