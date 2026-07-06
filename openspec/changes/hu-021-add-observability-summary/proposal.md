## Why

The current dashboard reads shallow backend health information, but operators need one backend-owned summary that explains whether the system can serve the application, process jobs, and support retrieval.

The frontend should not call processor internals directly, so the backend needs to aggregate operational health for the dashboard.

## What Changes

- Add a backend endpoint such as `GET /observability/summary` for the system health dashboard.
- Keep `GET /health` as the simple readiness endpoint and avoid breaking its existing response contract.
- Aggregate backend dependency status for CockroachDB, RabbitMQ, and Postgres + pgvector.
- Include processor operational health by calling or reading the processor internal health signal instead of exposing processor directly to the frontend.
- Include a job summary with counts by state when available.
- Include `checked_at` and a top-level `status` such as `ok` or `degraded`.

## Capabilities

### New Capabilities

- `observability-summary`: Provides one backend-owned operational health summary for the frontend dashboard.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: yes; future dashboard work should consume the new backend summary instead of relying only on `GET /health`.
- Backend: yes; adds a new route/service contract and may need configuration for the processor health URL.
- Processor: limited; relies on the existing internal health API and may require response shape alignment.
- Infra/DB: limited; reads existing health signals and job counts, with no new observability database required.

## Impact

- Creates the API foundation for health dashboards and in-app alerts.
- Preserves the architectural rule that the frontend talks only to backend.
- Does not turn pgvector into the primary operational database; CockroachDB remains the source for operational entities and job state.

## Risks / Unknowns

- The backend must handle processor health timeouts without making the whole dashboard hang.
- The summary response should avoid leaking internal URLs, credentials, or stack traces.
- The design should decide whether the endpoint requires authentication and tenant context, matching dashboard security expectations.
