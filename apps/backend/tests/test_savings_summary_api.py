"""Real session, membership, conversation and SQLite repositories; synthetic provider."""
from unittest.mock import MagicMock

import pytest

from test_tenant_isolation_api import api, call, headers
from tenant_isolation_support import tenant_database, populated_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from app.services.savings_summary import InvalidSavingsEvidence


pytestmark = pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
SELECTION = {"start_date": "2026-09-01", "end_date": "2026-10-01"}


def sample():
    return dict(
        contract_version="savings-input.v1", tenant_id="tenant-a", **SELECTION,
        subscription_id=None, generated_at="2026-10-10T08:00:00Z", data_status="available",
        opportunities=[dict(
            recommendation_id="rec-a", tenant_id="tenant-a", subscription_id="sub-a",
            title="Revisar recurso", action="Validar con responsable", state="proposed",
            currency="EUR", monthly_estimate="12.00", annual_estimate="100.00",
            independent_cost_basis="resource-a", risk="medium", confidence="low",
            assumptions=["Carga estable"], sources=[dict(
                evidence_id="evidence-a", title="Escenario sintetico", reference="scenario:a",
            )],
        )],
    )


def install_provider(api, monkeypatch, value=None):
    provider = MagicMock(spec=["load_snapshot"])
    provider.load_snapshot.return_value = sample() if value is None else value
    monkeypatch.setattr(api.app.state, "savings_provider", provider, raising=False)
    return provider


def send(api, **changes):
    options = dict(headers=headers(), json={"content": "Resumen ejecutivo", "savings_query": SELECTION})
    options.update(changes)
    return call(api, "POST", "/assistant/conversations/own/messages", **options)


def test_summary_persists_complete_evidence_and_does_not_retrieve_or_generate(api, monkeypatch):
    provider = install_provider(api, monkeypatch)
    response = send(api)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["retrieved_context"] == []
    message = body["assistant_message"]
    assert "12.00 EUR/mes; 100.00 EUR/año" in message["content"]
    assert "no es ahorro realizado" in message["content"]
    metadata = message["metadata"]
    assert metadata["citations"] == metadata["source_citations"] == []
    evidence = metadata["savings_evidence"]
    assert evidence["realized_savings"] is None
    assert evidence["source_snapshot"]["opportunities"][0]["sources"][0]["evidence_id"] == "evidence-a"
    provider.load_snapshot.assert_called_once()
    assert provider.load_snapshot.call_args.args[0] == "tenant-a"
    assert provider.load_snapshot.call_args.args[1].model_dump(mode="json") == dict(**SELECTION, subscription_id=None, top_n=5)
    api.embedding.embed.assert_not_called()
    api.vector.search_chunks.assert_not_called()
    reopened = call(api, "GET", "/assistant/conversations/own", headers=headers())
    assert reopened.json()["messages"][-1]["metadata"] == metadata
    assert call(api, "GET", "/assistant/conversations/own", headers=headers("bob", "tenant-b")).status_code == 404


@pytest.mark.parametrize("mode", ["absent", "exception"])
def test_unavailable_provider_is_503_without_partial_messages_or_leaks(api, monkeypatch, mode):
    if mode == "absent":
        monkeypatch.setattr(api.app.state, "savings_provider", None, raising=False)
    else:
        provider = install_provider(api, monkeypatch)
        provider.load_snapshot.side_effect = RuntimeError("SECRET backend endpoint tenant-b")
    response = send(api)
    assert response.status_code == 503
    assert "SECRET" not in response.text
    api.spies["append_message"].assert_not_called()
    api.embedding.embed.assert_not_called()


@pytest.mark.parametrize("bad", ["tenant", "period", "subscription", "duplicate", "money", "source", "row_tenant"])
def test_invalid_provider_evidence_fails_before_writes(api, monkeypatch, bad):
    data = sample()
    if bad == "tenant":
        data["tenant_id"] = "tenant-b"
    elif bad == "period":
        data["start_date"] = "2026-08-01"
    elif bad == "subscription":
        data["subscription_id"] = "sub-b"
    elif bad == "duplicate":
        data["opportunities"] *= 2
    elif bad == "money":
        data["opportunities"][0]["monthly_estimate"] = "NaN"
    elif bad == "source":
        data["opportunities"][0]["sources"] = []
    else:
        data["opportunities"][0]["tenant_id"] = "tenant-b"
    install_provider(api, monkeypatch, data)
    response = send(api)
    assert response.status_code == 502, response.text
    assert response.json()["detail"] == "Invalid savings evidence."
    api.spies["append_message"].assert_not_called()


@pytest.mark.parametrize("user,status", [(None, 401), ("alice", 403), ("bob", 404)])
def test_authorization_precedes_provider(api, monkeypatch, user, status):
    provider = install_provider(api, monkeypatch)
    response = send(api, headers=headers(user, "tenant-b") if user else {})
    assert response.status_code == status, response.text
    provider.load_snapshot.assert_not_called()
    api.spies["append_message"].assert_not_called()


@pytest.mark.parametrize("identifier", ["foreign-marker", "other-owner", "missing"])
def test_inaccessible_conversation_never_queries_provider(api, monkeypatch, identifier):
    provider = install_provider(api, monkeypatch)
    response = call(api, "POST", f"/assistant/conversations/{identifier}/messages", headers=headers(), json={"content": "Resumen", "savings_query": SELECTION})
    assert response.status_code == 404
    provider.load_snapshot.assert_not_called()


@pytest.mark.parametrize("extra", [{"tenant_id": "tenant-b"}, {"opportunities": []}, {"monthly_estimate": "99.00"}])
def test_client_cannot_supply_evidence_or_identity(api, monkeypatch, extra):
    provider = install_provider(api, monkeypatch)
    response = send(api, json={"content": "Resumen", "savings_query": dict(SELECTION, **extra)})
    assert response.status_code == 422
    provider.load_snapshot.assert_not_called()


def test_existing_chat_command_selects_savings_explicitly(api, monkeypatch):
    provider = install_provider(api, monkeypatch)
    response = send(api, json={"content": "/ahorro 2026-09-01 2026-10-01"})
    assert response.status_code == 201, response.text
    assert response.json()["assistant_message"]["metadata"]["savings_evidence"]["selection"]["start_date"] == "2026-09-01"
    provider.load_snapshot.assert_called_once()


@pytest.mark.parametrize("content", ["\x1c", "/ahorro 0 86400", "/ahorro", "/ahorro mañana hoy", "/ahorro 2026-10-01 2026-09-01", "/ahorro 2026-09-01 2026-10-01 tenant-b"])
def test_invalid_command_never_falls_back_to_document_search(api, monkeypatch, content):
    provider = install_provider(api, monkeypatch)
    response = send(api, json={"content": content})
    assert response.status_code == 422
    provider.load_snapshot.assert_not_called()
    api.embedding.embed.assert_not_called()


def test_ordinary_message_preserves_documentary_assistant(api, monkeypatch):
    provider = install_provider(api, monkeypatch)
    response = send(api, json={"content": "Explica FinOps"})
    assert response.status_code == 201
    provider.load_snapshot.assert_not_called()
    api.embedding.embed.assert_called_once_with("Explica FinOps")


def test_adapter_invalid_evidence_keeps_502_classification(api, monkeypatch):
    provider = install_provider(api, monkeypatch)
    provider.load_snapshot.side_effect = InvalidSavingsEvidence()
    response = send(api)
    assert response.status_code == 502
    api.spies["append_message"].assert_not_called()
