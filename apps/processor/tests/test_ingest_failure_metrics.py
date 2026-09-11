from app.core.metrics import ingest_jobs_failed_total
from app.repositories.jobs import JobRepository


class _FakeDatabase:
    def __init__(self):
        self.calls = []

    def update_job_status(self, job_id, status, result=None):
        self.calls.append((job_id, status, result))


def _read_counter_value() -> float:
    return ingest_jobs_failed_total._value.get()


def test_mark_failed_increments_ingest_failure_counter():
    before = _read_counter_value()
    repository = JobRepository(_FakeDatabase())

    repository.mark_failed("job-1", "ingestion_failed")

    assert _read_counter_value() == before + 1


def test_mark_completed_does_not_increment_ingest_failure_counter():
    before = _read_counter_value()
    repository = JobRepository(_FakeDatabase())

    repository.mark_completed("job-1", {"rows": 10})

    assert _read_counter_value() == before
