"""Confirmed metadata comes from the frozen authorized context and processor receipt."""
import asyncio
import copy
import json
import pytest
from sqlalchemy import text
from app.services.chat_operations import service
from test_chat_operations_jup035 import ANSWER,api,body,headers,messages,path,run

def frame_records(response):
    return [json.loads(line.removeprefix('data: ')) for line in response.text.splitlines() if line.startswith('data: ')]

def configure(api,monkeypatch,usage=None,authorized=(),citations=(),returned=()):
    candidate=copy.deepcopy(ANSWER)
    if returned: candidate.update(status='ok',answer='Respuesta documental.',evidence=list(returned),limitations=[])
    base=api[0].state.chat_context_builder
    manifest={'prompt_version':'synthetic-v2','input_contract_sha256':'d'*64,'response_schema_sha256':'e'*64,'variable_tokens':27}
    async def context(scope,payload,descriptor):
        value=await base(scope,payload,descriptor)
        value.update(authorized_evidence=list(authorized),source_citations=list(citations),manifest=manifest)
        return value
    async def stream(claim):
        api[2].claims.append(claim)
        yield {'type':'delta','text':'Provisional'}
        yield {'type':'candidate','result':candidate,'finish_reason':'stop','usage':usage}
    monkeypatch.setattr(api[0].state,'chat_context_builder',context)
    monkeypatch.setattr(api[2],'stream',stream)
    return candidate,manifest

def sources():
    evidence=[{'id':name,'kind':'corpus','title':name+' título','source':'Manual','content':name+' texto autorizado'} for name in ('doc-one','doc-two')]
    evidence.append({'id':'cost-screen','kind':'cost_query','title':'Consulta de costes','source':'billing-summary-v2','metrics':[]})
    citations=[{'evidence_id':e['id'],'kind':'corpus','document_id':e['id']+'-document','title':e['title'],'source':e['source'],
        'reference':'document:'+e['id']+'-document/chunk:0','section':None,'page':None,'excerpt':e['content'][:140]} for e in evidence[:2]]
    returned=[{key:e[key] for key in ('id','kind','title','source')} for e in (evidence[1],evidence[2])]
    return evidence,citations,returned

@pytest.mark.parametrize('state',['failed','completed'])
@pytest.mark.parametrize('delivery',['before_publication','published','stale_read'])
def test_initial_stream_preserves_committed_terminal_before_ram_publication(api,monkeypatch,state,delivery):
    """Force the DB-commit/RAM-event gap without depending on thread timing."""
    from uuid import uuid4
    runtime=service(api[0]);scope={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
    row,_=runtime.repository.reserve(scope,body(),{'prompt_version':'synthetic'})
    identifier=row['operation_id']
    runtime.buffers[identifier]={'events':[],'subscribers':set(),'partial':'',
        'initial_frame':runtime._frame(row,'started',operation=runtime.public(row))}
    active,won=runtime.repository.claim(scope,identifier,'synthetic-boot')
    assert won
    runtime._emit(active,'attempt_started',attempt_id=active['current_attempt_id'],number=1,seq=0)
    if state=='failed':
        row=runtime.repository.close_attempt(scope,identifier,active['current_attempt_id'],transient=False)
    else:
        row=runtime.repository.complete(scope,identifier,active['current_attempt_id'],ANSWER,{},str(uuid4()))
    async def scenario():
        event='final' if state=='completed' else 'terminal'
        if delivery!='before_publication':
            values=await runtime._final_values(scope,row) if state=='completed' else {'operation':runtime.public(row)}
            runtime._emit(row,event,**values)
        if delivery=='stale_read':
            async def stale_get(*args):return active
            monkeypatch.setattr(runtime,'get',stale_get)
        frames=[frame async for frame in runtime.events(scope,identifier,initial=True)]
        records=frame_records(type('Reply',(),{'text':''.join(frames)})())
        assert [item['type'] for item in records]==['started','attempt_started',event]
        assert records[-1]['operation']['state']==state
        assert len(messages(api[1]))==(2 if state=='completed' else 0)
    asyncio.run(asyncio.wait_for(scenario(),2))

@pytest.mark.parametrize('reported,expected',[
    ({'prompt_tokens':12,'completion_tokens':7,'total_tokens':19,'cost_usd':'0.00001230',
      'authorization':'Bearer private-secret','cached_tokens':777,'model':'invented-model','headers':{'secret':'secret'}},
     {'prompt_tokens':12,'completion_tokens':7,'total_tokens':19,'cost_usd':'0.00001230'}),
    ({'prompt_tokens':0,'completion_tokens':0,'total_tokens':0,'cost_usd':'0'},
     {'prompt_tokens':0,'completion_tokens':0,'total_tokens':0,'cost_usd':'0'}),
    ({'prompt_tokens':9007199254740993},{'prompt_tokens':9007199254740993}),
    ({'prompt_tokens':5,'completion_tokens':True,'total_tokens':-1,'cost_usd':'NaN'}, {'prompt_tokens':5}),
])
def test_reported_allowlisted_usage_survives_atomic_jsonb_result_history_and_final(api,monkeypatch,reported,expected):
    candidate,manifest=configure(api,monkeypatch,reported)
    runtime=service(api[0])
    original=runtime._emit
    observed=[]
    def emit(row,event,**values):
        if event=='final':
            persisted=messages(api[1])
            assert len(persisted)==2 and row['state']=='completed'
            observed.append(persisted)
        return original(row,event,**values)
    monkeypatch.setattr(runtime,'_emit',emit)
    async def scenario(client):
        payload=body()
        response=await asyncio.wait_for(client.post(path(),headers=headers(),json=payload),5)
        assert response.status_code==200,response.text
        final=next(item for item in frame_records(response) if item['type']=='final')
        assert final['usage']==expected
        operation=final['operation']
        base=path()+'/'+operation['operation_id']
        assert final['result_url']==base+'/result' and final['context_url']==base+'/context' and final['evidence_url']==base+'/evidence'
        result=await client.get(final['result_url'],headers=headers())
        assert result.status_code==200,result.text
        metadata=result.json()['metadata']
        assert metadata['generation']['usage']==expected and metadata['response']==candidate
        assert metadata['generation']['context_manifest']==manifest
        assert metadata['generation']['prompt_version']=='synthetic-v2'
        with api[1].engine.connect() as connection:
            input_hash=connection.execute(text("SELECT input_hash FROM chat_operations WHERE operation_id=:id AND tenant_id='t' AND user_id='alice'"),{'id':operation['operation_id']}).scalar_one()
        assert metadata['generation']['input_hash']==input_hash
        assert final['answer_id']==result.json()['id']
        observed_events=await client.get(base+'/events',headers=headers())
        observed_final=next(item for item in frame_records(observed_events) if item['type']=='final')
        assert observed_final['usage']==expected and observed_final['answer_id']==result.json()['id']
        context=await client.get(final['context_url'],headers=headers())
        evidence=await client.get(final['evidence_url'],headers=headers())
        assert context.json()['manifest']==manifest and evidence.json()=={'items':[]}
        detail=await client.get('/assistant/conversations/alice-chat',headers=headers())
        saved=next(message for message in detail.json()['messages'] if message['role']=='assistant')
        assert saved['metadata']==metadata and saved['id']==result.json()['id']
        repeated=await asyncio.wait_for(client.post(path(),headers=headers(),json=payload),5)
        assert repeated.json()['operation_id']==operation['operation_id'] and len(api[2].claims)==1
        assert observed and 'private-secret' not in result.text
        for unknown in ('cached_tokens','invented-model','authorization','headers'):
            assert unknown not in json.dumps(metadata)
    run(scenario,api)

@pytest.mark.parametrize('reported',[None,{}, {'prompt_tokens':False,'completion_tokens':-1,'total_tokens':2.5,'cost_usd':'Infinity'},
    {'cost_usd':float('nan')}, {'cost_usd':'-0.01'}, {'model':'economicon-chat','provider':'claimed-only'}, ['invalid'],
    {'prompt_tokens':12,'completion_tokens':7,'total_tokens':20}])
def test_missing_invalid_usage_remains_unknown_not_invented_zero_or_provider(api,monkeypatch,reported):
    configure(api,monkeypatch,reported)
    async def scenario(client):
        response=await asyncio.wait_for(client.post(path(),headers=headers(),json=body()),5)
        final=next(item for item in frame_records(response) if item['type']=='final')
        assert final['usage'] is None
        result=await client.get(final['result_url'],headers=headers())
        assert result.json()['metadata']['generation']['usage'] is None
        assert len(api[2].claims)==1 and len(messages(api[1]))==2
    run(scenario,api)

def test_only_used_authorized_corpus_citations_are_preserved_without_fabricating_screen_documents(api,monkeypatch):
    evidence,citations,returned=sources()
    configure(api,monkeypatch,authorized=evidence,citations=citations,returned=returned)
    async def scenario(client):
        response=await asyncio.wait_for(client.post(path(),headers=headers(),json=body()),5)
        final=next(item for item in frame_records(response) if item['type']=='final')
        result=await client.get(final['result_url'],headers=headers())
        metadata=result.json()['metadata']
        assert metadata['citations']==['doc-two'] and metadata['source_citations']==[citations[1]]
        assert metadata['response']['evidence']==returned
        detail=await client.get('/assistant/conversations/alice-chat',headers=headers())
        assert detail.json()['messages'][1]['metadata']==metadata
        assert 'doc-one-document' not in result.text and 'cost-screen-document' not in result.text
        assert len(api[2].claims)==1
        private=await client.get(final['result_url'],headers=headers('bob'))
        assert private.status_code==404 and 'doc-two texto' not in private.text
    run(scenario,api)

@pytest.mark.parametrize('problem',['foreign','duplicate','mismatch','missing','excerpt'])
def test_unresolvable_or_mismatched_citations_reject_before_final_without_retry_or_history(api,monkeypatch,problem):
    evidence,citations,returned=sources()
    if problem=='foreign': returned[0]={**returned[0],'id':'foreign-document'}
    if problem=='duplicate': citations.append(copy.deepcopy(citations[1]))
    if problem=='mismatch': citations[1]['source']='Another private source'
    if problem=='missing': citations=[citations[0]]
    if problem=='excerpt': citations[1]['excerpt']='Invented quotation from another source'
    configure(api,monkeypatch,authorized=evidence,citations=citations,returned=returned)
    async def scenario(client):
        response=await asyncio.wait_for(client.post(path(),headers=headers(),json=body()),5)
        records=frame_records(response)
        assert not any(item['type']=='final' for item in records)
        terminal=next(item for item in records if item['type']=='terminal')
        assert terminal['operation']['state']=='failed' and terminal['operation']['attempt_count']==1
        assert len(api[2].claims)==1 and messages(api[1])==[]
        result=await client.get(path()+'/'+terminal['operation']['operation_id']+'/result',headers=headers())
        assert result.status_code==409 and 'Another private source' not in result.text
    run(scenario,api)
