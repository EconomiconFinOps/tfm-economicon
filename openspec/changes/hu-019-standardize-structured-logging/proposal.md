## Why

Backend and processor logs are currently basic text logs, which makes it hard to debug failures across API requests, ingestion jobs, RabbitMQ processing, and assistant retrieval.

Operators and developers need consistent, searchable logs before adding richer health dashboards or alerting behavior.

## What Changes

- Define a structured logging contract shared by backend and processor.
- Emit logs with stable fields such as `service`, `level`, `logger`, `message`, `environment`, `request_id`, `correlation_id`, `tenant_id`, `job_id`, and `error_type` when those values are available.
- Keep sensitive data out of logs, including credentials, tokens, raw documents, assistant prompts, and full retrieved context.
- Add focused tests or assertions around the logging helpers/formatters.
- Keep existing application behavior unchanged except for log shape.

## Capabilities

### New Capabilities

- `structured-service-logging`: Defines consistent log fields for backend and processor runtime events.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: no; the frontend does not emit or consume these service logs in this HU.
- Backend: yes; request handling, health checks, auth, jobs, and assistant flows should be able to attach structured context to logs.
- Processor: yes; worker startup, RabbitMQ consumption, job execution, chunking, embeddings, and vector writes should emit structured context.
- Infra/DB: limited; no new logging stack, database table, or external log collector is introduced.

## Impact

- Improves debugging for backend and processor without changing public APIs.
- Prepares the codebase for later correlation IDs, alert summaries, and operational dashboard work.
- Does not introduce ELK, Loki, Datadog, OpenTelemetry Collector, or managed logging services.

## Risks / Unknowns

- Tests should avoid asserting brittle timestamps or full log lines.
- Logging context must not leak tenant-sensitive data or user secrets.
- If JSON logging is too intrusive for the current codebase, the design can use a stable key-value format as long as fields remain machine-readable.
