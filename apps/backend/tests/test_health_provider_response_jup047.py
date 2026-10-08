"""Synthetic HTTP/result contract through the actual runtime transport.

No listener, real socket or provider call is used. Assertions concern the public
provider observation and conservative ledger, not private receipt layout.
"""
import importlib
import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from test_health_provider_admission_jup047 import (
    Clock, check, main_module, no_network, policy, resource_mocks,
    restore_logging, service_type,
)
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers



def body(model="economicon-chat"):
    return {"id": "synthetic-generation", "model": model,
            "choices": [{"finish_reason": "stop", "message": {"content": " OK "}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2}}


def runtime_service(main_module, monkeypatch, *, data=None, raw=None, status=200, header="0.00002", error=None, configured=None):
    runtime = importlib.import_module("app.services.system_health_runtime")
    response = MagicMock()
    response.status = status
    response.read.return_value = raw if raw is not None else json.dumps(body() if data is None else data).encode()
    response.getheader.return_value = header
    connection = MagicMock()
    if error:
        connection.getresponse.side_effect = error
    else:
        connection.getresponse.return_value = response
    factory = MagicMock(return_value=connection)
    monkeypatch.setattr(runtime.http.client, "HTTPConnection", factory)
    clock = Clock()
    def transport(payload, *, timeout_seconds):
        return runtime._provider_request("http://synthetic-gateway.invalid", "synthetic-diagnostic-key",
                                         payload, timeout_seconds, "deepinfra/fp4", "a" * 32)
    service = service_type(main_module)(policy=policy() if configured is None else configured, transport=transport, clock=clock)
    return service, connection, clock


@pytest.mark.parametrize("model", ["economicon-chat", "z-ai/glm-5.2", "z-ai/glm-5.2-20260616", "openrouter/z-ai/glm-5.2", "other-model"])
def test_actual_http_parser_accepts_functional_response_independent_of_model(main_module, monkeypatch, model):
    service, connection, clock = runtime_service(main_module, monkeypatch, data=body(model))
    result = check(service)
    assert result["status"] == "ok" and result["verified_at"] == clock.value
    assert result["reported_model"] == model and result["model_identity"] == "unconfirmed"
    assert result["cost_confirmation"] == "unconfirmed"
    sent = json.loads(connection.request.call_args.kwargs["body"])
    assert sent["messages"] == [{"role": "user", "content": "Return exactly the two uppercase letters OK. Do not include punctuation, quotes, whitespace, or any other text."}]
    assert sent["model"] == "economicon-chat" and sent["max_tokens"] == 32
    assert sent["provider"]["order"] == ["deepinfra/fp4"]
    assert sent["provider"]["allow_fallbacks"] is False
    assert sent["reasoning"] == {"enabled": False}
    connection.request.assert_called_once()
    connection.close.assert_called_once()


@pytest.mark.parametrize("status,reason", [(401, "authentication"), (403, "authentication"), (500, "upstream_error")])
def test_http_error_is_not_masked_by_matching_model_or_cost(main_module, monkeypatch, status, reason):
    service, connection, _ = runtime_service(main_module, monkeypatch, data=body("openrouter/z-ai/glm-5.2"), status=status)
    result = check(service)
    assert result["status"] == "failed" and result["reason_code"] == reason
    assert result["verified_at"] is None
    assert service.accounting()["uncertain_usd"] == Decimal("0.00500752")
    connection.close.assert_called_once()


@pytest.mark.parametrize("change", [
    {"choices": []},
    {"choices": [{"finish_reason": "stop", "message": {"content": "OK"}}] * 2},
    {"choices": [{"finish_reason": "length", "message": {"content": "OK"}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": "wrong synthetic-secret"}}]},
    {"choices": [{"finish_reason": "stop", "message": {"content": None}}]},
    {"id": ""}, {"id": 42}, {"id": "x" * 257},
])
def test_invalid_functional_shape_never_advances_success(main_module, monkeypatch, change):
    data = body("openrouter/z-ai/glm-5.2")
    data.update(change)
    service, connection, _ = runtime_service(main_module, monkeypatch, data=data)
    result = check(service)
    assert result["status"] != "ok" and result["verified_at"] is None
    assert "synthetic-secret" not in str(result)
    assert service.accounting()["uncertain_usd"] == Decimal("0.00500752")
    connection.close.assert_called_once()


@pytest.mark.parametrize("raw", [b"{invalid JSON synthetic-secret", b"x" * 16385, b"[]"])
def test_invalid_or_excessive_body_is_closed_non_success(main_module, monkeypatch, raw):
    service, connection, _ = runtime_service(main_module, monkeypatch, raw=raw)
    result = check(service)
    assert result["status"] != "ok" and result["verified_at"] is None
    assert "synthetic-secret" not in str(result)
    connection.close.assert_called_once()


def test_transport_timeout_keeps_reserve_and_never_retries(main_module, monkeypatch):
    service, connection, _ = runtime_service(main_module, monkeypatch, error=TimeoutError("synthetic-secret"))
    result = check(service)
    assert result["status"] == "unknown" and result["reason_code"] == "timeout"
    assert result["verified_at"] is None and "synthetic-secret" not in str(result)
    assert service.accounting()["uncertain_usd"] == Decimal("0.00500752")
    connection.request.assert_called_once()
    connection.close.assert_called_once()


def test_gateway_cost_header_is_information_not_upstream_certification(main_module, monkeypatch):
    data = body("openrouter/z-ai/glm-5.2")
    data["usage"]["cost"] = "0.00001"
    service, _, _ = runtime_service(main_module, monkeypatch, data=data, header="0.00002")
    result = check(service)
    assert result["status"] == "ok"
    assert result["reported_cost_usd"] == "0.00002"
    assert result["cost_status"] == "gateway_reported" and result["cost_confirmation"] == "unconfirmed"
    # No new body/header concordance policy is introduced by informational data.
    assert service.accounting()["spent_usd"] == Decimal("0.00002")



@pytest.mark.parametrize("header,settled", [("0.00002", True), (None, False), ("0", False)])
def test_actual_http_parser_second_check_keeps_prior_reserve_and_cumulative_limit(
    main_module, monkeypatch, header, settled,
):
    configured = policy(known_spend_usd="0.000009225", uncertain_usd="0.002016",
                        pending_usd="0", known_execution_calls=1, execution_calls_limit=2)
    service, connection, clock = runtime_service(
        main_module, monkeypatch, data=body("openrouter/z-ai/glm-5.2"),
        header=header, configured=configured,
    )
    result = check(service, "authorized-second")
    assert result["http_status"] == 200 and result["status"] == "ok"
    assert result["verified_at"] == clock.value
    assert service.accounting()["uncertain_usd"] == Decimal("0.002016" if settled else "0.00702352")
    assert service.accounting()["spent_usd"] == Decimal("0.000029225" if settled else "0.000009225")
    connection.request.assert_called_once()
    connection.close.assert_called_once()
    clock.advance(61)
    assert check(service, "third")["reason_code"] == "budget_unavailable"
    connection.request.assert_called_once()

@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("model,cost,expected_model,expected_cost,cost_status", [
    ("economicon-chat", "0.00002", "economicon-chat", "0.00002", "gateway_reported"),
    (None, None, None, None, "unavailable"),
    ("unsafe://private?token=synthetic-secret", "NaN", None, None, "invalid"),
])
def test_authenticated_get_serializes_provider_information_after_post(
    main_module, api, monkeypatch, model, cost, expected_model, expected_cost, cost_status,
):
    service, connection, _ = runtime_service(main_module, monkeypatch, data=body(model), header=cost)
    monkeypatch.setattr(api.app.state, "health_provider_check", service, raising=False)
    routes = importlib.import_module("app.api.routes.health")
    # Isolate DTO/HTTP/auth behavior: external health probes and activity queries
    # are covered separately in test_system_health_jup047, not exercised here.
    probes = MagicMock(return_value=[
        {"id": identifier, "status": "ok", "reason_code": "none", "latency_ms": 0}
        for identifier in ("database", "rabbitmq", "vector_store", "processor", "azure_cost_api", "litellm")
    ])
    monkeypatch.setattr(routes, "run_probes", probes)
    for method, path in (("POST", "/health/provider-check"), ("GET", "/health/status")):
        payload = {"json": {"idempotency_key": "denied"}} if method == "POST" else {}
        for auth, expected_status in (([], 401), (headers(tenant="tenant-b"), 403)):
            assert call(api, method, path, headers=auth, **payload).status_code == expected_status
    connection.request.assert_not_called()
    probes.assert_not_called()
    auth = headers()
    post = call(api, "POST", "/health/provider-check", headers=auth,
                json={"idempotency_key": "get-serialized-information"})
    assert post.status_code == 200 and post.json()["status"] == "ok"
    response = call(api, "GET", "/health/status", headers=auth)
    assert response.status_code == 200 and response.headers["Cache-Control"] == "no-store"
    snapshot = response.json()
    assert snapshot["tenant_id"] == "tenant-a"
    item = next(component for component in snapshot["components"] if component["id"] == "openrouter")
    assert item["status"] == "ok"
    assert datetime.fromisoformat(item["verified_at"].replace("Z", "+00:00")) == datetime.fromisoformat(post.json()["verified_at"])
    assert item["reported_model"] == expected_model
    assert item["model_identity"] == "unconfirmed"
    assert item["reported_cost_usd"] == expected_cost and item["cost_status"] == cost_status
    assert item["cost_confirmation"] == "unconfirmed"
    assert "synthetic-secret" not in response.text
    connection.request.assert_called_once()
    connection.close.assert_called_once()
    probes.assert_called_once()


@pytest.mark.parametrize("content,expected", [
    ("OK", "ok"), ("ok", "ok"), (" \tOk\n", "ok"),
    ("OK.", "unknown"), ("OK extra", "unknown"), ("", "unknown"),
])
def test_fixed_request_keeps_exact_normalized_response_contract(main_module, monkeypatch, content, expected):
    data = body()
    data["choices"][0]["message"]["content"] = content
    service, connection, clock = runtime_service(main_module, monkeypatch, data=data)
    result = check(service)
    assert result["status"] == expected
    assert result["verified_at"] == (clock.value if expected == "ok" else None)
    assert result["reason_code"] == ("none" if expected == "ok" else "invalid_response")
    if expected != "ok":
        assert result["check_id"] is None
        assert service.accounting()["uncertain_usd"] == Decimal("0.00500752")
    connection.close.assert_called_once()
