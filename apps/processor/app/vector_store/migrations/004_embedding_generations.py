"""Add verified indexes without relabelling, resizing or deleting legacy vectors."""
from sqlalchemy import text


def upgrade(connection):
    statements = [
        """CREATE TABLE embedding_spaces (
            id TEXT PRIMARY KEY, descriptor JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now())""",
        """CREATE TABLE embedding_cache (
            tenant_id TEXT NOT NULL, space_id TEXT NOT NULL REFERENCES embedding_spaces(id),
            text_hash TEXT NOT NULL, embedding VECTOR(1536) NOT NULL,
            token_count INTEGER CHECK(token_count > 0 AND token_count <= 8192),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(), last_used_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY(tenant_id,space_id,text_hash))""",
        """CREATE TABLE rag_document_revisions (
            tenant_id TEXT NOT NULL, id TEXT NOT NULL, document_id TEXT NOT NULL,
            publication_id TEXT NOT NULL, source TEXT NOT NULL, content TEXT NOT NULL,
            metadata JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY(tenant_id,id), UNIQUE(tenant_id,id,document_id),
            UNIQUE(tenant_id,document_id,publication_id))""",
        """CREATE TABLE rag_revision_chunks (
            tenant_id TEXT NOT NULL, revision_id TEXT NOT NULL, chunk_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL CHECK(chunk_index >= 0), content TEXT NOT NULL, metadata JSONB NOT NULL,
            search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('pg_catalog.simple',content)) STORED,
            PRIMARY KEY(tenant_id,revision_id,chunk_id), UNIQUE(tenant_id,revision_id,chunk_index),
            FOREIGN KEY(tenant_id,revision_id) REFERENCES rag_document_revisions(tenant_id,id))""",
        "CREATE INDEX rag_revision_chunks_fts ON rag_revision_chunks USING GIN(search_vector)",
        """CREATE TABLE rag_chunk_vectors (
            tenant_id TEXT NOT NULL, revision_id TEXT NOT NULL, chunk_id TEXT NOT NULL,
            space_id TEXT NOT NULL, text_hash TEXT NOT NULL,
            PRIMARY KEY(tenant_id,revision_id,chunk_id,space_id),
            FOREIGN KEY(tenant_id,revision_id,chunk_id) REFERENCES rag_revision_chunks(tenant_id,revision_id,chunk_id),
            FOREIGN KEY(tenant_id,space_id,text_hash) REFERENCES embedding_cache(tenant_id,space_id,text_hash))""",
        """CREATE TABLE rag_generations (
            tenant_id TEXT NOT NULL, id TEXT NOT NULL, space_id TEXT NOT NULL REFERENCES embedding_spaces(id),
            state TEXT NOT NULL CHECK(state IN ('building','ready','failed','retired')),
            catalog_revision BIGINT NOT NULL, manifest JSONB NOT NULL DEFAULT '{}'::jsonb,
            retrieval_config JSONB NOT NULL DEFAULT '{"mode": "dense", "rrf_k": 60}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(), retired_at TIMESTAMPTZ,
            PRIMARY KEY(tenant_id,id))""",
        """CREATE TABLE rag_generation_members (
            tenant_id TEXT NOT NULL, generation_id TEXT NOT NULL, document_id TEXT NOT NULL, revision_id TEXT NOT NULL,
            PRIMARY KEY(tenant_id,generation_id,document_id),
            FOREIGN KEY(tenant_id,generation_id) REFERENCES rag_generations(tenant_id,id),
            FOREIGN KEY(tenant_id,revision_id,document_id) REFERENCES rag_document_revisions(tenant_id,id,document_id))""",
        """CREATE TABLE tenant_rag_head (
            tenant_id TEXT PRIMARY KEY, generation_id TEXT, previous_generation_id TEXT,
            version BIGINT NOT NULL DEFAULT 0, catalog_revision BIGINT NOT NULL DEFAULT 0,
            FOREIGN KEY(tenant_id,generation_id) REFERENCES rag_generations(tenant_id,id),
            FOREIGN KEY(tenant_id,previous_generation_id) REFERENCES rag_generations(tenant_id,id))""",
    ]
    for statement in statements:
        connection.execute(text(statement))
