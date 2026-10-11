"""Real isolated Cockroach24.1.11 contracts; IA is never called here.

Fixtures create only new JUP035 databases/rows and retain them for inspection.
Native forced SQLSTATE tests prove translation, not a post-COMMIT network loss.
"""
import importlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine,text,inspect,event
from sqlalchemy.exc import IntegrityError
from app.db.chat_repository import ChatError,ChatRepository
from app.db.migration_runner import MigrationRunner
from test_chat_operations_jup035 import ANSWER


MIGRATION=importlib.import_module('app.db.migrations.002_chat_operations')
DIRECTORY=Path(importlib.import_module('app.db.migrations').__file__).parent


@pytest.fixture(scope='module')
def sql():
    url=os.getenv('JUP035_COCKROACH_TEST_URL')
    if not url: pytest.skip('Requires exclusive JUP035 Cockroach test database')
    engine=create_engine(url)
    assert engine.url.database.startswith('economicon_jup035_mock')
    with engine.connect() as connection:
        assert 'v24.1.11' in connection.execute(text('SELECT version()')).scalar_one()
    MigrationRunner(engine,'app.db.migrations',DIRECTORY).run()
    yield engine
    engine.dispose()


def new_database(sql,tmp_path):
    name='economicon_jup035_mock_contract_'+uuid4().hex
    with sql.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
        connection.execute(text('CREATE DATABASE '+name))
    engine=create_engine(sql.url.set(database=name))
    initial_dir=tmp_path/name
    initial_dir.mkdir()
    (initial_dir/'001_initial.py').touch()
    MigrationRunner(engine,'app.db.migrations',initial_dir).run()
    print('Retained isolated database:',name)
    return engine


def owned_scope(engine):
    suffix=uuid4().hex
    scope={'tenant_id':'t-'+suffix,'user_id':'u-'+suffix,'conversation_id':'c-'+suffix}
    now=datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO tenants VALUES (:tenant_id,'Synthetic',:tenant_id,'test')"),scope)
        connection.execute(text("INSERT INTO users VALUES (:user_id,:email,'synthetic',:user_id,'member',:now)"),{**scope,'email':suffix+'@example.com','now':now})
        connection.execute(text("INSERT INTO user_tenants VALUES (:user_id,:tenant_id,'member',:now)"),{**scope,'now':now})
        if 'dialogue_history' in {column['name'] for column in inspect(connection).get_columns('conversations')}:
            history={'schema_version':1,'identity':dict(scope),'revision':0,'next_ordinal':0,'messages':[]}
            connection.execute(text("INSERT INTO conversations (id,tenant_id,user_id,title,created_at,updated_at,dialogue_history) VALUES (:conversation_id,:tenant_id,:user_id,'Synthetic',:now,:now,:history)"),{**scope,'now':now,'history':json.dumps(history)})
        else:
            # Explicit pre-003 migration fixtures retain their original schema.
            connection.execute(text("INSERT INTO conversations (id,tenant_id,user_id,title,created_at,updated_at) VALUES (:conversation_id,:tenant_id,:user_id,'Synthetic',:now,:now)"),{**scope,'now':now})
    return scope


def request():
    return {'request_id':str(uuid4()),'content':'Pregunta sintética','screen_context':{}}


def repository(sql):
    return ChatRepository(SimpleNamespace(engine=sql))


def count_messages(sql,scope):
    with sql.connect() as connection:
        value=connection.execute(text('SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id=:conversation_id AND tenant_id=:tenant_id AND user_id=:user_id'),scope).scalar_one()
        return len(json.loads(value)['messages'])


@pytest.mark.parametrize('incompatibility',['json_type','attempt_check','intent_unique','open_predicate','wait_predicate'])
def test_migration_rejects_incompatible_catalog_instead_of_accepting_names(sql,tmp_path,incompatibility):
    engine=new_database(sql,tmp_path)
    statements=MIGRATION.schema_steps()
    statement=statements[0]
    if incompatibility=='json_type': statement=statement.replace('canonical_input JSONB NOT NULL','canonical_input STRING NOT NULL')
    if incompatibility=='attempt_check': statement=statement.replace('CHECK(attempt_count BETWEEN 0 AND 4)','CHECK(attempt_count BETWEEN 0 AND 9)')
    if incompatibility=='intent_unique': statement=statement.replace('UNIQUE(tenant_id,user_id,conversation_id,client_request_id)','UNIQUE(tenant_id,user_id,conversation_id,question_message_id)')
    try:
        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            connection.execute(text(statement))
            index=0
            if incompatibility=='open_predicate':
                connection.execute(text(statements[1]+' OR TRUE'))
                index=1
            if incompatibility=='wait_predicate':
                connection.execute(text(statements[2]+" OR state='failed'"))
                index=2
            with pytest.raises(RuntimeError,match='Incompatible'):
                MIGRATION.step_applied(connection,index)
            assert connection.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='002'")).scalar_one()==0
    finally: engine.dispose()


def test_interrupted_additive_ddl_resumes_and_preserves_legacy_pair_json(sql,tmp_path):
    engine=new_database(sql,tmp_path)
    try:
        scope=owned_scope(engine)
        now=datetime.now(timezone.utc)
        with engine.begin() as connection:
            for role in ['user','assistant']:
                connection.execute(text('INSERT INTO messages VALUES (:id,:conversation_id,:tenant_id,:user_id,:role,:content,:metadata,:now)'),{**scope,'id':str(uuid4()),'role':role,'content':'Legacy '+role,'metadata':json.dumps({'legacy':True,'amount':'123.4500'}),'now':now})
        def history():
            with engine.connect() as connection:
                return [dict(row) for row in connection.execute(text('SELECT id,role,content,metadata,created_at FROM messages ORDER BY id')).mappings()]
        before=history()
        for statement in MIGRATION.schema_steps()[:2]:
            with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection: connection.execute(text(statement))
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='002'")).scalar_one()==0
        MigrationRunner(engine,'app.db.migrations',DIRECTORY).run()
        with engine.connect() as connection:
            MIGRATION.verify(connection)
            assert connection.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='002'")).scalar_one()==1
            assert connection.execute(text('SELECT dialogue_summary FROM conversations')).scalar_one() is None
        assert history()==before
    finally: engine.dispose()


def test_real_concurrent_same_intent_has_one_operation_no_visible_pair(sql):
    scope=owned_scope(sql);payload=request();repo=repository(sql);barrier=Barrier(2)
    def reserve():
        barrier.wait(timeout=5)
        return repo.reserve(scope,payload,{'prompt_version':'synthetic'})
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(reserve) for _ in range(2)]
        rows=[future.result(timeout=10) for future in futures]
    assert rows[0][0]['operation_id']==rows[1][0]['operation_id']
    assert sorted(row[1] for row in rows)==[False,True]
    assert all(row[0]['attempt_count']==0 for row in rows)
    assert count_messages(sql,scope)==0
    with pytest.raises(ChatError) as conflict: repo.reserve(scope,{**payload,'content':'Changed'}, {})
    assert (conflict.value.status,conflict.value.code)==(409,'intent_conflict')
    with pytest.raises(ChatError) as busy: repo.reserve(scope,request(),{})
    assert (busy.value.status,busy.value.code)==(409,'conversation_busy')


@pytest.mark.parametrize('constraint',['intent','open_operation'])
def test_native_unique_constraints_report_sqlstate23505(sql,constraint):
    scope=owned_scope(sql);repo=repository(sql)
    row,_=repo.reserve(scope,request(),{'prompt_version':'synthetic'})
    columns=['operation_id','tenant_id','user_id','conversation_id','client_request_id','question_message_id','question_content','canonical_input','input_hash','state','revision','attempt_count','current_attempt_id','attempt_deadline','retry_at','attempts','private_control','result_message_id','created_at','updated_at']
    selection=[(':copy_id' if col=='operation_id' else ':request_id' if col=='client_request_id' else col) for col in columns]
    with pytest.raises(IntegrityError) as failure:
        with sql.begin() as connection:
            connection.execute(text('INSERT INTO chat_operations ('+','.join(columns)+') SELECT '+','.join(selection)+' FROM chat_operations WHERE operation_id=:original'),{'copy_id':str(uuid4()),'request_id':row['client_request_id'] if constraint=='intent' else str(uuid4()),'original':row['operation_id']})
    assert failure.value.orig.sqlstate=='23505'
    assert repo.get(scope,row['operation_id'])['attempt_count']==0
    assert count_messages(sql,scope)==0


def test_atomic_pair_rolls_back_real_unique_failure_and_late_stop_fence(sql):
    scope=owned_scope(sql);repo=repository(sql)
    row,_=repo.reserve(scope,request(),{'prompt_version':'synthetic'})
    active,won=repo.claim(scope,row['operation_id'],'synthetic-boot')
    assert won and active['attempt_count']==1
    result_id=str(uuid4())
    def real_constraint_failure(connection,cursor,statement,parameters,context,many):
        if statement.startswith('UPDATE chat_operations SET') and context.compiled_parameters[0].get('state')=='completed':
            # A real native PK violation after the document write proves the
            # same transaction rolls back both canonical history and completion.
            connection.execute(text('INSERT INTO chat_operations SELECT * FROM chat_operations WHERE operation_id=:id'),{'id':row['operation_id']})
    event.listen(sql,'before_cursor_execute',real_constraint_failure)
    try:
        with pytest.raises(ChatError) as persistence:
            repo.complete(scope,row['operation_id'],active['current_attempt_id'],ANSWER,{},result_id)
    finally:
        event.remove(sql,'before_cursor_execute',real_constraint_failure)
    assert persistence.value.status==503 and count_messages(sql,scope)==0
    stopped=repo.stop(scope,row['operation_id'])
    assert stopped['state']=='cancelled'
    with pytest.raises(ChatError) as late:
        repo.complete(scope,row['operation_id'],active['current_attempt_id'],ANSWER,{},str(uuid4()))
    assert late.value.status==409 and count_messages(sql,scope)==0


@pytest.mark.parametrize('code',['40001','40003'])
def test_native_forced_sqlstate_translation_is_not_ambiguous_commit_acceptance(sql,code):
    scope=owned_scope(sql);repo=repository(sql);calls=[]
    def action(connection):
        calls.append(True)
        if len(calls)==1:
            connection.execute(text("SELECT crdb_internal.force_error(:code,'synthetic-contract-error')"),{'code':code})
        return connection.execute(text('SELECT 1')).scalar_one()
    if code=='40001':
        assert repo._transaction(scope,action)==1 and len(calls)==2
    else:
        with pytest.raises(ChatError) as failure: repo._transaction(scope,action)
        assert (failure.value.status,failure.value.code)==(503,'commit_unknown')
        assert len(calls)==1


def test_history_003_native_precision_checkpoint_and_read_source(sql, tmp_path):
    """Real JSONB text/Decimal, TIMESTAMPTZ, restart and frozen-source proof."""
    from decimal import Decimal
    from app.db.database import Database
    history_module = importlib.import_module('app.db.migrations.003_dialogue_history')
    engine = new_database(sql, tmp_path)
    try:
        scope = owned_scope(engine)
        legacy_directory = tmp_path/'history-legacy-index'
        legacy_directory.mkdir()
        for name in ('001_initial.py', '002_chat_operations.py'):
            (legacy_directory/name).touch()
        MigrationRunner(engine, 'app.db.migrations', legacy_directory).run()
        metadata = '{"amount":12345678901234567890.12345678901234567890123456789,"large":9007199254740993,"negative":-0.00000000000000000000001,"citation":{"id":"évidence-😀"}}'
        with engine.begin() as c:
            c.execute(text("INSERT INTO messages (id,conversation_id,tenant_id,user_id,role,content,metadata,created_at) VALUES ('z-question',:conversation_id,:tenant_id,:user_id,'user','  exacto é 😀\n',:metadata,:stamp)"),
                {**scope, 'metadata': metadata, 'stamp': '2026-10-10T04:12:00.123456+01:00'})
            c.execute(text("INSERT INTO messages (id,conversation_id,tenant_id,user_id,role,content,metadata,created_at) VALUES ('a-answer',:conversation_id,:tenant_id,NULL,'assistant','Completa',:metadata,:stamp)"),
                {**scope, 'metadata': '{"generation":{"question_message_id":"z-question"}}', 'stamp': '2026-10-10T03:12:00.123456Z'})
        def originals():
            with engine.connect() as c:
                return [dict(row) for row in c.execute(text('SELECT id,role,content,user_id,CAST(metadata AS TEXT) AS metadata,created_at FROM messages ORDER BY id')).mappings()]
        before = originals()
        with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as c:
            c.execute(text(history_module.schema_steps()[0]))
        history_module.backfill(engine)
        with engine.connect() as c:
            raw = c.execute(text('SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id=:conversation_id'), scope).scalar_one()
            assert c.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='003'")).scalar_one() == 0
        value = json.loads(raw, parse_float=Decimal)
        assert [m['id'] for m in value['messages']] == ['z-question', 'a-answer']
        question, answer = value['messages']
        assert question['created_at'] == '2026-10-10T03:12:00.123456Z'
        assert question['content'] == '  exacto é 😀\n'
        assert question['metadata']['amount'] == Decimal('12345678901234567890.12345678901234567890123456789')
        assert question['metadata']['negative'] == Decimal('-0.00000000000000000000001')
        assert question['metadata']['large'] == 9007199254740993
        assert answer['author_id'] is None and answer['question_id'] == 'z-question'
        assert value['migration']['source_count'] == 2
        MigrationRunner(engine, 'app.db.migrations', DIRECTORY).run()
        assert originals() == before
        with engine.connect() as c:
            assert c.execute(text('SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id=:conversation_id'), scope).scalar_one() == raw
        db = Database.__new__(Database)
        db.engine = engine
        statements = []
        from sqlalchemy import event
        event.listen(engine, 'before_cursor_execute',
            lambda c, cursor, statement, args, context, many: statements.append(statement))
        assert [m['id'] for m in db.fetch_messages(**scope)] == ['z-question', 'a-answer']
        MigrationRunner(engine, 'app.db.migrations', DIRECTORY).verify()
        assert not any('FROM messages' in statement or 'JOIN messages' in statement for statement in statements)
    finally: engine.dispose()


def test_history_003_native_inconsistent_source_is_retained_without_version(sql, tmp_path):
    engine = new_database(sql, tmp_path)
    try:
        scope = owned_scope(engine)
        with engine.begin() as c:
            c.execute(text("INSERT INTO messages (id,conversation_id,tenant_id,user_id,role,content,metadata,created_at) VALUES ('bad',:conversation_id,'foreign',:user_id,'user','original',NULL,:now)"),
                {**scope, 'now': datetime.now(timezone.utc)})
        with pytest.raises(RuntimeError, match='integrity'):
            MigrationRunner(engine, 'app.db.migrations', DIRECTORY).run()
        with engine.connect() as c:
            assert c.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='003'")).scalar_one() == 0
            assert c.execute(text("SELECT content FROM messages WHERE id='bad'")).scalar_one() == 'original'
            assert c.execute(text('SELECT dialogue_history FROM conversations WHERE id=:conversation_id'), scope).scalar_one() is None
    finally: engine.dispose()


class _CommitAckProxy:
    """Own-test PGwire proxy: drop actual COMMIT acknowledgement, never SQL log.

    Connections remain inside the exclusive native fixture. Packet contents are
    forwarded in memory and discarded; the receipt records only frame counts
    and whether the server confirmed COMMIT before the client was disconnected.
    """
    def __init__(self,host,port):
        import socket
        from threading import Event,Thread
        self.socket=socket
        self.Thread=Thread
        self.host,self.port=host,port
        self.stop=Event();self.armed=Event();self.committed=Event()
        self.frames={'client':0,'server':0}
        self.errors=[];self.connections=[];self.threads=[]
        self.listener=socket.socket()
        self.listener.bind(('127.0.0.1',0));self.listener.listen(4)
        self.listener.settimeout(.2)
        self.address=self.listener.getsockname()
        self.thread=Thread(target=self._accept,daemon=True);self.thread.start()

    def _exact(self,socket,count):
        value=bytearray()
        while len(value)<count and not self.stop.is_set():
            try:chunk=socket.recv(count-len(value))
            except self.socket.timeout:continue
            if not chunk:raise EOFError()
            value.extend(chunk)
        if len(value)!=count:raise EOFError()
        return bytes(value)

    def _close(self,*connections):
        for connection in connections:
            try:connection.shutdown(self.socket.SHUT_RDWR)
            except OSError:pass
            try:connection.close()
            except OSError:pass

    def _accept(self):
        from threading import Event
        while not self.stop.is_set():
            try:client,_=self.listener.accept()
            except self.socket.timeout:continue
            except OSError:break
            try:server=self.socket.create_connection((self.host,self.port),timeout=5)
            except OSError:
                self.errors.append('upstream_connect');self._close(client);continue
            client.settimeout(.2);server.settimeout(.2)
            self.connections.extend([client,server])
            pending=Event()
            for direction,source,target in [('client',client,server),('server',server,client)]:
                worker=self.Thread(target=self._forward,args=(direction,source,target,pending),daemon=True)
                self.threads.append(worker);worker.start()

    def _forward(self,direction,source,target,pending):
        import struct
        try:
            if direction=='client':
                header=self._exact(source,4)
                length=struct.unpack('!I',header)[0]
                if not 8<=length<=65536:raise ValueError()
                target.sendall(header+self._exact(source,length-4))
            while not self.stop.is_set():
                kind=self._exact(source,1)
                header=self._exact(source,4)
                length=struct.unpack('!I',header)[0]
                if not 4<=length<=4194304:raise ValueError()
                payload=self._exact(source,length-4)
                self.frames[direction]+=1
                if direction=='client' and self.armed.is_set() and kind in (b'Q',b'P'):
                    query=payload if kind==b'Q' else payload.split(b'\x00',1)[1].split(b'\x00',1)[0]
                    if query.strip(b' \r\n;\x00').upper()==b'COMMIT':pending.set()
                if direction=='server' and pending.is_set() and kind==b'C' and payload==b'COMMIT\x00':
                    self.committed.set();self.armed.clear()
                    self._close(source,target)
                    return
                target.sendall(kind+header+payload)
        except (EOFError,OSError):pass
        except Exception:self.errors.append('invalid_frame')
        finally:self._close(source,target)

    def close(self):
        self.stop.set();self._close(self.listener,*self.connections)
        self.thread.join(2)
        for worker in self.threads:worker.join(2)


def test_native_post_commit_lost_ack_resolves_canonical_final_without_duplicate(sql):
    """Actual server COMMIT + missing TCP ACK, not forced SQLSTATE simulation."""
    scope=owned_scope(sql);direct=repository(sql)
    operation,_=direct.reserve(scope,request(),{'prompt_version':'synthetic'})
    active,won=direct.claim(scope,operation['operation_id'],'synthetic-boot')
    assert won
    proxy=_CommitAckProxy(sql.url.host,sql.url.port or 26257)
    engine=create_engine(sql.url.set(host=proxy.address[0],port=proxy.address[1]),connect_args={'connect_timeout':5,'gssencmode':'disable'})
    result_id=str(uuid4())
    try:
        # Finish dialect initialization/pre-ping before arming the one-shot
        # fault, so it belongs precisely to the finalization transaction.
        with engine.begin() as c:assert c.execute(text('SELECT 1')).scalar_one()==1
        proxy.armed.set()
        proxied=repository(engine)
        with pytest.raises(ChatError) as error:
            proxied.complete(scope,operation['operation_id'],active['current_attempt_id'],ANSWER,{},result_id)
        assert error.value.status==503
        assert proxy.committed.wait(5), 'No server COMMIT acknowledgement was observed'
        assert not proxy.errors,proxy.errors
        known=direct.get(scope,operation['operation_id'])
        assert known['state']=='completed' and known['result_message_id']==result_id and known['attempt_count']==1
        assert direct.result(scope,known)['content']==ANSWER['answer']
        with sql.connect() as c:
            before=c.execute(text('SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id=:conversation_id'),scope).scalar_one()
        value=json.loads(before)
        assert value['revision']==1 and value['next_ordinal']==2
        assert [m['id'] for m in value['messages']]==[operation['question_message_id'],result_id]
        direct.complete(scope,operation['operation_id'],active['current_attempt_id'],ANSWER,{},result_id)
        with sql.connect() as c:
            assert c.execute(text('SELECT CAST(dialogue_history AS TEXT) FROM conversations WHERE id=:conversation_id'),scope).scalar_one()==before
            assert c.execute(text('SELECT COUNT(*) FROM messages WHERE conversation_id=:conversation_id'),scope).scalar_one()==0
        print('Post-COMMIT structural receipt:',json.dumps({'server_commit_seen':proxy.committed.is_set(),
            'ack_dropped':True,'frames':proxy.frames,'canonical_revision':1,'messages':2,'replay_identical':True}))
    finally:engine.dispose();proxy.close()
