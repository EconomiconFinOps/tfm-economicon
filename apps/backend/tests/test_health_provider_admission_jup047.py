"""Deterministic admission tests: no sockets, pricing lookup, credentials or cost.

Implementation seam: HealthProviderCheck(policy, transport, clock) owns admission;
check(session_id, tenant_id, idempotency_key) returns a sanitized mapping with
http_status/reason_code/verified_at. accounting() reports Decimal spent/pending/
uncertain, and observation() is a non-generative read. The policy below is ONLY
synthetic test data, never certification of an operator's real provider limits.

Red first asserts that the public POST exists on the existing application. Future
service imports are deliberately after that behavior assertion, not collection.
"""
import importlib
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from test_secret_boundaries import main_module, resource_mocks, restore_logging, request


def service_type(main_module):
    assert request(main_module.app, "POST", "/health/provider-check").status_code == 401, "The public health operation must exist and require authentication"
    return importlib.import_module("app.services.health_provider_check").HealthProviderCheck


class Clock:
    def __init__(self):
        self.value = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
    def __call__(self):
        return self.value
    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


def policy(**overrides):
    return {
        "credential_id": "synthetic-diagnostic-credential", "budget_usd": Decimal("0.40"),
        "input_tokens_upper": 1024, "output_tokens_upper": 800,
        "input_price_per_million_usd": Decimal("1.23"),
        "output_price_per_million_usd": Decimal("4.56"), "fees_upper_usd": Decimal("0.0001"),
        "price_verified": True, "routing_verified": True, "effective_cap_verified": True,
        "exclusive_accounting_verified": True, "enforceable_cost_ceiling_verified": True,
        "reservation_state_reconciled": True, "known_spend_usd": "0", "uncertain_usd": "0", "pending_usd": "0", **overrides,
    }


class Gateway:
    def __init__(self, receipt=None, error=None):
        self.requests = []
        self.receipt = receipt or {"model": "openrouter/z-ai/glm-5.2", "provider": "deepinfra/fp4", "usage": {"prompt_tokens": 10, "completion_tokens": 2}, "cost_usd": "0.00002", "route_verified": True, "result_valid": True}
        self.error = error
        self.before_send = None
    def __call__(self, payload, *, timeout_seconds):
        self.requests.append((deepcopy(payload), timeout_seconds))
        if self.before_send:
            self.before_send()
        if self.error:
            raise self.error
        return deepcopy(self.receipt)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Only controlled gateway doubles are permitted in Red")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)


def build(main_module, configured=None, gateway=None):
    clock = Clock()
    gateway = gateway or Gateway()
    service = service_type(main_module)(policy=policy() if configured is None else configured, transport=gateway, clock=clock)
    return service, gateway, clock


def check(service, key="opening", session="session-a", tenant="tenant-a"):
    return service.check(session_id=session, tenant_id=tenant, idempotency_key=key)


@pytest.mark.parametrize("missing", ["price_verified", "routing_verified", "effective_cap_verified", "exclusive_accounting_verified", "enforceable_cost_ceiling_verified"])
def test_uncertifiable_or_restart_state_never_sends(main_module, missing):
    service, gateway, _ = build(main_module, policy(**{missing: False}))
    result = check(service)
    assert result["http_status"] == 429 and result["reason_code"] == "budget_unavailable"
    assert gateway.requests == []


@pytest.mark.parametrize("field,value", [("input_price_per_million_usd", None), ("output_price_per_million_usd", None), ("fees_upper_usd", None), ("input_tokens_upper", None), ("output_tokens_upper", None), ("budget_usd", Decimal("0"))])
def test_missing_billable_bounds_or_budget_never_assumed_free(main_module, field, value):
    service, gateway, _ = build(main_module, policy(**{field: value}))
    assert check(service)["reason_code"] == "budget_unavailable"
    assert gateway.requests == []


def test_decimal_full_envelope_reservation_precedes_exactly_one_synthetic_send(main_module):
    service, gateway, _ = build(main_module)
    expected = (Decimal(1024) * Decimal("1.23") + Decimal(800) * Decimal("4.56")) / Decimal(1_000_000) + Decimal("0.0001")
    gateway.before_send = lambda: assert_reservation(service, expected)
    result = check(service)
    assert result["http_status"] == 200 and result["status"] == "ok"
    assert len(gateway.requests) == 1
    payload, deadline = gateway.requests[0]
    assert payload["model"] == "economicon-chat"
    assert payload["messages"] == [{"role": "user", "content": "Return exactly the two uppercase letters OK. Do not include punctuation, quotes, whitespace, or any other text."}]
    assert payload["max_tokens"] == 32 and payload.get("stream", False) is False
    assert "tools" not in payload and "tenant-a" not in str(payload) and "session-a" not in str(payload)
    assert payload["reasoning"] == {"enabled": False}
    assert payload["provider"]["allow_fallbacks"] is False
    assert deadline == 30
    account = service.accounting()
    assert account["spent_usd"] == Decimal("0.00002")
    assert account["pending_usd"] == account["uncertain_usd"] == Decimal("0")


def assert_reservation(service, expected):
    account = service.accounting()
    assert isinstance(account["pending_usd"], Decimal)
    assert account["pending_usd"] == expected and account["spent_usd"] == Decimal("0")


def test_budget_below_conservative_bound_blocks_send(main_module):
    service, gateway, _ = build(main_module, policy(budget_usd=Decimal("0.004")))
    assert check(service)["reason_code"] == "budget_unavailable"
    assert gateway.requests == []


@pytest.mark.parametrize("outcome", ["timeout", "missing-cost", "zero-cost-positive-usage", "wrong-route"])
def test_unknown_cost_or_route_retains_reserve_and_never_retries(main_module, outcome):
    gateway = Gateway(error=TimeoutError("private-provider-error") if outcome == "timeout" else None)
    if outcome == "missing-cost":
        gateway.receipt.pop("cost_usd")
    elif outcome == "zero-cost-positive-usage":
        gateway.receipt["cost_usd"] = "0"
    elif outcome == "wrong-route":
        gateway.receipt["provider"] = "unapproved-provider"
    service, gateway, clock = build(main_module, gateway=gateway)
    result = check(service)
    if outcome in {"missing-cost", "zero-cost-positive-usage"}:
        assert result["status"] == "ok" and result["verified_at"] == clock.value
    else:
        assert result["status"] != "ok" and result.get("verified_at") is None
    assert "private-provider-error" not in str(result)
    expected = Decimal("0.00500752")
    assert service.accounting()["uncertain_usd"] == expected
    assert service.accounting()["pending_usd"] == Decimal("0")
    clock.advance(61)
    another = check(service, "another-action")
    assert another["http_status"] == 200, "Recorded uncertainty is included in capacity, not an automatic veto"
    assert len(gateway.requests) == 2
    assert service.accounting()["uncertain_usd"] == expected*2


def test_duplicate_action_and_cooldown_do_not_advance_verification(main_module):
    service, gateway, clock = build(main_module)
    first = check(service)
    clock.advance(10)
    duplicate = check(service)
    assert duplicate["verified_at"] == first["verified_at"] and len(gateway.requests) == 1
    refused = check(service, "manual")
    assert refused["http_status"] == 429 and refused["reason_code"] == "cooldown"
    assert 0 < refused["retry_after"] <= 50 and len(gateway.requests) == 1
    clock.advance(50)
    assert check(service, "manual")["http_status"] == 200 and len(gateway.requests) == 2


def test_idempotency_is_bound_to_session_and_tenant(main_module):
    service, gateway, clock = build(main_module)
    first = check(service)
    clock.advance(61)
    second = check(service, session="session-b", tenant="tenant-b")
    assert len(gateway.requests) == 2 and second["verified_at"] != first["verified_at"]


def test_single_active_call_has_no_queue_and_reservation_is_atomic(main_module):
    service, gateway, _ = build(main_module)
    entered, release = threading.Event(), threading.Event()
    def hold():
        entered.set()
        assert release.wait(3), "Controlled test gateway was not released"
    gateway.before_send = hold
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(check, service)
        try:
            assert entered.wait(1)
            second = executor.submit(check, service, "other-action").result(timeout=1)
            assert second["http_status"] == 409 and second["reason_code"] == "busy"
            assert len(gateway.requests) == 1
            assert service.accounting()["pending_usd"] == Decimal("0.00500752")
        finally:
            release.set()
        assert first.result(timeout=1)["http_status"] == 200


def test_six_hourly_twenty_four_daily_calls_are_global_per_credential(main_module):
    service, gateway, clock = build(main_module)
    for hour in range(4):
        for index in range(6):
            assert check(service, f"{hour}-{index}", session=f"session-{index}", tenant=f"tenant-{index}")["http_status"] == 200
            clock.advance(61)
        blocked = check(service, f"hour-{hour}-extra")
        assert blocked["http_status"] == 429
        clock.advance(3600)
    assert len(gateway.requests) == 24
    assert check(service, "day-extra")["http_status"] == 429 and len(gateway.requests) == 24
    clock.advance(24 * 3600)
    assert check(service, "next-day")["http_status"] == 200


def test_passive_reads_and_staleness_preserve_actual_verified_at(main_module):
    service, gateway, clock = build(main_module)
    first = check(service)
    clock.advance(61)
    for _ in range(3):
        observation = service.observation()
        assert observation["status"] == "ok" and observation["reason_code"] == "none"
        assert observation["checked_at"] == first["checked_at"]
        assert observation["verified_at"] == first["verified_at"]
    assert len(gateway.requests) == 1


# Exact base-10 references for two admitted price envelopes, including a
# 31-significant-digit price (13 integer and 18 fractional digits).
PRECISE_ENVELOPES = [
    ("1.231234567890123456", "0.005008784197519486418944", "1", "0.005008784197519486"),
    ("1234567890123.123456789012345123", "1264197519.489826419751948641405952", "1264197520", "1264197519.489826419751948641"),
]


@pytest.mark.parametrize("price,expected,budget,below", PRECISE_ENVELOPES, ids=["over-six-digits", "over-twenty-eight-digits"])
def test_admitted_precise_envelope_is_reserved_exactly_before_send(main_module, price, expected, budget, below):
    service, gateway, _ = build(main_module, policy(input_price_per_million_usd=Decimal(price), budget_usd=Decimal(budget)))
    gateway.before_send = lambda: assert_reservation(service, Decimal(expected))
    result = check(service)
    assert result["http_status"] == 200 and result["status"] == "ok"
    assert len(gateway.requests) == 1


@pytest.mark.parametrize("price,expected,budget,below", PRECISE_ENVELOPES, ids=["over-six-digits", "over-twenty-eight-digits"])
def test_admitted_budget_just_below_exact_reserve_never_sends(main_module, price, expected, budget, below):
    assert Decimal(below) < Decimal(expected)
    service, gateway, _ = build(main_module, policy(input_price_per_million_usd=Decimal(price), budget_usd=Decimal(below)))
    assert check(service)["reason_code"] == "budget_unavailable"
    assert gateway.requests == []
    assert service.accounting()["pending_usd"] == Decimal("0")


@pytest.mark.parametrize("milliseconds", [59_999, 60_000, 60_001, 601_000])
def test_verification_is_retained_without_expiry_or_renewal(main_module, milliseconds):
    service, gateway, clock = build(main_module)
    first = check(service)
    verified_at = first["verified_at"]
    clock.value = verified_at + timedelta(milliseconds=milliseconds)
    observed = service.observation()
    assert observed["status"] == "ok"
    assert observed["reason_code"] == "none"
    assert observed["verified_at"] == verified_at
    assert observed["expires_at"] is None
    assert observed["checked_at"] == first["checked_at"]
    assert len(gateway.requests) == 1, "Reading the boundary cannot send or renew verification"


# Paris-approved 07/10 correction: functionality, identity and billing are
# independent observations. Every gateway below is synthetic and denied network.
@pytest.mark.parametrize("reported_model", [
    "openrouter/z-ai/glm-5.2", "economicon-chat",
    "z-ai/glm-5.2-20260616", "openrouter/z-ai/glm-5.2-20260616", "different-model",
])
def test_functional_alias_version_or_other_name_does_not_fail_availability(main_module, reported_model):
    gateway = Gateway()
    gateway.receipt["model"] = reported_model
    service, gateway, clock = build(main_module, gateway=gateway)
    gateway.before_send = lambda: assert_reservation(service, Decimal("0.00500752"))
    result = check(service)
    assert result["status"] == "ok" and result["reason_code"] == "none"
    assert result["verified_at"] == clock.value
    assert result["reported_model"] == reported_model
    assert result["model_identity"] == "unconfirmed", "Even a matching name is not remote identity proof"
    assert result["reported_cost_usd"] == "0.00002"
    assert result["cost_status"] == "gateway_reported" and result["cost_confirmation"] == "unconfirmed"
    assert service.accounting() == {"spent_usd": Decimal("0.00002"), "pending_usd": Decimal("0"), "uncertain_usd": Decimal("0")}
    assert len(gateway.requests) == 1
    assert gateway.requests[0][0]["model"] == "economicon-chat", "Acceptance of returned name cannot change configured request"


@pytest.mark.parametrize("value", [None, 42, {"name": "different-model"}, "x" * 257, "unsafe://private?token=synthetic-secret", "model\nsynthetic-secret"])
def test_missing_or_unsafe_model_is_unconfirmed_information_not_failed_health(main_module, value):
    gateway = Gateway()
    gateway.receipt["model"] = value
    service, gateway, _ = build(main_module, gateway=gateway)
    result = check(service)
    assert result["status"] == "ok"
    assert result["reported_model"] is None and result["model_identity"] == "unconfirmed"
    assert "synthetic-secret" not in str(result)
    assert len(gateway.requests) == 1


@pytest.mark.parametrize("receipt_change,cost_status,reported_cost", [
    ({"cost_usd": None}, "unavailable", None),
    ({"cost_usd": "0"}, "gateway_reported", "0"),
    ({"cost_usd": "not-money"}, "invalid", None),
    ({"cost_usd": "NaN"}, "invalid", None),
    ({"cost_usd": "Infinity"}, "invalid", None),
    ({"cost_usd": "-0.1"}, "invalid", None),
    ({"cost_usd": "1"}, "gateway_reported", "1"),
    ({"usage": {}}, "gateway_reported", "0.00002"),
    ({"usage": {"prompt_tokens": True, "completion_tokens": 2}}, "gateway_reported", "0.00002"),
    ({"usage": {"prompt_tokens": 1025, "completion_tokens": 2}}, "gateway_reported", "0.00002"),
    ({"usage": {"prompt_tokens": 1, "completion_tokens": 801}}, "gateway_reported", "0.00002"),
    ({"usage": {"prompt_tokens": 0, "completion_tokens": 0}}, "gateway_reported", "0.00002"),
])
def test_valid_functional_response_with_uncertain_cost_keeps_full_reserve(main_module, receipt_change, cost_status, reported_cost):
    gateway = Gateway()
    gateway.receipt.update(receipt_change)
    service, gateway, clock = build(main_module, gateway=gateway)
    result = check(service)
    assert result["status"] == "ok" and result["verified_at"] == clock.value
    assert result["cost_status"] == cost_status and result["reported_cost_usd"] == reported_cost
    assert result["cost_confirmation"] == "unconfirmed" and result["model_identity"] == "unconfirmed"
    assert service.accounting() == {"spent_usd": Decimal("0"), "pending_usd": Decimal("0"), "uncertain_usd": Decimal("0.00500752")}
    # Information changes cannot spend again, silently release, or renew time.
    duplicate = check(service)
    assert duplicate["verified_at"] == result["verified_at"]
    assert len(gateway.requests) == 1
    # Decision08/10 supersedes TTL: passive reads retain the real result.
    clock.advance(61)
    assert service.observation()["reason_code"] == "none"
    assert service.observation()["verified_at"] == result["verified_at"]
    next_result = check(service, "next-action")
    assert next_result["http_status"] == 200 and next_result["status"] == "ok"
    assert next_result["verified_at"] == clock.value
    assert service.accounting()["uncertain_usd"] == Decimal("0.01001504")
    assert len(gateway.requests) == 2


def test_cost_information_does_not_reset_existing_uncertainty_on_authorized_send(main_module):
    configured = policy(uncertain_usd="0.0007", known_execution_calls=1, execution_calls_limit=2)
    service, gateway, _ = build(main_module, configured)
    assert check(service)["http_status"] == 200
    assert service.accounting()["uncertain_usd"] == Decimal("0.0007")
    assert service.accounting()["spent_usd"] == Decimal("0.00002")
    assert len(gateway.requests) == 1


@pytest.mark.parametrize("receipt_change", [{"result_valid": False}, {"route_verified": False}, {"provider": "unapproved-provider"}])
def test_name_and_cost_cannot_override_invalid_functional_result_or_configured_route(main_module, receipt_change):
    gateway = Gateway()
    gateway.receipt.update(receipt_change)
    service, gateway, _ = build(main_module, gateway=gateway)
    result = check(service)
    assert result["status"] != "ok" and result["verified_at"] is None
    assert service.accounting()["uncertain_usd"] == Decimal("0.00500752")
    assert len(gateway.requests) == 1



# Explicitly authorized 07/10 ordinary admission change, still no live calls.
@pytest.mark.parametrize("legacy", ["absent", False, True])
def test_historical_uncertainty_is_not_itself_an_admission_veto(main_module, legacy):
    configured = policy(
        known_spend_usd="0.000009225", uncertain_usd="0.002016", pending_usd="0",
        known_execution_calls=1, execution_calls_limit=2,
        additional_limits_usd=["0.40"],
    )
    if legacy == "absent":
        configured.pop("reservation_state_reconciled")
    else:
        configured["reservation_state_reconciled"] = legacy
    original = deepcopy(configured)
    service, gateway, clock = build(main_module, configured)
    def before_second():
        assert service.accounting() == {
            "spent_usd": Decimal("0.000009225"),
            "uncertain_usd": Decimal("0.002016"),
            "pending_usd": Decimal("0.00500752"),
        }
    gateway.before_send = before_second
    second = check(service, "authorized-second")
    assert second["http_status"] == 200 and second["status"] == "ok"
    assert second["verified_at"] == clock.value and len(gateway.requests) == 1
    assert configured == original, "No retroactive edit/reconciliation of supplied history"
    assert service.accounting() == {
        "spent_usd": Decimal("0.000029225"),
        "uncertain_usd": Decimal("0.002016"), "pending_usd": Decimal("0"),
    }
    # Duplicate is the same second check; no third transport or fresh date.
    clock.advance(10)
    assert check(service, "authorized-second")["verified_at"] == second["verified_at"]
    assert len(gateway.requests) == 1
    clock.advance(51)
    third = check(service, "third-not-authorized")
    assert third["http_status"] == 429 and third["reason_code"] == "budget_unavailable"
    assert len(gateway.requests) == 1
    assert service.accounting()["uncertain_usd"] == Decimal("0.002016")


@pytest.mark.parametrize("delta,admitted", [("0", True), ("-0.000000000000000001", False)])
@pytest.mark.parametrize("limit_kind", ["budget_usd", "additional_limits_usd"])
def test_historical_reserve_exact_remaining_capacity_boundary(main_module, delta, admitted, limit_kind):
    from decimal import localcontext
    h, u, reserve = Decimal("0.000009225"), Decimal("0.002016"), Decimal("0.00500752")
    with localcontext() as context:
        context.prec = 80
        bound = h+u+reserve+Decimal(delta)
    configured = policy(
        known_spend_usd=str(h), uncertain_usd=str(u), pending_usd="0",
        known_execution_calls=1, execution_calls_limit=2,
        budget_usd=bound if limit_kind=="budget_usd" else Decimal("0.40"),
        additional_limits_usd=[str(bound)] if limit_kind=="additional_limits_usd" else ["0.40"],
    )
    service, gateway, _ = build(main_module, configured)
    before = service.accounting()
    result = check(service, "second-boundary")
    assert len(gateway.requests) == int(admitted)
    assert result["http_status"] == (200 if admitted else 429)
    assert service.accounting()["uncertain_usd"] == u
    if not admitted:
        assert result["reason_code"] == "budget_unavailable"
        assert service.accounting() == before


@pytest.mark.parametrize("failure", ["timeout", "unknown-cost"])
def test_second_possible_send_keeps_history_and_consumes_final_call_even_on_failure(main_module, failure):
    gateway = Gateway(error=TimeoutError("private-synthetic") if failure=="timeout" else None)
    if failure=="unknown-cost":
        gateway.receipt.pop("cost_usd")
    service, gateway, clock = build(main_module, policy(
        known_spend_usd="0.000009225", uncertain_usd="0.002016", pending_usd="0",
        known_execution_calls=1, execution_calls_limit=2,
    ), gateway)
    result = check(service, "second-possibly-charged")
    assert result["http_status"] == 200 and len(gateway.requests) == 1
    assert result["status"] == ("unknown" if failure=="timeout" else "ok")
    assert "private-synthetic" not in str(result)
    assert service.accounting() == {
        "spent_usd": Decimal("0.000009225"), "uncertain_usd": Decimal("0.00702352"),
        "pending_usd": Decimal("0"),
    }
    clock.advance(61)
    assert check(service, "third")["reason_code"] == "budget_unavailable"
    assert len(gateway.requests) == 1


@pytest.mark.parametrize("calls", [2, True, -1, "1"])
def test_exhausted_or_invalid_cumulative_counter_does_not_send(main_module, calls):
    service, gateway, _ = build(main_module, policy(
        known_spend_usd="0.000009225", uncertain_usd="0.002016", pending_usd="0",
        known_execution_calls=calls, execution_calls_limit=2,
    ))
    before = service.accounting()
    assert check(service)["reason_code"] == "budget_unavailable"
    assert gateway.requests == [] and service.accounting() == before


# Decision 08/10: retention replaces age expiry; no real transports.
def test_retained_replay_cannot_roll_back_a_later_timeout(main_module):
    service, gateway, clock = build(main_module)
    first = check(service, "retained-original")
    clock.advance(61)
    started = clock.value
    gateway.error = TimeoutError("synthetic-private")
    gateway.before_send = lambda: clock.advance(2)
    later = check(service, "later-timeout")
    assert later["status"] == "unknown" and later["reason_code"] == "timeout"
    assert later["verified_at"] == first["verified_at"]
    assert later["check_id"] == first["check_id"]
    assert later["last_attempt_at"] == started and later["checked_at"] == clock.value
    account = service.accounting()
    clock.advance(7200)
    replay = check(service, "retained-original")
    assert replay["status"] == "ok" and replay["verified_at"] == first["verified_at"]
    assert replay["checked_at"] == first["checked_at"]
    current = service.observation()
    assert current["status"] == "unknown" and current["reason_code"] == "timeout"
    assert current["checked_at"] == later["checked_at"]
    assert current["last_attempt_at"] == later["last_attempt_at"]
    assert current["verified_at"] == first["verified_at"] and current["expires_at"] is None
    assert service.accounting() == account and len(gateway.requests) == 2


def test_refusal_without_send_keeps_retained_result_and_observation_time(main_module):
    service, gateway, clock = build(main_module)
    first = check(service)
    clock.advance(1)
    refused = check(service, "too-early")
    assert refused["http_status"] == 429 and refused["reason_code"] == "cooldown"
    current = service.observation()
    for field in ("status", "reason_code", "checked_at", "verified_at", "check_id", "last_attempt_at"):
        assert current[field] == first[field]
    assert current["expires_at"] is None
    assert len(gateway.requests) == 1
