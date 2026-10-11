"""Scoped title-only updates; no processor or model calls."""
import pytest
from sqlalchemy import text
from test_chat_operations_jup035 import api, headers, run


def test_rename_persists_without_changing_history(api):
    db = api[1]
    with db.engine.connect() as connection:
        before = dict(connection.execute(text("SELECT * FROM conversations WHERE id='alice-chat'")).mappings().one())

    async def scenario(client):
        response = await client.patch('/assistant/conversations/alice-chat', headers=headers(), json={'title': '  Nuevo\n  nombre  '})
        assert response.status_code == 200, response.text
        assert response.json()['title'] == 'Nuevo nombre'
        assert response.json()['user_id'] == 'alice'
        detail = await client.get('/assistant/conversations/alice-chat', headers=headers())
        assert detail.json()['conversation']['title'] == 'Nuevo nombre'
        listing = await client.get('/assistant/conversations', headers=headers())
        assert listing.json()['items'][0]['title'] == 'Nuevo nombre'
    run(scenario, api)
    with db.engine.connect() as connection:
        after = dict(connection.execute(text("SELECT * FROM conversations WHERE id='alice-chat'")).mappings().one())
    assert {k: v for k, v in before.items() if k not in ('title', 'updated_at')} == {
        k: v for k, v in after.items() if k not in ('title', 'updated_at')}


@pytest.mark.parametrize('target', ['bob-chat', 'foreign-tenant', 'missing'])
def test_rename_foreign_or_missing_is_404(api, target):
    db = api[1]
    with db.engine.begin() as connection:
        connection.execute(text("INSERT INTO tenants VALUES ('other','Other','other','test')"))
    foreign = db.create_conversation('other', 'alice', 'Foreign')
    target_id = foreign['id'] if target == 'foreign-tenant' else target

    async def scenario(client):
        response = await client.patch('/assistant/conversations/' + target_id, headers=headers(), json={'title': 'Forbidden'})
        assert response.status_code == 404, response.text
        assert response.json()['detail'] == 'Conversation not found.'
    run(scenario, api)
    assert db.fetch_conversation('bob-chat', 't', 'bob')['title'] == 'Chat'
    assert db.fetch_conversation(foreign['id'], 'other', 'alice')['title'] == 'Foreign'


@pytest.mark.parametrize('payload', [{'title': ' \n\t '}, {'title': 'x' * 61}, {'title': '\U0001f600' * 61}, {'title': 'Valid', 'user_id': 'bob'}])
def test_rename_rejects_invalid_payload(api, payload):
    async def scenario(client):
        response = await client.patch('/assistant/conversations/alice-chat', headers=headers(), json=payload)
        assert response.status_code == 422, response.text
    run(scenario, api)
    assert api[1].fetch_conversation('alice-chat', 't', 'alice')['title'] == 'Chat'


def test_rename_accepts_60_unicode_codepoints(api):
    async def scenario(client):
        response = await client.patch('/assistant/conversations/alice-chat', headers=headers(), json={'title': '\U0001f600' * 60})
        assert response.status_code == 200, response.text
        assert response.json()['title'] == '\U0001f600' * 60
    run(scenario, api)
