"""Own disposable Cockroach probes; synthetic fixture data, no global/paid IO.

Creates a minimal conversations table only when absent and removes only its own
row. This setup does not validate the complete application schema/migrations.
"""
import asyncio,os,threading,time
from uuid import uuid4
from sqlalchemy import create_engine,event,text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

class Native:
    def __init__(self):
        url=os.environ.get('JUP035_COCKROACH_TEST_URL');assert url,'Documented own Cockroach test URL is required'
        self.engine=create_engine(url);self.inspect_engine=create_engine(url,poolclass=NullPool);self.inspector=None
        self.scope={'conversation_id':'jup035-native-fixture-'+uuid4().hex,'tenant_id':str(uuid4()),'user_id':str(uuid4())}
        self.fixture_row_created=False
        self.marker='jup035-native-job-'+str(uuid4());self.other_marker='jup035-native-main-'+str(uuid4())
        self.entered=threading.Event();self.returned=threading.Event();self.driver=None;self.code=None;self.query_seconds=0
        self.listener=None;self.fired=False;self.other_connection=None;self.other_thread=None;self.other_returned=threading.Event();self.other_success=False
        try:
            self.inspector=self.inspect_engine.connect()
            assert self.inspector.execute(text('SELECT current_database()')).scalar_one()==self.engine.url.database
            self.inspector.rollback()
            document=source_document();document['identity']=dict(self.scope)
            for message in document['messages']:message['author_id']=self.scope['user_id']
            with self.engine.begin() as connection:
                connection.execute(text('CREATE TABLE IF NOT EXISTS conversations(id STRING PRIMARY KEY,tenant_id STRING,user_id STRING,dialogue_history JSONB,dialogue_summary JSONB)'))
                connection.execute(text('INSERT INTO conversations(id,tenant_id,user_id,dialogue_history,dialogue_summary) VALUES (:conversation_id,:tenant_id,:user_id,CAST(:document AS JSONB),NULL)'),
                    {**self.scope,'document':canonical(document)})
            self.fixture_row_created=True
            row=self.inspector.execute(text('SELECT id,tenant_id,user_id FROM conversations WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id'),self.scope).first()
            assert row is not None,'Own prepared runtime conversation is required'
            self.scope={'conversation_id':row[0],'tenant_id':row[1],'user_id':row[2]}
        except BaseException:
            self.cleanup()
            raise
    def active(self,marker=None):
        return self.inspector.execute(text('SELECT count(*) FROM [SHOW CLUSTER QUERIES] WHERE query LIKE :pattern'),{'pattern':'%'+(marker or self.marker)+'%'}).scalar_one()>0
    def block(self,pattern,seconds=4):
        def before(connection,cursor,statement,params,context,many):
            if self.fired or pattern not in statement:return
            self.fired=True;self.driver=connection.connection.driver_connection;self.entered.set();start=time.monotonic()
            try:cursor.execute("SELECT pg_sleep("+str(seconds)+"), '"+self.marker+"' AS own_test_marker");cursor.fetchall()
            except Exception as exc:self.code=getattr(exc,'sqlstate',None);raise
            finally:self.query_seconds=time.monotonic()-start;self.returned.set()
        self.listener=before;event.listen(Engine,'before_cursor_execute',before)
    def main_control(self,seconds=1.7):
        self.other_connection=self.engine.connect()
        def run():
            try:self.other_connection.execute(text("SELECT pg_sleep("+str(seconds)+"), '"+self.other_marker+"' AS own_test_marker")).all();self.other_success=True
            finally:self.other_returned.set()
        self.other_thread=threading.Thread(target=run);self.other_thread.start()
    async def wait_active(self):
        for _ in range(200):
            if self.entered.is_set() and self.active():return
            await asyncio.sleep(.01)
        assert False,'Own real query was not observed active'
    async def wait_closed(self,seconds=1.2):
        until=time.monotonic()+seconds
        while time.monotonic()<until:
            if self.returned.is_set() and self.driver.closed:return
            await asyncio.sleep(.02)
    def verify_closed(self):
        observed={'query_returned':self.returned.is_set(),'query_active':self.active(),'physical_closed':bool(self.driver and self.driver.closed),'sqlstate':self.code}
        assert observed['query_returned'] and not observed['query_active'] and observed['physical_closed'],observed
    def verify_main(self):
        self.other_thread.join(3);assert self.other_success and not self.other_thread.is_alive()
        self.other_connection.rollback();assert self.other_connection.execute(text('SELECT 1')).scalar_one()==1
        assert not self.other_connection.connection.driver_connection.closed,'Summary cancelled or closed main connection'
    def cleanup(self):
        if self.listener:event.remove(Engine,'before_cursor_execute',self.listener)
        if self.driver is not None and not self.driver.closed and not self.returned.is_set():
            try:self.driver.cancel_safe(timeout=1)
            except Exception:pass
        if self.other_thread:self.other_thread.join(5)
        if self.other_connection:self.other_connection.close()
        try:
            if self.fixture_row_created:
                with self.engine.begin() as connection:
                    connection.execute(text('DELETE FROM conversations WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id'),self.scope)
                self.fixture_row_created=False
        finally:
            if self.inspector is not None:self.inspector.close()
            self.inspect_engine.dispose();self.engine.dispose()

from types import SimpleNamespace
import pytest
from test_chat_private_jup035 import private
from test_chat_resources_jup035 import resources
from test_chat_summary_resources_jup035 import summary_bundle
from test_chat_summary_gateway_jup035 import summary_session,envelope,exercise,request,ROUTE,source_document,canonical

async def wait_settled(job, seconds=1.5):
    # HTTP timeout/cancel responses do not acknowledge completion of cleanup.
    # Shield the owner so a failed test wait cannot cancel its SQL cleanup.
    assert job.task is not None
    await asyncio.wait_for(asyncio.shield(job.task), timeout=seconds)
    assert job.settled and (job.pending is None or job.pending.done())
    assert job.sql is None or job.sql.closed

@pytest.fixture
def native():
    if not os.environ.get('JUP035_COCKROACH_TEST_URL'):
        if os.environ.get('JUP035_REQUIRE_NATIVE_SQL')=='true':
            pytest.fail('Required native SQL integration has no JUP035_COCKROACH_TEST_URL')
        pytest.skip('Native SQL integration not configured; set JUP035_COCKROACH_TEST_URL and JUP035_REQUIRE_NATIVE_SQL=true')
    value=Native()
    try:yield value
    finally:value.cleanup()

@pytest.mark.parametrize('mode',['deadline','cancel','shutdown'])
def test_existing_private_summary_closes_real_owned_sql_before_settled(summary_session,native,monkeypatch,mode):
    native.block('SELECT CAST(dialogue_history AS TEXT)',4);native.main_control()
    async def scenario(client,application):
        monkeypatch.setattr(application.state,'chat_database',SimpleNamespace(engine=native.engine))
        # Allow preparation and the server-side visibility probe to finish before
        # expiry. The four-second query must still be cancelled in under three
        # seconds; the separate fallback test retains its real 0.35-second window.
        body=envelope(summary_session,scope=native.scope,deadline=time.time()+(1 if mode=='deadline' else 30))
        task=asyncio.create_task(request(client,'POST',ROUTE,body));shutdown=None
        try:
            await native.wait_active();job=application.state.summary_jobs[body['job_id']]
            assert not job.settled and not native.driver.closed
            if mode=='cancel':
                control={'v':2,'scope':native.scope,'boot_id':body['boot_id'],'input_hash':body['input_hash']}
                response=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
                assert response.status_code in [200,202]
                if response.json()['settled']:assert native.driver.closed and native.returned.is_set()
            elif mode=='shutdown':
                from app.summary import shutdown as close
                shutdown=asyncio.create_task(close(application))
            await native.wait_closed(1.5);native.verify_closed()
            assert native.code=='57014' and native.query_seconds<3
            responses=await asyncio.gather(task,return_exceptions=True)
            if mode=='deadline':
                assert responses[0].status_code==504
                assert responses[0].json()['code']=='summary_deadline'
            if shutdown is not None:await shutdown
            await wait_settled(job)
            assert job.settled and (job.pending is None or job.pending.done()) and summary_session[2]==[]
            assert application.state.chat_database.engine is native.engine
            native.verify_main()
        finally:
            if native.driver is not None and not native.driver.closed and not native.returned.is_set():native.driver.cancel_safe(timeout=1)
            await asyncio.gather(task,return_exceptions=True)
            if shutdown is not None:await asyncio.gather(shutdown,return_exceptions=True)
    exercise(summary_session,scenario)

def test_absent_cancel_owner_read_has_own_deadline_and_no_confirmed_marker_before_close(summary_session,native,monkeypatch):
    native.block('SELECT 1 FROM conversations',5);native.main_control(.2)
    async def scenario(client,application):
        monkeypatch.setattr(application.state,'chat_database',SimpleNamespace(engine=native.engine))
        body=envelope(summary_session,scope=native.scope);control={'v':2,'scope':native.scope,'boot_id':body['boot_id'],'input_hash':body['input_hash']}
        task=asyncio.create_task(request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control))
        try:
            await native.wait_active()
            assert body['job_id'] not in application.state.summary_jobs
            await native.wait_closed(3);native.verify_closed()
            assert native.code=='57014' and body['job_id'] not in application.state.summary_jobs
            response=await task;assert response.status_code==503 and response.json()['code']=='summary_control_unavailable'
            assert summary_session[2]==[] and application.state.chat_database.engine is native.engine
            native.verify_main()
        finally:
            if native.driver is not None and not native.driver.closed and not native.returned.is_set():native.driver.cancel_safe(timeout=1)
            await asyncio.gather(task,return_exceptions=True)
    exercise(summary_session,scenario)

def test_input_preparation_expiry_never_opens_late_sql_or_dispatches(summary_session,monkeypatch):
    async def scenario(client,application):
        resource=application.state.summary_resources;real=resource.prepare_input;entered=threading.Event();sql=[]
        def slow(*args):entered.set();time.sleep(.55);return real(*args)
        monkeypatch.setattr(type(resource),'prepare_input',lambda self,*args:slow(*args))
        database=application.state.chat_database.engine
        def record(connection,cursor,statement,params,context,many):
            if 'SELECT CAST(dialogue_history AS TEXT)' in statement:sql.append(time.time())
        event.listen(database,'before_cursor_execute',record)
        try:
            body=envelope(summary_session,deadline=time.time()+.25)
            response=await request(client,'POST',ROUTE,body)
            assert entered.is_set() and response.status_code in [409,504]
            assert sql==[],'SQL was started after preparation consumed the original deadline'
            assert summary_session[2]==[]
        finally:event.remove(database,'before_cursor_execute',record)
    exercise(summary_session,scenario)

def test_successful_native_reauthorization_closes_job_connection_and_leaves_main_engine_usable(summary_session,native,monkeypatch):
    async def scenario(client,application):
        from app.summary import source_json,ledger,valid_previous,digest
        resource=application.state.summary_resources
        with native.engine.connect() as c:
            row=c.execute(text('SELECT CAST(dialogue_history AS TEXT),CAST(dialogue_summary AS TEXT) FROM conversations WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id'),native.scope).first()
        document=source_json(row[0]);state=None if row[1] is None else source_json(row[1]);refs,qa=ledger(document,native.scope)
        previous,covered=valid_previous(state,native.scope,refs,qa,resource)
        assert len(qa)-covered>=5,'Own prepared runtime requires eligible native QA'
        payload={'previous_summary':previous,'pairs':qa[covered:covered+1]};resource.prepare_input(payload)
        body=envelope(summary_session,scope=native.scope,parent_hash=None if state is None else digest(state),
            lineage_epoch=state['lineage_epoch'] if state is not None and previous is not None else str(uuid4()),
            source_refs=refs[covered:covered+1],selected_pairs=1,payload=payload,input_hash=digest(payload))
        monkeypatch.setattr(application.state,'chat_database',SimpleNamespace(engine=native.engine))
        native.block('SELECT CAST(dialogue_history AS TEXT)',0);native.main_control(.2)
        response=await request(client,'POST',ROUTE,body)
        assert response.status_code==200 and response.json()['state']=='completed',response.text
        assert response.json()['settled'] is True and len(summary_session[2])==1
        assert native.entered.is_set() and native.returned.is_set() and native.driver.closed
        assert application.state.chat_database.engine is native.engine
        native.verify_main()
    exercise(summary_session,scenario)

def test_native_local_remaining_timeout_closes_owned_query_when_cancel_safe_fails_off_loop(summary_session,native,monkeypatch):
    """The server-local deadline still fences SQL if the owned cancel request fails."""
    measurements={};faults=[];rescue_used=False
    class TimedReturn(threading.Event):
        def set(self):
            measurements.setdefault('query_return',time.monotonic())
            super().set()
    native.returned=TimedReturn()
    native.block('SELECT CAST(dialogue_history AS TEXT)',4);native.main_control()
    async def scenario(client,application):
        nonlocal rescue_used
        monkeypatch.setattr(application.state,'chat_database',SimpleNamespace(engine=native.engine))
        started=time.monotonic();deadline=time.time()+.35
        body=envelope(summary_session,scope=native.scope,deadline=deadline)
        cls=type(native.other_connection.connection.driver_connection)
        real_cancel=cls.cancel_safe;real_close=cls.close
        task=None;job=None
        try:
            def broken_cancel(connection,*args,**kwargs):
                if connection is native.driver and threading.current_thread() is not threading.main_thread():
                    faults.append(time.monotonic())
                    raise RuntimeError('Injected owned off-loop cancellation request failure')
                return real_cancel(connection,*args,**kwargs)
            def measured_close(connection,*args,**kwargs):
                result=real_close(connection,*args,**kwargs)
                if connection is native.driver and connection.closed:
                    measurements.setdefault('physical_close',time.monotonic())
                return result
            monkeypatch.setattr(cls,'cancel_safe',broken_cancel)
            monkeypatch.setattr(cls,'close',measured_close)
            task=asyncio.create_task(request(client,'POST',ROUTE,body))
            task.add_done_callback(lambda _:measurements.setdefault('http_return',time.monotonic()))
            observed=False
            for _ in range(200):
                if native.entered.is_set() and await asyncio.to_thread(native.active):
                    observed=True;break
                if native.returned.is_set():break
                await asyncio.sleep(.005)
            assert observed,'Own real query was not observed active before its original deadline'
            job=application.state.summary_jobs[body['job_id']]
            assert not job.settled and not native.driver.closed
            # Cancel the real owner immediately; signed HTTP handling can otherwise
            # consume the remaining window before the off-loop monitor is exercised.
            job.sql.cancel()
            while not faults and not native.returned.is_set() and time.time()<deadline:
                await asyncio.sleep(.001)
            control={'v':2,'scope':native.scope,'boot_id':body['boot_id'],'input_hash':body['input_hash']}
            response=await request(client,'POST',ROUTE+'/'+body['job_id']+'/cancel',control)
            measurements['cancel_http_return']=time.monotonic()
            assert response.status_code in [200,202]
            if response.json()['settled']:assert native.driver.closed and native.returned.is_set()
            await native.wait_closed(1.5)
            native.verify_closed()
            assert faults,'The owned off-loop cancel failure was not exercised'
            assert native.code=='57014'
            assert native.query_seconds<3
            await asyncio.gather(task,return_exceptions=True)
            await wait_settled(job)
            assert job.settled and (job.pending is None or job.pending.done())
            assert native.driver.closed and summary_session[2]==[]
            assert application.state.chat_database.engine is native.engine
            native.verify_main()
            assert not rescue_used
        finally:
            if native.driver is not None and not native.driver.closed and not native.returned.is_set():
                rescue_used=True
                if real_cancel is None:native.driver.cancel_safe(timeout=1)
                else:real_cancel(native.driver,timeout=1)
            if task is not None:await asyncio.gather(task,return_exceptions=True)
            if job is not None:
                if job.task is not None:await asyncio.gather(job.task,return_exceptions=True)
                if job.pending is not None:await asyncio.gather(job.pending,return_exceptions=True)
            await asyncio.sleep(0)
            data={'deadline_window_seconds':.35,'query_seconds':native.query_seconds,
                  'off_loop_cancel_failures':len(faults),'rescue_used':rescue_used,
                  'sqlstate':native.code,'physical_closed':bool(native.driver and native.driver.closed)}
            for key in ['http_return','cancel_http_return','query_return','physical_close']:
                data[key+'_elapsed_seconds']=None if key not in measurements else measurements[key]-started
            data['cleanup_after_query_seconds']=None if not all(k in measurements for k in ['physical_close','query_return']) else measurements['physical_close']-measurements['query_return']
            print('SQL_CANCEL_FAILURE_MEASUREMENTS='+__import__('json').dumps(data,sort_keys=True))
    exercise(summary_session,scenario)


def test_http_timeout_does_not_acknowledge_pending_sql_cleanup(summary_session,monkeypatch):
    from app.core.summary_sql import SummarySQL
    entered=threading.Event();release=threading.Event()
    original=SummarySQL.close

    def held_close(owner):
        original(owner)
        entered.set()
        assert release.wait(3), 'Test did not release completed SQL cleanup'

    monkeypatch.setattr(SummarySQL,'close',held_close)

    async def scenario(client,application):
        body=envelope(summary_session,deadline=time.time()+.5)
        task=asyncio.create_task(request(client,'POST',ROUTE,body))
        job=None
        try:
            response=await asyncio.wait_for(asyncio.shield(task),2)
            job=application.state.summary_jobs[body['job_id']]
            assert entered.is_set() and job.sql.closed
            assert response.status_code==504 and response.json()['settled'] is False
            assert not job.settled and not job.task.done()
            assert job.pending is not None and not job.pending.done()
            control={'v':2,'scope':body['scope'],'boot_id':body['boot_id'],'input_hash':body['input_hash']}
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
            assert status.status_code==200 and status.json()['settled'] is False
            release.set()
            await wait_settled(job)
            status=await request(client,'GET',ROUTE+'/'+body['job_id'],control)
            assert status.status_code==200 and status.json()['settled'] is True
            assert status.json()['state']=='failed' and 'output' not in status.json()
            assert job.task.done() and not job.task.cancelled()
        finally:
            release.set()
            await asyncio.gather(task,return_exceptions=True)
            if job is not None:await asyncio.gather(job.task,return_exceptions=True)

    exercise(summary_session,scenario)
