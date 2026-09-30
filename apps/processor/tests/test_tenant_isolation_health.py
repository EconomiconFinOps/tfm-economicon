from itertools import product
from unittest.mock import MagicMock

import pytest

from app.api.routes.health import health


@pytest.mark.parametrize(
    'states',
    [
        pytest.param((True, True, True), id='states0'),
        pytest.param((True, True, False), id='states1'),
    ],
)
def test_health_preserves_dependency_status_without_querying_business_counts(states):
    dependencies = [MagicMock() for _ in states]
    for dependency, state in zip(dependencies, states):
        dependency.ping.return_value = state
    response = health(*dependencies)
    assert response["status"] == ("ok" if all(states) else "degraded")
    assert response["services"] == dict(zip(("database", "rabbitmq", "vector_store"), ("ok" if state else "failed" for state in states)))
    assert "jobs" not in response
    dependencies[0].fetch_job_counts.assert_not_called()
    for dependency in dependencies:
        dependency.ping.assert_called_once_with()
