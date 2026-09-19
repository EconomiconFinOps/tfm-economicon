"""Synthetic runtime configuration for isolated unit tests; never read local dotenv."""
import pytest

from app.core.config import Settings, get_settings

SYNTHETIC_ENV = {
    "RUNTIME_ENVIRONMENT": "test",
    "AUTH_SECRET_KEY": "jup053-synthetic-jwt-key-0123456789abcdef",
    "DATABASE_URL": "cockroachdb+psycopg://unit:db-fixture-pass@127.0.0.1:26257/unit?sslmode=require",
    "RABBITMQ_URL": "amqp://unit:broker-fixture-pass@127.0.0.1:5672/%2F",
    "VECTOR_DATABASE_URL": "postgresql+psycopg://unit:vector-fixture-pass@127.0.0.1:5432/unit",
    "ALLOW_INSECURE_LOCAL_DATABASE": "false",
    "DEMO_SEED_ENABLED": "false",
    "AZURE_COST_API_BASE_URL": "http://127.0.0.1:9",
}
RUNTIME_KEYS = {name.upper() for name in Settings.model_fields} | set(SYNTHETIC_ENV) | {
    "ECONOMICON_ENV_FILE", "DEMO_PASSWORD", "LITELLM_API_KEY",
    "OPENROUTER_API_KEY", "LITELLM_MASTER_KEY",
}


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch, tmp_path):
    for name in RUNTIME_KEYS:
        monkeypatch.delenv(name, raising=False)
    for name, value in SYNTHETIC_ENV.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def production_env(monkeypatch):
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "production")
    return dict(SYNTHETIC_ENV, RUNTIME_ENVIRONMENT="production")
