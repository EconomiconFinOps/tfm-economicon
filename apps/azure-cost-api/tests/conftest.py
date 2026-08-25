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
        azure_cost_auth_enabled=False,
        azure_cost_page_size=1000,
        azure_cost_skiptoken_secret="unit-test-secret",
    )


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def secure_settings(settings: Settings) -> Settings:
    return settings.model_copy(
        update={
            "azure_cost_auth_enabled": True,
            "azure_cost_valid_tokens": "test-valid-token",
            "azure_cost_forbidden_tokens": "test-forbidden-token",
            "azure_cost_page_size": 2,
            "azure_cost_fake_timeout_seconds": 0.01,
            "azure_cost_retry_after_seconds": 3,
        }
    )


@pytest.fixture
def secure_client(secure_settings: Settings):
    with TestClient(create_app(secure_settings)) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-valid-token"}
