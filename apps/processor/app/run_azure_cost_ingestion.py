from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.clients.azure_cost import AzureCostClient, AzureCostClientError
from app.core.config import Settings
from app.core.logging import configure_logging
from app.db.database import Database
from app.normalization.azure_cost import AzureCostNormalizer, AzureCostNormalizationError
from app.repositories.azure_cost import SqlAzureCostRepository
from app.tasks.azure_cost_ingest import AzureCostIngestionService


DEFAULT_DEFINITION = {
    "type": "ActualCost",
    "timeframe": "Custom",
    "timePeriod": {
        "from": "2024-06-01T00:00:00Z",
        "to": "2024-06-20T00:00:00Z",
    },
    "dataset": {
        "granularity": "Daily",
        "aggregation": {
            "totalCost": {"name": "PreTaxCost", "function": "Sum"}
        },
        "grouping": [{"type": "Dimension", "name": "ResourceGroup"}],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Azure Cost data into CockroachDB")
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--subscription-id", required=True)
    parser.add_argument("--definition-file", type=Path)
    return parser.parse_args()


def load_definition(path: Path | None) -> dict:
    if path is None:
        return DEFAULT_DEFINITION
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    configure_logging()
    settings = Settings()
    database = Database(settings.database_url)
    repository = SqlAzureCostRepository(database)
    try:
        database.initialize()
        service = AzureCostIngestionService(
            AzureCostClient(settings),
            AzureCostNormalizer(),
            repository,
        )
        summary = service.ingest(
            args.tenant_id,
            args.subscription_id,
            load_definition(args.definition_file),
        )
        persisted_run = repository.fetch_run(summary.run_id)
        persisted_records = repository.fetch_records(summary.run_id)
        if not persisted_run or persisted_run["status"] != "completed":
            raise RuntimeError("Persisted ingestion run is not completed")
        if len(persisted_records) != summary.row_count:
            raise RuntimeError("Persisted row count does not match ingestion result")
        print(
            json.dumps(
                {
                    **summary.to_dict(),
                    "persisted_row_count": len(persisted_records),
                    "status": "completed",
                },
                sort_keys=True,
            )
        )
        return 0
    except (AzureCostClientError, AzureCostNormalizationError) as exc:
        print(json.dumps({"error_code": type(exc).__name__, "status": "failed"}))
        return 1
    finally:
        database.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
