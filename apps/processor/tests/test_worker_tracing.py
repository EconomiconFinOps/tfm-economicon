import json

import structlog

from app.clients.rabbitmq_queue import QueueMessage
from app.core.logging import configure_logging
from app.workers.runner import ProcessorWorker


class _FakeQueue:
    def __init__(self):
        self.acked = []
        self.nacked = []

    def ack(self, delivery_tag):
        self.acked.append(delivery_tag)

    def nack(self, delivery_tag, requeue=True):
        self.nacked.append(delivery_tag)


class _FakeTask:
    def __init__(self):
        self.logger = structlog.get_logger("fake_task")

    def execute(self, job):
        self.logger.info("task_executed", job_id=job["id"])
        return {"status": "completed"}


def _build_worker() -> ProcessorWorker:
    worker = object.__new__(ProcessorWorker)
    worker.queue = _FakeQueue()
    worker.task = _FakeTask()
    return worker


def _captured_logs(capsys) -> list[dict]:
    return [
        json.loads(line)
        for line in capsys.readouterr().out.strip().splitlines()
        if line.strip()
    ]


def test_processing_a_job_with_request_id_correlates_all_logs(capsys):
    configure_logging()
    worker = _build_worker()
    message = QueueMessage(payload={"id": "job-1", "request_id": "req-abc"}, delivery_tag=1)

    worker._process_message(message)

    logs = [line for line in _captured_logs(capsys) if line["logger"] == "fake_task"]
    assert len(logs) == 1
    assert logs[0]["request_id"] == "req-abc"


def test_processing_a_job_without_request_id_generates_one(capsys):
    configure_logging()
    worker = _build_worker()
    message = QueueMessage(payload={"id": "job-2"}, delivery_tag=2)

    worker._process_message(message)

    logs = [line for line in _captured_logs(capsys) if line["logger"] == "fake_task"]
    assert len(logs) == 1
    assert logs[0]["request_id"]


def test_consecutive_jobs_do_not_leak_request_id(capsys):
    configure_logging()
    worker = _build_worker()

    worker._process_message(
        QueueMessage(payload={"id": "job-1", "request_id": "req-first"}, delivery_tag=1)
    )
    capsys.readouterr()
    worker._process_message(
        QueueMessage(payload={"id": "job-2", "request_id": "req-second"}, delivery_tag=2)
    )

    logs = [line for line in _captured_logs(capsys) if line["logger"] == "fake_task"]
    assert len(logs) == 1
    assert logs[0]["request_id"] == "req-second"
