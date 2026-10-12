"""Context uses canonical links/ordinals, excludes legitimate unpaired legacy."""
import asyncio
import copy
import json

import pytest
from sqlalchemy import event,text

from app.services.chat_context import ChatContext
from test_chat_operations_jup035 import api,body,headers,run
from test_chat_context_assembly_jup035 import prepared,initialize,current


SCOPE={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
STAMP='2026-10-10T03:12:00.123456Z'


def install(db,records, *, verified=False):
    messages=[]
    for ordinal,(identifier,role,question,metadata) in enumerate(records):
        messages.append({'ordinal':ordinal,'id':identifier,'role':role,'author_id':'alice',
            'question_id':question,'origin':'legacy','content':'Texto '+identifier,
            'metadata':metadata,'created_at':STAMP})
    value={'schema_version':1,'identity':dict(SCOPE),'revision':0,'next_ordinal':len(messages),'messages':messages}
    if verified:
        for message in messages:
            message['origin']='completed'
            if message['role']=='assistant':
                message['metadata']={'generation':{'v':2,'state':'completed','question_message_id':message['question_id']}}
    with db.engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='alice-chat'"),{'doc':json.dumps(value)})
    return value


def test_no_guessing_legacy_adjacent_question_without_canonical_link(api):
    install(api[1],[('q','user','q',{}),('a','assistant',None,{})])
    pairs,older=ChatContext(api[0],None).recent_pairs(SCOPE)
    assert pairs==[] and older==0


@pytest.mark.parametrize('metadata',[None,[],['opaque'],'opaque',{'generation':None},{'generation':[]},{'generation':{'question_message_id':'q'}}])
def test_opaque_legacy_metadata_cannot_override_null_canonical_link(api,metadata):
    install(api[1],[('q','user','q',{}),('a','assistant',None,metadata)])
    pairs,older=ChatContext(api[0],None).recent_pairs(SCOPE)
    assert pairs==[] and older==0


def test_canonical_link_not_original_metadata_selects_pair_and_latest_by_ordinal(api):
    value=install(api[1],[('q-A','user','q-A',{}),('a-A','assistant','q-A',None),
        ('q-B','user','q-B',{}),('a-B','assistant','q-B',{}),
        ('retry-A','assistant','q-A',{'generation':{'question_message_id':'q-B'}})])
    value['messages'][-1]['created_at']='2020-01-01T00:00:00.000001Z'
    with api[1].engine.begin() as c:
        c.execute(text("UPDATE conversations SET dialogue_history=:doc WHERE id='alice-chat'"),{'doc':json.dumps(value)})
    from app.db import chat_history
    pairs,_=chat_history.latest_pairs(value)
    older=0
    assert [(p['question_id'],p['answer_id']) for p in pairs]==[('q-A','retry-A'),('q-B','a-B')]
    assert older==0
    assert ChatContext(api[0],None).recent_pairs(SCOPE)[0]==[]


def test_other_legacy_role_with_reference_is_not_an_assistant_answer(api):
    install(api[1],[('q','user','q',{}),('system','system','q',{'generation':{'question_message_id':'q'}})])
    pairs,_=ChatContext(api[0],None).recent_pairs(SCOPE)
    assert pairs==[]


def test_context_declares_unpaired_messages_and_never_reads_frozen_table(prepared):
    api,_=prepared
    install(api[1],[('q','user','q',{}),('a','assistant',None,{})])
    statements=[]
    event.listen(api[1].engine,'before_cursor_execute',
        lambda c,cursor,statement,args,context,many:statements.append(statement))
    async def scenario(client):
        await initialize(api[0])
        result=await client.post('/assistant/conversations/alice-chat/generations',json=body(),headers=headers())
        assert result.status_code==200 and 'event: final' in result.text
        context,value=current(api)
        assert value['recent_pairs']==[]
        excluded=[entry for entry in value['omissions'] if entry.get('collection')=='dialogue_unpaired']
        assert excluded and excluded[0]['omitted_messages']==2
        assert set(excluded[0]['reasons'])=={'incomplete_legacy_question','unlinked_legacy_message'}
        assert not any('FROM messages' in statement or 'JOIN messages' in statement for statement in statements)
    run(scenario,api)
