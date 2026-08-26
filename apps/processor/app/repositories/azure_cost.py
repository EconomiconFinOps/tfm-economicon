from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import text

from app.db.database import Database
from app.normalization.azure_cost import NormalizedCostRecord


RECORD_NAMESPACE = uuid.UUID("df31a3dd-cff7-4018-9f34-0baeb3f53250")


class AzureCostRepository(Protocol):
    def start_run(
        self,
        run_id: str,
        tenant_id: str,
        subscription_id: str,
        definition: dict,
    ) -> None: ...

    def complete_run(
        self,
        run_id: str,
        tenant_id: str,
        subscription_id: str,
        records: tuple[NormalizedCostRecord, ...],
        *,
        page_count: int,
        retry_count: int,
    ) -> None: ...

    def fail_run(self, run_id: str, error_code: str) -> None: ...


class SqlAzureCostRepository:
    def __init__(self, database: Database):
        self.database = database

    def start_run(
        self,
        run_id: str,
        tenant_id: str,
        subscription_id: str,
        definition: dict,
    ) -> None:
        now = datetime.now(timezone.utc)
        with self.database.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO azure_cost_ingestion_runs (
                        id, tenant_id, subscription_id, request, status,
                        page_count, retry_count, row_count, error_code,
                        started_at, completed_at
                    ) VALUES (
                        :id, :tenant_id, :subscription_id, :request, 'running',
                        0, 0, 0, NULL, :started_at, NULL
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        status = 'running',
                        page_count = 0,
                        retry_count = 0,
                        row_count = 0,
                        error_code = NULL,
                        started_at = excluded.started_at,
                        completed_at = NULL
                    """
                ),
                {
                    "id": run_id,
                    "tenant_id": tenant_id,
                    "subscription_id": subscription_id,
                    "request": json.dumps(definition, sort_keys=True),
                    "started_at": now,
                },
            )

    def complete_run(
        self,
        run_id: str,
        tenant_id: str,
        subscription_id: str,
        records: tuple[NormalizedCostRecord, ...],
        *,
        page_count: int,
        retry_count: int,
    ) -> None:
        now = datetime.now(timezone.utc)
        with self.database.engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM azure_cost_records
                    WHERE ingestion_id = :run_id
                      AND tenant_id = :tenant_id
                      AND subscription_id = :subscription_id
                    """
                ),
                {
                    "run_id": run_id,
                    "tenant_id": tenant_id,
                    "subscription_id": subscription_id,
                },
            )
            for index, record in enumerate(records):
                record_id = str(
                    uuid.uuid5(
                        RECORD_NAMESPACE,
                        f"{run_id}:{index}:{record.source_row_hash}",
                    )
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO azure_cost_records (
                            id, ingestion_id, tenant_id, subscription_id,
                            usage_date, pretax_cost, currency,
                            billing_account_id, subscription_name,
                            resource_group, service_name, project,
                            consumed_quantity, consumed_unit, tags, dimensions,
                            source_row_hash, created_at
                        ) VALUES (
                            :id, :ingestion_id, :tenant_id, :subscription_id,
                            :usage_date, :pretax_cost, :currency,
                            :billing_account_id, :subscription_name,
                            :resource_group, :service_name, :project,
                            :consumed_quantity, :consumed_unit, :tags, :dimensions,
                            :source_row_hash, :created_at
                        )
                        """
                    ),
                    {
                        "id": record_id,
                        "ingestion_id": run_id,
                        "tenant_id": tenant_id,
                        "subscription_id": subscription_id,
                        "usage_date": record.usage_date,
                        "pretax_cost": record.pretax_cost,
                        "currency": record.currency,
                        "billing_account_id": record.billing_account_id,
                        "subscription_name": record.subscription_name,
                        "resource_group": record.resource_group,
                        "service_name": record.service_name,
                        "project": record.project,
                        "consumed_quantity": record.consumed_quantity,
                        "consumed_unit": record.consumed_unit,
                        "tags": json.dumps(record.tags, sort_keys=True),
                        "dimensions": json.dumps(record.dimensions, sort_keys=True),
                        "source_row_hash": record.source_row_hash,
                        "created_at": now,
                    },
                )
            connection.execute(
                text(
                    """
                    UPDATE azure_cost_ingestion_runs
                    SET status = 'completed',
                        page_count = :page_count,
                        retry_count = :retry_count,
                        row_count = :row_count,
                        error_code = NULL,
                        completed_at = :completed_at
                    WHERE id = :run_id
                      AND tenant_id = :tenant_id
                      AND subscription_id = :subscription_id
                    """
                ),
                {
                    "run_id": run_id,
                    "tenant_id": tenant_id,
                    "subscription_id": subscription_id,
                    "page_count": page_count,
                    "retry_count": retry_count,
                    "row_count": len(records),
                    "completed_at": now,
                },
            )

    def fail_run(self, run_id: str, error_code: str) -> None:
        with self.database.engine.begin() as connection:
            connection.execute(
                text("DELETE FROM azure_cost_records WHERE ingestion_id = :run_id"),
                {"run_id": run_id},
            )
            connection.execute(
                text(
                    """
                    UPDATE azure_cost_ingestion_runs
                    SET status = 'failed',
                        page_count = 0,
                        retry_count = 0,
                        row_count = 0,
                        error_code = :error_code,
                        completed_at = :completed_at
                    WHERE id = :run_id
                    """
                ),
                {
                    "run_id": run_id,
                    "error_code": error_code,
                    "completed_at": datetime.now(timezone.utc),
                },
            )

    def fetch_run(self, run_id: str) -> dict | None:
        with self.database.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, tenant_id, subscription_id, status,
                           page_count, retry_count, row_count, error_code
                    FROM azure_cost_ingestion_runs
                    WHERE id = :run_id
                    """
                ),
                {"run_id": run_id},
            ).mappings().first()
        return dict(row) if row else None

    def fetch_records(self, run_id: str) -> list[dict]:
        with self.database.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, usage_date, pretax_cost, currency,
                           billing_account_id, subscription_name,
                           resource_group, service_name, project,
                           consumed_quantity, consumed_unit, tags,
                           dimensions, source_row_hash
                    FROM azure_cost_records
                    WHERE ingestion_id = :run_id
                    ORDER BY usage_date, id
                    """
                ),
                {"run_id": run_id},
            ).mappings()
            return [dict(row) for row in rows]
