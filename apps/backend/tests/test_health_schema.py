from datetime import datetime, timezone

from app.api.routes.health import health
from app.schemas.health import HealthResponse


class FakeDependency:
    def __init__(self, healthy: bool):
        self.healthy = healthy

    def ping(self) -> bool:
        return self.healthy


def test_health_response_accepts_checked_at():
    checked_at = datetime.now(timezone.utc)

    payload = HealthResponse(
        status="ok",
        services={"database": "ok"},
        checked_at=checked_at,
    )

    assert payload.checked_at == checked_at


def test_health_route_returns_utc_checked_at():
    payload = health(
        database=FakeDependency(True),
        queue=FakeDependency(True),
        vector_store=FakeDependency(True),
    )

    assert payload.status == "ok"
    assert payload.checked_at.tzinfo is timezone.utc


def test_health_route_reports_degraded_when_any_service_fails():
    payload = health(
        database=FakeDependency(True),
        queue=FakeDependency(False),
        vector_store=FakeDependency(True),
    )

    assert payload.status == "degraded"
    assert payload.services == {
        "database": "ok",
        "rabbitmq": "failed",
        "vector_store": "ok",
    }
