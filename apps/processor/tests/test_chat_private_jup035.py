"""Processor private HTTP authorization/replay/scoped claim before gateway."""
import asyncio
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import create_engine,text


KEY=b'jup035-synthetic-private-key-32-bytes-only'


def signed(method,path,body=b'',nonce=None,at=None):
    nonce=nonce or str(uuid4());at=str(int(time.time())) if at is None else str(at)
    message=f'chat-v2\n{method}\n{path}\n{at}\n{nonce}\n{hashlib.sha256(body).hexdigest()}'.encode()
    return {'X-Chat-Key-Id':'chat-v2','X-Chat-Time':at,'X-Chat-Nonce':nonce,
            'X-Chat-Signature':hmac.new(KEY,message,hashlib.sha256).hexdigest(),'Content-Type':'application/json'}


@pytest.fixture
def private(tmp_path,monkeypatch):
    from app import main
    application=getattr(main,'chat_app',main.app)
    engine=create_engine('sqlite:///'+str(tmp_path/'private.db'),connect_args={'check_same_thread':False})
    with engine.begin() as c:
        c.execute(text('CREATE TABLE conversations(id STRING PRIMARY KEY,tenant_id STRING,user_id STRING)'))
        c.execute(text('CREATE TABLE chat_operations(operation_id STRING PRIMARY KEY,tenant_id STRING,user_id STRING,conversation_id STRING,state STRING,current_attempt_id STRING,attempt_count INT,attempt_deadline FLOAT,private_control JSONB,input_hash STRING)'))
        c.execute(text("INSERT INTO conversations VALUES ('chat','tenant','alice')"))
        c.execute(text("INSERT INTO chat_operations VALUES ('op','tenant','alice','chat','active','attempt',1,:deadline,:control,'frozen-hash')"),
                  {'deadline':time.time()+120,'control':json.dumps({'boot_id':'synthetic-boot','capability':'synthetic-capability'})})
    monkeypatch.setattr(application.state,'chat_database',SimpleNamespace(engine=engine),raising=False)
    monkeypatch.setattr(application.state,'chat_signing_key',KEY,raising=False)
    monkeypatch.setattr(application.state,'chat_boot_id','synthetic-boot',raising=False)
    monkeypatch.setattr(application.state,'chat_prompt_version','synthetic-v2',raising=False)
    monkeypatch.setattr(application.state,'chat_nonces',{},raising=False)
    monkeypatch.setattr(application.state,'chat_attempts',{},raising=False)
    calls=[]
    async def gateway(context,deadline):
        calls.append(context)
        yield {'type':'delta','text':'Sin evidencia'}
        yield {'type':'candidate','result':{'synthetic':'candidate'},'finish_reason':'stop','usage':None}
    monkeypatch.setattr(application.state,'chat_gateway',gateway,raising=False)
    yield application,main.app,engine,calls
    engine.dispose()


def claim(**changes):
    return {'v':2,'tenant_id':'tenant','user_id':'alice','conversation_id':'chat','operation_id':'op',
            'attempt_id':'attempt','number':1,'deadline':time.time()+110,'boot_id':'synthetic-boot',
            'capability':'synthetic-capability','input_hash':'frozen-hash','context':{
                'prompt_version':'synthetic-v2','messages':[{'role':'user','content':'pregunta'}]},**changes}


def run(application,scenario):
    async def execute():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application),base_url='http://private') as c:
            await scenario(c)
    asyncio.run(execute())


def test_private_descriptor_requires_signature_and_echoes_authenticated_nonce(private):
    async def scenario(c):
        r=await c.get('/internal/chat/v2/descriptor')
        assert r.status_code==401,r.text
        headers=signed('GET','/internal/chat/v2/descriptor')
        r=await c.get('/internal/chat/v2/descriptor',headers=headers)
        assert r.status_code==200,r.text
        assert r.json()['boot_id']=='synthetic-boot'
        assert r.headers['X-Chat-Nonce']==headers['X-Chat-Nonce']
        signature=hmac.new(KEY,f"chat-v2-response\n{headers['X-Chat-Nonce']}\n200\n{hashlib.sha256(r.content).hexdigest()}".encode(),hashlib.sha256).hexdigest()
        assert hmac.compare_digest(signature,r.headers['X-Chat-Signature'])
        assert KEY.decode() not in r.text
    run(private[0],scenario)


@pytest.mark.parametrize('change',[{'user_id':'bob'},{'tenant_id':'other'},{'attempt_id':'old'},
                                  {'boot_id':'old-boot'},{'capability':'wrong'},{'input_hash':'changed'}])
def test_signed_claim_still_requires_exact_current_owned_operation(private,change):
    async def scenario(c):
        raw=json.dumps(claim(**change),separators=(',',':')).encode()
        r=await c.post('/internal/chat/v2/attempts',content=raw,headers=signed('POST','/internal/chat/v2/attempts',raw))
        assert r.status_code in [404,409],r.text
        assert private[3]==[]
    run(private[0],scenario)


def test_valid_claim_streams_once_and_replay_never_dispatches(private):
    async def scenario(c):
        raw=json.dumps(claim(),separators=(',',':')).encode()
        headers=signed('POST','/internal/chat/v2/attempts',raw)
        r=await c.post('/internal/chat/v2/attempts',content=raw,headers=headers)
        assert r.status_code==200,r.text
        assert r.headers['content-type'].startswith('application/x-ndjson')
        assert r.text.index('"delta"')<r.text.index('"candidate_end"')
        replay=await c.post('/internal/chat/v2/attempts',content=raw,headers=headers)
        assert replay.status_code in [401,409]
        new_nonce=await c.post('/internal/chat/v2/attempts',content=raw,headers=signed('POST','/internal/chat/v2/attempts',raw))
        assert new_nonce.status_code==409
        assert len(private[3])==1
    run(private[0],scenario)


def test_main_health_app_never_exposes_private_chat(private):
    async def scenario(c):
        r=await c.get('/internal/chat/v2/descriptor',headers=signed('GET','/internal/chat/v2/descriptor'))
        assert r.status_code==404,r.text
    run(private[1],scenario)


def test_required_result_is_owned_signed_correlated_and_single_use(private, monkeypatch):
    async def scenario(client):
        entered=asyncio.Event();continued=[]
        assistant={'action': 'search', 'query': 'Synthetic policy','calculations':[]}
        async def gateway(context, deadline, *, tool_result):
            yield {'type':'tool_call','assistant':assistant}
            entered.set()
            result=await tool_result(assistant)
            continued.append(result)
            yield {'type':'candidate','result':{'synthetic':'candidate'},'finish_reason':'stop'}
        gateway.requires_tool_result=True
        monkeypatch.setattr(private[0].state,'chat_gateway',gateway)
        payload=claim(context={'prompt_version':'synthetic-v2','messages':[{'role':'user','content':'Synthetic'}],
            'tool_protocol':'structured-documentation-v3','financial_metrics_allowed':False})
        raw=json.dumps(payload).encode()
        task=asyncio.create_task(client.post('/internal/chat/v2/attempts',content=raw,
            headers=signed('POST','/internal/chat/v2/attempts',raw)))
        try:
            await asyncio.wait_for(entered.wait(),2)
            endpoint='/internal/chat/v2/attempts/attempt/tool-result'
            from app.core.chat_resources import validate_search_call
            result={'tool_call_id':validate_search_call(assistant)[0],'content':'{"evidence":[],"omissions":[]}', 'variable_tokens':0}
            async def post(claim_value, result_value, authenticated=True):
                body=json.dumps({'v':2,'claim':claim_value,'tool_result':result_value}).encode()
                return await client.post(endpoint,content=body,
                    headers=signed('POST',endpoint,body) if authenticated else {})
            assert (await post(payload,result,False)).status_code==401
            assert (await post({**payload,'tenant_id':'other'},result)).status_code==404
            assert (await post({**payload,'user_id':'other'},result)).status_code==404
            assert (await post({**payload,'deadline':time.time()-1},result)).status_code in (404,409)
            assert (await post(payload,{**result,'tool_call_id':'unknown'})).status_code==409
            assert (await post(payload,{**result,'content':'{"evidence":[{"kind":"cost_query"}],"omissions":[]}'})).status_code==409
            assert continued==[]
            assert (await post(payload,result)).status_code==200
            assert (await post(payload,result)).status_code==409
            response=await asyncio.wait_for(task,2)
            assert '"tool_call"' in response.text and '"candidate_end"' in response.text
            assert continued==[result]
        finally:
            task.cancel();await asyncio.gather(task,return_exceptions=True)
    run(private[0],scenario)


@pytest.mark.parametrize('tamper',['signature','timestamp','body','key_id','nonce'])
def test_private_authentication_rejects_tampering_before_dispatch(private,tamper):
    async def scenario(c):
        raw=json.dumps(claim(),separators=(',',':')).encode()
        headers=signed('POST','/internal/chat/v2/attempts',raw)
        if tamper=='signature': headers['X-Chat-Signature']='0'*64
        if tamper=='timestamp': headers=signed('POST','/internal/chat/v2/attempts',raw,at=int(time.time())-31)
        if tamper=='body': raw+=b' '
        if tamper=='key_id': headers['X-Chat-Key-Id']='unknown'
        if tamper=='nonce': headers['X-Chat-Nonce']='not-a-uuid'
        result=await c.post('/internal/chat/v2/attempts',content=raw,headers=headers)
        assert result.status_code==401,result.text
        assert private[3]==[] and KEY.decode() not in result.text
    run(private[0],scenario)


def test_descriptor_nonce_replay_is_rejected(private):
    async def scenario(c):
        headers=signed('GET','/internal/chat/v2/descriptor')
        assert (await c.get('/internal/chat/v2/descriptor',headers=headers)).status_code==200
        assert (await c.get('/internal/chat/v2/descriptor',headers=headers)).status_code==401
        assert private[3]==[]
    run(private[0],scenario)


@pytest.mark.parametrize('change',[{'number':2},{'deadline':time.time()-1},{'context':{'prompt_version':'wrong-version','messages':[]}}])
def test_current_scope_also_requires_number_deadline_and_prompt(private,change):
    async def scenario(c):
        raw=json.dumps(claim(**change),separators=(',',':')).encode()
        result=await c.post('/internal/chat/v2/attempts',content=raw,headers=signed('POST','/internal/chat/v2/attempts',raw))
        assert result.status_code in (404,409),result.text
        assert private[3]==[]
    run(private[0],scenario)


def test_stopped_sql_claim_cannot_emit_a_complete_candidate(private,monkeypatch):
    async def scenario(c):
        entered=asyncio.Event();release=asyncio.Event()
        async def blocked_gateway(context,deadline):
            private[3].append(context)
            yield {'type':'delta','text':'Provisional'}
            entered.set()
            await release.wait()
            yield {'type':'candidate','result':{'synthetic':'candidate'},'finish_reason':'stop','usage':None}
        monkeypatch.setattr(private[0].state,'chat_gateway',blocked_gateway)
        raw=json.dumps(claim(),separators=(',',':')).encode()
        task=asyncio.create_task(c.post('/internal/chat/v2/attempts',content=raw,headers=signed('POST','/internal/chat/v2/attempts',raw)))
        await asyncio.wait_for(entered.wait(),2)
        with private[2].begin() as connection:
            connection.execute(text("UPDATE chat_operations SET state='cancelled' WHERE operation_id='op'"))
        release.set()
        response=await task
        assert response.status_code==200 and '"delta"' in response.text
        assert '"candidate_end"' not in response.text
        assert len(private[3])==1
    run(private[0],scenario)


@pytest.mark.parametrize('cancel_first',[False,True])
def test_diagnostic64_context_is_owned_concurrent_and_cleaned_after_cancel(private,monkeypatch,cancel_first):
    from app.clients import chat_gateway as module
    # A missing context is an assertion failure about absent behavior, not an
    # import/setup failure. Existing gateways retain their two-argument signature.
    operation_ids=[str(uuid4()),str(uuid4())];attempt_ids=[str(uuid4()),str(uuid4())]
    with private[2].begin() as connection:
        connection.execute(text('DELETE FROM chat_operations'))
        for op,attempt in zip(operation_ids,attempt_ids):
            connection.execute(text('INSERT INTO chat_operations VALUES (:op,\'tenant\',\'alice\',\'chat\',\'active\',:attempt,1,:deadline,:control,\'frozen-hash\')'),
                {'op':op,'attempt':attempt,'deadline':time.time()+120,
                 'control':json.dumps({'boot_id':'synthetic-boot','capability':'synthetic-capability'})})
    async def scenario(client):
        entered=[asyncio.Event(),asyncio.Event()];release=asyncio.Event();seen=[];closed=[]
        def current():
            context=getattr(module,'_diagnostic_context',None)
            return None if context is None else context.get()
        async def gateway(context,deadline):
            i=context['messages'][0]['index']
            try:
                seen.append((i,await asyncio.to_thread(current)))
                entered[i].set()
                await release.wait()
                seen.append((i,await asyncio.to_thread(current)))
                yield {'type':'error','category':'invalid_response','status':422}
            finally:closed.append(i)
        monkeypatch.setattr(private[0].state,'chat_gateway',gateway)
        tasks=[]
        for i in range(2):
            payload=claim(operation_id=operation_ids[i],attempt_id=attempt_ids[i],
                context={'prompt_version':'synthetic-v2','messages':[{'role':'user','content':'Synthetic','index':i}]})
            raw=json.dumps(payload,separators=(',',':')).encode()
            tasks.append(asyncio.create_task(client.post('/internal/chat/v2/attempts',content=raw,
                headers=signed('POST','/internal/chat/v2/attempts',raw))))
        await asyncio.wait_for(asyncio.gather(*(event.wait() for event in entered)),2)
        try:
            if cancel_first:
                tasks[0].cancel();await asyncio.gather(tasks[0],return_exceptions=True)
            release.set()
            responses=await asyncio.gather(*tasks,return_exceptions=True)
            for i,response in enumerate(responses):
                if cancel_first and i==0:continue
                assert response.status_code==200 and '"category":"invalid_response"' in response.text
            expected={i:(operation_ids[i],attempt_ids[i]) for i in range(2)}
            assert seen and all(value==expected[i] for i,value in seen),'Context missing or crossed between streams/threads'
            assert sorted(closed)==[0,1]
            assert current() is None and await asyncio.to_thread(current) is None
            assert all(entry['task'] is None for entry in private[0].state.chat_attempts.values())
        finally:
            release.set()
            for task in tasks:
                if not task.done():task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
    run(private[0],scenario)


@pytest.mark.parametrize('terminal',['candidate','error','cancel','ownership_lost','exception'])
def test_diagnostic64_scope_closes_in_actual_consumer_task_on_every_exit(private,monkeypatch,terminal):
    from starlette.requests import Request
    from app.clients import chat_gateway as module
    operation_id=str(uuid4());attempt_id=str(uuid4());closed=[]
    with private[2].begin() as connection:
        connection.execute(text('UPDATE chat_operations SET operation_id=:op,current_attempt_id=:attempt'),
                           {'op':operation_id,'attempt':attempt_id})
    async def gateway(context,deadline):
        try:
            yield {'type':'delta','text':'Synthetic delta'}
            if terminal=='exception':raise RuntimeError('Synthetic gateway failure')
            yield ({'type':'candidate','result':{'synthetic':'candidate'},'finish_reason':'stop','usage':None}
                   if terminal=='candidate' else {'type':'error','status':422,'category':'invalid_response'})
        finally:closed.append(True)
    monkeypatch.setattr(private[0].state,'chat_gateway',gateway)
    async def scenario():
        request=Request({'type':'http','method':'POST','path':'/internal/chat/v2/attempts','headers':[]})
        request.state.chat_body=json.dumps(claim(operation_id=operation_id,attempt_id=attempt_id)).encode()
        request.state.chat_nonce=str(uuid4())
        route=next(route for route in private[0].routes if route.path=='/internal/chat/v2/attempts')
        # Unit-level consumer invokes the actual endpoint/stream after the SQL
        # ownership checks; the authentication tests remain separate and fixed.
        response=await route.endpoint(request);body=response.body_iterator
        diagnostic=module._diagnostic_context
        assert diagnostic.get() is None
        try:
            first=await body.__anext__();assert json.loads(first)['type']=='delta'
            assert diagnostic.get()==(operation_id,attempt_id)
            if terminal=='cancel':await body.aclose()
            else:
                if terminal=='ownership_lost':
                    with private[2].begin() as connection:
                        connection.execute(text('UPDATE chat_operations SET state=\'cancelled\''))
                records=[json.loads(chunk) async for chunk in body]
                if terminal=='candidate':assert records[-1]['type']=='candidate_end'
                if terminal=='error':assert records[-1]['category']=='invalid_response'
                if terminal=='exception':assert records[-1]['category']=='invalid_private_response'
                if terminal=='ownership_lost':assert records==[]
            assert diagnostic.get() is None,'Diagnostic scope leaked in the actual stream consumer task'
            assert closed==[True],'Gateway close was deferred beyond the stream consumer exit'
            assert all(entry['task'] is None for entry in private[0].state.chat_attempts.values())
        finally:await body.aclose()
    asyncio.run(scenario())
