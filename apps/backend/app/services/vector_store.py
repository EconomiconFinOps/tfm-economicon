from sqlalchemy import create_engine, text


class PgVectorQueryStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)

    def search_chunks(self, tenant_id: str, query_embedding: list[float], top_k: int = 4) -> list[dict]:
        vector = "[" + ",".join(f"{value:.6f}" for value in query_embedding) + "]"
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        dc.id AS chunk_id,
                        kd.source AS source,
                        dc.content AS content,
                        (ce.embedding <=> CAST(:query_embedding AS vector)) AS distance
                    FROM knowledge_documents kd
                    JOIN document_chunks dc ON dc.document_id = kd.id
                    JOIN chunk_embeddings ce ON ce.chunk_id = dc.id
                    WHERE kd.tenant_id = :tenant_id
                    ORDER BY ce.embedding <=> CAST(:query_embedding AS vector)
                    LIMIT :top_k
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "query_embedding": vector,
                    "top_k": top_k,
                },
            )
            return [
                {
                    "chunk_id": row.chunk_id,
                    "source": row.source,
                    "content": row.content,
                    "distance": float(row.distance),
                }
                for row in rows
            ]

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def close(self) -> None:
        self.engine.dispose()
