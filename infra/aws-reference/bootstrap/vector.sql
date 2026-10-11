-- Reference only. Run as the database owner in the vector database, not on apply.
-- Requires a PostgreSQL/RDS version supporting pgvector.
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
-- Application table creation and data migration belong to reviewed app migrations.
