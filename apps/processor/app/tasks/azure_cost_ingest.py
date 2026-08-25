from __future__ import annotations

import json
import logging
import uuid
from dataclasses import asdict, dataclass

from app.clients.azure_cost import AzureCostClient
from app.normalization.azure_cost import AzureCostNormalizer
from app.repositories.azure_cost import AzureCostRepository


logger = logging.getLogger(__name__)
RUN_NAMESPACE = uuid.UUID("7f921f96-d309-43df-b219-0b61dfe6864a")


class AzureCostIngestionScopeError(RuntimeError):
    """Reject an unsafe tenant or subscription before touching persistence."""


@dataclass(frozen=True)
class AzureCostIngestionSummary:
    run_id: str
    tenant_id: str
    subscription_id: str
    row_count: int
    page_count: int
    retry_count: int

    def to_dict(self) -> dict:
        return asdict(self)


class AzureCostIngestionService:
    def __init__(
        self,
        client: AzureCostClient,
        normalizer: AzureCostNormalizer,
        repository: AzureCostRepository,
    ):
        self.client = client
        self.normalizer = normalizer
        self.repository = repository

    def ingest(
        self,
        tenant_id: str,
        subscription_id: str,
        definition: dict,
    ) -> AzureCostIngestionSummary:
        tenant_id = _validated_scope("tenant_id", tenant_id)
        subscription_id = _validated_scope("subscription_id", subscription_id).casefold()
        run_id = ingestion_run_id(tenant_id, subscription_id, definition)
        self.repository.start_run(run_id, tenant_id, subscription_id, definition)
        _log(
            "azure_cost_persistence_started",
            run_id=run_id,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
        )
        try:
            query_result = self.client.query_all(subscription_id, definition)
            records = self.normalizer.normalize(query_result)
            self.repository.complete_run(
                run_id,
                tenant_id,
                subscription_id,
                records,
                page_count=query_result.page_count,
                retry_count=query_result.retry_count,
            )
        except Exception as exc:
            error_code = type(exc).__name__
            self.repository.fail_run(run_id, error_code)
            _log(
                "azure_cost_persistence_failed",
                error_code=error_code,
                run_id=run_id,
                tenant_id=tenant_id,
            )
            raise

        summary = AzureCostIngestionSummary(
            run_id=run_id,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            row_count=len(records),
            page_count=query_result.page_count,
            retry_count=query_result.retry_count,
        )
        _log("azure_cost_persistence_completed", **summary.to_dict())
        return summary


def ingestion_run_id(tenant_id: str, subscription_id: str, definition: dict) -> str:
    canonical = json.dumps(
        {
            "definition": definition,
            "subscriptionId": subscription_id.casefold(),
            "tenantId": tenant_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return str(uuid.uuid5(RUN_NAMESPACE, canonical))


def _log(event: str, **fields: object) -> None:
    logger.info(json.dumps({"event": event, **fields}, sort_keys=True))


def _validated_scope(name: str, value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise AzureCostIngestionScopeError(f"{name} must be a non-empty safe identifier")
    return value
