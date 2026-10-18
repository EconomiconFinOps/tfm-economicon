"""JUP-114: anomaly episode schema on real CockroachDB."""
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import exc, text

from app.db.migration_runner import MigrationRunner
from tenant_isolation_support import tenant_cockroach_database


MIGRATIONS = Path(__file__).resolve().parents[1] / "app" / "db" / "migrations"


@pytest.fixture
def schema(tenant_cockroach_database):
    db = tenant_cockroach_database
    MigrationRunner(db.engine, "app.db.migrations", MIGRATIONS).run()
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM anomaly_episodes"))
        connection.execute(text("DELETE FROM anomaly_detection_state"))
    yield db
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM anomaly_episodes"))
        connection.execute(text("DELETE FROM anomaly_detection_state"))


def episode(connection, identifier, *, tenant="tenant-a", service_key='"Compute"', status="new",
            observation="observed", severity="P3"):
    now = datetime.now(timezone.utc)
    connection.execute(text(
        "INSERT INTO anomaly_episodes (id, tenant_id, currency, service, service_key, start_date, "
        "last_seen_date, observation, reference_week_cost, opening_observed_cost, impact_numerator, "
        "impact_day_count, impact_through_date, severity, status, rules_version, rules, created_at, updated_at) "
        "VALUES (:id, :tenant, 'EUR', 'Compute', :key, :day, :day, :observation, 2800, 550, 1050, 1, :day, "
        ":severity, :status, 'jup019-daily-v1', '{}'::JSONB, :now, :now)"
    ), {"id": identifier, "tenant": tenant, "key": service_key, "day": date(2026, 9, 8),
        "observation": observation, "severity": severity, "status": status, "now": now})


def test_migration_applies_once_and_records_its_version(schema):
    MigrationRunner(schema.engine, "app.db.migrations", MIGRATIONS).run()
    with schema.engine.connect() as connection:
        versions = connection.execute(text("SELECT version FROM schema_migrations ORDER BY 1")).scalars().all()
        assert versions == ["001", "002", "003", "004", "005"]
        tables = set(connection.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )).scalars())
    assert {"anomaly_episodes", "anomaly_detection_state"} <= tables


def test_only_one_tracking_episode_per_tenant_currency_and_service(schema):
    with schema.engine.begin() as connection:
        episode(connection, "first")
    with pytest.raises(exc.IntegrityError):
        with schema.engine.begin() as connection:
            episode(connection, "second", status="investigating")
    with schema.engine.begin() as connection:
        episode(connection, "other-tenant", tenant="tenant-b")
        episode(connection, "null-service", service_key="null")
        episode(connection, "ended", observation="no_longer_observed")
        episode(connection, "closed", status="resolved")


@pytest.mark.parametrize("column,value", [
    ("status", "acknowledged"), ("observation", "gone"), ("severity", "P4"),
])
def test_enumerated_columns_reject_unknown_values(schema, column, value):
    with pytest.raises(exc.IntegrityError):
        with schema.engine.begin() as connection:
            episode(connection, "invalid", **{column: value})


def test_detection_state_has_one_row_per_tenant(schema):
    statement = text("INSERT INTO anomaly_detection_state VALUES (:tenant, :day, 'jup019-daily-v1', :now)")
    values = {"tenant": "tenant-a", "day": date(2026, 9, 13), "now": datetime.now(timezone.utc)}
    with schema.engine.begin() as connection:
        connection.execute(statement, values)
    with pytest.raises(exc.IntegrityError):
        with schema.engine.begin() as connection:
            connection.execute(statement, values)
