## Why

The assistant already retrieves vector context, but the retrieval path needs to be more traceable and tenant-safe before it can support user trust and future quality evaluation.

This HU improves the retrieval contract without adding streaming or automated quality scoring.

## What Changes

- Make top-k retrieval behavior explicit.
- Ensure retrieval remains filtered by active tenant.
- Return a useful response when no relevant context exists.
- Store or expose metadata about retrieved chunks used for an assistant answer.
- Add focused backend tests around retrieval behavior.

## Capabilities

### New Capabilities

- `assistant-retrieval-traceability`: Defines tenant-safe retrieval and context traceability for assistant answers.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: possible; if retrieval metadata is returned, the UI may display or preserve source/citation details in a later step.
- Backend: yes; assistant route/service, embedding call, vector search, and message metadata handling are the main implementation surface.
- Processor: no direct behavior change; it remains responsible for producing the chunks and embeddings that retrieval consumes.
- Infra/DB: yes; reads from pgvector and may store concise retrieval metadata with CockroachDB conversation messages.

## Impact

- Backend assistant route/service and tests.
- May add metadata to stored assistant messages or response payloads.
- No streaming, RAG quality evaluator, or model provider change.

## Risks / Unknowns

- Exposing too much chunk content in responses can leak implementation details; prefer concise metadata unless product UX requires full context.
- Retrieval tests should use fake vector store responses to avoid pgvector dependency unless integration coverage is explicitly needed.
