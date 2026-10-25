"""Small independent cost reference; no ingestion or production aggregation helpers."""
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text


PERIOD = {"start_date": "2024-06-01", "end_date": "2024-07-01", "timezone": "UTC"}
TOTALS = [
    {"currency": "EUR", "cost": "11.01", "record_count": 5},
    {"currency": "GBP", "cost": "0.00", "record_count": 1},
    {"currency": "USD", "cost": "9007199254740993.01", "record_count": 1},
]


def summary(**changes):
    return {
        "contract_version": 2, "period": PERIOD, "group_by": "service", "tag_key": None,
        "data_status": "partial", "totals": TOTALS,
        "groups": [], "missing_dimension_count": 1, "excluded_undated_count": 1,
        "monthly_spend": None, "currency": None, "savings_identified": None,
        "open_ingestions": 0, **changes,
    }


@pytest.fixture(scope="module")
def billing_schema(tenant_cockroach_database):
    db = tenant_cockroach_database
    # Processor migrations run in their own import namespace, as in production.
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    subprocess.run(
        [sys.executable, "-B", "-c",
         "import sys; from app.db.database import Database; "
         "db = Database(sys.argv[1]); db.initialize(); db.dispose()",
         db.engine.url.render_as_string(hide_password=False)],
        cwd=Path(__file__).resolve().parents[2] / "processor", env=env,
        check=True, capture_output=True, text=True, timeout=60,
    )
    return db


def insert_run(connection, identifier, tenant="tenant-a", subscription="sub-a", status="completed"):
    connection.execute(text(
        "INSERT INTO azure_cost_ingestion_runs "
        "(id, tenant_id, subscription_id, request, status, started_at) "
        "VALUES (:id, :tenant, :subscription, '{}'::JSONB, :status, :now)"
    ), {"id": identifier, "tenant": tenant, "subscription": subscription,
        "status": status, "now": datetime.now(timezone.utc)})


def insert_cost(connection, identifier, run="run-a", tenant="tenant-a", subscription="sub-a",
                day="2024-06-15", cost="1000", currency="EUR", resource_group=None,
                service=None, project=None, tags=None):
    connection.execute(text(
        "INSERT INTO azure_cost_records "
        "(id, ingestion_id, tenant_id, subscription_id, usage_date, pretax_cost, currency, "
        "dimensions, source_row_hash, created_at, resource_group, service_name, project, tags) "
        "VALUES (:id, :run, :tenant, :subscription, :day, :cost, :currency, '{}'::JSONB, "
        ":id, :now, :resource_group, :service, :project, CAST(:tags AS JSONB))"
    ), {"id": identifier, "run": run, "tenant": tenant, "subscription": subscription,
        "day": date.fromisoformat(day) if day else None, "cost": Decimal(cost),
        "currency": currency, "now": datetime.now(timezone.utc),
        "resource_group": resource_group, "service": service, "project": project,
        "tags": json.dumps(tags or {})})


@pytest.fixture
def cost_reference(billing_schema):
    db = billing_schema
    with db.engine.begin() as connection:
        connection.execute(text("DELETE FROM azure_cost_records"))
        connection.execute(text("DELETE FROM azure_cost_ingestion_runs"))
        insert_run(connection, "run-a")
        insert_run(connection, "run-b", subscription="sub-b")
        insert_run(connection, "foreign", tenant="tenant-b")
        insert_run(connection, "running", status="running")
        insert_run(connection, "failed", status="failed")
        insert_run(connection, "outside")
        common = {"resource_group": "Shared", "project": "Typed",
                  "tags": {"project": "Ignored", "environment": "Prod", "cost_center": "Finance",
                           "organization": "Team", "extra": "once"}}
        insert_cost(connection, "a", day="2024-06-01", cost="10.004", service="Compute", **common)
        insert_cost(connection, "b", day="2024-06-30", cost="2.004", service="compute",
                    resource_group="shared", project=" ",
                    tags={"project": "Fallback", "environment": "prod", "cost_center": "finance", "organization": "team"})
        insert_cost(connection, "c", run="run-b", subscription="sub-b", cost="-1.005",
                    resource_group="Shared", service="Storage")
        insert_cost(connection, "d", run="run-b", subscription="sub-b", cost="0",
                    resource_group=" ", service=" ", project=" ", tags={"environment": " "})
        insert_cost(connection, "e", run="run-b", subscription="sub-b", cost="0.005",
                    resource_group="Unknown", service="Unknown", project="Unknown",
                    tags={"environment": "Unknown", "cost_center": "Unknown", "organization": "Unknown"})
        insert_cost(connection, "f", cost="9007199254740993.005", currency="USD", service="Compute", **common)
        insert_cost(connection, "g", cost="-0.004", currency="GBP", service="Compute", **common)
        insert_cost(connection, "undated", day=None)
        insert_cost(connection, "before", day="2024-05-31")
        insert_cost(connection, "end", day="2024-07-01")
        insert_cost(connection, "outside-overlap", run="outside", day="2024-07-01")
        insert_cost(connection, "foreign", run="foreign", tenant="tenant-b")
        insert_cost(connection, "wrong-record-tenant", tenant="tenant-b")
        insert_cost(connection, "wrong-run-tenant", run="foreign")
        insert_cost(connection, "wrong-subscription", subscription="sub-b")
        insert_cost(connection, "running", run="running")
        insert_cost(connection, "failed", run="failed")
    try:
        yield db
    finally:
        with db.engine.begin() as connection:
            connection.execute(text("DELETE FROM azure_cost_records"))
            connection.execute(text("DELETE FROM azure_cost_ingestion_runs"))
