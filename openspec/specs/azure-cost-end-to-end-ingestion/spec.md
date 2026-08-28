# azure-cost-end-to-end-ingestion Specification

## Purpose
TBD - created by archiving change jup-077-azure-cost-e2e. Update Purpose after archive.
## Requirements
### Requirement: Public Azure costs retain trustworthy business semantics

The processor SHALL normalize every contractual row into a finite exact
decimal cost, uppercase three-letter currency, optional strict `yyyyMMdd` date,
preserved dimensions and deterministic SHA-256 content identity.

#### Scenario: Dataset contains zero costs and credits

- **WHEN** the public fixture returns positive, zero and negative numeric costs
- **THEN** all rows remain present with their original financial sign and value.

#### Scenario: Equivalent values use different representations

- **WHEN** equivalent rows contain `1` versus `1.0` or case/whitespace variants
  of the same currency
- **THEN** their normalized canonical content hashes are identical.

#### Scenario: Remote data violates normalization semantics

- **WHEN** a row contains a nonnumeric/nonfinite cost, invalid currency, unsafe
  date representation or impossible calendar date
- **THEN** ingestion fails before inserting partial cost rows.

### Requirement: Persistence remains tenant-scoped and idempotent

The processor SHALL persist formal CockroachDB ingestion runs and normalized
records using deterministic identifiers derived from tenant, case-insensitive
subscription, query definition and row content.

#### Scenario: The same public query runs twice

- **WHEN** an identical tenant/subscription/query returns 30 rows twice
- **THEN** both executions share one run identifier and exactly 30 records
  remain after the second successful atomic replacement.

#### Scenario: Different tenants query the same subscription

- **WHEN** two tenants submit the same contractual Azure query
- **THEN** their execution identifiers and durable records remain independent.

#### Scenario: Scope is missing or contains control characters

- **WHEN** tenant or subscription identifiers are empty, untrimmed or contain
  control characters
- **THEN** the processor rejects the request before starting a database run.

### Requirement: Failed executions expose safe consistent states

The processor SHALL report running, completed and failed states with bounded
operational counters and safe error classes without bearer values or stale rows.

#### Scenario: Authentication fails on a new execution

- **WHEN** the simulator rejects the configured bearer with HTTP `401`
- **THEN** the execution becomes failed, contains zero persisted rows and
  exposes only its safe failure class.

#### Scenario: A previously successful execution fails on rerun

- **WHEN** the same deterministic run subsequently fails authentication or
  normalization
- **THEN** its previous records are removed transactionally and its counters
  consistently report a failed zero-row execution.

#### Scenario: Three pages are ingested successfully

- **WHEN** the public fixture is consumed through three valid simulator pages
- **THEN** the run completes with 30 normalized records, three pages and the
  actual retry count while logs exclude configured bearer credentials.

### Requirement: Reproduction requires no real Azure tenant

The project SHALL provide an executable Docker-backed ingestion command using
the public fixture, existing simulator and privately reachable CockroachDB.

#### Scenario: Developers run the complete local flow

- **WHEN** Docker Compose starts the simulator and persistent CockroachDB and
  invokes the documented processor ingestion command
- **THEN** it initializes migrations, verifies durable row counts and exits
  successfully without Microsoft Entra authentication or cloud connectivity.

#### Scenario: Development database ports are published

- **WHEN** Compose exposes CockroachDB SQL or administration interfaces
- **THEN** host bindings remain restricted to loopback while processor traffic
  stays on the private container network.
