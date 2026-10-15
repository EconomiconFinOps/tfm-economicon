"""JUP-035 real loopback HTTP processor boundary, synthetic signing only."""
import hashlib
import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from test_chat_operations_jup035 import ANSWER,api,body,existing,headers,messages,path,run


KEY=b'jup035-synthetic-private-key-32-bytes-only'


@pytest.fixture
def private_processor(tmp_path):
    calls=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            nonce=self.headers.get('X-Chat-Nonce','')
            payload=json.dumps({'v':2,'boot_id':'synthetic-boot','prompt_version':'synthetic-v2',
                'capacity':8},separators=(',',':')).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(payload)))
            self.send_header('X-Chat-Nonce',nonce)
            signature=hmac.new(KEY,f'chat-v2-response\n{nonce}\n200\n{hashlib.sha256(payload).hexdigest()}'.encode(),hashlib.sha256).hexdigest()
            self.send_header('X-Chat-Signature',signature if not self.server.bad_signature else '0'*64)
            self.end_headers();self.wfile.write(payload)
        def do_POST(self):
            raw=self.rfile.read(int(self.headers['Content-Length']))
            signed=f"chat-v2\nPOST\n{self.path}\n{self.headers.get('X-Chat-Time','')}\n{self.headers.get('X-Chat-Nonce','')}\n{hashlib.sha256(raw).hexdigest()}".encode()
            valid=hmac.compare_digest(self.headers.get('X-Chat-Signature',''),hmac.new(KEY,signed,hashlib.sha256).hexdigest())
            if not valid:
                self.send_response(401);self.end_headers();return
            claim=json.loads(raw);calls.append(claim)
            candidate=json.dumps(ANSWER,separators=(',',':'),ensure_ascii=False).encode()
            records=[{'v':2,'type':'delta','text':'Sin evidencia'},
                {'v':2,'type':'candidate_chunk','offset':0,'text':candidate.decode()},
                {'v':2,'type':'candidate_end','size':len(candidate),'sha256':hashlib.sha256(candidate).hexdigest(),
                 'finish_reason':'stop','usage':None}]
            if getattr(self.server,'bad_candidate',None)=='offset': records[1]['offset']=1
            if getattr(self.server,'bad_candidate',None)=='hash': records[2]['sha256']='0'*64
            self.send_response(200);self.send_header('Content-Type','application/x-ndjson');self.end_headers()
            for record in records:
                self.wfile.write(json.dumps(record,ensure_ascii=False).encode()+b'\n');self.wfile.flush()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.bad_signature=False
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    key_file=tmp_path/'synthetic-hmac-key';key_file.write_bytes(KEY)
    yield server,calls,key_file
    server.shutdown();server.server_close();thread.join()


def configure(api,private_processor,monkeypatch):
    server,_,file=private_processor
    monkeypatch.delattr(api[0].state,'chat_transport')
    monkeypatch.setenv('PROCESSOR_CHAT_BASE_URL',f'http://127.0.0.1:{server.server_port}')
    monkeypatch.setenv('CHAT_SERVICE_HMAC_KEY_FILE',str(file))


def test_public_generation_uses_signed_private_http_and_streams_before_final(api,private_processor,monkeypatch):
    configure(api,private_processor,monkeypatch)
    async def scenario(c):
        payload=body()
        result=await c.post(path(),json=payload,headers=headers())
        assert result.status_code==200,result.text
        assert result.text.index('event: delta')<result.text.index('event: final')
        op=await existing(c,payload)
        assert op['state']=='completed'
        calls=private_processor[1]
        assert len(calls)==1 and calls[0]['attempt_id']==op['current_attempt_id']
        assert calls[0]['number']==1 and calls[0]['tenant_id']=='t' and calls[0]['user_id']=='alice'
        assert 'capability' not in result.text and KEY.decode() not in result.text
    run(scenario,api)


def test_descriptor_with_invalid_response_signature_never_reserves_or_dispatches(api,private_processor,monkeypatch):
    configure(api,private_processor,monkeypatch)
    private_processor[0].bad_signature=True
    async def scenario(c):
        result=await c.post(path(),json=body(),headers=headers())
        assert result.status_code==503,result.text
        assert private_processor[1]==[]
        assert KEY.decode() not in result.text
    run(scenario,api)


@pytest.mark.parametrize('tamper',['offset','hash'])
def test_invalid_private_candidate_never_commits_or_calls_again(api,private_processor,monkeypatch,tamper):
    configure(api,private_processor,monkeypatch)
    private_processor[0].bad_candidate=tamper
    async def scenario(c):
        payload=body()
        result=await c.post(path(),json=payload,headers=headers())
        assert result.status_code==200 and 'event: final' not in result.text
        op=await existing(c,payload)
        assert op['state']=='failed' and op['attempt_count']==1
        assert messages(api[1])==[] and len(private_processor[1])==1
    run(scenario,api)
