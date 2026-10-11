"""Private summary transport from existing constructor, counted loopback requests."""
import asyncio,copy,hashlib,hmac,json,time,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from uuid import uuid4
from pathlib import Path
import pytest
from app.services.chat_transport import PrivateChatTransport
from app.db.chat_repository import ChatError
from app.core.summary_resources import load_resources

KEY=b'jup035-synthetic-private-hmac-summary-control'
ROOT=Path('/workspace/apps/processor/app/agents/prompt_resources/jup035')
Q='q-'+'1'*64;A='a-'+'2'*64
SOURCES={Q:'No autoricé eliminar R-1. ¿Cómo comparar EUR y USD?',A:'No se confirmó un ahorro; las divisas permanecen separadas.'}
OUTPUT={'v':2,'topics':[{'text':'Intenciones sobre filtros y divisas, sin autoridad financiera.','question_refs':[Q],'answer_refs':[A]}],
        'facts':[{'quote':SOURCES[A],'source_ref':A}],'limitations':['La memoria no confirma hechos financieros.']}
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()

@pytest.fixture(scope='module')
def resources54():return load_resources(str(ROOT/'summary/v2'),str(ROOT/'chat/v2/tokenizer.json'))

def summary(base,key=KEY):
    transport=PrivateChatTransport(base,key);child=getattr(transport,'summary',None)
    assert child is not None,'Existing PrivateChatTransport constructor exposes no isolated summary transport'
    assert child is not transport
    return child

@pytest.fixture
def summary_server(resources54):
    calls=[];jobs={}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,value,status=200):
            raw=canonical(value).encode();nonce=self.headers.get('X-Chat-Nonce','')
            if self.server.behavior=='duplicate_json':raw=b'{"v":2,'+raw[1:]
            elif self.server.behavior=='oversized':raw=b'x'*(1024*1024+1)
            self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
            self.send_header('X-Chat-Nonce','other' if self.server.behavior=='nonce' else nonce)
            signature=hmac.new(KEY,f'chat-v2-response\n{nonce}\n{status}\n{hashlib.sha256(raw).hexdigest()}'.encode(),hashlib.sha256).hexdigest()
            self.send_header('X-Chat-Signature','0'*64 if self.server.behavior=='signature' else signature);self.end_headers()
            try:self.wfile.write(raw);self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError):pass
        def authorized(self,raw):
            text=f"chat-v2\n{self.command}\n{self.path}\n{self.headers['X-Chat-Time']}\n{self.headers['X-Chat-Nonce']}\n{hashlib.sha256(raw).hexdigest()}".encode()
            assert hmac.compare_digest(self.headers['X-Chat-Signature'],hmac.new(KEY,text,hashlib.sha256).hexdigest())
        def do_GET(self):
            raw=self.rfile.read(int(self.headers.get('Content-Length',0)));self.authorized(raw);calls.append({'method':'GET','path':self.path})
            if self.path.endswith('/descriptor'):
                value={'v':2,'boot_id':'synthetic-boot','summary_version':resources54.summary_version,'manifest_sha256':hashlib.sha256(resources54.manifest_bytes).hexdigest(),
                    'tokenizer_sha256':resources54.tokenizer_sha256,'response_schema_sha256':resources54.response_schema_sha256,
                    'context_budget':resources54.context_budget};self.send(value)
            else:self.send(jobs[self.path.rsplit('/',1)[1]])
        def do_POST(self):
            raw=self.rfile.read(int(self.headers['Content-Length']));self.authorized(raw);body=json.loads(raw);calls.append({'method':'POST','path':self.path,'body':body})
            if self.path.endswith('/cancel'):
                value=jobs[self.path.split('/')[-2]];value.update(state='cancelled',settled=True);value.pop('output',None);self.send(value);return
            receipt={'call_id':str(uuid4()),'dispatch_count':1,'input_hash':body['input_hash'],'output_hash':digest(OUTPUT),'usage':None,'cost':None}
            value={'v':2,'job_id':body['job_id'],'scope':body['scope'],'boot_id':body['boot_id'],'input_hash':body['input_hash'],'summary_version':body['summary_version'],
                'state':'completed','settled':True,'output':copy.deepcopy(OUTPUT),'receipt':receipt};jobs[body['job_id']]=value
            if self.server.behavior=='lost_ack':self.connection.shutdown(2);self.connection.close();return
            if self.server.behavior=='wrong_job':value={**value,'job_id':str(uuid4())}
            if self.server.behavior=='wrong_hash':value={**value,'input_hash':'0'*64}
            self.send(value)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.behavior='success';worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    yield server,calls,jobs
    server.shutdown();server.server_close();worker.join(timeout=2)

def envelope(resources):
    payload={'previous_summary':None,'pairs':[{'question_ref':Q,'question':SOURCES[Q],'answer_ref':A,'answer':SOURCES[A]}]}
    return {'v':2,'job_id':str(uuid4()),'scope':{'tenant_id':'t','user_id':'u','conversation_id':'c'},'boot_id':'synthetic-boot',
        'summary_version':resources.summary_version,'deadline':time.time()+30,'input_hash':digest(payload),'payload':payload}

def test_existing_constructor_summary_uses_authenticated_descriptor_and_one_bounded_post(summary_server,resources54):
    server,calls,_=summary_server;body=envelope(resources54);body['deadline']=time.time()+180
    async def run():
        child=summary(f'http://127.0.0.1:{server.server_port}');descriptor=await child.descriptor();resources54.verify_descriptor(descriptor)
        value=await child.submit(body);assert value['job_id']==body['job_id'] and value['receipt']['dispatch_count']==1
        assert value['receipt']['usage'] is None and value['receipt']['cost'] is None
        assert sum(x['method']=='POST' and x['path']=='/internal/chat/v2/summaries' for x in calls)==1
        assert calls[-1]['body']==body
    asyncio.run(run())

@pytest.mark.parametrize('behavior',['signature','nonce','duplicate_json','oversized','wrong_job','wrong_hash'])
def test_bad_private_response_never_becomes_candidate_or_redispatch(summary_server,resources54,behavior):
    server,calls,_=summary_server;server.behavior=behavior;body=envelope(resources54)
    async def run():
        child=summary(f'http://127.0.0.1:{server.server_port}')
        with pytest.raises(ChatError):await child.submit(body)
        assert sum(x['method']=='POST' for x in calls)==1
    asyncio.run(run())

def test_lost_ack_requires_status_reconciliation_and_never_second_post(summary_server,resources54):
    server,calls,_=summary_server;server.behavior='lost_ack';body=envelope(resources54)
    async def run():
        child=summary(f'http://127.0.0.1:{server.server_port}')
        with pytest.raises(ChatError) as error:await child.submit(body)
        assert error.value.code=='summary_outcome_unknown'
        value=await child.status(body);assert value['state']=='completed' and value['settled'] is True
        assert sum(x['method']=='POST' for x in calls)==1
        cancelled=await child.cancel(body);assert cancelled['state']=='cancelled' and cancelled['settled'] is True
        assert sum(x['path']=='/internal/chat/v2/summaries' for x in calls)==1
    asyncio.run(run())

def test_expired_lot_deadline_never_posts(summary_server,resources54):
    server,calls,_=summary_server;body=envelope(resources54);body['deadline']=time.time()-1
    async def run():
        child=summary(f'http://127.0.0.1:{server.server_port}')
        with pytest.raises(ChatError):await child.submit(body)
        assert calls==[]
    asyncio.run(run())


def test_summary_deadline_above_configured_ceiling_never_posts(summary_server,resources54):
    server,calls,_=summary_server;body=envelope(resources54);body['deadline']=time.time()+181
    async def run():
        child=summary(f'http://127.0.0.1:{server.server_port}')
        with pytest.raises(ChatError) as error:await child.submit(body)
        assert error.value.code=='summary_input_invalid' and calls==[]
    asyncio.run(run())

@pytest.mark.parametrize('defect',['valid','unknown_ref','invented_quote','invented_number','invented_url','invented_unit','negation','contradiction','unreferenced_topic','bad_schema'])
def test_backend_rechecks_schema_sources_entities_negation_and_contradiction(resources54,defect):
    child=summary('http://127.0.0.1:8003');value=copy.deepcopy(OUTPUT);sources=dict(SOURCES)
    if defect=='unknown_ref':value['topics'][0]['question_refs']=['q-'+'f'*64]
    elif defect=='invented_quote':value['facts'][0]['quote']='No existe este literal'
    elif defect=='invented_number':value['topics'][0]['text']='El ahorro confirmado es 999999 EUR.'
    elif defect=='invented_url':value['topics'][0]['text']='Consultar https://invented.invalid/cost'
    elif defect=='invented_unit':value['topics'][0]['text']='Se utilizaron GBP y USD.'
    elif defect=='negation':value['topics'][0]['text']='Se confirmó un ahorro.'
    elif defect=='contradiction':sources[A]='Se autorizó eliminar R-1; contradice la pregunta.';value['facts'][0]['quote']=sources[A];value['topics'][0]['text']='Se autorizó eliminar R-1.'
    elif defect=='unreferenced_topic':value['topics'][0]['question_refs']=[];value['topics'][0]['answer_refs']=[]
    elif defect=='bad_schema':value['v']=2.0
    if defect=='valid':assert child.validate_output(value,sources,resources54)==value
    else:
        with pytest.raises(ValueError):child.validate_output(value,sources,resources54)

@pytest.fixture
def absent_summary_server(resources54):
    """Synthetic signed control server: submit never registers a processor job."""
    calls=[];markers={}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def read_body(self):
            raw=self.rfile.read(int(self.headers.get('Content-Length','0')))
            at=self.headers['X-Chat-Time'];nonce=self.headers['X-Chat-Nonce']
            message=f'chat-v2\n{self.command}\n{self.path}\n{at}\n{nonce}\n{hashlib.sha256(raw).hexdigest()}'.encode()
            assert hmac.compare_digest(self.headers['X-Chat-Signature'],hmac.new(KEY,message,hashlib.sha256).hexdigest())
            calls.append((self.command,self.path))
            return json.loads(raw) if raw else {}
        def reply(self,status,value):
            raw=canonical(value).encode();nonce=self.headers['X-Chat-Nonce']
            message=f'chat-v2-response\n{nonce}\n{status}\n{hashlib.sha256(raw).hexdigest()}'.encode()
            self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
            self.send_header('X-Chat-Nonce',nonce);self.send_header('X-Chat-Signature',hmac.new(KEY,message,hashlib.sha256).hexdigest());self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            self.read_body();job=self.path.rsplit('/',1)[1]
            self.reply(200,markers[job]) if job in markers else self.reply(404,{'v':2,'code':'not_found'})
        def do_POST(self):
            body=self.read_body()
            if self.path==ROOT55A:
                self.connection.shutdown(2);self.connection.close();return
            job=self.path.split('/')[-2]
            marker={'v':2,'job_id':job,'scope':body['scope'],'boot_id':body['boot_id'],'input_hash':body['input_hash'],
                'summary_version':resources54.summary_version,'state':'cancelled','settled':True}
            markers.setdefault(job,marker);self.reply(200,markers[job])
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    yield server,calls,markers
    server.shutdown();server.server_close();worker.join(timeout=2)

ROOT55A='/internal/chat/v2/summaries'

def test_unknown_submit_and_missing_status_do_not_release_without_confirmed_cancel_marker(absent_summary_server,resources54):
    server,calls,markers=absent_summary_server;body=envelope(resources54)
    async def run():
        child=summary(f'http://127.0.0.1:{server.server_port}')
        with pytest.raises(ChatError) as error:await child.submit(body)
        assert error.value.code=='summary_outcome_unknown' and markers=={}
        with pytest.raises(ChatError):await child.status(body)
        assert markers=={} and sum(method=='POST' and path==ROOT55A for method,path in calls)==1
        cancelled=await child.cancel(body)
        assert cancelled['state']=='cancelled' and cancelled['settled'] is True and cancelled['job_id']==body['job_id']
        observed=await child.status(body);assert observed==cancelled
        with pytest.raises(ChatError):await child.submit(body)
        assert sum(method=='POST' and path==ROOT55A for method,path in calls)==1
    asyncio.run(run())
