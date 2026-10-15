"""The default-off delivery cannot start generation or summary work."""
import asyncio
from types import SimpleNamespace

import httpx
import pytest

from app.main import initialize_chat_resources
from test_chat_operations_jup035 import api, body, headers, path


def test_default_startup_does_not_load_chat_or_start_scheduler(monkeypatch):
    monkeypatch.delenv('CHAT_ENABLED', raising=False)
    application=SimpleNamespace(state=SimpleNamespace())
    asyncio.run(initialize_chat_resources(application))
    assert application.state.chat_enabled is False
    assert not hasattr(application.state,'chat_service')
    assert not hasattr(application.state,'chat_context_builder')


@pytest.mark.parametrize('suffix', ['', '/synthetic-operation/resume', '../summary/retry'])
def test_disabled_chat_cannot_start_work(api,monkeypatch,suffix):
    monkeypatch.setattr(api[0].state,'chat_enabled',False,raising=False)
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api[0]),base_url='http://test') as client:
            target=path()+suffix if not suffix.startswith('..') else '/assistant/conversations/alice-chat/summary/retry'
            response=await client.post(target,headers=headers(),json=body())
            assert response.status_code==503,response.text
            assert response.json()['detail']=='chat_unavailable'
        assert api[2].claims==[]
        assert not hasattr(api[0].state,'chat_service')
    asyncio.run(scenario())


@pytest.mark.parametrize('enabled,expected', [(True, True), (False, False), ('true', False), (1, False), (None, False)])
def test_capabilities_reports_only_effective_boolean_without_starting_chat(api, monkeypatch, enabled, expected):
    monkeypatch.setattr(api[0].state, 'chat_enabled', enabled, raising=False)
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api[0]), base_url='http://test') as client:
            response = await client.get('/assistant/capabilities', headers=headers())
            assert response.status_code == 200
            assert response.json() == {'chat_enabled': expected}
            assert response.headers['cache-control'] == 'no-store'
        assert api[2].claims == []
        assert not hasattr(api[0].state, 'chat_service')
        assert len(api[1].fetch_messages('alice-chat', 't', 'alice')) == 0
    asyncio.run(scenario())


def test_capabilities_requires_session_and_authorized_tenant(api):
    from app.api.dependencies import get_current_user
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api[0]), base_url='http://test') as client:
            assert (await client.get('/assistant/capabilities', headers={**headers(), 'X-Tenant-Id': 'other'})).status_code == 403
            assert (await client.get('/assistant/capabilities', headers={'Authorization': 'Bearer synthetic'})).status_code == 400
            api[0].dependency_overrides.pop(get_current_user)
            assert (await client.get('/assistant/capabilities')).status_code == 401
        assert api[2].claims == []
        assert not hasattr(api[0].state, 'chat_service')
    asyncio.run(scenario())
