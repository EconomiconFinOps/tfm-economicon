JUP: JUP-102
Trello: https://trello.com/c/4OJ1OK53

## Why

RF-021-001: the initial vector migration reads the process environment independently
of Settings. A new database configured with dimension 16 only in ECONOMICON_ENV_FILE
is created as vector(8), and the existing startup guard correctly rejects it.

## What Changes

- Pass the store's resolved dimension explicitly to migration 001.
- Preserve Settings precedence, the migration ledger and the existing dimension guard.
- Add offline regression and real PostgreSQL/pgvector acceptance tests.
- Replace the duplicate-export workaround with the effective configuration contract.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `vector-database-runtime`: initialize new schemas from the effective Settings dimension.

## Impact

Processor migration runner, vector migration 001 and its direct test callers.
No automatic resize, reindexing, provider change, new migration version or volume
replacement. Synthetic mock embeddings prove storage and isolation, not model quality.
