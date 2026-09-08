"""Opt-in tests for a disposable, real CockroachDB node.

From apps/processor, set PROCESSOR_COCKROACH_TEST_URL to
cockroachdb+psycopg://root@127.0.0.1:36413/defaultdb?sslmode=disable and run:

    python -B -m pytest -p no:cacheprovider \
        tests/test_azure_cost_cockroach_integration.py -v --basetemp=<unique-temp>

Use a newly started cockroachdb/cockroach:v24.1.11 start-single-node --insecure
container, without a persistent volume, publishing SQL on a loopback-only,
non-default port. On that disposable container ONLY, execute this separately:

    SET CLUSTER SETTING cluster.organization = 'processor-integration-tests'

The opt-in URL is an administration connection, never an application database.
The fixture rejects unmarked nodes, application URLs and pre-existing user
databases/tables. Each database has a generated name, is created without IF NOT
EXISTS, and is dropped only after this fixture successfully created it. Do not
run multiple pytest processes against the same node. Container/network lifecycle
belongs to the caller; database cleanup runs even when assertions fail.
"""

from __future__ import annotations

import json
import os
import shutil
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url

from app.db.database import Database
from app.db.migration_runner import MigrationRunner
from app.normalization.azure_cost import AzureCostNormalizationError, AzureCostNormalizer
from app.repositories.azure_cost import SqlAzureCostRepository
from app.tasks.azure_cost_ingest import AzureCostIngestionService, ingestion_run_id
from test_azure_cost_ingestion import DEFINITION, result
from test_azure_cost_normalized_schema import normalized_record


TEST_URL_ENV = "PROCESSOR_COCKROACH_TEST_URL"
pytestmark = pytest.mark.skipif(
    not os.environ.get(TEST_URL_ENV),
    reason=f"set {TEST_URL_ENV} to opt in to disposable CockroachDB tests",
)
MIGRATIONS = Path(__file__).parents[1] / "app" / "db" / "migrations"
MIGRATION_PACKAGE = "app.db.migrations"


@pytest.fixture(scope="module")
def database_factory():
    url = make_url(os.environ[TEST_URL_ENV])
    if (
        url.drivername != "cockroachdb+psycopg"
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or url.port is None
        or not 1024 <= url.port <= 65535
        or url.port in {5432, 26257}
        or url.database != "defaultdb"
        or url.username != "root"
        or url.password is not None
        or dict(url.query) != {"sslmode": "disable"}
    ):
        raise RuntimeError("Unsafe integration URL: use a disposable loopback node")

    admin = create_engine(
        url, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5}
    )
    try:
        with admin.connect() as connection:
            version = connection.execute(text("SELECT version()")).scalar_one()
            marker = connection.execute(
                text("SHOW CLUSTER SETTING cluster.organization")
            ).scalar_one()
            databases = set(connection.execute(text("SHOW DATABASES")).scalars())
            if "CockroachDB" not in version or marker != "processor-integration-tests":
                raise RuntimeError("Refusing an unmarked or non-CockroachDB server")
            if databases != {"defaultdb", "postgres", "system"}:
                raise RuntimeError("Refusing a node with pre-existing user databases")
            for name in ("defaultdb", "postgres"):
                tables = connection.execute(
                    text(f"SELECT table_name FROM {name}.information_schema.tables "
                         "WHERE table_schema NOT IN ('pg_catalog', 'information_schema', "
                         "'crdb_internal') AND table_type <> 'SYSTEM VIEW'")
                ).all()
                if tables:
                    raise RuntimeError("Refusing a node with pre-existing user tables")

        @contextmanager
        def create_database():
            name = "processor_test_" + uuid4().hex
            with admin.connect() as connection:
                connection.execute(text(f'CREATE DATABASE "{name}"'))
            database = None
            try:
                database = Database(url.set(database=name))
                yield database
            finally:
                if database is not None:
                    database.dispose()
                with admin.connect() as connection:
                    connection.execute(text(f'DROP DATABASE "{name}" CASCADE'))

        yield create_database
    finally:
        admin.dispose()


@pytest.fixture(scope="module")
def fresh_database(database_factory):
    with database_factory() as database:
        database.initialize()
        yield database


def _rows(database, statement):
    with database.engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(statement)).mappings()]


def _cost_snapshot(database):
    return _rows(database, "SELECT * FROM azure_cost_records ORDER BY id")


def _scope_totals(database):
    return _rows(
        database,
        "SELECT tenant_id, subscription_id, currency, count(*) AS row_count, "
        "sum(pretax_cost) AS total FROM azure_cost_records "
        "GROUP BY tenant_id, subscription_id, currency "
        "ORDER BY tenant_id, subscription_id, currency",
    )


def _assert_schema(database):
    assert _rows(
        database, "SELECT version FROM processor_schema_migrations ORDER BY version"
    ) == [{"version": version} for version in ("001", "002", "003")]
    with database.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM jobs")).scalar_one() == 0
    indexes = _rows(database, "SHOW INDEXES FROM azure_cost_records")
    for name, columns in {
        "idx_azure_cost_records_scope_date": ["tenant_id", "subscription_id", "usage_date"],
        "idx_azure_cost_records_resource_group": ["tenant_id", "resource_group"],
        "idx_azure_cost_records_service": ["tenant_id", "service_name"],
    }.items():
        keys = sorted(
            (row for row in indexes if row["index_name"] == name and not row["implicit"]),
            key=lambda row: row["seq_in_index"],
        )
        assert [row["column_name"] for row in keys] == columns, name


def test_fresh_migrations_and_repository_round_trip(fresh_database):
    database = fresh_database
    _assert_schema(database)
    repository = SqlAzureCostRepository(database)
    records = (
        normalized_record(),
        *AzureCostNormalizer().normalize(result(
            {"PreTaxCost": 0, "Currency": "EUR"},
            {"PreTaxCost": -1.25, "Currency": "USD", "UsageDate": 20240602,
             "Quantity": -2.5, "UnitOfMeasure": "GB"},
        )),
    )
    run_id = ingestion_run_id("round-trip", "subscription-demo", DEFINITION)
    repository.start_run(run_id, "round-trip", "subscription-demo", DEFINITION)
    repository.complete_run(
        run_id, "round-trip", "subscription-demo", records, page_count=2, retry_count=1
    )
    fetched = repository.fetch_records(run_id)
    assert len(fetched) == 3
    by_hash = {row["source_row_hash"]: row for row in fetched}
    for record in records:
        actual = dict(by_hash[record.source_row_hash])
        assert actual.pop("id")
        assert actual == asdict(record)
    assert repository.fetch_run(run_id) == {
        "id": run_id, "tenant_id": "round-trip", "subscription_id": "subscription-demo",
        "status": "completed", "page_count": 2, "retry_count": 1,
        "row_count": 3, "error_code": None,
    }
    before = _cost_snapshot(database)
    database.initialize()
    _assert_schema(database)
    assert _cost_snapshot(database) == before


def _seed_legacy(database, cases=None):
    cases = cases if cases is not None else [
        ("legacy-positive", "tenant-a", "sub-a", "EUR", "12.5", {
            "BillingAccountId": "billing-demo", "SubscriptionName": "Ecommerce Prod",
            "ResourceGroup": "RG-App", "MeterCategory": "Storage", "Project": "Jupiter",
            "Quantity": 3.25, "UnitOfMeasure": "GB/Month", "CostCenter": "1234",
            "env": "Prod", "org": "Finance", "ResourceLocation": "westeurope",
        }, {
            "billing_account_id": "billing-demo", "subscription_name": "Ecommerce Prod",
            "resource_group": "RG-App", "service_name": "Storage", "project": "Jupiter",
            "consumed_quantity": Decimal("3.25"), "consumed_unit": "GB/Month",
            "tags": {"cost_center": "1234", "project": "Jupiter",
                     "environment": "Prod", "organization": "Finance"},
        }),
        ("legacy-credit", "tenant-a", "sub-a", "EUR", "-1.25", {
            "SubAccountName": "Ecommerce Prod", "x_ResourceGroupName": "RG-Credit",
            "ServiceCategory": "Compute", "UsageQuantity": -2.5, "Unit": "Hours",
            "costcenter": "5678", "Environment": "Test", "Organization": "Platform",
        }, {
            "subscription_name": "Ecommerce Prod", "resource_group": "RG-Credit",
            "service_name": "Compute", "consumed_quantity": Decimal("-2.5"),
            "consumed_unit": "Hours", "tags": {"cost_center": "5678",
                "environment": "Test", "organization": "Platform"},
        }),
        ("legacy-zero", "tenant-a", "sub-a", "USD", "0", {
            "ResourceGroupName": "RG-Zero", "ServiceName": "Network",
            "ConsumedQuantity": 0, "ConsumedUnit": "GB",
        }, {"resource_group": "RG-Zero", "service_name": "Network",
            "consumed_quantity": Decimal("0"), "consumed_unit": "GB"}),
        ("legacy-sparse", "tenant-b", "sub-a", "EUR", "9.125", {
            "ResourceLocation": "eastus", "AdditionalMeter": 7,
        }, {}),
        ("legacy-other-sub", "tenant-a", "sub-b", "EUR", "2.75", {}, {}),
        ("legacy-serialized-tags", "tenant-b", "sub-b", "USD", "4.5", {
            "ResourceGroup": "RG-Tags", "ServiceName": "Storage",
            "Tags": '"Project":"Jupiter","CostCenter":"1234","Owner Team":"Platform"',
        }, {"resource_group": "RG-Tags", "service_name": "Storage", "project": "Jupiter",
            "tags": {"project": "Jupiter", "cost_center": "1234", "owner_team": "Platform"}}),
    ]
    now = datetime(2024, 6, 3, tzinfo=timezone.utc)
    expected = {}
    repository = SqlAzureCostRepository(database)
    for index, (record_id, tenant, subscription, currency, cost, dimensions, fields) in enumerate(cases):
        run_id = "run-" + record_id
        repository.start_run(run_id, tenant, subscription, DEFINITION)
        with database.engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO azure_cost_records (id, ingestion_id, tenant_id, subscription_id, "
                "usage_date, pretax_cost, currency, dimensions, source_row_hash, created_at) "
                "VALUES (:id, :run, :tenant, :subscription, :day, :cost, :currency, "
                ":dimensions, :hash, :created)"
            ), {
                "id": record_id, "run": run_id, "tenant": tenant,
                "subscription": subscription, "day": date(2024, 6, 1),
                "cost": Decimal(cost), "currency": currency,
                "dimensions": json.dumps(dimensions), "hash": str(index + 1) * 64,
                "created": now,
            })
            connection.execute(text(
                "UPDATE azure_cost_ingestion_runs SET status = 'completed', row_count = 1, "
                "page_count = 1, completed_at = :completed WHERE id = :run"
            ), {"run": run_id, "completed": now})
        expected[record_id] = {
            "billing_account_id": None, "subscription_name": None, "resource_group": None,
            "service_name": None, "project": None, "consumed_quantity": None,
            "consumed_unit": None, "tags": {}, **fields,
        }
    return expected


@pytest.mark.parametrize("interruption", [None, "ddl", "backfill", "index", "version"])
def test_legacy_upgrade_preserves_rows_backfills_and_ingestion(
    database_factory, tmp_path, interruption,
):
    with database_factory() as database:
        for migration in MIGRATIONS.glob("00[12]_*.py"):
            shutil.copyfile(migration, tmp_path / migration.name)
        MigrationRunner(
            database.engine, MIGRATION_PACKAGE, tmp_path,
            version_table="processor_schema_migrations",
        ).run()
        assert _rows(
            database, "SELECT version FROM processor_schema_migrations ORDER BY version"
        ) == [{"version": "001"}, {"version": "002"}]
        expected = _seed_legacy(database)
        before = _cost_snapshot(database)
        totals_before = _scope_totals(database)
        runs_before = _rows(database, "SELECT * FROM azure_cost_ingestion_runs ORDER BY id")
        assert len(before) == 6
        assert len(totals_before) == 5

        if interruption is not None:
            def interrupt(connection, cursor, statement, parameters, context, executemany):
                sql = " ".join(statement.upper().split())
                boundary = {
                    "ddl": sql.startswith("ALTER TABLE AZURE_COST_RECORDS"),
                    "backfill": "UPDATE AZURE_COST_RECORDS AS RECORDS" in sql,
                    "index": sql.startswith(
                        "CREATE INDEX IF NOT EXISTS IDX_AZURE_COST_RECORDS_SCOPE_DATE"
                    ),
                    "version": sql.startswith("INSERT INTO PROCESSOR_SCHEMA_MIGRATIONS"),
                }
                if boundary[interruption]:
                    raise RuntimeError(f"injected migration interruption: {interruption}")

            hook = "before_cursor_execute" if interruption == "version" else "after_cursor_execute"
            event.listen(database.engine, hook, interrupt)
            try:
                with pytest.raises(RuntimeError, match=f"injected migration interruption: {interruption}"):
                    database.initialize()
            finally:
                event.remove(database.engine, hook, interrupt)

            assert _rows(
                database, "SELECT version FROM processor_schema_migrations ORDER BY version"
            ) == [{"version": "001"}, {"version": "002"}]
            partial = _cost_snapshot(database)
            for old, new in zip(before, partial, strict=True):
                assert {key: new[key] for key in old} == old
            assert _scope_totals(database) == totals_before
            assert "billing_account_id" in partial[0]
            if interruption != "ddl":
                positive = next(row for row in partial if row["id"] == "legacy-positive")
                assert positive["billing_account_id"] == "billing-demo"
                assert positive["tags"] == expected["legacy-positive"]["tags"]
            if interruption in {"index", "version"}:
                assert "idx_azure_cost_records_scope_date" in {
                    row["index_name"] for row in _rows(database, "SHOW INDEXES FROM azure_cost_records")
                }

            # Differing populated values make destructive retry backfills observable.
            with database.engine.begin() as connection:
                connection.execute(text(
                    "UPDATE azure_cost_records SET billing_account_id = 'retained-account', "
                    "tags = CAST(:tags AS JSONB) WHERE id = 'legacy-positive'"
                ), {"tags": json.dumps({"owner": "retained-owner"})})
            expected["legacy-positive"].update(
                billing_account_id="retained-account",
                tags={**expected["legacy-positive"]["tags"], "owner": "retained-owner"},
            )

        database.initialize()

        after = _cost_snapshot(database)
        assert len(after) == len(before)
        for old, new in zip(before, after, strict=True):
            assert {key: new[key] for key in old} == old, old["id"]
        assert _scope_totals(database) == totals_before
        assert _rows(database, "SELECT * FROM azure_cost_ingestion_runs ORDER BY id") == runs_before
        _assert_schema(database)
        for row in after:
            assert {key: row[key] for key in expected[row["id"]]} == expected[row["id"]], row["id"]
        database.initialize()
        assert _cost_snapshot(database) == after
        _assert_idempotent_ingestion(database)


def _initialize_legacy(database, tmp_path):
    for migration in MIGRATIONS.glob("00[12]_*.py"):
        shutil.copyfile(migration, tmp_path / migration.name)
    MigrationRunner(
        database.engine, MIGRATION_PACKAGE, tmp_path,
        version_table="processor_schema_migrations",
    ).run()
    assert _rows(
        database, "SELECT version FROM processor_schema_migrations ORDER BY version"
    ) == [{"version": "001"}, {"version": "002"}]


def _interrupt_003(database, boundary):
    def interrupt(connection, cursor, statement, parameters, context, executemany):
        sql = " ".join(statement.upper().split())
        if (
            boundary == "ddl" and sql.startswith("ALTER TABLE AZURE_COST_RECORDS")
            or boundary == "backfill" and "UPDATE AZURE_COST_RECORDS AS RECORDS" in sql
        ):
            raise RuntimeError(f"injected migration interruption: {boundary}")

    event.listen(database.engine, "after_cursor_execute", interrupt)
    try:
        with pytest.raises(RuntimeError, match=f"injected migration interruption: {boundary}"):
            database.initialize()
    finally:
        event.remove(database.engine, "after_cursor_execute", interrupt)
    assert _rows(
        database, "SELECT version FROM processor_schema_migrations ORDER BY version"
    ) == [{"version": "001"}, {"version": "002"}]


def _assert_upgrade_preserved(database, before, totals_before, runs_before):
    after = _cost_snapshot(database)
    assert len(after) == len(before)
    for old, new in zip(before, after, strict=True):
        assert {key: new[key] for key in old} == old, old["id"]
    assert _scope_totals(database) == totals_before
    assert _rows(database, "SELECT * FROM azure_cost_ingestion_runs ORDER BY id") == runs_before
    _assert_schema(database)
    database.initialize()
    assert _cost_snapshot(database) == after
    return after


@pytest.mark.parametrize(("dimensions", "tags", "project"), [
    pytest.param({"CostCenter": 1234}, {"cost_center": "1234"}, None, id="numeric-cost-center"),
    pytest.param({"Project": 1234}, {"project": "1234"}, "1234", id="numeric-project"),
])
def test_legacy_numeric_individual_tags_upgrade(
    database_factory, tmp_path, dimensions, tags, project,
):
    with database_factory() as database:
        _initialize_legacy(database, tmp_path)
        _seed_legacy(database, [
            ("legacy-numeric", "tenant-a", "sub-a", "EUR", "12.5", dimensions, {}),
        ])
        before = _cost_snapshot(database)
        assert before[0]["dimensions"] == dimensions
        totals = _scope_totals(database)
        runs = _rows(database, "SELECT * FROM azure_cost_ingestion_runs ORDER BY id")

        database.initialize()

        after = _assert_upgrade_preserved(database, before, totals, runs)
        assert after[0]["tags"] == tags
        assert after[0]["project"] == project


@pytest.mark.parametrize("interruption", [None, "ddl", "backfill"])
@pytest.mark.parametrize(("individual", "source_tags"), [
    pytest.param({"Project": "Jupiter"}, {"project": "Jupiter"}, id="project"),
    pytest.param({"CostCenter": "1234"}, {"cost_center": "1234"}, id="cost-center"),
    pytest.param({"CostCenter": 1234}, {"cost_center": "1234"}, id="numeric-cost-center"),
])
def test_legacy_mixed_tags_merge_without_clobbering(
    database_factory, tmp_path, interruption, individual, source_tags,
):
    dimensions = {**individual, "Tags": '{"Owner Team":"Platform"}'}
    expected_tags = {**source_tags, "owner_team": "Platform"}
    with database_factory() as database:
        _initialize_legacy(database, tmp_path)
        _seed_legacy(database, [
            ("legacy-mixed", "tenant-a", "sub-a", "EUR", "-1.25", dimensions, {}),
            ("legacy-mixed-source", "tenant-a", "sub-a", "EUR", "0", dimensions, {}),
        ])
        before = _cost_snapshot(database)
        totals = _scope_totals(database)
        runs = _rows(database, "SELECT * FROM azure_cost_ingestion_runs ORDER BY id")
        if interruption is not None:
            _interrupt_003(database, interruption)
            # Model a prior partial backfill plus independently validated values.
            retained = {
                **_cost_snapshot(database)[0]["tags"],
                "validated": "preserve",
                next(iter(source_tags)): "retained-value",
            }
            with database.engine.begin() as connection:
                connection.execute(text(
                    "UPDATE azure_cost_records SET tags = CAST(:tags AS JSONB) "
                    "WHERE id = 'legacy-mixed'"
                ), {"tags": json.dumps(retained)})
            expected_tags.update(retained)

        database.initialize()

        after = _assert_upgrade_preserved(database, before, totals, runs)
        assert after[0]["tags"] == expected_tags
        assert after[1]["tags"] == {**source_tags, "owner_team": "Platform"}
        if "Project" in individual:
            assert after[0]["project"] == "Jupiter"
            assert after[1]["project"] == "Jupiter"


@pytest.mark.parametrize(("quantity", "unit", "expected_quantity", "expected_unit"), [
    pytest.param(None, "Hours", None, "Hours", id="unmatched-unit"),
    pytest.param(Decimal("3"), None, Decimal("3"), None, id="unmatched-quantity"),
    pytest.param(None, "GB", Decimal("2"), "GB", id="matched-unit"),
    pytest.param(Decimal("2"), None, Decimal("2"), "GB", id="matched-quantity"),
])
def test_legacy_partial_consumption_requires_matching_partner(
    database_factory, tmp_path, quantity, unit, expected_quantity, expected_unit,
):
    with database_factory() as database:
        _initialize_legacy(database, tmp_path)
        _seed_legacy(database, [
            ("legacy-partial", "tenant-a", "sub-a", "EUR", "0",
             {"Quantity": 2, "Unit": "GB", "ResourceLocation": "eastus"}, {}),
        ])
        before = _cost_snapshot(database)
        totals = _scope_totals(database)
        runs = _rows(database, "SELECT * FROM azure_cost_ingestion_runs ORDER BY id")
        _interrupt_003(database, "ddl")
        with database.engine.begin() as connection:
            connection.execute(text(
                "UPDATE azure_cost_records SET consumed_quantity = :quantity, "
                "consumed_unit = :unit WHERE id = 'legacy-partial'"
            ), {"quantity": quantity, "unit": unit})
        staged = _cost_snapshot(database)[0]
        assert (staged["consumed_quantity"], staged["consumed_unit"]) == (quantity, unit)

        database.initialize()

        after = _assert_upgrade_preserved(database, before, totals, runs)
        assert (after[0]["consumed_quantity"], after[0]["consumed_unit"]) == (
            expected_quantity, expected_unit,
        )


class SourceClient:
    def __init__(self, *rows):
        self.rows = rows

    def query_all(self, subscription_id, definition):
        assert subscription_id == "subscription-demo"
        assert definition == DEFINITION
        return result(*self.rows, page_count=2, retry_count=1)


def _assert_idempotent_ingestion(database):
    repository = SqlAzureCostRepository(database)
    baseline = _cost_snapshot(database)
    ea_row = {
        "PreTaxCost": 12.5, "Currency": " eur ", "UsageDate": 20240601,
        "BillingAccountId": " billing-demo ", "SubscriptionName": " Ecommerce Prod ",
        "ResourceGroup": " RG-App ", "MeterCategory": " Storage ",
        "Quantity": 3.25, "UnitOfMeasure": " GB/Month ",
        "Tags": '"Project":"Jupiter","CostCenter":"1234","Owner Team":"Platform"',
        "ResourceLocation": " westeurope ",
    }
    focus_row = {
        "PreTaxCost": 12.5, "Currency": "EUR", "UsageDate": 20240601,
        "BillingAccountId": "billing-demo", "SubAccountName": "Ecommerce Prod",
        "x_ResourceGroupName": "RG-App", "ServiceName": "Storage",
        "ConsumedQuantity": 3.25, "ConsumedUnit": "GB/Month",
        "Tags": '{"Project":"Jupiter","CostCenter":"1234","Owner Team":"Platform"}',
        "ResourceLocation": "westeurope",
    }
    zero = {"PreTaxCost": 0, "Currency": "EUR", "Quantity": 0, "Unit": "GB"}
    credit = {"PreTaxCost": -1.25, "Currency": "USD", "Quantity": -2.5, "Unit": "GB"}
    client = SourceClient(ea_row, zero, credit)
    service = AzureCostIngestionService(client, AzureCostNormalizer(), repository)
    first = service.ingest("idempotency", "subscription-demo", DEFINITION)
    records = repository.fetch_records(first.run_id)
    state = repository.fetch_run(first.run_id)
    totals = _scope_totals(database)
    assert first.row_count == len(records) == 3
    assert state["status"] == "completed"
    assert (state["page_count"], state["retry_count"], state["row_count"]) == (2, 1, 3)
    by_cost = {row["pretax_cost"]: row for row in records}
    full = by_cost[Decimal("12.5")]
    assert full["billing_account_id"] == "billing-demo"
    assert full["subscription_name"] == "Ecommerce Prod"
    assert (full["resource_group"], full["service_name"], full["project"]) == (
        "RG-App", "Storage", "Jupiter"
    )
    assert full["tags"] == {"project": "Jupiter", "cost_center": "1234", "owner_team": "Platform"}
    assert full["dimensions"] == {"ResourceLocation": "westeurope"}
    assert full["consumed_quantity"] == Decimal("3.25")
    assert full["consumed_unit"] == "GB/Month"
    assert by_cost[Decimal("0")]["consumed_quantity"] == Decimal("0")
    assert by_cost[Decimal("-1.25")]["consumed_quantity"] == Decimal("-2.5")
    assert [row for row in totals if row["tenant_id"] == "idempotency"] == [
        {"tenant_id": "idempotency", "subscription_id": "subscription-demo",
         "currency": "EUR", "row_count": 2, "total": Decimal("12.5")},
        {"tenant_id": "idempotency", "subscription_id": "subscription-demo",
         "currency": "USD", "row_count": 1, "total": Decimal("-1.25")},
    ]
    for source in (ea_row, focus_row):
        client.rows = (source, zero, credit)
        repeated = service.ingest("idempotency", "subscription-demo", DEFINITION)
        assert repeated == first
        assert repository.fetch_run(first.run_id) == state
        assert repository.fetch_records(first.run_id) == records
        assert _scope_totals(database) == totals
    assert [row for row in _cost_snapshot(database) if row["ingestion_id"] != first.run_id] == baseline


def test_fresh_service_ingestion_is_idempotent_across_aliases(fresh_database):
    _assert_idempotent_ingestion(fresh_database)


INVALID_ROWS = [
    pytest.param({"PreTaxCost": value}, message, id=f"cost-{name}")
    for name, value, message in (
        ("text", "bad", "must be numeric"), ("boolean", True, "must be numeric"),
        ("nan", float("nan"), "must be finite"),
        ("infinity", float("inf"), "must be finite"),
    )
] + [
    pytest.param({"ConsumedQuantity": value, "ConsumedUnit": "GB"}, message,
                 id=f"quantity-{name}")
    for name, value, message in (
        ("text", "bad", "must be numeric"), ("boolean", True, "must be numeric"),
        ("nan", float("nan"), "must be finite"),
        ("infinity", float("inf"), "must be finite"),
    )
] + [
    pytest.param({"Quantity": 2}, "supplied together", id="quantity-without-unit"),
    pytest.param({"Unit": "GB"}, "supplied together", id="unit-without-quantity"),
    pytest.param({"ServiceName": "Storage", "MeterCategory": "Compute"},
                 "Conflicting aliases", id="conflicting-aliases"),
    pytest.param({"Project": "Jupiter", "Tags": '{"Project":"Other"}'},
                 "Conflicting values for tag project", id="conflicting-tags"),
]


@pytest.mark.parametrize(("invalid_fields", "message"), INVALID_ROWS)
def test_invalid_batch_leaves_no_partial_rows(fresh_database, invalid_fields, message):
    database = fresh_database
    repository = SqlAzureCostRepository(database)
    before = _cost_snapshot(database)
    totals_before = _scope_totals(database)
    tenant = "invalid-" + uuid4().hex
    valid = {"PreTaxCost": 1, "Currency": "EUR"}
    client = SourceClient(valid, {**valid, **invalid_fields}, valid)
    service = AzureCostIngestionService(client, AzureCostNormalizer(), repository)

    with pytest.raises(AzureCostNormalizationError, match=message):
        service.ingest(tenant, "subscription-demo", DEFINITION)

    run_id = ingestion_run_id(tenant, "subscription-demo", DEFINITION)
    assert repository.fetch_run(run_id) == {
        "id": run_id, "tenant_id": tenant, "subscription_id": "subscription-demo",
        "status": "failed", "page_count": 0, "retry_count": 0, "row_count": 0,
        "error_code": "AzureCostNormalizationError",
    }
    assert repository.fetch_records(run_id) == []
    assert _cost_snapshot(database) == before
    assert _scope_totals(database) == totals_before
