from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal

import pytest

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
from app.tasks.azure_cost_ingest import AzureCostIngestionService, ingestion_run_id


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
    assert normalized[0].dimensions == {"ResourceGroup": "rg-zero"}
    assert normalized[1].pretax_cost == Decimal("-1.25")
    assert normalized[1].currency == "USD"


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


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("PreTaxCost", "not-a-number"),
        ("Currency", ""),
        ("UsageDate", 20240231),
        ("UsageDate", "20240601"),
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


def test_service_persists_completed_run_and_structured_logs(caplog):
    repository = MemoryRepository()
    service = AzureCostIngestionService(
        SuccessClient(), AzureCostNormalizer(), repository
    )

    with caplog.at_level(logging.INFO):
        summary = service.ingest("tenant-demo", "subscription-demo", DEFINITION)

    assert summary.row_count == 1
    assert summary.page_count == 3
    assert summary.retry_count == 2
    assert repository.started[0][0] == summary.run_id
    assert repository.completed[0][0] == summary.run_id
    assert repository.completed[0][4:] == (3, 2)
    assert repository.failed == []
    events = [json.loads(record.message) for record in caplog.records]
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


def test_ingestion_run_id_is_stable_and_scoped():
    first = ingestion_run_id("tenant-a", "SUBSCRIPTION", DEFINITION)
    reordered = ingestion_run_id(
        "tenant-a", "subscription", {"dataset": {"granularity": "Daily"}, "type": "ActualCost"}
    )
    another_tenant = ingestion_run_id("tenant-b", "subscription", DEFINITION)

    assert first == reordered
    assert first != another_tenant
