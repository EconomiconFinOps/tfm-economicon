from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal

import pytest

from app.core.logging import configure_logging
from app.clients.azure_cost import (
    AzureCostHttpError,
    AzureCostQueryResult,
    CostColumn,
)
from app.normalization.azure_cost import (
    AzureCostNormalizationError,
    AzureCostNormalizer,
    NormalizedCostRecord,
)
from app.tasks.azure_cost_ingest import (
    AzureCostIngestionScopeError,
    AzureCostIngestionService,
    ingestion_run_id,
)


DEFINITION = {"type": "ActualCost", "dataset": {"granularity": "Daily"}}
COLUMNS = (
    CostColumn("PreTaxCost", "Number"),
    CostColumn("Currency", "String"),
    CostColumn("UsageDate", "Number"),
    CostColumn("ResourceGroup", "String"),
)


def result(*rows: dict, page_count: int = 1, retry_count: int = 0):
    return AzureCostQueryResult(
        columns=COLUMNS,
        rows=tuple(rows),
        page_count=page_count,
        retry_count=retry_count,
    )


def test_normalizer_preserves_zero_negative_cost_and_dimensions():
    normalized = AzureCostNormalizer().normalize(
        result(
            {
                "PreTaxCost": 0,
                "Currency": " eur ",
                "UsageDate": 20240601,
                "ResourceGroup": "rg-zero",
            },
            {
                "PreTaxCost": -1.25,
                "Currency": "usd",
                "UsageDate": 20240602,
                "ResourceGroup": "rg-credit",
            },
        )
    )

    assert normalized[0].pretax_cost == Decimal("0")
    assert normalized[0].currency == "EUR"
    assert normalized[0].usage_date.isoformat() == "2024-06-01"
    assert normalized[0].resource_group == "rg-zero"
    assert normalized[0].dimensions == {}
    assert normalized[1].pretax_cost == Decimal("-1.25")
    assert normalized[1].currency == "USD"


def test_normalizer_promotes_finops_dimensions_consumption_and_tags():
    record = AzureCostNormalizer().normalize(
        result(
            {
                "PreTaxCost": 12.5,
                "Currency": "eur",
                "UsageDate": 20240601,
                "BillingAccountId": " billing-demo ",
                "SubscriptionName": " Ecommerce Prod ",
                "ResourceGroup": " RG-App ",
                "ServiceName": " Storage ",
                "Quantity": 3.25,
                "UnitOfMeasure": " GB/Month ",
                "Tags": '"CostCenter": "1234","Owner Team": "Platform"',
                "Project": "Jupiter",
                "ResourceLocation": " westeurope ",
            }
        )
    )[0]

    assert record.billing_account_id == "billing-demo"
    assert record.subscription_name == "Ecommerce Prod"
    assert record.resource_group == "RG-App"
    assert record.service_name == "Storage"
    assert record.project == "Jupiter"
    assert record.consumed_quantity == Decimal("3.25")
    assert record.consumed_unit == "GB/Month"
    assert record.tags == {
        "cost_center": "1234",
        "owner_team": "Platform",
        "project": "Jupiter",
    }
    assert record.dimensions == {"ResourceLocation": "westeurope"}


def test_normalizer_hash_is_deterministic():
    source = result(
        {
            "PreTaxCost": 4.2,
            "Currency": "EUR",
            "UsageDate": 20240601,
            "ResourceGroup": "rg-demo",
        }
    )

    first = AzureCostNormalizer().normalize(source)[0]
    second = AzureCostNormalizer().normalize(source)[0]

    assert first.source_row_hash == second.source_row_hash
    assert len(first.source_row_hash) == 64


def test_normalizer_hash_ignores_equivalent_cost_and_currency_representations():
    first = AzureCostNormalizer().normalize(
        result({"PreTaxCost": 1, "Currency": "eur", "UsageDate": 20240601})
    )[0]
    second = AzureCostNormalizer().normalize(
        result({"PreTaxCost": 1.0, "Currency": " EUR ", "UsageDate": 20240601})
    )[0]

    assert first.source_row_hash == second.source_row_hash


def test_normalizer_hash_ignores_equivalent_finops_aliases():
    first = AzureCostNormalizer().normalize(
        result(
            {
                "PreTaxCost": 1,
                "Currency": "EUR",
                "MeterCategory": "Storage",
                "Quantity": 2,
                "UnitOfMeasure": "GB",
            }
        )
    )[0]
    second = AzureCostNormalizer().normalize(
        result(
            {
                "PreTaxCost": 1.0,
                "Currency": "EUR",
                "ServiceName": "Storage",
                "ConsumedQuantity": 2.0,
                "ConsumedUnit": "GB",
            }
        )
    )[0]

    assert first == second
    assert first.source_row_hash == second.source_row_hash


@pytest.mark.parametrize(
    "row",
    [
        {
            "PreTaxCost": 1,
            "Currency": "EUR",
            "ConsumedQuantity": 2,
        },
        {
            "PreTaxCost": 1,
            "Currency": "EUR",
            "ConsumedUnit": "GB",
        },
    ],
)
def test_normalizer_requires_quantity_and_unit_together(row):
    with pytest.raises(AzureCostNormalizationError, match="supplied together"):
        AzureCostNormalizer().normalize(result(row))


def test_normalizer_rejects_conflicting_aliases_and_tags():
    with pytest.raises(AzureCostNormalizationError, match="Conflicting aliases"):
        AzureCostNormalizer().normalize(
            result(
                {
                    "PreTaxCost": 1,
                    "Currency": "EUR",
                    "ServiceName": "Storage",
                    "MeterCategory": "Compute",
                }
            )
        )

    with pytest.raises(AzureCostNormalizationError, match="tag project"):
        AzureCostNormalizer().normalize(
            result(
                {
                    "PreTaxCost": 1,
                    "Currency": "EUR",
                    "Tags": '{"Project":"Jupiter"}',
                    "Project": "Another",
                }
            )
        )


def test_normalizer_allows_missing_usage_date_and_preserves_empty_result():
    record = AzureCostNormalizer().normalize(
        result({"PreTaxCost": -0.0, "Currency": "EUR"})
    )[0]

    assert record.usage_date is None
    assert record.pretax_cost == Decimal("0")
    assert AzureCostNormalizer().normalize(result()) == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("PreTaxCost", "not-a-number"),
        ("PreTaxCost", "12.5"),
        ("PreTaxCost", True),
        ("PreTaxCost", float("nan")),
        ("PreTaxCost", float("inf")),
        ("Currency", ""),
        ("Currency", "EU"),
        ("Currency", "EU4"),
        ("Currency", "ÉUR"),
        ("UsageDate", 20240231),
        ("UsageDate", "20240601"),
        ("UsageDate", 2024061),
        ("UsageDate", True),
    ],
)
def test_normalizer_rejects_invalid_values(field, value):
    row = {
        "PreTaxCost": 1.0,
        "Currency": "EUR",
        "UsageDate": 20240601,
        "ResourceGroup": "rg-demo",
    }
    row[field] = value

    with pytest.raises(AzureCostNormalizationError):
        AzureCostNormalizer().normalize(result(row))


@dataclass
class MemoryRepository:
    started: list[tuple] = field(default_factory=list)
    completed: list[tuple] = field(default_factory=list)
    failed: list[tuple] = field(default_factory=list)

    def start_run(self, run_id, tenant_id, subscription_id, definition):
        self.started.append((run_id, tenant_id, subscription_id, definition))

    def complete_run(
        self,
        run_id,
        tenant_id,
        subscription_id,
        records,
        *,
        page_count,
        retry_count,
    ):
        self.completed.append(
            (
                run_id,
                tenant_id,
                subscription_id,
                records,
                page_count,
                retry_count,
            )
        )

    def fail_run(self, run_id, error_code):
        self.failed.append((run_id, error_code))


class SuccessClient:
    def query_all(self, subscription_id, definition):
        assert subscription_id == "subscription-demo"
        assert definition == DEFINITION
        return result(
            {
                "PreTaxCost": 12.5,
                "Currency": "EUR",
                "UsageDate": 20240601,
                "ResourceGroup": "rg-demo",
            },
            page_count=3,
            retry_count=2,
        )


class FailureClient:
    def query_all(self, subscription_id, definition):
        raise AzureCostHttpError(401, "Unauthorized")


class InvalidRowClient:
    def query_all(self, subscription_id, definition):
        return result({"PreTaxCost": 1.0, "Currency": "NOT-A-CURRENCY"})


def test_service_persists_completed_run_and_structured_logs(capsys):
    configure_logging()
    repository = MemoryRepository()
    service = AzureCostIngestionService(
        SuccessClient(), AzureCostNormalizer(), repository
    )

    summary = service.ingest("tenant-demo", "subscription-demo", DEFINITION)

    assert summary.row_count == 1
    assert summary.page_count == 3
    assert summary.retry_count == 2
    assert repository.started[0][0] == summary.run_id
    assert repository.completed[0][0] == summary.run_id
    assert repository.completed[0][4:] == (3, 2)
    assert repository.failed == []

    captured = capsys.readouterr().out
    events = [
        json.loads(line)
        for line in captured.strip().splitlines()
        if line.strip()
    ]
    events = [
        event for event in events if event["logger"] == "app.tasks.azure_cost_ingest"
    ]
    assert [event["event"] for event in events] == [
        "azure_cost_persistence_started",
        "azure_cost_persistence_completed",
    ]
    assert "token" not in json.dumps(events).lower()


def test_service_marks_failed_run_and_rethrows():
    repository = MemoryRepository()
    service = AzureCostIngestionService(
        FailureClient(), AzureCostNormalizer(), repository
    )

    with pytest.raises(AzureCostHttpError):
        service.ingest("tenant-demo", "subscription-demo", DEFINITION)

    assert repository.completed == []
    assert repository.failed == [
        (repository.started[0][0], "AzureCostHttpError")
    ]


def test_service_marks_normalization_failure_without_partial_records():
    repository = MemoryRepository()
    service = AzureCostIngestionService(
        InvalidRowClient(), AzureCostNormalizer(), repository
    )

    with pytest.raises(AzureCostNormalizationError):
        service.ingest("tenant-demo", "subscription-demo", DEFINITION)

    assert repository.completed == []
    assert repository.failed == [
        (repository.started[0][0], "AzureCostNormalizationError")
    ]


@pytest.mark.parametrize(
    ("tenant_id", "subscription_id"),
    [
        ("", "subscription-demo"),
        (" tenant-demo", "subscription-demo"),
        ("tenant-demo\nother", "subscription-demo"),
        ("tenant-demo", ""),
        ("tenant-demo", " subscription-demo "),
        ("tenant-demo", "subscription\x7fdemo"),
    ],
)
def test_service_rejects_unsafe_scope_before_persistence(tenant_id, subscription_id):
    repository = MemoryRepository()
    service = AzureCostIngestionService(
        SuccessClient(), AzureCostNormalizer(), repository
    )

    with pytest.raises(AzureCostIngestionScopeError):
        service.ingest(tenant_id, subscription_id, DEFINITION)

    assert repository.started == []
    assert repository.completed == []
    assert repository.failed == []


def test_service_normalizes_subscription_case_before_persistence():
    repository = MemoryRepository()
    service = AzureCostIngestionService(
        SuccessClient(), AzureCostNormalizer(), repository
    )

    summary = service.ingest("tenant-demo", "SUBSCRIPTION-DEMO", DEFINITION)

    assert summary.subscription_id == "subscription-demo"
    assert repository.started[0][2] == "subscription-demo"


def test_ingestion_run_id_is_stable_and_scoped():
    first = ingestion_run_id("tenant-a", "SUBSCRIPTION", DEFINITION)
    reordered = ingestion_run_id(
        "tenant-a", "subscription", {"dataset": {"granularity": "Daily"}, "type": "ActualCost"}
    )
    another_tenant = ingestion_run_id("tenant-b", "subscription", DEFINITION)

    assert first == reordered
    assert first != another_tenant
