import os

from sqlalchemy import text


def upgrade(connection) -> None:
    embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "8"))
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    connection.execute(
        text(
            """
            CREATE TABLE knowledge_documents (
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
            CREATE TABLE document_chunks (
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
            CREATE TABLE chunk_embeddings (
                id TEXT PRIMARY KEY,
                chunk_id TEXT UNIQUE NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
                embedding VECTOR({embedding_dimension}) NOT NULL,
                dimension INTEGER NOT NULL,
                provider TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
    )
