## Why

The current dashboard has a basic service health block, but it does not yet present enough operational context for someone to understand system status at a glance.

Operators need a richer health dashboard that uses backend-owned observability data while preserving the existing frontend architecture.

## What Changes

- Update the dashboard to consume `GET /observability/summary` from backend.
- Show top-level system status, service/dependency status, processor status, job counts, active alerts, and last checked time.
- Add clear empty, loading, degraded, and unavailable states.
- Add a lightweight refresh behavior suitable for a health dashboard.
- Keep the frontend from calling processor, RabbitMQ, CockroachDB, or pgvector directly.

## Capabilities

### New Capabilities

- `system-health-dashboard`: Displays operational status, dependency health, job summary, and active alerts in the frontend.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: yes; Dashboard page, API client, data hook, and styling are the main implementation surface.
- Backend: yes; depends on the observability summary endpoint being available and stable.
- Processor: no direct frontend integration; processor status is surfaced only through backend.
- Infra/DB: no direct change expected in this HU.

## Impact

- Improves operator visibility without requiring external observability tools.
- Keeps the dashboard focused on current state rather than historical analytics.
- Does not add time-series charts, SLO views, incident timelines, or admin configuration screens.

## Risks / Unknowns

- The UI should remain useful when some summary sections are missing because a service is down.
- Refresh behavior should avoid excessive polling during local development.
- The dashboard should not imply historical monitoring if the backend only provides current-state snapshots.
