## Why

Logging, correlation ids, observability summaries, alerts, and the dashboard need a shared validation path so the team can prove the operational story works end to end.

This HU should make the expected behavior testable and teach future implementers how to check degraded scenarios safely.

## What Changes

- Document and validate the main observability scenarios across backend, processor, RabbitMQ, CockroachDB, and pgvector.
- Include checks for healthy system, RabbitMQ unavailable, pgvector unavailable, processor unavailable, failed job, and request-to-job correlation.
- Define the expected dashboard state and backend summary response for each scenario.
- Add the minimum automated, scripted, or manual checks that are practical for the repo.
- Keep this as validation and documentation, not a production monitoring rollout.

## Capabilities

### New Capabilities

- `observability-scenario-validation`: Defines how to verify logs, correlation ids, summaries, alerts, and dashboard states together.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: yes if dashboard scenarios are validated through UI or browser smoke checks.
- Backend: yes; summary API, alert calculation, and correlation headers are part of the validation path.
- Processor: yes; worker logs and processor health behavior are part of the validation path.
- Infra/DB: yes; local RabbitMQ, CockroachDB, and Postgres + pgvector availability states may be simulated or exercised.

## Impact

- Gives the team a repeatable operational acceptance path for the observability feature group.
- Helps catch regressions where logs, summary API, alerts, and dashboard disagree.
- Does not add production SLOs, external dashboards, deployment automation, or performance monitoring.

## Risks / Unknowns

- Some degraded scenarios may require Docker Compose or dependency stubbing to validate safely.
- Full-stack checks can be slower than unit tests, so the design should separate smoke checks from fast tests.
- If prior HUs are incomplete, this HU may need to defer some assertions until the underlying behavior exists.
