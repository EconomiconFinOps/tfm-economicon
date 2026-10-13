"""Chronological history uses complete logical pairs even with adversarial UUIDs."""
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from importlib import import_module

import app.db.chat_repository as repository_module
from app.db.chat_repository import ChatRepository
from app.services.chat_context import ChatContext
from test_chat_operations_jup035 import ANSWER, api, body, headers, run

SCOPE={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}


def complete_pair(api,monkeypatch,number):
    _,database,_,clock=api
    ids=iter(f'{prefix}0000000-0000-4000-8000-{number:012d}' for prefix in ('e','f','c','d'))
    monkeypatch.setattr(repository_module,'uuid4',lambda:next(ids))
    repository=ChatRepository(database,clock)
    payload=body(content=f'Pregunta {number}')
    row,created=repository.reserve(SCOPE,payload,{'messages':[],'authorized_evidence':[]})
    assert created
    claim,won=repository.claim(SCOPE,row['operation_id'],'synthetic')
    assert won
    result_id=f'00000000-0000-4000-8000-{number:012d}'
    metadata={'generation':{'question_message_id':row['question_message_id']},'unchanged':'value'}
    result={**ANSWER,'answer':f'Respuesta {number}'}
    completed=repository.complete(SCOPE,row['operation_id'],claim['current_attempt_id'],result,metadata,result_id)
    assert completed['state']=='completed'
    return row['question_message_id'],result_id,metadata


def insert(database,identifier,role,at,metadata=None,owner='alice'):
    database.test_legacy_rows_staged=True
    with database.engine.begin() as connection:
        connection.execute(text('INSERT INTO messages(id,conversation_id,tenant_id,user_id,role,content,metadata,created_at) '
            'VALUES(:id,:conversation,:tenant,:user,:role,:content,:metadata,:at)'),
            {'id':identifier,'conversation':owner+'-chat','tenant':'t','user':owner,'role':role,
             'content':identifier,'metadata':json.dumps(metadata),'at':datetime.fromtimestamp(at,timezone.utc)})


def history(api):
    if getattr(api[1],'test_legacy_rows_staged',False):
        # Historical rows are staged exclusively in this owned SQLite fixture,
        # then imported through the real approved migration before any reader.
        # Active backend readers must not infer a fallback from these rows.
        with api[1].engine.begin() as connection:
            connection.execute(text('UPDATE conversations SET dialogue_history=NULL'))
        import_module('app.db.migrations.003_dialogue_history').backfill(api[1].engine)
        api[1].test_legacy_rows_staged=False
    return api[1].fetch_messages('alice-chat','t','alice')


def test_real_atomic_pair_is_question_then_answer_through_private_history(api,monkeypatch):
    question,answer,metadata=complete_pair(api,monkeypatch,1)
    assert answer<question  # Adversarial IDs; no dependence on chance.
    rows=history(api)
    assert [row['id'] for row in rows]==[question,answer]
    assert [row['role'] for row in rows]==['user','assistant']
    assert rows[0]['created_at']==rows[1]['created_at']
    assert rows[1]['metadata']==metadata
    async def scenario(client):
        reply=await client.get('/assistant/conversations/alice-chat',headers=headers())
        assert reply.status_code==200
        assert [row['id'] for row in reply.json()['messages']]==[question,answer]
        foreign=await client.get('/assistant/conversations/alice-chat',headers=headers('bob'))
        assert foreign.status_code==404
    run(scenario,api)


def test_multiple_pairs_at_same_instant_are_adjacent_stable_and_keep_recent_pair_references(api,monkeypatch):
    one=complete_pair(api,monkeypatch,1)
    two=complete_pair(api,monkeypatch,2)
    expected=[one[0],one[1],two[0],two[1]]
    first=history(api)
    assert [row['id'] for row in first]==expected
    assert [row['role'] for row in first]==['user','assistant','user','assistant']
    assert history(api)==first
    recent,omitted=ChatContext(api[0],None).recent_pairs(SCOPE)
    assert omitted==0
    assert [(row['question_id'],row['answer_id']) for row in recent]==[(one[0],one[1]),(two[0],two[1])]


@pytest.mark.parametrize('reference',['missing','0-foreign','z-assistant'])
def test_unknown_foreign_or_assistant_references_cannot_group_authorized_history(api,reference):
    at=api[3].value
    insert(api[1],'0-foreign','user',at,owner='bob')
    insert(api[1],'m-user','user',at)
    insert(api[1],'z-assistant','assistant',at)
    metadata={'generation':{'question_message_id':reference}}
    insert(api[1],'a-answer','assistant',at,metadata)
    rows=history(api)
    assert [row['id'] for row in rows]==['a-answer','m-user','z-assistant']
    assert rows[0]['metadata']==metadata
    assert api[1].fetch_messages('alice-chat','t','bob')==[]


@pytest.mark.parametrize('generation',[None,[],'malformed',{'question_message_id':[]},
    {'question_message_id':{}},{'question_message_id':1}])
def test_malformed_generation_metadata_does_not_raise_or_change_legacy_order(api,generation):
    at=api[3].value
    insert(api[1],'m-user','user',at)
    metadata={'generation':generation}
    insert(api[1],'a-answer','assistant',at,metadata)
    rows=history(api)
    assert [row['id'] for row in rows]==['a-answer','m-user']
    assert rows[0]['metadata']==metadata


def test_different_dates_and_later_retry_keep_chronology_and_latest_answer(api):
    at=api[3].value
    insert(api[1],'old-question','user',at)
    insert(api[1],'original-answer','assistant',at+1,{'generation':{'question_message_id':'old-question'}})
    insert(api[1],'new-question','user',at+2)
    insert(api[1],'new-answer','assistant',at+3,{'generation':{'question_message_id':'new-question'}})
    insert(api[1],'0-late-retry','assistant',at+4,{'generation':{'question_message_id':'old-question'}})
    rows=history(api)
    assert [row['id'] for row in rows]==['old-question','original-answer','new-question','new-answer','0-late-retry']
    assert [row['created_at'] for row in rows]==sorted(row['created_at'] for row in rows)
    recent,omitted=ChatContext(api[0],None).recent_pairs(SCOPE)
    assert omitted==0
    assert [(row['question_id'],row['answer_id']) for row in recent]==[
        ('old-question','0-late-retry'),('new-question','new-answer')]


def test_a_user_generation_reference_is_not_an_assistant_link(api):
    at=api[3].value
    insert(api[1],'m-user','user',at)
    insert(api[1],'a-other-user','user',at,{'generation':{'question_message_id':'m-user'}})
    assert [row['id'] for row in history(api)]==['a-other-user','m-user']


def test_later_retry_at_another_question_time_does_not_change_its_id_tiebreak(api):
    at=api[3].value
    insert(api[1],'z-old-question','user',at)
    insert(api[1],'m-new-question','user',at+1)
    insert(api[1],'a-later-retry','assistant',at+1,
        {'generation':{'question_message_id':'z-old-question'}})
    assert [row['id'] for row in history(api)]==['z-old-question','a-later-retry','m-new-question']


def test_legacy_nonobject_metadata_is_preserved_without_exception(api):
    at=api[3].value
    insert(api[1],'m-user','user',at)
    insert(api[1],'a-answer','assistant',at,['legacy-opaque'])
    rows=history(api)
    assert [row['id'] for row in rows]==['a-answer','m-user']
    assert rows[0]['metadata']==['legacy-opaque']
