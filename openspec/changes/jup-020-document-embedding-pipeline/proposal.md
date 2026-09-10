JUP: JUP-020
Trello: https://trello.com/c/Mi3kPCOD

## Why

An ordinary `POST /jobs/ingest` receives HTTP 202 but never completes: the
backend publishes a job envelope with `id` and `payload.text_content`, while
the processor graph expects `job_id` and `text_content`. This is the contract
incident recorded on 2026-09-09 in JUP-020 and RF-053-004.

## What Changes

- Adapt the backend job envelope to the graph input explicitly in `IngestTask`.
- Preserve envelope identity, document metadata, existing job status handling,
  safe error reporting, and worker request correlation.
- Add regression coverage for the actual backend envelope and verify ordinary
  HTTP ingestion against RabbitMQ, CockroachDB and pgvector.
- Record reproducible evidence and the remaining JUP-020 scope.

This delivery fixes the handoff incident. Full corpus loading, versioned
metadata on each chunk, idempotent reprocessing and a production embedding
provider remain residual work on the same Trello card. Mock model providers
in the smoke test establish transport and persistence, not semantic quality.

## Capabilities

### New Capabilities

- `document-ingestion-handoff`: map persisted job envelopes to graph input.

### Modified Capabilities

None.

## Impact

Changes the processor task adapter and regression tests. The HTTP API,
RabbitMQ envelope, database schema, graph nodes, provider selection and
infrastructure remain compatible. Runtime dependencies and architecture do
not change; processor test dependencies include the backend's JWT library
so the contract regression can exercise its real producer in isolation.
The existing migration startup race is tracked separately by JUP-096.

Trello consulted through the DockerServer Economicon integration on
2026-09-10. Roles: Victor Mendez leads, Alejandro Aguado pairs, Lucia Mateo
reviews, Paris Arcos Martin validates. Automated checks do not stand in for
those assigned human reviews or attest that they have happened.
