"""Configured startup capacity, SQL claims and release under five live producers.

SQLite and the scripted processor prove local contracts, not real-provider capacity.
"""
import asyncio
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from app.core.runtime_secrets import StartupError
from app.db.chat_repository import ChatError
from app.services.chat_operations import ChatOperations
from test_chat_operations_jup035 import api,body,messages


def ready(api,monkeypatch,value):
    from app import main
    from app.services import chat_context
    monkeypatch.setenv('CHAT_ENABLED','true')
    if value is None:monkeypatch.delenv('CHAT_MAX_ACTIVE',raising=False)
    else:monkeypatch.setenv('CHAT_MAX_ACTIVE',value)
    monkeypatch.setattr(api[0].state,'chat_resources',SimpleNamespace(),raising=False)
    builder=api[0].state.chat_context_builder
    monkeypatch.setattr(chat_context,'ChatContext',lambda app,resources:builder)
    return main


@pytest.mark.parametrize('configured,expected',[(None,8),('5',5),('6',6),('7',7),('8',8),(' 5 ',5)])
def test_backend_startup_uses_one_configured_capacity(api,monkeypatch,configured,expected):
    main=ready(api,monkeypatch,configured)
    async def scenario():
        try:
            await main.initialize_chat_resources(api[0])
            assert api[0].state.chat_max_active==expected
            assert api[0].state.chat_service.capacity==expected
        finally:
            service=getattr(api[0].state,'chat_service',None)
            if service:await service.close()
    asyncio.run(scenario())


@pytest.mark.parametrize('value',['',' ','4','9','-1','5.0','true','False','text','05','+5'])
def test_invalid_backend_configuration_cannot_start_scheduler_or_admit_chat(api,monkeypatch,value):
    main=ready(api,monkeypatch,value)
    async def scenario():
        try:
            with pytest.raises(StartupError):await main.initialize_chat_resources(api[0])
            assert getattr(api[0].state,'chat_service',None) is None
        finally:
            service=getattr(api[0].state,'chat_service',None)
            if service:await service.close()
    asyncio.run(scenario())


@pytest.mark.parametrize('value',[True,False,5.0,'5',None])
def test_programmatic_capacity_requires_integer_and_rejects_boolean_even_with_test_clock(api,monkeypatch,value):
    monkeypatch.setattr(api[0].state,'chat_max_active',value)
    with pytest.raises(ChatError) as failure:ChatOperations(api[0])
    assert failure.value.status==503 and failure.value.code=='capacity_invalid'


def test_chat_disabled_ignores_capacity_and_does_not_activate_service(api,monkeypatch):
    from app import main
    monkeypatch.setenv('CHAT_ENABLED','false')
    monkeypatch.setenv('CHAT_MAX_ACTIVE','invalid')
    asyncio.run(main.initialize_chat_resources(api[0]))
    assert getattr(api[0].state,'chat_service',None) is None


@pytest.mark.parametrize('release_mode',['stop','final'])
def test_five_producers_before_first_final_sixth_waits_without_attempt_then_claims_released_slot(api,monkeypatch,release_mode):
    main=ready(api,monkeypatch,'5')
    # Sixth conversation is owned by an existing identity; no synthetic sixth human.
    history={'schema_version':1,'identity':{'tenant_id':'t','user_id':'alice','conversation_id':'alice-extra'},'revision':0,'next_ordinal':0,'messages':[]}
    with api[1].engine.begin() as connection:
        connection.execute(text("INSERT INTO conversations (id,tenant_id,user_id,title,created_at,updated_at,dialogue_history) SELECT 'alice-extra',tenant_id,user_id,'Extra',created_at,updated_at,:history FROM conversations WHERE id='alice-chat'"),{'history':json.dumps(history)})
    async def scenario():
        releases={};entered=[]
        async def descriptor():return {'v':2,'boot_id':'synthetic-boot','prompt_version':'synthetic-v2','capacity':5}
        async def stream(claim):
            api[2].claims.append(claim);entered.append(claim['operation_id'])
            release=releases.setdefault(claim['operation_id'],asyncio.Event())
            yield {'type':'delta','text':'Sin evidencia'}
            await release.wait()
            yield {'type':'candidate','result':api[2].candidate,'finish_reason':'stop','usage':None}
        monkeypatch.setattr(api[2],'descriptor',descriptor)
        monkeypatch.setattr(api[2],'stream',stream)
        await main.initialize_chat_resources(api[0])
        service=api[0].state.chat_service
        scopes=[{'tenant_id':'t','user_id':owner,'conversation_id':owner+'-chat'} for owner in ['alice','bob','carol','dave','eve']]
        try:
            rows=[]
            for scope in scopes:
                row,_=await service.open(scope,body(scope['user_id']));rows.append(row)
            for _ in range(100):
                if len(entered)==5:break
                await asyncio.sleep(.01)
            assert len(entered)==5 and service.occupied==5 and messages(api[1])==[]
            with api[1].engine.connect() as connection:
                assert connection.execute(text("SELECT count(*) FROM chat_operations WHERE state='active' AND attempt_count=1")).scalar_one()==5
            sixth_scope={'tenant_id':'t','user_id':'alice','conversation_id':'alice-extra'}
            sixth,_=await service.open(sixth_scope,body())
            assert sixth['state']=='waiting' and sixth['attempt_count']==0 and sixth['current_attempt_id'] is None
            assert service.public(sixth)['wait_info']['reason']=='local_capacity'
            assert len(api[2].claims)==5 and service.occupied==5
            if release_mode=='stop':await service.stop(scopes[0],rows[0]['operation_id'])
            else:releases[rows[0]['operation_id']].set()
            for _ in range(150):
                sixth=await service.get(sixth_scope,sixth['operation_id'])
                if sixth['state']=='active' and len(api[2].claims)==6:break
                await asyncio.sleep(.01)
            assert sixth['state']=='active' and sixth['attempt_count']==1
            assert len(api[2].claims)==6 and service.occupied==5
            assert len(messages(api[1]))==(0 if release_mode=='stop' else 2)
        finally:
            for event in releases.values():event.set()
            await service.close()
    asyncio.run(scenario())
