"""Synthetic provider wire; no paid calls, model decisions are controlled."""
import asyncio
import copy
import io
import json
import threading
import time
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.clients.chat_gateway import ChatGateway
from test_chat_gateway_jup035 import ANSWER, _provider, request_provider
from test_chat_private_jup035 import private, claim, run, signed


TOOL = {'id': 'call-auto', 'type': 'function', 'function': {
    'name': 'search_documentation', 'arguments': '{"query":"Synthetic policy"}'}}

DECISION={'action':'search','query':'Synthetic policy'}


def decision_id():
    from app.core.chat_resources import validate_search_call
    return validate_search_call(DECISION)[0]


def decision_delta(search):
    return {'content':json.dumps(DECISION if search else {'action':'none','query':None,'comparisons':[],'calculations':[]})}


def retrieval_context():
    return {'tool_protocol':'server-documentation-v4','financial_metrics_allowed':False,
            'messages':[{'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':'Synthetic policy'})}],
            'authorized_evidence':[]}


def empty_result():
    return {'tool_call_id':decision_id(),'content':'{"evidence":[],"omissions":[]}','variable_tokens':0}


@pytest.mark.parametrize('with_source',[False,True])
def test_final_schema_contains_only_effective_authenticated_evidence(monkeypatch,with_source):
    source={'id':'corpus:current:0','kind':'corpus','title':'Current source','source':'Manual','content':'A supported threshold of 17%.'}
    gateway,requests=provider(monkeypatch,[wire({'content':json.dumps(request_provider())})])
    async def result(control):
        return {**empty_result(),'content':json.dumps({'evidence':[source] if with_source else [],'omissions':[]})}
    async def exercise():return [r async for r in gateway(retrieval_context(),time.time()+60,tool_result=result)]
    records=asyncio.run(exercise())
    assert records[-1]['type']=='candidate' and len(requests)==1
    assert requests[0]['reasoning']=={'effort':'high','exclude':True}
    assert requests[0]['max_tokens']==3200
    assert requests[0]['timeout']<=60 and requests[0]['num_retries']==0
    schema=requests[0]['response_format']['json_schema']['schema']
    if with_source:
        choices=schema['$defs']['Evidence']['anyOf']
        assert len(choices)==1
        assert {k:v['const'] for k,v in choices[0]['properties'].items() if k!='support_quote'}=={k:source[k] for k in ('id','kind','title','source')}
        assert schema['$defs']['SourceQuantity']['properties']['quantity']['enum']==['document:corpus:current:0:17 %']
    else:
        assert schema['properties']['evidence']['maxItems']==0
        assert 'status' not in schema['properties'] and 'status' not in schema['required']
    for branch in schema.get('anyOf',[schema]):assert branch['properties']['metrics']['maxItems']==0
    for field in ('estimated_savings','currency'):
        assert schema['$defs']['Recommendation']['properties'][field]=={'type':'null'}


def test_final_failure_diagnostic_never_contains_candidate_or_secret(monkeypatch,caplog):
    gateway,requests=provider(monkeypatch,[wire({'content':'{"answer":[{"text":"PRIVATE CANDIDATE'},'length')])
    records=list(gateway._records(retrieval_context(),time.time()+60,{},threading.Event()))
    assert records[-1]=={'type':'error','status':502,'category':'incomplete'}
    assert len(requests)==1
    diagnostic=next(json.loads(r.message) for r in caplog.records if 'chat_gateway_diagnostic' in r.message)
    assert diagnostic['category']=='incomplete' and diagnostic['finish_reason']=='length'
    assert all(marker not in caplog.text for marker in ('PRIVATE CANDIDATE','Synthetic policy','Bearer','synthetic.invalid'))


@pytest.mark.parametrize('failure',['native','invalid_final','eof','length','wrong_id','429'])
def test_single_generation_failures_never_retry_or_change_provider(monkeypatch,failure):
    from urllib.error import HTTPError
    final=wire({'content':json.dumps(request_provider())})
    if failure=='native':final=wire({'tool_calls':[{'index':0,**TOOL},{'index':1,**TOOL}]},'tool_calls')
    if failure=='invalid_final':final=wire({'content':'{"answer":"not strict"}'})
    if failure=='eof':final=final.replace(b'data: [DONE]\n\n',b'')
    if failure=='length':final=wire({'content':'{"answer":['},'length')
    if failure=='429':final=HTTPError('http://synthetic.invalid',429,'Synthetic',{'Retry-After':'17'},io.BytesIO())
    gateway,requests=provider(monkeypatch,[final]);searches=[]
    async def result(control):
        assert not requests
        searches.append(control)
        return {**empty_result(),'tool_call_id':'wrong' if failure=='wrong_id' else decision_id()}
    async def exercise():return [record async for record in gateway(retrieval_context(),time.time()+60,tool_result=result)]
    if failure=='wrong_id':
        with pytest.raises(ValueError,match='correlation'):asyncio.run(exercise())
        assert requests==[]
    else:
        records=asyncio.run(exercise())
        assert records[-1]['type']=='error' and not any(r['type']=='candidate' for r in records)
        assert len(requests)==1
        assert requests[0]['num_retries']==0 and requests[0]['provider']=={'order':['deepinfra/fp4'],'allow_fallbacks':False,'require_parameters':True}
    assert searches==[DECISION]


@pytest.mark.parametrize('phase',['retrieval','generation'])
def test_cancellation_stops_current_phase_and_preserves_deadline(monkeypatch,phase):
    gateway,requests=provider(monkeypatch,[]);entered=threading.Event();stopped=threading.Event();seen=[]
    deadline=time.time()+60
    def records(context,limit,holder,cancelled,choice=None):
        seen.append(limit);entered.set()
        assert cancelled.wait(2)
        stopped.set()
        yield from ()
    monkeypatch.setattr(gateway,'_records',records)
    async def result(control):
        if phase=='retrieval':
            entered.set()
            try:await asyncio.Event().wait()
            finally:stopped.set()
        return empty_result()
    async def exercise():
        async def consume():return [r async for r in gateway(retrieval_context(),deadline,tool_result=result)]
        task=asyncio.create_task(consume())
        assert await asyncio.to_thread(entered.wait,2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):await task
        assert await asyncio.to_thread(stopped.wait,2)
    asyncio.run(exercise())
    assert seen==([] if phase=='retrieval' else [deadline]) and requests==[]


def test_retrieval_does_not_reset_attempt_deadline(monkeypatch):
    gateway,requests=provider(monkeypatch,[]);deadline=time.time()+60
    async def result(control):
        monkeypatch.setattr(time,'time',lambda:deadline-4)
        return empty_result()
    async def exercise():return [r async for r in gateway(retrieval_context(),deadline,tool_result=result)]
    assert asyncio.run(exercise())[-1]=={'type':'error','category':'timeout'}
    assert requests==[]


@pytest.mark.parametrize('legacy',['required-documentation-v1','structured-documentation-v3'])
def test_legacy_protocol_cannot_silently_become_direct(monkeypatch,legacy):
    gateway,requests=provider(monkeypatch,[])
    async def exercise():return [r async for r in gateway({'tool_protocol':legacy},time.time()+60)]
    assert asyncio.run(exercise())==[{'type':'error','status':422,'category':'invalid_response'}]
    assert requests==[]


def test_private_endpoint_hmac_retrieval_then_one_final(private,monkeypatch):
    gateway,requests=provider(monkeypatch,[wire({'content':json.dumps(request_provider())},tokens=24)])
    monkeypatch.setattr(private[0].state,'chat_gateway',gateway)
    async def scenario(client):
        payload=claim(context={'prompt_version':'synthetic-v2',**retrieval_context()})
        raw=json.dumps(payload).encode()
        task=asyncio.create_task(client.post('/internal/chat/v2/attempts',content=raw,headers=signed('POST','/internal/chat/v2/attempts',raw)))
        try:
            for _ in range(200):
                pending=[entry for entry in private[0].state.chat_attempts.values() if entry['tool_future'] is not None]
                if pending:break
                await asyncio.sleep(.005)
            assert pending and requests==[]
            endpoint='/internal/chat/v2/attempts/attempt/tool-result'
            data=json.dumps({'v':2,'claim':payload,'tool_result':empty_result()}).encode()
            reply=await client.post(endpoint,content=data,headers=signed('POST',endpoint,data))
            assert reply.status_code==200,reply.text
            response=await asyncio.wait_for(task,3)
            records=[json.loads(line) for line in response.text.splitlines()]
            assert records[-1]['type']=='candidate_end',response.text
            assert records[-1]['usage']['total_tokens']==24
            assert sum(r['type']=='tool_call' for r in records)==1 and len(requests)==1
        finally:
            task.cancel();await asyncio.gather(task,return_exceptions=True)
    run(private[0],scenario)






def wire(delta, finish='stop', tokens=12):
    event = {'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}],
             'usage': {'prompt_tokens': tokens-2, 'completion_tokens': 2,
                       'total_tokens': tokens, 'cost': .001}}
    return ('data: '+json.dumps(event)+'\n\ndata: [DONE]\n\n').encode()




def provider(monkeypatch, responses, read_size=7):
    gateway = ChatGateway(SimpleNamespace(llm_model='economicon-chat',
        litellm_base_url='http://synthetic.invalid/v1', litellm_api_key=SecretStr('synthetic')))
    requests = []
    class Response(io.BytesIO):
        headers = {'Content-Type': 'text/event-stream'}
        def read1(self, size=-1):
            return super().read1(min(size, read_size))  # split UTF-8/SSE/JSON on real byte boundaries
    def opened(req, **kwargs):
        requests.append(json.loads(req.data))
        response = responses[len(requests)-1]
        if isinstance(response, Exception): raise response
        return Response(response)
    monkeypatch.setattr(gateway.client.transport, 'open', opened)
    return gateway, requests
