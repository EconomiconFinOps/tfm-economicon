JUP: JUP-076
ADR: docs/adr/ADR-0001-azure-cost-api-simulation.md

## Context

JUP-074 and JUP-075 integrated a standalone, authenticated Azure Cost Query
simulator supporting opaque pagination and deterministic failure scenarios.
JUP-076 adds the consuming HTTP boundary inside `apps/processor`; persistence
and the complete ingestion pipeline remain the responsibility of JUP-077.

## Goals / Non-Goals

**Goals:**

- Switch between simulator and future Azure endpoints exclusively through
  validated URL, bearer, API-version and operational settings.
- Traverse all contractual continuation pages without leaking bearer tokens or
  accepting cross-origin, cross-subscription, cross-version or cyclic links.
- Retry only configured transient HTTP conditions using bounded delays.
- Normalize positional rows into named values while rejecting malformed,
  inconsistent, non-numeric and non-finite responses.
- Emit useful structured telemetry without logging credentials, request bodies,
  query strings or public cost rows.

**Non-Goals:**

- Authenticate against Microsoft Entra, provision a tenant or call real Azure
  during project validation.
- Normalize costs into a database schema, apply migrations or persist ingestion
  runs; those belong to JUP-077.
- Modify the existing embeddings pipeline, backend, frontend or Azure fixture.

## Decisions

### Keep transport injectable and isolate bearer handling

`AzureCostClient` accepts an injectable HTTP transport and sleep strategy for
deterministic tests. Runtime transport uses the Python standard library and
explicitly disables all redirects. The configured bearer is stored as Pydantic
`SecretStr`, sent only to verified contractual routes and excluded from logs,
exception messages, Docker build context and settings representations.

### Bind continuations to the configured contract and active subscription

The first URL is built from configured base origin, requested subscription and
API version. Every absolute or relative `nextLink` must retain the exact
scheme/authority, subscription query route and one matching `api-version`,
without fragments. A visited-link set and bounded page count reject cycles and
infinite responses before additional authenticated requests.

### Retry only bounded server-side transient failures

Only `429` and `500` are retried, up to the configured per-page maximum.
Finite numeric `Retry-After` values are clamped to a configured ceiling;
malformed or non-finite headers fall back to exponential backoff. Timeouts and
authentication errors fail explicitly without exposing configured secrets.

### Validate transport-independent column semantics

Every response must expose contractual `columns`, `rows` and `nextLink`.
Columns are non-empty, unique and stable across pages; `PreTaxCost` must be
numeric and finite, and `Currency` must be a string. Row arity follows ordered
columns. Empty final results are accepted, but empty intermediate pages fail.

### Reuse the established simulator and container boundary

Compose injects only configuration into the processor and waits for the
already-hardened simulated API to become healthy. A processor `.dockerignore`
excludes local environments, credentials, dependencies, caches and tests.
Switching to a future Azure endpoint changes configuration rather than client
or normalization code.

## Risks / Trade-offs

- [Bearer is leaked by an untrusted continuation or redirect] -> Verify exact
  origin/path/version and reject automatic redirects before resending tokens.
- [Server returns malformed rows or infinite pagination] -> Validate every
  column/value, detect cycles and cap pages.
- [Retries stall the processor] -> Bound attempts, timeouts, delays and
  `Retry-After`; reject non-finite delay headers.
- [Operational logs disclose sensitive material] -> Log only event names,
  paths, counters, HTTP statuses and delays; mask the configured token.
- [Client and simulator drift] -> Execute shared-contract, simulator, processor
  and real Docker smoke suites against the same public fixture.
