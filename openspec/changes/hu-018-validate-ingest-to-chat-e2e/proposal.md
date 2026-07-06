## Why

The ingestion, chunking, embeddings, vector storage, and assistant retrieval pieces need an end-to-end validation path so the team can prove the full user journey works together.

This HU documents and validates the happy path from ingested text to assistant answer using local/mock data.

## What Changes

- Define an end-to-end scenario from ingestion to assistant retrieval.
- Use local seed/mock data and deterministic providers where possible.
- Document the operational steps needed to run the scenario.
- Add the minimum automated or scripted checks that are practical in the repo.
- Keep performance, production observability, and deployment hardening out of scope.

## Capabilities

### New Capabilities

- `ingest-to-chat-e2e`: Defines the expected end-to-end behavior from text ingestion to assistant retrieval.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: yes if the smoke workflow exercises the browser flow; otherwise it should still document the frontend-facing path.
- Backend: yes; login, tenant context, job creation, and assistant endpoints are part of the validation path.
- Processor: yes; worker execution, chunking, embeddings, and vector writes are part of the validation path.
- Infra/DB: yes; RabbitMQ, CockroachDB, and Postgres + pgvector must participate in the end-to-end scenario.

## Impact

- Documentation and validation checks across backend, processor, RabbitMQ, CockroachDB, and pgvector.
- May add a focused integration test or smoke script if the team chooses a lightweight route.
- No production deployment changes.

## Risks / Unknowns

- Full stack validation may require Docker Compose and can be slower than unit tests.
- If prior HUs are not complete, this HU may need to defer some assertions until the underlying behavior is available.
