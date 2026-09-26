import pytest

from app.core.metrics import ingest_jobs_failed_total
from app.repositories.jobs import JobRepository


class _FakeDatabase:
    def __init__(self):
        self.calls = []

    def update_job_status(self, job_id, status, result=None, *, tenant_id, created_by):
        self.calls.append((job_id, status, result, tenant_id, created_by))


def _read_counter_value() -> float:
    return ingest_jobs_failed_total._value.get()


def test_mark_failed_increments_ingest_failure_counter():
    before = _read_counter_value()
    repository = JobRepository(_FakeDatabase())

    repository.mark_failed("job-1", "ingestion_failed", tenant_id="tenant-a", created_by="alice")

    assert _read_counter_value() == before + 1
    assert repository.database.calls == [("job-1", "failed", {"error": "ingestion_failed"}, "tenant-a", "alice")]


def test_mark_completed_does_not_increment_ingest_failure_counter():
    before = _read_counter_value()
    repository = JobRepository(_FakeDatabase())

    repository.mark_completed("job-1", {"rows": 10}, tenant_id="tenant-a", created_by="alice")

    assert _read_counter_value() == before
    assert repository.database.calls == [("job-1", "completed", {"rows": 10}, "tenant-a", "alice")]


def test_failed_status_write_does_not_count_an_unpersisted_failure():
    class UnavailableDatabase:
        def update_job_status(self, *args, **kwargs):
            raise RuntimeError("database unavailable")

    before = _read_counter_value()
    repository = JobRepository(UnavailableDatabase())

    with pytest.raises(RuntimeError, match="database unavailable"):
        repository.mark_failed("job-1", "ingestion_failed", tenant_id="tenant-a", created_by="alice")

    assert _read_counter_value() == before
