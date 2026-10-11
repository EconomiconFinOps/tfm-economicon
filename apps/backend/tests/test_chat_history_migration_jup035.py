"""Additive, resumable and lossless 003 migration through MigrationRunner."""
import json
from decimal import Decimal

import pytest
from sqlalchemy import event, inspect, text

from test_chat_history_document_jup035 import legacy_db, runner, SCOPE, STAMP


PRECISE = '{"amount":12345678901234567890.12345678901234567890123456789,"negative":-0.00000000000000000000001,"large":9007199254740993,"citation":{"id":"évidence-😀"}}'


def add(db, identifier, role, metadata=None, *, author='u', tenant='t', stamp=STAMP):
    with db.engine.begin() as c:
        c.execute(text('INSERT INTO messages (id,conversation_id,tenant_id,user_id,role,content,metadata,created_at) VALUES (:id,\'c\',:tenant,:author,:role,:content,:metadata,:stamp)'),
            {'id': identifier, 'tenant': tenant, 'author': author, 'role': role,
             'content': '  exacto é 😀\n'+identifier, 'metadata': metadata, 'stamp': stamp})


def source(db):
    with db.engine.connect() as c:
        return [dict(row) for row in c.execute(text('SELECT id,conversation_id,tenant_id,user_id,role,content,CAST(metadata AS TEXT) AS metadata,created_at FROM messages ORDER BY id')).mappings()]


def history(db):
    with db.engine.connect() as c:
        value = c.execute(text("SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id='c'")).scalar_one()
    return json.loads(value, parse_float=Decimal)


def version(db):
    with db.engine.connect() as c:
        return c.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='003'")).scalar_one()


def migrate(db):
    runner(db).run()
    assert 'dialogue_history' in {col['name'] for col in inspect(db.engine).get_columns('conversations')}, '003 must add the canonical column'


def test_backfill_preserves_exact_values_orphans_and_valid_links(legacy_db):
    add(legacy_db, 'z-question', 'user', PRECISE)
    add(legacy_db, 'a-answer', 'assistant', '{"generation":{"question_message_id":"z-question"}}', author=None)
    add(legacy_db, 'orphan', 'assistant', '{"generation":{"question_message_id":"unknown"}}', author=None, stamp='2026-10-10T04:12:01.654321+01:00')
    add(legacy_db, 'unanswered', 'user', None, stamp='2026-10-10T03:12:02.000001Z')
    before = source(legacy_db)
    migrate(legacy_db)
    value = history(legacy_db)
    assert source(legacy_db) == before
    assert value['identity'] == SCOPE and value['revision'] == 0
    assert value['next_ordinal'] == 4 and len(value['messages']) == 4
    assert [m['ordinal'] for m in value['messages']] == list(range(4))
    records = {m['id']: m for m in value['messages']}
    assert [m['id'] for m in value['messages']][:2] == ['z-question', 'a-answer']
    assert records['a-answer']['author_id'] is None and records['a-answer']['question_id'] == 'z-question'
    assert records['orphan']['question_id'] is None
    assert records['unanswered']['question_id'] == 'unanswered' and records['unanswered']['metadata'] is None
    assert records['orphan']['created_at'] == '2026-10-10T03:12:01.654321Z'
    assert records['z-question']['metadata']['amount'] == Decimal('12345678901234567890.12345678901234567890123456789')
    assert records['z-question']['metadata']['large'] == 9007199254740993
    assert records['z-question']['metadata']['negative'] == Decimal('-0.00000000000000000000001')
    assert records['z-question']['metadata']['citation']['id'] == 'évidence-😀'
    assert all(m['origin'] == 'legacy' and m['content'] == '  exacto é 😀\n'+m['id'] for m in value['messages'])
    receipt = value['migration']
    assert receipt['version'] == '003' and receipt['source_count'] == 4
    assert len(receipt['source_sha256']) == 64
    assert version(legacy_db) == 1
    runner(legacy_db).verify()


def test_restart_validates_existing_checkpoint_without_rewriting_it(legacy_db):
    add(legacy_db, 'question', 'user', PRECISE)
    migrate(legacy_db)
    before = history(legacy_db)
    # Simulate crash after all conversation commits, before version commit.
    with legacy_db.engine.begin() as c:
        c.execute(text("DELETE FROM schema_migrations WHERE version='003'"))
    updates = []
    event.listen(legacy_db.engine, 'before_cursor_execute',
        lambda c, cursor, sql, args, context, many: updates.append(sql) if 'UPDATE conversations' in sql else None)
    runner(legacy_db).run()
    assert history(legacy_db) == before and version(legacy_db) == 1
    assert not updates, 'restart must verify the retained checkpoint, not overwrite it'


@pytest.mark.parametrize('defect', ['source_content', 'source_metadata', 'document_content', 'receipt'])
def test_restart_blocks_changed_source_or_document_and_preserves_both(legacy_db, defect):
    add(legacy_db, 'question', 'user', PRECISE)
    migrate(legacy_db)
    with legacy_db.engine.begin() as c:
        c.execute(text("DELETE FROM schema_migrations WHERE version='003'"))
        if defect == 'source_content': c.execute(text("UPDATE messages SET content='changed' WHERE id='question'"))
        elif defect == 'source_metadata': c.execute(text("UPDATE messages SET metadata='{}' WHERE id='question'"))
        else:
            value = history(legacy_db)
            if defect == 'document_content': value['messages'][0]['content'] = 'changed'
            else: value['migration']['source_sha256'] = '0'*64
            # Preserve Decimal through an already serialized source lexeme.
            original = c.execute(text("SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id='c'")).scalar_one()
            value_raw = original.replace('  exacto é 😀\\nquestion', 'changed') if defect == 'document_content' else original.replace(value['migration']['source_sha256'], '0'*64)
            if defect == 'receipt':
                original_hash = history(legacy_db)['migration']['source_sha256']
                value_raw = original.replace(original_hash, '0'*64)
            c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='c'"), {'doc': value_raw})
    saved_source, saved_doc = source(legacy_db), history(legacy_db)
    with pytest.raises(RuntimeError): runner(legacy_db).run()
    assert source(legacy_db) == saved_source and history(legacy_db) == saved_doc
    assert version(legacy_db) == 0


@pytest.mark.parametrize('defect', ['tenant', 'author', 'role', 'json'])
def test_inconsistent_legacy_scope_or_structure_blocks_version(legacy_db, defect):
    add(legacy_db, 'bad', '' if defect == 'role' else 'user', '{broken' if defect == 'json' else '{}',
        tenant='other' if defect == 'tenant' else 't', author='other' if defect == 'author' else 'u')
    before = source(legacy_db)
    with pytest.raises(RuntimeError): runner(legacy_db).run()
    assert source(legacy_db) == before and version(legacy_db) == 0


def test_incompatible_existing_column_is_not_accepted_by_name(legacy_db):
    with legacy_db.engine.begin() as c:
        c.execute(text('ALTER TABLE conversations ADD COLUMN dialogue_history TEXT NULL'))
    with pytest.raises(RuntimeError): runner(legacy_db).run()
    assert version(legacy_db) == 0


def test_checkpoint_survives_interruption_between_conversations(legacy_db):
    with legacy_db.engine.begin() as c:
        c.execute(text("INSERT INTO conversations (id,tenant_id,user_id,title,created_at,updated_at) VALUES ('d','t','u','Second',:now,:now)"), {'now': STAMP})
    writes = []
    def interrupted(c, cursor, sql, args, context, many):
        if sql.startswith('UPDATE conversations SET dialogue_history'):
            writes.append(sql)
            if len(writes) == 2: raise RuntimeError('synthetic interruption')
    event.listen(legacy_db.engine, 'before_cursor_execute', interrupted)
    with pytest.raises(RuntimeError, match='synthetic interruption'): runner(legacy_db).run()
    event.remove(legacy_db.engine, 'before_cursor_execute', interrupted)
    assert history(legacy_db)['migration']['source_count'] == 0 and version(legacy_db) == 0
    with legacy_db.engine.connect() as c:
        assert c.execute(text("SELECT dialogue_history FROM conversations WHERE id='d'")).scalar_one() is None
    runner(legacy_db).run()
    assert version(legacy_db) == 1
    runner(legacy_db).verify()
