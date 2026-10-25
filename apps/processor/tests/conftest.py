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


@pytest.fixture
def litellm_settings():
    return Settings(
        _env_file=None, llm_provider="litellm", embedding_provider="litellm",
        embedding_dimension=1536, litellm_api_key="jup023-synthetic-virtual-key",
        litellm_base_url="http://gateway.invalid:4000/v1",
    )


@pytest.fixture
def gateway_transport(monkeypatch):
    import io
    import json
    import socket
    import time
    from email.message import Message
    from types import SimpleNamespace
    from urllib import request, response

    transport = SimpleNamespace(responses=[], calls=[], delays=[])

    def open_http(handler, req):
        transport.calls.append(req)
        assert transport.responses, "Unexpected gateway attempt or fallback"
        outcome = transport.responses.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        status, body, headers = outcome
        message = Message()
        for name, value in headers.items():
            message[name] = value
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        result = response.addinfourl(io.BytesIO(raw), message, req.full_url, status)
        result.msg = "synthetic gateway response"
        return result

    def forbid_network(*args, **kwargs):
        pytest.fail("Offline test attempted a socket connection")

    # Keep urllib's real redirect/error processing; replace only socket transport.
    monkeypatch.setattr(request.HTTPHandler, "http_open", open_http)
    monkeypatch.setattr(request.HTTPSHandler, "https_open", open_http)
    monkeypatch.setattr(socket, "create_connection", forbid_network)
    monkeypatch.setattr(time, "sleep", transport.delays.append)
    monkeypatch.setenv("NO_PROXY", "*")
    return transport
