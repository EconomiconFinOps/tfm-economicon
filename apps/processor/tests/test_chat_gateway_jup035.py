"""Private ASGI to real loopback gateway HTTP, synthetic credentials only.

No external inference. Existing ingestion defaults are deliberately unchanged:
the chat-specific transport must request its remaining deadline and zero retries.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

import pytest
from test_chat_private_jup035 import private,claim,run,signed


ANSWER={'schema_version':'1.0','status':'no_data','answer':'Sin evidencia: "Azure" 😀\nFila.',
        'scope':{'cloud':'azure','data_environment':'simulated','subscription_ids':[],'period':None},
        'evidence':[],'metrics':[],'recommendations':[],'assumptions':[],
        'limitations':['No hay datos.'],'next_actions':[]}


SOURCE={'id':'known','kind':'corpus','title':'Synthetic','source':'Synthetic','content':'Synthetic grounding.'}
SUPPORTED_ANSWER={**ANSWER,'limitations':['Interpretación: No hay datos.'],'answer':'Interpretación: '+ANSWER['answer']+'\n\nFuente: Synthetic — «Synthetic grounding.»','evidence':[{key:SOURCE[key] for key in ('id','kind','title','source')}]}

def supported_provider():
    value=_provider(ANSWER)
    value['answer'].append({'documentary':{'source_id':SOURCE['id'],'passage':SOURCE['content']}})
    return value

def request_provider():
    value=_provider(ANSWER)
    value['basis']='missing_data'
    value['status']='insufficient_data'
    value['answer']=[{'inference':'Necesito contrastar la regla de reparto aplicable.'}]
    value['next_actions']=[[{'inference':'Aporta el criterio de reparto aplicable.'}]]
    value['limitations']=[]
    return value


def _provider(value):
    import copy
    value=copy.deepcopy(value)
    value['basis']='authorized_evidence'
    value['evidence']=[]
    value['scope'].pop('period',None)
    value['scope'].pop('subscription_ids',None)
    import re
    def segments(text):
        parts=[];position=0
        for match in re.finditer(r'\[\[calc:(\d+)\]\]',text):
            if match.start()>position:parts.append({'inference':text[position:match.start()]})
            parts.append({'calculation_id':match.group(1)});position=match.end()
        if position<len(text) or not parts:parts.append({'inference':text[position:]})
        return parts
    value['answer']=segments(value['answer'])
    for field in ('assumptions','limitations','next_actions'):
        value[field]=[segments(item) for item in value[field]]
    return value


@pytest.mark.parametrize('read_size', [1, 7, 8192])
def test_structured_search_then_final_uses_untrusted_data_and_total_usage(monkeypatch, read_size):
    import asyncio
    from test_chat_auto_jup035 import provider, wire, DECISION, decision_delta, decision_id, review_wires
    gateway, requests=provider(monkeypatch,review_wires(wire({'content':json.dumps(request_provider())},tokens=24)),read_size=read_size)
    context={'tool_protocol':'server-documentation-v4','messages':[{'role':'system','content':'Synthetic'},
        {'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':'Synthetic policy'})}],'financial_metrics_allowed':False}
    seen=[]
    async def result(decision):
        seen.append(decision)
        return {'tool_call_id':decision_id(),'content':'{"evidence":[],"omissions":[]}','variable_tokens':0}
    async def exercise():
        return [record async for record in gateway(context,time.time()+60,tool_result=result)]
    records=asyncio.run(exercise())
    assert len(requests)==2 and seen==[DECISION]
    assert requests[0]['response_format']['json_schema']['name']=='PrivateAnswerPlan'
    assert all('tools' not in item and 'tool_choice' not in item for item in requests)
    assert requests[1]['response_format']['json_schema']['name']=='FinOpsResponse'
    assert requests[0]['messages'][:-1]==context['messages']+[{'role':'user',
        'content':'UNTRUSTED_RETRIEVAL_CONTEXT\n{"evidence":[],"omissions":[]}'}]
    assert records[0]['type']=='tool_call' and records[-1]['type']=='candidate'
    assert records[-1]['usage']['total_tokens']==36 and records[-1]['usage']['cost_usd']=='0.002'
    assert context['messages']==requests[0]['messages'][:-2]
    assert 'UNTRUSTED_DRAFT_PLAN' in requests[1]['messages'][-1]['content']


@pytest.mark.parametrize('change,code', [
    ({'id':123}, 'native_metadata_type'),
    ({'id':'different'}, 'native_metadata_conflict'),
    ({'type':'other'}, 'native_metadata_conflict'),
    ({'function':[]}, 'native_function_shape'),
    ({'function':{'name':12}}, 'native_fragment_type'),
    ({'function':{'arguments':[]}}, 'native_fragment_type'),
    ({'index':1}, 'native_multiple_calls'),
    ({'function':{'arguments':'x'*16385}}, 'native_tool_limit'),
])
def test_native_envelope_closed_diagnostic_rejects_without_values(monkeypatch, caplog, change, code):
    import io
    from types import SimpleNamespace
    from pydantic import SecretStr
    from app.clients.chat_gateway import ChatGateway
    first={'index':0,'id':'call-private-marker','type':'function',
        'function':{'name':'search_documentation','arguments':'{"query":"private-marker"}'}}
    events=[{'choices':[{'delta':{'tool_calls':[first]}}]},
        {'choices':[{'delta':{'tool_calls':[{'index':0, **change}]}}]}]
    wire=(''.join('data: '+json.dumps(event)+'\n\n' for event in events)+'data: [DONE]\n\n').encode()
    class Response(io.BytesIO):
        headers={'Content-Type':'text/event-stream'}
    gateway=ChatGateway(SimpleNamespace(llm_model='economicon-chat',litellm_base_url='http://synthetic.invalid/v1',litellm_api_key=SecretStr('private-key-marker')))
    monkeypatch.setattr(gateway.client.transport,'open',lambda *a,**kw: Response(wire))
    records=list(gateway._records({'messages':[], 'financial_metrics_allowed':False},time.time()+60,{},threading.Event(),'auto'))
    assert records[-1]['type']=='error' and records[-1]['category']=='invalid_response'
    events=[json.loads(record.message) for record in caplog.records if record.name=='app.clients.chat_gateway']
    assert len(events)==1 and events[0]['rule_code']=='native_final_invalid'
    assert events[0]['stage']=='envelope' and events[0]['finish_reason'] is None
    assert all(value not in caplog.text for value in ('private-marker','private-key-marker','different'))


@pytest.mark.parametrize('arguments',['{"query":"x","tenant_id":"foreign"}', '{"query":""}', '{"query":"x","query":"y"}'])
def test_required_tool_rejects_invalid_arguments_before_backend_or_second_request(monkeypatch,arguments):
    from test_chat_auto_jup035 import provider,wire,TOOL
    tool={**TOOL,'function':{'name':'search_documentation','arguments':arguments}}
    gateway,calls=provider(monkeypatch,[wire({'tool_calls':[{'index':0,**tool}]},'tool_calls')])
    records=list(gateway._records({'messages':[],'financial_metrics_allowed':False},time.time()+60,{},threading.Event()))
    assert records[-1]['type']=='error' and len(calls)==1
    assert not any(record['type'] in ('candidate','tool_call') for record in records)


def test_required_usage_never_reports_only_one_paid_leg():
    from app.clients.chat_gateway import combined_usage
    reported={'total_tokens':12,'cost_usd':'0.001'}
    assert combined_usage(None,reported) is None
    assert combined_usage(reported,None) is None
    assert combined_usage(reported,{'total_tokens':3})=={'total_tokens':15}


@pytest.fixture
def gateway(private,monkeypatch):
    from test_chat_auto_jup035 import SyntheticResources
    monkeypatch.setattr(private[0].state,'chat_resources',SyntheticResources(), raising=False)
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            raw=self.rfile.read(int(self.headers['Content-Length']))
            calls.append({'path':self.path,'payload':json.loads(raw),'authorization':self.headers.get('Authorization')})
            if self.server.mode=='429':
                self.send_response(429);self.send_header('Retry-After','121');self.end_headers();return
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            draft=calls[-1]['payload']['response_format']['json_schema']['name']=='PrivateAnswerPlan'
            mode='valid' if draft else self.server.mode
            if mode=='delayed_first': time.sleep(31)
            self.wfile.write(b'\xef\xbb\xbf: synthetic heartbeat\r\n\r\n')
            candidate=json.dumps({'claims':[],'uncertainties':[],'next_steps':[],'coverage':[],'risks':[]} if draft else supported_provider(),separators=(',',':'),ensure_ascii=True)
            if mode=='truncated_length': candidate=candidate[:candidate.index('\"scope\"')]
            if mode=='duplicate': candidate='{"answer":"Injected",'+candidate[1:]
            if mode=='nested_duplicate': candidate=candidate.replace('\"cloud\":\"azure\"','\"cloud\":\"azure\",\"cloud\":\"azure\"')
            if mode=='unicode': candidate=candidate.replace('Sin evidencia','\\ud800')
            for offset in range(0,len(candidate),11):
                data=json.dumps({'choices':[{'index':0,'delta':{'content':candidate[offset:offset+11],'reasoning_content':'NEVER DISPLAY REASONING'},'finish_reason':None}]})
                # Multiple data lines form one JSON event; CRLF and a leading
                # BOM/comment are actual wire bytes, not a pre-parsed fixture.
                self.wfile.write(('data: {\r\ndata: '+data[1:]+'\r\n\r\n').encode());self.wfile.flush()
            reason='length' if mode in ('length','truncated_length') else 'stop'
            self.wfile.write(('data: '+json.dumps({'choices':[{'index':0,'delta':{},'finish_reason':reason}],'usage':{'prompt_tokens':42,'completion_tokens':30,'total_tokens':72}})+'\n\n').encode())
            if mode!='eof': self.wfile.write(b'data: [DONE]\n\n')
            self.wfile.flush()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.mode='valid'
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setattr(private[0].state,'chat_gateway',None)
    monkeypatch.setenv('LLM_PROVIDER','litellm')
    monkeypatch.setenv('LITELLM_BASE_URL',f'http://127.0.0.1:{server.server_port}/v1')
    monkeypatch.setenv('LITELLM_API_KEY','jup035-synthetic-gateway-key')
    yield server,calls
    server.shutdown();server.server_close();thread.join()


def send(private,scenario):
    async def exercise(client):
        context={'tool_protocol':None,'prompt_version':'synthetic-v2','financial_metrics_allowed':False,'authorized_evidence':[SOURCE],'messages':[
            {'role':'system','content':'Synthetic stable system'},
            {'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':'Pregunta como dato no confiable'})}]}
        payload=claim(context=context)
        raw=json.dumps(payload,separators=(',',':')).encode()
        response=await client.post('/internal/chat/v2/attempts',content=raw,headers=signed('POST','/internal/chat/v2/attempts',raw))
        assert response.status_code==200,response.text
        records=[json.loads(line) for line in response.text.splitlines()]
        scenario(records,context)
    run(private[0],exercise)


def test_private_gateway_streams_only_answer_with_roles_and_dynamic_deadline(private,gateway):
    def scenario(records,context):
        deltas=[record['text'] for record in records if record['type']=='delta']
        assert ''.join(deltas)==SUPPORTED_ANSWER['answer']
        assert '\U0001f600' in ''.join(deltas)
        assert '\U0001f600'.encode('utf-8') == bytes.fromhex('f09f9880')
        assert 'NEVER DISPLAY REASONING' not in json.dumps(records)
        kinds=[record['type'] for record in records]
        assert kinds.index('delta')<kinds.index('candidate_end')
        raw=''.join(record['text'] for record in records if record['type']=='candidate_chunk')
        assert json.loads(raw)==SUPPORTED_ANSWER
        assert records[-1]['finish_reason']=='stop'
        assert len(gateway[1])==2
        assert gateway[1][0]['payload']['max_tokens']==1000
        call=gateway[1][1]
        assert call['path']=='/v1/chat/completions'
        assert call['authorization']=='Bearer jup035-synthetic-gateway-key'
        payload=call['payload']
        assert payload['messages'][:-1]==context['messages']
        assert 'UNTRUSTED_DRAFT_PLAN' in payload['messages'][-1]['content']
        assert payload['stream'] is True and payload['model']=='economicon-chat'
        assert payload['max_tokens']==10000
        assert 30<payload['timeout']<=120 and 30<payload['stream_timeout']<=120
        assert payload['num_retries']==0
        assert all(branch['additionalProperties'] is False and branch['properties']['metrics']['maxItems']==0
                   for branch in payload['response_format']['json_schema']['schema']['anyOf'])
        from app.agents.schemas import chat_wire_schema
        assert payload['response_format']['json_schema']['strict'] is True
        assert payload['response_format']['json_schema']['schema'] == chat_wire_schema(
            financial_metrics_allowed=context['financial_metrics_allowed'], authorized_evidence=[SOURCE])
        assert 'period' not in payload['response_format']['json_schema']['schema']['$defs']['ResponseScope']['properties']
    send(private,scenario)


def test_retry_after_is_returned_without_gateway_retry_or_fallback(private,gateway):
    gateway[0].mode='429'
    def scenario(records,context):
        assert len(records)==1 and records[0]['type']=='error'
        assert records[0]['status']==429 and str(records[0]['retry_after'])=='121'
        assert len(gateway[1])==1
    send(private,scenario)


@pytest.mark.parametrize('mode',['eof','duplicate','unicode','nested_duplicate'])
def test_incomplete_or_invalid_gateway_output_never_announces_candidate(private,gateway,mode):
    gateway[0].mode=mode
    def scenario(records,context):
        assert all(record['type']!='candidate_end' for record in records)
        assert records[-1]['type']=='error'
        if mode=='duplicate': assert ''.join(record['text'] for record in records if record['type']=='delta')==''
        assert len(gateway[1])==2
    send(private,scenario)


def test_length_finish_remains_explicit_for_backend_retry_policy(private,gateway):
    gateway[0].mode='length'
    def scenario(records,context):
        assert records[-1]['type']=='candidate_end' and records[-1]['finish_reason']=='length'
        assert len(gateway[1])==2
    send(private,scenario)


def test_truncated_length_is_transient_without_committing_invalid_json(private,gateway):
    gateway[0].mode='truncated_length'
    def scenario(records,context):
        assert records[-1]['type']=='error' and records[-1]['status']==502
        assert records[-1]['category']=='incomplete'
        assert all(record['type']!='candidate_end' for record in records)
        assert len(gateway[1])==2
    send(private,scenario)


def test_delayed_first_content_after30_seconds_uses_remaining_chat_deadline(private,gateway):
    gateway[0].mode='delayed_first'
    started=time.monotonic()
    def scenario(records,context):
        elapsed=time.monotonic()-started
        assert 30<elapsed<105
        assert ''.join(record['text'] for record in records if record['type']=='delta')==SUPPORTED_ANSWER['answer']
        assert records[-1]['type']=='candidate_end' and records[-1]['finish_reason']=='stop'
        assert len(gateway[1])==2
    send(private,scenario)


# Diagnostic64: exercise the original stream/parser/model boundary, never a
# stand-alone sanitizer. All payloads and credentials below are synthetic.
def _diagnostic_wire(raw,finish='stop'):
    event={'choices':[{'index':0,'delta':{'content':raw},'finish_reason':None}]}
    end={'choices':[{'index':0,'delta':{},'finish_reason':finish}]}
    return ('data: '+json.dumps(event)+'\n\ndata: '+json.dumps(end)+'\n\ndata: [DONE]\n\n').encode()


def _diagnostic_run(monkeypatch,wire,caplog,transport_error=None,period=None):
    import io,logging,hashlib
    from types import SimpleNamespace
    from pydantic import SecretStr
    from app.clients.chat_gateway import ChatGateway
    settings=SimpleNamespace(llm_model='economicon-chat',litellm_base_url='http://synthetic.invalid/v1',
                             litellm_api_key=SecretStr('DIAGNOSTIC_SYNTHETIC_KEY_NEVER_LOG'))
    gateway=ChatGateway(settings);requests=[]
    class Response(io.BytesIO):
        headers={'Content-Type':'text/event-stream'}
    def opened(req,**kwargs):
        requests.append(req)
        if transport_error is not None: raise transport_error
        return Response(wire)
    monkeypatch.setattr(gateway.client.transport,'open',opened)
    context={'messages':[{'role':'user','content':'UNTRUSTED_CURRENT_CONTEXT\n'+json.dumps({'question':'DIAGNOSTIC_SYNTHETIC_PROMPT_NEVER_LOG'})}],
        'response_period':period, 'financial_metrics_allowed':False,
        'authorized_evidence':[{'id':'known','kind':'corpus','title':'Synthetic','source':'Synthetic','content':'Synthetic grounding.'}]}
    caplog.set_level(logging.WARNING,logger='app.clients.chat_gateway')
    records=list(gateway._records(context,time.time()+120,{},threading.Event()))
    events=[]
    for record in caplog.records:
        if record.name!='app.clients.chat_gateway':continue
        event=json.loads(record.getMessage())
        assert event['event']=='chat_gateway_diagnostic'
        assert len(record.getMessage().encode())<=2048
        assert set(event)<= {'event','operation_id','attempt_id','request_sha256','stage','exception_class','errors','finish_reason','http_status','category','rule_code','stream_location'}
        assert 'DIAGNOSTIC_SYNTHETIC' not in record.getMessage()
        for item in event['errors']:
            assert set(item)=={'type','loc','rule_code'}
            assert len(item['loc'])<=6
        events.append(event)
    assert len(requests)==1
    if events:assert events[0]['request_sha256']==hashlib.sha256(requests[0].data).hexdigest()
    return records,events


def test_real_four_byte_utf8_survives_single_byte_transport(monkeypatch,caplog):
    import io
    original=io.BytesIO
    class SingleByte(original):
        def read1(self,size=-1): return super().read(1 if size!=0 else 0)
    monkeypatch.setattr(io,'BytesIO',SingleByte)
    raw=json.dumps(supported_provider(),ensure_ascii=False)
    event={'choices':[{'index':0,'delta':{'content':raw},'finish_reason':'stop'}]}
    wire=('data: '+json.dumps(event,ensure_ascii=False)+'\n\ndata: [DONE]\n\n').encode('utf-8')
    assert bytes.fromhex('f09f9880') in wire
    records,events=_diagnostic_run(monkeypatch,wire,caplog)
    assert records[-1]['result']['answer']==SUPPORTED_ANSWER['answer']
    assert ''.join(r['text'] for r in records if r['type']=='delta')==SUPPORTED_ANSWER['answer']
    assert events==[]


def _rule_candidate(rule):
    import copy
    value=copy.deepcopy(SUPPORTED_ANSWER)
    evidence={'id':'known','kind':'corpus','title':'Synthetic','source':'Synthetic'}
    metric={'name':'Synthetic','value':'1','unit':'USD','evidence_ids':['known']}
    recommendation={'category':'investigation','action':'Synthetic','rationale':'Synthetic',
        'estimated_savings':'1','currency':None,'confidence':'low','risk':'low',
        'evidence_ids':['known'],'requires_human_approval':True}
    value['evidence']=[evidence]
    if rule=='period_order':value['scope']['period']={'from':'2026-10-11','to':'2026-10-10'}
    if rule=='savings_currency_pair':
        value.update(status='ok',evidence=[evidence],recommendations=[recommendation])
    if rule=='evidence_id_duplicates':value['evidence']=[evidence,evidence.copy()]
    if rule=='non_actionable_with_metrics_or_recommendations':
        value.update(evidence=[evidence],metrics=[metric])
    if rule=='unknown_evidence_reference':
        metric['evidence_ids']=['DIAGNOSTIC_SYNTHETIC_UNKNOWN_REFERENCE']
        value.update(status='ok',evidence=[evidence],metrics=[metric])
    if rule=='actionable_requires_evidence':value.update(status='ok',evidence=[])
    return value


@pytest.mark.parametrize('rule',['period_order','savings_currency_pair','evidence_id_duplicates',
    'non_actionable_with_metrics_or_recommendations','unknown_evidence_reference','actionable_requires_evidence'])
def test_diagnostic64_six_actual_model_rules_are_actionable_and_private(monkeypatch,caplog,rule):
    candidate=supported_provider()
    if rule=='actionable_requires_evidence':
        candidate=_provider(ANSWER);candidate['status']='ok'
    else:
        # Inject malformed canonical data at the final model boundary. The
        # renderer now derives/deduplicates citations, so these model failures
        # cannot all be manufactured through private provider selections.
        # Keep actual Pydantic validation and the real gateway diagnostic path.
        from app.agents.schemas import FinOpsResponse
        validate=FinOpsResponse.model_validate
        monkeypatch.setattr(FinOpsResponse,'model_validate',lambda value:validate(_rule_candidate(rule)))
    records,events=_diagnostic_run(monkeypatch,_diagnostic_wire(json.dumps(candidate)),caplog,
        period={'from':'2026-10-11','to':'2026-10-10'} if rule=='period_order' else None)
    assert records[-1]=={'type':'error','category':'invalid_response','status':422}
    assert len(events)==1,'Original gateway discards the diagnostic before returning its error'
    event=events[0]
    if rule=='actionable_requires_evidence':
        assert event['stage']=='model_validation' and event['rule_code']=='narrative_evidence_required'
        assert event['errors']==[]
        return
    assert event['stage']=='model_validation' and event['exception_class']=='ValidationError'
    assert event['finish_reason']=='stop'
    assert event['errors'][0]['rule_code']==rule
    assert event['errors'][0]['type']=='value_error'
    assert event['errors'][0]['loc']==([] if rule not in ['period_order','savings_currency_pair'] else
                                    ['scope','period'] if rule=='period_order' else ['recommendations',0])


def test_diagnostic64_valid_candidate_and_wire_remain_identical_without_event(monkeypatch,caplog):
    records,events=_diagnostic_run(monkeypatch,_diagnostic_wire(json.dumps(supported_provider())),caplog)
    assert records[-1]['type']=='candidate' and records[-1]['result']==SUPPORTED_ANSWER
    assert records[-1]['finish_reason']=='stop' and events==[]


@pytest.mark.parametrize('raw,finish,stage,category',[
    ('{"answer":"DIAGNOSTIC_SYNTHETIC_PARTIAL",','stop','candidate_json','invalid_response'),
    ('{"answer":"DIAGNOSTIC_SYNTHETIC_PARTIAL",','length','candidate_json','incomplete'),
    (json.dumps(ANSWER),'DIAGNOSTIC_SYNTHETIC_FINISH','finish','invalid_response')])
def test_diagnostic64_json_and_finish_failures_are_sanitized_before_length_return(monkeypatch,caplog,raw,finish,stage,category):
    records,events=_diagnostic_run(monkeypatch,_diagnostic_wire(raw,finish),caplog)
    assert records[-1]['type']=='error' and records[-1]['category']==category
    assert len(events)==1
    assert events[0]['stage']==stage and events[0]['errors']==[]
    assert events[0]['finish_reason']==('other' if finish.startswith('DIAGNOSTIC') else finish)


def test_diagnostic64_field_errors_are_bounded_and_unknown_names_are_removed(monkeypatch,caplog):
    value=supported_provider();value.pop('status');value['schema_version']=32
    value['DIAGNOSTIC_SYNTHETIC_UNKNOWN_FIELD']='DIAGNOSTIC_SYNTHETIC_VALUE'
    records,events=_diagnostic_run(monkeypatch,_diagnostic_wire(json.dumps(value)),caplog)
    assert records[-1]['status']==422 and len(events)==1
    errors=events[0]['errors'];assert 1<=len(errors)<=3
    assert any(item['type']=='missing' and item['loc']==['status'] for item in errors)
    assert any(item['loc']==['unknown'] for item in errors)


def test_diagnostic64_unknown_model_message_never_leaks_or_matches_by_substring(monkeypatch,caplog):
    from pydantic import ValidationError
    from app.agents.schemas import FinOpsResponse
    def rejected(value):
        raise ValidationError.from_exception_data('Synthetic',[{'type':'value_error','loc':(),
            'input':{'secret':'DIAGNOSTIC_SYNTHETIC_INPUT'},
            'ctx':{'error':ValueError('evidence ids must be unique DIAGNOSTIC_SYNTHETIC_CONTEXT')}}])
    monkeypatch.setattr(FinOpsResponse,'model_validate',rejected)
    records,events=_diagnostic_run(monkeypatch,_diagnostic_wire(json.dumps(supported_provider())),caplog)
    assert records[-1]['status']==422 and len(events)==1
    assert events[0]['errors']==[{'type':'value_error','loc':[],'rule_code':'unclassified_model_rule'}]


def test_diagnostic64_observer_failure_cannot_change_existing_error(monkeypatch,caplog):
    import logging
    def broken(*args,**kwargs):raise RuntimeError('DIAGNOSTIC_SYNTHETIC_OBSERVER')
    monkeypatch.setattr(logging.getLogger('app.clients.chat_gateway'),'warning',broken)
    records,events=_diagnostic_run(monkeypatch,_diagnostic_wire(json.dumps(_rule_candidate('actionable_requires_evidence'))),caplog)
    assert records[-1]=={'type':'error','category':'invalid_response','status':422} and events==[]


def test_diagnostic64_eof_and_transport_have_no_fabricated_finish(monkeypatch,caplog):
    records,events=_diagnostic_run(monkeypatch,b'',caplog)
    assert records==[{'type':'error','category':'eof'}] and len(events)==1
    assert events[0]['finish_reason'] is None and events[0]['exception_class'] is None


@pytest.mark.parametrize('wire,stage',[
    (b'data: []\n\n','envelope'),
    (b'data: \xff\n\n','envelope'),
    (_diagnostic_wire(json.dumps({'answer':'x'*4001})),'provisional_answer')])
def test_diagnostic64_actual_early_parser_errors_keep_stage_and_no_payload(monkeypatch,caplog,wire,stage):
    records,events=_diagnostic_run(monkeypatch,wire,caplog)
    assert records[-1]['category']=='invalid_response' and len(events)==1
    assert events[0]['stage']==stage and events[0]['errors']==[]
    assert events[0]['finish_reason'] is None


def test_diagnostic64_actual_transport_error_is_structural_only(monkeypatch,caplog):
    from urllib.error import URLError
    records,events=_diagnostic_run(monkeypatch,b'',caplog,
        transport_error=URLError(OSError('DIAGNOSTIC_SYNTHETIC_TRANSPORT_REASON')))
    assert records[-1]['type']=='error' and len(events)==1
    assert events[0]['stage']=='transport' and events[0]['finish_reason'] is None
    assert events[0]['exception_class']=='OtherException'


@pytest.mark.parametrize('split', [False, True])
def test_provisional_equation_failure_identifies_only_segment_or_adjacent_group(monkeypatch,caplog,split):
    value=supported_provider()
    prose='DIAGNOSTIC_SYNTHETIC_SEGMENT_NEVER_LOG '
    if split:
        value['answer']=[value['answer'][-1],{'inference':prose+'80 /'}, {'inference':' 200 = 40'}]
        expected={'field':'answer','mode':'adjacent_prose','kind':'inference','first_segment':1,'last_segment':2}
    else:
        value['answer']=[value['answer'][0],value['answer'][-1],{'inference':prose+'80 / 200 = 40'}]
        expected={'field':'answer','mode':'segment','kind':'inference','first_segment':2,'last_segment':2}
    records,events=_diagnostic_run(monkeypatch,_diagnostic_wire(json.dumps(value)),caplog)
    assert records[-1]=={'type':'error','category':'invalid_response','status':422}
    assert len(events)==1 and events[0]['rule_code']=='calculation_free_numeric_equation_forbidden'
    assert events[0]['stage']=='provisional_answer' and events[0]['stream_location']==expected
    assert '80' not in json.dumps(events[0]['stream_location'])


def test_provisional_location_never_copies_untrusted_keys_values_or_out_of_range_indexes(caplog):
    from app.clients.chat_gateway import _record_diagnostic
    from app.core.chat_calculations import CalculationError
    import logging
    caplog.set_level(logging.WARNING,logger='app.clients.chat_gateway')
    failure=CalculationError('Free numeric equation forbidden.')
    _record_diagnostic('provisional_answer',failure,None,None,stream_location={
        'field':'answer','mode':'segment','kind':'inference','first_segment':True,
        'last_segment':999,'DIAGNOSTIC_SYNTHETIC_PRIVATE_KEY':'DIAGNOSTIC_SYNTHETIC_PRIVATE_VALUE'})
    event=json.loads(caplog.records[-1].message)
    assert event['stream_location']=={'field':'answer','mode':'segment','kind':'inference'}
    assert 'DIAGNOSTIC_SYNTHETIC' not in caplog.text
    _record_diagnostic('model_validation',failure,None,None,stream_location={
        'field':'answer','mode':'segment','kind':'inference','first_segment':0,'last_segment':0})
    assert 'stream_location' not in json.loads(caplog.records[-1].message)
    _record_diagnostic('provisional_answer',failure,None,None,stream_location={
        'field':'answer','mode':'segment','kind':['DIAGNOSTIC_SYNTHETIC_PRIVATE_VALUE']})
    assert 'stream_location' not in json.loads(caplog.records[-1].message)
