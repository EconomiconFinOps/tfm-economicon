"""Ordinary admission certificate tests; synthetic files and forbidden network.

Paris decision 07/10: historical nonzero uncertainty is retained, not a veto.
No financial exception, fabricated reconciliation, operator key or live ledger.
"""
import hashlib
import importlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import SecretStr
from test_health_provider_admission_jup047 import (
    Gateway, build, check, main_module, no_network, policy, resource_mocks,
    restore_logging,
)

NOW = datetime(2026, 10, 7, 22, 0, tzinfo=timezone.utc)
KEY = "synthetic-ordinary-policy-key"


class CertificateClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW if tz else NOW.replace(tzinfo=None)


def certificate(runtime, **changes):
    data = policy(
        known_spend_usd="0.000009225", uncertain_usd="0",
        pending_usd="0", known_execution_calls=1, execution_calls_limit=2,
        additional_limits_usd=["0.40"],
    )
    data.update(
        price_checked_at=(NOW-timedelta(minutes=2)).isoformat(),
        reconciled_at=(NOW-timedelta(seconds=90)).isoformat(),
        valid_from=(NOW-timedelta(minutes=1)).isoformat(),
        valid_until=(NOW+timedelta(hours=1)).isoformat(),
        instance_id=runtime.INSTANCE_ID,
        single_replica_verified=True, single_process_verified=True,
        credential_dedicated=True, credential_alias_only=True,
        credential_sha256=hashlib.sha256(KEY.encode()).hexdigest(),
        gateway_base_url="http://synthetic-gateway.invalid",
        routing_config_sha256="a"*64,
        routing_alias="economicon-chat", routing_model="openrouter/z-ai/glm-5.2",
        routing_provider="deepinfra/fp4", input_envelope_certified=True,
        gateway_retries=0, router_retries=0, reasoning_enabled=False,
        allow_fallbacks=False, privacy_verified=True,
        execution_id="synthetic-jup047-trial",
        ledger_reference="synthetic-private-ledger",
        authorization_reference="synthetic-authorized-second-check",
    )
    data.update(changes)
    return {k: str(v) if isinstance(v, Decimal) else v for k, v in data.items()}


def fixture_policy(main_module, monkeypatch, tmp_path, **changes):
    runtime = importlib.import_module("app.services.system_health_runtime")
    monkeypatch.setattr(runtime, "datetime", CertificateClock)
    data = certificate(runtime, **changes)
    path = tmp_path/"ordinary-certificate.json"
    settings = SimpleNamespace(
        health_provider_enabled=True, health_provider_policy_path=str(path),
        health_provider_api_key=SecretStr(KEY),
        litellm_base_url="http://synthetic-gateway.invalid",
    )
    return runtime, settings, data, path


def save(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_existing_ordinary_certificate_control_is_loadable(main_module, monkeypatch, tmp_path):
    runtime, settings, data, path = fixture_policy(main_module, monkeypatch, tmp_path)
    digest = save(path, data)
    loaded, actual = runtime._read_policy(settings)
    assert loaded == data and actual == digest
    assert runtime.RuntimeTransport(settings, digest).preflight() == data


@pytest.mark.parametrize("legacy", ["absent", "false", "true"])
def test_ordinary_certificate_retains_nonzero_uncertainty_without_fabricated_reconciliation(
    main_module, monkeypatch, tmp_path, legacy,
):
    runtime, settings, data, path = fixture_policy(
        main_module, monkeypatch, tmp_path, uncertain_usd="0.002016",
    )
    data.pop("reconciled_at")
    if legacy == "absent":
        data.pop("reservation_state_reconciled")
    else:
        data["reservation_state_reconciled"] = legacy == "true"
    digest = save(path, data)
    try:
        loaded, actual = runtime._read_policy(settings)
        preflight = runtime.RuntimeTransport(settings, digest).preflight()
    except (KeyError, ValueError, TypeError) as failure:
        pytest.fail("Valid ordinary certificate rejected solely for recorded uncertainty / absent reconciliation: "+type(failure).__name__, pytrace=False)
    assert loaded == data and preflight == data and actual == digest
    assert loaded["uncertain_usd"] == "0.002016"
    assert loaded["known_spend_usd"] == "0.000009225"
    assert loaded["known_execution_calls"] == 1 and loaded["execution_calls_limit"] == 2
    assert path.read_text(encoding="utf-8") == json.dumps(data)
    assert not any(k in loaded for k in ("trial_exception", "reservation_state_recorded", "state_recorded_at"))
    # Prove admission through the actual parsed ordinary certificate, not a bypass.
    service, gateway, _ = build(main_module, loaded)
    before = service.accounting()
    result = check(service, "authorized-second")
    assert result["http_status"] == 200 and len(gateway.requests) == 1
    assert service.accounting()["uncertain_usd"] == before["uncertain_usd"]
    assert service.accounting()["spent_usd"] == before["spent_usd"]+Decimal("0.00002")


@pytest.mark.parametrize("field,value", [
    ("instance_id", "different-process"),
    ("valid_until", (NOW-timedelta(seconds=1)).isoformat()),
    ("valid_from", (NOW+timedelta(seconds=1)).isoformat()),
    ("price_checked_at", (NOW-timedelta(days=2)).isoformat()),
    ("credential_sha256", "b"*64),
    ("known_execution_calls", True), ("known_execution_calls", -1),
    ("known_execution_calls", 3), ("execution_calls_limit", True),
    ("execution_calls_limit", 0),
    ("known_spend_usd", "NaN"), ("uncertain_usd", "-0.1"),
    ("uncertain_usd", "Infinity"), ("pending_usd", "0.001"),
    ("gateway_retries", 1), ("router_retries", 1),
    ("allow_fallbacks", True), ("routing_model", "unapproved-model"),
    ("routing_provider", "unapproved-provider"),
])
def test_existing_ordinary_negative_gates_remain_effective(
    main_module, monkeypatch, tmp_path, field, value,
):
    runtime, settings, data, path = fixture_policy(main_module, monkeypatch, tmp_path)
    data[field] = value
    digest = save(path, data)
    with pytest.raises((ValueError, KeyError, TypeError)):
        runtime.RuntimeTransport(settings, digest).preflight()


@pytest.mark.parametrize("field", [
    "known_spend_usd", "uncertain_usd", "pending_usd",
    "known_execution_calls", "execution_calls_limit",
    "execution_id", "ledger_reference", "authorization_reference",
])
def test_missing_recorded_state_never_defaults_to_zero(
    main_module, monkeypatch, tmp_path, field,
):
    runtime, settings, data, path = fixture_policy(main_module, monkeypatch, tmp_path)
    data.pop(field)
    digest = save(path, data)
    with pytest.raises((ValueError, KeyError, TypeError)):
        runtime.RuntimeTransport(settings, digest).preflight()


def test_changed_ordinary_certificate_is_not_silently_reloaded(main_module, monkeypatch, tmp_path):
    runtime, settings, data, path = fixture_policy(main_module, monkeypatch, tmp_path)
    digest = save(path, data)
    transport = runtime.RuntimeTransport(settings, digest)
    assert transport.preflight() == data
    data["authorization_reference"] = "different-authorization"
    save(path, data)
    with pytest.raises(ValueError):
        transport.preflight()


def test_expiration_between_admission_and_send_never_calls_isolated_transport(
    main_module, monkeypatch, tmp_path,
):
    runtime, settings, data, path = fixture_policy(main_module, monkeypatch, tmp_path)
    digest = save(path, data)
    transport = runtime.RuntimeTransport(settings, digest)
    assert transport.preflight() == data
    class ExpiredClock(CertificateClock):
        @classmethod
        def now(cls, tz=None):
            return NOW+timedelta(hours=2)
    monkeypatch.setattr(runtime, "datetime", ExpiredClock)
    calls = []
    monkeypatch.setattr(runtime, "isolated_operation", lambda *a, **k: calls.append((a,k)))
    with pytest.raises(ValueError):
        transport({"model":"economicon-chat"}, timeout_seconds=30)
    assert calls == []

