from __future__ import annotations

import importlib
from contextlib import AbstractContextManager
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from app.normalization.azure_cost import NormalizedCostRecord
from app.repositories.azure_cost import SqlAzureCostRepository


class RecordingConnection:
    def __init__(self):
        self.calls: list[tuple[str, dict | None]] = []

    def execute(self, statement, params=None):
        self.calls.append((str(statement), params))


class RecordingTransaction(AbstractContextManager):
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class RecordingEngine:
    def __init__(self, connection):
        self.connection = connection

    def begin(self):
        return RecordingTransaction(self.connection)


def normalized_record() -> NormalizedCostRecord:
    return NormalizedCostRecord(
        usage_date=date(2024, 6, 1),
        pretax_cost=Decimal("12.5"),
        currency="EUR",
        billing_account_id="billing-demo",
        subscription_name="Ecommerce Prod",
        resource_group="rg-app",
        service_name="Storage",
        project="Jupiter",
        consumed_quantity=Decimal("3.25"),
        consumed_unit="GB/Month",
        tags={"cost_center": "1234", "project": "Jupiter"},
        dimensions={"ResourceLocation": "westeurope"},
        source_row_hash="a" * 64,
    )


def test_migration_adds_backfills_and_indexes_finops_columns():
    connection = RecordingConnection()
    migration = importlib.import_module(
        "app.db.migrations.003_normalized_cost_dimensions"
    )

    migration.upgrade(connection)

    sql = "\n".join(statement for statement, _ in connection.calls)
    for column in (
        "billing_account_id",
        "subscription_name",
        "resource_group",
        "service_name",
        "project",
        "consumed_quantity",
        "consumed_unit",
        "tags",
    ):
        assert column in sql
    assert "dimensions->>'BillingAccountId'" in sql
    assert "dimensions->>'SubAccountName'" in sql
    assert "dimensions->>'ResourceGroup'" in sql
    assert "dimensions->>'ConsumedQuantity'" in sql
    assert "dimensions->>'UsageQuantity'" in sql
    assert "dimensions->>'UnitOfMeasure'" in sql
    assert "jsonb_build_object" in sql
    assert "'cost_center'" in sql
    assert "idx_azure_cost_records_scope_date" in sql
    assert "idx_azure_cost_records_resource_group" in sql
    assert "idx_azure_cost_records_service" in sql


def test_repository_persists_explicit_finops_columns():
    connection = RecordingConnection()
    database = SimpleNamespace(engine=RecordingEngine(connection))
    repository = SqlAzureCostRepository(database)

    repository.complete_run(
        "run-demo",
        "tenant-demo",
        "subscription-demo",
        (normalized_record(),),
        page_count=1,
        retry_count=0,
    )

    insert = next(
        (statement, params)
        for statement, params in connection.calls
        if "INSERT INTO azure_cost_records" in statement
    )
    statement, params = insert
    assert params is not None
    assert "billing_account_id" in statement
    assert "consumed_quantity" in statement
    assert params["resource_group"] == "rg-app"
    assert params["service_name"] == "Storage"
    assert params["project"] == "Jupiter"
    assert params["consumed_quantity"] == Decimal("3.25")
    assert params["tags"] == '{"cost_center": "1234", "project": "Jupiter"}'
