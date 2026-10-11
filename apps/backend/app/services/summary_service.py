"""Cold, bounded, scoped RAM queue for derived QA memory after committed finals.

The main-operation lock owns the shared reservation. SQL and token work retain
their actual workers until completion; uncertainty never releases admission.
"""
import asyncio,os,time
from dataclasses import dataclass
from uuid import uuid4
from app.db.chat_repository import ChatError,ChatRepository
from app.services.summary_sql import SummarySQL
from types import SimpleNamespace
from app.db.chat_summary_repository import ledger,digest
from app.db.chat_history import dumps

ADMISSION_POLICY='jup-035.summary-one-reserve-five.v2'

@dataclass
class Record:
    scope:dict
    pressure:int=0
    pending:bool=True
    reason:str='queued'
    pairs:int|None=None
    tokens:int=0
    parent:str|None=None
    last_event:str|None=None
    last_attempt:str|None=None
    active:bool=False
    control:dict|None=None
    uncertain:bool=False

class SummaryService:
    def __init__(self,main):
        self.main=main;self.resources=getattr(main.app.state,'summary_resources',None)
        self.transport=getattr(main.transport,'summary',None)
        self.enabled=os.getenv('SUMMARY_ENABLED','false')=='true' and self.resources is not None and self.transport is not None
        self.records={};self.task=None;self.closing=False;self.reserved=False;self.workers=set();self.sql_owners=set()
        self.owner=str(uuid4());self.reserved_scope=None

    @property
    def state_count(self):return len(self.records)

    def state(self,scope):
        return self.main.repository.compactions.public(scope)

    async def recover(self):
        if not self.enabled or self.closing:return
        # SQL discovery excludes failed/cleared controls, but a live worker may
        # still hold the reservation for a job settled by another worker.
        for record in self.records.values():
            if record.uncertain and not record.active:record.pending=True
        for scope in await self.worker(self.main.repository.compactions.recoverable):
            key=tuple(scope[k] for k in ('tenant_id','user_id','conversation_id'))
            if key not in self.records and len(self.records)>=32:continue
            record=self.records.setdefault(key,Record(dict(scope)))
            if not record.active:record.pending=True
        self.wake()

    async def retry(self,scope):
        if not self.enabled:raise ChatError(503,'summary_not_ready')
        await self.worker(self.main.repository.compactions.retry,scope)
        await self.recover()

    def on_completed(self,scope,context,event_id):
        if not self.enabled or self.closing:return False
        key=tuple(scope[k] for k in ('tenant_id','user_id','conversation_id'))
        record=self.records.get(key)
        if record is None:
            if len(self.records)>=32:return False
            record=Record(dict(scope));self.records[key]=record
        if record.last_event==event_id:return True
        record.last_event=event_id
        manifest=context.get('manifest',{}) if isinstance(context,dict) else {}
        pressure=manifest.get('variable_tokens',0)
        record.pressure=pressure if type(pressure) is int and pressure>=0 else 0
        record.pending=True
        self.wake()
        return True

    def wake(self):
        if self.closing or not self.enabled:return
        if self.task is None or self.task.done():
            if any(r.pending for r in self.records.values()):self.task=asyncio.create_task(self._pump())

    async def wait_idle(self):
        while self.task is not None and not self.task.done():await asyncio.shield(self.task)

    async def worker(self,function,*args,**kwargs):
        task=asyncio.create_task(asyncio.to_thread(function,*args,**kwargs));self.workers.add(task)
        try:return await asyncio.shield(task)
        finally:
            if task.done():self.workers.discard(task)

    def begin_close(self):
        self.closing=True
        for owner in list(self.sql_owners):owner.cancel()

    async def close(self):
        self.begin_close()
        # The queue task is cooperative: it cannot abandon an owned SQL read.
        if self.task is not None:await asyncio.gather(self.task,return_exceptions=True)
        if self.workers:await asyncio.gather(*self.workers,return_exceptions=True)
        for owner in list(self.sql_owners):
            await self.worker(owner.close)
            self.sql_owners.discard(owner)
        if self.transport is not None:await self.transport.close()

    async def _reserve(self,record):
        async with self.main.lock:
            if self.reserved and self.reserved_scope==record.scope:return True
            if (self.closing or self.reserved or getattr(self.main,'main_waiters',0)
                or self.main.capacity-self.main.occupied-1<5):return False
            self.main.occupied+=1;self.reserved=True;self.reserved_scope=dict(record.scope)
            return True

    async def _release(self):
        async with self.main.lock:
            if self.reserved:self.main.occupied-=1;self.reserved=False;self.reserved_scope=None

    async def _pump(self):
        await asyncio.sleep(0)
        for record in list(self.records.values()):
            if self.closing:break
            if not record.pending:continue
            if not await self._reserve(record):
                record.reason='capacity_deferred';continue
            record.pending=False;record.active=True
            try:await self._event(record)
            except (ChatError,ValueError,KeyError,TypeError):record.reason='failed'
            except Exception:record.reason='failed'
            finally:
                record.active=False
                # Failed physical cleanup retains the reservation and owner.
                if not self.sql_owners and not record.uncertain:await self._release()
                if not record.uncertain and not record.pending:
                    self.records.pop(tuple(record.scope[k] for k in ('tenant_id','user_id','conversation_id')),None)
        # No self-waking loop: only a committed event or main release wakes RAM.

    async def _event(self,record):
        controls=self.main.repository.compactions
        if record.uncertain and record.control is not None:
            current=await self.worker(controls.get,record.scope)
            # A job is removed/replaced only after confirmed settlement. An
            # expired lease with the same job is not evidence of settlement.
            settled=(current is None or current['generation']!=record.control['generation']
                or (current['revision']>record.control['revision']
                    and current.get('job')!=record.control.get('job')))
            if settled:
                record.uncertain=False
                record.control=None
                return
        claimed=await self.worker(controls.claim,record.scope,self.owner)
        if claimed is None:return
        record.control=claimed
        record.uncertain=record.control.get('job') is not None
        if record.uncertain:
            response=await self._reconcile({**record.control['job'],'scope':record.scope})
            if response is None:
                await self._transition(record,state='reconciling',reason='remote_uncertain',
                    owner=None,lease_until=None)
                return
            # Recovery never repeats POST. A settled result without the original
            # validated snapshot needs an explicit retry, preserving valid memory.
            record.uncertain=False
            await self._transition(record,state='failed',reason='failed',job=None,owner=None,lease_until=None)
            return
        deadline=time.time()+30
        owner=SummarySQL(self.main.repository.engine,deadline);self.sql_owners.add(owner)
        repository=ChatRepository(SimpleNamespace(engine=owner),self.main.clock)
        try:
            return await self._owned_event(record,deadline,repository)
        except Exception:
            await self._transition(record,state='reconciling' if record.uncertain else 'failed',
                reason='remote_uncertain' if record.uncertain else 'failed',owner=None,lease_until=None,
                job=record.control.get('job') if record.uncertain else None)
            raise
        finally:
            await self.worker(owner.close)
            self.sql_owners.discard(owner)

    async def _transition(self,record,**changes):
        record.control=await self.worker(self.main.repository.compactions.transition,
            record.scope,record.control,**changes)

    async def _defer(self,record,reason):
        record.reason=reason
        await self._transition(record,state='pending',reason=reason,owner=None,lease_until=None)

    async def _clear(self,record,reason):
        record.reason=reason
        await self._transition(record,clear=True)

    async def _owned_event(self,record,deadline,local):
        resources=self.resources
        if await self.worker(self._main_due,local):
            await self._defer(record,'capacity_deferred');return
        descriptor=await self.transport.descriptor()
        resources.verify_descriptor(descriptor)
        if (descriptor.get('capacity')!=self.main.capacity or descriptor.get('admission_policy')!=ADMISSION_POLICY
            or descriptor.get('summary_ready') is not True or not isinstance(descriptor.get('boot_id'),str)):
            await self._transition(record,state='failed',reason='descriptor_mismatch',owner=None,lease_until=None);return
        contract=resources.contract
        repository=local.summaries
        snapshot=await self.worker(repository.snapshot,record.scope,contract,resources)
        refs,qa,_=await self.worker(ledger,snapshot.document)
        tokens=await self.worker(resources.count,dumps(qa))
        from app.core.context_budget import budget
        chat_budget=budget('chat')
        remaining=qa[snapshot.covered_pairs:]
        eligible_tokens=await self.worker(resources.count,dumps(remaining))
        pressure=(record.control.get('full_context_pressure') is True
            or record.control.get('reason')=='retry_requested'
            or record.pressure>=chat_budget['context_tokens']*.75
            or eligible_tokens>=chat_budget['context_tokens']*.75
            or len(dumps(remaining).encode())>=chat_budget['body_limit_bytes']*.75)
        if not pressure:
            await self._clear(record,'trigger_deferred');return
        record.pairs=len(qa);record.tokens=tokens
        for _ in range(2):
            if self.closing or time.time()>=deadline:
                await self._defer(record,'queued');return
            refs,qa,_=await self.worker(ledger,snapshot.document)
            job_id=str(uuid4())
            def envelope_for(payload,selected):
                return {'v':2,'job_id':job_id,'scope':dict(record.scope),'boot_id':descriptor['boot_id'],
                    'summary_version':resources.summary_version,'schema_sha256':resources.response_schema_sha256,
                    'tokenizer_sha256':resources.tokenizer_sha256,'parent_hash':snapshot.parent_hash,'lineage_epoch':snapshot.epoch,
                    'source_refs':refs[snapshot.covered_pairs:snapshot.covered_pairs+selected],
                    'selected_pairs':selected,'deadline':deadline,'input_hash':digest(payload),'payload':payload}
            lot=await self.worker(resources.prepare_lot,snapshot.previous_payload_used,qa[snapshot.covered_pairs:],envelope_for)
            record.reason=lot['reason'] or 'ready'
            if lot['payload'] is None:
                if lot['reason']=='recent_pairs_only':await self._clear(record,lot['reason'])
                else:await self._transition(record,state='failed',reason='pending_pair_too_large',owner=None,lease_until=None)
                return
            attempt=digest({'scope':record.scope,'parent':snapshot.parent_hash,'contract':contract,'refs':refs[snapshot.covered_pairs:snapshot.covered_pairs+lot['selected_pairs']],'input':lot['input_hash']})
            if attempt==record.last_attempt:
                await self._transition(record,state='failed',reason='failed',owner=None,lease_until=None);return
            record.last_attempt=attempt
            envelope=envelope_for(lot['payload'],lot['selected_pairs'])
            if self.closing or time.time()>=deadline:
                await self._defer(record,'queued');return
            job={key:envelope[key] for key in ('job_id','boot_id','input_hash','summary_version')}
            await self._transition(record,state='running',reason='running',job=job)
            record.uncertain=True
            record.reason='running'
            try:response=await self.transport.submit(envelope)
            except ChatError as error:
                if error.code!='summary_outcome_unknown':raise
                response=await self._reconcile(envelope)
            if response is not None and response.get('settled') is not True:
                response=await self._reconcile(envelope)
            if response is None:
                await self._transition(record,state='reconciling',reason='remote_uncertain',owner=None,lease_until=None)
                return
            record.uncertain=False
            if response.get('state')!='completed':
                await self._transition(record,state='failed',reason='failed',job=None,owner=None,lease_until=None);return
            sources={pair[role+'_ref']:pair[role] for pair in qa[:snapshot.covered_pairs+lot['selected_pairs']] for role in ('question','answer')}
            output=await self.worker(self.transport.validate_output,response['output'],sources,resources)
            if self.closing or time.time()>=deadline:
                await self._transition(record,state='failed',reason='failed',job=None,owner=None,lease_until=None);return
            candidate=await self.worker(repository.candidate,snapshot,output,response['receipt'],lot['selected_pairs'])
            await self.worker(repository.install,record.scope,snapshot,candidate,record.control)
            record.control=await self.worker(self.main.repository.compactions.claim,record.scope,self.owner)
            if record.control is None:return
            record.reason='completed'
            snapshot=await self.worker(repository.snapshot,record.scope,contract,resources)
            record.parent=snapshot.parent_hash
            if lot['pending_pairs']==0:
                await self._clear(record,'completed');return
        await self._defer(record,'queued')

    async def _reconcile(self,envelope):
        for action in (self.transport.status,self.transport.cancel):
            try:response=await action(envelope)
            except ChatError:continue
            if response.get('settled') is True:return response
        # A signed404 or elapsed lease is not settlement. Persist uncertainty;
        # subsequent scheduler ticks reconcile this job without another POST.
        return None

    def _main_due(self,repository=None):
        repository=repository or self.main.repository
        # Main/retry rows are read without modifying them. The main scheduler
        # performs all transitions and wakes deferred RAM on reservation release.
        for ref in repository.recoverable():
            scope={k:ref[k] for k in ('tenant_id','user_id','conversation_id')}
            row=repository.get(scope,ref['operation_id'])
            if row['state']=='waiting' and (row['retry_at'] is None or row['retry_at']<=self.main.clock()):return True
        return False
