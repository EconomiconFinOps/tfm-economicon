"""Canonical history contracts through existing Database/Runner interfaces.

SQLite is a focused fixture; native Cockroach preservation is proved separately.
No product module which does not yet exist is imported for Red.
"""
import copy
import importlib
import json
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text

from app.core.runtime_secrets import StartupError
from app.db.chat_repository import ChatError
from app.db.database import Database
from app.db.migration_runner import MigrationRunner


DIRECTORY = Path(importlib.import_module('app.db.migrations').__file__).parent
SCOPE = {'tenant_id': 't', 'user_id': 'u', 'conversation_id': 'c'}
STAMP = '2026-10-10T03:12:00.123456Z'


def runner(db, directory=DIRECTORY):
    return MigrationRunner(db.engine, 'app.db.migrations', directory)


@pytest.fixture
def legacy_db(tmp_path):
    db = Database.__new__(Database)
    db.engine = create_engine('sqlite:///'+str(tmp_path/'history.db'))
    event.listen(db.engine, 'before_cursor_execute',
        lambda c, cursor, sql, args, context, many:
            (sql.replace('DEFAULT now()', 'DEFAULT CURRENT_TIMESTAMP'), args), retval=True)
    # Cockroach STRING has text semantics; SQLite assigns NUMERIC affinity to
    # STRING and otherwise converts migration '001' to integer 1 on reread.
    with db.engine.begin() as c:
        c.execute(text('CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)'))
    initial = tmp_path/'legacy'
    initial.mkdir()
    for filename in ('001_initial.py', '002_chat_operations.py'):
        (initial/filename).touch()
    runner(db, initial).run()
    with db.engine.begin() as c:
        c.execute(text("INSERT INTO tenants VALUES ('t','Tenant','tenant','test')"))
        c.execute(text("INSERT INTO users VALUES ('u','u@example.com','synthetic','User','member',:now)"), {'now': STAMP})
        c.execute(text("INSERT INTO user_tenants VALUES ('u','t','member',:now)"), {'now': STAMP})
        c.execute(text("INSERT INTO conversations (id,tenant_id,user_id,title,created_at,updated_at) VALUES ('c','t','u','Chat',:now,:now)"), {'now': STAMP})
    yield db
    db.dispose()


def document():
    messages = []
    for ordinal, (identifier, role, question) in enumerate([
            ('z-q', 'user', 'z-q'), ('a-answer', 'assistant', 'z-q'),
            ('q-B', 'user', 'q-B'), ('answer-B', 'assistant', 'q-B'),
            ('retry-A', 'assistant', 'z-q')]):
        messages.append({'ordinal': ordinal, 'id': identifier, 'role': role,
            'author_id': 'u', 'question_id': question, 'origin': 'completed',
            'content': 'Texto completo '+identifier, 'metadata': {}, 'created_at': STAMP})
    return {'schema_version': 1, 'identity': dict(SCOPE), 'revision': 3,
        'next_ordinal': 5, 'messages': messages}


def install(db, value):
    with db.engine.begin() as c:
        c.execute(text('ALTER TABLE conversations ADD COLUMN dialogue_history JSONB NULL'))
        c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='c'"),
            {'doc': value if isinstance(value, str) else json.dumps(value)})
        c.execute(text("INSERT INTO schema_migrations(version) VALUES ('003')"))


def raw(db):
    with db.engine.connect() as c:
        return c.execute(text("SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id='c'")).scalar_one()


def test_owned_read_is_canonical_ordinal_order_without_legacy_sql(legacy_db):
    value = document()
    # Deliberately decreasing timestamps and random IDs cannot reorder history.
    value['messages'][4]['created_at'] = '2020-01-01T00:00:00.000001Z'
    value['messages'][1]['author_id'] = None
    value['messages'][1]['origin'] = 'legacy'
    install(legacy_db, value)
    statements = []
    event.listen(legacy_db.engine, 'before_cursor_execute',
        lambda c, cursor, sql, args, context, many: statements.append(sql))
    observed = legacy_db.fetch_messages('c', 't', 'u')
    assert [row['id'] for row in observed] == [m['id'] for m in value['messages']]
    assert observed[1]['content'] == value['messages'][1]['content']
    assert all(row['created_at'].tzinfo is not None for row in observed)
    assert not any('FROM messages' in sql or 'JOIN messages' in sql for sql in statements)
    assert json.loads(raw(legacy_db)) == value


def test_new_conversation_has_valid_empty_document(legacy_db):
    install(legacy_db, document())
    conversation = legacy_db.create_conversation('t', 'u', 'Nuevo')
    with legacy_db.engine.connect() as c:
        value = c.execute(text('SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id=:id'), conversation).scalar_one()
    assert value is not None, 'NULL is unconverted history, not an empty conversation'
    assert json.loads(value) == {'schema_version': 1,
        'identity': {**SCOPE, 'conversation_id': conversation['id']},
        'revision': 0, 'next_ordinal': 0, 'messages': []}


def test_public_projection_preserves_json_numbers_and_null_metadata(legacy_db):
    value = document()
    value['messages'][1]['origin'] = 'legacy'
    value = json.dumps(value).replace('"metadata": {}',
        '"metadata": {"amount": 12345678901234567890.12345678901234567890123456789}', 1)
    value = value.replace('"metadata": {}', '"metadata": null', 1)
    install(legacy_db, value)
    observed = legacy_db.fetch_messages('c', 't', 'u')
    assert len(observed) == 5
    assert observed[0]['metadata']['amount'] == Decimal('12345678901234567890.12345678901234567890123456789')
    assert observed[1]['metadata'] is None


def test_new_completed_message_with_null_metadata_fails_closed(legacy_db):
    value = document()
    value['messages'][1]['metadata'] = None
    install(legacy_db, value)
    with pytest.raises(ChatError) as failure:
        legacy_db.fetch_messages('c', 't', 'u')
    assert failure.value.status == 503


@pytest.mark.parametrize('defect', [
    'null', 'json', 'duplicate_key', 'version', 'bool_version', 'identity',
    'extra', 'negative_revision', 'bool_revision', 'next', 'bool_next',
    'duplicate_id', 'ordinal', 'bool_ordinal', 'role_type', 'author_type',
    'timestamp', 'timezone', 'question', 'origin', 'content', 'extra_message'])
def test_malformed_history_fails_closed_without_fallback(legacy_db, defect):
    value = document()
    if defect == 'null': value = 'null'
    elif defect == 'json': value = '{broken'
    elif defect == 'duplicate_key': value = json.dumps(value).replace('"revision": 3', '"revision": 3, "revision": 0')
    elif defect == 'version': value['schema_version'] = 2
    elif defect == 'bool_version': value['schema_version'] = True
    elif defect == 'identity': value['identity']['user_id'] = 'foreign'
    elif defect == 'extra': value['fallback'] = []
    elif defect == 'negative_revision': value['revision'] = -1
    elif defect == 'bool_revision': value['revision'] = True
    elif defect == 'next': value['next_ordinal'] = 4
    elif defect == 'bool_next': value['next_ordinal'] = True
    elif defect == 'duplicate_id': value['messages'][1]['id'] = 'z-q'
    elif defect == 'ordinal': value['messages'][1]['ordinal'] = 0
    elif defect == 'bool_ordinal': value['messages'][0]['ordinal'] = False
    elif defect == 'role_type': value['messages'][0]['role'] = 7
    elif defect == 'author_type': value['messages'][0]['author_id'] = 7
    elif defect == 'timestamp': value['messages'][0]['created_at'] = 'not-a-time'
    elif defect == 'timezone': value['messages'][0]['created_at'] = '2026-10-10T03:12:00.123456'
    elif defect == 'question': value['messages'][1]['question_id'] = 'absent'
    elif defect == 'origin': value['messages'][0]['origin'] = 'delta'
    elif defect == 'content': value['messages'][0]['content'] = None
    elif defect == 'extra_message': value['messages'][0]['buffer'] = 'partial'
    install(legacy_db, value)
    with pytest.raises(ChatError) as failure:
        legacy_db.fetch_messages('c', 't', 'u')
    assert failure.value.status == 503


def test_null_column_is_not_an_empty_history(legacy_db):
    install(legacy_db, document())
    with legacy_db.engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_history=NULL WHERE id='c'"))
    with pytest.raises(ChatError) as failure:
        legacy_db.fetch_messages('c', 't', 'u')
    assert failure.value.status == 503


@pytest.mark.parametrize('tenant,user', [('foreign', 'u'), ('t', 'foreign')])
def test_unowned_read_does_not_parse_or_expose_document(legacy_db, tenant, user):
    install(legacy_db, '{broken')
    assert legacy_db.fetch_messages('c', tenant, user) == []


def test_verify_requires_003_instead_of_accepting_legacy_schema(legacy_db):
    with pytest.raises(StartupError):
        runner(legacy_db).verify()


@pytest.mark.parametrize('defect', ['null', 'version', 'identity', 'ordinal'])
def test_verify_rejects_incomplete_or_incoherent_history(legacy_db, defect):
    value = document()
    if defect == 'null': value = 'null'
    elif defect == 'version': value['schema_version'] = 2
    elif defect == 'identity': value['identity']['tenant_id'] = 'other'
    else: value['messages'][1]['ordinal'] = 0
    install(legacy_db, value)
    with pytest.raises(StartupError):
        runner(legacy_db).verify()


def test_verify_valid_document_never_reads_legacy_rows(legacy_db):
    install(legacy_db, document())
    runner(legacy_db).run()  # Add the now-required operational column/version004.
    statements = []
    event.listen(legacy_db.engine, 'before_cursor_execute',
        lambda c, cursor, sql, args, context, many: statements.append(sql))
    runner(legacy_db).verify()
    assert not any('FROM messages' in sql or 'JOIN messages' in sql for sql in statements)
