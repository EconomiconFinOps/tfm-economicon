"""JUP-086 source-schema SQL fixtures, with explicit disposable-service opt-ins."""
import importlib
import importlib.util
import inspect
import json
import os
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

from app.db.database import Database


def required_scope(method, **scope):
    missing = set(scope) - set(inspect.signature(method).parameters)
    assert not missing, f"Required scope missing from {method.__name__}: {sorted(missing)}"
    return scope


def snapshot(database, *tables):
    allowed = {"jobs", "azure_cost_ingestion_runs", "azure_cost_records", "knowledge_documents", "document_chunks", "chunk_embeddings"}
    with database.engine.connect() as connection:
        result = []
        for table in tables:
            assert table in allowed
            result.append([dict(row) for row in connection.execute(text(f"SELECT * FROM {table} ORDER BY id")).mappings()])
        return result


def backend_schema(connection):
    path = Path(__file__).resolve().parents[2] / "backend/app/db/migrations/001_initial.py"
    spec = importlib.util.spec_from_file_location("jup086_backend_schema", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.upgrade(connection)


@pytest.fixture(scope="module")
def cockroach_isolation_database(request):
    if not os.environ.get("PROCESSOR_COCKROACH_TEST_URL"):
        pytest.skip("PROCESSOR_COCKROACH_TEST_URL absent: real isolated CockroachDB not exercised")
    factory = request.getfixturevalue("database_factory")
    with factory() as database:
        database.test_owned_name = database.engine.url.database
        database.initialize()
        with database.engine.begin() as connection:
            backend_schema(connection)
        yield database


def clean_owned_database(database):
    assert database.engine.url.database == database.test_owned_name
    assert database.test_owned_name.startswith("processor_test_")
    with database.engine.begin() as connection:
        for table in ("azure_cost_records", "azure_cost_ingestion_runs", "messages", "conversations", "jobs", "user_tenants", "users", "tenants"):
            connection.execute(text(f"DELETE FROM {table}"))


@pytest.fixture(params=["sqlite", "cockroach"])
def isolation_database(request, monkeypatch):
    if request.param == "cockroach":
        database = request.getfixturevalue("cockroach_isolation_database")
        clean_owned_database(database)
        try:
            yield database
        finally:
            clean_owned_database(database)
        return
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    monkeypatch.setitem(sqlite3.adapters, (Decimal, sqlite3.PrepareProtocol), str)
    database = Database.__new__(Database)
    database.engine = engine
    try:
        with engine.begin() as connection:
            backend_schema(connection)
            importlib.import_module("app.db.migrations.002_azure_cost_ingestion").upgrade(connection)
            # SQLite is only a fast predicate/transaction test; real migration
            # 003/004 execution remains in the CockroachDB parameter above.
            columns = {name: "TEXT" for name in ("billing_account_id", "subscription_name", "resource_group", "service_name", "resource_id", "resource_name", "project", "consumed_unit", "tags", "resource_group_conflicts")}
            columns["consumed_quantity"] = "NUMERIC"
            for name, kind in columns.items():
                connection.execute(text(f"ALTER TABLE azure_cost_records ADD COLUMN {name} {kind}"))
        yield database
    finally:
        engine.dispose()


def seed_job(database, *, identifier="job-a", tenant="tenant-a", creator="alice", status="queued"):
    now = datetime.now(timezone.utc)
    payload = {"tenant_id": tenant, "source": "report", "artifact_uri": "corpus://own", "text_content": "Persisted content for " + identifier, "metadata": {"title": "Report"}}
    job = {"id": identifier, "tenant_id": tenant, "created_by": creator, "source": "report", "artifact_uri": "corpus://own", "payload": payload, "status": status, "request_id": "req-jup086-safe"}
    with database.engine.begin() as connection:
        connection.execute(text("INSERT INTO users VALUES (:id, :email, 'test-hash', :id, 'member', :now) ON CONFLICT DO NOTHING"), {"id": creator, "email": creator + "@example.com", "now": now})
        connection.execute(text("INSERT INTO tenants VALUES (:id, :id, :id, 'test') ON CONFLICT DO NOTHING"), {"id": tenant})
        connection.execute(text("INSERT INTO user_tenants VALUES (:user, :tenant, 'member', :now) ON CONFLICT DO NOTHING"), {"user": creator, "tenant": tenant, "now": now})
        connection.execute(text("INSERT INTO jobs VALUES (:id, :tenant_id, :created_by, :source, :artifact_uri, :payload, :status, :result, :now, :now)"), {**job, "payload": json.dumps(payload), "result": json.dumps({"sentinel": "original-result"}) if status == "completed" else None, "now": now})
    return job
