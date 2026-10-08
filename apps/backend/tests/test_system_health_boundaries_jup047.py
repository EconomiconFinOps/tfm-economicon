"""Decision/transport seams for JUP-047; controlled sockets only, no DNS/egress.

run_probes accepts {id: callable(timeout_seconds=...)}. Each callback models a
bounded transport that releases its own resource; this proves orchestration,
not live driver/DNS enforcement (separate integration validation is required).
bounded_http_get uses stdlib HTTPConnection/HTTPSConnection, does not redirect,
and returns only a closed observation rather than upstream bodies.
"""
import importlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock

import pytest

from test_secret_boundaries import main_module, resource_mocks, restore_logging, request


def module(main_module):
    assert request(main_module.app, "GET", "/health/status").status_code == 401, "The public health operation must exist and require authentication"
    return importlib.import_module("app.services.system_health")


@pytest.mark.parametrize("observations,expected", [
    ([{"id": "database", "status": "unknown"}, {"id": "openrouter", "status": "unknown"}], "unknown"),
    ([{"id": "backend", "status": "ok"}, {"id": "database", "status": "failed"}], "failed"),
    ([{"id": "backend", "status": "ok"}, {"id": "rabbitmq", "status": "failed"}], "failed"),
    ([{"id": "backend", "status": "ok"}, {"id": "vector_store", "status": "failed"}], "failed"),
    ([{"id": "backend", "status": "ok"}, {"id": "processor", "status": "failed"}], "failed"),
    ([{"id": "backend", "status": "ok"}, {"id": "openrouter", "status": "failed"}], "degraded"),
    ([{"id": "database", "status": "ok"}, {"id": "openrouter", "status": "unknown"}], "degraded"),
    ([{"id": name, "status": "ok"} for name in ("backend", "database", "rabbitmq", "processor", "vector_store", "azure_cost_api", "litellm", "openrouter")], "ok"),
])
def test_aggregate_precedence(main_module, observations, expected):
    assert module(main_module).aggregate_status(observations) == expected


@pytest.mark.parametrize("http_status,expected", [(200, "ok"), (302, "failed"), (401, "failed"), (503, "failed")])
def test_http_probe_uses_deadline_closes_and_does_not_redirect_or_disclose_body(main_module, monkeypatch, http_status, expected):
    health = module(main_module)
    connection = MagicMock()
    response = connection.getresponse.return_value
    response.status = http_status
    response.read.return_value = b'{"status": "ok", "private": "jup047-secret-upstream-body"}'
    response.getheader.return_value = "https://arbitrary-redirect.example/private"
    factory = MagicMock(return_value=connection)
    monkeypatch.setattr("http.client.HTTPConnection", factory)
    result = health.bounded_http_get("http://synthetic-health.example:8123/health", timeout_seconds=2)
    assert result["status"] == expected
    assert factory.call_args.kwargs["timeout"] <= 2
    assert connection.request.call_count == 1
    assert connection.request.call_args.args[:2] == ("GET", "/health")
    connection.close.assert_called_once()
    assert "jup047-secret-upstream-body" not in str(result)
    assert "synthetic-health.example" not in str(result)
    if http_status == 302:
        assert factory.call_count == 1, "A redirect must not create a second request"


def test_transport_timeout_is_unknown_and_connection_is_released(main_module, monkeypatch):
    health = module(main_module)
    connection = MagicMock()
    connection.getresponse.side_effect = TimeoutError("jup047-private-dsn")
    monkeypatch.setattr("http.client.HTTPConnection", MagicMock(return_value=connection))
    result = health.bounded_http_get("http://synthetic-health.example/health", timeout_seconds=2)
    assert result["status"] == "unknown" and result["reason_code"] == "timeout"
    assert "jup047-private-dsn" not in str(result)
    connection.close.assert_called_once()


def test_probe_transport_receives_budget_and_repeated_timeouts_release_resources(main_module):
    health = module(main_module)
    active = 0
    maximum = 0
    lock = threading.Lock()
    def probe(*, timeout_seconds):
        nonlocal active, maximum
        assert 0 < timeout_seconds <= 0.05
        with lock:
            active += 1
            maximum = max(maximum, active)
        try:
            time.sleep(timeout_seconds)
            raise TimeoutError("synthetic-private-probe")
        finally:
            with lock:
                active -= 1
    started = time.monotonic()
    for _ in range(3):
        result = health.run_probes({f"probe-{index}": probe for index in range(8)}, probe_seconds=0.05, overall_seconds=0.2, max_active=4)
        assert len(result) == 8
        assert all(item["status"] == "unknown" and item["reason_code"] in {"timeout", "busy"} for item in result)
        assert active == 0, "Returning early with orphaned work is not resource recovery"
    assert maximum <= 4 and time.monotonic() - started < 0.8


def test_active_probe_limit_is_shared_across_simultaneous_aggregations(main_module):
    health = module(main_module)
    active = 0
    maximum = 0
    lock = threading.Lock()
    entered, release = threading.Event(), threading.Event()
    def probe(*, timeout_seconds):
        nonlocal active, maximum
        with lock:
            active += 1
            maximum = max(maximum, active)
        if active == 4:
            entered.set()
        try:
            if not release.wait(timeout_seconds):
                raise TimeoutError()
            return {"status": "ok", "reason_code": "none"}
        finally:
            with lock:
                active -= 1
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(health.run_probes, {f"first-{index}": probe for index in range(4)}, probe_seconds=2, overall_seconds=3, max_active=4)
        try:
            assert entered.wait(0.1)
            second = executor.submit(health.run_probes, {f"second-{index}": probe for index in range(4)}, probe_seconds=0.2, overall_seconds=0.3, max_active=4)
            # First probes stay held through the second call; its 0.2s budget
            # must finish before the outer safety margin, so busy is asserted.
            result = second.result(timeout=0.5)
            assert all(item["reason_code"] == "busy" for item in result)
        finally:
            release.set()
        first.result(timeout=0.5)
    assert maximum <= 4 and active == 0


def test_direct_probe_exception_is_redacted_from_result_and_all_output(main_module, capsys, caplog):
    health = module(main_module)
    marker = "jup047-sensitive-catch-sentinel password=synthetic SELECT private"
    def fault(*, timeout_seconds):
        raise RuntimeError(marker)
    result = health.run_probes({"database": fault}, probe_seconds=0.1, overall_seconds=0.5)
    assert len(result) == 1
    assert result[0]["status"] == "failed" and result[0]["reason_code"] == "connection"
    captured = capsys.readouterr()
    assert marker not in str(result) + captured.out + captured.err + caplog.text


def _liveliness_adapter(health):
    adapter = getattr(health, "bounded_litellm_liveliness_get", None)
    assert callable(adapter), "LiteLLM needs its own bounded HTTP200/JSON-string adapter"
    return adapter


@pytest.mark.parametrize("raw,expected", [
    (b'"I\'m alive!"', "ok"),
    (b'"I\'m alive!"' + b" " * (16384 - len(b'"I\'m alive!"')), "ok"),
    (b'"I\'m alive!"' + b" " * (16385 - len(b'"I\'m alive!"')), "unknown"),
    (b'"I\'m alive"', "unknown"), (b'" I\'m alive!"', "unknown"),
    (b'"I\'m alive! "', "unknown"), (b'"other-secret-body"', "unknown"),
    (b'{"status":"ok"}', "unknown"), (b'{"status":"healthy"}', "unknown"),
    (b'{"status":"degraded"}', "unknown"), (b'[]', "unknown"),
    (b'null', "unknown"), (b'true', "unknown"), (b'42', "unknown"),
    (b'""', "unknown"), (b'invalid-secret-body', "unknown"),
])
def test_litellm_liveliness_accepts_only_exact_pinned_json_string(main_module, monkeypatch, raw, expected):
    health = module(main_module)
    adapter = _liveliness_adapter(health)
    connection = MagicMock()
    response = connection.getresponse.return_value
    response.status = 200
    response.read.return_value = raw
    factory = MagicMock(return_value=connection)
    monkeypatch.setattr(health.http.client, "HTTPConnection", factory)
    result = adapter("http://synthetic-gateway.invalid:4000/health/liveliness", timeout_seconds=0.7)
    assert result["status"] == expected
    assert result["reason_code"] == ("none" if expected == "ok" else "invalid_response")
    response.read.assert_called_once_with(16385)
    connection.request.assert_called_once_with("GET", "/health/liveliness", headers={"Accept": "application/json"})
    assert factory.call_args.kwargs["timeout"] == 0.7
    connection.close.assert_called_once()
    assert "secret-body" not in str(result) and "alive" not in str(result)


@pytest.mark.parametrize("http_status,reason", [(201, "upstream_error"), (302, "upstream_error"), (401, "authentication"), (403, "authentication"), (500, "upstream_error")])
def test_litellm_liveliness_non200_never_reads_or_redirects(main_module, monkeypatch, http_status, reason):
    health = module(main_module)
    adapter = _liveliness_adapter(health)
    connection = MagicMock()
    response = connection.getresponse.return_value
    response.status = http_status
    factory = MagicMock(return_value=connection)
    monkeypatch.setattr(health.http.client, "HTTPConnection", factory)
    result = adapter("http://synthetic.invalid/health/liveliness", timeout_seconds=0.2)
    assert result == {"status": "failed", "reason_code": reason}
    response.read.assert_not_called()
    connection.request.assert_called_once()
    factory.assert_called_once()
    connection.close.assert_called_once()


@pytest.mark.parametrize("error,status,reason", [(TimeoutError("private-secret-body"), "unknown", "timeout"), (OSError("private-secret-body"), "failed", "connection"), (ValueError("private-secret-body"), "unknown", "invalid_response")])
def test_litellm_read_failure_closes_and_redacts(main_module, monkeypatch, error, status, reason):
    health = module(main_module)
    adapter = _liveliness_adapter(health)
    connection = MagicMock()
    connection.getresponse.return_value.status = 200
    connection.getresponse.return_value.read.side_effect = error
    monkeypatch.setattr(health.http.client, "HTTPConnection", MagicMock(return_value=connection))
    assert adapter("http://synthetic.invalid/health/liveliness", timeout_seconds=0.2) == {"status": status, "reason_code": reason}
    connection.close.assert_called_once()


@pytest.mark.parametrize("url", ["http://user:secret@synthetic.invalid/health/liveliness", "http://synthetic.invalid/health/liveliness?key=secret", "http://synthetic.invalid/health/liveliness#secret", "file:///health/liveliness"])
def test_litellm_invalid_destination_never_creates_connection(main_module, monkeypatch, url):
    health = module(main_module)
    adapter = _liveliness_adapter(health)
    factory = MagicMock()
    monkeypatch.setattr(health.http.client, "HTTPConnection", factory)
    assert adapter(url, timeout_seconds=0.2) == {"status": "unknown", "reason_code": "not_configured"}
    factory.assert_not_called()


@pytest.mark.parametrize("raw,status,reason", [
    (b'{"status":"ok"}', "ok", "none"),
    (b'{"status":"healthy"}', "ok", "none"),
    (b'{"status":"degraded"}', "degraded", "upstream_error"),
    (b'"I\'m alive!"', "unknown", "invalid_response"),
])
def test_generic_http_contract_is_not_replaced_by_litellm(main_module, monkeypatch, raw, status, reason):
    health = module(main_module)
    connection = MagicMock()
    connection.getresponse.return_value.status = 200
    connection.getresponse.return_value.read.return_value = raw
    monkeypatch.setattr(health.http.client, "HTTPConnection", MagicMock(return_value=connection))
    assert health.bounded_http_get("http://synthetic.invalid/health", timeout_seconds=0.2) == {"status": status, "reason_code": reason}
    connection.close.assert_called_once()


def test_litellm_wrapper_and_child_keep_http_work_inside_isolation(main_module, monkeypatch):
    runtime = importlib.import_module("app.services.system_health_runtime")
    probe = getattr(runtime, "litellm_liveliness_probe", None)
    assert callable(probe), "Gateway liveliness needs an isolated-operation wrapper"
    isolated = MagicMock(return_value={"status": "ok", "reason_code": "none"})
    monkeypatch.setattr(runtime, "isolated_operation", isolated)
    assert probe(None, timeout_seconds=0.4)["reason_code"] == "not_configured"
    isolated.assert_not_called()
    url = "http://synthetic.invalid/health/liveliness"
    assert probe(url, timeout_seconds=0.4)["status"] == "ok"
    isolated.assert_called_once_with("litellm_liveliness", (url,), timeout_seconds=0.4)
    child_adapter = MagicMock(return_value={"status": "ok", "reason_code": "none"})
    assert callable(getattr(runtime, "bounded_litellm_liveliness_get", None))
    monkeypatch.setattr(runtime, "bounded_litellm_liveliness_get", child_adapter)
    monkeypatch.setattr(runtime.os, "dup2", lambda *args: None)
    monkeypatch.setattr(runtime.logging, "disable", lambda *args: None)
    pipe = MagicMock()
    runtime._child(pipe, "litellm_liveliness", (url,), 0.3)
    child_adapter.assert_called_once_with(url, timeout_seconds=0.3)
    pipe.send.assert_called_once_with((True, {"status": "ok", "reason_code": "none"}))
    pipe.close.assert_called_once()


def test_litellm_isolated_dns_deadline_terminates_and_releases(main_module, monkeypatch):
    runtime = importlib.import_module("app.services.system_health_runtime")
    probe = getattr(runtime, "litellm_liveliness_probe", None)
    assert callable(probe), "Liveliness must use the killable DNS/HTTP operation"
    context = MagicMock()
    receive, send = MagicMock(), MagicMock()
    receive.poll.return_value = False
    context.Pipe.return_value = (receive, send)
    process = context.Process.return_value
    process.pid = 123
    process.is_alive.side_effect = [True, False]
    factory = MagicMock(return_value=context)
    monkeypatch.setattr(runtime.multiprocessing, "get_context", factory)
    monkeypatch.setattr("socket.getaddrinfo", lambda *args, **kwargs: pytest.fail("DNS must not run in the parent"))
    with pytest.raises(TimeoutError):
        probe("http://unresolved.synthetic.invalid/health/liveliness", timeout_seconds=0.5)
    factory.assert_called_once_with("spawn")
    assert context.Process.call_args.kwargs["target"] is runtime._child
    assert context.Process.call_args.kwargs["args"][1:3] == ("litellm_liveliness", ("http://unresolved.synthetic.invalid/health/liveliness",))
    assert 0 <= receive.poll.call_args.args[0] <= 0.5
    process.start.assert_called_once()
    process.terminate.assert_called_once()
    process.join.assert_called_once()
    assert 0.01 <= process.join.call_args.kwargs["timeout"] <= 0.5
    process.close.assert_called_once()
    receive.close.assert_called_once()
    assert send.close.call_count >= 1
