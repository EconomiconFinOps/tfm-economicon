"""Opt-in disposable Cockroach probes with migrated synthetic data; no paid IO."""
import asyncio,os,threading,time
from uuid import uuid4
from sqlalchemy import create_engine,event,text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

class Native:
    def __init__(self,engine,scope):
        self.engine=engine;self.inspect_engine=create_engine(engine.url,poolclass=NullPool)
        self.inspector=self.inspect_engine.connect();self.scope=scope
        self.marker='jup035-native-job-'+str(uuid4());self.other_marker='jup035-native-main-'+str(uuid4())
        self.entered=threading.Event();self.returned=threading.Event();self.driver=None;self.code=None;self.query_seconds=0
        self.listener=None;self.fired=False;self.other_connection=None;self.other_thread=None;self.other_returned=threading.Event();self.other_success=False
    def active(self,marker=None):
        return self.inspector.execute(text('SELECT count(*) FROM [SHOW CLUSTER QUERIES] WHERE query LIKE :pattern'),{'pattern':'%'+(marker or self.marker)+'%'}).scalar_one()>0
    def block(self,pattern,seconds=4):
        def before(connection,cursor,statement,params,context,many):
            if self.fired or pattern not in statement:return
            # Durable admission reads history on the principal engine first.
            # Inject only into the job-owned SQL connection measured below.
            if connection.engine in (self.engine,self.inspect_engine):return
            assert isinstance(connection.engine.pool,NullPool)
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
        self.inspector.close();self.inspect_engine.dispose();self.engine.dispose()

import pytest
from test_chat_operations_jup035 import api
from test_chat_summary_lifecycle_jup035 import summary_resources53
from test_chat_summary_scheduler_jup035 import packet,runtime,source
from test_chat_cockroach_jup035 import sql,owned_scope

@pytest.fixture
def native(packet,request):
    # Reuse the opt-in disposable database guard and migrations, never a saved
    # conversation from a developer's smoke environment.
    if not os.getenv('JUP035_COCKROACH_TEST_URL') and os.getenv('JUP035_REQUIRE_NATIVE_SQL')=='true':
        pytest.fail('Required native SQL integration has no JUP035_COCKROACH_TEST_URL')
    sql=request.getfixturevalue('sql')
    scope=owned_scope(sql)
    original=packet[1].engine
    try:
        packet[1].engine=sql
        source(packet,count=8,long=False,scope=scope)
    finally:
        packet[1].engine=original
    value=Native(sql,scope)
    try:yield value
    finally:value.cleanup()

@pytest.mark.parametrize('mode',['deadline','shutdown'])
def test_existing_summary_service_closes_real_owned_sql_before_releasing_reservation(packet,native,monkeypatch,mode):
    old_engine=packet[1].engine;packet[1].engine=native.engine
    main,child=runtime(packet);clock={'now':time.time()};native.block('SELECT CAST(dialogue_history AS TEXT)',4);native.main_control()
    async def scenario():
        closer=None
        try:
            child.on_completed(native.scope,{'manifest':{'variable_tokens':8192}},event_id='native-'+mode)
            await native.wait_active()
            assert child.reserved and main.occupied==1 and not native.driver.closed
            if mode=='deadline':
                from app.core.config import get_settings
                elapsed=get_settings().summary_timeout_seconds+1
                monkeypatch.setattr(time,'time',lambda:clock['now']+elapsed)
            else:closer=asyncio.create_task(main.close())
            await native.wait_closed(1.2)
            native.verify_closed()
            assert native.code=='57014' and native.query_seconds<3,'Native SQL did not stop because of the job deadline/close'
            await child.wait_idle()
            assert not child.reserved and main.occupied==0 and not child.workers and packet[3].calls==[]
            assert main.repository.engine is native.engine,'Summary changed the principal engine'
            native.verify_main()
        finally:
            # Cleanup is distinct from the measured product cancellation.
            if native.driver is not None and not native.driver.closed and not native.returned.is_set():
                native.driver.cancel_safe(timeout=1)
            await main.close()
            if closer is not None:await asyncio.gather(closer,return_exceptions=True)
    try:asyncio.run(scenario())
    finally:packet[1].engine=old_engine

def test_successful_existing_summary_snapshot_closes_only_its_physical_connection(packet,native):
    old_engine=packet[1].engine;packet[1].engine=native.engine;main,child=runtime(packet)
    native.block('SELECT CAST(dialogue_history AS TEXT)',0);native.main_control(.2)
    async def scenario():
        try:
            child.on_completed(native.scope,{'manifest':{'variable_tokens':0}},event_id='native-success')
            await child.wait_idle()
            assert native.entered.is_set() and native.returned.is_set() and native.driver.closed
            assert main.repository.engine is native.engine and not child.reserved and main.occupied==0
            assert packet[3].calls==[]
            native.verify_main()
        finally:await main.close()
    try:asyncio.run(scenario())
    finally:packet[1].engine=old_engine

def test_preparation_after_original_deadline_never_dispatches_and_retains_worker_until_return(packet,monkeypatch):
    import app.services.summary_service as service
    from test_chat_summary_scheduler_jup035 import source,SCOPE
    source(packet,count=8,long=False);main,child=runtime(packet)
    entered=threading.Event();release=threading.Event();returned=threading.Event();real=packet[4].prepare_lot
    def blocked(*args):
        entered.set()
        try:release.wait(3);return real(*args)
        finally:returned.set()
    monkeypatch.setattr(type(packet[4]),'prepare_lot',lambda self,*args:blocked(*args))
    async def scenario():
        try:
            child.on_completed(SCOPE,{'manifest':{'variable_tokens':8192}},event_id='cpu-deadline')
            for _ in range(200):
                if entered.is_set():break
                await asyncio.sleep(.005)
            assert entered.is_set() and child.reserved and child.workers
            from app.core.config import get_settings
            now=time.time();elapsed=get_settings().summary_timeout_seconds+1
            monkeypatch.setattr(time,'time',lambda:now+elapsed)
            await asyncio.sleep(.06)
            assert child.reserved and not returned.is_set() and packet[3].calls==[]
            release.set();await child.wait_idle()
            assert returned.is_set() and not child.reserved and not child.workers and packet[3].calls==[]
        finally:release.set();await main.close()
    asyncio.run(scenario())
