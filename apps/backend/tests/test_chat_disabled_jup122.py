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
