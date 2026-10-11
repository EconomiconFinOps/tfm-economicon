"""JUP-054: persisted job -> LangGraph -> real agent guardrails -> persisted result.

The repository and schema use isolated SQLite through the existing fixture.
Only provider output and vector persistence are doubles; chunking, deterministic
embeddings, AgentRuntime, PipelineRunner and IngestTask execute production code.
This does not exercise CockroachDB, pgvector, a broker or a remote LLM.
"""

import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text

from app.agents.service import AgentRuntime
from app.clients.litellm import ProviderError
from app.core.config import Settings
from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask
from tenant_isolation_support import isolation_database, seed_job, snapshot


def provider_response():
    return {
        "schema_version": "1.0",
        "status": "ok",
        "answer": "  El coste observado cuenta con evidencia.  ",
        "scope": {
            "cloud": "azure",
            "data_environment": "simulated",
            "subscription_ids": ["synthetic-subscription"],
            "period": {"from": "2024-06-01", "to": "2024-07-01"},
        },
        "evidence": [{
            "id": "cost-query:synthetic",
            "kind": "cost_query",
            "title": "Synthetic cost result",
            "source": "Azure Cost Management simulado",
        }],
        "metrics": [{
            "name": "total_cost", "value": "125.50", "unit": "EUR",
            "evidence_ids": ["cost-query:synthetic"],
        }],
        "recommendations": [],
        "assumptions": [],
        "limitations": [],
        "next_actions": ["Revisar el coste por servicio."],
    }


@pytest.fixture
def ingestion(isolation_database):
    database = isolation_database
    job = seed_job(database, identifier="jup054-agent-job")
    job["source"] = job["payload"]["source"] = " Azure-Cost "
    job["payload"]["metadata"] = {"title": "Synthetic monthly report"}
    job["payload"]["text_content"] = (
        "Synthetic Azure cost report. Its content spans multiple chunks so that "
        "successful agent analysis must reach every embedding and the vector sink."
    )
    with database.engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET source=:source, payload=:payload WHERE id=:id"), {
            "id": job["id"], "source": job["source"], "payload": json.dumps(job["payload"]),
        })

    def persisted():
        [row] = snapshot(database, "jobs")[0]
        return row

    events = []
    response = provider_response()
    provider = MagicMock(spec_set=["invoke"])

    def analyze(prompt, *, response_format):
        events.append(("analyze", persisted()["status"]))
        return json.dumps(response)

    provider.invoke.side_effect = analyze
    vector = MagicMock(spec_set=["store_document"])

    def store(**payload):
        events.append(("store", persisted()["status"]))
        return {
            "document_id": payload["job_id"],
            "chunk_count": len(payload["chunks"]),
            "embedding_count": len(payload["embeddings"]),
            "vector_store": "test-double",
            "provider": payload["provider_name"],
        }

    vector.store_document.side_effect = store
    embeddings = MagicMock(wraps=MockEmbeddingProvider(8))
    embeddings.name = "mock"
    return SimpleNamespace(
        database=database, job=job, persisted=persisted, events=events,
        response=response, provider=provider, vector=vector, embeddings=embeddings,
    )


def task(flow, *, route="mock"):
    settings = Settings(_env_file=None, llm_provider=route,
                        litellm_api_key="jup054-synthetic-injected-provider-key")
    runtime = AgentRuntime(settings, provider=flow.provider)
    pipeline = PipelineRunner(runtime, TextChunker(48, 8), flow.embeddings, flow.vector)
    return IngestTask(JobRepository(flow.database), pipeline)


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
def test_validated_agent_response_reaches_persisted_completed_job(ingestion):
    original = deepcopy(ingestion.job)
    result = task(ingestion).execute(ingestion.job)

    row = ingestion.persisted()
    assert row["status"] == "completed"
    assert json.loads(row["result"]) == result
    expected = provider_response()
    expected["answer"] = expected["answer"].strip()
    assert result["insight"] == {
        "provider": "mock", "model": "economicon-chat", "response": expected,
    }
    assert ingestion.job == original
    assert ingestion.events == [("analyze", "running"), ("store", "running")]
    ingestion.provider.invoke.assert_called_once()
    assert ingestion.provider.invoke.call_args.kwargs["response_format"]["json_schema"]["strict"] is True
    ingestion.vector.store_document.assert_called_once()
    saved = ingestion.vector.store_document.call_args.kwargs
    assert saved["job_id"] == ingestion.job["id"]
    assert saved["tenant_id"] == ingestion.job["tenant_id"]
    assert saved["source"] == "azure-cost"
    assert saved["text_content"] == ingestion.job["payload"]["text_content"]
    assert len(saved["chunks"]) > 1
    assert saved["embeddings"] == [MockEmbeddingProvider(8).embed(chunk) for chunk in saved["chunks"]]
    assert ingestion.embeddings.embed.call_count == len(saved["chunks"])
    assert result["embedding_result"]["chunk_count"] == len(saved["chunks"])


@pytest.mark.parametrize("isolation_database", ["sqlite"], indirect=True)
@pytest.mark.parametrize("route", ["mock", "litellm"])
def test_agent_evidence_rejection_fails_job_before_embedding_or_vector_persistence(ingestion, route):
    # Structurally plausible provider output points at evidence absent from its response.
    # The complete graph must propagate rejection before the next node can persist it.
    ingestion.response["metrics"][0]["evidence_ids"] = ["missing-evidence"]
    original = deepcopy(ingestion.job)
    expected_error = ProviderError if route == "litellm" else RuntimeError
    with pytest.raises(expected_error) as caught:
        task(ingestion, route=route).execute(ingestion.job)

    if route == "litellm":
        assert caught.value.category == "invalid_response"
    else:
        assert str(caught.value) == "ingestion_failed"
    row = ingestion.persisted()
    assert row["status"] == "failed"
    assert json.loads(row["result"]) == {"error": "ingestion_failed"}
    assert ingestion.job == original
    assert ingestion.events == [("analyze", "running")]
    ingestion.provider.invoke.assert_called_once()
    ingestion.embeddings.embed.assert_not_called()
    ingestion.vector.store_document.assert_not_called()
