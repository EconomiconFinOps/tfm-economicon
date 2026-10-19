"""JUP-035 operation contract through public routes and persisted SQL effects.

SQLite is a fast transaction fixture, not Cockroach acceptance. Processor is a
scripted boundary; real private HTTP/Compose and asset loading have separate tests.
"""
import asyncio
import importlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError

from app.api.dependencies import get_current_user
from app.db.database import Database
from app.db.migration_runner import MigrationRunner


ANSWER = {
    "schema_version": "1.0", "status": "no_data", "answer": "Sin evidencia disponible.",
    "scope": {"cloud": "azure", "data_environment": "simulated", "subscription_ids": [], "period": None},
    "evidence": [], "metrics": [], "recommendations": [], "assumptions": [],
    "limitations": ["No hay datos autorizados."], "next_actions": [],
}


class Clock:
    def __init__(self):
        self.value = time.time()

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class Processor:
    """Double of a processor emitting versioned stream records, never real IA."""
    def __init__(self):
        self.claims = []
        self.errors = []
        self.release = None
        self.candidate = ANSWER

    async def descriptor(self):
        return {"v": 2, "boot_id": "synthetic-boot", "prompt_version": "synthetic-v2", "capacity": 8}

    async def stream(self, claim):
        self.claims.append(claim)
        if self.errors:
            yield {"type": "error", **self.errors.pop(0)}
            return
        yield {"type": "delta", "text": "Sin evidencia"}
        if self.release is not None:
            await self.release.wait()
        yield {"type": "candidate", "result": self.candidate, "finish_reason": "stop", "usage": None}

    async def cancel(self, claim):
        return None


@pytest.fixture
def api(tmp_path, monkeypatch):
    from app.main import app
    db = Database.__new__(Database)
    db.engine = create_engine("sqlite:///"+str(tmp_path/'operations.db'), connect_args={"check_same_thread": False})
    # SQLite's DEFAULT grammar differs; this adapter is restricted to the
    # fixture's clock default, not application queries/transaction effects.
    def sqlite_clock_default(connection, cursor, statement, parameters, context, many):
        return statement.replace('DEFAULT now()', 'DEFAULT CURRENT_TIMESTAMP').replace('version STRING PRIMARY KEY', 'version TEXT PRIMARY KEY'), parameters
    event.listen(db.engine, 'before_cursor_execute', sqlite_clock_default, retval=True)
    migrations = Path(importlib.import_module('app.db.migrations').__file__).parent
    MigrationRunner(db.engine, 'app.db.migrations', migrations).run()
    now = datetime.now(timezone.utc)
    with db.engine.begin() as c:
        c.execute(text("INSERT INTO tenants VALUES ('t','Tenant','tenant','test')"))
        for owner in ['alice','bob','carol','dave','eve']:
            c.execute(text("INSERT INTO users VALUES (:id,:email,'synthetic-password',:id,'member',:now)"),{'id':owner,'email':owner+'@example.com','now':now})
            c.execute(text("INSERT INTO user_tenants VALUES (:id,'t','member',:now)"),{'id':owner,'now':now})
            history={'schema_version':1,'identity':{'tenant_id':'t','user_id':owner,'conversation_id':owner+'-chat'},'revision':0,'next_ordinal':0,'messages':[]}
            c.execute(text("INSERT INTO conversations (id,tenant_id,user_id,title,created_at,updated_at,dialogue_history) VALUES (:id,'t',:owner,'Chat',:now,:now,:history)"),{'id':owner+'-chat','owner':owner,'now':now,'history':json.dumps(history)})
    # Production serializes transitions with SELECT FOR UPDATE on the parent.
    # SQLite omits that clause and its legacy transaction mode does not begin
    # on SELECT. Acquire its database write lock before the first read so the
    # scheduler and POST cannot both mutate the same stale revision in this
    # fixture. Native SQL tests remain responsible for production lock scope.
    @event.listens_for(db.engine, 'begin')
    def sqlite_serialized_transition(connection):
        connection.exec_driver_sql('BEGIN IMMEDIATE')
    db.test_sqlite_transition_lock = sqlite_serialized_transition
    async def identity(request: __import__('fastapi').Request):
        return {'id': request.headers.get('X-Test-User','alice')}
    app.dependency_overrides[get_current_user] = identity
    processor, clock = Processor(), Clock()
    monkeypatch.setattr(app.state,'database',db,raising=False)
    monkeypatch.setattr(app.state,'chat_transport',processor,raising=False)
    monkeypatch.setattr(app.state,'chat_clock',clock,raising=False)
    # This fixture models an enabled runtime; startup/disabled tests must not
    # leak their global app.state flag into subsequent operation tests.
    monkeypatch.setattr(app.state,'chat_enabled',True,raising=False)
    monkeypatch.setattr(app.state,'chat_max_active',8,raising=False)
    monkeypatch.setattr(app.state,'chat_scheduler_interval',0.005,raising=False)
    # Isolate operations from retrieval/tokenizer with a scoped frozen contract.
    async def context_builder(scope, payload, descriptor):
        return {'prompt_version':descriptor['prompt_version'],'messages':[
            {'role':'system','content':'Synthetic contract'},
            {'role':'user','content':payload['content']}], 'authorized_evidence':[],
            'screen_context':payload['screen_context']}
    monkeypatch.setattr(app.state,'chat_context_builder',context_builder,raising=False)
    monkeypatch.delattr(app.state,'chat_service',raising=False)
    yield app,db,processor,clock
    app.dependency_overrides.clear()
    db.dispose()


def body(owner='alice', content='¿Qué datos hay?'):
    return {'request_id':str(uuid4()),'content':content,'screen_context':{
        'schema_version':'2','screen_version':'prepared-1','route':'/assistant','tab_id':'assistant',
        'source':'loaded-screen','identity':{'tenant_id':'t','user_id':owner},
        'captured_at':'2026-10-09T22:00:00Z','selection':{},'datasets':[]}}


def headers(owner='alice'):
    return {'X-Tenant-Id':'t','X-Test-User':owner,'Authorization':'Bearer synthetic'}


def path(owner='alice'):
    return f'/assistant/conversations/{owner}-chat/generations'


def messages(db):
    return [message for owner in ['alice','bob','carol','dave','eve']
            for message in db.fetch_messages(owner+'-chat','t',owner)]


async def existing(client, payload, owner='alice'):
    result=await client.post(path(owner),json=payload,headers=headers(owner))
    assert result.status_code==200, result.text
    assert result.headers['content-type'].startswith('application/json')
    return result.json()


async def until_reserved(api, payload, owner='alice', *, claimed=False):
    """Wait for the first POST's durable precondition, not a machine-speed sleep."""
    async def poll():
        while True:
            runtime=getattr(api[0].state,'chat_service',None)
            if runtime is not None:
                row=await runtime._db(runtime.repository.existing,
                    {'tenant_id':'t','user_id':owner,'conversation_id':owner+'-chat'}, payload['request_id'])
                if row is not None and (not claimed or row['attempt_count']>0):
                    return row
            await asyncio.sleep(.005)
    return await asyncio.wait_for(poll(),2)


async def until_state(client, base, expected, owner='alice', *, attempt_count=None):
    for _ in range(100):
        r=await client.get(base,headers=headers(owner))
        assert r.status_code==200,r.text
        if r.json()['state']==expected and (attempt_count is None or r.json()['attempt_count']==attempt_count):
            return r.json()
        await asyncio.sleep(0.01)
    pytest.fail(f'Operation did not reach {expected}: {r.text}')


def run(scenario, api):
    async def execute():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api[0]),base_url='http://test') as client:
            await scenario(client)
    asyncio.run(execute())


def test_completed_pair_and_stream_are_confirmed_together(api):
    async def scenario(c):
        r=await c.post(path(),json=body(),headers=headers())
        assert r.status_code==200,r.text
        assert r.headers['content-type'].startswith('text/event-stream')
        assert r.text.index('event: delta') < r.text.index('event: final')
        rows=messages(api[1])
        assert {x['role'] for x in rows}=={'user','assistant'}
        assert len(rows)==2
        assert next(x for x in rows if x['role']=='assistant')['content']==ANSWER['answer']
        assert len(api[2].claims)==1
    run(scenario,api)


def test_required_tool_extension_validates_and_persists_only_recovered_sources(api, monkeypatch):
    import copy
    source={'id':'manual:4','kind':'corpus','title':'Synthetic manual','source':'synthetic'}
    full={**source,'content':'Review before scheduling.'}
    citation={'evidence_id':'manual:4','title':'Synthetic manual','source':'synthetic',
        'reference':'document:manual/chunk:4','excerpt':full['content'],
        'kind':'corpus','document_id':'manual','section':None,'page':None}
    calls=[];extensions=[];claims=[]
    assistant={'action': 'search', 'query': 'Review rule'}
    async def build(scope,payload,descriptor):
        return {'prompt_version':'synthetic-v2','tool_protocol':'server-documentation-v4',
            'messages':[], 'authorized_evidence':[],'source_citations':[],
            'financial_metrics_allowed':False,'response_period':None,'response_subscriptions':[]}
    async def extension(scope,context,call,deadline):
        calls.append((scope,call,deadline))
        assert context['authorized_evidence']==[] and context['financial_metrics_allowed'] is False
        effective={**context,'authorized_evidence':[full],'source_citations':[citation]}
        return {'tool_call_id':'call-synthetic','content':'Synthetic trusted result','variable_tokens':0},effective
    build.tool_extension=extension
    monkeypatch.setattr(api[0].state,'chat_context_builder',build)
    async def stream(claim):
        claims.append(copy.deepcopy(claim))
        yield {'type':'tool_call','assistant':assistant}
        assert len(extensions)==1
        yield {'type':'candidate','finish_reason':'stop','result':{**ANSWER,'status':'partial',
            'answer':full['content'],'evidence':[source]}}
    async def send(claim,result):extensions.append((copy.deepcopy(claim),result))
    monkeypatch.setattr(api[2],'stream',stream)
    monkeypatch.setattr(api[2],'tool_result',send,raising=False)
    async def scenario(client):
        response=await client.post(path(),json=body(),headers=headers())
        assert 'event: final' in response.text,response.text
        assert len(claims)==1 and len(calls)==1
        assert calls[0][0]=={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
        assert extensions[0][0]==claims[0], 'Initial signed claim must stay frozen'
        saved=messages(api[1])
        assert len(saved)==2
        metadata=next(item['metadata'] for item in saved if item['role']=='assistant')
        assert metadata['citations']==['manual:4']
        assert metadata['source_citations']==[{**citation, 'content': full['content']}]
        reopened=api[1].fetch_messages('alice-chat','t','alice')
        assert len(reopened)==2
    run(scenario,api)


def test_reservation_idempotency_busy_and_stop_without_history(api):
    async def scenario(c):
        api[2].release=asyncio.Event()
        payload=body()
        task=asyncio.create_task(c.post(path(),json=payload,headers=headers()))
        try:
            reserved_id=None
            for _ in range(100):
                with api[1].engine.connect() as connection:
                    reserved_id=connection.execute(text(
                        "SELECT operation_id FROM chat_operations WHERE tenant_id='t' "
                        "AND user_id='alice' AND conversation_id='alice-chat' "
                        "AND client_request_id=:request_id"),{'request_id':payload['request_id']}).scalar_one_or_none()
                if reserved_id is not None:
                    break
                await asyncio.sleep(0.01)
            assert reserved_id is not None,'The original request did not reserve an operation.'
            observed=await until_state(c,path()+'/'+reserved_id,'active')
            op=await existing(c,payload)
            assert op['operation_id']==reserved_id==observed['operation_id']
            assert op['state']=='active' and op['attempt_count']==1
            assert messages(api[1])==[]
            conflict=await c.post(path(),json={**payload,'content':'cambio'},headers=headers())
            assert conflict.status_code==409
            busy=await c.post(path(),json=body(),headers=headers())
            assert busy.status_code==409
            stop=await c.post(op['status_url']+'/stop',headers=headers())
            assert stop.status_code==200 and stop.json()['state']=='cancelled'
            api[2].release.set()
            await task
            assert len(api[2].claims)==1 and messages(api[1])==[]
            assert api[2].claims[0]['operation_id']==reserved_id
            assert (await c.get(op['status_url'],headers=headers())).json()['state']=='cancelled'
        finally:
            api[2].release.set()
            if not task.done(): task.cancel()
    run(scenario,api)


def test_local_capacity_wait_does_not_consume_attempt_or_reset_on_resume(api):
    api[0].state.chat_max_active=1
    async def scenario(c):
        api[2].release=asyncio.Event()
        first_payload=body()
        first=asyncio.create_task(c.post(path(),json=first_payload,headers=headers()))
        payload=body('bob')
        second=None
        try:
            # Capacity waiting has an established occupied-slot precondition.
            # Simultaneous requests are covered separately; they have no fixed winner.
            for _ in range(100):
                if api[2].claims:
                    break
                await asyncio.sleep(.01)
            assert len(api[2].claims)==1 and api[2].claims[0]['user_id']=='alice'
            active=await existing(c,first_payload)
            assert active['state']=='active' and active['attempt_count']==1
            assert active['current_attempt_id']==api[2].claims[0]['attempt_id']
            assert active['attempt_deadline'] is not None
            second=asyncio.create_task(c.post(path('bob'),json=payload,headers=headers('bob')))
            assert (await second).status_code==200
            op=await existing(c,payload,'bob')
            assert op['state']=='waiting' and op['attempt_count']==0
            assert op['current_attempt_id'] is None and op['attempt_deadline'] is None
            assert len(api[2].claims)==1 and messages(api[1])==[]
            api[3].advance(120)
            paused=await until_state(c,op['status_url'],'paused','bob')
            assert paused['wait_info']['local_remaining_ms']==0
            assert paused['wait_info']['provider_remaining_ms']==120000
            # Advancing the global fixture clock also expires Alice's claim.
            # Wait for its actual release, then occupy the slot with a fresh
            # claim whose deadline is later than the new clock value.
            # Bob's budget is checked at exactly120s above. Expiration of
            # Alice's separate claim must cross SQL's microsecond-rounded D.
            api[3].advance(.001)
            alice_op=await existing(c,first_payload)
            assert api[3]()>api[2].claims[0]['deadline']
            await until_state(c,alice_op['status_url'],'waiting')
            await c.post((await existing(c,first_payload))['status_url']+'/stop',headers=headers())
            await first
            blocker_payload=body('carol')
            blocker=asyncio.create_task(c.post(path('carol'),json=blocker_payload,headers=headers('carol')))
            for _ in range(100):
                if len(api[2].claims)==2: break
                await asyncio.sleep(.01)
            blocker_op=await existing(c,blocker_payload,'carol')
            assert blocker_op['state']=='active'
            assert datetime.fromisoformat(blocker_op['attempt_deadline'].replace('Z','+00:00')).timestamp()>api[3]()
            resumed=await c.post(op['status_url']+'/resume',headers=headers('bob'))
            assert resumed.status_code==200 and resumed.json()['state']=='paused'
            assert resumed.json()['attempt_count']==0
            assert resumed.json()['wait_info']['local_remaining_ms']==0
            await c.post(blocker_op['status_url']+'/stop',headers=headers('carol'))
            await blocker
            api[2].release.set()
            await first
            await asyncio.sleep(0.03)
            assert (await c.get(op['status_url'],headers=headers('bob'))).json()['state']=='paused'
            resumed=await c.post(op['status_url']+'/resume',headers=headers('bob'))
            assert resumed.status_code==200
            final=await until_state(c,op['status_url'],'completed','bob')
            assert final['attempt_count']==1 and final['wait_info']['local_remaining_ms']==0
            await second
        finally:
            api[2].release.set()
            for task in [first,second]:
                if task is not None and not task.done(): task.cancel()
    run(scenario,api)


@pytest.mark.parametrize('failure_source', ['repository', 'summary'])
def test_scheduler_survives_database_outage_and_completes_waiting_operation(api, monkeypatch, caplog, failure_source):
    api[0].state.chat_max_active=1
    async def scenario(c):
        api[2].release=asyncio.Event()
        first=asyncio.create_task(c.post(path(),json=body(),headers=headers()))
        try:
            for _ in range(100):
                if api[2].claims: break
                await asyncio.sleep(.01)
            assert len(api[2].claims)==1
            payload=body('bob')
            assert (await c.post(path('bob'),json=payload,headers=headers('bob'))).status_code==200
            op=await existing(c,payload,'bob')
            assert op['state']=='waiting' and op['attempt_count']==0
            service=api[0].state.chat_service
            scheduler=service.scheduler
            failed=asyncio.Event()
            restored=asyncio.Event()
            error=OperationalError('sensitive SQL', {'secret':'private-value'}, Exception('private DSN'))
            if failure_source=='repository':
                original=service.repository.recoverable
                def flaky():
                    if not restored.is_set():
                        raise error
                    return original()
                monkeypatch.setattr(service.repository,'recoverable',flaky)
            else:
                original=service.summary.recover
                async def flaky():
                    if not restored.is_set():
                        raise error
                    return await original()
                monkeypatch.setattr(service.summary,'recover',flaky)
            for _ in range(100):
                if 'Chat scheduler recovery failed' in caplog.text:
                    failed.set()
                    break
                await asyncio.sleep(.01)
            assert failed.is_set()
            assert service.scheduler is scheduler and not scheduler.done()
            assert all(value not in caplog.text for value in ['sensitive SQL','private-value','private DSN'])
            restored.set()
            api[2].release.set()
            await first
            final=await until_state(c,op['status_url'],'completed','bob')
            assert final['attempt_count']==1
            assert len(api[2].claims)==2 and len(messages(api[1]))==4
            await service.close()
            assert scheduler.cancelled()
        finally:
            api[2].release.set()
            if not first.done(): first.cancel()
            if hasattr(api[0].state,'chat_service'):
                await api[0].state.chat_service.close()
    run(scenario,api)


def test_provider_budget_accumulates_and_resume_respects_minimum_date(api):
    api[2].errors=[{'status':429,'retry_after':50},{'status':429,'retry_after':50},{'status':429,'retry_after':30}]
    async def scenario(c):
        payload=body()
        task=asyncio.create_task(c.post(path(),json=payload,headers=headers()))
        try:
            await until_reserved(api,payload,claimed=True)
            op=await existing(c,payload)
            base=op['status_url']
            for expected_count in [1,2]:
                # The scheduler can still expose the previous waiting attempt;
                # a fixed 30ms sleep is not evidence that it has advanced.
                waiting=await until_state(c,base,'waiting',attempt_count=expected_count)
                assert waiting['attempt_count']==expected_count
                api[3].advance(50)
                await asyncio.sleep(0.03)
            paused=await until_state(c,base,'paused')
            assert paused['attempt_count']==3
            assert paused['wait_info']['provider_remaining_ms']==20000
            assert paused['wait_info']['local_remaining_ms']==120000
            early=await c.post(base+'/resume',headers=headers())
            assert early.status_code==409
            api[3].advance(500)  # human pause is not automatic waiting
            resumed=await c.post(base+'/resume',headers=headers())
            assert resumed.status_code==200
            final=await until_state(c,base,'completed')
            assert final['attempt_count']==4
            assert final['wait_info']['provider_remaining_ms']==20000
            assert len({x['attempt_id'] for x in api[2].claims})==4
            await task
        finally:
            if not task.done(): task.cancel()
    run(scenario,api)


@pytest.mark.parametrize('suffix',['','/events','/result','/context','/evidence','/stop','/resume'])
def test_other_user_of_same_tenant_cannot_observe_or_control_operation(api,suffix):
    async def scenario(c):
        payload=body()
        result=await c.post(path(),json=payload,headers=headers())
        assert result.status_code==200,result.text
        op=await existing(c,payload)
        r=await c.request('POST' if suffix in ['/stop','/resume'] else 'GET',op['status_url']+suffix,headers=headers('bob'))
        assert r.status_code==404,r.text
        assert 'private_control' not in r.text and len(api[2].claims)==1
    run(scenario,api)


def test_invalid_final_never_commits_partial_pair(api):
    api[2].candidate={**ANSWER,'status':'ok','evidence':[{'id':'alien','kind':'corpus','title':'Alien','source':'unknown'}]}
    async def scenario(c):
        payload=body()
        r=await c.post(path(),json=payload,headers=headers())
        assert r.status_code==200,r.text
        assert 'event: final' not in r.text
        op=await existing(c,payload)
        assert op['state']=='failed'
        assert len(api[2].claims)==1 and messages(api[1])==[]
    run(scenario,api)


def test_sql_failure_after_question_insert_rolls_back_without_another_model_call(api):
    with api[1].engine.begin() as connection:
        connection.execute(text("""CREATE TRIGGER reject_synthetic_final BEFORE UPDATE OF dialogue_history ON conversations
            BEGIN SELECT RAISE(ABORT,'synthetic final document failure'); END"""))
    async def scenario(c):
        payload=body()
        r=await c.post(path(),json=payload,headers=headers())
        assert r.status_code==200 and 'event: final' not in r.text
        op=await existing(c,payload)
        assert op['state']=='failed'
        assert messages(api[1])==[]
        assert len(api[2].claims)==1
        with api[1].engine.connect() as connection:
            row=connection.execute(text('SELECT question_content FROM chat_operations WHERE operation_id=:id'),{'id':op['operation_id']}).first()
            assert row[0]==payload['content']
    run(scenario,api)


def test_confirmed_stop_fences_a_complete_candidate_even_in_commit_race(api):
    from app.db.chat_repository import ChatError
    async def scenario(c):
        api[2].release=asyncio.Event()
        payload=body()
        task=asyncio.create_task(c.post(path(),json=payload,headers=headers()))
        try:
            await until_reserved(api,payload,claimed=True)
            op=await existing(c,payload)
            attempt=op['current_attempt_id']
            r=await c.post(op['status_url']+'/stop',headers=headers())
            assert r.status_code==200 and r.json()['state']=='cancelled'
            # Simulate a complete candidate already received before Stop but
            # committed after it: SQL fence, not cooperative cancellation alone.
            repo=api[0].state.chat_service.repository
            with pytest.raises(ChatError) as failure:
                repo.complete({'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'},
                              op['operation_id'],attempt,ANSWER,{},str(uuid4()))
            assert failure.value.status==409
            assert messages(api[1])==[]
            api[2].release.set()
            await task
        finally:
            api[2].release.set()
            if not task.done(): task.cancel()
    run(scenario,api)


@pytest.mark.parametrize('kind',['same','changed_payload','different_intent'])
def test_concurrent_reserve_resolves_unique_conflict_without_duplicate_intent(api,kind):
    """Both prechecks see no row; real SQLite UNIQUE arbitration decides winner.

    SQLSTATE23505 is covered separately against Cockroach; this fixture reports
    its actual SQLite2067 category rather than claiming database equivalence.
    """
    from concurrent.futures import ThreadPoolExecutor
    # This test deliberately bypasses parent-lock serialization to exercise the
    # UNIQUE fallback itself; retain its real two-writer constraint conflict.
    event.remove(api[1].engine, 'begin', api[1].test_sqlite_transition_lock)
    from threading import Barrier
    from app.db.chat_repository import ChatError, ChatRepository
    repository=ChatRepository(api[1],api[3])
    scope={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
    left=body()
    right=left.copy()
    if kind=='changed_payload': right['content']='Otra pregunta'
    if kind=='different_intent': right['request_id']=str(uuid4())
    barrier=Barrier(2)
    unique_codes=[]
    def before_insert(connection,cursor,statement,parameters,context,many):
        if statement.startswith('INSERT INTO chat_operations '):
            barrier.wait(timeout=5)
    def record_failure(context):
        unique_codes.append(getattr(context.original_exception,'sqlite_errorcode',None))
    event.listen(api[1].engine,'before_cursor_execute',before_insert)
    event.listen(api[1].engine,'handle_error',record_failure)
    def reserve(payload):
        try: return repository.reserve(scope,payload,{'prompt_version':'synthetic-v2'})
        except ChatError as failure: return failure
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(reserve,payload) for payload in (left,right)]
            results=[future.result(timeout=10) for future in futures]
    finally:
        event.remove(api[1].engine,'before_cursor_execute',before_insert)
        event.remove(api[1].engine,'handle_error',record_failure)
    assert unique_codes==[2067],unique_codes
    created=[result for result in results if isinstance(result,tuple) and result[1]]
    assert len(created)==1
    if kind=='same':
        assert all(isinstance(result,tuple) for result in results),[(getattr(r,'status',None),getattr(r,'code',None)) for r in results]
        assert results[0][0]['operation_id']==results[1][0]['operation_id']
        assert sorted(result[1] for result in results)==[False,True]
    else:
        failure=next(result for result in results if isinstance(result,ChatError))
        assert (failure.status,failure.code)==(409,'intent_conflict' if kind=='changed_payload' else 'conversation_busy')
    with api[1].engine.connect() as connection:
        assert connection.execute(text('SELECT COUNT(*) FROM chat_operations')).scalar_one()==1
    assert messages(api[1])==[] and api[2].claims==[]


def test_genuine_reservation_storage_failure_remains_sanitized_503(api):
    from app.db.chat_repository import ChatError, ChatRepository
    with api[1].engine.begin() as connection:
        connection.execute(text("CREATE TRIGGER reject_operation BEFORE INSERT ON chat_operations BEGIN SELECT RAISE(ABORT,'synthetic-private-storage-detail'); END"))
    with pytest.raises(ChatError) as failure:
        ChatRepository(api[1],api[3]).reserve({'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'},body(),{})
    assert (failure.value.status,failure.value.code)==(503,'storage_unavailable')
    assert 'private-storage-detail' not in str(failure.value)
    assert messages(api[1])==[]


def test_expired_claim_frees_slot_for_explicit_resume_without_restoring_wait_budget(api):
    api[0].state.chat_max_active=1
    async def scenario(c):
        api[2].release=asyncio.Event()
        first_payload=body()
        first=asyncio.create_task(c.post(path(),json=first_payload,headers=headers()))
        await until_reserved(api,first_payload,claimed=True)
        second_payload=body('bob')
        second=asyncio.create_task(c.post(path('bob'),json=second_payload,headers=headers('bob')))
        try:
            await until_reserved(api,second_payload,'bob')
            op=await existing(c,second_payload,'bob')
            assert op['state']=='waiting' and op['attempt_count']==0
            api[3].advance(120)
            paused=await until_state(c,op['status_url'],'paused','bob')
            assert paused['wait_info']['local_remaining_ms']==0
            api[3].advance(.001)
            first_op=await existing(c,first_payload)
            # The scheduler can already have cleared the old attempt; use
            # its recorded first claim deadline rather than a nullable field.
            assert api[3]()>api[2].claims[0]['deadline']
            await until_state(c,first_op['status_url'],'waiting')
            await c.post(first_op['status_url']+'/stop',headers=headers())
            await first
            resumed=await c.post(op['status_url']+'/resume',headers=headers('bob'))
            assert resumed.status_code==200 and resumed.json()['state']=='active'
            assert resumed.json()['attempt_count']==1
            assert resumed.json()['wait_info']['local_remaining_ms']==0
            assert resumed.json()['wait_info']['provider_remaining_ms']==120000
            api[2].release.set()
            final=await until_state(c,op['status_url'],'completed','bob')
            assert final['attempt_count']==1
            await second
        finally:
            api[2].release.set()
            for task in [first,second]:
                if not task.done(): task.cancel()
    run(scenario,api)
