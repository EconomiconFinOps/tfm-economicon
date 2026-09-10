from unittest.mock import MagicMock

import structlog

from app.api.routes.jobs import create_ingest_job
from app.db.database import Database
from app.schemas.jobs import IngestJobRequest


class _FakeDatabase(Database):
    def __init__(self):
        self.engine = MagicMock()


class _CapturingQueue:
    queue_name = "processor:jobs"

    def __init__(self):
        self.published = None

    def publish(self, job):
        self.published = job
        return True


def test_ingest_job_payload_carries_the_current_request_id():
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id="req-abc-123")
    queue = _CapturingQueue()
    payload = IngestJobRequest(
        tenant_id="tenant-core",
        source="azure-cost",
        artifact_uri="corpus://monthly-report",
        text_content="report",
        metadata={"title": "Monthly report", "tenant_id": "metadata-is-not-authorization"},
    )

    response = create_ingest_job(
        payload=payload,
        current_user={"id": "user-1"},
        tenant_id="tenant-core",
        database=_FakeDatabase(),
        queue=queue,
    )

    assert queue.published["request_id"] == "req-abc-123"
    assert queue.published["id"] == response.job_id
    assert queue.published["tenant_id"] == payload.tenant_id
    assert queue.published["source"] == payload.source
    assert queue.published["artifact_uri"] == payload.artifact_uri
    assert queue.published["payload"] == payload.model_dump()
    assert "text_content" not in queue.published
    structlog.contextvars.clear_contextvars()


def test_ingest_job_payload_has_no_request_id_when_none_is_bound():
    structlog.contextvars.clear_contextvars()
    queue = _CapturingQueue()

    create_ingest_job(
        payload=IngestJobRequest(
            tenant_id="tenant-core",
            source="aws-cur",
            text_content="report",
        ),
        current_user={"id": "user-1"},
        tenant_id="tenant-core",
        database=_FakeDatabase(),
        queue=queue,
    )

    assert queue.published.get("request_id") is None
