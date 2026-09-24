"""JUP-085 residual: native CORS over the real application and isolated settings."""
import asyncio
import json
import traceback
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.metrics import MetricsMiddleware
from app.core.runtime_secrets import StartupError
from app.core.security import create_access_token
from conftest import SYNTHETIC_ENV
from test_secret_boundaries import (
    main_module, request, resource_mocks, restore_logging,
)

ALLOWED = "https://console.example.test"
DENIED = "https://elsewhere.example.test"


@pytest.fixture(autouse=True)
def isolated_origins(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    get_settings.cache_clear()


@pytest.mark.parametrize("raw", [None, "[]"])
def test_origins_default_to_empty_without_granting_access(main_module, monkeypatch, raw):
    if raw is not None:
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", raw)
    settings = get_settings()
    assert settings.model_dump().get("cors_allowed_origins") == []
    response = request(main_module.app, "GET", "/me", headers={"Origin": ALLOWED})
    assert response.status_code == 401
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("environment,origins", [
    ("production", [ALLOWED]),
    ("production", ["https://console.example.test:8443"]),
    ("development", ["http://localhost:5173", "http://127.0.0.1:5173"]),
    ("test", ["http://localhost:5173", ALLOWED]),
])
def test_settings_preserve_exact_json_origins(monkeypatch, environment, origins):
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", environment)
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", json.dumps(origins))
    assert get_settings().model_dump().get("cors_allowed_origins") == origins


@pytest.mark.parametrize("raw", [
    "", " ", "[", "null", '"https://console.example.test"', "{}", "123", "true",
    '[null]', '[42]', '[true]', '[{}]', '[[]]', '["*"]', '["null"]',
    '["https://*.example.test"]', '["https://.*"]', '["^https://example.test$"]',
    '["https://console.example.test/"]', '["https://console.example.test/path"]',
    '["https://unit:private-sentinel@console.example.test"]',
    '["https://console.example.test?private-sentinel=1"]',
    '["https://console.example.test#private-sentinel"]',
    '[" https://console.example.test"]', '["https://console.example.test "]',
    '["https://console.example.test:65536"]', '["https://console.example.test:port"]',
    '["https://console.example.test:-1"]', '["https://"]', '["ftp://example.test"]',
    '["HTTPS://console.example.test"]', '["https://CONSOLE.example.test"]',
    '["https://console.example.test:443"]',
    '["https://console.example.test", "*"]',
])
def test_invalid_origins_fail_startup_with_sanitized_diagnostic(monkeypatch, raw, capsys):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", raw)
    with pytest.raises(StartupError) as failure:
        get_settings()
    assert str(failure.value) == "Invalid runtime configuration; check required credentials and settings."
    diagnostic = "".join(traceback.format_exception(failure.value))
    captured = capsys.readouterr()
    for sentinel in ("private-sentinel", SYNTHETIC_ENV["AUTH_SECRET_KEY"], SYNTHETIC_ENV["DATABASE_URL"]):
        assert sentinel not in diagnostic + captured.out + captured.err
    assert failure.value.__cause__ is None
    assert "ValidationError" not in diagnostic and "JSONDecodeError" not in diagnostic


def test_production_rejects_http_origins(monkeypatch):
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", '["http://localhost:5173"]')
    with pytest.raises(StartupError):
        get_settings()


@pytest.fixture
def cors_app(main_module, monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", json.dumps([ALLOWED, "http://localhost:5173"]))
    database = MagicMock()
    database.fetch_user_by_id.return_value = {
        "id": "cors-user", "email": "operator@example.com", "full_name": "CORS Operator", "role": "operator",
    }
    database.user_has_tenant.return_value = False
    monkeypatch.setattr(main_module.app.state, "database", database, raising=False)
    configure_logging()
    return main_module.app


def bearer():
    return "Bearer " + create_access_token("cors-user", SYNTHETIC_ENV["AUTH_SECRET_KEY"], 10)


@pytest.mark.parametrize("method,path,headers", [
    ("POST", "/auth/login", "Content-Type"),
    ("GET", "/me", "Authorization,Content-Type"),
    ("GET", "/tenants", "Authorization"),
    ("GET", "/billing/summary", "Authorization,Content-Type,X-Tenant-Id"),
    ("POST", "/jobs/ingest", "authorization,content-type,x-tenant-id"),
    ("GET", "/health", "Accept,Accept-Language,Content-Language"),
])
def test_native_preflight_needs_no_jwt_or_inner_middleware(cors_app, method, path, headers, capsys):
    configure_logging()
    with patch.object(MetricsMiddleware, "_record") as record:
        response = request(cors_app, "OPTIONS", path, headers={
            "Origin": ALLOWED, "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": headers,
        })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert "origin" in response.headers["vary"].lower()
    assert set(response.headers["access-control-allow-methods"].split(", ")) == {"GET", "POST"}
    permitted = {value.strip().lower() for value in response.headers["access-control-allow-headers"].split(",")}
    assert {"authorization", "content-type", "x-tenant-id", "accept", "accept-language", "content-language"} <= permitted
    assert "*" not in permitted
    assert response.headers["access-control-max-age"] == "600"
    assert "access-control-allow-credentials" not in response.headers
    assert "access-control-expose-headers" not in response.headers
    assert not cors_app.state.database.mock_calls
    record.assert_not_called()
    assert '"http_request"' not in capsys.readouterr().out


@pytest.mark.parametrize("origin,method,headers", [
    (DENIED, "GET", "Authorization"), ("null", "GET", "Authorization"),
    ("http://127.0.0.1:5173", "GET", "Authorization"),
    ("http://localhost:5174", "GET", "Authorization"),
    (ALLOWED, "DELETE", "Authorization"), (ALLOWED, "PUT", "Authorization"),
    (ALLOWED, "GET", "X-Unapproved"),
])
def test_denied_preflight_does_not_grant_requested_combination(cors_app, origin, method, headers):
    response = request(cors_app, "OPTIONS", "/me", headers={
        "Origin": origin, "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": headers,
    })
    assert response.status_code == 400
    if origin != ALLOWED:
        assert "access-control-allow-origin" not in response.headers
    if method not in {"GET", "POST"}:
        assert method not in response.headers.get("access-control-allow-methods", "")
    if headers == "X-Unapproved":
        assert headers.lower() not in response.headers.get("access-control-allow-headers", "").lower()
    assert not cors_app.state.database.mock_calls


@pytest.mark.parametrize("origin", [ALLOWED, DENIED, "null", None])
@pytest.mark.parametrize("status", [200, 401, 403, 422, 500])
def test_real_response_matrix_keeps_auth_sanitization_metrics_and_cors(cors_app, origin, status, capsys):
    configure_logging()
    headers = {"Origin": origin} if origin else {}
    method, path, payload = "GET", "/me", None
    if status in {200, 403, 500}:
        headers["Authorization"] = bearer()
    if status == 403:
        path = "/billing/summary"
        headers["X-Tenant-Id"] = "denied-tenant"
    if status == 422:
        method, path, payload = "POST", "/auth/login", {"email": "private-input-sentinel", "password": ""}
    if status == 500:
        cors_app.state.database.fetch_user_by_id.side_effect = RuntimeError("private-db-sentinel")
    with patch.object(MetricsMiddleware, "_record", wraps=MetricsMiddleware._record) as record:
        response = request(cors_app, method, path, headers=headers, json=payload)
    assert response.status_code == status
    if status == 200:
        assert response.json() == cors_app.state.database.fetch_user_by_id.return_value
    elif status == 401:
        assert response.json() == {"detail": "Missing or invalid bearer token."}
        cors_app.state.database.fetch_user_by_id.assert_not_called()
    elif status == 403:
        assert response.json() == {"detail": "The current user cannot access the requested tenant."}
        cors_app.state.database.user_has_tenant.assert_called_once_with("cors-user", "denied-tenant")
    elif status == 422:
        assert all(set(item) == {"type", "msg"} for item in response.json()["detail"])
    else:
        assert response.json() == {"detail": "Internal server error"}
    captured = capsys.readouterr()
    assert "private-db-sentinel" not in response.text + captured.out + captured.err
    assert "private-input-sentinel" not in response.text + captured.out + captured.err
    assert '"http_request"' in captured.out
    record.assert_called_once()
    assert record.call_args.kwargs["status_code"] == status
    if origin == ALLOWED:
        assert response.headers.get("access-control-allow-origin") == ALLOWED
        assert "origin" in response.headers.get("vary", "").lower()
    else:
        assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers
    assert "access-control-expose-headers" not in response.headers


def test_cors_preserves_fastapi_api_and_resource_lifespan(cors_app, resource_mocks):
    assert isinstance(cors_app, FastAPI)
    assert cors_app.router.routes
    assert isinstance(cors_app.dependency_overrides, dict)

    async def run():
        async with cors_app.router.lifespan_context(cors_app):
            assert cors_app.state.database is resource_mocks[0].return_value
            assert cors_app.state.queue is resource_mocks[1].return_value
            assert cors_app.state.vector_store is resource_mocks[2].return_value
    asyncio.run(run())
    resource_mocks[0].return_value.initialize.assert_called_once()
    resource_mocks[0].return_value.dispose.assert_called_once()
    resource_mocks[1].return_value.close.assert_called_once()
    resource_mocks[2].return_value.close.assert_called_once()


def test_outer_server_error_is_outside_cors_guarantee(cors_app):
    class OuterFailure:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            raise RuntimeError("outer-failure-sentinel")

    cors_app.add_middleware(OuterFailure)
    response = request(cors_app, "GET", "/me", headers={"Origin": ALLOWED})
    assert response.status_code == 500
    assert "access-control-allow-origin" not in response.headers
    assert "outer-failure-sentinel" not in response.text
