from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def settings() -> Settings:
    return Settings(
        azure_cost_dataset_path=(
            REPOSITORY_ROOT / "fixtures/azure-cost/EA-Cost-Actual.sample.csv"
        ),
        azure_cost_mapping_path=(
            REPOSITORY_ROOT / "docs/api/azure-cost-query-mapping.json"
        ),
        azure_cost_openapi_path=(
            REPOSITORY_ROOT / "docs/api/azure-cost-query.openapi.json"
        ),
    )


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client
