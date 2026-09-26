"""RF-086-003: publication outcomes, HTTP admission and scoped SQL races."""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import asyncio
import json
import sqlite3
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, text

from app.core.metrics import ingest_jobs_total
from app.core.runtime_secrets import StartupError
from app.services.rabbitmq_queue import RabbitMQQueue
from tenant_isolation_support import populated_database, rows, tenant_database, tenant_cockroach_database
from test_secret_boundaries import main_module, resource_mocks, restore_logging
from test_tenant_isolation_api import api, call, headers
from test_rabbitmq_publisher import PikaDriver, URL


DETAIL = "Unable to publish the job into RabbitMQ."
BODY = {"tenant_id": "tenant-a", "source": "test", "text_content": "private-body-marker"}
OUTCOMES = [
    ("confirmed", "confirmed", "queued"),
    ("not_sent", "deadline_before_send", "publish_failed"),
    ("rejected", "broker_nack", "publish_failed"),
    ("rejected", "unroutable", "publish_failed"),
    ("unknown", "confirm_timeout", "publish_unknown"),
    ("unknown", "connection_lost", "publish_unknown"),
]


@dataclass(frozen=True)
class OutcomeDouble:
    outcome: str
    code: str

    def __bool__(self):
        # Compatibility only to reach the old route's SQL/HTTP assertions.
        # A separate test below forbids bool on the new result contract.
        return self.outcome == "confirmed"


class PublicationQueue:
    queue_name = "jup086-publication-test"

    def __init__(self, outcome="confirmed", code="confirmed"):
        self.token = object()
        self.reserve = MagicMock(return_value=self.token)
        self.publish = MagicMock(return_value=OutcomeDouble(outcome, code))
        self.cancel = MagicMock()


def set_queue(api, queue):
    api.app.state.queue = queue
    return queue


def post(api):
    return call(api, "POST", "/jobs/ingest", headers=headers(), json=BODY)


def decoded(value):
    return json.loads(value) if isinstance(value, str) else value


def finalize(database, job, outcome="confirmed", code="confirmed", **scope):
    method = getattr(database, "finalize_job_publication", None)
    assert callable(method), "Contract entrypoint absent: Database.finalize_job_publication"
    return method(job["id"], tenant_id=scope.get("tenant_id", job["tenant_id"]),
                  created_by=scope.get("created_by", job["created_by"]), outcome=outcome, code=code)


def pending(database):
    job = database.create_job(BODY, created_by="alice")
    # Set up a pending row independently of create_job, so CAS tests do not
    # accidentally test the INSERT implementation instead of finalization.
    with database.engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET status='publish_pending', result=:result WHERE id=:id"),
                           {"id": job["id"], "result": json.dumps({"publication": {"outcome": "pending", "code": "awaiting_publisher"}})})
    return job








@pytest.mark.parametrize(
    'tenant_database,outcome,code,target',
    [
        pytest.param('sqlite', 'not_sent', 'deadline_before_send', 'publish_failed', id='sqlite-not_sent-deadline_before_send-publish_failed'),
        pytest.param('sqlite', 'rejected', 'broker_nack', 'publish_failed', id='sqlite-rejected-broker_nack-publish_failed'),
        pytest.param('sqlite', 'unknown', 'confirm_timeout', 'publish_unknown', id='sqlite-unknown-confirm_timeout-publish_unknown'),
        pytest.param('cockroach', 'confirmed', 'confirmed', 'queued', id='cockroach-confirmed-confirmed-queued'),
    ],
    indirect=['tenant_database'],
)
def test_http_outcome_is_persisted_and_only_confirmed_is_accepted(api, outcome, code, target):
    queue = set_queue(api, PublicationQueue(outcome, code))
    before = ingest_jobs_total._value.get()
    response = post(api)
    row = rows(api.db, "jobs")[0]
    assert row["status"] == target, "Publish failure left a queued orphan or lost uncertainty"
    assert decoded(row["result"]) == {"publication": {"outcome": outcome, "code": code}}
    assert queue.publish.call_count == 1
    if outcome == "confirmed":
        assert response.status_code == 202
        assert response.json() == {"job_id": row["id"], "status": "queued", "queue": queue.queue_name}
    else:
        assert response.status_code == 503
        assert response.json() == {"detail": DETAIL, "code": "publish_" + outcome, "job_id": row["id"], "retryable": False}
        assert "retry-after" not in response.headers and len(response.content) <= 512
    assert ingest_jobs_total._value.get() == before + (outcome == "confirmed")
















@pytest.mark.parametrize(
    'tenant_database,state,scope',
    [
        pytest.param('sqlite', 'publish_pending', {'tenant_id': 'tenant-b'}, id='sqlite-publish_pending-scope0'),
        pytest.param('sqlite', 'publish_pending', {'created_by': 'bob'}, id='sqlite-publish_pending-scope1'),
        pytest.param('sqlite', 'completed', {'tenant_id': 'tenant-b'}, id='sqlite-completed-scope0'),
        pytest.param('sqlite', 'completed', {'created_by': 'bob'}, id='sqlite-completed-scope1'),
    ],
    indirect=['tenant_database'],
)
def test_cas_zero_row_read_cannot_accept_foreign_progress(tenant_database, scope, state):
    job = pending(tenant_database)
    with tenant_database.engine.begin() as connection:
        connection.execute(text("UPDATE jobs SET status=:state WHERE id=:id"), {"id": job["id"], "state": state})
    before = rows(tenant_database, "jobs")
    method = getattr(tenant_database, "finalize_job_publication", None)
    assert callable(method), "Contract entrypoint absent: Database.finalize_job_publication"
    with pytest.raises((PermissionError, LookupError, RuntimeError, ValueError)):
        finalize(tenant_database, job, **scope)
    assert rows(tenant_database, "jobs") == before






@pytest.mark.parametrize(
    'tenant_database,outcome,code',
    [
        pytest.param('sqlite', 'unknown', 'confirm_timeout', id='sqlite-unknown-confirm_timeout'),
    ],
    indirect=['tenant_database'],
)
def test_sql_finalization_failure_is_503_with_known_outcome(api, monkeypatch, outcome, code):
    queue = set_queue(api, PublicationQueue(outcome, code))
    failure = MagicMock(side_effect=RuntimeError("SELECT private-SQL-marker FROM tenant-b"))
    monkeypatch.setattr(api.db, "finalize_job_publication", failure, raising=False)
    before = ingest_jobs_total._value.get()
    response = post(api)
    row = rows(api.db, "jobs")[0]
    assert response.status_code == 503
    assert response.json() == {"detail": DETAIL, "code": "publication_state_unavailable", "job_id": row["id"],
                               "retryable": False, "publication_outcome": outcome}
    assert row["status"] == "publish_pending"
    assert queue.publish.call_count == 1 and failure.call_count == 1
    assert ingest_jobs_total._value.get() == before


@pytest.mark.parametrize(
    'tenant_database,outcome,code,state',
    [
        pytest.param('cockroach', 'confirmed', 'confirmed', 'completed', id='cockroach-confirmed-confirmed-completed'),
    ],
    indirect=['tenant_database'],
)
def test_worker_wins_between_send_and_http_finalization(api, state, outcome, code):
    queue = set_queue(api, PublicationQueue(outcome, code))
    after_worker = []

    def publish(job, *, reservation=None):
        with api.db.engine.begin() as connection:
            connection.execute(text("UPDATE jobs SET status=:state, result=:result WHERE id=:id AND tenant_id=:tenant AND created_by=:creator"),
                               {"state": state, "result": '{"worker":"preserve-exactly"}', "id": job["id"],
                                "tenant": job["tenant_id"], "creator": job["created_by"]})
        after_worker.extend(rows(api.db, "jobs"))
        return OutcomeDouble(outcome, code)

    queue.publish.side_effect = publish
    response = post(api)
    assert rows(api.db, "jobs") == after_worker
    assert response.status_code == (202 if outcome == "confirmed" else 503)
    assert "preserve-exactly" not in response.text
