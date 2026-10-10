"""Content-free observations of completed logical provider calls (JUP-046)."""

from contextlib import contextmanager
from time import perf_counter

import structlog
from prometheus_client import Counter, Histogram


_CATEGORIES = frozenset({
    "timeout", "connection", "transport", "authentication", "request",
    "redirect", "rate_limit", "upstream", "invalid_response",
})

requests_total = Counter(
    "llm_provider_requests_total",
    "Completed logical LiteLLM provider calls after retries and response validation",
    ["operation", "outcome", "category"],
)

duration_seconds = Histogram(
    "llm_provider_request_duration_seconds",
    "Logical LiteLLM provider call duration including retries and response validation",
    ["operation"],
    buckets=(.1, .25, .5, 1, 2, 5, 10, 20, 30, 60, 120),
)
logger = structlog.get_logger(__name__)


@contextmanager
def observe_provider_call(operation, provider_error):
    """Observe known provider results only; unrelated application errors are not LLM failures."""
    if operation not in {"generation", "embedding"}:
        raise ValueError("Unknown provider operation")
    # Establish zero baselines for categories that have not failed yet. Otherwise
    # Prometheus increase() cannot see the first burst of a newly created series.
    requests_total.labels(operation, "success", "none")
    for category in _CATEGORIES:
        requests_total.labels(operation, "failure", category)
    duration_seconds.labels(operation)
    started = perf_counter()
    try:
        yield
    except provider_error as exc:
        category = exc.category if exc.category in _CATEGORIES else "transport"
        _record(operation, "failure", category, started)
        raise
    else:
        _record(operation, "success", "none", started)


def _record(operation, outcome, category, started):
    elapsed = max(0, perf_counter() - started)
    requests_total.labels(operation, outcome, category).inc()
    duration_seconds.labels(operation).observe(elapsed)
    logger.info(
        "llm_observation", operation=operation, outcome=outcome, category=category,
        duration_ms=round(elapsed * 1000, 2),
    )
