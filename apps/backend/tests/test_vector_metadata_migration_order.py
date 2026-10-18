"""Real pgvector recovery before/after 003, with selective errors and bounded IO."""
import asyncio
import importlib.util
from pathlib import Path
from threading import Event
import sys
import time
from unittest.mock import Mock

import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.services import vector_store
from app.services.vector_store import PgVectorQueryStore
from test_tenant_isolation_vector import retrieval  # noqa: F401

MIGRATION = Path(__file__).resolve().parents[2] / 'processor/app/vector_store/migrations/003_chunking_metadata.py'


@pytest.fixture(autouse=True)
def selector_loop_on_windows():
    previous = asyncio.get_event_loop_policy()
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    yield
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(previous)


def drop_chunking_metadata(store, tables=('document_chunks', 'knowledge_documents')):
    with store.engine.begin() as connection:
        for table in tables:
            connection.execute(text(f'ALTER TABLE {table} DROP COLUMN metadata'))


def apply_chunking_metadata(store):
    spec = importlib.util.spec_from_file_location('chunking_metadata_schema', MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with store.engine.begin() as connection:
        module.upgrade(connection)


def options(store, bounded):
    if not bounded:
        return {}
    assert store.ping()  # Capture the authenticated peer, as startup does.
    return {'deadline': time.time() + 10, 'cancelled': Event()}


@pytest.mark.parametrize('bounded', [False, True], ids=['ordinary', 'deadline-cancelled'])
@pytest.mark.parametrize('missing', [('document_chunks',), ('knowledge_documents',),
                                   ('document_chunks', 'knowledge_documents')],
                         ids=['chunk-metadata', 'parent-metadata', 'both'])
def test_backend_started_before_migration_003_still_retrieves_and_then_uses_metadata(retrieval, bounded, missing):
    drop_chunking_metadata(retrieval, missing)
    early = PgVectorQueryStore(retrieval.engine.url)
    observations = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        if 'dc.id AS chunk_id' in statement:
            # Observe the actual server transaction after rollback, including the async path.
            state = connection.execute(text("SELECT current_setting('transaction_isolation'), "
                "current_setting('statement_timeout'), current_setting('lock_timeout')")).one()
            observations.append((statement, tuple(state)))

    event.listen(Engine, 'after_cursor_execute', capture)
    try:
        before = early.search_chunks('tenant-a', [0.0, 1.0] + [0.0] * 6,
            top_k=4, provider='mock', **options(early, bounded))
        assert [item['chunk_id'] for item in before] == ['own']
        assert 'chunk_metadata' not in before[0] and before[0]['title']
        assert any('NULL AS metadata' in statement for statement, state in observations)
        for statement, state in observations:
            assert state[0] == 'repeatable read'
            if bounded:
                assert state[1] != '0' and state[2] != '0'
        # 003 is transactional, not an idempotent repair of a partially migrated schema.
        drop_chunking_metadata(retrieval, tuple(table for table in (
            'document_chunks', 'knowledge_documents') if table not in missing))
        apply_chunking_metadata(retrieval)
        with retrieval.engine.begin() as connection:
            connection.execute(text("UPDATE document_chunks SET metadata = CAST(:value AS jsonb) WHERE id = 'own'"),
                               {'value': '{"source_spans": [], "primary_spans": [], "section_path": null}'})
        observations.clear()
        after = early.search_chunks('tenant-a', [0.0, 1.0] + [0.0] * 6,
            top_k=4, provider='mock', **options(early, bounded))
        assert [item['chunk_id'] for item in after] == ['own']
        assert after[0]['chunk_metadata']['source_spans'] == []
        assert len(observations) == 1 and 'dc.metadata AS metadata' in observations[0][0]
        assert early.search_chunks('tenant-a', [0.0, 1.0] + [0.0] * 6,
            provider='other', **options(early, bounded)) == []
        assert early.search_chunks('no-documents', [0.0, 1.0] + [0.0] * 6,
            provider='mock', **options(early, bounded)) == []
    finally:
        event.remove(Engine, 'after_cursor_execute', capture)
        early.close()


@pytest.mark.parametrize('bounded', [False, True], ids=['ordinary', 'deadline-cancelled'])
@pytest.mark.parametrize('failure,sqlstate', [('table', '42P01'), ('provider', '42703')])
def test_unrelated_sql_error_propagates_without_retry_or_pending_003_diagnostic(retrieval, monkeypatch, bounded, failure, sqlstate):
    if failure == 'table':
        change = 'ALTER TABLE chunk_embeddings RENAME TO unavailable_embeddings'
    else:
        change = 'ALTER TABLE chunk_embeddings RENAME COLUMN provider TO unavailable_provider'
    with retrieval.engine.begin() as connection:
        connection.execute(text(change))
    warning = Mock()
    monkeypatch.setattr(vector_store.logger, 'warning', warning)
    attempts = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        if 'dc.id AS chunk_id' in statement:
            attempts.append(statement)

    event.listen(Engine, 'before_cursor_execute', capture)
    try:
        with pytest.raises(ProgrammingError) as failure_info:
            retrieval.search_chunks('tenant-a', [0.0, 1.0] + [0.0] * 6,
                provider='mock', **options(retrieval, bounded))
        assert failure_info.value.orig.sqlstate == sqlstate
        assert len(attempts) == 1  # A broad ProgrammingError/42703 catch would retry.
        warning.assert_not_called()
    finally:
        event.remove(Engine, 'before_cursor_execute', capture)


@pytest.mark.parametrize('limit', ['cancelled', 'deadline'])
def test_limits_are_rechecked_after_metadata_error_before_fallback(retrieval, monkeypatch, limit):
    drop_chunking_metadata(retrieval)
    assert retrieval.ping()
    cancelled = Event()
    deadline = time.time() + 0.5
    fallback_entered = Event()

    def on_missing_metadata(*args, **kwargs):
        fallback_entered.set()
        if limit == 'cancelled':
            cancelled.set()
        else:
            time.sleep(max(0, deadline - time.time()) + 0.05)

    monkeypatch.setattr(vector_store.logger, 'warning', on_missing_metadata)
    started = time.monotonic()
    with pytest.raises(TimeoutError, match='Retrieval deadline'):
        retrieval.search_chunks('tenant-a', [0.0, 1.0] + [0.0] * 6, provider='mock',
            deadline=deadline, cancelled=cancelled)
    assert fallback_entered.is_set()  # Not merely an already-expired request at entry.
    assert time.monotonic() - started < 2


def test_non_42703_error_at_metadata_position_is_not_retried(retrieval, monkeypatch):
    from types import SimpleNamespace
    warning = Mock()
    monkeypatch.setattr(vector_store.logger, 'warning', warning)
    failures = []

    def inject(connection, cursor, statement, parameters, context, executemany):
        if 'dc.id AS chunk_id' in statement:
            # Keep the metadata location identical; only SQLSTATE disqualifies fallback.
            original = SimpleNamespace(sqlstate='42601', diag=SimpleNamespace(
                statement_position=str(statement.index('dc.metadata') + 1)))
            error = ProgrammingError(statement, parameters, original)
            failures.append(error)
            raise error

    event.listen(Engine, 'before_cursor_execute', inject)
    try:
        with pytest.raises(ProgrammingError) as caught:
            retrieval.search_chunks('tenant-a', [0.0, 1.0] + [0.0] * 6, provider='mock')
        assert len(failures) == 1 and caught.value is failures[0]
        warning.assert_not_called()
    finally:
        event.remove(Engine, 'before_cursor_execute', inject)


@pytest.mark.parametrize('sqlstate,exception', [('42501', ProgrammingError), ('40001', OperationalError)])
def test_permission_and_serialization_errors_never_trigger_legacy_fallback(retrieval, sqlstate, exception):
    class DriverError(Exception):
        pass
    original = DriverError()
    original.sqlstate = sqlstate
    calls = []
    def fail(*args):
        calls.append(True)
        raise exception('synthetic', {}, original)
    event.listen(retrieval.engine, 'before_cursor_execute', fail)
    try:
        with pytest.raises(exception):
            retrieval.search_chunks('tenant-a', [0., 1.] + [0.] * 6)
    finally:
        event.remove(retrieval.engine, 'before_cursor_execute', fail)
    assert len(calls) == 1
