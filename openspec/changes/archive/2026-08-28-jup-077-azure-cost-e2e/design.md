JUP: JUP-077
ADR: docs/adr/ADR-0001-azure-cost-api-simulation.md

## Context

The approved Microsoft public fixture already travels through the simulated
Azure Cost Query contract and JUP-076's defensive HTTP client. JUP-077 closes
the remaining boundary between contractual rows and durable tenant-scoped cost
records without changing the source dataset or requiring an Azure tenant.

## Goals / Non-Goals

**Goals:**

- Preserve positive, zero and negative public costs with exact decimal storage.
- Validate currency/date semantics and produce deterministic canonical hashes.
- Persist reproducible runs and records through a formal CockroachDB migration.
- Make equivalent queries idempotent, isolate tenants and reject unsafe scopes.
- Expose safe completed/failed outcomes and run a real Docker integration test.

**Non-Goals:**

- Anonymize Microsoft's already-public sample dataset or transform source rows.
- Call real Azure, provision a tenant or introduce Microsoft Entra credentials.
- Replace the existing frontend, backend authentication or embeddings pipeline.

## Decisions

### Normalize only validated contractual cost semantics

The normalizer accepts finite numeric costs, canonical three-letter currencies
and optional exact-eight-digit usage dates. Zero and credits are preserved;
equivalent numeric spellings share the same SHA-256 content hash. All remaining
contractual cells are retained as dimensions without inventing private data.

### Keep persistence tenant-scoped, reproducible and transactional

A UUID v5 derived from tenant, case-insensitive subscription and canonical query
identifies a run. Row identities additionally include their position and
canonical hash. Successful replacement and completion occur inside one SQL
transaction; failures remove any stale records and mark the same run failed in
one transaction. Scope is rejected before persistence and successful writes are
restricted to the matching tenant/subscription.

### Use native Cockroach behavior and a constrained development boundary

Both Python services use `sqlalchemy-cockroachdb` with `cockroachdb+psycopg`.
The processor migration constrains run states and links records to their run.
Compose gives CockroachDB a persistent volume, private container connectivity
and loopback-only SQL/admin host bindings; the existing simulator hardening
and bearer safeguards remain unchanged.

### Validate the complete flow without secret exposure

The command initializes migrations, consumes every page, normalizes/persists
the response and verifies its durable row count. Structured events contain
tenant, run and operational counters but never bearer values. Real containers
exercise a 30-row, three-page ingestion, deterministic rerun, tenant separation
and a controlled authentication failure without residual records.

## Risks / Trade-offs

- [Duplicate runs inflate public costs] -> Derive scoped deterministic UUIDs
  and atomically replace existing rows instead of appending duplicates.
- [Malformed amounts or dates reach storage] -> Reject non-finite/non-numeric
  amounts, invalid currency codes and noncanonical or impossible dates.
- [A repeated failed run leaves stale records] -> Delete its previous records
  and mark failure inside the same transaction.
- [Cross-tenant writes leak operational data] -> Validate scope early, include
  tenant/subscription in persistence mutations and test independent run IDs.
- [Docker exposes insecure CockroachDB] -> Bind SQL and admin host ports only
  to loopback while keeping container access on the private Compose network.
