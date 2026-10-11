"""Scoped cold RAM scheduler through the existing ChatOperations constructor.

All private responses here are labelled synthetic boundary fixtures. Real
counted HTTP/gateway behavior is demonstrated separately; no LLM fidelity claim.
"""
import asyncio,copy,hashlib,json,time,threading
from datetime import datetime,timezone
from uuid import uuid4
import httpx,pytest
from sqlalchemy import text
from app.db import chat_history
from app.db.chat_repository import ChatError
from app.services.chat_operations import ChatOperations
from app.services.summary_validation import validate_output
from test_chat_operations_jup035 import api,body,headers,path,existing,until_state,Processor
from test_chat_summary_lifecycle_jup035 import summary_resources53

SCOPE={'tenant_id':'t','user_id':'alice','conversation_id':'alice-chat'}
def digest(value):return hashlib.sha256(chat_history.dumps(value).encode()).hexdigest()

class SyntheticSummaryBoundary:
    def __init__(self,app,resources):
        self.app=app;self.resources=resources;self.calls=[];self.controls=[];self.results={}
        self.release=None;self.mode='valid';self.confirmed=False
    async def descriptor(self):
        return {'v':2,'boot_id':'synthetic-boot','summary_version':self.resources.summary_version,
            'manifest_sha256':hashlib.sha256(self.resources.manifest_bytes).hexdigest(),
            'tokenizer_sha256':self.resources.tokenizer_sha256,'response_schema_sha256':self.resources.response_schema_sha256,
            'capacity':self.app.state.chat_max_active,'admission_policy':'jup-035.summary-one-reserve-five.v2','summary_ready':True,
            'context_budget':self.resources.context_budget}
    async def submit(self,envelope):
        self.calls.append(copy.deepcopy(envelope))
        pairs=envelope['payload']['pairs']
        output={'v':2,'topics':[{'text':'Preguntas sobre diálogo, sin autoridad financiera.',
            'question_refs':[p['question_ref'] for p in pairs],'answer_refs':[p['answer_ref'] for p in pairs]}],
            'facts':[{'quote':pairs[0]['answer'].split(';')[0],'source_ref':pairs[0]['answer_ref']}],
            'limitations':['La memoria describe diálogo y no acredita datos financieros.']}
        if self.mode=='invalid':output['facts'][0]['quote']='Literal inexistente en fuentes'
        receipt={'synthetic':True,'call_id':str(uuid4()),'dispatch_count':1,'input_hash':envelope['input_hash'],
            'output_hash':digest(output),'usage':None,'cost':None,'boot_id':envelope['boot_id'],'summary_version':envelope['summary_version']}
        value={k:envelope[k] for k in ['job_id','scope','boot_id','input_hash','summary_version']}
        value.update(v=2,state='completed',settled=True,output=output,receipt=receipt);self.results[envelope['job_id']]=value
        if self.release is not None:await self.release.wait()
        if self.mode in ['uncertain','lost_ack_completed']:raise ChatError(503,'summary_outcome_unknown')
        return copy.deepcopy(value)
    async def status(self,envelope):
        self.controls.append(('status',envelope['job_id']))
        if self.mode=='uncertain' and not self.confirmed:
            return self.control(envelope,'running',False)
        if self.mode=='uncertain':
            return self.control(envelope,'cancelled',True)
        return copy.deepcopy(self.results[envelope['job_id']])
    def control(self,envelope,state,settled):
        return {**{k:envelope[k] for k in ['job_id','scope','boot_id','input_hash','summary_version']},'v':2,'state':state,'settled':settled}
    async def cancel(self,envelope):
        self.controls.append(('cancel',envelope['job_id']))
        if self.mode=='uncertain' and not self.confirmed:
            return self.control(envelope,'cancelling',False)
        if self.release is not None:self.release.set()
        return self.control(envelope,'cancelled',True)
    def validate_output(self,value,sources,resources):return validate_output(value,sources,resources)
    async def close(self):
        if self.release is not None:self.release.set()
        self.confirmed=True

@pytest.fixture
def packet(api,summary_resources53,monkeypatch):
    from dataclasses import replace
    monkeypatch.setenv('CHAT_CONTEXT_TOKENS','8192')
    summary_resources53=replace(summary_resources53,
        context_budget={**summary_resources53.context_budget,'context_tokens':14096})
    application,db,main,clock=api
    monkeypatch.setenv('SUMMARY_ENABLED','true')
    monkeypatch.setattr(application.state,'summary_resources',summary_resources53,raising=False)
    summary=SyntheticSummaryBoundary(application,summary_resources53)
    main.summary=summary
    return application,db,main,summary,summary_resources53,clock

def runtime(packet):
    value=ChatOperations(packet[0])
    child=getattr(value,'summary',None)
    assert child is not None,'Existing ChatOperations constructor exposes no bounded summary service'
    notify=child.on_completed
    def committed(scope,context,event_id):
        # Synthetic committed events now include their durable barrier. Native
        # final tests below still exercise the real atomic final transaction.
        def pending(c):
            busy=c.execute(text("SELECT 1 FROM chat_operations WHERE tenant_id=:tenant_id AND user_id=:user_id "
                "AND conversation_id=:conversation_id AND state IN ('active','waiting','paused')"),scope).first()
            if not busy and value.repository.compactions.read(c,scope) is None:
                value.repository.compactions.pending(c,scope)
        if child.enabled:
            try:value.repository._transaction(scope,pending)
            except ChatError as error:
                if error.status!=404:raise
        return notify(scope,context,event_id)
    child.on_completed=committed
    return value,child

def source(packet,count=12,long=True,scope=None,first_large=False):
    scope=scope or SCOPE;db=packet[1];now=datetime.now(timezone.utc)
    for index in range(count):
        qid=str(uuid4());common={'conversation_id':scope['conversation_id'],'tenant_id':scope['tenant_id'],
            'requester_id':scope['user_id'],'created_at':now}
        question='Pregunta '+str(index)+'. '+(('diálogo histórico '*400) if long else '¿Qué se preguntó?')
        if first_large and index==0:question='diálogo '*10000
        q={**common,'id':qid,'user_id':scope['user_id'],'role':'user','content':question,
            'metadata':{'marker':'SYNTHETIC_METADATA_NEVER_SUMMARY_MODEL'}}
        a={**common,'id':str(uuid4()),'user_id':scope['user_id'],'role':'assistant',
            'content':'No se confirmó una conclusión financiera.; Se conserva el diálogo.',
            'metadata':{'generation':{'question_message_id':qid}}}
        db.append_pair(question=q,assistant=a)
    return document(packet,scope)

def document(packet,scope=SCOPE):
    with packet[1].engine.connect() as c:
        raw=c.execute(text('SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id=:conversation_id '
            'AND tenant_id=:tenant_id AND user_id=:user_id'),scope).scalar_one()
    return chat_history.loads(raw)

def derived(packet,scope=SCOPE):
    with packet[1].engine.connect() as c:
        raw=c.execute(text('SELECT CAST(dialogue_summary AS TEXT) FROM conversations WHERE id=:conversation_id '
            'AND tenant_id=:tenant_id AND user_id=:user_id'),scope).scalar_one()
    return None if raw is None else chat_history.loads(raw)

def context(essentials=0):return {'manifest':{'variable_tokens':essentials}}
async def idle(child):await asyncio.wait_for(child.wait_idle(),3)
async def calls_at_least(boundary,count):
    for _ in range(200):
        if len(boundary.calls)>=count:return
        await asyncio.sleep(.005)
    pytest.fail('Synthetic boundary never received scheduled job')

@pytest.mark.parametrize('flag',['false','TRUE','1','yes'])
def test_server_only_disabled_or_invalid_enable_does_not_dispatch_or_break_main(packet,monkeypatch,flag):
    monkeypatch.setenv('SUMMARY_ENABLED',flag);service,child=runtime(packet);source(packet)
    async def run():
        try:
            child.on_completed(SCOPE,context(),event_id=str(uuid4()))
            await idle(child)
            assert packet[3].calls==[] and service.occupied==0
            row,_=await service.open(SCOPE,body())
            for _ in range(100):
                actual=await service.get(SCOPE,row['operation_id'])
                if actual['state']=='completed':break
                await asyncio.sleep(.01)
            assert actual['state']=='completed' and len(packet[2].claims)==1 and packet[3].calls==[]
        finally:await service.close()
    asyncio.run(run())

def test_startup_and_get_are_cold_even_with_eligible_old_history(packet):
    service,child=runtime(packet);source(packet)
    async def run():
        try:
            service.start()
            await service.requests({'tenant_id':'t','user_id':'alice'})
            for _ in range(3):child.state(SCOPE)
            await asyncio.sleep(.05);await idle(child)
            assert packet[3].calls==[] and derived(packet) is None
        finally:await service.close()
    asyncio.run(run())

def test_oldest_contiguous_two_lots_reuse_exact_confirmed_previous_and_preserve_originals(packet):
    service,child=runtime(packet);before=document(packet);source(packet);before=document(packet);raw=digest(before)
    async def run():
        try:
            child.on_completed(SCOPE,context(),event_id=str(uuid4()));await idle(child)
            calls=packet[3].calls
            assert len(calls)==2
            first,second=calls
            assert first['payload']['previous_summary'] is None
            assert second['payload']['previous_summary']==packet[3].results[first['job_id']]['output']
            assert second['parent_hash'] is not None and first['job_id']!=second['job_id']
            assert all(0<call['selected_pairs']<=len(chat_history.latest_pairs(before)[0])-4 for call in calls)
            assert all(call['deadline']<=time.time()+30 and digest(call['payload'])==call['input_hash'] for call in calls)
            assert 'SYNTHETIC_METADATA_NEVER_SUMMARY_MODEL' not in json.dumps([call['payload'] for call in calls])
            state=derived(packet);artifact=state['artifact']
            assert state['validity']['valid'] and artifact['previous_payload_used']==packet[3].results[first['job_id']]['output']
            assert len(artifact['source_refs'])==sum(call['selected_pairs'] for call in calls)
            assert artifact['source_refs']==first['source_refs']+second['source_refs']
            assert len(artifact['source_refs'])<=len(chat_history.latest_pairs(before)[0])-4
            assert digest(document(packet))==raw
            assert artifact['observations']['usage'] is None and artifact['observations']['cost'] is None
            assert service.occupied==0
        finally:await service.close()
    asyncio.run(run())

def test_small_history_does_not_trigger_without_pressure_but_pressure_does(packet):
    service,child=runtime(packet);source(packet,count=5,long=False)
    async def run():
        try:
            child.on_completed(SCOPE,context(),event_id=str(uuid4()));await idle(child);assert packet[3].calls==[]
            child.on_completed(SCOPE,context(8192),event_id=str(uuid4()));await idle(child)
            assert len(packet[3].calls)==1 and packet[3].calls[0]['selected_pairs']==1
            assert len(derived(packet)['artifact']['source_refs'])==1
        finally:await service.close()
    asyncio.run(run())

def test_durable_pending_continues_in_bounded_ticks_without_empty_wake_loop(packet):
    service,child=runtime(packet);source(packet)
    async def run():
        try:
            child.on_completed(SCOPE,context(),event_id=str(uuid4()));await idle(child);count=len(packet[3].calls);assert count==2
            for _ in range(5):child.wake();child.state(SCOPE)
            await idle(child);assert len(packet[3].calls)==count
            pending=service.repository.compactions.get(SCOPE)
            assert pending['state']=='pending' and child.state(SCOPE)['blocked']
            await child.recover();await idle(child)
            assert count<len(packet[3].calls)<=count+2
            assert len({call['job_id'] for call in packet[3].calls})==len(packet[3].calls)
            assert all(call['payload']['pairs'] for call in packet[3].calls)
        finally:await service.close()
    asyncio.run(run())

def test_oversized_oldest_pair_never_skips_truncates_or_advances_frontier(packet):
    service,child=runtime(packet);source(packet,count=8,long=False,first_large=True);original=digest(document(packet))
    async def run():
        try:
            child.on_completed(SCOPE,context(),event_id=str(uuid4()));await idle(child)
            assert packet[3].calls==[] and derived(packet) is None and digest(document(packet))==original
            assert child.state(SCOPE)['reason']=='pending_pair_too_large' and service.occupied==0
        finally:await service.close()
    asyncio.run(run())

def test_coalescing_limits_same_scope_to_one_task_and_two_lots_without_empty_loop(packet):
    service,child=runtime(packet);source(packet)
    async def run():
        try:
            for _ in range(20):child.on_completed(SCOPE,context(),event_id=str(uuid4()))
            await idle(child)
            assert len(packet[3].calls)==2 and child.state_count==0 and service.occupied==0
            assert service.repository.compactions.get(SCOPE)['state']=='pending'
            await asyncio.sleep(.05);assert len(packet[3].calls)==2
        finally:await service.close()
    asyncio.run(run())

def test_cold_ram_queue_bounds_scopes_to_32_without_evicting_uncertain_record(packet):
    service,child=runtime(packet)
    async def run():
        try:
            accepted=[child.on_completed({**SCOPE,'conversation_id':'synthetic-scope-'+str(i)},context(),event_id=str(uuid4())) for i in range(33)]
            assert accepted[:32]==[True]*32 and accepted[32] is False and child.state_count==32
            await idle(child);assert packet[3].calls==[] and child.state_count<=32
        finally:await service.close()
    asyncio.run(run())

@pytest.mark.parametrize('capacity,main_active,admit',[(5,0,False),(6,0,True),(6,1,False),(7,1,True),(7,2,False),(8,2,True),(8,3,False)])
def test_backend_reserves_summary_in_same_lock_only_with_five_main_slots_free(packet,monkeypatch,capacity,main_active,admit):
    monkeypatch.setattr(packet[0].state,'chat_max_active',capacity)
    service,child=runtime(packet);source(packet,count=5,long=False)
    async def run():
        boundary=packet[3];boundary.release=asyncio.Event();service.occupied=main_active
        try:
            child.on_completed(SCOPE,context(8192),event_id=str(uuid4()))
            for _ in range(100):
                if boundary.calls or child.state(SCOPE).get('reason')=='capacity_deferred':break
                await asyncio.sleep(.005)
            assert bool(boundary.calls) is admit
            assert service.occupied==main_active+(1 if admit else 0) and service.occupied<=capacity
            if admit:
                child.on_completed(SCOPE,context(8192),event_id=str(uuid4()))
                await asyncio.sleep(.02);assert len(boundary.calls)==1
        finally:
            boundary.release.set();service.occupied-=main_active
            await service.close()
        assert service.occupied==0
    asyncio.run(run())

def test_five_main_producers_start_before_first_final_and_defer_background(packet):
    service,child=runtime(packet);source(packet);packet[2].release=asyncio.Event()
    async def run():
        try:
            opened=await asyncio.gather(*(service.open({**SCOPE,'user_id':owner,'conversation_id':owner+'-chat'},body(owner)) for owner in ['alice','bob','carol','dave','eve']))
            for _ in range(100):
                if len(packet[2].claims)==5:break
                await asyncio.sleep(.005)
            assert len(packet[2].claims)==5 and service.occupied==5
            rows=await asyncio.gather(*(service.get({**SCOPE,'user_id':owner,'conversation_id':owner+'-chat'},opened[i][0]['operation_id']) for i,owner in enumerate(['alice','bob','carol','dave','eve'])))
            assert all(row['state']=='active' for row in rows)
            child.on_completed(SCOPE,context(),event_id=str(uuid4()))
            await asyncio.sleep(.05);assert packet[3].calls==[] and service.occupied==5
        finally:
            packet[2].release.set();await service.close()
    asyncio.run(run())

def test_native_final_schedules_only_after_commit_and_does_not_wait_for_compression(packet,monkeypatch):
    service,child=runtime(packet);source(packet);packet[3].release=asyncio.Event()
    original=service.repository.complete;entered=threading.Event();release=threading.Event()
    def blocked(*args,**kwargs):
        entered.set();assert release.wait(4)
        return original(*args,**kwargs)
    monkeypatch.setattr(service.repository,'complete',blocked)
    async def run():
        try:
            row,_=await service.open(SCOPE,body())
            for _ in range(100):
                if entered.is_set():break
                await asyncio.sleep(.005)
            assert entered.is_set() and packet[3].calls==[] and derived(packet) is None
            release.set()
            for _ in range(100):
                row=await service.get(SCOPE,row['operation_id'])
                if row['state']=='completed':break
                await asyncio.sleep(.005)
            assert row['state']=='completed'
            await calls_at_least(packet[3],1)
            finals=[json.loads(frame.split('data: ',1)[1]) for frame in service.buffers[row['operation_id']]['events'] if frame.startswith('event: final\n')]
            assert len(finals)==1 and finals[0]['type']=='final' and finals[0]['operation']['state']=='completed'
            assert finals[0]['operation_id']==row['operation_id'] and finals[0]['operation']['operation_id']==row['operation_id']
            assert derived(packet) is None and service.occupied==1
            packet[3].release.set();await idle(child);assert len(packet[3].calls)<=2
        finally:
            release.set();packet[3].release.set();await service.close()
    asyncio.run(run())

def test_reconciled_commit_unknown_final_queues_once_without_provider_redispatch(packet,monkeypatch):
    service,child=runtime(packet);source(packet);original=service.repository.complete
    def lost_ack(*args,**kwargs):
        original(*args,**kwargs)
        raise ChatError(503,'commit_unknown')
    monkeypatch.setattr(service.repository,'complete',lost_ack)
    async def run():
        try:
            row,_=await service.open(SCOPE,body())
            for _ in range(100):
                actual=await service.get(SCOPE,row['operation_id'])
                if actual['state']=='completed':break
                await asyncio.sleep(.005)
            assert actual['state']=='completed'
            await calls_at_least(packet[3],1);await idle(child)
            assert len(packet[2].claims)==1 and 0<len(packet[3].calls)<=2
            for _ in range(3):await service.get(SCOPE,row['operation_id']);child.wake()
            await idle(child);assert len(packet[3].calls)<=2
        finally:await service.close()
    asyncio.run(run())

def test_main_claim_waiting_on_shared_lock_has_priority_over_queued_summary(packet):
    service,child=runtime(packet);source(packet);packet[2].release=asyncio.Event();packet[3].release=asyncio.Event()
    async def run():
        task=None
        try:
            await service.lock.acquire()
            task=asyncio.create_task(service.open({**SCOPE,'user_id':'bob','conversation_id':'bob-chat'},body('bob')))
            await asyncio.sleep(.05)
            child.on_completed(SCOPE,context(),event_id=str(uuid4()))
            await asyncio.sleep(.02);assert packet[3].calls==[] and packet[2].claims==[]
            service.lock.release()
            row,_=await asyncio.wait_for(task,2)
            for _ in range(100):
                if packet[2].claims:break
                await asyncio.sleep(.005)
            assert len(packet[2].claims)==1
            await calls_at_least(packet[3],1)
            assert service.occupied==2 and service.occupied<=service.capacity
        finally:
            if service.lock.locked():service.lock.release()
            packet[2].release.set();packet[3].release.set();await service.close()
            if task is not None:await asyncio.gather(task,return_exceptions=True)
    asyncio.run(run())

def test_invalid_candidate_preserves_frontier_and_same_failed_attempt_never_auto_retries(packet):
    service,child=runtime(packet);source(packet,count=5,long=False);packet[3].mode='invalid';original=digest(document(packet))
    async def run():
        try:
            child.on_completed(SCOPE,context(8192),event_id=str(uuid4()));await idle(child)
            assert len(packet[3].calls)==1 and derived(packet) is None and digest(document(packet))==original
            for _ in range(4):child.wake();child.state(SCOPE)
            await idle(child);assert len(packet[3].calls)==1
        finally:await service.close()
    asyncio.run(run())

def test_uncertain_ack_keeps_shared_reservation_until_own_cancel_confirms_and_never_redispatches(packet):
    service,child=runtime(packet);source(packet,count=5,long=False);packet[3].mode='uncertain'
    async def run():
        try:
            child.on_completed(SCOPE,context(8192),event_id=str(uuid4()));await calls_at_least(packet[3],1)
            await asyncio.sleep(.05)
            assert service.occupied==1 and derived(packet) is None and len(packet[3].calls)==1
            child.wake();await asyncio.sleep(.05)
            assert service.occupied==1 and len(packet[3].calls)==1
            packet[3].confirmed=True;await child.recover();await idle(child)
            assert service.occupied==0 and derived(packet) is None and len(packet[3].calls)==1
        finally:
            packet[3].confirmed=True;await service.close()
    asyncio.run(run())

def test_lost_ack_completed_status_installs_once_without_new_provider_post(packet):
    service,child=runtime(packet);source(packet,count=5,long=False);packet[3].mode='lost_ack_completed'
    async def run():
        try:
            child.on_completed(SCOPE,context(8192),event_id=str(uuid4()));await idle(child)
            assert len(packet[3].calls)==1 and len(derived(packet)['artifact']['source_refs'])==1
            assert service.occupied==0 and packet[3].controls
        finally:await service.close()
    asyncio.run(run())

def test_shutdown_waits_for_owned_sql_query_and_prevents_dispatch_after_close(packet,monkeypatch):
    from app.db.chat_summary_repository import SummaryRepository
    service,child=runtime(packet);source(packet);principal=service.repository.summaries;original=SummaryRepository.snapshot
    entered=threading.Event();release=threading.Event();observed=[]
    def blocked(self,*args,**kwargs):
        if self is principal or args[0]!=SCOPE:return original(self,*args,**kwargs)
        assert self.repository is not service.repository and self.repository.engine is not service.repository.engine
        observed.append(self);entered.set();assert release.wait(4)
        return original(self,*args,**kwargs)
    monkeypatch.setattr(SummaryRepository,'snapshot',blocked)
    from test_chat_summary_lifecycle_jup035 import contract53
    principal.snapshot(SCOPE,contract53(packet[4]),packet[4])
    assert not entered.is_set() and principal.repository is service.repository
    async def run():
        close=None
        try:
            child.on_completed(SCOPE,context(),event_id=str(uuid4()))
            for _ in range(100):
                if entered.is_set():break
                await asyncio.sleep(.005)
            assert entered.is_set() and len(observed)==1 and observed[0] is not principal
            assert service.repository.summaries is principal and principal.repository is service.repository
            close=asyncio.create_task(service.close());await asyncio.sleep(.05)
            assert not close.done() and packet[3].calls==[] and service.occupied==1
            release.set();await asyncio.wait_for(close,2)
            assert service.occupied==0 and packet[3].calls==[]
        finally:
            release.set()
            if close is not None:await asyncio.gather(close,return_exceptions=True)
            else:await service.close()
    asyncio.run(run())
