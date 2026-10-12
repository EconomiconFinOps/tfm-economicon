"""Offline size/legacy contracts; persisted synthetic artifacts, no model calls."""
import copy
import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import text
from app.core.context_budget import budget
from app.core.summary_resources import load_resources, sha
from app.db.chat_repository import ChatRepository, ChatError
from app.db.chat_summary_repository import ledger, digest
from app.services.chat_context import ChatContext, escaped
from test_chat_operations_jup035 import api, body
from test_chat_context_assembly_jup035 import prepared
from test_chat_summary_lifecycle_jup035 import summary_resources53, contract53
from test_chat_summary_context_jup035 import install_memory, package
from test_chat_summary_scheduler_jup035 import source, document, derived, SCOPE

ROOT=Path(__file__).resolve().parents[3]/'apps/processor/app/agents/prompt_resources/jup035'

def current():
    return load_resources(ROOT/'summary/v3', ROOT/'chat/v2/tokenizer.json')

def contract(r):
    m=json.loads(r.manifest_bytes)
    return dict(prompt_version=r.summary_version,schema_sha256=r.response_schema_sha256,
                tokenizer_sha256=r.tokenizer_sha256,policy_version=m['kind']+':'+m['policy_sha256'])

def test_reserves_and_minimum(monkeypatch):
    assert budget('summary')['output_tokens']==10000
    assert budget('chat')['output_tokens']==3200
    assert budget('summary')['body_limit_bytes']==1048576
    assert budget('chat')['body_limit_bytes']==2097152
    monkeypatch.setenv('SUMMARY_CONTEXT_TOKENS','11024')
    with pytest.raises(ValueError):budget('summary')
    monkeypatch.setenv('SUMMARY_CONTEXT_TOKENS','11025')
    assert budget('summary')['context_tokens']==11025

def test_planner_reserves_full_generation_and_descriptor_rejects_mismatch(summary_resources53):
    r=summary_resources53
    pairs=[dict(question_ref='q-'+format(i,'064x'),answer_ref='a-'+format(i,'064x'),question='x '*300,answer='sin confirmar') for i in range(7)]
    measured=r.prepare_lot(None,pairs)['input_total_tokens']
    bounded=replace(r,context_budget={**r.context_budget,'context_tokens':measured+9999})
    result=bounded.prepare_lot(None,pairs)
    assert result['selected_pairs']<3
    descriptor=dict(v=2,summary_version=r.summary_version,manifest_sha256=sha(r.manifest_bytes),
        tokenizer_sha256=r.tokenizer_sha256,response_schema_sha256=r.response_schema_sha256,context_budget=r.context_budget)
    r.verify_descriptor(descriptor)
    bad=copy.deepcopy(descriptor);bad['context_budget']['output_tokens']=800
    with pytest.raises(ValueError):r.verify_descriptor(bad)

def test_persisted_v2_consumed_then_v3_installed_without_rewriting_history(prepared,summary_resources53,monkeypatch):
    api,_=prepared;old=summary_resources53;new=current()
    source(package(api,old),count=8,long=False)
    from app.db.chat_history import dumps
    seeded=document(package(api,old))
    for message in seeded['messages']:
        if message['role']=='assistant':message['content']+=' <dato> sin confirmar.'
    with api[1].engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='alice-chat'"),{'doc':dumps(seeded)})
    output,state=install_memory(api,old,count=1)
    before_history=digest(document(package(api,old)));before_state=copy.deepcopy(state)
    monkeypatch.setenv('SUMMARY_ENABLED','true');api[0].state.summary_resources=new
    from app.core.chat_resources import load_resources as chat_load
    chat=chat_load(ROOT/'chat/v3')
    builder=ChatContext(api[0],chat)
    context=builder.build(SCOPE,body())
    assert context['manifest']['summary']['used'] is True
    assert context['manifest']['summary']['summary_version']==old.summary_version
    assert context['manifest']['summary']['artifact_sha256']==digest(state['artifact'])
    assert derived(package(api,new))==before_state
    helper=ChatRepository(api[1],api[3]).summaries
    snapshot=helper.snapshot(SCOPE,contract(new),new)
    assert snapshot.previous_payload_used==output and snapshot.covered_pairs==1
    assert snapshot.epoch==state['lineage_epoch']
    pair=snapshot.new_pairs[0]
    larger={'v':2,'topics':[{'text':'sin confirmar < > '*20,'question_refs':[pair['question_ref']],'answer_refs':[pair['answer_ref']]} for _ in range(8)],'facts':[],'limitations':[]}
    assert new.count(escaped(larger))>768
    receipt=dict(synthetic=True,call_id=str(uuid4()),dispatch_count=1,
        input_hash=digest({'previous_summary':output,'pairs':[pair]}),output_hash=digest(larger))
    candidate=helper.candidate(snapshot,larger,receipt,1)
    assert candidate.artifact['observations']['context_budget']['output_tokens']==10000
    assert candidate.artifact['parent_artifact_sha256']==digest(state['artifact'])
    helper.install(SCOPE,snapshot,candidate)
    assert digest(document(package(api,new)))==before_history
    installed=derived(package(api,new))
    assert installed['artifact']['previous_payload_used']==output
    assert installed['lineage_epoch']==before_state['lineage_epoch']
    assert installed['artifact']['parent_artifact_id']==before_state['artifact']['artifact_id']
    # Sources remain authoritative: use literal source text for the large prefix.
    larger['topics']=[{'text':pair['answer'],'question_refs':[pair['question_ref']],'answer_refs':[pair['answer_ref']]} for _ in range(8)]
    receipt['output_hash']=digest(larger)
    snapshot=helper.snapshot(SCOPE,contract(new),new)
    pair=snapshot.new_pairs[0];receipt['input_hash']=digest({'previous_summary':snapshot.previous_payload_used,'pairs':[pair]})
    candidate=helper.candidate(snapshot,larger,receipt,1);helper.install(SCOPE,snapshot,candidate)
    result=builder.build(SCOPE,body())
    prefix=result['messages'][1]['content']
    assert prefix=='UNTRUSTED_DIALOGUE_SUMMARY\n'+escaped(larger)
    assert '\\u003c' in prefix and '<dato>' not in prefix
    assert chat.count(prefix)>768 and result['manifest']['summary']['used'] is True
    assert digest(document(package(api,new)))==before_history
    from app.schemas.chat import canonical
    essential=copy.deepcopy(result['messages'])
    current_context=json.loads(essential[-1]['content'].split('\n',1)[1])
    current_context['recent_pairs']=[]
    current_context['omissions'].append({'collection':'recent_pairs','omitted_pairs':5})
    essential[-1]['content']='UNTRUSTED_CURRENT_CONTEXT\n'+escaped(current_context)
    ceiling=chat.count(canonical(essential))+chat.count(chat.schema_text)+1024+3200-1
    without_prefix=[essential[0],essential[-1]]
    assert chat.count(canonical(without_prefix))+chat.count(chat.schema_text)+1024+3200<ceiling
    bounded=replace(chat,context_budget={**chat.context_budget,'context_tokens':ceiling})
    with pytest.raises(ChatError):ChatContext(api[0],bounded).build(SCOPE,body())

def test_candidate_reserve_is_checked_before_install(prepared,summary_resources53):
    api,_=prepared;r=summary_resources53;source(package(api,r),count=6,long=False)
    helper=ChatRepository(api[1],api[3]).summaries;snapshot=helper.snapshot(SCOPE,contract53(r),r)
    output={'v':2,'topics':[],'facts':[],'limitations':[]}
    receipt=dict(synthetic=True,call_id='offline',dispatch_count=1,input_hash=digest({'previous_summary':None,'pairs':snapshot.new_pairs[:1]}),output_hash=digest(output))
    candidate=helper.candidate(snapshot,output,receipt,1)
    count=candidate.artifact['observations']['input_total_tokens']
    narrow=replace(r,context_budget={**r.context_budget,'context_tokens':count+9999})
    with pytest.raises(ChatError):helper.candidate(replace(snapshot,resources=narrow),output,receipt,1)
    assert derived(package(api,r)) is None

def test_legacy_limits_unknown_contract_and_v3_limits(summary_resources53):
    old=summary_resources53;new=current()
    assert new.resources_for_contract(contract(old)).summary_version==old.summary_version
    with pytest.raises(ValueError):new.resources_for_contract({**contract(old),'policy_version':'unknown'})
    with pytest.raises(ValueError):old.resources_for_contract(contract(new))
    value={'v':2,'topics':[],'facts':[],'limitations':['x '*120]*4}
    # Valid under the new profile, too large under the old profile.
    value['topics']=[dict(text='x '*250,question_refs=['q-'+'1'*64],answer_refs=[]) for _ in range(8)]
    assert new.validate_payload(value)==value
    with pytest.raises(ValueError):old.validate_payload(value)
    content=dict(v=2,topics=[],facts=[],limitations=[])
    for i in range(16):
        if i<8:content['topics'].append(dict(text='漢'*512,question_refs=['q-'+'1'*64],answer_refs=[]))
        else:content['facts'].append(dict(quote='漢'*512,source_ref='q-'+'1'*64))
        words='\n'.join([x['text'] for x in content['topics']]+[x['quote'] for x in content['facts']])
        if new.count(words)>6144:break
    from app.schemas.chat import canonical
    assert new.count(words)>6144 and new.count(canonical(content))<=8192
    with pytest.raises(ValueError):new.validate_payload(content)
    payload=copy.deepcopy(value)
    payload['topics']=[dict(text='x '*250,question_refs=['q-'+sha(str(i).encode()) for i in range(8)],answer_refs=['a-'+sha(str(i).encode()) for i in range(8)]) for _ in range(8)]
    assert new.count(canonical(payload))>8192
    assert new.count('\n'.join([x['text'] for x in payload['topics']]+payload['limitations']))<6144
    with pytest.raises(ValueError):new.validate_payload(payload)

def test_persisted_v2_cannot_borrow_v3_limits(prepared,summary_resources53):
    api,_=prepared;old=summary_resources53;new=current()
    source(package(api,old),count=8,long=False)
    output,state=install_memory(api,old,count=1)
    larger=copy.deepcopy(output);larger['topics']*=8
    assert new.validate_payload(larger)==larger
    with pytest.raises(ValueError):old.validate_payload(larger)
    state['artifact']['exact_output']=larger
    state['artifact']['text_sha256']=digest(larger)
    state['artifact']['observations']['receipt']['output_hash']=digest(larger)
    from app.db.chat_history import dumps
    with api[1].engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_summary=:state WHERE id='alice-chat'"),{'state':dumps(state)})
    helper=ChatRepository(api[1],api[3]).summaries
    assert helper.snapshot(SCOPE,contract(new),new).previous_payload_used is None
    assert derived(package(api,new))==state
