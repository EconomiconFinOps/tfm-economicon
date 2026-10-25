JUP: JUP-077
Trello: https://trello.com/c/2ZCQUbhr

## Why

JUP-072 through JUP-076 provide a public Microsoft cost fixture, a contractual
Azure Cost Query simulator and a resilient consuming client, but their output
is not yet normalized, persisted or verified as a complete reproducible flow.

## What Changes

- Normalize finite public cost values, three-letter currencies, strict usage
  dates and arbitrary contractual dimensions without dropping zero or credits.
- Persist tenant-scoped ingestion runs and normalized cost records in
  CockroachDB using formal migrations and its SQLAlchemy dialect.
- Derive stable execution/record identities, replace successful reruns
  atomically and remove stale records after controlled failures.
- Record operational page, retry and row counters plus safe failure classes
  without persisting or logging credentials.
- Wire a reproducible ingestion command and securely bound persistent
  CockroachDB service into the existing Docker Compose environment.
- Verify normalization, invalid scope/data, pagination, persistence,
  idempotency and controlled authentication errors against real containers.

## Capabilities

### New Capabilities

- `azure-cost-end-to-end-ingestion`: Reproducible, tenant-scoped ingestion from
  public Microsoft fixture through simulated Azure API into CockroachDB.

### Modified Capabilities

- None. Existing frontend, embeddings pipeline, Azure contract and simulator
  remain compatible.

## Impact

- Affected areas: processor normalization, repositories, tasks, migrations,
  ingestion command/tests, Cockroach dialect configuration, Compose and docs.
- Dependencies: JUP-013, JUP-014 and JUP-072 through JUP-076.
- No Azure tenant, real credentials, dataset anonymization or external cloud
  connection is introduced.
