## Why

Chunking is a core step between ingestion and embeddings. It needs an explicit contract so later retrieval behavior can rely on predictable chunk size, overlap, and edge-case handling.

This HU formalizes the current text chunking behavior and makes it configurable and test-covered.

## What Changes

- Define expected chunking behavior for short, long, empty, and whitespace-heavy text.
- Verify configured chunk size and overlap are respected.
- Add focused tests for the chunker.
- Keep file parsing and extraction from PDF/CSV out of scope.

## Capabilities

### New Capabilities

- `configurable-chunking`: Defines how ingested `text_content` is split before embedding.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: no; users do not interact with chunking directly.
- Backend: no API change required; backend continues to submit `text_content` through ingestion jobs.
- Processor: yes; `TextChunker`, processor configuration, and pipeline tests are the main implementation surface.
- Infra/DB: limited; no schema change expected unless design decides to persist extra chunking metadata.

## Impact

- Processor chunker and tests.
- May clarify processor configuration names or validation.
- No backend API changes required.

## Risks / Unknowns

- Overlap behavior can create duplicate-looking content; tests should define acceptable boundaries.
- Empty or whitespace-only text may already be rejected upstream; chunker behavior should still be deterministic.
