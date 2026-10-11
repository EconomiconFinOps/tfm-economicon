"""Summary gateway exercised through existing private app: real counted loopback POSTs.

Provider answers are scripted simulations, never evidence of remote LLM fidelity.
"""
import asyncio,copy,hashlib,json,time,threading
from decimal import Decimal
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from uuid import uuid4
from pathlib import Path
import httpx,pytest
from sqlalchemy import text
from test_chat_summary_resources_jup035 import summary_bundle
from test_chat_private_jup035 import signed

ROUTE='/internal/chat/v2/summaries'
SCOPE={'tenant_id':'tenant','user_id':'alice','conversation_id':'chat'}
SUMMARY_KEY='jup035-synthetic-summary-key-distinct-from-main'
MAIN_KEY='jup035-synthetic-main-key-never-used-by-summary'

def canonical(value):
    if isinstance(value,Decimal):return format(value,'f')
    if isinstance(value,dict):return '{'+','.join(json.dumps(k,ensure_ascii=False)+':'+canonical(value[k]) for k in sorted(value))+'}'
    if isinstance(value,list):return '['+','.join(canonical(x) for x in value)+']'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def source_document():
    messages=[]
    for index in range(6):
        q='question-'+str(index);a='answer-'+str(index)
        messages.extend([{'ordinal':2*index,'id':q,'role':'user','author_id':'alice','question_id':q,'origin':'completed',
            'content':'¿Cómo comparar EUR y USD sin conversiones?','metadata':{'marker':'SYNTHETIC_METADATA_NEVER_MODEL'},'created_at':'2026-10-10T18:00:00.000000Z'},
            {'ordinal':2*index+1,'id':a,'role':'assistant','author_id':'alice','question_id':q,'origin':'completed',
            'content':'No se confirmó un ahorro; las divisas permanecen separadas.','metadata':{'generation':{'question_message_id':q}},'created_at':'2026-10-10T18:00:01.000000Z'}])
    return {'schema_version':1,'identity':dict(SCOPE),'revision':6,'next_ordinal':12,'messages':messages}

@pytest.fixture
def summary_session(summary_bundle,monkeypatch,tmp_path):
    private,root,manifest,_=summary_bundle;application=private[0];doc=source_document();calls=[];release=threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            raw=self.rfile.read(int(self.headers['Content-Length']));body=json.loads(raw);calls.append({'body':body,'summary_key_used':self.headers.get('Authorization')=='Bearer '+SUMMARY_KEY,'path':self.path})
            payload=json.loads(body['messages'][-1]['content'].partition('\n')[2]);pair=payload['pairs'][0]
            output={'v':2,'topics':[{'text':'Preguntas sobre divisas y filtros, sin autoridad financiera.','question_refs':[pair['question_ref']],'answer_refs':[pair['answer_ref']]}],
                'facts':[{'quote':pair['answer'],'source_ref':pair['answer_ref']}],'limitations':['La memoria no confirma hechos financieros.']}
            behavior=self.server.behavior
            if behavior=='unknown_ref':output['topics'][0]['answer_refs']=['a-'+'f'*64]
            elif behavior=='invented_quote':output['facts'][0]['quote']='Literal que no existe'
            elif behavior=='invented_number':output['topics'][0]['text']='El coste confirmado es 999999 EUR.'
            elif behavior=='invented_url':output['topics'][0]['text']='Consultar https://invented.invalid/cost'
            elif behavior=='invented_unit':output['topics'][0]['text']='Se compararon GBP y USD.'
            elif behavior=='negation_inverted':output['topics'][0]['text']='Se confirmó un ahorro.'
            elif behavior=='contradiction_flattened':output['topics'][0]['text']='Se autorizó eliminar R-1.'
            elif behavior=='duplicate_question_refs':output['topics'][0]['question_refs']*=2
            elif behavior=='duplicate_answer_refs':output['topics'][0]['answer_refs']*=2
            elif behavior=='bad_schema':output['v']=2.0
            elif behavior=='unreferenced_topic':output['topics'][0]['question_refs']=[];output['topics'][0]['answer_refs']=[]
            content=canonical(output)
            if behavior=='duplicate_json':content='{"v":2,'+content[1:]
            elif behavior=='nonfinite_json':content=content[:-1]+',"extra":NaN}'
            if behavior=='stall':release.wait(5)
            status=429 if behavior=='429' else 307 if behavior=='redirect' else 200
            response={'id':'mock-summary54','model':'mock-qa-provider','choices':[{'index':0,'message':{'role':'assistant','content':content},'finish_reason':'length' if behavior=='length' else 'stop'}]}
            if behavior!='unknown_usage':response['usage']={'prompt_tokens':41,'completion_tokens':20,'total_tokens':61}
            raw=canonical(response).encode()
            if behavior=='oversized_response':raw=b'x'*(1024*1024+1)
            self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
            if behavior=='redirect':self.send_header('Location','/must-not-follow')
            self.end_headers()
            try:self.wfile.write(raw);self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.behavior='success';worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    file=tmp_path/'summary-only-synthetic-key';file.write_text(SUMMARY_KEY,encoding='utf-8')
    for key,value in {'SUMMARY_ENABLED':'true','SUMMARY_API_KEY_FILE':str(file),'LLM_PROVIDER':'litellm','LLM_MODEL':'economicon-chat',
        'LITELLM_BASE_URL':f'http://127.0.0.1:{server.server_port}/v1','LITELLM_API_KEY':MAIN_KEY}.items():monkeypatch.setenv(key,value)
    monkeypatch.setattr(application.state,'chat_capacity',8,raising=False)
    monkeypatch.setattr(application.state,'summary_jobs',{},raising=False)
    monkeypatch.setattr(application.state,'summary_gateway',None,raising=False)
    with private[2].begin() as c:
        c.execute(text('ALTER TABLE conversations ADD COLUMN dialogue_history JSONB'))
        c.execute(text('ALTER TABLE conversations ADD COLUMN dialogue_summary JSONB'))
        c.execute(text("UPDATE conversations SET dialogue_history=:doc,dialogue_summary=NULL WHERE id='chat'"),{'doc':canonical(doc)})
    yield summary_bundle,server,calls,doc,release
    release.set();server.shutdown();server.server_close();worker.join(timeout=2)

def persist_doc(session):
    with session[0][0][2].begin() as c:c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='chat'"),{'doc':canonical(session[3])})

def envelope(session,**changes):
    doc=session[3];refs=[];pairs=[]
    for i in range(2):
        q,a=doc['messages'][2*i:2*i+2]
        refs.append({'question_id':q['id'],'answer_id':a['id'],'question_ordinal':q['ordinal'],'answer_ordinal':a['ordinal'],'question_sha256':digest(q),'answer_sha256':digest(a)})
        pairs.append({'question_ref':'q-'+digest({'scope':SCOPE,'role':'user','id':q['id']}),'question':q['content'],
            'answer_ref':'a-'+digest({'scope':SCOPE,'role':'assistant','id':a['id']}),'answer':a['content']})
    manifest=session[0][2];payload={'previous_summary':None,'pairs':pairs}
    return {'v':2,'job_id':str(uuid4()),'scope':dict(SCOPE),'boot_id':'synthetic-boot','summary_version':'jup-035.summary.v2:'+digest(manifest),
        'schema_sha256':manifest['response_schema_sha256'],'tokenizer_sha256':manifest['tokenizer']['sha256'],
        'parent_hash':None,'lineage_epoch':str(uuid4()),'source_refs':refs,'selected_pairs':2,'deadline':time.time()+30,
        'input_hash':digest(payload),'payload':payload,**changes}

async def request(client,method,path,body,headers=None):
    raw=canonical(body).encode();return await client.request(method,path,content=raw,headers=headers or signed(method,path,raw))

def exercise(session,callback):
    async def run():
        application=session[0][0][0]
        async with application.router.lifespan_context(application):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application),base_url='http://private') as client:return await callback(client,application)
    return asyncio.run(run())

def test_summary_gateway_dispatches_once_nonstream_strict_qa_only_separate_key(summary_session):
    body=envelope(summary_session)
    async def run(client,application):
        result=await request(client,'POST',ROUTE,body);assert result.status_code==200,result.text
        response=result.json();assert response['state']=='completed' and response['settled'] is True
        assert response['job_id']==body['job_id'] and response['receipt']['dispatch_count']==1
        assert response['receipt']['input_hash']==body['input_hash'] and response['receipt']['output_hash']==digest(response['output'])
        assert len(summary_session[2])==1;call=summary_session[2][0];payload=call['body']
        assert call['summary_key_used'] and call['path']=='/v1/chat/completions'
        assert payload['model']=='economicon-chat' and payload['stream'] is False and payload['max_tokens']==10000 and payload['num_retries']==0
        assert payload['reasoning']=={'enabled':False} and payload['provider']['allow_fallbacks'] is False
        assert payload['response_format']['json_schema']['name']=='SummaryResponse' and payload['response_format']['json_schema']['strict'] is True

        local=application.state.summary_resources
        original=local.response_schema
        projected=copy.deepcopy(original)
        for field in ['question_refs','answer_refs']:
            assert original['$defs']['SummaryTopic']['properties'][field]['uniqueItems'] is True
            del projected['$defs']['SummaryTopic']['properties'][field]['uniqueItems']
        assert payload['response_format']['json_schema']['schema']==projected
        assert local.response_schema==original
        assert local.response_schema==local.response_model.model_json_schema()
        assert hashlib.sha256(canonical(original).encode()).hexdigest()==body['schema_sha256']
        assert hashlib.sha256(canonical(projected).encode()).hexdigest()=='ec92ca50508a0fe0b94ef08ef81c3b1f330973d5b9266d22a53c9b1ca4b8e5ac'
        assert json.loads(payload['messages'][-1]['content'].partition('\n')[2])==body['payload']
        assert all(marker not in canonical(payload) for marker in ['SYNTHETIC_METADATA_NEVER_MODEL',MAIN_KEY,body['job_id']])
        with summary_session[0][0][2].connect() as c:assert c.execute(text("SELECT dialogue_summary FROM conversations WHERE id='chat'")).scalar_one() is None
    exercise(summary_session,run)

@pytest.mark.parametrize('behavior',['unknown_ref','invented_quote','invented_number','invented_url','invented_unit','negation_inverted','contradiction_flattened','duplicate_question_refs','duplicate_answer_refs','bad_schema','unreferenced_topic','duplicate_json','nonfinite_json','length','429','redirect','oversized_response'])
def test_summary_gateway_invalid_candidates_or_provider_errors_fail_closed_without_retry(summary_session,behavior):
    summary_session[1].behavior=behavior
    if behavior=='contradiction_flattened':
        summary_session[3]['messages'][0]['content']='No autoricé eliminar R-1.'
        summary_session[3]['messages'][1]['content']='Se autorizó eliminar R-1; existe una contradicción con la pregunta.';persist_doc(summary_session)
    body=envelope(summary_session)
    async def run(client,application):
        result=await request(client,'POST',ROUTE,body);assert result.status_code in [422,502,503],result.text
        assert result.json()['state']=='failed' and 'output' not in result.json()
        assert len(summary_session[2])==1
        status=await request(client,'GET',ROUTE+'/'+body['job_id'],{'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']})
        assert status.status_code==200 and status.json()['state']=='failed' and len(summary_session[2])==1
    exercise(summary_session,run)

def test_summary_gateway_unknown_usage_and_cost_remain_unknown(summary_session):
    summary_session[1].behavior='unknown_usage';body=envelope(summary_session)
    async def run(client,application):
        result=await request(client,'POST',ROUTE,body);assert result.status_code==200,result.text
        assert result.json()['receipt']['usage'] is None and result.json()['receipt']['cost'] is None
    exercise(summary_session,run)

def test_summary_gateway_absolute_deadline_closes_only_own_request_without_retry(summary_session):
    summary_session[1].behavior='stall'
    async def run(client,application):
        start=time.monotonic();body=envelope(summary_session,deadline=time.time()+.35)
        result=await request(client,'POST',ROUTE,body);assert result.status_code==504,result.text
        assert result.json()['state'] in ['failed','cancelling'] and len(summary_session[2])<=1
        for _ in range(40):
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],{'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']})
            if status.json()['settled']:break
            await asyncio.sleep(.025)
        assert status.json()['settled'] is True and len(summary_session[2])<=1
        assert time.monotonic()-start<2.5
    exercise(summary_session,run)

# Register every existing fixture dependency in this collected module.
from test_chat_private_jup035 import private
from test_chat_resources_jup035 import resources
from test_chat_summary_resources_jup035 import summary_bundle
