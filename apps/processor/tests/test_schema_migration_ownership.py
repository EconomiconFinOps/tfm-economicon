"""Opt-in: schema ownership between backend and processor on a real CockroachDB.

Uses the disposable node described in test_azure_cost_cockroach_integration.py
(PROCESSOR_COCKROACH_TEST_URL). Each service migrates in its own process, as in
Docker Compose, loading only its migration runner and migrations.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from sqlalchemy import text

from test_azure_cost_cockroach_integration import TEST_URL_ENV, database_factory  # noqa: F401

pytestmark = pytest.mark.skipif(
    not os.environ.get(TEST_URL_ENV),
    reason=f"set {TEST_URL_ENV} to opt in to disposable CockroachDB tests",
)

APPS = Path(__file__).resolve().parents[2]
BACKEND_TABLES = {"tenants", "users", "user_tenants", "jobs", "conversations", "messages"}
PROCESSOR_TABLES = {"azure_cost_ingestion_runs", "azure_cost_records"}
VERSION_TABLES = {"backend": "schema_migrations", "processor": "processor_schema_migrations"}
LEGACY_PROCESSOR_JOBS_DDL = """
    CREATE TABLE IF NOT EXISTS jobs (
        id STRING PRIMARY KEY,
        tenant_id STRING NOT NULL,
        created_by STRING NOT NULL,
        source STRING NOT NULL,
        artifact_uri STRING,
        payload JSONB NOT NULL,
        status STRING NOT NULL,
        result JSONB,
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL
    )
"""
MIGRATE = """
import sys, time
from pathlib import Path
from sqlalchemy import create_engine
from app.db.migration_runner import MigrationRunner
import app.db.migrations as migrations
url, version_table, start_at = sys.argv[1], sys.argv[2], float(sys.argv[3])
engine = create_engine(url)
options = {} if version_table == "schema_migrations" else {"version_table": version_table}
runner = MigrationRunner(engine, "app.db.migrations", Path(migrations.__file__).parent, **options)
while time.time() < start_at:
    time.sleep(0.001)
try:
    runner.run()
finally:
    engine.dispose()
"""


def _expected_versions(service):
    folder = APPS / service / "app" / "db" / "migrations"
    return sorted(path.stem.split("_", 1)[0] for path in folder.glob("[0-9][0-9][0-9]_*.py"))


def _start(service, database, start_at):
    url = database.engine.url.render_as_string(hide_password=False)
    return subprocess.Popen(
        [sys.executable, "-B", "-c", MIGRATE, url, VERSION_TABLES[service], str(start_at)],
        cwd=APPS / service,
        env={**os.environ, "PYTHONPATH": str(APPS / service), "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )


def _migrate(service, database):
    process = _start(service, database, 0)
    output, _ = process.communicate(timeout=300)
    assert process.returncode == 0, f"{service} migration failed:\n{output[-2000:]}"


def _tables(database):
    with database.engine.connect() as connection:
        return set(connection.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )).scalars())


def _versions(database, service):
    with database.engine.connect() as connection:
        return [row[0] for row in connection.execute(
            text(f"SELECT version FROM {VERSION_TABLES[service]} ORDER BY version")
        )]


def _jobs_rows(database):
    with database.engine.connect() as connection:
        return [dict(row) for row in connection.execute(
            text("SELECT id, tenant_id, status, payload FROM jobs ORDER BY id")
        ).mappings()]


def _insert_job(database, job_id):
    with database.engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO jobs (id, tenant_id, created_by, source, payload, status, created_at, updated_at)
            VALUES (:id, 'tenant-a', 'user-a', 'azure', '{"text_content": "x"}', 'queued', now(), now())
        """), {"id": job_id})


def test_processor_alone_creates_no_backend_table(database_factory):
    with database_factory() as database:
        _migrate("processor", database)

        tables = _tables(database)
        assert PROCESSOR_TABLES <= tables
        assert tables & BACKEND_TABLES == set()
        assert _versions(database, "processor") == _expected_versions("processor")


def test_backend_alone_creates_no_processor_table(database_factory):
    with database_factory() as database:
        _migrate("backend", database)

        tables = _tables(database)
        assert BACKEND_TABLES <= tables
        assert tables & PROCESSOR_TABLES == set()
        assert _versions(database, "backend") == _expected_versions("backend")


@pytest.mark.parametrize("offset", [0.0, 0.5], ids=["simultaneous", "offset-0.5s"])
def test_concurrent_cold_start_migrations_both_succeed(database_factory, offset):
    failures = []
    for attempt in range(5):
        with database_factory() as database:
            start_at = time.time() + 8
            processes = {
                "backend": _start("backend", database, start_at),
                "processor": _start("processor", database, start_at + offset),
            }
            outputs = {name: process.communicate(timeout=300)[0] for name, process in processes.items()}
            failed = {name for name, process in processes.items() if process.returncode != 0}
            if failed:
                failures.append((attempt, {name: outputs[name][-600:] for name in failed}))
                continue
            assert _versions(database, "backend") == _expected_versions("backend")
            assert _versions(database, "processor") == _expected_versions("processor")
            assert BACKEND_TABLES | PROCESSOR_TABLES <= _tables(database)

    assert not failures, "\n\n".join(
        f"attempt {attempt}, {name}:\n{output}"
        for attempt, outputs in failures for name, output in outputs.items()
    )


def test_restart_of_fully_migrated_database_changes_nothing(database_factory):
    with database_factory() as database:
        _migrate("backend", database)
        _migrate("processor", database)
        _insert_job(database, "job-existing")
        before = (_tables(database), _versions(database, "backend"),
                  _versions(database, "processor"), _jobs_rows(database))

        _migrate("processor", database)
        _migrate("backend", database)

        assert (_tables(database), _versions(database, "backend"),
                _versions(database, "processor"), _jobs_rows(database)) == before


def test_backend_adopts_jobs_created_by_legacy_processor(database_factory):
    with database_factory() as database:
        _migrate("processor", database)
        with database.engine.begin() as connection:
            connection.execute(text(LEGACY_PROCESSOR_JOBS_DDL))
        _insert_job(database, "job-from-legacy-processor")
        rows = _jobs_rows(database)
        processor_versions = _versions(database, "processor")

        _migrate("backend", database)

        assert _versions(database, "backend") == _expected_versions("backend")
        assert _versions(database, "processor") == processor_versions
        assert _jobs_rows(database) == rows
        assert BACKEND_TABLES | PROCESSOR_TABLES <= _tables(database)
