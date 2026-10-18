"""Additive metadata; existing documents and vectors remain searchable."""
from sqlalchemy import text


def upgrade(connection) -> None:
    connection.execute(text("ALTER TABLE knowledge_documents ADD COLUMN metadata JSONB NOT NULL DEFAULT '{}'::jsonb"))
    connection.execute(text("ALTER TABLE document_chunks ADD COLUMN metadata JSONB NOT NULL DEFAULT '{}'::jsonb"))
