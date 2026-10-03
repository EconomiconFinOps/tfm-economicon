from sqlalchemy import bindparam, create_engine, text

from app.services.citations import DocumentCitations


class PgVectorQueryStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True, pool_pre_ping=True)

    def search_chunks(self, tenant_id: str, query_embedding: list[float], top_k: int = 4) -> list[dict]:
        vector = "[" + ",".join(f"{value:.6f}" for value in query_embedding) + "]"
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
            rows = connection.execute(
                text(
                    """
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
                    ORDER BY ce.embedding <=> CAST(:query_embedding AS vector)
                    LIMIT :top_k
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "query_embedding": vector,
                    "top_k": top_k,
                },
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

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def close(self) -> None:
        self.engine.dispose()
