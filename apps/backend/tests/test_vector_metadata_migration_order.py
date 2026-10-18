"""Retrieval keeps working while the processor has not yet applied vector migration 003."""
import importlib.util
from pathlib import Path

from sqlalchemy import text

from app.services.vector_store import PgVectorQueryStore
from test_tenant_isolation_vector import retrieval  # noqa: F401  (disposable real pgvector fixture)

MIGRATION = Path(__file__).resolve().parents[2] / 'processor/app/vector_store/migrations/003_chunking_metadata.py'


def drop_chunking_metadata(store):
    with store.engine.begin() as connection:
        connection.execute(text('ALTER TABLE document_chunks DROP COLUMN metadata'))
        connection.execute(text('ALTER TABLE knowledge_documents DROP COLUMN metadata'))


def apply_chunking_metadata(store):
    spec = importlib.util.spec_from_file_location('chunking_metadata_schema', MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with store.engine.begin() as connection:
        module.upgrade(connection)


def test_backend_started_before_migration_003_still_retrieves_and_then_uses_metadata(retrieval):  # noqa: F811
    drop_chunking_metadata(retrieval)
    early = PgVectorQueryStore(retrieval.engine.url)
    try:
        before = early.search_chunks('tenant-a', [0.0, 1.0] + [0.0] * 6, top_k=4, provider='mock')
        assert [item['chunk_id'] for item in before] == ['own']
        assert 'chunk_metadata' not in before[0] and before[0]['title']
        apply_chunking_metadata(retrieval)
        with retrieval.engine.begin() as connection:
            connection.execute(text("""UPDATE document_chunks SET metadata = CAST(:value AS jsonb) WHERE id = 'own'"""),
                               {'value': '{"source_spans": [], "primary_spans": [], "section_path": null}'})
        after = early.search_chunks('tenant-a', [0.0, 1.0] + [0.0] * 6, top_k=4, provider='mock')
        assert [item['chunk_id'] for item in after] == ['own']
        assert after[0]['chunk_metadata']['source_spans'] == []
    finally:
        early.close()
