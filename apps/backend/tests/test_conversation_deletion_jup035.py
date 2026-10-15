"""Disposable fixtures for scoped, atomic conversation deletion; no inference."""
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import event, text

from app.db.chat_repository import ChatRepository
from test_chat_operations_jup035 import api, body, headers, run

SCOPE = {'tenant_id': 't', 'user_id': 'alice', 'conversation_id': 'alice-chat'}


def operation(db, state='completed'):
    row, _ = ChatRepository(db).reserve(SCOPE, body(), {})
    with db.engine.begin() as connection:
        connection.execute(text('UPDATE chat_operations SET state=:state WHERE operation_id=:id'),
                           {'state': state, 'id': row['operation_id']})
    return row['operation_id']


def legacy(db, owner=None, tenant='t'):
    with db.engine.begin() as connection:
        connection.execute(text("INSERT INTO messages (id,conversation_id,tenant_id,user_id,role,content,created_at) "
                                "VALUES ('legacy','alice-chat',:tenant,:owner,'assistant','Synthetic',:now)"),
                           {'tenant': tenant, 'owner': owner, 'now': datetime.now(timezone.utc)})


def control(db, state, job=None, owner=None):
    with db.engine.begin() as connection:
        connection.execute(text("UPDATE conversations SET dialogue_compaction=:control WHERE id='alice-chat'"),
                           {'control': json.dumps({'v': 1, 'generation': 'synthetic', 'revision': 0,
                                                   'state': state, 'job': job, 'owner': owner})})


def delete(api, expected, target='alice-chat', code=None):
    async def scenario(client):
        response = await client.delete('/assistant/conversations/' + target, headers=headers())
        assert response.status_code == expected, response.text
        if expected == 204:
            assert response.content == b''
        if code:
            assert response.json()['detail'] == code
    run(scenario, api)


@pytest.mark.parametrize('state', ['completed', 'cancelled', 'failed'])
def test_delete_removes_own_terminal_children_and_parent_only(api, state):
    db = api[1]
    operation(db, state)
    legacy(db)
    # Enforce FK ordering in this SQLite fixture as well as transaction effects.
    with db.engine.connect() as connection:
        connection.execute(text('PRAGMA foreign_keys=ON'))
    delete(api, 204)
    with db.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM chat_operations WHERE conversation_id='alice-chat'")).scalar() == 0
        assert connection.execute(text("SELECT count(*) FROM messages WHERE conversation_id='alice-chat'")).scalar() == 0
    assert db.fetch_conversation('alice-chat', 't', 'alice') is None
    assert db.fetch_conversation('bob-chat', 't', 'bob')['title'] == 'Chat'
    delete(api, 404, code='not_found')


@pytest.mark.parametrize('target', ['bob-chat', 'foreign-tenant', 'missing'])
def test_delete_foreign_and_missing_share_404(api, target):
    db = api[1]
    with db.engine.begin() as connection:
        connection.execute(text("INSERT INTO tenants VALUES ('other','Other','other','test')"))
    foreign = db.create_conversation('other', 'alice', 'Foreign')
    delete(api, 404, target=foreign['id'] if target == 'foreign-tenant' else target, code='not_found')
    assert db.fetch_conversation('bob-chat', 't', 'bob') is not None
    assert db.fetch_conversation(foreign['id'], 'other', 'alice') is not None


@pytest.mark.parametrize('state', ['active', 'waiting', 'paused'])
def test_delete_blocks_open_operation(api, state):
    operation(api[1], state)
    delete(api, 409, code='conversation_busy')
    assert api[1].fetch_conversation('alice-chat', 't', 'alice') is not None


@pytest.mark.parametrize('state,job,owner', [('pending', None, None), ('running', None, None),
    ('reconciling', {'id': 'remote'}, None), ('failed', {'id': 'remote'}, None), ('failed', None, 'worker')])
def test_delete_blocks_compaction_until_settled(api, state, job, owner):
    control(api[1], state, job, owner)
    delete(api, 409, code='conversation_compacting')
    assert api[1].fetch_conversation('alice-chat', 't', 'alice') is not None


def test_delete_allows_settled_failed_compaction(api):
    control(api[1], 'failed')
    delete(api, 204)


@pytest.mark.parametrize('kind', ['operation-owner', 'legacy-owner', 'legacy-tenant'])
def test_delete_aborts_owner_anomaly_without_partial_deletion(api, kind):
    db = api[1]
    operation(db)
    legacy(db, owner='bob' if kind == 'legacy-owner' else None, tenant='other' if kind == 'legacy-tenant' else 't')
    if kind == 'operation-owner':
        with db.engine.begin() as connection:
            connection.execute(text("UPDATE chat_operations SET user_id='bob' WHERE conversation_id='alice-chat'"))
    delete(api, 503, code='conversation_integrity')
    with db.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM chat_operations')).scalar() == 1
        assert connection.execute(text('SELECT count(*) FROM messages')).scalar() == 1
    assert db.fetch_conversation('alice-chat', 't', 'alice') is not None


def test_delete_rolls_back_children_if_parent_delete_fails(api):
    db = api[1]
    operation(db)
    legacy(db)
    def fail_parent(connection, cursor, statement, parameters, context, many):
        if statement.strip().startswith('DELETE FROM conversations'):
            raise RuntimeError('Synthetic storage failure')
    event.listen(db.engine, 'before_cursor_execute', fail_parent)
    try:
        delete(api, 503, code='storage_unavailable')
    finally:
        event.remove(db.engine, 'before_cursor_execute', fail_parent)
    with db.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM chat_operations')).scalar() == 1
        assert connection.execute(text('SELECT count(*) FROM messages')).scalar() == 1
    assert db.fetch_conversation('alice-chat', 't', 'alice') is not None
