# JUP-020: document ingestion handoff

## Context

`Database.create_job` persists the original request and returns an envelope.
The route adds `request_id`; RabbitMQ serializes it unchanged; the worker
binds request context and invokes `IngestTask`. Passing that envelope directly
to `PipelineRunner` loses the nested document fields from its typed state.

## Decision

Perform a single explicit mapping at the task/graph boundary, within the
existing failure-handling block:

| Graph field | Envelope field |
| --- | --- |
| `job_id` | `id` |
| `tenant_id` | `tenant_id` |
| `source` | `source` |
| `artifact_uri` | `artifact_uri` (optional) |
| `text_content` | `payload.text_content` |
| `metadata` | `payload.metadata`, default `{}` |

Do not unpack the entire payload: payload fields or user metadata must not
overwrite the job/tenant identity or inject graph state. Do not mutate the
queue envelope; retries must see the same content and `request_id`. Worker
correlation remains in structlog context rather than document metadata.

The API validates nonempty text. Invalid envelopes fail inside the task's
existing `mark_failed(..., "ingestion_failed")` path, retaining the exception
cause for the redacted worker logger. The existing worker retry policy is
unchanged. Hand-crafted flat queue messages are not an API contract; direct
`PipelineRunner.run` callers continue to use the graph's flat input.

## Validation

Exercise the actual backend job shape and a real compiled graph, replacing
external model/storage effects only in unit tests. Verify the normal worker
success/ack path and failure/retry correlation. Run an isolated Docker smoke
using HTTP authentication and ordinary ingestion requests, then query jobs,
documents and chunks for the returned identifiers. Run the backend before
the processor to keep the separate JUP-096 migration race out of this check.

The smoke uses the existing character chunker (500 characters, overlap 50)
and deterministic mock embeddings (8 dimensions). These are test settings,
not a newly approved production embedding policy. Metadata reaches the graph
and job result; per-chunk metadata storage remains part of the corpus work.

## Limits and rollout

Deploying the processor adapter is sufficient for already queued valid
backend envelopes. No schema or queue migration is required. A normal PR
against `develop` allows assigned review before integration. This delivery
does not close all of JUP-020 or declare a production RAG pipeline validated.
