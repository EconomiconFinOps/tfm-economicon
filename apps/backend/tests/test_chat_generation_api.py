"""Real auth and SQL persistence; explicit doubles for embeddings and generation."""
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.services.assistant import AssistantService
from app.services.embedding_provider import ProviderError
from tenant_isolation_support import populated_database, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers, citation_record

BANK = json.loads((Path(__file__).resolve().parents[3] / "docs/validation/JUP-069-questions.json").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("tenant_database", ["sqlite", "cockroach"], indirect=True)
def test_generated_reply_persists_with_claims_and_reloads_without_cross_tenant_leak(api, monkeypatch):
    record = citation_record()
    record["content"] = "El presupuesto no es una previsión."
    api.vector.search_chunks.return_value = [record]
    provider = Mock()
    provider.generate.return_value = json.dumps({"status": "answer", "statements": [{
        "text": "El presupuesto y la previsión son conceptos distintos.",
        "support": [{"id": record["chunk_id"], "quote": record["content"]}],
    }]})
    monkeypatch.setattr(api.app.state, "assistant_service", AssistantService(provider))
    response = call(api, "POST", "/assistant/conversations/own/messages", headers=headers(), json={"content": "¿Budget es forecast?"})
    assert response.status_code == 201, response.text
    message = response.json()["assistant_message"]
    assert message["metadata"]["generation"] == "litellm"
    assert message["metadata"]["claims"][0]["evidence_ids"] == ["chunk-1"]
    reloaded = call(api, "GET", "/assistant/conversations/own", headers=headers()).json()
    assert [m["role"] for m in reloaded["messages"]] == ["user", "assistant"]
    assert reloaded["messages"][-1]["metadata"] == message["metadata"]
    assert call(api, "GET", "/assistant/conversations/own", headers=headers("bob", "tenant-b")).status_code == 404


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("failure", ["timeout", "authentication", "invalid_response"])
def test_generation_failure_never_stores_or_returns_invented_answer(api, monkeypatch, failure):
    api.vector.search_chunks.return_value = [citation_record()]
    provider = Mock()
    provider.generate.side_effect = ProviderError(failure)
    monkeypatch.setattr(api.app.state, "assistant_service", AssistantService(provider))
    result = call(api, "POST", "/assistant/conversations/own/messages", headers=headers(), json={"content": "Pregunta"})
    assert result.status_code == 503
    assert "verificable" in result.json()["detail"]
    messages = api.db.fetch_messages("own", "tenant-a", "alice")
    assert [m["role"] for m in messages] == ["user"]


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_too_long_question_rejected_before_retrieval_or_generation(api):
    result = call(api, "POST", "/assistant/conversations/own/messages", headers=headers(), json={"content": "x" * 4001})
    assert result.status_code == 422
    api.embedding.embed.assert_not_called()
    api.spies["append_message"].assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
def test_cost_generation_keeps_tenant_scoped_tool_evidence(api, monkeypatch):
    from test_ownership_questions import billing_double, request_body
    api.spies["fetch_billing_summary"].side_effect = lambda *args, **kwargs: billing_double()
    provider = Mock()
    def generate(system, context, schema):
        source = json.loads(context)["untrusted_sources"][0]
        assert source["kind"] == "cost"
        quote = "Gasto de la selección: 9.01 EUR (4 registros)."
        assert quote in source["text"]
        return json.dumps({"status": "answer", "statements": [{"text": "Se registran 9.01 EUR en la selección.",
            "support": [{"id": source["id"], "quote": quote}]}]})
    provider.generate.side_effect = generate
    monkeypatch.setattr(api.app.state, "assistant_service", AssistantService(provider))
    result = call(api, "POST", "/assistant/conversations/own/messages", headers=headers(), json=request_body())
    assert result.status_code == 201, result.text
    metadata = result.json()["assistant_message"]["metadata"]
    assert metadata["cost_evidence"]["selection"]["group_by"] == "application"
    assert metadata["claims"][0]["evidence_ids"] == [metadata["cost_evidence"]["id"]]
    assert metadata["cost_evidence"]["limitations"]
    assert api.spies["fetch_billing_summary"].call_args.args == ("tenant-a",)
    api.vector.search_chunks.assert_not_called()


@pytest.mark.parametrize("tenant_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("case", BANK, ids=lambda case: case["id"])
def test_jup069_questions_abstain_through_chat_api_without_evidence(api, monkeypatch, case):
    """No-context control over the complete bank, not a model-quality evaluation."""
    provider = Mock()
    monkeypatch.setattr(api.app.state, "assistant_service", AssistantService(provider))
    result = call(api, "POST", "/assistant/conversations/own/messages", headers=headers(), json={"content": case["question"]})
    assert result.status_code == 201, result.text
    message = result.json()["assistant_message"]
    assert message["metadata"]["answer_status"] == "insufficient_data"
    assert message["metadata"]["citations"] == []
    assert message["metadata"]["claims"] == []
    provider.generate.assert_not_called()
