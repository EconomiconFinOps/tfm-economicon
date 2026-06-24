## Context

The backend health endpoint currently returns aggregate service status and per-service statuses. It does not expose when the health check was evaluated.

The active Python version is 3.10.11, so `datetime.UTC` is not available. The implementation will use `timezone.utc` from the standard library and bind it as `UTC` to keep the route expression as `datetime.now(UTC)`.

## Goals / Non-Goals

**Goals:**

- Add a timezone-aware UTC timestamp to each health response.
- Keep the response backward compatible.
- Cover schema and route behavior with backend tests.

**Non-Goals:**

- No frontend rendering changes.
- No processor changes.
- No infrastructure health semantics changes.
- No changes to service names or `ok`/`degraded` logic.

## Decisions

- Add `checked_at: datetime` to `HealthResponse`.
- Generate `checked_at` inside `health()` using `datetime.now(UTC)`.
- Use direct route unit tests with fake dependency objects instead of integration tests requiring external services.
- Archive this change with spec sync because it changes a public API capability.

## Risks / Trade-offs

- Timestamp serialization depends on FastAPI/Pydantic response handling -> Mitigated by typing the schema as `datetime` and testing the route model.
- Python 3.10 lacks `datetime.UTC` -> Mitigated by using `UTC = timezone.utc`.
- Clients may ignore unknown fields -> This is additive and backward compatible.

## Open Questions

- None for this HU.
