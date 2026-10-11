"""Consume only scoped validated QA memory; retain originals and freeze used input.

Artifacts in these tests use explicitly synthetic candidates through the existing
CAS; they never claim model dispatch/fidelity. Main producer is existing fixture.
"""
import asyncio,copy,hashlib,json
from uuid import uuid4
import pytest
from sqlalchemy import text
from app.db.chat_repository import ChatRepository,ChatError
from app.db.chat_summary_repository import ledger
from app.services.chat_context import ChatContext,escaped
from test_chat_operations_jup035 import api,body,headers,path,run,existing,until_state
from test_chat_context_assembly_jup035 import prepared,initialize,RESOURCE_ROOT
from test_chat_summary_lifecycle_jup035 import summary_resources53,contract53
from test_chat_summary_scheduler_jup035 import source,document,derived,digest,SCOPE

ROOT='/assistant/conversations/alice-chat/summary'
SUMMARY_ROOT='/workspace/apps/processor/app/agents/prompt_resources/jup035/summary/v2'

def package(api,resources):return (api[0],api[1],api[2],None,resources,api[3])

def install_memory(api,resources,count=2):
    helper=ChatRepository(api[1],api[3]).summaries;snapshot=helper.snapshot(SCOPE,contract53(resources),resources)
    refs,qa,_=ledger(snapshot.document);chosen=qa[snapshot.covered_pairs:snapshot.covered_pairs+count]
    assert len(chosen)==count
    output={'v':2,'topics':[{'text':'Preguntas de diálogo, sin autoridad financiera.','question_refs':[p['question_ref'] for p in chosen],'answer_refs':[p['answer_ref'] for p in chosen]}],
        'facts':[{'quote':chosen[0]['answer'],'source_ref':chosen[0]['answer_ref']}],
        'limitations':['La memoria puede omitir matices y no acredita hechos financieros.']}
    payload={'previous_summary':snapshot.previous_payload_used,'pairs':chosen}
    receipt={'synthetic':True,'call_id':str(uuid4()),'dispatch_count':1,'input_hash':digest(payload),'output_hash':digest(output),'usage':None,'cost':None}
    candidate=helper.candidate(snapshot,output,receipt,count);result=helper.install(SCOPE,snapshot,candidate)
    assert result['installed'];return output,derived(package(api,resources))

@pytest.fixture
def memory(prepared,summary_resources53,monkeypatch):
    api,manifest=prepared;monkeypatch.setenv('SUMMARY_ENABLED','true');monkeypatch.setenv('SUMMARY_RESOURCE_DIRECTORY',SUMMARY_ROOT)
    monkeypatch.setattr(api[0].state,'summary_resources',summary_resources53,raising=False)
    source(package(api,summary_resources53),count=8,long=False)
    output,state=install_memory(api,summary_resources53)
    return api,summary_resources53,output,state

def context_current(context):return json.loads(context['messages'][-1]['content'].partition('\n')[2])

def test_valid_memory_is_whole_untrusted_user_before_current_and_freezes_exact_used_payload(memory):
    api,resources,output,state=memory;before=digest(document(package(api,resources)))
    resource_hashes={name:hashlib.sha256((RESOURCE_ROOT/name).read_bytes()).hexdigest() for name in ['system.md','input.md','manifest.json','tokenizer.json']}
    async def scenario(client):
        await initialize(api[0]);builder=ChatContext(api[0],api[0].state.chat_resources)
        context=builder.build(SCOPE,body());messages=context['messages']
        assert len(messages)==3 and [m['role'] for m in messages]==['system','user','user']
        assert messages[1]['content']=='UNTRUSTED_DIALOGUE_SUMMARY\n'+escaped(output)
        assert api[0].state.chat_resources.count(messages[1]['content'])<=768
        assert messages[0]['content']==(RESOURCE_ROOT/'system.md').read_text(encoding='utf-8')
        assert context['manifest']['variable_tokens']==api[0].state.chat_resources.count_messages(messages)<=8192
        used=context['manifest']['summary']
        assert used['used'] is True and used['payload']==output and used['payload_sha256']==digest(output)
        assert used['artifact_id']==state['artifact']['artifact_id'] and used['artifact_sha256']==digest(state['artifact'])
        assert used['summary_version']==resources.summary_version
        assert len(context_current(context)['recent_pairs'])==6
        assert not any(item.get('kind')=='summary' for item in context['authorized_evidence'])
        assert digest(document(package(api,resources)))==before and api[2].claims==[]
    run(scenario,api)
    assert resource_hashes=={name:hashlib.sha256((RESOURCE_ROOT/name).read_bytes()).hexdigest() for name in resource_hashes}

@pytest.mark.parametrize('defect',['foreign_scope','source_hash','version','output_hash','negation_inverted','unreferenced_topic','invalidated'])
def test_invalid_memory_is_omitted_entirely_without_repairing_or_mutating_originals(memory,defect):
    api,resources,output,original=memory;state=copy.deepcopy(original)
    if defect=='foreign_scope':state['scope']['user_id']='bob'
    elif defect=='source_hash':state['artifact']['source_refs'][0]['question_sha256']='0'*64
    elif defect=='version':state['artifact']['contract']['prompt_version']='other-version'
    elif defect=='output_hash':state['artifact']['text_sha256']='0'*64
    elif defect=='invalidated':state['validity']={'valid':False,'reason':'retry_covered'}
    else:
        value=state['artifact']['exact_output']
        if defect=='negation_inverted':value['topics'][0]['text']='Se confirmó una conclusión financiera.'
        else:value['topics'][0]['question_refs']=[];value['topics'][0]['answer_refs']=[]
        state['artifact']['text_sha256']=digest(value);state['artifact']['observations']['receipt']['output_hash']=digest(value)
    with api[1].engine.begin() as c:c.execute(text("UPDATE conversations SET dialogue_summary=:state WHERE id='alice-chat'"),{'state':__import__('app.db.chat_history',fromlist=['dumps']).dumps(state)})
    raw_summary=digest(state);raw_history=digest(document(package(api,resources)))
    async def scenario(client):
        await initialize(api[0]);context=ChatContext(api[0],api[0].state.chat_resources).build(SCOPE,body())
        assert len(context['messages'])==2 and all(not m['content'].startswith('UNTRUSTED_DIALOGUE_SUMMARY\n') for m in context['messages'])
        assert context['manifest'].get('summary',{}).get('used') is False
        assert len(context_current(context)['recent_pairs'])==8
        assert digest(derived(package(api,resources)))==raw_summary and digest(document(package(api,resources)))==raw_history
        assert api[2].claims==[]
    run(scenario,api)

def test_whole_memory_is_preserved_or_explicit_limit_without_silent_loss(memory):
    api,resources,output,state=memory
    async def scenario(client):
        await initialize(api[0]);builder=ChatContext(api[0],api[0].state.chat_resources)
        from app.db import chat_history
        from app.schemas.chat import canonical
        from dataclasses import replace
        before=digest(document(package(api,resources)))
        payload=body(content='x/ '*3670)
        assert len(payload['content'].encode())<=16384
        context=builder.build(SCOPE,payload)
        assert len(context['messages'])==3 and context['manifest']['summary']['payload']==output
        builder.resources=replace(builder.resources,
            context_budget={**builder.resources.context_budget,'context_tokens':4096})
        with pytest.raises(ChatError) as error:builder.build(SCOPE,payload)
        assert error.value.code=='context_token_limit'
        assert digest(document(package(api,resources)))==before
        assert derived(package(api,resources))['artifact']['exact_output']==output
    run(scenario,api)

def test_summary_get_is_owned_cold_reports_coverage_and_does_not_change_jsonb_or_dispatch(memory):
    api,resources,output,state=memory;before_history=digest(document(package(api,resources)));before_summary=digest(state)
    async def scenario(client):
        await initialize(api[0])
        for _ in range(3):
            response=await client.get(ROOT,headers=headers());assert response.status_code==200,response.text
            value=response.json()
            assert value['v']==2 and value['scope']==SCOPE and value['available'] is True
            assert value['coverage']['processed_pairs']==2 and value['coverage']['pending_pairs']==2 and value['coverage']['recent_reserved']==4
            assert value['limitations'] and value['artifact_id']==state['artifact']['artifact_id']
        assert (await client.get(ROOT,headers=headers('bob'))).status_code==404
        other=await client.get(ROOT,headers={**headers(),'X-Tenant-Id':'foreign'});assert other.status_code in [403,404]
        assert api[2].claims==[] and digest(document(package(api,resources)))==before_history and digest(derived(package(api,resources)))==before_summary
    run(scenario,api)

def test_automatic_retry_reuses_used_memory_after_new_artifact_is_installed(memory):
    api,resources,output,state=memory;api[2].errors=[{'status':429,'category':'provider_error','retry_after':1}]
    async def scenario(client):
        await initialize(api[0]);payload=body();response=await client.post(path(),json=payload,headers=headers());assert response.status_code==200,response.text
        opened=await existing(client,payload);await until_state(client,opened['status_url'],'waiting')
        frozen=copy.deepcopy(api[2].claims[0]['context'])
        assert frozen['manifest']['summary']['used'] is True and frozen['manifest']['summary']['payload']==output
        install_memory(api,resources,count=1)
        assert derived(package(api,resources))['artifact']['artifact_id']!=state['artifact']['artifact_id']
        api[3].advance(2);await until_state(client,opened['status_url'],'completed')
        assert len(api[2].claims)==2 and api[2].claims[1]['context']==frozen
    run(scenario,api)

def test_human_retry_covered_omits_memory_before_final_but_invalidation_waits_for_commit(prepared,summary_resources53,monkeypatch):
    api,_=prepared;resources=summary_resources53;monkeypatch.setenv('SUMMARY_ENABLED','true');monkeypatch.setenv('SUMMARY_RESOURCE_DIRECTORY',SUMMARY_ROOT)
    monkeypatch.setattr(api[0].state,'summary_resources',resources,raising=False)
    async def scenario(client):
        await initialize(api[0]);payload=body(content='Pregunta original completa')
        first=await client.post(path(),json=payload,headers=headers());assert first.status_code==200,first.text
        operation=await existing(client,payload);assert operation['state']=='completed'
        repository=ChatRepository(api[1],api[3])
        maintenance=repository.compactions.claim(SCOPE,'synthetic-no-eligible-pairs')
        assert maintenance is not None
        repository.compactions.transition(SCOPE,maintenance,clear=True)
        source(package(api,resources),count=7,long=False);output,state=install_memory(api,resources,count=2)
        before=digest(state);api[2].release=asyncio.Event();task=None
        try:
            retry={**body(content=payload['content']),'retry_of_operation_id':operation['operation_id']}
            task=asyncio.create_task(client.post(path(),json=retry,headers=headers()))
            for _ in range(200):
                if len(api[2].claims)==2:break
                await asyncio.sleep(.005)
            assert len(api[2].claims)==2
            context=api[2].claims[-1]['context']
            assert len(context['messages'])==2 and context['manifest']['summary']['used'] is False
            assert context['manifest']['summary']['reason']=='retry_covered'
            assert digest(derived(package(api,resources)))==before and state['validity']['valid'] is True
            api[2].release.set();response=await asyncio.wait_for(task,2);assert response.status_code==200,response.text
            invalid=derived(package(api,resources));assert invalid['validity']=={'valid':False,'reason':'retry_covered'}
            assert invalid['artifact']['exact_output']==output and invalid['lineage_epoch']!=state['lineage_epoch']
        finally:
            api[2].release.set()
            if task is not None:await asyncio.gather(task,return_exceptions=True)
    run(scenario,api)

def test_disabled_memory_preserves_main_and_all_originals_without_provider(memory,monkeypatch):
    api,resources,output,state=memory;monkeypatch.setenv('SUMMARY_ENABLED','false')
    async def scenario(client):
        await initialize(api[0]);context=ChatContext(api[0],api[0].state.chat_resources).build(SCOPE,body())
        assert len(context['messages'])==2 and context['manifest']['summary']['used'] is False and context['manifest']['summary']['reason']=='summary_disabled'
        response=await client.get(ROOT,headers=headers());assert response.status_code==200 and response.json()['available'] is False
        assert len(document(package(api,resources))['messages'])==16 and api[2].claims==[]
    run(scenario,api)
