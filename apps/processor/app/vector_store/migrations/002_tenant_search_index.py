from sqlalchemy import text


def upgrade(connection) -> None:
    # Exact cosine search keeps complete tenant-scoped results for the MVP.
    # The unique document_chunks(document_id, chunk_index) and
    # chunk_embeddings(chunk_id) indexes already support both joins.
    connection.execute(text(
        "CREATE INDEX knowledge_documents_tenant_id_idx ON knowledge_documents (tenant_id)"
    ))
