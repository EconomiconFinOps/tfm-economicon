## Why

A raw list of service statuses is useful for developers, but operators need clear alert messages when the system is degraded.

The first version should surface actionable in-app alerts without introducing external notification infrastructure.

## What Changes

- Add alert calculation to the backend observability summary.
- Return `alerts[]` with fields such as `id`, `severity`, `component`, `message`, and `checked_at`.
- Create alert rules for CockroachDB unavailable, RabbitMQ unavailable, pgvector unavailable, processor health unavailable or degraded, and failed ingestion jobs.
- Keep alerts computed from current health/job state rather than requiring a new persistent alert table.
- Keep `GET /health` unchanged and place alert details only in the observability summary.

## Capabilities

### New Capabilities

- `in-app-health-alerts`: Shows active operational alerts derived from system health and job state.

### Modified Capabilities

- `observability-summary`: Extends the summary response with computed alert details.

## Architectural Impact

- Frontend: yes; later UI can render active alerts from the summary response.
- Backend: yes; owns alert rules and severity mapping.
- Processor: limited; its health and job outcomes feed alert rules, but the processor does not send notifications.
- Infra/DB: limited; no new external alerting system or alert persistence is required for v1.

## Impact

- Gives operators a clearer degraded-state explanation than service status alone.
- Keeps alerting local to the application dashboard.
- Does not add email, Slack, webhooks, Alertmanager, PagerDuty, or scheduled background alert dispatch.

## Risks / Unknowns

- Alert severity rules should stay simple and predictable in v1.
- Job failure alerts need a clear window or count rule to avoid noisy dashboard states.
- Alerts must not expose sensitive tenant data or raw job payload content.
