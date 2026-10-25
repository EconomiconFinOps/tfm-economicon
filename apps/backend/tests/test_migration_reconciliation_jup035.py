"""Converge both published 002 branches without rewriting their ledger/data."""
import importlib
import json
from pathlib import Path
import pytest
from sqlalchemy import create_engine, event, text, inspect
from app.db.migration_runner import MigrationRunner

DIRECTORY = Path(importlib.import_module('app.db.migrations').__file__).parent

@pytest.fixture
def engine(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'reconcile.db'))
    event.listen(engine, 'before_cursor_execute', lambda c, cursor, sql, args, context, many:
                 (sql.replace('DEFAULT now()', 'DEFAULT CURRENT_TIMESTAMP'), args), retval=True)
    with engine.begin() as c:
        c.execute(text('CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)'))
    yield engine
    engine.dispose()

@pytest.mark.parametrize('branch', ['fresh', 'anomaly', 'chat', 'chat_current'])
def test_both_002_histories_converge_preserving_ledger_and_data(engine, tmp_path, branch):
    if branch != 'fresh':
        old = tmp_path / 'old'; old.mkdir()
        names = ['001_initial.py', '002_anomaly_episodes.py' if branch == 'anomaly' else '002_chat_operations.py']
        if branch == 'chat_current': names += ['003_dialogue_history.py','004_dialogue_compaction.py']
        for name in names: (old / name).touch()
        MigrationRunner(engine, 'app.db.migrations', old).run()
        with engine.begin() as c:
            c.execute(text("INSERT INTO tenants VALUES ('preserved','Preserved','preserved','test')"))
        if branch in ('anomaly', 'chat_current'): seed_payload(engine, branch)
        with engine.connect() as c:
            payload_before = snapshot_payload(c, branch)
            before = c.execute(text('SELECT version,applied_at FROM schema_migrations ORDER BY version')).all()
    runner = MigrationRunner(engine, 'app.db.migrations', DIRECTORY)
    runner.run(); runner.verify(); runner.run(); runner.verify()
    with engine.connect() as c:
        assert c.execute(text('SELECT version FROM schema_migrations ORDER BY version')).scalars().all() == ['001','002','003','004','005','006']
        assert {'chat_operations','anomaly_episodes','anomaly_detection_state'} <= set(inspect(c).get_table_names())
        if branch != 'fresh':
            assert c.execute(text("SELECT version,applied_at FROM schema_migrations WHERE version != '005' ORDER BY version")).all()[:len(before)] == before
            assert snapshot_payload(c, branch) == payload_before
            assert c.execute(text("SELECT name FROM tenants WHERE id='preserved'")).scalar_one() == 'Preserved'


def test_other_duplicate_ids_fail_before_database_mutation(engine, tmp_path):
    directory = tmp_path / 'duplicate'; directory.mkdir()
    for name in ('001_initial.py', '001_unknown.py'): (directory / name).touch()
    with pytest.raises(RuntimeError, match='Duplicate'):
        MigrationRunner(engine, 'app.db.migrations', directory).run()
    with engine.connect() as c:
        assert inspect(c).get_table_names() == ['schema_migrations']


def test_partial_ddl_resumes_and_verify_never_repairs(engine, tmp_path):
    from app.core.runtime_secrets import StartupError
    old = tmp_path / 'initial'; old.mkdir(); (old / '001_initial.py').touch()
    MigrationRunner(engine, 'app.db.migrations', old).run()
    anomaly = importlib.import_module('app.db.migrations.002_anomaly_episodes')
    with engine.begin() as c:
        c.execute(text(anomaly.schema_steps()[0]))
    runner = MigrationRunner(engine, 'app.db.migrations', DIRECTORY)
    with pytest.raises(StartupError): runner.verify()
    with engine.connect() as c:
        assert not inspect(c).has_table('chat_operations')
        assert c.execute(text('SELECT version FROM schema_migrations')).scalars().all() == ['001']
    runner.run(); runner.verify()


def test_incompatible_existing_table_does_not_mark_reconciled(engine, tmp_path):
    old = tmp_path / 'initial'; old.mkdir(); (old / '001_initial.py').touch()
    MigrationRunner(engine, 'app.db.migrations', old).run()
    with engine.begin() as c:
        c.execute(text('CREATE TABLE anomaly_episodes (id STRING PRIMARY KEY)'))
    with pytest.raises(RuntimeError, match='Incompatible anomaly'):
        MigrationRunner(engine, 'app.db.migrations', DIRECTORY).run()
    with engine.connect() as c:
        assert '005' not in c.execute(text('SELECT version FROM schema_migrations')).scalars().all()


def seed_payload(engine, branch):
    with engine.begin() as c:
        if branch == 'anomaly':
            c.execute(text("INSERT INTO anomaly_detection_state VALUES ('preserved','2026-09-20','rules-original','2026-10-13T00:00:00Z')"))
            c.execute(text("""INSERT INTO anomaly_episodes
                (id,tenant_id,currency,service_key,start_date,last_seen_date,observation,
                 reference_week_cost,opening_observed_cost,impact_numerator,impact_day_count,
                 impact_through_date,severity,status,rules_version,rules,created_at,updated_at)
                VALUES ('episode','preserved','EUR','Compute','2026-09-19','2026-09-20','observed',
                 700.123,200.456,100.333,2,'2026-09-20','P2','investigating','original',
                 '{"threshold":"19.123456789"}','2026-10-13T00:00:00Z','2026-10-13T00:00:00Z')"""))
        else:
            from test_chat_history_document_jup035 import document
            value = document(); value['identity'] = {'tenant_id':'preserved','user_id':'u','conversation_id':'c'}
            c.execute(text("INSERT INTO users VALUES ('u','u@test.invalid','synthetic','User','member','2026-10-13T00:00:00Z')"))
            c.execute(text("""INSERT INTO conversations
                (id,tenant_id,user_id,title,created_at,updated_at,dialogue_history,dialogue_summary,dialogue_compaction)
                VALUES ('c','preserved','u','Kept','2026-10-13T00:00:00Z','2026-10-13T00:00:00Z',
                :history,:summary,:compaction)"""), {'history':json.dumps(value),
                'summary':json.dumps({'text':'Exact summary é','amount':'0.123456789012345'}),
                'compaction':json.dumps({'state':'completed','original':'preserved'})})


def snapshot_payload(connection, branch):
    if branch == 'anomaly':
        return [connection.execute(text('SELECT * FROM '+table+' ORDER BY 1')).all()
                for table in ('anomaly_episodes','anomaly_detection_state')]
    if branch == 'chat_current':
        return connection.execute(text('SELECT id,CAST(dialogue_history AS TEXT),CAST(dialogue_summary AS TEXT),'
            'CAST(dialogue_compaction AS TEXT) FROM conversations ORDER BY id')).all()
    return []
