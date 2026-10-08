"""JUP-047 public API contracts; real auth/SQLite, no real network or inference.

The existing application is imported, not a future route/schema/service module.
Assertions intentionally expose absent behavior as HTTP 404 during Red.
"""
import importlib
import json
import socket
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_tenant_isolation_api import api, call, headers
from test_secret_boundaries import main_module, resource_mocks, restore_logging

pytestmark = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
COMPONENT_IDS = {"backend", "database", "rabbitmq", "processor", "vector_store", "azure_cost_api", "litellm", "openrouter"}
STATES = {"ok", "degraded", "failed", "unknown"}
REASONS = {"none", "connection", "upstream_error", "authentication", "timeout", "invalid_response", "not_configured", "not_initialized", "not_verified", "busy", "cooldown", "budget_unavailable", "stale"}
JOB_STATES = {"publish_pending", "publish_failed", "publish_unknown", "queued", "running", "completed", "failed", "other"}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("JUP-047 Red must not open a socket or spend inference credit")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


class _SerializablePingDouble:
    """Keep the parent's spies, serialize only behavior needed by isolated ping."""
    def __init__(self):
        self.ping = MagicMock(return_value=True)

    def __getstate__(self):
        return {"return_value": self.ping.return_value, "side_effect": self.ping.side_effect}

    def __setstate__(self, state):
        self.__init__()
        self.ping.return_value = state["return_value"]
        self.ping.side_effect = state["side_effect"]


class _SerializableQueueDouble(_SerializablePingDouble):
    def __init__(self):
        super().__init__()
        self.queue_name = "jup047-test"
        self.reserve = MagicMock()
        self.publish = MagicMock()
        self.cancel = MagicMock()


class _SerializableVectorDouble(_SerializablePingDouble):
    def __init__(self):
        super().__init__()
        self.search_chunks = MagicMock(return_value=[])



@pytest.fixture
def operational_api(api, monkeypatch):
    # Existing resource seams, without bypassing bearer or membership checks.
    monkeypatch.setattr(api.db, "ping", MagicMock(return_value=True))
    api.queue = _SerializableQueueDouble()
    monkeypatch.setattr(api.app.state, "queue", api.queue)
    api.vector = _SerializableVectorDouble()
    monkeypatch.setattr(api.app.state, "vector_store", api.vector)
    with api.db.engine.begin() as connection:
        connection.execute(text("""CREATE TABLE azure_cost_ingestion_runs (
            id STRING PRIMARY KEY, tenant_id STRING NOT NULL, subscription_id STRING NOT NULL,
            request JSONB NOT NULL, status STRING NOT NULL CHECK (status IN ('running','completed','failed')),
            page_count INT8 NOT NULL DEFAULT 0, retry_count INT8 NOT NULL DEFAULT 0,
            row_count INT8 NOT NULL DEFAULT 0, error_code STRING,
            started_at TIMESTAMPTZ NOT NULL, completed_at TIMESTAMPTZ
        )"""))
    return api


def utc(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)
    return parsed


def status(api, **kwargs):
    response = call(api, "GET", "/health/status", headers=headers(), **kwargs)
    assert response.status_code == 200, "Authenticated operational diagnostics must exist"
    return response, response.json()


def add_job(api, identifier, state, updated, tenant="tenant-a"):
    with api.db.engine.begin() as connection:
        connection.execute(text("""INSERT INTO jobs
            (id, tenant_id, created_by, source, payload, status, created_at, updated_at)
            VALUES (:id, :tenant, 'alice', 'synthetic-private-document', :payload, :state, :updated, :updated)
        """), {"id": identifier, "tenant": tenant, "payload": json.dumps({"text": "private-job-body"}), "state": state, "updated": updated})


@pytest.mark.parametrize("method,path", [("GET", "/health/status"), ("POST", "/health/provider-check")])
@pytest.mark.parametrize("auth,expected", [([], 401), (headers(tenant=None), 400), (headers(tenant="tenant-b"), 403), (headers(tenant=" tenant-a"), 400)])
def test_authentication_and_tenant_precede_diagnostics(operational_api, method, path, auth, expected):
    response = call(operational_api, method, path, headers=auth, **({"json": {"idempotency_key": "red-action"}} if method == "POST" else {}))
    assert response.status_code == expected
    operational_api.db.ping.assert_not_called()
    operational_api.queue.ping.assert_not_called()
    operational_api.vector.ping.assert_not_called()
    assert "tenant-a" not in response.text and "private-job-body" not in response.text


def test_public_health_retains_legacy_contract_without_tenant(operational_api):
    response = call(operational_api, "GET", "/health")
    assert response.status_code == 200
    assert set(response.json()) == {"status", "services", "checked_at"}
    assert response.json()["status"] == "ok"
    utc(response.json()["checked_at"])
    operational_api.queue.ping.return_value = False
    assert call(operational_api, "GET", "/health").json()["status"] == "degraded"


def test_closed_contract_utc_and_explicit_unverified_provider(operational_api):
    response, body = status(operational_api)
    assert response.headers.get("cache-control") == "no-store"
    assert body["tenant_id"] == "tenant-a" and body["status"] in STATES
    checked = utc(body["checked_at"])
    assert utc(body["window"]["end"]) == checked
    assert utc(body["window"]["start"]) == checked - timedelta(hours=24)
    assert {component["id"] for component in body["components"]} == COMPONENT_IDS
    assert len(body["components"]) == len(COMPONENT_IDS)
    for component in body["components"]:
        assert component["status"] in STATES and component["reason_code"] in REASONS
        assert component["source_kind"] in {"live", "simulated", "mock", "unverified"}
        utc(component["checked_at"])
        assert component["latency_ms"] is None or component["latency_ms"] >= 0
    provider = next(c for c in body["components"] if c["id"] == "openrouter")
    assert provider["status"] == "unknown" and provider["verified_at"] is None
    assert body["status"] != "ok", "A reachable gateway cannot certify a real inference"


def test_empty_histories_differ_from_unavailable_schema(operational_api):
    _, body = status(operational_api)
    for name, latest in (("jobs", "last_updated_at"), ("ingestion", "last_completed_at")):
        assert body[name]["data_status"] == "empty"
        assert body[name]["failed_last_24h"] == 0 and body[name][latest] is None
        assert all(value == 0 for value in body[name]["counts"].values())
    with operational_api.db.engine.begin() as connection:
        connection.execute(text("DROP TABLE azure_cost_ingestion_runs"))
    _, missing = status(operational_api)
    assert missing["ingestion"]["data_status"] == "unavailable"
    assert missing["ingestion"]["counts"] is None and missing["ingestion"]["failed_last_24h"] is None


def test_native_publication_states_unknown_state_and_tenant_filter(operational_api):
    now = datetime.now(timezone.utc)
    for index, state in enumerate(sorted(JOB_STATES - {"other"}) + ["private-arbitrary-state"]):
        add_job(operational_api, str(index), state, now - timedelta(minutes=10))
    add_job(operational_api, "foreign-job", "failed", now, tenant="tenant-b")
    add_job(operational_api, "old-failure", "failed", now - timedelta(hours=25))
    _, body = status(operational_api)
    assert body["jobs"]["data_status"] == "available"
    assert body["jobs"]["counts"] == {state: 2 if state == "failed" else 1 for state in JOB_STATES}
    assert body["jobs"]["failed_last_24h"] == 2, "failed and publish_failed count; publish_unknown is indeterminate"
    assert "private-arbitrary-state" not in json.dumps(body)
    assert next(c for c in body["components"] if c["id"] == "database")["status"] == "ok"
    assert body["status"] == "degraded", "Historical failures alone do not mean database failure"
    south = call(operational_api, "GET", "/health/status", headers=headers("multi", "tenant-b"))
    assert south.status_code == 200 and south.json()["jobs"]["counts"]["failed"] == 1


def test_ingestion_latest_completion_is_not_refresh_failure_or_other_tenant(operational_api):
    now = datetime.now(timezone.utc)
    completed = now - timedelta(hours=3)
    with operational_api.db.engine.begin() as connection:
        for identifier, tenant, state, started, ended in (
            ("done", "tenant-a", "completed", completed - timedelta(minutes=5), completed),
            ("failed", "tenant-a", "failed", now - timedelta(minutes=15), now - timedelta(minutes=10)),
            ("failed-no-end", "tenant-a", "failed", now - timedelta(minutes=5), None),
            ("running", "tenant-a", "running", now, None),
            ("foreign", "tenant-b", "completed", now, now),
        ):
            connection.execute(text("INSERT INTO azure_cost_ingestion_runs (id,tenant_id,subscription_id,request,status,started_at,completed_at) VALUES (:id,:tenant,'synthetic-subscription','{}',:state,:start,:end)"), {"id": identifier, "tenant": tenant, "state": state, "start": started, "end": ended})
    _, body = status(operational_api)
    assert body["ingestion"]["counts"] == {"running": 1, "completed": 1, "failed": 2, "other": 0}
    assert body["ingestion"]["failed_last_24h"] == 2
    assert utc(body["ingestion"]["last_completed_at"]) == completed
    assert utc(body["checked_at"]) > completed


def test_repeated_gets_do_not_mutate_product_or_infer(operational_api):
    before = {table: rows(operational_api.db, table) for table in ("jobs", "messages", "conversations")}
    for _ in range(3):
        status(operational_api)
    assert before == {table: rows(operational_api.db, table) for table in before}
    operational_api.queue.reserve.assert_not_called()
    operational_api.queue.publish.assert_not_called()
    operational_api.vector.search_chunks.assert_not_called()
    operational_api.embedding.embed.assert_not_called()


def test_probe_error_retains_other_components_and_redacts_private_markers(operational_api, caplog, capsys):
    marker = "jup047-private-password SELECT private https://secret.example/document"
    operational_api.queue.ping.side_effect = RuntimeError(marker)
    _, body = status(operational_api)
    queue = next(c for c in body["components"] if c["id"] == "rabbitmq")
    assert queue["status"] == "failed" and queue["reason_code"] in {"connection", "upstream_error"}
    assert body["status"] == "failed"
    assert next(c for c in body["components"] if c["id"] == "backend")["status"] == "ok"
    captured = capsys.readouterr()
    assert marker not in json.dumps(body) + caplog.text + captured.out + captured.err


@pytest.mark.parametrize("field,value", [("model", "other-model"), ("prompt", "private-user-text"), ("max_tokens", 9999), ("url", "https://arbitrary.example"), ("tenant_id", "tenant-b")])
def test_provider_check_rejects_client_control(operational_api, field, value):
    response = call(operational_api, "POST", "/health/provider-check", headers=headers(), json={"idempotency_key": "one-action", field: value})
    assert response.status_code == 422
    assert str(value) not in response.text


def test_unconfigured_provider_budget_fails_closed_without_sending(operational_api):
    response = call(operational_api, "POST", "/health/provider-check", headers=headers(), json={"idempotency_key": "one-action"})
    assert response.status_code == 429
    assert response.json()["reason_code"] == "budget_unavailable"
    assert response.json().get("verified_at") is None


def test_jobs_latest_timestamp_is_scoped_symmetrically(operational_api):
    older = datetime(2026, 10, 5, 11, tzinfo=timezone.utc)
    newer = older + timedelta(hours=1)
    add_job(operational_api, "latest-a", "completed", older, tenant="tenant-a")
    add_job(operational_api, "latest-b", "completed", newer, tenant="tenant-b")
    for tenant, expected in (("tenant-a", older), ("tenant-b", newer)):
        response = call(operational_api, "GET", "/health/status", headers=headers("multi", tenant))
        assert response.status_code == 200
        assert utc(response.json()["jobs"]["last_updated_at"]) == expected


def test_ingestion_failures_are_scoped_to_the_requested_tenant(operational_api):
    now = datetime.now(timezone.utc) - timedelta(minutes=1)
    with operational_api.db.engine.begin() as connection:
        for identifier, tenant, state in (("ingest-a", "tenant-a", "completed"), ("ingest-b", "tenant-b", "failed")):
            connection.execute(text("INSERT INTO azure_cost_ingestion_runs (id,tenant_id,subscription_id,request,status,started_at,completed_at) VALUES (:id,:tenant,'synthetic','{}',:state,:at,:at)"), {"id": identifier, "tenant": tenant, "state": state, "at": now})
    for tenant, expected in (("tenant-a", 0), ("tenant-b", 1)):
        response = call(operational_api, "GET", "/health/status", headers=headers("multi", tenant))
        assert response.status_code == 200
        assert response.json()["ingestion"]["failed_last_24h"] == expected


@pytest.mark.parametrize("ingestion", [False, True], ids=["jobs", "ingestion"])
def test_failure_window_includes_both_utc_endpoints_only(operational_api, monkeypatch, ingestion):
    checked = datetime(2026, 10, 6, 12, tzinfo=timezone.utc)
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return checked if tz is not None else checked.replace(tzinfo=None)
    monkeypatch.setattr(importlib.import_module("app.api.routes.health"), "datetime", FixedDateTime)
    start = checked - timedelta(hours=24)
    times = (start - timedelta(microseconds=1), start, start + timedelta(hours=12), checked, checked + timedelta(microseconds=1))
    for index, at in enumerate(times):
        if ingestion:
            with operational_api.db.engine.begin() as connection:
                connection.execute(text("INSERT INTO azure_cost_ingestion_runs (id,tenant_id,subscription_id,request,status,started_at,completed_at) VALUES (:id,'tenant-a','synthetic','{}','failed',:at,:at)"), {"id": f"edge-{index}", "at": at})
        else:
            add_job(operational_api, f"edge-{index}", "failed", at)
    _, body = status(operational_api)
    assert utc(body["checked_at"]) == checked
    assert utc(body["window"]["start"]) == start and utc(body["window"]["end"]) == checked
    assert body["ingestion" if ingestion else "jobs"]["failed_last_24h"] == 3


def test_get_uses_only_provider_observation_never_check(operational_api, monkeypatch):
    provider_type = importlib.import_module("app.services.health_provider_check").HealthProviderCheck
    provider = MagicMock(wraps=provider_type(policy={}, transport=None), spec_set=["observation", "check"])
    monkeypatch.setattr(operational_api.app.state, "health_provider_check", provider, raising=False)
    for _ in range(3):
        status(operational_api)
    assert provider.observation.call_count == 3
    provider.check.assert_not_called()


@pytest.mark.parametrize("enabled,gateway_raw,gateway_status,gateway_reason", [
    (True, b'"I\'m alive!"', "ok", "none"),
    (True, b'{"status":"ok"}', "unknown", "invalid_response"),
    (False, b'"I\'m alive!"', "unknown", "not_configured"),
])
def test_route_selects_exclusive_gateway_probe_without_real_inference(
    operational_api, monkeypatch, enabled, gateway_raw, gateway_status, gateway_reason,
):
    from types import SimpleNamespace
    routes = importlib.import_module("app.api.routes.health")
    runtime = importlib.import_module("app.services.system_health_runtime")
    health = importlib.import_module("app.services.system_health")
    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(
        litellm_base_url="http://synthetic-gateway.invalid:4000/v1",
        processor_health_base_url="http://synthetic-processor.invalid/health",
        azure_cost_health_base_url="http://synthetic-azure.invalid/health",
        health_gateway_probe_enabled=enabled,
        health_probe_timeout_seconds=8,
    ))
    connections = []
    def connection(host, *, port=None, timeout):
        conn = MagicMock()
        conn.getresponse.return_value.status = 200
        conn.getresponse.return_value.read.return_value = (
            gateway_raw if host == "synthetic-gateway.invalid"
            else b'{"status":"degraded"}' if host == "synthetic-azure.invalid"
            else b'{"status":"healthy"}'
        )
        connections.append((host, conn))
        return conn
    monkeypatch.setattr(health.http.client, "HTTPConnection", connection)
    operations = []
    def isolated(operation, args, *, timeout_seconds):
        operations.append((operation, args))
        adapter = health.bounded_http_get if operation == "http" else getattr(health, "bounded_litellm_liveliness_get", None)
        assert callable(adapter), "Route must dispatch the gateway-specific bounded adapter"
        assert operation in {"http", "litellm_liveliness"}
        return adapter(*args, timeout_seconds=timeout_seconds)
    monkeypatch.setattr(runtime, "isolated_operation", isolated)
    def probes(callbacks, *, probe_seconds, overall_seconds):
        assert (probe_seconds, overall_seconds) == (8, 18)
        return [
            {"id": name, **(callback(timeout_seconds=0.2) if name in {"processor", "azure_cost_api", "litellm"} else {"status": "ok", "reason_code": "none"})}
            for name, callback in callbacks.items()
        ]
    monkeypatch.setattr(routes, "run_probes", probes)
    provider_type = importlib.import_module("app.services.health_provider_check").HealthProviderCheck
    provider = MagicMock(wraps=provider_type(policy={}, transport=None), spec_set=["observation", "check"])
    monkeypatch.setattr(operational_api.app.state, "health_provider_check", provider, raising=False)
    for auth, expected in (([], 401), (headers(tenant="tenant-b"), 403)):
        assert call(operational_api, "GET", "/health/status", headers=auth).status_code == expected
    assert not operations and not connections
    for _ in range(2):
        _, snapshot = status(operational_api)
        components = {item["id"]: item for item in snapshot["components"]}
        assert components["litellm"]["status"] == gateway_status
        assert components["litellm"]["reason_code"] == gateway_reason
        assert components["processor"]["status"] == "ok"
        assert components["azure_cost_api"]["status"] == "degraded"
        assert components["openrouter"]["status"] == "unknown"
        assert components["openrouter"]["verified_at"] is None
        assert components["openrouter"]["check_id"] is None
    assert [op for op, args in operations].count("litellm_liveliness") == (2 if enabled else 0)
    assert [op for op, args in operations].count("http") == 4
    for host, conn in connections:
        assert conn.request.call_args.args[0] == "GET"
        assert conn.request.call_args.args[1] == ("/health/liveliness" if host == "synthetic-gateway.invalid" else "/health")
        conn.close.assert_called_once()
    provider.check.assert_not_called()
    assert provider.observation.call_count == 2

def test_simulator_health_and_real_result_retained_until_new_timeout(operational_api, monkeypatch, main_module):
    from test_health_provider_admission_jup047 import build, check
    service, gateway, clock = build(main_module)
    first = check(service)
    routes = importlib.import_module("app.api.routes.health")
    monkeypatch.setattr(operational_api.app.state, "health_provider_check", service, raising=False)
    def probes(callbacks, *, probe_seconds, overall_seconds):
        assert (probe_seconds, overall_seconds) == (8, 18)
        return [
            {"id": name, "status": "ok", "reason_code": "none", "latency_ms": 0}
            for name in callbacks
        ]
    monkeypatch.setattr(routes, "run_probes", probes)
    clock.advance(601)
    _, body = status(operational_api)
    items = {item["id"]: item for item in body["components"]}
    assert items["azure_cost_api"]["status"] == "ok"
    assert items["azure_cost_api"]["source_kind"] == "simulated"
    assert items["litellm"]["status"] == "ok" and items["litellm"]["source_kind"] == "live"
    assert items["openrouter"]["status"] == "ok"
    assert items["openrouter"]["expires_at"] is None
    assert utc(items["openrouter"]["checked_at"]) == first["checked_at"]
    gateway.error = TimeoutError("synthetic-private")
    later = check(service, "new-timeout")
    _, body = status(operational_api)
    item = next(item for item in body["components"] if item["id"] == "openrouter")
    assert item["status"] == "unknown" and item["reason_code"] == "timeout"
    assert utc(item["verified_at"]) == first["verified_at"]
    assert item["check_id"] == first["check_id"]
    assert utc(item["last_attempt_at"]) == later["last_attempt_at"]
    assert len(gateway.requests) == 2, "The two authenticated GETs must not infer"


@pytest.mark.parametrize("budget", [2, 4.5, 8])
def test_operational_route_applies_configured_probe_budget_with_fixed_aggregate(operational_api, monkeypatch, budget):
    from app.core.config import get_settings
    monkeypatch.setenv("HEALTH_PROBE_TIMEOUT_SECONDS", str(budget))
    get_settings.cache_clear()
    routes = importlib.import_module("app.api.routes.health")
    probes = MagicMock(return_value=[])
    monkeypatch.setattr(routes, "run_probes", probes)
    response = call(operational_api, "GET", "/health/status", headers=headers())
    assert response.status_code == 200
    assert probes.call_args.kwargs == {"probe_seconds": budget, "overall_seconds": 18}
    assert len(probes.call_args.args[0]) == 6
    assert response.headers["Cache-Control"] == "no-store"
    operational_api.queue.publish.assert_not_called()
