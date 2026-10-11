"""Authenticated RAM-only summary jobs; read-only source reauthorization."""
import asyncio
from dataclasses import dataclass,field
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
import re
import time
from uuid import UUID,uuid4
from fastapi import Request
from sqlalchemy import text
from app.clients.chat_stream_parser import complete_json
from app.clients.summary_gateway import SummaryGatewayError,configured_gateway
from app.core.summary_resources import validate_output
from app.core.summary_sql import SummarySQL,SummarySQLDeadline

ROOT='/internal/chat/v2/summaries'
SCOPE_KEYS={'tenant_id','user_id','conversation_id'}
ENVELOPE={'v','job_id','scope','boot_id','summary_version','schema_sha256','tokenizer_sha256','parent_hash',
    'lineage_epoch','source_refs','selected_pairs','deadline','input_hash','payload'}
REF_KEYS={'question_id','answer_id','question_ordinal','answer_ordinal','question_sha256','answer_sha256'}
MESSAGE_KEYS={'ordinal','id','role','author_id','question_id','origin','content','metadata','created_at'}

def canonical(value):
    # Exactly match the canonical JSONB number representation, without importing
    # backend or rounding historical metadata through a binary float.
    if isinstance(value,Decimal) or type(value) is int:
        number=Decimal(value)
        if not number.is_finite():raise ValueError('Non-finite source.')
        sign,digits,exponent=number.as_tuple();digits=list(digits)
        while len(digits)>1 and digits[-1]==0:digits.pop();exponent+=1
        if not any(digits):return '0'
        prefix='-' if sign else '';coefficient=''.join(str(d) for d in digits)
        if -64<=exponent<=64:
            point=len(coefficient)+exponent
            if exponent>=0:return prefix+coefficient+'0'*exponent
            if point>0:return prefix+coefficient[:point]+'.'+coefficient[point:]
            return prefix+'0.'+'0'*(-point)+coefficient
        return prefix+coefficient+'e'+str(exponent)
    if isinstance(value,list):return '['+','.join(canonical(x) for x in value)+']'
    if isinstance(value,dict) and all(isinstance(k,str) for k in value):
        return '{'+','.join(json.dumps(k,ensure_ascii=False)+':'+canonical(value[k]) for k in sorted(value))+'}'
    return json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)

def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def unique(items):
    result={}
    for k,v in items:
        if k in result:raise ValueError('Duplicate source key.')
        result[k]=v
    return result
def source_json(raw):
    def reject(value):raise ValueError('Non-finite source number.')
    return json.loads(raw,parse_float=Decimal,parse_constant=reject,object_pairs_hook=unique)
def identifier(value):return isinstance(value,str) and bool(value)
def uuid(value):
    try:return isinstance(value,str) and str(UUID(value))==value
    except ValueError:return False
def hash_value(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
def opaque(scope,role,identifier):return ('q-' if role=='user' else 'a-')+digest({'scope':scope,'role':role,'id':identifier})

class Rejected(Exception):
    def __init__(self,status,code):
        self.status,self.code=status,code
        super().__init__(code)

def ledger(document,scope):
    if (not isinstance(document,dict) or set(document) not in ({'schema_version','identity','revision','next_ordinal','messages'},
        {'schema_version','identity','revision','next_ordinal','messages','migration'})
        or type(document.get('schema_version')) is not int or document['schema_version']!=1 or document['identity']!=scope
        or any(type(document[k]) is not int or document[k]<0 for k in ('revision','next_ordinal'))
        or not isinstance(document['messages'],list) or len(document['messages'])!=document['next_ordinal']):
        raise Rejected(409,'summary_sources_invalid')
    by_id={};questions={};latest={}
    for ordinal,message in enumerate(document['messages']):
        if (not isinstance(message,dict) or set(message)!=MESSAGE_KEYS or type(message['ordinal']) is not int
            or message['ordinal']!=ordinal or not identifier(message['id']) or message['id'] in by_id
            or not isinstance(message['content'],str) or not identifier(message['role']) or message['origin'] not in ('legacy','completed')
            or message['author_id'] not in (None,scope['user_id'])):
            raise Rejected(409,'summary_sources_invalid')
        if message['role']=='user':
            if message['question_id']!=message['id']:raise Rejected(409,'summary_sources_invalid')
            questions[message['id']]=message
        elif message['role']=='assistant' and message['question_id'] in questions:
            latest[message['question_id']]=message
        if message['origin']=='completed' and (message['role'] not in ('user','assistant') or message['author_id']!=scope['user_id']
            or not isinstance(message['metadata'],dict) or message['question_id'] is None):
            raise Rejected(409,'summary_sources_invalid')
        if message['origin']=='completed' and message['role']=='assistant' and message['question_id'] not in questions:
            raise Rejected(409,'summary_sources_invalid')
        stamp=message['created_at']
        try:
            parsed=datetime.fromisoformat(stamp.replace('Z','+00:00'))
            if parsed.tzinfo is None or parsed.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')!=stamp:raise ValueError()
        except (ValueError,AttributeError,TypeError):raise Rejected(409,'summary_sources_invalid') from None
        canonical(message['metadata'])
        by_id[message['id']]=message
    # Known linked legacy assistants may precede their question in a migrated
    # array. Match only canonical links, never infer from adjacency or metadata.
    for message in document['messages']:
        if message['role']=='assistant' and message['question_id'] in questions:
            latest[message['question_id']]=message
    refs=[];qa=[]
    for q in questions.values():
        a=latest.get(q['id'])
        if a is None:continue
        refs.append({'question_id':q['id'],'answer_id':a['id'],'question_ordinal':q['ordinal'],'answer_ordinal':a['ordinal'],
            'question_sha256':digest(q),'answer_sha256':digest(a)})
        qa.append({'question_ref':opaque(scope,'user',q['id']),'question':q['content'],
            'answer_ref':opaque(scope,'assistant',a['id']),'answer':a['content']})
    return refs,qa

def valid_previous(state,scope,refs,qa,resources):
    if not isinstance(state,dict) or set(state)!={'v','scope','state_revision','lineage_epoch','validity','artifact','invalidation'}:
        return None,0
    try:
        artifact=state['artifact']
        origin=resources.resources_for_contract(artifact['contract'])
        contract=origin.contract
        if (type(state['v']) is not int or state['v']!=2 or state['scope']!=scope
            or type(state['state_revision']) is not int or state['state_revision']<0
            or not (uuid(state['lineage_epoch']) or hash_value(state['lineage_epoch']))
            or state['validity']!={'valid':True,'reason':None} or state['invalidation'] is not None
            or not isinstance(artifact,dict) or artifact['lineage_epoch']!=state['lineage_epoch']
            or set(artifact)!={'artifact_id','artifact_revision','lineage_epoch','parent_artifact_id','parent_artifact_sha256',
                'previous_payload_used','source_refs','frontier_processed','source_selection_hash','exact_output','text_sha256','contract','observations'}
            or not (uuid(artifact['artifact_id']) or hash_value(artifact['artifact_id']))
            or type(artifact['artifact_revision']) is not int or artifact['artifact_revision']<=0
            or not isinstance(artifact['observations'],dict)
            or artifact['contract']!=contract or not artifact['source_refs']
            or artifact['source_refs']!=refs[:len(artifact['source_refs'])]
            or artifact['frontier_processed']!=artifact['source_refs'][-1]
            or artifact['source_selection_hash']!=digest({'scope':scope,'pairs':artifact['source_refs']})
            or artifact['text_sha256']!=digest(artifact['exact_output'])):
            return None,0
        covered=len(artifact['source_refs'])
        sources={p[r+'_ref']:p[r] for p in qa[:covered] for r in ('question','answer')}
        return validate_output(artifact['exact_output'],sources,origin),covered
    except (KeyError,ValueError,TypeError):return None,0

def authorize(app,envelope,resources,engine=None):
    scope=envelope['scope'];database=getattr(app.state,'chat_database',None)
    if database is None:raise Rejected(503,'summary_not_ready')
    with (engine or database.engine).connect() as c:
        row=c.execute(text('SELECT CAST(dialogue_history AS TEXT),CAST(dialogue_summary AS TEXT) FROM conversations '
            'WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id'),scope).first()
    if row is None:raise Rejected(404,'not_found')
    document=source_json(row[0]);refs,qa=ledger(document,scope)
    state=None if row[1] is None else source_json(row[1])
    if envelope['parent_hash']!=(None if state is None else digest(state)):
        raise Rejected(409,'summary_parent_stale')
    previous,covered=valid_previous(state,scope,refs,qa,resources)
    if previous is not None and envelope['lineage_epoch']!=state['lineage_epoch']:
        raise Rejected(409,'summary_epoch_stale')
    if (isinstance(state,dict) and state.get('scope')==scope and isinstance(state.get('validity'),dict)
        and state['validity'].get('valid') is False and (uuid(state.get('lineage_epoch')) or hash_value(state.get('lineage_epoch')))
        and envelope['lineage_epoch']!=state['lineage_epoch']):
        raise Rejected(409,'summary_epoch_stale')
    selected=envelope['selected_pairs']
    if covered+selected>len(qa)-4 or envelope['source_refs']!=refs[covered:covered+selected]:
        raise Rejected(409,'summary_sources_stale')
    payload={'previous_summary':previous,'pairs':qa[covered:covered+selected]}
    if envelope['payload']!=payload or envelope['input_hash']!=digest(payload):
        raise Rejected(409,'summary_input_stale')
    messages,total=resources.prepare_input(payload)
    sources={p[r+'_ref']:p[r] for p in qa[:covered+selected] for r in ('question','answer')}
    return messages,total,sources

def parse_envelope(raw,app,resources):
    try:
        if len(raw)>1048576:raise Rejected(413,'summary_input_limit')
        value=complete_json(raw.decode())
        if not isinstance(value,dict) or set(value)!=ENVELOPE:raise ValueError()
        scope=value['scope']
        if (type(value['v']) is not int or value['v']!=2 or not uuid(value['job_id']) or not (uuid(value['lineage_epoch']) or hash_value(value['lineage_epoch']))
            or not isinstance(scope,dict) or set(scope)!=SCOPE_KEYS or not all(identifier(x) for x in scope.values())
            or value['boot_id']!=app.state.chat_boot_id or value['summary_version']!=resources.summary_version
            or value['schema_sha256']!=resources.response_schema_sha256 or value['tokenizer_sha256']!=resources.tokenizer_sha256
            or not hash_value(value['input_hash']) or (value['parent_hash'] is not None and not hash_value(value['parent_hash']))
            or type(value['selected_pairs']) is not int or value['selected_pairs']<=0
            or not isinstance(value['source_refs'],list) or len(value['source_refs'])!=value['selected_pairs']
            or any(not isinstance(r,dict) or set(r)!=REF_KEYS for r in value['source_refs'])
            or any(not all(identifier(r[k]) for k in ('question_id','answer_id'))
                or not all(type(r[k]) is int and r[k]>=0 for k in ('question_ordinal','answer_ordinal'))
                or not all(hash_value(r[k]) for k in ('question_sha256','answer_sha256')) for r in value['source_refs'])
            or type(value['deadline']) not in (int,float) or not time.time()<value['deadline']<=time.time()+30):
            raise ValueError()
        resources.prepare_input(value['payload'])
        if value['input_hash']!=digest(value['payload']):raise ValueError()
        return value
    except Rejected:raise
    except (ValueError,TypeError,KeyError,RecursionError):raise Rejected(409,'summary_input_invalid') from None

@dataclass
class Job:
    envelope:dict
    task:object=None
    state:str='running'
    settled:bool=False
    stop_reason:str|None=None
    status:int=200
    code:str|None=None
    output:dict|None=None
    receipt:dict|None=None
    pending:object=None
    call_id:str=field(default_factory=lambda:str(uuid4()))
    admitted:bool=False
    sql:object=None

    def public(self):
        value={k:self.envelope[k] for k in ('job_id','scope','boot_id','input_hash','summary_version')}
        value.update(v=2,state=self.state,settled=self.settled)
        if self.code is not None:value['code']=self.code
        if self.output is not None:value['output']=self.output;value['receipt']=self.receipt
        return value

async def tracked(job,function,*args):
    worker=asyncio.create_task(asyncio.to_thread(function,*args))
    job.pending=worker
    try:return await asyncio.shield(worker)
    finally:
        if worker.done():job.pending=None

async def run_job(app,job,resources):
    try:
        database=getattr(app.state,'chat_database',None)
        if database is None:raise Rejected(503,'summary_not_ready')
        job.sql=SummarySQL(database.engine,job.envelope['deadline'])
        messages,total,sources=await tracked(job,authorize,app,job.envelope,resources,job.sql)
        if job.stop_reason or job.envelope['deadline']<=time.time():raise Rejected(504,'summary_deadline')
        result=await app.state.summary_gateway.dispatch(job.envelope['job_id'],messages,resources,job.envelope['deadline'])
        if job.stop_reason:raise Rejected(503,'summary_cancelled')
        output=await tracked(job,validate_output,result['output'],sources,resources)
        if job.stop_reason or job.envelope['deadline']<=time.time():raise Rejected(504,'summary_deadline')
        job.output=output
        job.receipt={'call_id':job.call_id,'dispatch_count':1,'input_hash':job.envelope['input_hash'],'output_hash':digest(output),
            'summary_version':resources.summary_version,'boot_id':app.state.chat_boot_id,
            'input_total_tokens':total,'wrapper_margin_tokens':1024,'usage':result['usage'],'cost':result['cost'],'observed_model':result['observed_model']}
        job.state='completed'
    except (Rejected,SummaryGatewayError) as failure:
        job.status=failure.status;job.code=failure.code;job.state='failed'
    except SummarySQLDeadline:
        job.status=504;job.code='summary_deadline';job.state='failed'
    except ValueError:
        job.status=422;job.code='summary_invalid_response';job.state='failed'
    except Exception:
        job.status=503;job.code='summary_failed';job.state='failed'
    finally:
        # This task is not cancelled by the observer/cancel endpoint: it waits
        # for the owned SQL/CPU/gateway worker to finish before declaring settled.
        if job.sql is not None:await tracked(job,job.sql.close)
        if job.stop_reason:
            job.state='cancelled' if job.stop_reason=='cancelled' else 'failed'
            job.output=None;job.receipt=None
        job.settled=True
        # Retain authenticated status/output for uncertain-ACK recovery, while
        # removing heavy source input from terminal RAM records.
        job.envelope={k:v for k,v in job.envelope.items() if k not in ('payload','source_refs')}

def stop(app,job,reason):
    if job.settled:return
    job.stop_reason=reason;job.state='cancelling'
    if job.sql is not None:job.sql.cancel()
    gateway=getattr(app.state,'summary_gateway',None)
    if gateway is not None:gateway.cancel(job.envelope['job_id'])

async def shutdown(app):
    jobs=getattr(app.state,'summary_jobs',{})
    controls=list(getattr(app.state,'summary_sql_controls',set()))
    for owner,worker in controls:owner.cancel()
    gateway=getattr(app.state,'summary_gateway',None)
    for job in list(jobs.values()):
        if isinstance(job,Job):stop(app,job,'cancelled')
    tasks=[job.task for job in jobs.values() if isinstance(job,Job) and job.task is not None]
    app.state.summary_gateway=None
    preparations=list(getattr(app.state,'summary_preparations',set()))
    await asyncio.gather(*tasks,*(worker for owner,worker in controls),*preparations,return_exceptions=True)
    for owner,worker in controls:await asyncio.to_thread(owner.close)
    if any(isinstance(job,Job) and job.sql is not None and not job.sql.closed for job in jobs.values()):
        raise RuntimeError('Summary SQL physical shutdown not confirmed.')
    app.state.summary_sql_controls=set()
    app.state.summary_preparations=set()
    if gateway is not None:await gateway.close()
    app.state.summary_jobs={}
    app.state.summary_gateway=None

def install_routes(app,signed_response):
    app.state.summary_jobs={}
    app.state.summary_gateway=None
    app.state.summary_sql_controls=set()
    app.state.summary_preparations=set()

    @app.post(ROOT)
    async def submit(request:Request):
        resources=getattr(app.state,'summary_resources',None)
        gateway=getattr(app.state,'summary_gateway',None)
        if resources is None or gateway is None:
            return signed_response(request,{'v':2,'code':'summary_not_ready'},503)
        try:
            preparation=asyncio.create_task(asyncio.to_thread(parse_envelope,request.state.chat_body,app,resources))
            app.state.summary_preparations.add(preparation)
            preparation.add_done_callback(app.state.summary_preparations.discard)
            envelope=await asyncio.shield(preparation)
            if envelope['deadline']<=time.time():raise Rejected(504,'summary_deadline')
            with app.state.chat_gate:
                jobs=app.state.summary_jobs
                if resources is not getattr(app.state,'summary_resources',None) or gateway is not getattr(app.state,'summary_gateway',None):raise Rejected(503,'summary_not_ready')
                if envelope['job_id'] in jobs:raise Rejected(409,'summary_job_replayed')
                from app.chat import validate_capacity
                from app.core.chat_admission import summary_allowed
                try:capacity=validate_capacity(getattr(app.state,'chat_capacity',8))
                except Exception:raise Rejected(503,'capacity_invalid') from None
                if len(jobs)>=4096 or any(not isinstance(job,Job) for job in jobs.values()) or not summary_allowed(app,capacity):
                    raise Rejected(503,'summary_capacity')
                # Cancel and POST use the SAME registration lock. A confirmed
                # marker fences even a POST whose input preparation ran earlier.
                job=Job(envelope,admitted=True);jobs[envelope['job_id']]=job
                job.task=asyncio.create_task(run_job(app,job,resources))
            try:
                await asyncio.wait_for(asyncio.shield(job.task),max(.001,envelope['deadline']-time.time()))
            except asyncio.TimeoutError:
                job.status=504;job.code='summary_deadline'
                stop(app,job,'deadline')
            except asyncio.CancelledError:
                stop(app,job,'cancelled')
                raise
            return signed_response(request,job.public(),job.status)
        except Rejected as failure:
            return signed_response(request,{'v':2,'code':failure.code},failure.status)

    def owned(job_id,raw):
        try:
            body=complete_json(raw.decode());job=app.state.summary_jobs.get(job_id)
            if (not isinstance(body,dict) or set(body)!={'v','scope','boot_id','input_hash'}
                or type(body['v']) is not int or body['v']!=2 or not isinstance(job,Job)
                or any(body[k]!=job.envelope[k] for k in ('scope','boot_id','input_hash'))
                or body['boot_id']!=app.state.chat_boot_id):
                return None
            return job
        except (ValueError,KeyError,TypeError):return None

    @app.get(ROOT+'/{job_id}')
    async def status(job_id:str,request:Request):
        job=owned(job_id,request.state.chat_body)
        if job is None:return signed_response(request,{'v':2,'code':'not_found'},404)
        return signed_response(request,job.public())

    def cancel_control(job_id,raw):
        try:
            body=complete_json(raw.decode())
            if (not uuid(job_id) or not isinstance(body,dict) or set(body)!={'v','scope','boot_id','input_hash'}
                or type(body['v']) is not int or body['v']!=2 or body['boot_id']!=app.state.chat_boot_id
                or not hash_value(body['input_hash']) or not isinstance(body['scope'],dict)
                or set(body['scope'])!=SCOPE_KEYS or not all(identifier(x) for x in body['scope'].values())):
                return None
            return body
        except (KeyError,ValueError,TypeError):return None

    def scope_owned(scope,engine):
        database=getattr(app.state,'chat_database',None)
        if database is None:return False
        with engine.connect() as connection:
            return connection.execute(text('SELECT 1 FROM conversations WHERE id=:conversation_id '
                'AND tenant_id=:tenant_id AND user_id=:user_id'),scope).first() is not None

    @app.post(ROOT+'/{job_id}/cancel')
    async def cancel(job_id:str,request:Request):
        body=cancel_control(job_id,request.state.chat_body)
        if body is None:return signed_response(request,{'v':2,'code':'not_found'},404)
        # A 404 alone is never confirmation. An absent job requires an owner
        # read and an atomic marker; the marker prohibits every later dispatch.
        with app.state.chat_gate:
            entry=app.state.summary_jobs.get(job_id)
            job=owned(job_id,request.state.chat_body)
            if entry is not None and job is None:
                return signed_response(request,{'v':2,'code':'not_found'},404)
        if job is None:
            resources=getattr(app.state,'summary_resources',None)
            if resources is None:
                return signed_response(request,{'v':2,'code':'summary_not_ready'},503)
            owner=None;worker=None;registry=app.state.summary_jobs
            try:
                database=getattr(app.state,'chat_database',None)
                if database is None:raise RuntimeError('Summary SQL unavailable.')
                owner=SummarySQL(database.engine,time.time()+2)
                worker=asyncio.create_task(asyncio.to_thread(scope_owned,body['scope'],owner))
                entry=(owner,worker);app.state.summary_sql_controls.add(entry)
                try:allowed=await asyncio.shield(worker)
                except asyncio.CancelledError:
                    owner.cancel();await asyncio.gather(worker,return_exceptions=True);raise
                finally:
                    await asyncio.to_thread(owner.close)
                    app.state.summary_sql_controls.discard(entry)
            except Exception:
                return signed_response(request,{'v':2,'code':'summary_control_unavailable'},503)
            if not allowed:return signed_response(request,{'v':2,'code':'not_found'},404)
            with app.state.chat_gate:
                # Recheck after the SQL await: POST may already own this job.
                if body['boot_id']!=app.state.chat_boot_id or registry is not app.state.summary_jobs:
                    return signed_response(request,{'v':2,'code':'not_found'},404)
                entry=app.state.summary_jobs.get(job_id)
                job=owned(job_id,request.state.chat_body)
                if entry is not None and job is None:
                    return signed_response(request,{'v':2,'code':'not_found'},404)
                if job is None:
                    if len(app.state.summary_jobs)>=4096:
                        return signed_response(request,{'v':2,'code':'summary_capacity'},503)
                    marker={'v':2,'job_id':job_id,'scope':body['scope'],'boot_id':body['boot_id'],
                        'input_hash':body['input_hash'],'summary_version':resources.summary_version}
                    job=Job(marker,state='cancelled',settled=True,stop_reason='cancelled')
                    app.state.summary_jobs[job_id]=job
        stop(app,job,'cancelled')
        # Give the owned socket/resolver worker a bounded chance to settle;
        # otherwise return202 and keep the reservation until status confirms it.
        if not job.settled:
            await asyncio.wait({job.task},timeout=.1)
        return signed_response(request,job.public(),200 if job.settled else 202)
