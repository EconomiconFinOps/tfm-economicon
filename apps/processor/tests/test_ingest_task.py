"""Regress the real backend message contract through the processor pipeline."""

import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import MagicMock, call

import pytest
import structlog

from app.clients.rabbitmq_queue import QueueMessage
from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider
from app.graphs.pipeline import PipelineRunner
from app.tasks.ingest import IngestTask
from app.workers.runner import ProcessorWorker


BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
PRODUCE_MESSAGE = """
import json
import sys
from unittest.mock import MagicMock

import structlog

from app.api.routes.jobs import create_ingest_job
from app.db.database import Database
from app.schemas.jobs import IngestJobRequest
from app.services.rabbitmq_queue import RabbitMQQueue

request = json.load(sys.stdin)
database = Database.__new__(Database)
database.engine = MagicMock()
queue = RabbitMQQueue("amqp://unit:synthetic@localhost:5672/%2F", "processor:jobs")
queue._connect = MagicMock()
queue.channel = MagicMock()
structlog.contextvars.bind_contextvars(request_id=request["request_id"])
create_ingest_job(
    IngestJobRequest.model_validate(request["payload"]),
    current_user={"id": "test-operator"},
    tenant_id=request["payload"]["tenant_id"],
    database=database,
    queue=queue,
)
print(queue.channel.basic_publish.call_args.kwargs["body"])
"""


def _backend_message(tenant_id="tenant-core"):
    # The two services both use the package name `app`. A fresh interpreter
    # exercises the producer without replacing processor modules in sys.modules.
    payload = {
        "tenant_id": tenant_id,
        "source": " Azure-Cost ",
        "artifact_uri": "corpus://monthly-cost-report",
        "text_content": "A monthly Azure cost report with enough text to produce several chunks.",
        "metadata": {
            "title": "Monthly Azure cost report",
            "region": "westeurope",
            "id": "metadata-document-id",
            "job_id": "metadata-job-id",
            "tenant_id": "metadata-tenant-id",
            "source": "metadata-source",
            "artifact_uri": "metadata-artifact",
        },
    }
    completed = subprocess.run(
        [sys.executable, "-c", PRODUCE_MESSAGE],
        input=json.dumps({"payload": payload, "request_id": "req-jup020-contract"}),
        cwd=BACKEND_ROOT,
        env={**os.environ, "PYTHONPATH": str(BACKEND_ROOT)},
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    return json.loads(completed.stdout)


class _AgentRuntime:
    def __init__(self):
        self.inputs = []
        self.request_ids = []

    def invoke(self, payload, status):
        self.inputs.append(payload.copy())
        self.request_ids.append(structlog.contextvars.get_contextvars().get("request_id"))
        return {"provider": "mock", "status": status}


class _VectorStore:
    def __init__(self, fail_once=False):
        self.documents = {}
        self.fail_once = fail_once

    def store_document(self, **payload):
        if self.fail_once:
            self.fail_once = False
            raise ValueError("temporary storage failure")
        self.documents[payload["job_id"]] = payload
        return {
            "document_id": payload["job_id"],
            "chunk_count": len(payload["chunks"]),
            "embedding_count": len(payload["embeddings"]),
            "vector_store": "pgvector",
            "provider": payload["provider_name"],
        }


def _pipeline(agent, vector_store):
    return PipelineRunner(
        agent,
        TextChunker(chunk_size=32, chunk_overlap=8),
        MockEmbeddingProvider(dimension=8),
        vector_store,
    )


@pytest.mark.parametrize(
    ("tenant_id", "nested_control_fields"),
    [("tenant-core", False), ("tenant-growth", False), ("tenant-core", True)],
)
def test_backend_message_completes_pipeline_with_original_identity_and_metadata(
    tenant_id, nested_control_fields
):
    job = _backend_message(tenant_id)
    if nested_control_fields:
        job["payload"].update({
            "id": "nested-id", "job_id": "nested-job-id", "tenant_id": "nested-tenant",
            "source": "nested-source", "artifact_uri": "nested-artifact",
        })
    original_job = json.loads(json.dumps(job))
    repository = MagicMock()
    agent = _AgentRuntime()
    vector_store = _VectorStore()

    result = IngestTask(repository, _pipeline(agent, vector_store)).execute(job)

    assert "text_content" not in job
    assert "job_id" not in job
    assert job == original_job
    assert result["job_id"] == job["id"]
    assert result["tenant_id"] == tenant_id
    assert result["metadata"] == job["payload"]["metadata"]
    assert agent.inputs[0]["metadata"] == job["payload"]["metadata"]
    saved = vector_store.documents[job["id"]]
    assert saved["job_id"] == job["id"]
    assert saved["tenant_id"] == tenant_id
    assert saved["source"] == "azure-cost"
    assert saved["artifact_uri"] == job["artifact_uri"]
    assert saved["text_content"] == job["payload"]["text_content"]
    assert len(saved["chunks"]) > 1
    assert len(saved["embeddings"]) == len(saved["chunks"])
    assert all(len(embedding) == 8 for embedding in saved["embeddings"])
    assert result["embedding_result"]["document_id"] == job["id"]
    assert repository.method_calls == [
        call.mark_running(job["id"]),
        call.mark_completed(job["id"], result),
    ]


def test_omitted_optional_fields_use_empty_metadata_and_no_artifact():
    job = _backend_message()
    del job["artifact_uri"]
    del job["payload"]["artifact_uri"]
    del job["payload"]["metadata"]
    agent = _AgentRuntime()
    vector_store = _VectorStore()

    result = IngestTask(MagicMock(), _pipeline(agent, vector_store)).execute(job)

    assert result["metadata"] == {}
    assert agent.inputs[0]["metadata"] == {}
    assert vector_store.documents[job["id"]]["artifact_uri"] is None


def test_invalid_envelope_marks_failure_without_running_pipeline():
    job = _backend_message()
    del job["payload"]["text_content"]
    repository = MagicMock()
    pipeline = MagicMock()

    with pytest.raises(RuntimeError, match="^ingestion_failed$") as failure:
        IngestTask(repository, pipeline).execute(job)

    assert isinstance(failure.value.__cause__, KeyError)
    pipeline.run.assert_not_called()
    assert repository.method_calls == [
        call.mark_running(job["id"]),
        call.mark_failed(job["id"], "ingestion_failed"),
    ]


def test_worker_retries_backend_envelope_and_preserves_request_id_until_completion():
    job = _backend_message()
    repository = MagicMock()
    agent = _AgentRuntime()
    vector_store = _VectorStore(fail_once=True)
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = MagicMock()
    worker.task = IngestTask(repository, _pipeline(agent, vector_store))

    try:
        with pytest.raises(RuntimeError, match="^ingestion_failed$"):
            worker._process_message(QueueMessage(job, delivery_tag=41))
        worker.queue.ack.assert_not_called()
        worker.queue.nack.assert_called_once_with(41, requeue=True)

        worker._process_message(QueueMessage(job, delivery_tag=42))

        worker.queue.ack.assert_called_once_with(42)
        assert agent.request_ids == [job["request_id"], job["request_id"]]
        assert list(vector_store.documents) == [job["id"]]
        assert repository.mark_running.call_args_list == [call(job["id"]), call(job["id"])]
        repository.mark_failed.assert_called_once_with(job["id"], "ingestion_failed")
        repository.mark_completed.assert_called_once()
        assert repository.mark_completed.call_args.args[0] == job["id"]
    finally:
        structlog.contextvars.clear_contextvars()
