"""The private claim and ledger must use the actual durable SQL deadline."""
import math
import time

import pytest

from app.db.chat_repository import ChatError, ChatRepository
from test_chat_operations_jup035 import ANSWER, api, body


@pytest.mark.parametrize('fraction', [.0000003, .0000008, .1234563, .1234568, .9999998])
def test_claim_and_ledger_use_persisted_deadline_without_extending_attempt(api, fraction):
    _,database,_,clock=api
    clock.value=math.floor(time.time())+fraction
    scope={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
    repository=ChatRepository(database,clock)
    context={'prompt_version':'synthetic-v2','messages':[{'role':'system','content':'Synthetic'},
             {'role':'user','content':'Question'}],'authorized_evidence':[]}
    reserved,created=repository.reserve(scope,body(),context)
    assert created
    claimed,won=repository.claim(scope,reserved['operation_id'],'synthetic-boot')
    assert won and claimed['attempt_count']==1
    persisted=repository.get(scope,claimed['operation_id'])
    assert claimed['attempt_deadline']==persisted['attempt_deadline'], 'A valid private claim must never exceed its SQL fence'
    assert claimed['attempts'][-1]['deadline']==persisted['attempt_deadline'], 'The attempt ledger must record the same durable deadline'
    assert claimed['attempt_deadline']<=clock.value+120, 'Precision handling cannot buy a longer attempt'
    assert 0<=clock.value+120-claimed['attempt_deadline']<.000002
    with pytest.raises(ChatError) as wrong:
        repository.complete(scope,claimed['operation_id'],'foreign-attempt',ANSWER,{},'foreign-result')
    assert wrong.value.status==409 and wrong.value.code=='attempt_not_current'
    assert database.fetch_messages('alice-chat','t','alice')==[]
    duplicate,again=repository.claim(scope,claimed['operation_id'],'synthetic-boot')
    assert not again and duplicate['attempt_count']==1
    assert duplicate['attempt_deadline']==claimed['attempt_deadline']
    clock.value=persisted['attempt_deadline']
    with pytest.raises(ChatError) as error:
        repository.complete(scope,claimed['operation_id'],claimed['current_attempt_id'],ANSWER,{},'must-not-exist')
    assert error.value.status==409 and error.value.code=='attempt_not_current'
    assert database.fetch_messages('alice-chat','t','alice')==[]
    clock.value=persisted['attempt_deadline']-1
    repository.stop(scope,claimed['operation_id'])
    with pytest.raises(ChatError) as stopped:
        repository.complete(scope,claimed['operation_id'],claimed['current_attempt_id'],ANSWER,{},'stopped-result')
    assert stopped.value.status==409
    assert database.fetch_messages('alice-chat','t','alice')==[]
