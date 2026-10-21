import asyncio
import io
import json
import threading
import time
from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from app.clients.chat_gateway import ChatGateway,diagnostic_scope
from app.core.chat_review import validate_draft,draft_schema,phase_messages,admission_tokens
from app.core.chat_resources import ChatResources, FLASH_TOKENIZER

PLAN={'claims':[{'claim':'The user greets us.','source_ids':[]}],'coverage':[],'risks':[],'uncertainties':[],'next_steps':[]}
FINAL={'schema_version':'1.0','basis':'greeting','status':'no_data','answer':[{'text':'Hola 😀'}],
       'scope':{'cloud':'azure','data_environment':'simulated'},'evidence':[],'metrics':[],
       'recommendations':[],'assumptions':[],'limitations':[],'next_actions':[]}
CONTEXT={'messages':[{'role':'system','content':'Synthetic'},{'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n{"question":"Hola"}'}],
         'financial_metrics_allowed':False,'authorized_evidence':[]}

def wire(value,finish='stop',usage=True):
    event={'choices':[{'index':0,'delta':{'content':value if isinstance(value,str) else json.dumps(value,ensure_ascii=True)},'finish_reason':finish}]}
    if usage:event['usage']={'prompt_tokens':10,'completion_tokens':5,'total_tokens':15,'cost':0.001}
    return ('data: '+json.dumps(event)+'\n\ndata: [DONE]\n\n').encode()

class Resources:
    manifest_bytes = b'{"v":4}'
    tokenizer_sha256 = FLASH_TOKENIZER['sha256']
    # Keep the real generation guard while simulating counting and transport.
    check_generation = ChatResources.check_generation
    def count(self,text):return len(text.encode())
    def check_messages(self,messages,schema):
        assert messages[0]==CONTEXT['messages'][0]
        assert all(item['role']=='user' for item in messages[1:])

def gateway(monkeypatch,responses):
    instance=ChatGateway(SimpleNamespace(llm_model='economicon-chat',litellm_base_url='http://synthetic.invalid/v1',litellm_api_key=SecretStr('synthetic')))
    instance.resources=Resources();requests=[];streams=[]
    class Stream(io.BytesIO):headers={'Content-Type':'text/event-stream','x-litellm-response-cost':'0.001'}
    def open(req,**kwargs):
        if streams:assert streams[-1].closed,'Draft transport must close before final admission.'
        requests.append(json.loads(req.data));stream=Stream(responses[len(requests)-1]);streams.append(stream);return stream
    monkeypatch.setattr(instance.client.transport,'open',open)
    return instance,requests,streams

def execute(instance,deadline=None):
    async def run():return [item async for item in instance(CONTEXT,deadline or time.time()+120)]
    return asyncio.run(run())

@pytest.mark.parametrize('field,value', [
    ('manifest_bytes', b'{"v":3}'),
    ('tokenizer_sha256', 'historical-tokenizer'),
])
def test_historical_resources_never_admit_draft(monkeypatch,field,value):
    instance,requests,streams=gateway(monkeypatch,[])
    setattr(instance.resources,field,value)
    with pytest.raises(ValueError,match='Historical chat resources are read-only'):
        execute(instance)
    assert requests == [] and streams == []

def test_private_plan_then_only_final_stream_and_aggregate_usage(monkeypatch,caplog):
    instance,requests,streams=gateway(monkeypatch,[wire(PLAN),wire(FINAL)])
    caplog.set_level('INFO',logger='app.clients.chat_gateway')
    with diagnostic_scope('11111111-1111-4111-8111-111111111111','22222222-2222-4222-8222-222222222222'):
        records=execute(instance)
    assert len(requests)==2 and [item['max_tokens'] for item in requests]==[1000,2200]
    assert all(item['num_retries']==0 for item in requests)
    assert all(item['temperature']==0 for item in requests)
    assert requests[0]['response_format']['json_schema']['name']=='PrivateAnswerPlan'
    assert 'UNTRUSTED_DRAFT_PLAN' in requests[1]['messages'][-1]['content']
    assert ''.join(item['text'] for item in records if item['type']=='delta')=='Hola 😀'
    assert sum(item['type']=='candidate' for item in records)==1
    assert not any(item['type']=='draft' for item in records)
    assert records[-1]['usage']['total_tokens']==30
    assert records[-1]['usage']['cost_usd']=='0.002'
    assert records[-1]['usage_report']['complete'] is True
    assert all(stream.closed for stream in streams)
    assert 'The user greets us.' not in caplog.text
    assert 'request_sha256' in caplog.text and 'input_tokens' in caplog.text

@pytest.mark.parametrize('plan,finish', [('not-json','stop'),(PLAN,'length'),({**PLAN,'extra':True},'stop'),
    ({**PLAN,'claims':[{'claim':'x','source_ids':['foreign']}]},'stop')])
def test_invalid_draft_never_emits_or_calls_final(monkeypatch,plan,finish):
    instance,requests,_=gateway(monkeypatch,[wire(plan,finish)])
    records=execute(instance)
    assert len(requests)==1 and [item['type'] for item in records]==['error']
    assert records[0]['status']==(502 if finish=='length' else 422)
    assert records[0]['category']==('incomplete' if finish=='length' else 'invalid_response')
    assert records[0]['usage_report']['observed']['total_tokens']==15

def test_final_failure_preserves_partial_draft_usage(monkeypatch):
    instance,requests,_=gateway(monkeypatch,[wire(PLAN),wire('bad-json',usage=False)])
    records=execute(instance)
    assert len(requests)==2 and records[-1]['type']=='error'
    assert records[-1]['usage'] is None
    assert records[-1]['usage_report']=={'observed':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15,'cost_usd':'0.001'},
        'complete':False,'attempted_legs':2,'reported_legs':1}

def test_preflight_token_failure_does_not_admit_final(monkeypatch):
    instance,requests,_=gateway(monkeypatch,[wire(PLAN)])
    original=instance.resources.check_messages
    def check(messages,schema):
        original(messages,schema)
        if 'FINAL_REVIEW_PHASE' in messages[-1]['content']:raise ValueError('budget')
    instance.resources.check_messages=check
    with pytest.raises(ValueError,match='budget'):execute(instance)
    assert len(requests)==1

def test_expired_attempt_never_admits_a_request(monkeypatch):
    instance,requests,_=gateway(monkeypatch,[])
    records=execute(instance,time.time()-1)
    assert requests==[] and records[-1]['category']=='timeout' and records[-1]['usage_report'] is None

def test_draft_schema_and_local_bounds_and_no_authority():
    assert validate_draft(PLAN,[]) is PLAN
    assert draft_schema([])['properties']['claims']['items']['properties']['source_ids']['maxItems']==0
    for plan in ({**PLAN,'coverage':['x'*201]},{**PLAN,'risks':['x']*4},{**PLAN,'uncertainties':[' ']},{**PLAN,'next_steps':['x'*201]},
                 {**PLAN,'claims':[{'claim':'x','source_ids':[]}]*7}):
        with pytest.raises(ValueError):validate_draft(plan,[])
    assert all(item['role']=='user' for item in phase_messages(CONTEXT['messages'],'final',PLAN)[1:])
    reserve=admission_tokens(len,CONTEXT['messages'],{'type':'object'},[])
    assert reserve['total_output_tokens']==3200
    assert reserve['total_input_reserved_tokens']>reserve['draft_input_tokens']


def test_deadline_between_draft_and_final_preserves_only_admitted_usage(monkeypatch):
    instance,requests,_=gateway(monkeypatch,[])
    calls=[];closed=[]
    def records(context,deadline,holder,cancelled):
        calls.append((context['_review_phase'],deadline))
        try:
            if context['_review_phase']=='draft':
                holder['attempted_legs']=1
                holder['usage']={'prompt_tokens':10,'completion_tokens':5,'total_tokens':15,'cost_usd':'0.001'}
                yield {'type':'draft','plan':PLAN,'usage':holder['usage']}
            else:
                holder['usage']=None
                yield {'type':'error','category':'timeout'}
        finally:closed.append(context['_review_phase'])
    monkeypatch.setattr(instance,'_records',records)
    result=execute(instance)
    assert requests==[] and len(calls)==2 and calls[0][1]==calls[1][1]
    assert closed==['draft','final']
    assert result[-1]['category']=='timeout' and result[-1]['usage_report']['attempted_legs']==1
    assert result[-1]['usage_report']['observed']['total_tokens']==15


@pytest.mark.parametrize('phase',['draft','final'])
def test_cancel_interrupts_active_leg_even_if_observational_logging_fails(monkeypatch,phase):
    instance,_,_=gateway(monkeypatch,[])
    started=threading.Event();released=threading.Event();cancel_flags=[];calls=[]
    def records(context,deadline,holder,cancelled):
        calls.append(context['_review_phase']);cancel_flags.append(cancelled)
        holder['attempted_legs']=len(calls)
        holder['usage']={'total_tokens':4}
        if context['_review_phase']=='draft' and phase=='final':
            yield {'type':'draft','plan':PLAN,'usage':holder['usage']};return
        holder['response']=object();started.set()
        assert released.wait(2)
        assert cancelled.is_set()
        return
        yield
    monkeypatch.setattr(instance,'_records',records)
    monkeypatch.setattr('app.clients.chat_gateway.interrupt',lambda response:released.set())
    def broken(*args,**kwargs):raise OSError('Synthetic logger failure')
    monkeypatch.setattr('app.clients.chat_gateway._diagnostic_logger.info',broken)
    async def run():
        async def consume():return [item async for item in instance(CONTEXT,time.time()+120)]
        task=asyncio.create_task(consume())
        assert await asyncio.to_thread(started.wait,1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):await task
    asyncio.run(run())
    assert released.is_set() and all(flag.is_set() for flag in cancel_flags)
    assert calls==(['draft'] if phase=='draft' else ['draft','final'])
