"""Opt-in end to end check of the demo data path: generated CSV -> simulated API -> ingestion -> real CockroachDB.

Needs PROCESSOR_COCKROACH_TEST_URL as test_azure_cost_cockroach_integration.py does. The simulated API is started as a
subprocess from apps/azure-cost-api and scripts/demo_data.py runs as the operator would run it.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

import pytest
from sqlalchemy import text

from test_azure_cost_cockroach_integration import TEST_URL_ENV, database_factory  # noqa: F401

pytestmark = pytest.mark.skipif(
    not os.environ.get(TEST_URL_ENV),
    reason=f"set {TEST_URL_ENV} to opt in to disposable CockroachDB tests",
)
ROOT = Path(__file__).resolve().parents[3]
PROCESSOR = ROOT / "apps" / "processor"
API = ROOT / "apps" / "azure-cost-api"
SCRIPT = ROOT / "scripts" / "demo_data.py"


def load_dataset():
    spec = importlib.util.spec_from_file_location("economicon_demo_dataset_e2e", ROOT / "scripts" / "demo_dataset.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dataset = load_dataset()


@contextmanager
def simulated_api():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=API, env=dict(os.environ, AZURE_COST_DATASET_PATH=str(dataset.DEMO_PATH)),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1).read()
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("the simulated API did not start")
        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        process.wait(timeout=10)


def operator(command, url, api_url):
    env = dict(os.environ, DATABASE_URL=url, AZURE_COST_API_BASE_URL=api_url, RUNTIME_ENVIRONMENT="development",
               ALLOW_INSECURE_LOCAL_DATABASE="true", RABBITMQ_URL="amqp://probe:probepass9x@127.0.0.1:5672/",
               VECTOR_DATABASE_URL="postgresql://probe:probepass9x@127.0.0.1:5432/probe", PYTHONUTF8="1",
               PROCESSOR_APP_DIR=str(PROCESSOR))
    return subprocess.run([sys.executable, str(SCRIPT), command], env=env, capture_output=True, text=True, timeout=600)


def expected_totals():
    """Sums per tenant, month, currency, service and project from the CSV rows with exact decimals."""
    manifest = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))
    tenants = {pair["subscription"]: pair["tenant"] for pair in manifest["pairs"]}
    daily: dict[tuple, Decimal] = defaultdict(Decimal)
    with dataset.DEMO_PATH.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            day = datetime.strptime(row["Date"], dataset.DATE_FORMAT).date()
            daily[(tenants[row["SubscriptionId"]], day, row["BillingCurrencyCode"],
                   row["MeterCategory"] or None, dataset.project_of(row))] += Decimal(row["CostInBillingCurrency"])
    totals: dict[tuple, Decimal] = defaultdict(Decimal)
    for (tenant, day, currency, service, project), cost in daily.items():
        # The cost column keeps twelve decimals and the public rows carry fifteen, so each stored record is rounded.
        totals[(tenant, day.strftime("%Y-%m"), currency, service, project)] += cost.quantize(Decimal("1E-12"), rounding=ROUND_HALF_EVEN)
    return dict(totals)


def stored_totals(database):
    with database.engine.connect() as connection:
        rows = connection.execute(text(
            "SELECT tenant_id, to_char(usage_date, 'YYYY-MM') AS month, currency, service_name, project, "
            "sum(pretax_cost) AS cost FROM azure_cost_records GROUP BY 1, 2, 3, 4, 5")).mappings().all()
    return {(r["tenant_id"], r["month"], r["currency"], r["service_name"], r["project"]): Decimal(r["cost"]) for r in rows}


def counts(database):
    with database.engine.connect() as connection:
        return (connection.execute(text("SELECT count(*) FROM azure_cost_ingestion_runs")).scalar_one(),
                connection.execute(text("SELECT count(*) FROM azure_cost_records")).scalar_one())


def test_the_whole_path_loads_the_totals_of_the_file_and_is_repeatable_and_removable(database_factory):
    manifest = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))
    with database_factory() as database, simulated_api() as api_url:
        database.initialize()
        url = database.engine.url.render_as_string(hide_password=False)

        started = time.monotonic()
        loaded = operator("apply", url, api_url)
        print(f"complete load of {len(manifest['pairs'])} pairs: {time.monotonic() - started:.1f}s")
        assert loaded.returncode == 0, loaded.stdout + loaded.stderr
        assert "loaded" in loaded.stdout
        runs, records = counts(database)
        assert runs == len(manifest["pairs"])
        assert records == sum(pair["stored_rows"] for pair in manifest["pairs"])
        found, wanted = stored_totals(database), expected_totals()
        assert {k: v for k, v in found.items() if v != wanted.get(k)} == {}
        assert set(found) == set(wanted)
        assert found[("tenant-growth", "2026-10", "USD", "Archive", "Beta")] == Decimal("9007199254740993")

        again = operator("apply", url, api_url)
        assert again.returncode == 0 and "already-present" in again.stdout, again.stdout
        assert counts(database) == (runs, records)
        status = operator("status", url, api_url)
        assert "tenant-core: present" in status.stdout and "tenant-growth: present" in status.stdout

        with database.engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO azure_cost_ingestion_runs (id, tenant_id, subscription_id, request, status, started_at) "
                "VALUES ('foreign-run', 'tenant-core', 'foreign-subscription', '{}'::JSONB, 'completed', now())"))
        refused = operator("remove", url, api_url)
        assert refused.returncode == 0
        assert counts(database) == (1, 0)
        blocked = operator("apply", url, api_url)
        assert blocked.returncode == 2 and "other-data" in blocked.stdout
        assert counts(database) == (1, 0)

        with database.engine.begin() as connection:
            connection.execute(text("DELETE FROM azure_cost_ingestion_runs WHERE id = 'foreign-run'"))
        assert operator("apply", url, api_url).returncode == 0
        assert operator("remove", url, api_url).returncode == 0
        assert counts(database) == (0, 0)
        assert operator("remove", url, api_url).returncode == 0
        assert counts(database) == (0, 0)
