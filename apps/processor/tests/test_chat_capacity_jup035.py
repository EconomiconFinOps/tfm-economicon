"""Processor capacity is frozen at startup and shared by descriptor/admission."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from app.core.runtime_secrets import StartupError
from test_chat_runtime_jup035 import combined
from test_chat_private_jup035 import private,claim,run,signed


@pytest.mark.parametrize('configured,expected',[(None,8),('5',5),('6',6),('7',7),('8',8),(' 5 ',5)])
def test_combined_startup_sets_configured_private_capacity(combined,monkeypatch,configured,expected):
    run_all,main,factory,worker,calls,bound=combined
    if configured is None:monkeypatch.delenv('CHAT_MAX_ACTIVE',raising=False)
    else:monkeypatch.setenv('CHAT_MAX_ACTIVE',configured)
    run_all.main()
    assert main.chat_app.state.chat_capacity==expected
    assert factory.call_count==1 and len(calls)==2


@pytest.mark.parametrize('value',['',' ','4','9','-1','5.0','true','False','text','05','+5'])
def test_invalid_processor_capacity_fails_before_bind_worker_or_listeners(combined,monkeypatch,value):
    run_all,main,factory,worker,calls,bound=combined
    monkeypatch.setenv('CHAT_MAX_ACTIVE',value)
    with pytest.raises(StartupError):run_all.main()
    assert factory.call_count==0 and calls==[] and bound==[]


def test_disabled_processor_keeps_ingestion_and_does_not_bind_private_listener(combined,monkeypatch):
    run_all,main,factory,worker,calls,bound=combined
    monkeypatch.setenv('CHAT_ENABLED','false');monkeypatch.setenv('CHAT_MAX_ACTIVE','invalid')
    run_all.main()
    assert factory.call_count==1 and len(calls)==1 and calls[0]['app']=='app.main:app' and bound==[]


@pytest.mark.parametrize('value',[True,False,5.0,'5',None,4,9])
def test_descriptor_rejects_invalid_programmatic_capacity_without_gateway(private,monkeypatch,value):
    monkeypatch.setattr(private[0].state,'chat_capacity',value,raising=False)
    async def scenario(client):
        response=await client.get('/internal/chat/v2/descriptor',headers=signed('GET','/internal/chat/v2/descriptor'))
        assert response.status_code==503 and response.json()['code']=='capacity_invalid'
        assert private[3]==[]
    run(private[0],scenario)


@pytest.mark.parametrize('value',[True,5.0])
def test_invalid_capacity_cannot_dispatch_even_without_requesting_descriptor(private,monkeypatch,value):
    monkeypatch.setattr(private[0].state,'chat_capacity',value,raising=False)
    async def scenario(client):
        endpoint='/internal/chat/v2/attempts'
        raw=json.dumps(claim(),separators=(',',':')).encode()
        response=await client.post(endpoint,content=raw,headers=signed('POST',endpoint,raw))
        assert response.status_code==503 and response.json()['code']=='capacity_invalid'
        assert private[3]==[] and private[0].state.chat_attempts=={}
    run(private[0],scenario)


@pytest.mark.parametrize('configured,expected',[(None,8),('5',5),('8',8),(' 5 ',5)])
def test_private_lifespan_initializes_capacity_before_resource_readiness(monkeypatch,configured,expected):
    from app import chat
    from app.core import chat_resources
    application=chat.create_chat_app()
    monkeypatch.setenv('CHAT_ENABLED','true')
    if configured is None:monkeypatch.delenv('CHAT_MAX_ACTIVE',raising=False)
    else:monkeypatch.setenv('CHAT_MAX_ACTIVE',configured)
    monkeypatch.setattr(chat_resources,'load_resources',lambda *args:SimpleNamespace(prompt_version='synthetic-v2'))
    async def scenario():
        async with chat.resource_lifespan(application):
            assert getattr(application.state,'chat_capacity',None)==expected
            assert application.state.chat_prompt_version=='synthetic-v2'
    asyncio.run(scenario())


def test_descriptor_and_admission_use_frozen_five_and_release_on_final(private,monkeypatch):
    monkeypatch.setattr(private[0].state,'chat_capacity',5,raising=False)
    async def scenario(client):
        release=asyncio.Event();entered=[];tasks=[]
        async def gateway(context,deadline):
            entered.append(context)
            yield {'type':'delta','text':'Provisional'}
            await release.wait()
            yield {'type':'candidate','result':{'synthetic':'candidate'},'finish_reason':'stop','usage':None}
        monkeypatch.setattr(private[0].state,'chat_gateway',gateway)
        try:
            response=await client.get('/internal/chat/v2/descriptor',headers=signed('GET','/internal/chat/v2/descriptor'))
            assert response.status_code==200 and response.json()['capacity']==5
            # Startup is authoritative even if an environment variable later changes.
            monkeypatch.setenv('CHAT_MAX_ACTIVE','8')
            payloads=[]
            for index in range(6):
                payload=claim(operation_id=f'op-{index}',attempt_id=f'attempt-{index}')
                payloads.append(json.dumps(payload,separators=(',',':')).encode())
                with private[2].begin() as connection:
                    connection.execute(text("INSERT INTO chat_operations SELECT :op,tenant_id,user_id,conversation_id,state,:attempt,attempt_count,attempt_deadline,private_control,input_hash FROM chat_operations WHERE operation_id='op'"),{'op':f'op-{index}','attempt':f'attempt-{index}'})
            endpoint='/internal/chat/v2/attempts'
            for raw in payloads[:5]:tasks.append(asyncio.create_task(client.post(endpoint,content=raw,headers=signed('POST',endpoint,raw))))
            for _ in range(100):
                if len(entered)==5:break
                await asyncio.sleep(.01)
            assert len(entered)==5 and all(not task.done() for task in tasks)
            raw=payloads[5]
            refused=await asyncio.wait_for(client.post(endpoint,content=raw,headers=signed('POST',endpoint,raw)),2)
            assert refused.status_code==503 and refused.json()['code']=='capacity_unavailable' and len(entered)==5
            release.set()
            completed=await asyncio.wait_for(asyncio.gather(*tasks),2)
            assert all(response.status_code==200 and '"candidate_end"' in response.text for response in completed)
            accepted=await asyncio.wait_for(client.post(endpoint,content=raw,headers=signed('POST',endpoint,raw)),2)
            assert accepted.status_code==200 and len(entered)==6
        finally:
            release.set()
            for task in tasks:
                if not task.done():task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
    run(private[0],scenario)


def test_compose_passes_same_configurable_capacity_to_both_services():
    source=(Path(__file__).resolve().parents[3]/'docker-compose.yml').read_text()
    services={};current=None
    for line in source.splitlines():
        if line.startswith('  ') and not line.startswith('   ') and line.endswith(':'):
            current=line.strip()[:-1];services[current]={}
        elif current and line.startswith('      ') and ':' in line:
            key,value=line.strip().split(':',1);services[current][key]=value.strip()
    assert services['backend'].get('CHAT_MAX_ACTIVE')=='${CHAT_MAX_ACTIVE:-8}'
    assert services['processor'].get('CHAT_MAX_ACTIVE')==services['backend']['CHAT_MAX_ACTIVE']


@pytest.mark.parametrize('value',[True,None,5.0,'5'])
def test_private_lifespan_rejects_invalid_existing_capacity_before_loading_resources(monkeypatch,value):
    from app import chat
    from app.core import chat_resources
    application=chat.create_chat_app();application.state.chat_capacity=value
    monkeypatch.setenv('CHAT_ENABLED','true');monkeypatch.setenv('CHAT_MAX_ACTIVE','8')
    loaded=[]
    monkeypatch.setattr(chat_resources,'load_resources',lambda *args:loaded.append(True))
    async def scenario():
        with pytest.raises(StartupError):
            async with chat.resource_lifespan(application):pytest.fail('Invalid startup reached readiness')
        assert loaded==[] and application.state.chat_prompt_version is None
    asyncio.run(scenario())


@pytest.mark.parametrize('value',['invalid','4','5.0','','true'])
def test_private_lifespan_rejects_invalid_environment_without_resource_load(monkeypatch,value):
    from app import chat
    from app.core import chat_resources
    application=chat.create_chat_app()
    monkeypatch.setenv('CHAT_ENABLED','true');monkeypatch.setenv('CHAT_MAX_ACTIVE',value)
    loaded=[]
    monkeypatch.setattr(chat_resources,'load_resources',lambda *args:loaded.append(True))
    async def scenario():
        with pytest.raises(StartupError):
            async with chat.resource_lifespan(application):pytest.fail('Invalid startup reached readiness')
        assert loaded==[] and application.state.chat_prompt_version is None
    asyncio.run(scenario())


def test_private_lifespan_keeps_entrypoint_capacity_frozen_even_if_environment_changes(monkeypatch):
    from app import chat
    from app.core import chat_resources
    application=chat.create_chat_app();application.state.chat_capacity=5
    monkeypatch.setenv('CHAT_ENABLED','true');monkeypatch.setenv('CHAT_MAX_ACTIVE','8')
    monkeypatch.setattr(chat_resources,'load_resources',lambda *args:SimpleNamespace(prompt_version='synthetic-v2'))
    async def scenario():
        async with chat.resource_lifespan(application):assert application.state.chat_capacity==5
    asyncio.run(scenario())

