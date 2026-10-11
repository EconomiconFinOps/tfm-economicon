"""Single-process supervised producer; observers never own its lifecycle."""
import asyncio
import json
import time
from email.utils import parsedate_to_datetime
from uuid import uuid4

from app.db.chat_repository import ChatError, ChatRepository, TERMINAL
from app.schemas.chat import canonical, validate_response, reported_usage, response_citations


class ChatOperations:
    def __init__(self,app,active=False):
        self.app=app
        self.clock=getattr(app.state,'chat_clock',time.time)
        self.repository=ChatRepository(app.state.database,self.clock)
        self.transport=getattr(app.state,'chat_transport',None)
        if self.transport is None:
            from app.services.chat_transport import configured_transport
            self.transport=configured_transport()
        self.context_builder=getattr(app.state,'chat_context_builder',None)
        self.capacity=getattr(app.state,'chat_max_active',8)
        if type(self.capacity) is not int or (not 5<=self.capacity<=8 and getattr(app.state,'chat_clock',None) is None):
            raise ChatError(503,'capacity_invalid')
        self.interval=getattr(app.state,'chat_scheduler_interval',5)
        self.occupied=0
        self.lock=asyncio.Lock()
        self.tasks={}
        self.buffers={}
        self.scheduler=None
        self.main_waiters=0
        from app.services.summary_service import SummaryService
        self.summary=SummaryService(self)
        if active:
            self.start()

    def start(self):
        if self.scheduler is None and self.transport is not None and self.context_builder is not None:
            self.scheduler=asyncio.create_task(self._schedule())

    async def close(self):
        self.summary.begin_close()
        tasks=[task for task in [self.scheduler,*self.tasks.values()] if task is not None]
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        await self.summary.close()

    async def _db(self,method,*args,**kwargs):
        return await asyncio.to_thread(method,*args,**kwargs)

    def public(self,row,outcome=None):
        base=f"/assistant/conversations/{row['conversation_id']}/generations/{row['operation_id']}"
        wait=row['private_control']['wait']
        used={key:wait[key] for key in ['local_used_ms','provider_used_ms']}
        if row['state']=='waiting' and wait['reason']:
            key='local_used_ms' if wait['reason']=='local_capacity' else 'provider_used_ms'
            elapsed=max(0,min(self.clock(),wait['until'])-wait['started'])*1000
            used[key]=min(120000,used[key]+round(elapsed))
        def date(value):
            from datetime import datetime,timezone
            return datetime.fromtimestamp(value,timezone.utc).isoformat() if value is not None else None
        value={'v':2,'operation_id':row['operation_id'],'question_id':row['question_message_id'],
            'request_id':row['client_request_id'],'state':row['state'],'attempt_count':row['attempt_count'],
            'current_attempt_id':row['current_attempt_id'],'attempt_deadline':date(row['attempt_deadline']),
            'retry_at':date(row['retry_at']),'prompt_version':row['canonical_input']['context']['prompt_version'],
            'status_url':base,'events_url':base+'/events','result_url':base+'/result' if row['state']=='completed' else None,
            'wait_info':{'reason':wait['reason'],'local_remaining_ms':120000-used['local_used_ms'],
                'provider_remaining_ms':120000-used['provider_used_ms'],
                'automatic_until':date(wait['until']) if row['state']=='waiting' and wait['reason'] else None,
                'retry_at':date(row['retry_at']),'pause_reason':row['private_control']['pause_reason']}}
        if outcome: value['outcome']=outcome
        return value

    async def get(self,scope,identifier):
        return await self._db(self.repository.get,scope,identifier)

    async def requests(self,scope):
        rows=await self._db(self.repository.owned_requests,scope)
        return {'items':[{'tenant_id':row['tenant_id'],'user_id':row['user_id'],
            'conversation_id':row['conversation_id'],'question':row['question_content'],
            'operation':self.public(row)} for row in rows]}

    async def open(self,scope,payload):
        prior=await self._db(self.repository.existing,scope,payload['request_id'])
        if prior:
            if canonical(prior['canonical_input']['request'])!=canonical(payload):
                raise ChatError(409,'intent_conflict')
            return prior,False
        if self.transport is None or self.context_builder is None:
            raise ChatError(503,'chat_not_ready')
        await self._db(self.repository.compactions.ensure_idle,scope)
        descriptor=await asyncio.wait_for(self.transport.descriptor(),10)
        for retry in range(2):
            fence=await self._db(self.repository.compactions.fence,scope)
            context=await asyncio.wait_for(self.context_builder(scope,payload,descriptor),30)
            context['memory_fence']=fence
            try:
                row,created=await self._db(self.repository.reserve,scope,payload,context)
                break
            except ChatError as error:
                if error.code!='context_stale' or retry:raise
        if created:
            self.buffers[row['operation_id']]={'events':[],'subscribers':set(),'partial':''}
            self.buffers[row['operation_id']]['initial_frame']=self._frame(row,'started',operation=self.public(row))
            await self._try_claim(scope,row,descriptor)
        return await self.get(scope,row['operation_id']),created

    def _frame(self,row,event,**values):
        wire={'v':2,'type':event,'operation_id':row['operation_id'],'revision':row['revision'],**values}
        identifier=(f"{row['operation_id']}:{values['attempt_id']}:{values.get('seq',0)}"
                    if event in ('attempt_started','delta','snapshot') and values.get('attempt_id')
                    else f"{row['operation_id']}:operation:{row['revision']}")
        frame=f"event: {event}\nid: {identifier}\ndata: {canonical(wire)}\n\n"
        if len(frame.encode())>65536:
            raise ChatError(502,'frame_limit')
        return frame

    def _emit(self,row,event,**values):
        buffer=self.buffers.setdefault(row['operation_id'],{'events':[],'subscribers':set(),'partial':''})
        frame=self._frame(row,event,**values)
        if event in ('attempt_started','delta'):
            buffer['cursor']={'attempt_id':values['attempt_id'],'number':row['attempt_count'],
                'revision':row['revision'],'seq':values.get('seq',0)}
        buffer['events'].append(frame)
        buffer['total_events']=buffer.get('total_events',0)+1
        buffer['events']=buffer['events'][-64:]
        for queue in list(buffer['subscribers']):
            if queue.full():
                buffer['subscribers'].discard(queue)
                while not queue.empty(): queue.get_nowait()
                queue.put_nowait(None)
            else: queue.put_nowait(frame)

    async def _final_values(self,scope,row):
        result=await self._db(self.repository.result,scope,row)
        base=f"/assistant/conversations/{row['conversation_id']}/generations/{row['operation_id']}"
        generation=result['metadata'].get('generation',{})
        return {'operation':self.public(row),'answer':result['content'],'answer_id':result['id'],
            'result_url':base+'/result','context_url':base+'/context','evidence_url':base+'/evidence',
            'usage':reported_usage(generation.get('usage')) if isinstance(generation,dict) else None}

    async def _emit_completed(self,scope,row):
        self._emit(row,'final',**await self._final_values(scope,row))
        self.summary.on_completed(scope,row['canonical_input']['context'],event_id=row['result_message_id'])

    async def _try_claim(self,scope,row,descriptor=None,explicit=False):
        self.main_waiters+=1
        try:return await self._claim_with_priority(scope,row,descriptor,explicit)
        finally:
            self.main_waiters-=1
            self.summary.wake()

    async def _claim_with_priority(self,scope,row,descriptor=None,explicit=False):
        if self.transport is None:
            return False
        async with self.lock:
            if self.occupied>=self.capacity or row['operation_id'] in self.tasks:
                return False
            self.occupied+=1
            try:
                descriptor=descriptor or await asyncio.wait_for(self.transport.descriptor(),10)
                if descriptor['prompt_version']!=row['canonical_input']['context']['prompt_version']:
                    raise ChatError(503,'prompt_changed')
                claimed,won=await self._db(self.repository.claim,scope,row['operation_id'],descriptor['boot_id'],explicit)
                if not won:
                    self.occupied-=1
                    return False
                self.buffers.setdefault(claimed['operation_id'],{'events':[],'subscribers':set(),'partial':''})['partial']=''
                self._emit(claimed,'attempt_started',attempt_id=claimed['current_attempt_id'],number=claimed['attempt_count'],
                           seq=0,deadline=self.public(claimed)['attempt_deadline'])
                self.tasks[claimed['operation_id']]=asyncio.create_task(self._produce(scope,claimed))
                return True
            except BaseException:
                self.occupied-=1
                raise

    def _delay(self,value,attempt):
        fallback=min(4,2**(attempt-1))
        if type(value) in (int,float) and value>=0:
            return float(value)
        if isinstance(value,str):
            if value.isdigit(): return float(value)
            try:
                date=parsedate_to_datetime(value)
                if date.tzinfo is not None: return max(0,date.timestamp()-self.clock())
            except (ValueError,TypeError,OverflowError):
                pass
        return fallback

    async def _error(self,scope,row,transient,delay=0,reason='provider_error'):
        result=await self._db(self.repository.close_attempt,scope,row['operation_id'],row['current_attempt_id'],
            transient=transient,delay=delay,reason=reason,partial=self.buffers.get(row['operation_id'],{}).get('partial',''))
        if result['state']=='waiting': self._emit(result,'retry_scheduled',operation=self.public(result))
        elif result['state']=='paused': self._emit(result,'paused',operation=self.public(result))
        elif result['state']=='failed': self._emit(result,'terminal',operation=self.public(result))

    async def _produce(self,scope,row):
        claim={'v':2,**scope,'operation_id':row['operation_id'],'attempt_id':row['current_attempt_id'],
            'number':row['attempt_count'],'deadline':row['attempt_deadline'],
            'boot_id':row['private_control']['boot_id'],'capability':row['private_control']['capability'],
            'input_hash':row['input_hash'],'context':row['canonical_input']['context']}
        try:
            async def consume():
                seq,offset=0,0
                async for record in self.transport.stream(claim):
                    current=await self.get(scope,row['operation_id'])
                    if current['state']!='active' or current['current_attempt_id']!=row['current_attempt_id']:
                        return
                    if self.clock()>=row['attempt_deadline']-5:
                        raise TimeoutError()
                    if record.get('type')=='delta':
                        value=record.get('text')
                        if not isinstance(value,str) or len(value.encode())>8192:
                            raise ValueError('Invalid delta.')
                        buffer=self.buffers[row['operation_id']]
                        if len(buffer['partial']+value)>4000:
                            raise ValueError('Invalid answer size.')
                        buffer['partial']+=value
                        seq+=1
                        self._emit(current,'delta',attempt_id=row['current_attempt_id'],seq=seq,offset=offset,text=value)
                        offset+=len(value.encode('utf-16-le'))//2
                    elif record.get('type')=='error':
                        transient=record.get('status') in [429,502,503,504] or record.get('category') in ['timeout','transport','eof']
                        await self._error(scope,row,transient,self._delay(record.get('retry_after'),row['attempt_count']) if transient else 0)
                        return
                    elif record.get('type')=='candidate':
                        if record.get('finish_reason')=='length':
                            await self._error(scope,row,True,self._delay(None,row['attempt_count']),'incomplete')
                            return
                        if record.get('finish_reason')!='stop':
                            raise ValueError('Invalid finish reason.')
                        candidate=validate_response(record.get('result'),claim['context'].get('authorized_evidence',[]),
                            expected_period=claim['context'].get('response_period'))
                        result_id=str(uuid4())
                        references,citations=response_citations(candidate,claim['context'])
                        metadata={'response':candidate,'citations':references,'source_citations':citations,
                            'generation':{'v':2,'operation_id':row['operation_id'],'attempt_id':row['current_attempt_id'],
                                'question_message_id':row['question_message_id'],'prompt_version':claim['context']['prompt_version'],
                                'state':'completed','input_hash':row['input_hash'],
                                'context_manifest':claim['context'].get('manifest',{}),'usage':reported_usage(record.get('usage'))}}
                        final_limit=time.monotonic()+5
                        while True:
                            try:
                                final=await self._db(self.repository.complete,scope,row['operation_id'],row['current_attempt_id'],candidate,metadata,result_id)
                                await self._emit_completed(scope,final)
                                return
                            except ChatError as error:
                                if error.code=='commit_unknown':
                                    known=await self.get(scope,row['operation_id'])
                                    if known['state']=='completed':
                                        await self._emit_completed(scope,known)
                                        return
                                if error.status!=503 or time.monotonic()>=final_limit or self.clock()>=row['attempt_deadline']:
                                    # SQL failure never buys another model call.
                                    await self._error(scope,row,False,reason='persistence_error')
                                    return
                                await asyncio.sleep(.05)
                    else:
                        raise ValueError('Invalid stream record.')
                await self._error(scope,row,True,self._delay(None,row['attempt_count']),'eof')
            await asyncio.wait_for(consume(),max(.001,row['attempt_deadline']-self.clock()-5))
        except asyncio.CancelledError:
            # Scheduler/Stop owns the durable transition; reader never cancels us.
            raise
        except (TimeoutError,OSError):
            await self._error(scope,row,True,self._delay(None,row['attempt_count']),'timeout')
        except ChatError:
            # A storage uncertainty must remain fenced for recovery, not become
            # an unverified failed state or a new upstream dispatch.
            pass
        except Exception:
            await self._error(scope,row,False,reason='invalid_response')
        finally:
            async with self.lock:
                self.occupied-=1
                self.tasks.pop(row['operation_id'],None)
            self.summary.wake()

    async def _schedule(self):
        while True:
            await asyncio.sleep(self.interval)
            try:
                await self.summary.recover()
                records=await self._db(self.repository.recoverable)
                for record in records:
                    scope={key:record[key] for key in ['tenant_id','user_id','conversation_id']}
                    row=await self.get(scope,record['operation_id'])
                    if row['state']=='active':
                        if row['attempt_deadline'] is None: continue
                        if self.clock()>=row['attempt_deadline']:
                            await self._error(scope,row,True,self._delay(None,row['attempt_count']),'timeout')
                            task=self.tasks.get(row['operation_id'])
                            if task: task.cancel()
                        continue
                    row=await self._db(self.repository.reconcile,scope,row['operation_id'])
                    if row['state']=='paused':
                        self._emit(row,'paused',operation=self.public(row))
                    elif row['state']=='waiting' and row['private_control']['wait']['reason']=='local_capacity':
                        await self._try_claim(scope,row)
            except ChatError:
                # No database truth, no new claims. Existing producers recheck.
                continue

    async def stop(self,scope,identifier):
        row=await self.get(scope,identifier)
        stopped=await self._db(self.repository.stop,scope,identifier)
        if stopped['state']=='cancelled':
            self._emit(stopped,'terminal',operation=self.public(stopped))
            task=self.tasks.get(identifier)
            if task: task.cancel()
            if self.transport and row['current_attempt_id']:
                # Stop result is already committed; failure to abort upstream
                # never rescinds it or announces a guarantee of stopped billing.
                try:
                    await asyncio.wait_for(self.transport.cancel({'operation_id':identifier,
                        'attempt_id':row['current_attempt_id'],**scope,'boot_id':row['private_control'].get('boot_id'),
                        'capability':row['private_control'].get('capability'),'input_hash':row['input_hash'],
                        'number':row['attempt_count']}),2)
                except Exception:
                    pass
        return stopped

    async def resume(self,scope,identifier):
        row=await self.get(scope,identifier)
        if row['state']!='paused': raise ChatError(409,'not_paused')
        if row['retry_at'] is not None and self.clock()<row['retry_at']: raise ChatError(409,'provider_not_ready')
        if not await self._try_claim(scope,row,explicit=True):
            row=await self._db(self.repository.pause_or_resume_wait,scope,identifier)
        return await self.get(scope,identifier)

    async def events(self,scope,identifier,initial=False):
        row=await self.get(scope,identifier)
        value=self.public(row)
        started=self._frame(row,'started',operation=value)
        buffer=self.buffers.get(identifier)
        # Only the winning POST can receive its still-complete original RAM
        # delivery. A later observer receives a current snapshot, not this tail.
        original_delivery=bool(initial and buffer and buffer.get('initial_frame')
                               and buffer.get('total_events',0)<=64)
        if row['state'] in TERMINAL and not original_delivery:
            yield started
            if row['state']=='completed': yield self._frame(row,'final',**await self._final_values(scope,row))
            else: yield self._frame(row,'terminal',operation=value)
            return
        if buffer is None:
            yield started
            yield self._frame(row,'recovering',operation=value)
            return
        if row['state'] in ('paused','waiting') and not original_delivery:
            yield started
            yield self._frame(row,row['state'],operation=value)
            return
        queue=asyncio.Queue(maxsize=64)
        replay=list(buffer['events']) if original_delivery else None
        if original_delivery:
            started=buffer['initial_frame']
        # Capture the current attempt and attach atomically in this event loop.
        # A bounded event tail is not a complete replay after more than64deltas.
        cursor=buffer.get('cursor')
        snapshot=None
        if cursor and cursor['attempt_id']==row['current_attempt_id']:
            snapshot=self._frame({**row,'revision':cursor['revision']},'snapshot',
                attempt_id=cursor['attempt_id'],number=cursor['number'],seq=cursor['seq'],
                offset=len(buffer['partial'].encode('utf-16-le'))//2,text=buffer['partial'])
        buffer['subscribers'].add(queue)
        try:
            yield started
            if replay is not None:
                for frame in replay:
                    yield frame
                if row['state'] in TERMINAL or row['state'] in ('paused','waiting'):
                    return
            elif snapshot is not None:
                yield snapshot
            while True:
                try:
                    frame=await asyncio.wait_for(queue.get(),10)
                except TimeoutError:
                    yield ': heartbeat\n\n'
                    continue
                if frame is None: return
                yield frame
                if any(frame.startswith(f'event: {end}\n') for end in ['final','terminal','paused','retry_scheduled']):
                    return
        finally:
            buffer['subscribers'].discard(queue)


def service(app,active=False):
    current=getattr(app.state,'chat_service',None)
    if current is None:
        current=app.state.chat_service=ChatOperations(app,active=active)
    elif active:
        current.start()
    return current
