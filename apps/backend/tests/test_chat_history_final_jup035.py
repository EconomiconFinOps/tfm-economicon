"""Canonical atomic finals, alternatives, result integrity and legacy writer."""
import asyncio
import hashlib
import json
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import event, text

from app.db.chat_repository import ChatError, ChatRepository
from test_chat_history_document_jup035 import legacy_db, runner, SCOPE
from test_chat_operations_jup035 import ANSWER, Clock, api, body, headers, run
from test_chat_legacy_jup035 import legacy_resources


@pytest.fixture
def repo(legacy_db):
    runner(legacy_db).run()
    return ChatRepository(legacy_db, Clock()), legacy_db


def raw(db, conversation='c'):
    with db.engine.connect() as c:
        return c.execute(text('SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id=:id'), {'id':conversation}).scalar_one()


def create(repository, content='Pregunta', retry=None):
    payload={'request_id':str(uuid4()), 'content':content, 'screen_context':{}}
    if retry is not None: payload['retry_of_operation_id']=retry
    operation, created=repository.reserve(SCOPE, payload, {'messages':[], 'prompt_version':'synthetic'})
    assert created
    operation, won=repository.claim(SCOPE, operation['operation_id'], 'synthetic')
    assert won
    return operation


def complete(repository, operation, answer='Completa', result_id=None):
    result_id=result_id or str(uuid4())
    metadata={'generation':{'v':2,'state':'completed','question_message_id':operation['question_message_id']},'citations':[{'id':'synthetic'}]}
    result=repository.complete(SCOPE, operation['operation_id'], operation['current_attempt_id'],
        {**ANSWER,'answer':answer}, metadata, result_id)
    return result, result_id


def test_reserve_claim_wait_and_stop_leave_document_identical(repo):
    repository, db=repo
    before=raw(db)
    operation=create(repository)
    assert raw(db)==before
    repository.close_attempt(SCOPE, operation['operation_id'], operation['current_attempt_id'], transient=True, delay=1, partial='delta')
    assert raw(db)==before
    repository.stop(SCOPE, operation['operation_id'])
    assert raw(db)==before


def test_final_commits_complete_pair_revision_and_operation_once(repo):
    repository, db=repo
    operation=create(repository)
    before=json.loads(raw(db))
    completed, result_id=complete(repository, operation)
    value=json.loads(raw(db))
    assert value['revision']==before['revision']+1 and value['next_ordinal']==2
    assert [m['id'] for m in value['messages']]==[operation['question_message_id'],result_id]
    assert [m['role'] for m in value['messages']]==['user','assistant']
    assert [m['ordinal'] for m in value['messages']]==[0,1]
    assert all(m['origin']=='completed' and m['question_id']==operation['question_message_id'] for m in value['messages'])
    assert value['messages'][1]['metadata']['citations']==[{'id':'synthetic'}]
    assert completed['state']=='completed' and repository.result(SCOPE, completed)['id']==result_id
    repository.complete(SCOPE, completed['operation_id'], operation['current_attempt_id'], ANSWER, {}, result_id)
    assert json.loads(raw(db))==value, 'replayed final must neither append nor increment revision'


def test_no_active_history_sql_outside_document(repo):
    repository, db=repo
    statements=[]
    event.listen(db.engine,'before_cursor_execute',
        lambda c,cursor,statement,args,context,many:statements.append(statement))
    operation=create(repository)
    completed,_=complete(repository,operation)
    repository.result(SCOPE,completed)
    db.fetch_messages(**SCOPE)
    assert not any('FROM messages' in sql or 'INTO messages' in sql or 'UPDATE messages' in sql for sql in statements)


def test_failure_after_document_write_rolls_back_document_and_completed_state(repo):
    repository, db=repo
    operation=create(repository)
    before=raw(db)
    with db.engine.begin() as c:
        c.execute(text("CREATE TRIGGER reject_completed BEFORE UPDATE ON chat_operations WHEN NEW.state='completed' BEGIN SELECT RAISE(ABORT,'synthetic'); END"))
    with pytest.raises(ChatError) as error:complete(repository,operation)
    assert error.value.status==503
    assert raw(db)==before
    assert repository.get(SCOPE,operation['operation_id'])['state']=='active'


def test_two_questions_and_retry_first_append_only_new_answer(repo):
    repository, db=repo
    first=create(repository,'Pregunta A')
    first_done,answer_a=complete(repository,first,'Respuesta A')
    second=create(repository,'Pregunta B')
    _,answer_b=complete(repository,second,'Respuesta B')
    retry=create(repository,'Pregunta A',first['operation_id'])
    assert retry['question_message_id']==first['question_message_id']
    _,answer_retry=complete(repository,retry,'Alternativa A')
    value=json.loads(raw(db))
    assert value['revision']==3 and value['next_ordinal']==5
    assert [m['id'] for m in value['messages']]==[first['question_message_id'],answer_a,second['question_message_id'],answer_b,answer_retry]
    assert value['messages'][-1]['question_id']==first['question_message_id']
    assert repository.result(SCOPE,first_done)['content']=='Respuesta A'


def test_failed_question_retry_after_another_completion_keeps_logical_id(repo):
    repository, db=repo
    first=create(repository,'Pregunta A')
    repository.close_attempt(SCOPE,first['operation_id'],first['current_attempt_id'],transient=False)
    second=create(repository,'Pregunta B')
    _,answer_b=complete(repository,second)
    retry=create(repository,'Pregunta A',first['operation_id'])
    assert retry['question_message_id']==first['question_message_id']
    _,answer_a=complete(repository,retry)
    value=json.loads(raw(db))
    assert [m['id'] for m in value['messages']]==[second['question_message_id'],answer_b,first['question_message_id'],answer_a]
    assert value['revision']==2


def test_retry_changed_question_is_rejected_before_new_operation(repo):
    repository, db=repo
    first=create(repository,'Original')
    complete(repository,first)
    before=raw(db)
    with pytest.raises(ChatError) as error:create(repository,'Changed',first['operation_id'])
    assert error.value.status==409 and raw(db)==before


@pytest.mark.parametrize('defect',['missing','role','question_link','content'])
def test_completed_result_or_replay_cannot_ignore_canonical_integrity(repo,defect):
    repository, db=repo
    operation=create(repository)
    completed,result_id=complete(repository,operation)
    value=json.loads(raw(db))
    assert len(value['messages'])==2
    if defect=='missing':value['messages'].pop();value['next_ordinal']=1
    elif defect=='role':value['messages'][-1]['role']='user'
    elif defect=='question_link':value['messages'][-1]['question_id']='absent'
    else:value['messages'][0]['content']='tampered'
    with db.engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_history=:value WHERE id='c'"),{'value':json.dumps(value)})
    saved=raw(db)
    with pytest.raises(ChatError) as error:repository.result(SCOPE,completed)
    assert error.value.status==503
    with pytest.raises(ChatError):repository.complete(SCOPE,operation['operation_id'],operation['current_attempt_id'],ANSWER,{},result_id)
    assert raw(db)==saved


def test_retry_invalidates_derived_summary_in_same_final_commit(repo):
    from app.db import chat_history
    repository, db=repo
    first=create(repository)
    complete(repository,first)
    before=chat_history.loads(raw(db))
    with db.engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_summary=:value WHERE id='c'"),{'value':json.dumps({'source_question':first['question_message_id'],'epoch':7})})
    retry=create(repository,retry=first['operation_id'])
    finished,result_id=complete(repository,retry)
    with db.engine.connect() as c:
        summary_raw=c.execute(text("SELECT CAST(dialogue_summary AS TEXT) FROM conversations WHERE id='c'")).scalar_one()
    actual=chat_history.loads(summary_raw)
    assert isinstance(actual,dict) and set(actual)=={'v','scope','state_revision','lineage_epoch','validity','artifact','invalidation'}
    fixture={'source_question':first['question_message_id'],'epoch':7}
    assert actual['v']==2 and actual['scope']==SCOPE and actual['state_revision']==1
    assert actual['validity']=={'valid':False,'reason':'invalid_summary'} and actual['artifact'] is None
    invalidation=actual['invalidation']
    assert invalidation['reason']=='invalid_summary' and invalidation['history_revision']==2
    assert invalidation['question_id']==first['question_message_id'] and invalidation['result_message_id']==result_id
    assert invalidation['diagnostic_raw']==fixture
    assert invalidation['diagnostic_sha256']==hashlib.sha256(chat_history.dumps(fixture).encode('utf-8')).hexdigest()
    epoch=actual['lineage_epoch']
    assert isinstance(epoch,str) and len(epoch)==64 and all(character in '0123456789abcdef' for character in epoch)
    assert epoch!=fixture['epoch'] and epoch!='7'
    history_raw=raw(db)
    history=chat_history.loads(history_raw)
    assert history['revision']==2 and history['next_ordinal']==3
    assert [message['ordinal'] for message in history['messages']]==[0,1,2]
    assert [message['role'] for message in history['messages']]==['user','assistant','assistant']
    assert history['messages'][:2]==before['messages']
    assert history['messages'][-1]['id']==result_id
    assert all(message['question_id']==first['question_message_id'] for message in history['messages'])
    assert repository.get(SCOPE,first['operation_id'])['state']=='completed' and finished['state']=='completed'
    replay,replay_result=complete(repository,retry,result_id=result_id)
    assert replay['state']=='completed' and replay_result==result_id
    with db.engine.connect() as c:
        assert c.execute(text("SELECT CAST(dialogue_summary AS TEXT) FROM conversations WHERE id='c'")).scalar_one()==summary_raw
    assert raw(db)==history_raw


def test_public_retry_reuses_question_and_old_results_without_second_authority(api):
    async def scenario(client):
        first=body(content='Pregunta A')
        reply=await client.post('/assistant/conversations/alice-chat/generations',json=first,headers=headers())
        assert 'event: final' in reply.text
        row=(await client.post('/assistant/conversations/alice-chat/generations',json=first,headers=headers())).json()
        retry={**body(content='Pregunta A'),'retry_of_operation_id':row['operation_id']}
        response=await client.post('/assistant/conversations/alice-chat/generations',json=retry,headers=headers())
        assert response.status_code==200,response.text
        assert 'event: final' in response.text
        value=json.loads(raw(api[1],'alice-chat'))
        assert [m['role'] for m in value['messages']]==['user','assistant','assistant']
        assert value['revision']==2
        assert all(m['question_id']==row['question_id'] for m in value['messages'])
    run(scenario,api)


def test_generation_appends_pair_to_canonical_document(api,monkeypatch):
    async def scenario(client):
        reply=await client.post('/assistant/conversations/alice-chat/generations',json=body(content='Pregunta'),headers=headers())
        assert reply.status_code==200 and 'event: final' in reply.text,reply.text
        result=api[1].fetch_messages('alice-chat','t','alice')
        value=json.loads(raw(api[1],'alice-chat'))
        assert [m['id'] for m in value['messages']]==[item['id'] for item in result]
        assert [m['ordinal'] for m in value['messages']]==[0,1]
        assert value['revision']==1
        with api[1].engine.connect() as c:
            assert c.execute(text('SELECT COUNT(*) FROM messages')).scalar_one()==0
    run(scenario,api)


def test_history_http_preserves_original_json_numbers_null_and_citations(api):
    from decimal import Decimal
    value={'schema_version':1,'identity':{'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'},
        'revision':0,'next_ordinal':2,'messages':[
            {'ordinal':0,'id':'q-preserved','role':'user','author_id':'alice','question_id':'q-preserved',
             'origin':'legacy','content':'  exacto 😀\n','metadata':{'amount':'NUMERIC_PLACEHOLDER','source_citations':[{'reference':'évidence-😀'}]},'created_at':'2026-10-10T03:12:00.123456Z'},
            {'ordinal':1,'id':'unlinked-assistant','role':'assistant','author_id':None,'question_id':None,
             'origin':'legacy','content':'Visible','metadata':None,'created_at':'2026-10-10T03:12:01.654321Z'}]}
    numeric='12345678901234567890.12345678901234567890123456789'
    encoded=json.dumps(value,ensure_ascii=False).replace('"NUMERIC_PLACEHOLDER"',numeric)
    with api[1].engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='alice-chat'"),{'doc':encoded})
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api[0],raise_app_exceptions=False),base_url='http://test') as client:
            reply=await client.get('/assistant/conversations/alice-chat',headers=headers())
            assert reply.status_code==200,reply.text
            observed=json.loads(reply.text,parse_float=Decimal)['messages']
            assert observed[0]['metadata']['amount']==Decimal(numeric)
            assert observed[1]['metadata'] is None
            assert observed[0]['metadata']['source_citations']==[{'reference':'évidence-😀'}]
            assert observed[0]['content']=='  exacto 😀\n'
            assert observed[0]['created_at'].replace('+00:00','Z')=='2026-10-10T03:12:00.123456Z'
    asyncio.run(scenario())


def test_retired_single_message_writer_cannot_create_second_history(repo):
    repository, db=repo
    before=raw(db)
    with pytest.raises(ChatError) as error:
        db.append_message(conversation_id='c',tenant_id='t',user_id='u',requester_id='u',
            role='user',content='Standalone')
    assert error.value.status==409 and raw(db)==before
    with db.engine.connect() as c:
        assert c.execute(text('SELECT COUNT(*) FROM messages')).scalar_one()==0


def test_retry_of_completed_operation_with_missing_result_is_not_admitted(repo):
    repository, db=repo
    original=create(repository)
    complete(repository,original)
    value=json.loads(raw(db))
    value['messages'].pop();value['next_ordinal']=1
    with db.engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='c'"),{'doc':json.dumps(value)})
    with pytest.raises(ChatError) as error:create(repository,retry=original['operation_id'])
    assert error.value.status==503
    with db.engine.connect() as c:
        assert c.execute(text('SELECT COUNT(*) FROM chat_operations')).scalar_one()==1


def test_foreign_operation_cannot_supply_question_for_human_retry(repo):
    repository, db=repo
    document={'schema_version':1,'identity':{**SCOPE,'conversation_id':'foreign'},'revision':0,'next_ordinal':0,'messages':[]}
    with db.engine.begin() as c:
        c.execute(text("INSERT INTO conversations (id,tenant_id,user_id,title,created_at,updated_at,dialogue_history) VALUES ('foreign','t','u','Foreign','2026-10-10T03:12:00Z','2026-10-10T03:12:00Z',:doc)"),{'doc':json.dumps(document)})
    other={**SCOPE,'conversation_id':'foreign'}
    operation,_=repository.reserve(other,{'request_id':str(uuid4()),'content':'Pregunta','screen_context':{}},{'messages':[]})
    repository.stop(other,operation['operation_id'])
    before=raw(db)
    with pytest.raises(ChatError) as error:create(repository,retry=operation['operation_id'])
    assert error.value.status==404 and raw(db)==before


def test_received_delta_does_not_change_canonical_document(api):
    async def scenario(client):
        api[2].release=asyncio.Event()
        before=raw(api[1],'alice-chat')
        payload=body()
        task=asyncio.create_task(client.post('/assistant/conversations/alice-chat/generations',json=payload,headers=headers()))
        try:
            for _ in range(100):
                await asyncio.sleep(.005)
                if api[2].claims:break
            assert len(api[2].claims)==1
            assert raw(api[1],'alice-chat')==before
            assert api[1].fetch_messages('alice-chat','t','alice')==[]
            api[2].release.set()
            result=await task
            assert 'event: delta' in result.text and 'event: final' in result.text
            assert json.loads(raw(api[1],'alice-chat'))['revision']==1
        finally:
            api[2].release.set()
            if not task.done():task.cancel()
    run(scenario,api)


def test_historical_request_without_optional_retry_field_remains_idempotent(api):
    import hashlib
    from app.schemas.chat import canonical
    async def scenario(client):
        payload=body()
        first=await client.post('/assistant/conversations/alice-chat/generations',json=payload,headers=headers())
        assert 'event: final' in first.text
        with api[1].engine.begin() as c:
            row=c.execute(text('SELECT operation_id,canonical_input FROM chat_operations')).mappings().one()
            frozen=json.loads(row['canonical_input'])
            # Exact request schema accepted and stored before the optional retry
            # field existed; preserve all other request/context/hash values.
            frozen['request'].pop('retry_of_operation_id',None)
            encoded=canonical(frozen)
            c.execute(text('UPDATE chat_operations SET canonical_input=:value,input_hash=:digest WHERE operation_id=:id'),
                {'value':encoded,'digest':hashlib.sha256(encoded.encode()).hexdigest(),'id':row['operation_id']})
        saved=raw(api[1],'alice-chat')
        repeated=await client.post('/assistant/conversations/alice-chat/generations',json=payload,headers=headers())
        assert repeated.status_code==200,repeated.text
        assert repeated.json()['outcome']=='existing' and repeated.json()['state']=='completed'
        assert len(api[2].claims)==1 and raw(api[1],'alice-chat')==saved
    run(scenario,api)


def test_optional_retry_omission_preserves_nested_null_values_and_hash(api):
    import hashlib
    from app.schemas.chat import canonical
    async def scenario(client):
        payload={**body(),'retry_of_operation_id':None}
        payload['screen_context']['selection']={'period':None,'selected_currency':None,
            'filters':{'tags':[],'subscriptions':['visible-sub'],'services':[]}}
        first=await client.post('/assistant/conversations/alice-chat/generations',json=payload,headers=headers())
        assert first.status_code==200 and 'event: final' in first.text
        with api[1].engine.connect() as c:
            row=c.execute(text('SELECT canonical_input,input_hash FROM chat_operations')).mappings().one()
        frozen=json.loads(row['canonical_input'])
        assert 'retry_of_operation_id' not in frozen['request']
        assert frozen['request']['screen_context']==payload['screen_context']
        assert hashlib.sha256(canonical(frozen).encode()).hexdigest()==row['input_hash']
        saved=raw(api[1],'alice-chat')
        duplicate=await client.post('/assistant/conversations/alice-chat/generations',json=payload,headers=headers())
        assert duplicate.status_code==200 and duplicate.json()['outcome']=='existing'
        changed={**payload,'screen_context':{**payload['screen_context'],'selection':{**payload['screen_context']['selection'],'selected_currency':'EUR'}}}
        conflict=await client.post('/assistant/conversations/alice-chat/generations',json=changed,headers=headers())
        assert conflict.status_code==409
        assert len(api[2].claims)==1 and raw(api[1],'alice-chat')==saved
    run(scenario,api)
