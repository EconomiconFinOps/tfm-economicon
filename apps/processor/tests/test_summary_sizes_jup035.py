"""Real tokenizer and scripted transport only; no paid provider."""
import copy,json,threading,time
from dataclasses import replace
from pathlib import Path
from uuid import uuid4
import pytest
from app.core.context_budget import budget
from app.core.summary_resources import load_resources
from app.clients.summary_gateway import SummaryGateway,SummaryGatewayError
from app.core.config import Settings
from pydantic import SecretStr
from app.summary import valid_previous,ledger,digest
from test_chat_summary_gateway_jup035 import source_document,SCOPE

ROOT=Path(__file__).resolve().parents[1]/'app/agents/prompt_resources/jup035'
def current():return load_resources(ROOT/'summary/v3',ROOT/'chat/v2/tokenizer.json')
def old():return load_resources(ROOT/'summary/v2',ROOT/'chat/v2/tokenizer.json')
def contract(r):
    m=json.loads(r.manifest_bytes)
    return dict(prompt_version=r.summary_version,schema_sha256=r.response_schema_sha256,tokenizer_sha256=r.tokenizer_sha256,policy_version=m['kind']+':'+m['policy_sha256'])

def test_reserve_minimum_and_processor_admission(monkeypatch):
    assert budget('summary')['output_tokens']==10000 and budget('chat')['output_tokens']==3200
    monkeypatch.setenv('SUMMARY_CONTEXT_TOKENS','11024')
    with pytest.raises(ValueError):budget('summary')
    monkeypatch.setenv('SUMMARY_CONTEXT_TOKENS','32768')
    r=old();payload={'previous_summary':None,'pairs':[dict(question='x',answer='sin confirmar',question_ref='q-'+'1'*64,answer_ref='a-'+'2'*64)]}
    _,count=r.prepare_input(payload)
    with pytest.raises(ValueError):replace(r,context_budget={**r.context_budget,'context_tokens':count+9999}).prepare_input(payload)

@pytest.mark.parametrize('finish',['stop','length'])
def test_gateway_uses_independent_generation_ceiling(finish):
    r=current();seen=[]
    output=dict(v=2,topics=[dict(text='x '*250,question_refs=['q-'+'1'*64],answer_refs=[]) for _ in range(8)],facts=[],limitations=[])
    assert r.count(json.dumps(output))>800
    class Response:
        headers={'Content-Type':'application/json'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return json.dumps({'choices':[{'index':0,'message':{'content':json.dumps(output)},'finish_reason':finish}]}).encode()
    class Transport:
        def open(self,request,timeout):seen.append(json.loads(request.data));return Response()
    gateway=SummaryGateway(Settings(llm_provider='litellm',llm_model='economicon-chat',litellm_api_key=SecretStr('offline-key'),llm_max_output_tokens=800))
    gateway.client.transport=Transport()
    if finish=='stop':assert gateway._post([],r,time.time()+20,{},threading.Event())['output']==output
    else:
        with pytest.raises(SummaryGatewayError):gateway._post([],r,time.time()+20,{},threading.Event())
    assert seen[0]['max_tokens']==10000

def test_previous_v2_validated_under_origin_and_not_relabelled():
    r=old();new=current();doc=source_document();refs,qa=ledger(doc,SCOPE)
    output=dict(v=2,topics=[],facts=[dict(quote=qa[0]['answer'],source_ref=qa[0]['answer_ref'])],limitations=[])
    epoch=str(uuid4());artifact=dict(artifact_id=str(uuid4()),artifact_revision=1,lineage_epoch=epoch,parent_artifact_id=None,parent_artifact_sha256=None,previous_payload_used=None,
        source_refs=refs[:1],frontier_processed=refs[0],source_selection_hash=digest({'scope':SCOPE,'pairs':refs[:1]}),exact_output=output,text_sha256=digest(output),contract=contract(r),observations={})
    state=dict(v=2,scope=SCOPE,state_revision=1,lineage_epoch=epoch,validity={'valid':True,'reason':None},artifact=artifact,invalidation=None)
    before=copy.deepcopy(state)
    assert valid_previous(state,SCOPE,refs,qa,new)==(output,1)
    assert state==before
    state['artifact']['contract']['policy_version']='unknown'
    assert valid_previous(state,SCOPE,refs,qa,new)==(None,0)
    state=copy.deepcopy(before)
    oversized=dict(v=2,topics=[dict(text=qa[0]['answer'],question_refs=[qa[0]['question_ref']],answer_refs=[qa[0]['answer_ref']]) for _ in range(8)],facts=[],limitations=[])
    assert new.validate_payload(oversized)==oversized
    state['artifact']['exact_output']=oversized;state['artifact']['text_sha256']=digest(oversized)
    assert valid_previous(state,SCOPE,refs,qa,new)==(None,0)

def test_new_bundle_limits_and_pin(tmp_path):
    r=current();m=json.loads(r.manifest_bytes)
    assert m['budgets']==dict(input_total_tokens=1048576,output_tokens=10000,payload_tokens=8192,content_tokens=6144)
    value=dict(v=2,topics=[dict(text='x '*250,question_refs=['q-'+'1'*64],answer_refs=[]) for _ in range(8)],facts=[],limitations=[])
    assert r.validate_payload(value)==value
    with pytest.raises(ValueError):old().validate_payload(value)
    from app.core.chat_resources import canonical,sha
    content=dict(v=2,topics=[],facts=[],limitations=[])
    for i in range(16):
        if i<8:content['topics'].append(dict(text='漢'*512,question_refs=['q-'+'1'*64],answer_refs=[]))
        else:content['facts'].append(dict(quote='漢'*512,source_ref='q-'+'1'*64))
        words='\n'.join([x['text'] for x in content['topics']]+[x['quote'] for x in content['facts']])
        if r.count(words)>6144:break
    assert r.count(words)>6144 and r.count(canonical(content).decode())<=8192
    with pytest.raises(ValueError):r.validate_payload(content)
    payload=copy.deepcopy(value)
    payload['topics']=[dict(text='x '*250,question_refs=['q-'+sha(str(i).encode()) for i in range(8)],answer_refs=['a-'+sha(str(i).encode()) for i in range(8)]) for _ in range(8)]
    payload['limitations']=['x '*120]*4
    assert r.count(canonical(payload).decode())>8192
    assert r.count('\n'.join([x['text'] for x in payload['topics']]+payload['limitations']))<6144
    with pytest.raises(ValueError):r.validate_payload(payload)
    import shutil
    root=tmp_path/'v3';shutil.copytree(ROOT/'summary/v3',root)
    raw=(root/'system.md').read_bytes()+b'changed'
    (root/'system.md').write_bytes(raw)
    m['system_sha256']=__import__('hashlib').sha256(raw).hexdigest()
    (root/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    with pytest.raises(ValueError):load_resources(root,ROOT/'chat/v2/tokenizer.json')
