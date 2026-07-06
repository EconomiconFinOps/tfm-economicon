## Why

The processor consumes jobs from RabbitMQ and updates job state in the database. That path needs stronger reliability checks before ingestion becomes a foundation for more product behavior.

This HU focuses on making worker success and failure behavior predictable without adding advanced queue infrastructure.

## What Changes

- Verify successful jobs are acknowledged and marked completed.
- Verify failing jobs are marked failed with useful error information.
- Verify queue ack/nack behavior is explicit and test-covered.
- Improve focused tests around the worker runner or ingest task.
- Keep dead-letter queues and advanced retry policy out of scope.

## Capabilities

### New Capabilities

- `processor-worker-reliability`: Defines reliable worker behavior for queue consumption and job status updates.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: no; there is no direct UI behavior in this HU.
- Backend: no public API change expected; backend-created jobs remain the worker input.
- Processor: yes; worker, ingest task, queue client, and job status repository are the main implementation surface.
- Infra/DB: yes; RabbitMQ ack/nack behavior and CockroachDB job status updates are part of the reliability boundary.

## Impact

- Processor worker, ingest task, repository, and queue tests.
- May adjust error logging or result payloads for failed jobs.
- No new external infrastructure.

## Risks / Unknowns

- Full RabbitMQ integration tests can be heavy; prefer fakes or focused unit tests unless Docker is already required by the test suite.
- Requeue behavior should stay simple and documented.
