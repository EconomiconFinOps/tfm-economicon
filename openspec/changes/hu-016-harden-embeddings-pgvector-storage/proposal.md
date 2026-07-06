## Why

The processor stores chunks and embeddings in Postgres + pgvector. That storage path needs a stricter contract before retrieval can be considered reliable.

This HU hardens vector storage around embedding dimensions, migrations, and repeated job storage.

## What Changes

- Validate stored embedding dimensions against configured pgvector dimension.
- Ensure vector migrations initialize required tables and extension.
- Make storage behavior for repeated job ids explicit.
- Add focused tests for pgvector store formatting and persistence behavior where practical.
- Keep real paid embedding providers out of scope.

## Capabilities

### New Capabilities

- `vector-storage-contract`: Defines storage requirements for documents, chunks, and embeddings in pgvector.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: no; vector storage is internal infrastructure behavior.
- Backend: no direct retrieval change in this HU; backend benefits later from more reliable vector records.
- Processor: yes; embedding provider contract and `PgVectorStore` behavior are the main implementation surface.
- Infra/DB: yes; Postgres + pgvector migrations, vector dimension, and document/chunk/embedding tables are in scope.

## Impact

- Processor vector store and tests.
- May clarify migration behavior for pgvector.
- No backend retrieval changes in this HU.

## Risks / Unknowns

- Tests that require a real pgvector database can be slower; use unit tests where possible and document any integration requirement.
- Idempotent storage may require delete-and-reinsert or upsert semantics; choose the simplest safe behavior in design.
