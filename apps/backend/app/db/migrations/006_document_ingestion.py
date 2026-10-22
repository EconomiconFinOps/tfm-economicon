"""Additive document-upload sessions, outbox and recoverable extracted documents."""
from sqlalchemy import inspect, text


TABLES = {
    'document_uploads': '''CREATE TABLE IF NOT EXISTS document_uploads (
        id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, user_id TEXT NOT NULL,
        filename TEXT NOT NULL, format TEXT NOT NULL, expected_size INT8 NOT NULL,
        content_hash TEXT NOT NULL, source TEXT NOT NULL, staging_key TEXT NOT NULL,
        final_key TEXT NOT NULL, status TEXT NOT NULL, job_id TEXT,
        force_reprocess BOOL NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ NOT NULL,
        outbox_sent BOOL NOT NULL DEFAULT false, outbox_next TIMESTAMPTZ NOT NULL,
        cleanup_done BOOL NOT NULL DEFAULT false,
        terminal_failure BOOL NOT NULL DEFAULT false)''',
    'document_upload_slots': '''CREATE TABLE IF NOT EXISTS document_upload_slots (
        user_id TEXT PRIMARY KEY, upload_id TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL)''',
    'document_content_claims': '''CREATE TABLE IF NOT EXISTS document_content_claims (
        tenant_id TEXT NOT NULL, content_hash TEXT NOT NULL, job_id TEXT NOT NULL,
        PRIMARY KEY (tenant_id, content_hash))''',
    'extracted_documents': '''CREATE TABLE IF NOT EXISTS extracted_documents (
        job_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, document JSONB NOT NULL,
        created_at TIMESTAMPTZ NOT NULL)''',
    'extracted_document_parts': '''CREATE TABLE IF NOT EXISTS extracted_document_parts (
        job_id TEXT NOT NULL, tenant_id TEXT NOT NULL, generation TEXT NOT NULL,
        part_index INT8 NOT NULL, content TEXT NOT NULL,
        PRIMARY KEY (job_id, generation, part_index))''',
    'document_execution_claims': '''CREATE TABLE IF NOT EXISTS document_execution_claims (
        job_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, owner TEXT NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL)''',
}

COLUMNS = {
    'document_uploads': set('id tenant_id user_id filename format expected_size content_hash source staging_key final_key status job_id force_reprocess created_at expires_at outbox_sent outbox_next cleanup_done terminal_failure'.split()),
    'document_upload_slots': {'user_id', 'upload_id', 'expires_at'},
    'document_content_claims': {'tenant_id', 'content_hash', 'job_id'},
    'extracted_documents': {'job_id', 'tenant_id', 'document', 'created_at'},
    'extracted_document_parts': {'job_id', 'tenant_id', 'generation', 'part_index', 'content'},
    'document_execution_claims': {'job_id', 'tenant_id', 'owner', 'expires_at'},
}


def schema_steps():
    return list(TABLES.values())


def step_applied(connection, index):
    return inspect(connection).has_table(list(TABLES)[index])


def verify(connection):
    inspector = inspect(connection)
    for name, expected in COLUMNS.items():
        if not inspector.has_table(name):
            raise RuntimeError('Document ingestion schema is incomplete')
        actual = {column['name'] for column in inspector.get_columns(name)}
        if not expected <= actual:
            raise RuntimeError('Document ingestion schema is incomplete')
