"""JUP-114 fixtures: real CockroachDB with processor cost tables and backend episode tables."""
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text

from app.db.migration_runner import MigrationRunner
from billing_support import insert_cost, insert_run


MIGRATIONS = Path(__file__).resolve().parents[1] / "app" / "db" / "migrations"
D = date(2026, 9, 8)


def clear(db):
    with db.engine.begin() as connection:
        for table in ("anomaly_episodes", "anomaly_detection_state", "azure_cost_records", "azure_cost_ingestion_runs"):
            connection.execute(text(f"DELETE FROM {table}"))


@pytest.fixture
def episode_store(billing_schema):
    db = billing_schema
    MigrationRunner(db.engine, "app.db.migrations", MIGRATIONS).run()
    clear(db)
    try:
        yield db
    finally:
        clear(db)


def load_series(db, values, *, start=D - timedelta(days=7), tenant="tenant-a", run="run-a",
                service="Compute", currency="EUR", subscription="sub-a", prefix=None):
    """One record per day; None leaves the day without a record of this group."""
    with db.engine.begin() as connection:
        exists = connection.execute(text("SELECT count(*) FROM azure_cost_ingestion_runs WHERE id = :id"),
                                    {"id": run}).scalar_one()
        if not exists:
            insert_run(connection, run, tenant=tenant, subscription=subscription)
        for offset, value in enumerate(values):
            if value is None:
                continue
            day = start + timedelta(days=offset)
            insert_cost(connection, f"{prefix or tenant}-{run}-{service}-{currency}-{day}", run=run, tenant=tenant,
                        subscription=subscription, day=day.isoformat(), cost=value, currency=currency,
                        service=service)


def episode_rows(db, tenant=None):
    query = "SELECT * FROM anomaly_episodes" + (" WHERE tenant_id = :tenant" if tenant else "") + " ORDER BY id"
    with db.engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(query), {"tenant": tenant}).mappings()]
