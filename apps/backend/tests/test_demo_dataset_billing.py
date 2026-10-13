"""JUP-119: the demo dataset, read by the real billing and detection code at the reference dates of the reference files."""
import csv
import importlib.util
import json
import sys
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.services import reference_date
from anomaly_episode_support import clear, episode_store
from billing_support import billing_schema, insert_cost, insert_run
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("economicon_demo_dataset_backend", ROOT / "scripts" / "demo_dataset.py")
dataset = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dataset
spec.loader.exec_module(dataset)
EXPECTED = json.loads((ROOT / "docs" / "demo" / "JUP-119" / "esperados-anomalias.json").read_text("utf-8"))
MANIFEST = json.loads(dataset.DEMO_MANIFEST_PATH.read_text("utf-8"))
pytestmark = pytest.mark.parametrize("tenant_database", ["cockroach"], indirect=True)
FIELDS = ("service", "start_date", "last_seen_date", "observation", "no_longer_observed_on", "reference_daily_cost",
          "accumulated_impact", "impact_day_count", "severity")


def stored_groups(tenant):
    """The records the ingestion stores for a tenant: the CSV rows summed by day, service, project and currency."""
    wanted = {pair["subscription"] for pair in MANIFEST["pairs"] if pair["tenant"] == tenant}
    groups = defaultdict(Decimal)
    with dataset.DEMO_PATH.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            if row["SubscriptionId"] in wanted:
                key = (row["SubscriptionId"], datetime.strptime(row["Date"], dataset.DATE_FORMAT).date(),
                       row["MeterCategory"] or None, dataset.project_of(row), row["BillingCurrencyCode"])
                groups[key] += Decimal(row["CostInBillingCurrency"])
    return groups


@pytest.fixture
def demo_tenant_a(episode_store, api):
    """Loads the rows of a demo tenant under tenant-a, which the test users belong to."""
    db = episode_store

    def load(source_tenant):
        with db.engine.begin() as connection:
            runs = set()
            for number, ((subscription, day, service, project, currency), cost) in enumerate(sorted(
                    stored_groups(source_tenant).items(), key=lambda item: str(item[0])), 1):
                if subscription not in runs:
                    insert_run(connection, "run-" + subscription, subscription=subscription)
                    runs.add(subscription)
                insert_cost(connection, f"demo-{number}", run="run-" + subscription, subscription=subscription,
                            day=day.isoformat(), cost=format(cost, "f"), currency=currency, service=service,
                            project=project, tags={"project": project} if project else {})
    yield api, load


@pytest.mark.parametrize("reference", sorted(EXPECTED["episodes_by_reference"]))
def test_one_detection_opens_the_episodes_of_the_reference_file(demo_tenant_a, reference):
    api, load = demo_tenant_a
    load("tenant-core")
    reference_date.configure(date.fromisoformat(reference))
    run = call(api, "POST", "/billing/anomalies/detect", headers=headers())
    assert run.status_code == 200, run.text
    wanted = EXPECTED["episodes_by_reference"][reference]
    assert run.json()["last_complete_day"] == wanted["last_evaluated_date"]
    listed = call(api, "GET", "/billing/anomalies/episodes?scope=all", headers=headers()).json()["episodes"]
    assert sorted(tuple(item[name] for name in FIELDS) for item in listed) == sorted(
        tuple(item[name] for name in FIELDS) for item in wanted["episodes"])


def test_the_calm_base_of_july_and_august_opens_no_episode(demo_tenant_a):
    api, load = demo_tenant_a
    load("tenant-core")
    reference_date.configure(date(2026, 8, 31))
    assert call(api, "POST", "/billing/anomalies/detect", headers=headers()).json()["opened"] == 0


def test_the_big_integer_is_read_by_billing_without_losing_a_cent(demo_tenant_a):
    api, load = demo_tenant_a
    load("tenant-growth")
    reference_date.configure(date(2026, 10, 30))
    body = call(api, "GET", "/billing/summary?start_date=2026-10-01&end_date=2026-11-01&group_by=service", headers=headers()).json()
    archive = [g for g in body["groups"] if g["value"] == "Archive"]
    assert [(g["currency"], g["cost"]) for g in archive] == [("USD", "9007199254740993.00")]


def test_the_usd_gap_and_the_recorded_zero_stay_distinguishable_in_billing(demo_tenant_a):
    api, load = demo_tenant_a
    load("tenant-growth")
    reference_date.configure(date(2026, 10, 30))

    def usd(month_start, month_end):
        body = call(api, "GET", f"/billing/summary?start_date={month_start}&end_date={month_end}", headers=headers()).json()
        return [item for item in body["totals"] if item["currency"] == "USD"]
    assert usd("2026-07-01", "2026-08-01") == []
    assert usd("2026-08-01", "2026-09-01") == [{"currency": "USD", "cost": "0.00", "record_count": 31}]
    assert usd("2026-09-01", "2026-10-01")[0]["record_count"] == sum(
        pair["stored_rows"] for pair in MANIFEST["pairs"] if pair["origin"] == "public-shifted")
