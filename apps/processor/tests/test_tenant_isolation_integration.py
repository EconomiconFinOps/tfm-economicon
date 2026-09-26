"""HTTP -> isolated CockroachDB -> RabbitMQ -> worker -> pgvector -> retrieval.

Requires PROCESSOR_COCKROACH_TEST_URL, JUP086_VECTOR_TEST_URL and
JUP086_RABBITMQ_TEST_URL. No default services, dotenv, shared migrations or
queue purge. Only the generated database/queue is removed by these fixtures.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import MagicMock
from urllib.parse import unquote, urlsplit
from uuid import uuid4

import pika
import pytest
from sqlalchemy import event, text

from app.clients.rabbitmq_queue import RabbitMQQueue
from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask
from app.workers.runner import ProcessorWorker
from tenant_isolation_support import clean_owned_database, cockroach_isolation_database, seed_job, snapshot
from test_azure_cost_cockroach_integration import database_factory
from test_tenant_isolation_vector import document, vector_store, vector_snapshot


BACKEND = Path(__file__).resolve().parents[2] / "backend"
HTTP_EXCHANGE = r'''
import asyncio, json, sys
import httpx
from app.main import app
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.database import Database
from app.services.rabbitmq_queue import RabbitMQQueue
from app.services.vector_store import PgVectorQueryStore
from app.services.assistant import AssistantService
from app.services.embedding_provider import MockEmbeddingProvider
args = json.load(sys.stdin)
db = Database(args['database_url'])
queue = RabbitMQQueue(args['queue_url'], args['queue_name'])
vector = PgVectorQueryStore(args['vector_url'])
app.state.database, app.state.queue, app.state.vector_store = db, queue, vector
app.state.assistant_service = AssistantService()
app.state.embedding_provider = MockEmbeddingProvider(8)
token = create_access_token(args['user'], get_settings().auth_secret_key.get_secret_value(), 5)
async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        return await client.request(args['method'], args['path'], headers={'Authorization':'Bearer '+token,'X-Tenant-Id':args['tenant']}, json=args.get('body'))
try:
    queue.start()
    response = asyncio.run(run())
    print('JUP086_HTTP_RESPONSE:' + json.dumps({'status':response.status_code,'body':response.json()}), flush=True)
finally:
    db.dispose(); queue.close(); vector.close()
'''


@pytest.fixture
def real_database(cockroach_isolation_database):
    database = cockroach_isolation_database
    clean_owned_database(database)
    try:
        seed_job(database, identifier="fixture-identity-a")
        seed_job(database, identifier="fixture-identity-b", tenant="tenant-b", creator="bob")
        with database.engine.begin() as connection:
            connection.execute(text("DELETE FROM jobs WHERE id IN ('fixture-identity-a','fixture-identity-b')"))
        yield database
    finally:
        clean_owned_database(database)


@pytest.fixture
def real_queue():
    raw = os.environ.get("JUP086_RABBITMQ_TEST_URL")
    if not raw:
        pytest.skip("JUP086_RABBITMQ_TEST_URL absent: real isolated RabbitMQ not exercised")
    url = urlsplit(raw)
    assert url.scheme == "amqp" and url.hostname in {"127.0.0.1", "localhost"}
    assert url.port not in {None, 5672} and not url.query
    assert unquote(url.path) in {"//", "/"} or unquote(url.path).lstrip("/").startswith("jup086")
    queue = RabbitMQQueue(raw, "jup086.test." + uuid4().hex)
    try:
        queue._connect()
        yield queue
    finally:
        try:
            queue._connect()
            queue.channel.queue_delete(queue=queue.queue_name)
        finally:
            queue.close()


def http(database, queue, vector, user, tenant, method, path, body=None):
    environment = {**os.environ, "PYTHONPATH": str(BACKEND), "PYTHONDONTWRITEBYTECODE": "1"}
    environment.pop("ECONOMICON_ENV_FILE", None)
    completed = subprocess.run([sys.executable, "-B", "-c", HTTP_EXCHANGE], cwd=BACKEND, env=environment, input=json.dumps({
        "database_url": database.engine.url.render_as_string(hide_password=False),
        "queue_url": queue.rabbitmq_url, "queue_name": queue.queue_name,
        "vector_url": vector.engine.url.render_as_string(hide_password=False),
        "user": user, "tenant": tenant, "method": method, "path": path, "body": body,
    }), text=True, capture_output=True, timeout=30, check=True)
    prefix = "JUP086_HTTP_RESPONSE:"
    frames = [line[len(prefix):] for line in completed.stdout.splitlines() if line.startswith(prefix)]
    assert len(frames) == 1, "Backend subprocess must emit exactly one framed response"
    response = json.loads(frames[0])
    assert set(response) == {"status", "body"} and type(response["status"]) is int
    return response


def worker(database, queue, vector):
    instance = ProcessorWorker.__new__(ProcessorWorker)
    instance.queue = queue
    agent = MagicMock()
    agent.invoke.return_value = {"status": "ok"}
    pipeline = PipelineRunner(agent, TextChunker(64, 8), MockEmbeddingProvider(8), vector)
    instance.task = IngestTask(JobRepository(database), pipeline)
    return instance


def produce(database, queue, vector, user="alice", tenant="tenant-a"):
    result = http(database, queue, vector, user, tenant, "POST", "/jobs/ingest", {"tenant_id": tenant, "source": "integration", "text_content": tenant + "-content-marker"})
    assert result["status"] == 202
    message = queue.blocking_pop(timeout=2)
    assert message is not None
    return message


def execute(instance, message):
    try:
        instance._process_message(message)
    except (PermissionError, ValueError, LookupError, RuntimeError):
        pass


def test_two_tenant_http_ingest_worker_retrieval_and_completed_replay(real_database, real_queue, vector_store):
    instance = worker(real_database, real_queue, vector_store)
    for user, tenant in (("alice", "tenant-a"), ("bob", "tenant-b")):
        message = produce(real_database, real_queue, vector_store, user, tenant)
        execute(instance, message)
        assert message.payload.get("created_by") == user
    documents = vector_snapshot(vector_store)[0]
    assert {row["tenant_id"] for row in documents} == {"tenant-a", "tenant-b"}
    conversation = http(real_database, real_queue, vector_store, "alice", "tenant-a", "POST", "/assistant/conversations", {"title": "Own question"})
    assert conversation["status"] == 201
    reply = http(real_database, real_queue, vector_store, "alice", "tenant-a", "POST", f"/assistant/conversations/{conversation['body']['id']}/messages", {"content": "report"})
    assert reply["status"] == 201
    assert "tenant-a-content-marker" in str(reply)
    assert "tenant-b-content-marker" not in str(reply)
    before = (snapshot(real_database, "jobs"), vector_snapshot(vector_store))
    real_queue.channel.basic_publish(exchange="", routing_key=real_queue.queue_name, body=json.dumps(message.payload), properties=pika.BasicProperties(delivery_mode=2))
    replay = real_queue.blocking_pop(timeout=2)
    assert replay is not None
    execute(instance, replay)
    assert (snapshot(real_database, "jobs"), vector_snapshot(vector_store)) == before


@pytest.mark.parametrize(
    'attack',
    [
        pytest.param('revoked', id='revoked'),
    ],
)
def test_real_broker_permanent_rejection_discards_without_persisted_effects(real_database, real_queue, vector_store, attack):
    message = produce(real_database, real_queue, vector_store)
    # Replace only this fixture's message, never purge a queue.
    real_queue.ack(message.delivery_tag)
    job = deepcopy(message.payload)
    if attack == "legacy":
        job.pop("created_by", None)
    elif attack == "content":
        job["payload"]["text_content"] = "foreign-content-marker"
    else:
        with real_database.engine.begin() as connection:
            connection.execute(text("DELETE FROM user_tenants WHERE user_id='alice'" if attack == "revoked" else "DELETE FROM users WHERE id='alice'"))
    real_queue.channel.basic_publish(exchange="", routing_key=real_queue.queue_name, body=json.dumps(job), properties=pika.BasicProperties(delivery_mode=2))
    message = real_queue.blocking_pop(timeout=2)
    before = snapshot(real_database, "jobs"), vector_snapshot(vector_store)
    execute(worker(real_database, real_queue, vector_store), message)
    assert (snapshot(real_database, "jobs"), vector_snapshot(vector_store)) == before
    frame, _, _ = real_queue.channel.basic_get(queue=real_queue.queue_name, auto_ack=False)
    assert frame is None, "Permanent rejection was requeued"


def test_real_vector_connection_loss_rolls_back_then_broker_redelivery_succeeds(real_database, real_queue, vector_store):
    document(vector_store, job="foreign-preserved", tenant="tenant-b")
    foreign_before = vector_snapshot(vector_store)
    message = produce(real_database, real_queue, vector_store)
    instance = worker(real_database, real_queue, vector_store)
    disconnected = []

    def disconnect(connection, cursor, statement, parameters, context, executemany):
        if disconnected or not statement.lstrip().startswith("INSERT INTO document_chunks"):
            return
        assert connection.engine.url.database.startswith("jup086_vector_")
        pid = connection.connection.driver_connection.info.backend_pid
        with vector_store.engine.connect() as control:
            assert control.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid}).scalar_one()
        disconnected.append(pid)

    event.listen(vector_store.engine, "before_cursor_execute", disconnect)
    try:
        with pytest.raises(RuntimeError, match="^ingestion_failed$"):
            instance._process_message(message)
    finally:
        event.remove(vector_store.engine, "before_cursor_execute", disconnect)
    assert len(disconnected) == 1
    assert snapshot(real_database, "jobs")[0][0]["status"] == "failed"
    assert vector_snapshot(vector_store) == foreign_before

    retry = real_queue.blocking_pop(timeout=2)
    assert retry is not None and retry.payload == message.payload
    instance._process_message(retry)
    assert snapshot(real_database, "jobs")[0][0]["status"] == "completed"
    for previous, current in zip(foreign_before, vector_snapshot(vector_store), strict=True):
        assert all(row in current for row in previous)
        assert len(current) == len(previous) + 1
    frame, _, _ = real_queue.channel.basic_get(queue=real_queue.queue_name, auto_ack=False)
    assert frame is None


