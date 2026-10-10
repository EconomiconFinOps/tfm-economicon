"""Content-free observations of completed provider operations, not retry attempts."""

from contextlib import contextmanager
from time import perf_counter

import structlog
from prometheus_client import Counter, Histogram


requests_total = Counter(
    "llm_provider_requests_total", "Completed logical provider operations",
    ["operation", "outcome", "category"],
)
duration_seconds = Histogram(
    "llm_provider_request_duration_seconds", "Logical provider latency including retries",
    ["operation"], buckets=(.1, .25, .5, 1, 2, 5, 10, 20, 30, 60, 120),
)
_CATEGORIES = frozenset({
    "timeout", "connection", "transport", "authentication", "request",
    "redirect", "rate_limit", "upstream", "invalid_response",
})
logger = structlog.get_logger(__name__)


@contextmanager
def observe_provider_call(operation, provider_error):
    """Only call at a real provider boundary, after local input validation."""
    if operation not in {"embedding", "generation"}:
        raise ValueError("Unsupported provider operation")
    # Seed every bounded outcome before the first call. Otherwise a category's
    # first burst appears as its initial counter value and increase() loses it.
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
