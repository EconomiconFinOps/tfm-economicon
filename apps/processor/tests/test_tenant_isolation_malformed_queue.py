"""RF-086-001/002: permanent malformed deliveries, not transient retries."""
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from app.clients.rabbitmq_queue import RabbitMQQueue
from app.core.logging import configure_logging
from tenant_isolation_support import cockroach_isolation_database, isolation_database, seed_job, snapshot
from test_azure_cost_cockroach_integration import database_factory
from test_secret_boundaries import restore_logging
from test_tenant_isolation_integration import real_queue
from test_tenant_isolation_jobs import assert_discarded, delivery, process


DEPTH_POISON = b"[" * 10000 + b"0" + b"]" * 10000


@pytest.mark.parametrize(
    'isolation_database,escaped,field',
    [
        pytest.param('sqlite', '"\\ud800"', 'created_by', id='sqlite-high-created_by'),
    ],
    indirect=['isolation_database'],
)
def test_unpaired_surrogate_identifier_is_discarded_before_lookup(delivery, monkeypatch, capsys, caplog, field, escaped):
    configure_logging()
    job = deepcopy(delivery.job)
    marker = "foreign-surrogate-marker-"
    job[field] = marker + json.loads(escaped)
    if field == "tenant_id":
        job["payload"]["tenant_id"] = job[field]
    lookup = MagicMock(wraps=delivery.db.fetch_authorized_job)
    monkeypatch.setattr(delivery.db, "fetch_authorized_job", lookup)
    before = snapshot(delivery.db, "jobs")

    process(delivery.worker, job)

    assert snapshot(delivery.db, "jobs") == before
    delivery.pipeline.run.assert_not_called()
    captured = capsys.readouterr()
    assert marker not in captured.out + captured.err + caplog.text
    assert_discarded(delivery.worker.queue)
    lookup.assert_not_called()




def queue_with_deliveries(*deliveries):
    queue = RabbitMQQueue("amqp://127.0.0.1:9/%2F", "jup086.depth-unit")
    queue._connect = MagicMock()
    queue.channel = MagicMock()
    queue.channel.basic_get.side_effect = deliveries
    return queue


def pop_after_poison(queue):
    try:
        return queue.blocking_pop(timeout=2)
    except RecursionError:
        # Assert delivery settlement/continuation, not just the escaped exception.
        return None


def test_json_depth_error_is_discarded_once_then_next_delivery_is_returned():
    following = {"id": "following-valid-delivery", "created_by": "alice"}
    queue = queue_with_deliveries(
        (SimpleNamespace(delivery_tag=18), None, DEPTH_POISON),
        (SimpleNamespace(delivery_tag=19), None, json.dumps(following).encode()),
    )

    message = pop_after_poison(queue)

    queue.channel.basic_nack.assert_called_once_with(delivery_tag=18, requeue=False)
    queue.channel.basic_ack.assert_not_called()
    assert message is not None and message.payload == following and message.delivery_tag == 19
    queue.ack(message.delivery_tag)
    queue.channel.basic_ack.assert_called_once_with(delivery_tag=19)
    assert queue.channel.basic_get.call_count == 2
