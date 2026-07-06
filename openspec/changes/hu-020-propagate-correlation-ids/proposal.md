## Why

A user action can move from frontend to backend, then into RabbitMQ, then through the processor and back into persisted job/vector state.

Without a shared correlation identifier, developers cannot reliably connect the API request that created work with the worker logs and resulting job status.

## What Changes

- Accept `X-Request-Id` on backend HTTP requests and generate one when the client does not send it.
- Return the active request id in backend HTTP responses.
- Propagate a `correlation_id` or equivalent request identifier into ingestion job payloads sent through RabbitMQ.
- Ensure processor logs include the propagated correlation id when consuming and processing a job.
- Ensure job-related backend logs include request id, tenant id, and job id when available.

## Capabilities

### New Capabilities

- `request-job-correlation`: Allows a request that creates asynchronous work to be traced through backend logs, RabbitMQ payloads, and processor logs.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: limited; API client may pass `X-Request-Id`, but backend must still generate one if missing.
- Backend: yes; middleware or request handling must manage request ids and include them in responses and job payloads.
- Processor: yes; worker consumption must read the propagated id and attach it to logs for each job.
- Infra/DB: limited; RabbitMQ job payload shape changes, but no external tracing system is introduced.

## Impact

- Makes request-to-job debugging possible without full distributed tracing.
- Preserves frontend-to-backend-only communication.
- Does not add OpenTelemetry SDK, collector, exporter, trace UI, or vendor-specific tracing.

## Risks / Unknowns

- Existing queued job payloads may not contain a correlation id; worker behavior should remain backward compatible.
- Request ids must be sanitized and bounded to avoid unsafe header values.
- The implementation should define whether `request_id` and `correlation_id` are identical for v1 or separate concepts.
