#!/usr/bin/env python3
"""Demo cost dataset in the Azure cost export format: pure generators, no database, no network, no clock.

The public rows are the 50 rows of EA-Cost-Actual.sample.csv with only their date columns shifted. Every other row is
synthetic, is not an Azure invoice and does not come from the public dataset. All rows fall in one common window.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SOURCE = ROOT / "fixtures" / "azure-cost" / "EA-Cost-Actual.sample.csv"
DERIVED_DIR = ROOT / "fixtures" / "azure-cost" / "derived"
DERIVED_PATH = DERIVED_DIR / "EA-Cost-Actual.shifted-2026-09.sample.csv"
DERIVED_MANIFEST_PATH = DERIVED_DIR / "manifest.json"
DEMO_DIR = ROOT / "fixtures" / "azure-cost" / "demo"
DEMO_PATH = DEMO_DIR / "demo-cost.csv"
DEMO_MANIFEST_PATH = DEMO_DIR / "manifest.json"

GENERATOR_VERSION = 1
WINDOW_START = date(2026, 7, 1)
WINDOW_END = date(2026, 10, 30)
PUBLIC_FIRST_DAY = date(2024, 6, 1)
SHIFTED_FIRST_DAY = date(2026, 9, 1)
SHIFT_DAYS = (SHIFTED_FIRST_DAY - PUBLIC_FIRST_DAY).days
DATE_COLUMNS = ("Date", "BillingPeriodStartDate", "BillingPeriodEndDate")
DATE_FORMAT = "%m/%d/%Y"
PREFIX = "synthetic-"
TENANT_CORE = "tenant-core"
TENANT_GROWTH = "tenant-growth"
ANOMALIES_SUBSCRIPTION = PREFIX + "anomalies"
GROWTH_EUR_SUBSCRIPTION = PREFIX + "growth-eur"
GROWTH_USD_SUBSCRIPTION = PREFIX + "growth-usd"
ORIGIN_PUBLIC = "public-shifted"
ORIGIN_SYNTHETIC = "synthetic"
# The query API groups by two fields at most; the demo carries the service and the Project tag.
GROUPING = (("Dimension", "ServiceName"), ("Tag", "Project"))
ABSENT_FIELDS = ("resource_group", "cost_center", "owner", "application", "environment")
BIG_INTEGER = "9007199254740993"

HEADER = (
    "InvoiceSectionName", "AccountName", "AccountOwnerId", "SubscriptionId", "SubscriptionName", "ResourceGroup",
    "ResourceLocation", "Date", "ProductName", "MeterCategory", "MeterSubCategory", "MeterId", "MeterName",
    "MeterRegion", "UnitOfMeasure", "Quantity", "EffectivePrice", "CostInBillingCurrency", "CostCenter",
    "ConsumedService", "ResourceId", "Tags", "OfferId", "AdditionalInfo", "ServiceInfo1", "ServiceInfo2",
    "ResourceName", "ReservationId", "ReservationName", "UnitPrice", "ProductOrderId", "ProductOrderName", "Term",
    "PublisherType", "PublisherName", "ChargeType", "Frequency", "PricingModel", "AvailabilityZone",
    "BillingAccountId", "BillingAccountName", "BillingCurrencyCode", "BillingPeriodStartDate",
    "BillingPeriodEndDate", "BillingProfileId", "BillingProfileName", "InvoiceSectionId", "IsAzureCreditEligible",
    "PartNumber", "PayGPrice", "PlanName", "ServiceFamily", "CostAllocationRuleName", "benefitId", "benefitName",
)

# Daily EUR cost per service for 2026-09-01 to 2026-09-21; None is no record; weeks one and two keep the JUP-030 totals.
SEPTEMBER = {
    "Compute": ["140"] * 5 + ["150"] * 2 + ["140"] + ["377"] * 4 + ["376"] * 2 + ["377"] * 7,
    "Analytics": ["314"] * 5 + ["315"] * 2 + ["303", "303", "480", "303", "303", "304", "304"] + ["305"] * 7,
    "Storage": ["114"] * 6 + ["116"] + ["117"] * 6 + ["118"] + ["117"] * 7,
    "Database": ["214"] * 5 + ["215"] * 2 + ["171"] * 4 + ["172"] * 3 + ["171", "300", "300", "300", "300", "300", "171"],
    "Tools": ["1"] * 4 + ["2"] * 3 + ["5"] * 2 + ["6"] * 5 + ["6"] * 7,
    "Backup": ["0"] * 7 + ["0", "0", "300", "0", "0", "0", "0"] + ["0"] * 7,
    "Networking": [None] * 13 + ["600"] + ["85"] * 7,
}
SEPTEMBER_FIRST_DAY = date(2026, 9, 1)
# 2026-09-22 to 2026-10-30: Compute falls back on 10-04, Storage rises on 10-20, Tools spikes once on 10-08.
EXTENSION_DAYS = 39
EXTENSION = {
    "Compute": ["377"] * 12 + ["140"] * 27,
    "Analytics": ["305"] * 39,
    "Storage": ["117"] * 28 + ["240"] * 11,
    "Database": ["171"] * 39,
    "Tools": ["6"] * 16 + ["150"] + ["6"] * 22,
    "Backup": ["0"] * 39,
    "Networking": ["85"] * 39,
}

# (service, project, daily base in EUR); the cost grows 8 % a month and drops 20 % on weekends.
GROWTH_SERVICES = (("Compute", "Alpha", 300), ("Storage", "Beta", 120), ("Database", "Alpha", 180), ("Networking", "Beta", 60))
CREDIT_DAY = date(2026, 8, 15)
UNLABELLED_SERVICE_DAY = date(2026, 9, 3)
RECORDED_ZERO_MONTH = 8
CLOSING_USD_MONTH = 10


def days(first: date, last: date) -> Iterable[date]:
    for offset in range((last - first).days + 1):
        yield first + timedelta(days=offset)


def month_bounds(day: date) -> tuple[date, date]:
    first = day.replace(day=1)
    following = first.replace(year=first.year + 1, month=1) if first.month == 12 else first.replace(month=first.month + 1)
    return first, following - timedelta(days=1)


def blank_row() -> dict[str, str]:
    return {name: "" for name in HEADER}


def tag_text(project: str | None) -> str:
    return "" if project is None else f'"Project": "{project}"'


def synthetic_row(subscription: str, day: date, cost: str, currency: str, service: str, project: str | None) -> dict[str, str]:
    first, last = month_bounds(day)
    row = blank_row()
    row.update({
        "SubscriptionId": subscription, "SubscriptionName": subscription, "Date": day.strftime(DATE_FORMAT),
        "CostInBillingCurrency": cost, "BillingCurrencyCode": currency, "MeterCategory": service,
        "Tags": tag_text(project), "ResourceId": f"/subscriptions/{subscription}/synthetic/{service or 'none'}",
        "BillingPeriodStartDate": first.strftime(DATE_FORMAT), "BillingPeriodEndDate": last.strftime(DATE_FORMAT),
    })
    return row


def anomaly_levels() -> dict[str, list[str | None]]:
    """Per service, one value for every day of the window: calm base, then September, then the extension."""
    september_days = (SEPTEMBER_FIRST_DAY - WINDOW_START).days
    levels: dict[str, list[str | None]] = {}
    for service, values in SEPTEMBER.items():
        base = values[0]
        levels[service] = [base] * september_days + values + EXTENSION[service]
    return levels


def anomaly_rows() -> list[dict[str, str]]:
    rows = []
    for service, values in anomaly_levels().items():
        for day, value in zip(days(WINDOW_START, WINDOW_END), values):
            if value is not None:
                rows.append(synthetic_row(ANOMALIES_SUBSCRIPTION, day, value + ".00", "EUR", service, "Demo"))
    return rows


def growth_cents(base: int, day: date) -> int:
    month = day.month - WINDOW_START.month
    weekend = 80 if day.weekday() >= 5 else 100
    return base * 100 * (100 + 8 * month) * weekend // 10000


def money(cents: int) -> str:
    return f"{Decimal(cents) / 100:.2f}"


def growth_eur_rows() -> list[dict[str, str]]:
    rows = []
    for day in days(WINDOW_START, WINDOW_END):
        for service, project, base in GROWTH_SERVICES:
            unlabelled = service == "Networking" and day.toordinal() % 7 == 0
            rows.append(synthetic_row(GROWTH_EUR_SUBSCRIPTION, day, money(growth_cents(base, day)), "EUR", service,
                                      None if unlabelled else project))
    rows.append(synthetic_row(GROWTH_EUR_SUBSCRIPTION, CREDIT_DAY, "-250.00", "EUR", "Credits", "Beta"))
    rows.append(synthetic_row(GROWTH_EUR_SUBSCRIPTION, UNLABELLED_SERVICE_DAY, "12.50", "EUR", "", "Alpha"))
    return rows


def growth_usd_rows() -> list[dict[str, str]]:
    """July has no USD record, August a recorded zero every day, September only the public rows, October costs."""
    rows = []
    for day in days(WINDOW_START, WINDOW_END):
        if day.month == RECORDED_ZERO_MONTH:
            rows.append(synthetic_row(GROWTH_USD_SUBSCRIPTION, day, "0.00", "USD", "Compute", "Alpha"))
        elif day.month == CLOSING_USD_MONTH:
            rows.append(synthetic_row(GROWTH_USD_SUBSCRIPTION, day, f"{25 + day.day % 7}.25", "USD", "Storage", "Beta"))
    rows.append(synthetic_row(GROWTH_USD_SUBSCRIPTION, date(2026, 10, 3), BIG_INTEGER, "USD", "Archive", "Beta"))
    return rows


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        return list(reader.fieldnames or []), list(reader)


def shift_public_rows(rows: Iterable[dict[str, str]], shift_days: int = SHIFT_DAYS) -> list[dict[str, str]]:
    shifted = []
    for row in rows:
        copy = dict(row)
        for column in DATE_COLUMNS:
            if copy[column]:
                moved = datetime.strptime(copy[column], DATE_FORMAT).date() + timedelta(days=shift_days)
                copy[column] = moved.strftime(DATE_FORMAT)
        shifted.append(copy)
    return shifted


def public_shifted_rows() -> list[dict[str, str]]:
    return shift_public_rows(read_rows(PUBLIC_SOURCE)[1])


def sort_key(row: dict[str, str]) -> tuple:
    return (row["SubscriptionId"], datetime.strptime(row["Date"], DATE_FORMAT), row["MeterCategory"], row["Tags"],
            row["BillingCurrencyCode"], row["CostInBillingCurrency"], row["ResourceId"])


def render_csv(rows: Iterable[dict[str, str]], ordered: bool = False) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(HEADER), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows if ordered else sorted(rows, key=sort_key))
    return buffer.getvalue().encode("utf-8")


def demo_rows() -> list[dict[str, str]]:
    return public_shifted_rows() + anomaly_rows() + growth_eur_rows() + growth_usd_rows()


def subscription_pairs() -> list[dict[str, str]]:
    pairs = [
        {"tenant": TENANT_CORE, "subscription": ANOMALIES_SUBSCRIPTION, "origin": ORIGIN_SYNTHETIC},
        {"tenant": TENANT_GROWTH, "subscription": GROWTH_EUR_SUBSCRIPTION, "origin": ORIGIN_SYNTHETIC},
        {"tenant": TENANT_GROWTH, "subscription": GROWTH_USD_SUBSCRIPTION, "origin": ORIGIN_SYNTHETIC},
    ]
    public = sorted({row["SubscriptionId"] for row in public_shifted_rows()})
    return pairs + [{"tenant": TENANT_GROWTH, "subscription": item, "origin": ORIGIN_PUBLIC} for item in public]


def checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def render_json(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def derived_manifest(content: bytes, row_count: int) -> dict:
    return {
        "schema_version": 1, "kind": "derived", "source_fixture": "fixtures/azure-cost/EA-Cost-Actual.sample.csv",
        "transformation": "The columns " + ", ".join(DATE_COLUMNS) + " are shifted by a fixed number of days; every other value is the public value.",
        "shift_days": SHIFT_DAYS, "shifted_first_day": SHIFTED_FIRST_DAY.isoformat(),
        "path": DERIVED_PATH.name, "rows": row_count, "sha256": checksum(content),
    }


def project_of(row: dict[str, str]) -> str | None:
    if not row["Tags"]:
        return None
    return next((value for key, value in json.loads("{" + row["Tags"] + "}").items() if key.lower() == "project"), None)


def demo_manifest(content: bytes, rows: list[dict[str, str]]) -> dict:
    counts: dict[str, int] = {}
    groups: dict[str, set] = {}
    for row in rows:
        counts[row["SubscriptionId"]] = counts.get(row["SubscriptionId"], 0) + 1
        # The query API sums the rows of one day, service, project and currency into one stored record.
        groups.setdefault(row["SubscriptionId"], set()).add(
            (row["Date"], row["MeterCategory"], project_of(row), row["BillingCurrencyCode"]))
    pairs = [{**pair, "rows": counts[pair["subscription"]], "stored_rows": len(groups[pair["subscription"]])}
             for pair in subscription_pairs()]
    return {
        "schema_version": 1, "generator_version": GENERATOR_VERSION, "path": DEMO_PATH.name,
        "rows": len(rows), "sha256": checksum(content),
        "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
        "public_shift_days": SHIFT_DAYS,
        "grouping": [{"type": kind, "name": name} for kind, name in GROUPING],
        "absent_fields": list(ABSENT_FIELDS),
        "pairs": pairs,
    }


def ingestion_definition() -> dict:
    return {
        "type": "ActualCost", "timeframe": "Custom",
        "timePeriod": {"from": WINDOW_START.isoformat() + "T00:00:00Z",
                       "to": (WINDOW_END + timedelta(days=1)).isoformat() + "T00:00:00Z"},
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
            "grouping": [{"type": kind, "name": name} for kind, name in GROUPING],
        },
    }


def generate() -> dict[Path, bytes]:
    """Every versioned output of the generator, by path."""
    public = public_shifted_rows()
    derived = render_csv(public, ordered=True)
    rows = demo_rows()
    demo = render_csv(rows)
    return {
        DERIVED_PATH: derived,
        DERIVED_MANIFEST_PATH: render_json(derived_manifest(derived, len(public))),
        DEMO_PATH: demo,
        DEMO_MANIFEST_PATH: render_json(demo_manifest(demo, rows)),
        DEMO_DIR / "ingestion-definition.json": render_json(ingestion_definition()),
    }


def write_all() -> list[Path]:
    outputs = generate()
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return sorted(outputs)


if __name__ == "__main__":
    for written in write_all():
        print(written.relative_to(ROOT).as_posix())
