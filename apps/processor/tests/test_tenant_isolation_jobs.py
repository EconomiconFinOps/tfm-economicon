"""Queue authority tested against real persisted jobs and current memberships."""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
from sqlalchemy import text
import structlog

from app.clients.rabbitmq_queue import QueueMessage
from app.core.logging import configure_logging
from app.embeddings.chunker import TextChunker
from app.embeddings.providers import MockEmbeddingProvider
from app.graphs.pipeline import PipelineRunner
from app.repositories.jobs import JobRepository
from app.tasks.ingest import IngestTask
from app.workers.runner import ProcessorWorker
from tenant_isolation_support import cockroach_isolation_database, isolation_database, required_scope, seed_job, snapshot
from test_azure_cost_cockroach_integration import database_factory
from test_secret_boundaries import restore_logging


@pytest.fixture
def delivery(isolation_database):
    db = isolation_database
    job = seed_job(db)
    seed_job(db, identifier="job-b-foreign-marker", tenant="tenant-b", creator="bob")
    pipeline = MagicMock()
    pipeline.run.side_effect = lambda payload: {**payload, "summary": "done"}
    worker = ProcessorWorker.__new__(ProcessorWorker)
    worker.queue = MagicMock()
    worker.task = IngestTask(JobRepository(db), pipeline)
    return SimpleNamespace(db=db, job=job, worker=worker, pipeline=pipeline)


def process(worker, job, tag=19):
    try:
        worker._process_message(QueueMessage(job, delivery_tag=tag))
    except (RuntimeError, ValueError, PermissionError, LookupError):
        pass
    finally:
        structlog.contextvars.clear_contextvars()


def assert_discarded(queue, tag=19):
    assert queue.method_calls in ([call.ack(tag)], [call.nack(tag, requeue=False)]), "Permanent rejection must discard exactly once, never requeue"


@pytest.mark.parametrize(
    'isolation_database,attack',
    [
        pytest.param('sqlite', 'tenant-both', id='sqlite-tenant-both'),
        pytest.param('sqlite', 'creator', id='sqlite-creator'),
        pytest.param('sqlite', 'all-controls', id='sqlite-all-controls'),
        pytest.param('sqlite', 'legacy', id='sqlite-legacy'),
        pytest.param('sqlite', 'deleted-creator', id='sqlite-deleted-creator'),
        pytest.param('sqlite', 'revoked-member', id='sqlite-revoked-member'),
    ],
    indirect=['isolation_database'],
)
def test_permanent_rejection_preserves_all_rows_and_never_executes(delivery, attack):
    job = deepcopy(delivery.job)
    if attack == "job-id":
        job["id"] = "job-b-foreign-marker"
    elif attack == "tenant-both":
        job["tenant_id"] = job["payload"]["tenant_id"] = "tenant-b"
    elif attack == "creator":
        job["created_by"] = "bob"
    elif attack == "all-controls":
        job.update(id="job-b-foreign-marker", tenant_id="tenant-b", created_by="bob")
        job["payload"]["tenant_id"] = "tenant-b"
    elif attack == "source-both":
        job["source"] = job["payload"]["source"] = "foreign-source"
    elif attack == "artifact-both":
        job["artifact_uri"] = job["payload"]["artifact_uri"] = "corpus://foreign-artifact"
    elif attack == "content":
        job["payload"]["text_content"] = "foreign-content-marker"
    elif attack == "metadata":
        job["payload"]["metadata"] = {"title": "foreign-metadata-marker"}
    elif attack.startswith("payload-"):
        job["payload"][attack.removeprefix("payload-")] = "foreign-control"
    elif attack == "legacy":
        del job["created_by"]
    elif attack == "blank-creator":
        job["created_by"] = ""
    elif attack == "malformed":
        del job["payload"]["text_content"]
    else:
        with delivery.db.engine.begin() as connection:
            statement = "DELETE FROM users WHERE id = 'alice'" if attack == "deleted-creator" else "DELETE FROM user_tenants WHERE user_id = 'alice'"
            connection.execute(text(statement))
    before = snapshot(delivery.db, "jobs")
    process(delivery.worker, job)
    assert snapshot(delivery.db, "jobs") == before
    delivery.pipeline.run.assert_not_called()
    assert_discarded(delivery.worker.queue)


@pytest.mark.parametrize(
    'isolation_database,invalid',
    [
        pytest.param('sqlite', True, id='sqlite-revoked'),
    ],
    indirect=['isolation_database'],
)
def test_completed_replay_never_overwrites_state_or_result(delivery, invalid):
    with delivery.db.engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET status='completed', result=:result WHERE id='job-a'"), {"result": '{"original":"must-survive"}'})
        if invalid:
            connection.execute(text("DELETE FROM user_tenants WHERE user_id='alice'"))
    before = snapshot(delivery.db, "jobs")
    process(delivery.worker, delivery.job)
    assert snapshot(delivery.db, "jobs") == before
    delivery.pipeline.run.assert_not_called()
    if invalid:
        assert_discarded(delivery.worker.queue)
    else:
        delivery.worker.queue.ack.assert_called_once_with(19)
        delivery.worker.queue.nack.assert_not_called()




@pytest.mark.parametrize(
    'isolation_database,authority,publication_state',
    [
        pytest.param('sqlite', 'authorized', 'publish_pending', id='sqlite-authorized-publish_pending'),
        pytest.param('sqlite', 'authorized', 'publish_unknown', id='sqlite-authorized-publish_unknown'),
    ],
    indirect=['isolation_database'],
)
def test_publication_diagnostic_does_not_replace_worker_authorization(delivery, publication_state, authority):
    import json

    with delivery.db.engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET status=:state, result=:result WHERE id='job-a'"), {
            "state": publication_state,
            "result": json.dumps({"publication": {"outcome": "pending" if publication_state == "publish_pending" else "unknown",
                                                   "code": "awaiting_publisher" if publication_state == "publish_pending" else "confirm_timeout"}}),
        })
        if authority == "revoked":
            connection.execute(text("DELETE FROM user_tenants WHERE user_id='alice'"))
        elif authority == "deleted":
            connection.execute(text("DELETE FROM users WHERE id='alice'"))
    job = deepcopy(delivery.job)
    job["status"] = "queued"
    if authority == "tampered-creator":
        job["created_by"] = "bob"
    before = snapshot(delivery.db, "jobs")
    process(delivery.worker, job)
    after = snapshot(delivery.db, "jobs")
    if authority == "authorized":
        assert after[0][0]["status"] == "completed"
        assert after[0][1] == before[0][1]
        result = after[0][0]["result"]
        assert "publication" not in (json.loads(result) if isinstance(result, str) else result)
        delivery.pipeline.run.assert_called_once()
        delivery.worker.queue.ack.assert_called_once_with(19)
    else:
        assert after == before
        delivery.pipeline.run.assert_not_called()
        assert_discarded(delivery.worker.queue)


@pytest.mark.parametrize(
    'isolation_database',
    [
        pytest.param('sqlite', id='sqlite'),
    ],
    indirect=['isolation_database'],
)
def test_transient_failure_requeues_then_revalidates_on_next_delivery(delivery):
    foreign_before = snapshot(delivery.db, "jobs")[0][1]
    delivery.pipeline.run.side_effect = RuntimeError("temporary dependency failure")
    process(delivery.worker, delivery.job)
    delivery.worker.queue.nack.assert_called_once_with(19, requeue=True)
    delivery.worker.queue.ack.assert_not_called()
    assert delivery.pipeline.run.call_count == 1
    saved = snapshot(delivery.db, "jobs")[0]
    assert saved[0]["status"] == "failed"
    assert saved[1] == foreign_before
    with delivery.db.engine.begin() as connection:
        connection.execute(text("DELETE FROM user_tenants WHERE user_id='alice'"))
    before = snapshot(delivery.db, "jobs")
    delivery.worker.queue.reset_mock()
    delivery.pipeline.reset_mock()
    process(delivery.worker, delivery.job, tag=20)
    assert snapshot(delivery.db, "jobs") == before
    delivery.pipeline.run.assert_not_called()
    assert_discarded(delivery.worker.queue, tag=20)


@pytest.mark.parametrize(
    'isolation_database',
    [
        pytest.param('sqlite', id='sqlite'),
    ],
    indirect=['isolation_database'],
)
def test_metadata_and_model_output_cannot_replace_pipeline_authority(delivery):
    hostile = {"tenant_id": "tenant-b", "job_id": "job-b-foreign-marker", "created_by": "bob", "user_id": "bob", "roles": ["admin"]}
    job = delivery.job
    job["payload"]["metadata"].update(hostile)
    import json
    with delivery.db.engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET payload=:payload WHERE id='job-a'"), {"payload": json.dumps(job["payload"])})
    agent, store = MagicMock(), MagicMock()
    agent.invoke.return_value = hostile
    store.store_document.return_value = {"document_id": "job-a", "chunk_count": 1}
    delivery.worker.task.pipeline = PipelineRunner(agent, TextChunker(64, 8), MockEmbeddingProvider(8), store)
    process(delivery.worker, job)
    store.store_document.assert_called_once()
    persisted = store.store_document.call_args.kwargs
    assert (persisted["job_id"], persisted["tenant_id"], persisted["text_content"]) == ("job-a", "tenant-a", job["payload"]["text_content"])


@pytest.mark.parametrize(
    'isolation_database',
    [
        pytest.param('sqlite', id='sqlite'),
    ],
    indirect=['isolation_database'],
)
def test_worker_diagnostics_do_not_render_foreign_ids_or_untrusted_request_id(delivery, capsys, caplog):
    configure_logging()
    job = deepcopy(delivery.job)
    job["id"] = "job-b-foreign-marker"
    job["request_id"] = "foreign-correlation-marker\nforged-event"
    process(delivery.worker, job)
    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    for marker in ("job-b-foreign-marker", "foreign-correlation-marker", "forged-event"):
        assert marker not in rendered


@pytest.mark.parametrize(
    'isolation_database,tenant,creator',
    [
        pytest.param('sqlite', 'tenant-b', 'alice', id='sqlite-tenant-b-alice'),
        pytest.param('sqlite', 'tenant-a', 'bob', id='sqlite-tenant-a-bob'),
    ],
    indirect=['isolation_database'],
)
def test_direct_status_transition_requires_matching_scope(delivery, tenant, creator):
    scope = required_scope(delivery.db.update_job_status, tenant_id=tenant, created_by=creator)
    before = snapshot(delivery.db, "jobs")
    try:
        delivery.db.update_job_status("job-a", "completed", result={"attempt": True}, **scope)
    except (PermissionError, ValueError, LookupError):
        pass
    assert snapshot(delivery.db, "jobs") == before


@pytest.mark.parametrize(
    'isolation_database,tenant,creator',
    [
        pytest.param('sqlite', 'tenant-b', 'alice', id='sqlite-tenant-b-alice'),
        pytest.param('sqlite', 'tenant-a', 'bob', id='sqlite-tenant-a-bob'),
    ],
    indirect=['isolation_database'],
)
def test_direct_job_lookup_requires_matching_scope(delivery, tenant, creator):
    assert delivery.db.fetch_authorized_job("job-a", tenant_id=tenant, created_by=creator) is None




@pytest.mark.parametrize(
    'isolation_database',
    [
        pytest.param('sqlite', id='sqlite'),
    ],
    indirect=['isolation_database'],
)
def test_worker_loop_sanitizes_dependency_exception_and_cause(delivery, capsys, caplog):
    configure_logging()
    def fail(_):
        try:
            raise ValueError("foreign-cause-marker SELECT secret_column")
        except ValueError as cause:
            raise RuntimeError("foreign-provider-content-marker") from cause
    delivery.pipeline.run.side_effect = fail
    delivery.worker.settings = SimpleNamespace(processor_queue_name="jup086-test")
    delivery.worker._stopping = MagicMock()
    delivery.worker._stopping.is_set.side_effect = [False, True]
    delivery.worker.queue.blocking_pop.return_value = QueueMessage(delivery.job, 19)
    delivery.worker.run_forever()
    captured = capsys.readouterr()
    rendered = captured.out + captured.err + caplog.text
    for marker in ("foreign-cause-marker", "SELECT secret_column", "foreign-provider-content-marker"):
        assert marker not in rendered
    assert "req-jup086-safe" in rendered
    delivery.worker.queue.nack.assert_called_once_with(19, requeue=True)
