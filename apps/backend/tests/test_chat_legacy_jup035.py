"""Legacy writer must share the conversation exclusion and atomic final pair."""
import asyncio
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import text

from app.services.assistant import AssistantService
from test_chat_operations_jup035 import api,body,existing,headers,messages,path,run
from test_ownership_questions import billing_double, request_body


def legacy_resources(api,monkeypatch):
    monkeypatch.setattr(api[0].state,'embedding_provider',SimpleNamespace(name='mock',alias='mock',dimension=8,embed=lambda _: [1.0]+[0.0]*7),raising=False)
    monkeypatch.setattr(api[0].state,'vector_store',SimpleNamespace(search_chunks=lambda *a,**k: []),raising=False)
    monkeypatch.setattr(api[0].state,'assistant_service',AssistantService(),raising=False)


@pytest.mark.parametrize('ownership', [False, True])
def test_legacy_message_cannot_interleave_with_open_operation(api,monkeypatch,ownership):
    legacy_resources(api,monkeypatch)
    async def scenario(c):
        api[2].release=asyncio.Event()
        payload=body()
        task=asyncio.create_task(c.post(path(),json=payload,headers=headers()))
        try:
            # Observe the first request's real reservation before replay.
            from test_chat_operations_jup035 import until_state
            reserved_id=None
            for _ in range(100):
                with api[1].engine.connect() as connection:
                    reserved_id=connection.execute(text(
                        "SELECT operation_id FROM chat_operations WHERE tenant_id='t' "
                        "AND user_id='alice' AND conversation_id='alice-chat' "
                        "AND client_request_id=:request_id"),{'request_id':payload['request_id']}).scalar_one_or_none()
                if reserved_id is not None:break
                await asyncio.sleep(.01)
            assert reserved_id is not None,'The first request did not reserve its operation.'
            observed=await until_state(c,path()+'/'+reserved_id,'active')
            assert not task.done() and not api[2].release.is_set()
            op=await existing(c,payload)
            assert op['operation_id']==reserved_id==observed['operation_id']
            result=await c.post('/assistant/conversations/alice-chat/messages',json=request_body() if ownership else {'content':'Otra pregunta'},headers=headers())
            assert result.status_code==409,result.text
            assert messages(api[1])==[]
            await c.post(op['status_url']+'/stop',headers=headers())
            api[2].release.set();await task
        finally:
            api[2].release.set()
            if not task.done():task.cancel()
    run(scenario,api)


@pytest.mark.parametrize('ownership', [False, True])
def test_legacy_assistant_sql_failure_rolls_back_question(api,monkeypatch,ownership):
    legacy_resources(api,monkeypatch)
    monkeypatch.setattr(api[1],'fetch_billing_summary',lambda *a,**k: billing_double())
    with api[1].engine.begin() as connection:
        connection.execute(text("""CREATE TRIGGER reject_legacy_final BEFORE UPDATE OF dialogue_history ON conversations
            BEGIN SELECT RAISE(ABORT,'synthetic failure'); END"""))
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api[0],raise_app_exceptions=False),base_url='http://test') as c:
            result=await c.post('/assistant/conversations/alice-chat/messages',json=request_body() if ownership else {'content':'Pregunta'},headers=headers())
            assert messages(api[1])==[], 'Partial question committed by legacy route'
            assert result.status_code==503,result.text
    asyncio.run(scenario())
