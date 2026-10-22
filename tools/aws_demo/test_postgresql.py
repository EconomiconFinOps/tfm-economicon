"""Opt-in integration against a dedicated disposable PostgreSQL instance.

AWS_POSTGRES_TEST_URL must use loopback, a nonstandard port, and database
economicon_jup131_test. No application database is accepted. Each test creates
and drops only its own randomly named databases; no existing schema is changed.
"""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.environ.get("AWS_POSTGRES_TEST_URL"), "dedicated PostgreSQL opt-in required")
class PostgreSQLApplicationTests(unittest.TestCase):
    def test_complete_schema_and_restart(self):
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url

        url = make_url(os.environ["AWS_POSTGRES_TEST_URL"])
        self.assertEqual(url.drivername, "postgresql+psycopg")
        self.assertIn(url.host, {"localhost", "127.0.0.1", "::1"})
        self.assertIsNotNone(url.port)
        self.assertNotIn(url.port, {5432, 26257})
        self.assertEqual(url.database, "economicon_jup131_test")
        admin = create_engine(url, isolation_level="AUTOCOMMIT")
        created = []
        try:
            with admin.connect() as connection:
                for suffix in ("operational", "vector"):
                    name = f"jup131_{suffix}_{uuid4().hex}"
                    connection.execute(text(f'CREATE DATABASE "{name}"'))
                    created.append(name)
            environment = dict(os.environ,
                RUNTIME_ENVIRONMENT="test", ALLOW_INSECURE_LOCAL_DATABASE="true",
                DATABASE_URL=url.set(database=created[0]).render_as_string(hide_password=False),
                VECTOR_DATABASE_URL=url.set(database=created[1]).render_as_string(hide_password=False),
                RABBITMQ_URL="amqps://unit:synthetic-broker-pass@localhost:5671/%2F",
                AUTH_SECRET_KEY="jup131-synthetic-key-0123456789abcdef",
                DEMO_SEED_ENABLED="true", DEMO_PASSWORD="jup131-disposable-demo-pass",
                EMBEDDING_PROVIDER="mock", EMBEDDING_DIMENSION="8", CHAT_ENABLED="false",
                BACKEND_SCHEMA_MODE="migrate", ECONOMICON_ENV_FILE="")

            def run(app, code):
                result = subprocess.run([sys.executable, "-c", code],
                    cwd=ROOT / "apps" / app,
                    env=dict(environment, PYTHONPATH=str(ROOT / "apps" / app)),
                    capture_output=True, text=True, timeout=90)
                self.assertEqual(result.returncode, 0, f"{app}: {result.stdout}\n{result.stderr}")

            run("backend", """
from app.core.config import get_settings
from app.db.database import Database
from app.db.migration_runner import MigrationRunner
from app.aws_bootstrap_identity import bind_identity
from app.aws_bootstrap_common import BootstrapError
from pathlib import Path
from sqlalchemy import text
d=Database(get_settings().database_url.get_secret_value())
try:
    d.initialize()
    d.initialize()
    MigrationRunner(d.engine,'app.db.migrations',Path('app/db/migrations')).verify()
    assert d.fetch_user_by_email('operator@example.com')['id']=='user-finops-admin'
    assert d.user_has_tenant('user-finops-admin','tenant-core')
    assert not d.user_has_tenant('user-finops-admin','tenant-forbidden')
    with d.engine.connect() as c:
        assert c.execute(text('SELECT count(*) FROM schema_migrations')).scalar_one()==6
        assert c.execute(text('SELECT count(*) FROM users')).scalar_one()==1
    identity={'id':'dd0a7871-d3c3-441f-9c40-d01aee724131','email':'aws-defensa+ensayo1@example.com'}
    bind_identity(d.engine,identity)
    bind_identity(d.engine,identity)
    assert d.user_has_tenant(identity['id'],'tenant-core')
    assert not d.user_has_tenant(identity['id'],'tenant-growth')
    with d.engine.begin() as c:
        c.execute(text("INSERT INTO user_tenants(user_id,tenant_id,role,created_at) VALUES(:id,'tenant-growth','analyst',now())"),identity)
    try:
        bind_identity(d.engine,identity)
    except BootstrapError:
        pass
    else:
        raise AssertionError('Bootstrap accepted a conflicting membership')
    with d.engine.connect() as c:
        assert c.execute(text('SELECT count(*) FROM users')).scalar_one()==2
finally: d.dispose()
""")
            run("processor", """
from app.core.config import get_settings
from app.db.database import Database
from app.vector_store.pgvector_store import PgVectorStore
from sqlalchemy import text
s=get_settings()
d=Database(s.database_url.get_secret_value())
try:
    d.initialize()
    d.initialize()
    with d.engine.connect() as c:
        assert c.execute(text('SELECT count(*) FROM processor_schema_migrations')).scalar_one()>=4
        assert c.execute(text('SELECT count(*) FROM azure_cost_records')).scalar_one()==0
    with d.engine.begin() as c:
        c.execute(text("INSERT INTO azure_cost_ingestion_runs(id,tenant_id,subscription_id,request,status,started_at,completed_at) VALUES ('fixture-run','tenant-core','fixture-sub','{}','completed',now(),now())"))
        c.execute(text("INSERT INTO azure_cost_records(id,ingestion_id,tenant_id,subscription_id,usage_date,pretax_cost,currency,dimensions,source_row_hash,created_at,service_name) VALUES ('fixture-record','fixture-run','tenant-core','fixture-sub','2026-10-01',12.50,'EUR','{}','fixture-hash',now(),'Compute')"))
    v=PgVectorStore(s.vector_database_url.get_secret_value(),embedding_dimension=8)
    try:
        v.initialize()
        v.initialize()
        with v.engine.connect() as c:
            assert c.execute(text('SELECT count(*) FROM knowledge_documents')).scalar_one()==0
    finally: v.engine.dispose()
finally: d.engine.dispose()
""")
            run("backend", """
from app.core.config import get_settings
from app.db.database import Database
from datetime import date
d=Database(get_settings().database_url.get_secret_value())
try:
    period=dict(start_date=date(2026,10,1),end_date=date(2026,10,31),group_by='service')
    allowed=d.fetch_billing_summary('tenant-core',**period)
    assert allowed['totals']==[dict(currency='EUR',cost='12.50',record_count=1)], allowed
    assert d.fetch_billing_summary('tenant-growth',**period)['totals']==[]
finally: d.dispose()
""")
        finally:
            with admin.connect() as connection:
                for name in reversed(created):
                    connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            admin.dispose()


if __name__ == "__main__":
    unittest.main()
