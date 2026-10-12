"""Signed scoped summary jobs reauthorize current JSONB before any inference."""
import asyncio,copy,time
from decimal import Decimal
import httpx,pytest
from sqlalchemy import text
from test_chat_summary_gateway_jup035 import summary_session,envelope,exercise,request,ROUTE,SCOPE,canonical,persist_doc
from test_chat_private_jup035 import signed

def test_private_summary_nonce_and_job_replay_cannot_dispatch_again(summary_session):
    body=envelope(summary_session)
    async def run(client,application):
        raw=canonical(body).encode();headers=signed('POST',ROUTE,raw)
        first=await request(client,'POST',ROUTE,body,headers);assert first.status_code==200,first.text
        replay=await request(client,'POST',ROUTE,body,headers);assert replay.status_code==401
        duplicate=await request(client,'POST',ROUTE,body);assert duplicate.status_code==409
        assert len(summary_session[2])==1
    exercise(summary_session,run)

@pytest.mark.parametrize('defect',['missing_signature','bad_signature','query','foreign_user','foreign_tenant','foreign_conversation','boot','version','schema','tokenizer','input_hash','parent','source_hash','source_ordinal','source_gap','opaque_ref','body_extra','screen','metadata','cost_evidence','expired','too_long'])
def test_private_summary_rejects_bad_auth_scope_versions_and_sources_before_provider(summary_session,defect):
    body=envelope(summary_session);headers=None;path=ROUTE
    if defect=='missing_signature':headers={'Content-Type':'application/json'}
    elif defect=='bad_signature':headers=signed('POST',ROUTE,canonical(body).encode());headers['X-Chat-Signature']='0'*64
    elif defect=='query':path+='?debug=1'
    elif defect in ['foreign_user','foreign_tenant','foreign_conversation']:body['scope'][{'foreign_user':'user_id','foreign_tenant':'tenant_id','foreign_conversation':'conversation_id'}[defect]]='foreign'
    elif defect=='boot':body['boot_id']='other-boot'
    elif defect=='version':body['summary_version']='other-version'
    elif defect=='schema':body['schema_sha256']='0'*64
    elif defect=='tokenizer':body['tokenizer_sha256']='0'*64
    elif defect=='input_hash':body['input_hash']='0'*64
    elif defect=='parent':body['parent_hash']='0'*64
    elif defect=='source_hash':body['source_refs'][0]['answer_sha256']='0'*64
    elif defect=='source_ordinal':body['source_refs'][0]['question_ordinal']+=1
    elif defect=='source_gap':body['source_refs']=body['source_refs'][1:]
    elif defect=='opaque_ref':body['payload']['pairs'][0]['question_ref']='q-'+'f'*64
    elif defect=='body_extra':body['unapproved']='not allowed'
    elif defect in ['screen','metadata','cost_evidence']:body['payload'][defect]='synthetic-not-model'
    elif defect=='expired':body['deadline']=time.time()-1
    else:
        from app.core.config import get_settings
        body['deadline']=time.time()+get_settings().summary_timeout_seconds+1
    async def run(client,application):
        if defect=='too_long':
            from app.core.config import get_settings
            body['deadline']=time.time()+get_settings().summary_timeout_seconds+1
        response=await request(client,'POST',path,body,headers)
        assert response.status_code in [401,404,409,413,503],response.text
        assert summary_session[2]==[]
    exercise(summary_session,run)

def test_private_summary_checks_latest_answer_again_after_backend_snapshot(summary_session):
    body=envelope(summary_session);doc=summary_session[3];new=copy.deepcopy(doc['messages'][1]);new.update(id='new-latest',ordinal=12,content='Alternativa vigente')
    doc['messages'].append(new);doc['next_ordinal']=13;doc['revision']+=1;persist_doc(summary_session)
    async def run(client,application):
        result=await request(client,'POST',ROUTE,body);assert result.status_code==409,result.text
        assert summary_session[2]==[]
    exercise(summary_session,run)

def test_private_summary_source_hash_preserves_decimal_metadata_but_never_sends_it(summary_session):
    summary_session[3]['messages'][0]['metadata']['precise']=Decimal('12345678901234567890.000000000000000000001');persist_doc(summary_session)
    body=envelope(summary_session)
    async def run(client,application):
        result=await request(client,'POST',ROUTE,body);assert result.status_code==200,result.text
        assert '12345678901234567890' not in canonical(summary_session[2][0]['body'])
        assert len(summary_session[2])==1
    exercise(summary_session,run)

def test_private_summary_status_is_scoped_and_public_app_has_no_dispatch_surface(summary_session):
    body=envelope(summary_session)
    async def run(client,application):
        result=await request(client,'POST',ROUTE,body);assert result.status_code==200,result.text
        control={'v':2,'scope':{**SCOPE,'user_id':'foreign'},'boot_id':'synthetic-boot','input_hash':body['input_hash']}
        status=await request(client,'GET',ROUTE+'/'+body['job_id'],control);assert status.status_code==404
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=summary_session[0][0][1]),base_url='http://public') as public:
            result=await request(public,'POST',ROUTE,body);assert result.status_code==404 and 'summary_version' not in result.text
        assert len(summary_session[2])==1
    exercise(summary_session,run)

@pytest.mark.parametrize('failure',['disabled','missing_key','main_key_reused','resource_missing'])
def test_unavailable_optional_summary_keeps_main_descriptor_and_makes_no_call(summary_session,monkeypatch,failure,tmp_path):
    if failure=='disabled':monkeypatch.setenv('SUMMARY_ENABLED','false')
    elif failure=='missing_key':monkeypatch.setenv('SUMMARY_API_KEY_FILE',str(tmp_path/'missing'))
    elif failure=='main_key_reused':
        from test_chat_summary_gateway_jup035 import MAIN_KEY
        file=tmp_path/'same-key';file.write_text(MAIN_KEY,encoding='utf-8');monkeypatch.setenv('SUMMARY_API_KEY_FILE',str(file))
    else:monkeypatch.setenv('SUMMARY_RESOURCE_DIRECTORY',str(tmp_path/'missing'))
    body=envelope(summary_session)
    async def run(client,application):
        response=await request(client,'POST',ROUTE,body);assert response.status_code==503,response.text
        main=await client.get('/internal/chat/v2/descriptor',headers=signed('GET','/internal/chat/v2/descriptor'));assert main.status_code==200
        assert summary_session[2]==[]
    exercise(summary_session,run)

def test_private_summary_cancel_reconciles_own_job_and_never_redispatches(summary_session):
    summary_session[1].behavior='stall';body=envelope(summary_session)
    async def run(client,application):
        task=asyncio.create_task(request(client,'POST',ROUTE,body))
        for _ in range(100):
            if summary_session[2]:break
            await asyncio.sleep(.005)
        assert len(summary_session[2])==1
        control={'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']}
        cancel=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control);assert cancel.status_code in [200,202],cancel.text
        for _ in range(40):
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
            if status.json()['settled']:break
            await asyncio.sleep(.025)
        assert status.json()['state']=='cancelled' and status.json()['settled'] is True
        await asyncio.wait_for(task,1)
        assert (await request(client,'POST',ROUTE,body)).status_code==409 and len(summary_session[2])==1
    exercise(summary_session,run)

# Register every existing fixture dependency in this collected module.
from test_chat_private_jup035 import private
from test_chat_resources_jup035 import resources
from test_chat_summary_resources_jup035 import summary_bundle

# Reconciliation55a: only signed private controls may fence a not-yet-arrived job.
def test_summary_cancel_missing_owned_job_is_confirmed_without_dispatch_and_fences_late_post(summary_session):
    body=envelope(summary_session)
    control={'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']}
    async def run(client,application):
        before=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
        assert before.status_code==404 and before.json().get('settled') is not True
        result=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
        assert result.status_code==200,result.text
        marker=result.json()
        assert marker['state']=='cancelled' and marker['settled'] is True and marker['job_id']==body['job_id']
        assert marker['scope']==SCOPE and marker['boot_id']==body['boot_id'] and marker['input_hash']==body['input_hash']
        assert marker['summary_version']==body['summary_version'] and 'output' not in marker and 'receipt' not in marker
        assert summary_session[2]==[]
        assert (await request(client,'POST',ROUTE,body)).status_code==409
        assert summary_session[2]==[]
        again=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
        assert again.status_code==200 and again.json()==marker
        status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
        assert status.status_code==200 and status.json()==marker
        with summary_session[0][0][2].connect() as connection:
            row=connection.execute(text("SELECT CAST(dialogue_history AS TEXT),CAST(dialogue_summary AS TEXT) FROM conversations WHERE id='chat'")).first()
        assert row[0]==canonical(summary_session[3]) and row[1] is None
    exercise(summary_session,run)

@pytest.mark.parametrize('defect',['foreign_user','foreign_tenant','foreign_conversation','boot','hash','extra'])
def test_summary_absent_cancel_never_fences_foreign_or_tampered_control(summary_session,defect):
    body=envelope(summary_session)
    control={'v':2,'scope':dict(SCOPE),'boot_id':'synthetic-boot','input_hash':body['input_hash']}
    if defect.startswith('foreign'):
        control['scope'][{'foreign_user':'user_id','foreign_tenant':'tenant_id','foreign_conversation':'conversation_id'}[defect]]='foreign'
    elif defect=='boot':control['boot_id']='other-boot'
    elif defect=='hash':control['input_hash']='not-a-hash'
    else:control['extra']='not permitted'
    async def run(client,application):
        result=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
        assert result.status_code==404,result.text
        assert application.state.summary_jobs=={} and summary_session[2]==[]
    exercise(summary_session,run)

def test_summary_absent_cancel_missing_summary_key_preserves_main_and_fences_job(summary_session,monkeypatch,tmp_path):
    monkeypatch.setenv('SUMMARY_API_KEY_FILE',str(tmp_path/'missing'))
    body=envelope(summary_session);control={'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']}
    async def run(client,application):
        result=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
        assert result.status_code==200 and result.json()['settled'] is True and result.json()['state']=='cancelled'
        main=await client.get('/internal/chat/v2/descriptor',headers=signed('GET','/internal/chat/v2/descriptor'))
        assert main.status_code==200 and summary_session[2]==[]
    exercise(summary_session,run)

def test_summary_cancel_registered_job_waits_for_own_sql_worker_before_settled(summary_session,monkeypatch):
    import threading
    from app import summary as existing
    original=existing.authorize;entered=threading.Event();release=threading.Event()
    def blocked(*args):
        entered.set()
        assert release.wait(4),'Synthetic owned SQL read was not released'
        return original(*args)
    monkeypatch.setattr(existing,'authorize',blocked)
    body=envelope(summary_session)
    async def run(client,application):
        task=asyncio.create_task(request(client,'POST',ROUTE,body))
        try:
            for _ in range(100):
                if entered.is_set():break
                await asyncio.sleep(.005)
            assert entered.is_set()
            control={'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']}
            cancelled=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
            assert cancelled.status_code==202 and cancelled.json()['settled'] is False
            assert summary_session[2]==[]
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
            assert status.json()['settled'] is False and status.json()['state']=='cancelling'
            release.set()
            await asyncio.wait_for(task,2)
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
            assert status.json()['settled'] is True and status.json()['state']=='cancelled'
            assert summary_session[2]==[] and (await request(client,'POST',ROUTE,body)).status_code==409
        finally:
            release.set()
            await asyncio.gather(task,return_exceptions=True)
    exercise(summary_session,run)

def test_summary_cancel_while_post_prepares_rechecks_marker_before_admission(summary_session,monkeypatch):
    import threading
    from app import summary as existing
    original=existing.parse_envelope;entered=threading.Event();release=threading.Event()
    def blocked(*args):
        entered.set();assert release.wait(4)
        return original(*args)
    monkeypatch.setattr(existing,'parse_envelope',blocked)
    body=envelope(summary_session)
    async def run(client,application):
        task=asyncio.create_task(request(client,'POST',ROUTE,body))
        try:
            for _ in range(100):
                if entered.is_set():break
                await asyncio.sleep(.005)
            assert entered.is_set()
            control={'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']}
            marker=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
            assert marker.status_code==200 and marker.json()['state']=='cancelled' and marker.json()['settled'] is True
            release.set()
            posted=await asyncio.wait_for(task,2)
            assert posted.status_code==409 and summary_session[2]==[]
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
            assert status.json()['state']=='cancelled' and status.json()['settled'] is True
        finally:
            release.set();await asyncio.gather(task,return_exceptions=True)
    exercise(summary_session,run)

def test_summary_cancel_missing_job_registration_is_bounded_without_evicting_live_or_tombstones(summary_session):
    body=envelope(summary_session)
    async def run(client,application):
        # Synthetic occupied RAM entries are an explicit boundary fixture, not
        # proof that thousands of real calls were made.
        retained={str(i):{'synthetic':'occupied'} for i in range(4096)}
        application.state.summary_jobs.update(retained)
        control={'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']}
        result=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
        assert result.status_code==503 and result.json().get('settled') is not True
        assert application.state.summary_jobs==retained and summary_session[2]==[]
        application.state.summary_jobs.clear()
    exercise(summary_session,run)


# 55b narrow reconciliation race: absent cancel SQL read versus live POST.
def test_summary_absent_cancel_sql_race_closes_registered_upstream_job_without_replacing_it(summary_session,monkeypatch):
    import threading
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    entered=threading.Event();release=threading.Event();cancel_thread=[]
    def pause_owner_read(connection,cursor,statement,parameters,context,many):
        if (connection.engine is not engine and connection.engine.url==engine.url
            and statement.startswith('SELECT 1 FROM conversations')
            and context.compiled_parameters and all(context.compiled_parameters[0].get(k)==SCOPE[k] for k in SCOPE)):
            cancel_thread.append(threading.get_ident());entered.set();assert release.wait(4)
    engine=summary_session[0][0][2]
    event.listen(Engine,'before_cursor_execute',pause_owner_read)
    body=envelope(summary_session);summary_session[1].behavior='stall'
    async def run(client,application):
        cancel_task=post_task=None
        try:
            control={'v':2,'scope':SCOPE,'boot_id':'synthetic-boot','input_hash':body['input_hash']}
            cancel_task=asyncio.create_task(request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control))
            for _ in range(100):
                if entered.is_set():break
                await asyncio.sleep(.005)
            assert entered.is_set()
            post_task=asyncio.create_task(request(client,'POST',ROUTE,body))
            for _ in range(100):
                if summary_session[2]:break
                await asyncio.sleep(.005)
            assert len(summary_session[2])==1
            original=application.state.summary_jobs[body['job_id']]
            assert original.task is not None and not original.settled
            release.set();cancel=await asyncio.wait_for(cancel_task,2)
            assert cancel.status_code in [200,202],cancel.text
            assert application.state.summary_jobs[body['job_id']] is original
            await asyncio.wait_for(post_task,2)
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
            assert status.json()['state']=='cancelled' and status.json()['settled'] is True
            assert original.task.done() and original.pending is None
            assert len(summary_session[2])==1 and (await request(client,'POST',ROUTE,body)).status_code==409
        finally:
            release.set();summary_session[4].set()
            await asyncio.gather(*(t for t in (cancel_task,post_task) if t is not None),return_exceptions=True)
    try:exercise(summary_session,run)
    finally:event.remove(Engine,'before_cursor_execute',pause_owner_read)
