"""JUP-086 fixtures: source schema, real SQL, synthetic identities only."""
import importlib
import inspect
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import StaticPool

from app.db.database import Database


def rows(database, table):
    assert table in {"users", "user_tenants", "tenants", "jobs", "conversations", "messages"}
    with database.engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(f"SELECT * FROM {table} ORDER BY 1")).mappings()]


def required_scope(method, **scope):
    missing = set(scope) - set(inspect.signature(method).parameters)
    assert not missing, f"Required scope missing from {method.__name__}: {sorted(missing)}"
    return scope


@pytest.fixture(scope="module")
def tenant_cockroach_database():
    raw = os.environ.get("JUP086_COCKROACH_TEST_URL")
    if not raw:
        pytest.skip("JUP086_COCKROACH_TEST_URL absent: real isolated CockroachDB not exercised")
    url = make_url(raw)
    assert url.drivername == "cockroachdb+psycopg"
    assert url.host in {"127.0.0.1", "localhost"} and url.port not in {None, 26257, 5432}
    assert url.port is not None and 1024 <= url.port <= 65535
    assert url.database == "defaultdb" and url.username == "root" and url.password is None
    assert dict(url.query) == {"sslmode": "disable"}
    admin = create_engine(url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5})
    name = None
    engine = None
    try:
        with admin.connect() as connection:
            assert "CockroachDB" in connection.execute(text("SELECT version()")).scalar_one()
            assert connection.execute(text("SHOW CLUSTER SETTING cluster.organization")).scalar_one() == "processor-integration-tests"
            assert set(connection.execute(text("SHOW DATABASES")).scalars()) == {"defaultdb", "postgres", "system"}
            for existing in ("defaultdb", "postgres"):
                assert not connection.execute(text(
                    f"SELECT table_name FROM {existing}.information_schema.tables "
                    "WHERE table_schema NOT IN ('pg_catalog','information_schema','crdb_internal') "
                    "AND table_type <> 'SYSTEM VIEW'"
                )).all()
            candidate = "jup086_backend_" + uuid4().hex
            connection.execute(text(f'CREATE DATABASE "{candidate}"'))
            name = candidate
        engine = create_engine(url.set(database=name))
        database = Database.__new__(Database)
        database.engine = engine
        database.test_owned_name = name
        with engine.begin() as connection:
            importlib.import_module("app.db.migrations.001_initial").upgrade(connection)
        yield database
    finally:
        if engine is not None:
            engine.dispose()
        try:
            if name is not None:
                with admin.connect() as connection:
                    connection.execute(text(f'DROP DATABASE "{name}" CASCADE'))
        finally:
            admin.dispose()


def clean_owned_database(database):
    assert database.engine.url.database == database.test_owned_name
    assert database.test_owned_name.startswith("jup086_backend_")
    with database.engine.begin() as connection:
        for table in ("messages", "conversations", "jobs", "user_tenants", "users", "tenants"):
            connection.execute(text(f"DELETE FROM {table}"))


@pytest.fixture(params=["sqlite", "cockroach"])
def tenant_database(request):
    if request.param == "cockroach":
        database = request.getfixturevalue("tenant_cockroach_database")
        clean_owned_database(database)
        try:
            yield database
        finally:
            clean_owned_database(database)
        return
    database = Database.__new__(Database)
    database.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    try:
        with database.engine.begin() as connection:
            importlib.import_module("app.db.migrations.001_initial").upgrade(connection)
        yield database
    finally:
        database.dispose()


@pytest.fixture
def populated_database(tenant_database):
    from app.core.security import hash_password

    now = datetime.now(timezone.utc)
    with tenant_database.engine.begin() as connection:
        for tenant in ("tenant-a", "tenant-b"):
            connection.execute(text("INSERT INTO tenants VALUES (:id, :id, :id, 'test')"), {"id": tenant})
        for user in ("alice", "bob", "other-a", "multi", "admin-alone"):
            connection.execute(text("INSERT INTO users VALUES (:id, :email, :password, :id, :role, :now)"), {
                "id": user, "email": user + "@example.com", "password": hash_password("test-password"),
                "role": "admin" if user == "admin-alone" else "member", "now": now,
            })
        for user, tenant in (("alice", "tenant-a"), ("bob", "tenant-b"), ("other-a", "tenant-a"), ("multi", "tenant-a"), ("multi", "tenant-b")):
            connection.execute(text("INSERT INTO user_tenants VALUES (:user, :tenant, 'member', :now)"), {"user": user, "tenant": tenant, "now": now})
        for identifier, tenant, owner in (("own", "tenant-a", "alice"), ("foreign-marker", "tenant-b", "bob"), ("other-owner", "tenant-a", "other-a"), ("multi-b", "tenant-b", "multi")):
            connection.execute(text("INSERT INTO conversations VALUES (:id, :tenant, :owner, :id, :now, :now)"), {"id": identifier, "tenant": tenant, "owner": owner, "now": now})
    return tenant_database
