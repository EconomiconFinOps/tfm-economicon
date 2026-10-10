"""Real Azure simulator -> HTTP client -> normalizer -> SQL repository contract.

The simulator runs in a subprocess because both services own a package called
``app``. It binds an ephemeral loopback port and uses the committed CSV/mapping.
Persistence uses the existing SQLite schema adapter; CockroachDB migrations and
decimal/storage behavior remain covered by the explicit CockroachDB suite.
"""
from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

import pytest
from sqlalchemy import text

from app.clients.azure_cost import AzureCostClient, AzureCostHttpError
from app.core.config import Settings
from app.normalization.azure_cost import AzureCostNormalizer
from app.repositories.azure_cost import SqlAzureCostRepository
from app.tasks.azure_cost_ingest import AzureCostIngestionService, ingestion_run_id
from tenant_isolation_support import isolation_database, snapshot


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = json.loads(
    (ROOT / "docs/api/azure-cost-query-contract-cases.json").read_text(encoding="utf-8")
)
SUBSCRIPTION = CONTRACT["knownSubscriptionId"]
DEFINITION = next(
    case["request"]
    for case in CONTRACT["cases"]
    if case["id"] == "daily-cost-by-resource-id"
)
TOKEN = "jup054-synthetic-contract-token"
PAGE_SIZE = 2
pytestmark = pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)

# No fake response bodies: Uvicorn serves the production app and query engine.
SERVER = """
import socket
import sys
from pathlib import Path

root, address_file = map(Path, sys.argv[1:])
sys.path.insert(0, str(root / 'apps/azure-cost-api'))
import uvicorn
from app.config import Settings
from app.main import create_app

settings = Settings(
    _env_file=None,
    azure_cost_dataset_path=root / 'fixtures/azure-cost/EA-Cost-Actual.sample.csv',
    azure_cost_mapping_path=root / 'docs/api/azure-cost-query-mapping.json',
    azure_cost_openapi_path=root / 'docs/api/azure-cost-query.openapi.json',
    azure_cost_auth_enabled=True,
    azure_cost_valid_tokens='jup054-synthetic-contract-token',
    azure_cost_forbidden_tokens='jup054-forbidden-contract-token',
    azure_cost_page_size=2,
    azure_cost_skiptoken_secret='jup054-synthetic-pagination-secret',
)
with socket.socket() as listener:
    listener.bind(('127.0.0.1', 0))
    address_file.write_text(str(listener.getsockname()[1]), encoding='utf-8')
    server = uvicorn.Server(uvicorn.Config(create_app(settings), log_level='warning'))
    server.run(sockets=[listener])
"""


@pytest.fixture(scope="module")
def azure_api_url(tmp_path_factory):
    directory = tmp_path_factory.mktemp("azure-contract-server")
    address_file = directory / "port.txt"
    log_file = directory / "server.log"
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("AZURE_COST_") and key.upper() != "PYTHONPATH"
    }
    # Readiness must bypass any developer-machine proxy, just like the client.
    opener = build_opener(ProxyHandler({}))
    with log_file.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-B", "-u", "-c", SERVER, str(ROOT), str(address_file)],
            cwd=directory,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            # Windows CI may scan the new interpreter process and dependencies.
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    pytest.fail(f"Azure simulator exited: {log_file.read_text(encoding='utf-8')}")
                if address_file.exists():
                    port = address_file.read_text(encoding="utf-8").strip()
                    if port:
                        url = f"http://127.0.0.1:{int(port)}"
                        try:
                            with opener.open(f"{url}/health", timeout=0.25) as response:
                                if json.load(response)["status"] == "ok":
                                    break
                        except (URLError, TimeoutError):
                            pass
                time.sleep(0.05)
            else:
                pytest.fail(f"Azure simulator did not start: {log_file.read_text(encoding='utf-8')}")
            yield url
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


@pytest.fixture
def ingestion_factory(azure_api_url, isolation_database, monkeypatch):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    repository = SqlAzureCostRepository(isolation_database)

    def create(token=TOKEN):
        settings = Settings(
            _env_file=None,
            azure_cost_api_base_url=azure_api_url,
            azure_cost_api_token=token,
            # Contract tests allow a loaded host to reply; deadline behavior is
            # tested separately in test_azure_cost_client.py.
            azure_cost_api_timeout_seconds=10,
            azure_cost_api_max_retries=0,
        )
        return AzureCostIngestionService(
            AzureCostClient(settings), AzureCostNormalizer(), repository
        )

    return create, repository


def expected_fixture_costs():
    """Independent CSV oracle, without using either service's transformation code."""
    start = datetime.fromisoformat(DEFINITION["timePeriod"]["from"]).date()
    end = datetime.fromisoformat(DEFINITION["timePeriod"]["to"]).date()
    expected = defaultdict(Decimal)
    with (ROOT / "fixtures/azure-cost/EA-Cost-Actual.sample.csv").open(
        encoding="utf-8-sig", newline=""
    ) as fixture:
        for row in csv.DictReader(fixture):
            usage_date = datetime.strptime(row["Date"], "%m/%d/%Y").date()
            if row["SubscriptionId"].casefold() == SUBSCRIPTION and start <= usage_date < end:
                key = (
                    usage_date.isoformat(), row["ResourceId"],
                    row["ResourceGroup"], row["BillingCurrencyCode"],
                )
                expected[key] += Decimal(row["CostInBillingCurrency"])
    return expected


def test_real_paginated_costs_are_normalized_persisted_and_idempotent(ingestion_factory, isolation_database):
    create, repository = ingestion_factory
    service = create()
    first = service.ingest("tenant-a", SUBSCRIPTION, DEFINITION)
    own_scope = {"tenant_id": "tenant-a", "subscription_id": SUBSCRIPTION}
    first_records = repository.fetch_records(first.run_id, **own_scope)
    expected = expected_fixture_costs()

    assert len(expected) > PAGE_SIZE  # This must exercise a real nextLink.
    assert first.row_count == len(expected)
    assert first.page_count == math.ceil(len(expected) / PAGE_SIZE)
    assert first.retry_count == 0
    actual = {
        (str(row["usage_date"]), row["resource_id"], row["resource_group"], row["currency"]):
        Decimal(str(row["pretax_cost"]))
        for row in first_records
    }
    assert actual.keys() == expected.keys()
    for key, cost in expected.items():
        # SQLite uses floating point; Cockroach's exact decimal checks are separate.
        assert actual[key].quantize(Decimal("1e-12")) == cost.quantize(Decimal("1e-12"))
    assert all(len(row["source_row_hash"]) == 64 for row in first_records)
    assert repository.fetch_run(first.run_id, **own_scope)["status"] == "completed"

    other = service.ingest("tenant-b", SUBSCRIPTION, DEFINITION)
    other_scope = {"tenant_id": "tenant-b", "subscription_id": SUBSCRIPTION}
    other_records = repository.fetch_records(other.run_id, **other_scope)
    assert other.run_id != first.run_id
    assert len(other_records) == len(expected)
    assert {row["id"] for row in first_records}.isdisjoint(row["id"] for row in other_records)
    assert repository.fetch_records(first.run_id, **other_scope) == []

    second = service.ingest("tenant-a", SUBSCRIPTION.upper(), DEFINITION)
    assert second == first
    assert repository.fetch_records(first.run_id, **own_scope) == first_records
    assert repository.fetch_records(other.run_id, **other_scope) == other_records
    with isolation_database.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM azure_cost_records")).scalar_one() == 2 * len(expected)
        assert connection.execute(text("SELECT count(*) FROM azure_cost_ingestion_runs")).scalar_one() == 2


@pytest.mark.parametrize(
    "token,subscription,status,code",
    [
        ("invalid-contract-token", SUBSCRIPTION, 401, "AuthenticationFailed"),
        ("jup054-forbidden-contract-token", SUBSCRIPTION, 403, "AuthorizationFailed"),
        (TOKEN, "missing-subscription", 404, "SubscriptionNotFound"),
    ],
)
def test_real_http_failure_marks_run_failed_without_touching_other_costs(
    ingestion_factory, isolation_database, token, subscription, status, code
):
    create, repository = ingestion_factory
    good = create().ingest("tenant-a", SUBSCRIPTION, DEFINITION)
    before = snapshot(isolation_database, "azure_cost_records")

    with pytest.raises(AzureCostHttpError) as failure:
        create(token).ingest("tenant-b", subscription, DEFINITION)

    assert (failure.value.status_code, failure.value.error_code) == (status, code)
    assert snapshot(isolation_database, "azure_cost_records") == before
    failed_id = ingestion_run_id("tenant-b", subscription, DEFINITION)
    failed = repository.fetch_run(failed_id, tenant_id="tenant-b", subscription_id=subscription)
    assert failed["status"] == "failed"
    assert failed["error_code"] == "AzureCostHttpError"
    assert (failed["row_count"], failed["page_count"], failed["retry_count"]) == (0, 0, 0)
    assert repository.fetch_records(failed_id, tenant_id="tenant-b", subscription_id=subscription) == []
    assert repository.fetch_run(good.run_id, tenant_id="tenant-a", subscription_id=SUBSCRIPTION)["status"] == "completed"
