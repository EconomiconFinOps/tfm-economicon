"""Observation is read-only; a live snapshot and cold state are distinct."""
import asyncio
import copy
import json

from app.db.chat_repository import ChatRepository
from app.services.chat_operations import service
from test_chat_operations_jup035 import ANSWER,api,body,headers,messages,path,run,until_state

def frame(value):
    data=next(line[6:] for line in value.splitlines() if line.startswith('data: '))
    identifier=next((line[4:] for line in value.splitlines() if line.startswith('id: ')),None)
    return identifier,json.loads(data)


def test_cold_observer_projects_recovering_without_dispatch_or_renewing_operation(api):
    scope={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
    row,_=ChatRepository(api[1],api[3]).reserve(scope,body(),{
        'prompt_version':'synthetic-v2','messages':[{'role':'user','content':'Pregunta'}],'authorized_evidence':[]})
    async def scenario(client):
        response=await client.get(path()+'/'+row['operation_id']+'/events',headers=headers())
        assert response.status_code==202,response.text
        records=[frame(value)[1] for value in response.text.strip().split('\n\n') if 'data: ' in value]
        assert records[-1]['type']=='recovering'
        assert records[-1]['operation']['operation_id']==row['operation_id']
        assert records[-1]['operation']['attempt_count']==0
        assert records[-1]['operation']['wait_info']['local_remaining_ms']==120000
        await asyncio.sleep(.03)
        assert api[2].claims==[] and messages(api[1])==[]
        assert (await client.get(path()+'/'+row['operation_id']+'/events',headers=headers('bob'))).status_code==404
        retained=ChatRepository(api[1],api[3]).get(scope,row['operation_id'])
        assert retained['revision']==row['revision'] and retained['private_control']==row['private_control']
    run(scenario,api)


def test_snapshot_of_next_attempt_excludes_the_closed_previous_buffer(api,monkeypatch):
    second_ready=asyncio.Event()
    api[2].release=asyncio.Event()
    async def stream(claim):
        api[2].claims.append(claim)
        if len(api[2].claims)==1:
            yield {'type':'delta','text':'Anterior'}
            yield {'type':'error','category':'transport','status':503}
            return
        yield {'type':'delta','text':'🌍 nuevo'}
        second_ready.set()
        await api[2].release.wait()
        answer=copy.deepcopy(ANSWER);answer['answer']='🌍 nuevo'
        yield {'type':'candidate','result':answer,'finish_reason':'stop','usage':None}
    monkeypatch.setattr(api[2],'stream',stream)
    async def scenario(client):
        scope={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
        runtime=service(api[0],active=True)
        row,_=await runtime.open(scope,body())
        observer=None
        try:
            await until_state(client,path()+'/'+row['operation_id'],'waiting')
            api[3].advance(2)
            await asyncio.wait_for(second_ready.wait(),3)
            observer=runtime.events(scope,row['operation_id'])
            _,started=frame(await anext(observer))
            assert started['operation']['attempt_count']==2
            _,snapshot=frame(await anext(observer))
            assert snapshot['type']=='snapshot' and snapshot['text']=='🌍 nuevo'
            assert snapshot['seq']==1 and snapshot['offset']==8 and snapshot['number']==2
            assert snapshot['attempt_id']==api[2].claims[1]['attempt_id']
            assert snapshot['attempt_id']!=api[2].claims[0]['attempt_id']
            assert len(api[2].claims)==2 and messages(api[1])==[]
        finally:
            api[2].release.set()
            if observer is not None: await observer.aclose()
            await runtime.close()
    run(scenario,api)


def test_live_observer_after_over64_deltas_starts_at_full_snapshot_and_continues_same_attempt(api,monkeypatch):
    ready=asyncio.Event()
    api[2].release=asyncio.Event()
    answer=copy.deepcopy(ANSWER);answer['answer']='🌍'*100+' listo'
    async def stream(claim):
        api[2].claims.append(claim)
        for _ in range(100): yield {'type':'delta','text':'🌍'}
        ready.set()
        await api[2].release.wait()
        yield {'type':'delta','text':' listo'}
        yield {'type':'candidate','result':answer,'finish_reason':'stop','usage':None}
    monkeypatch.setattr(api[2],'stream',stream)
    async def scenario(client):
        scope={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
        runtime=service(api[0],active=True)
        row,created=await runtime.open(scope,body())
        assert created
        await asyncio.wait_for(ready.wait(),3)
        observer=runtime.events(scope,row['operation_id'])
        try:
            _,started=frame(await anext(observer))
            assert started['type']=='started' and started['operation']['state']=='active'
            identifier,snapshot=frame(await anext(observer))
            assert snapshot['type']=='snapshot'
            assert snapshot['text']=='🌍'*100 and snapshot['offset']==200 and snapshot['seq']==100
            assert snapshot['attempt_id']==row['current_attempt_id'] and snapshot['operation_id']==row['operation_id']
            assert identifier==row['operation_id']+':'+row['current_attempt_id']+':100'
            api[2].release.set()
            _,delta=frame(await asyncio.wait_for(anext(observer),3))
            assert delta['type']=='delta' and delta['text']==' listo'
            assert delta['seq']==101 and delta['offset']==200 and delta['attempt_id']==snapshot['attempt_id']
            await until_state(client,path()+'/'+row['operation_id'],'completed')
            assert len(api[2].claims)==1 and len(messages(api[1]))==2
        finally:
            api[2].release.set()
            await observer.aclose()
            await runtime.close()
    run(scenario,api)
