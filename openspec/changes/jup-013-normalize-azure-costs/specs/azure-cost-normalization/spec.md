## Purpose

Define a stable FinOps record for Azure costs and optional consumption while
remaining compatible with dynamic Azure Cost Query aggregations.

## ADDED Requirements

### Requirement: Explicit normalized FinOps record
The processor SHALL expose cost, currency, usage date, billing account,
subscription name, resource group, service, project, tags, optional consumed
quantity/unit and additional dimensions as distinct normalized fields.

#### Scenario: Query contains a complete FinOps slice
- **WHEN** an Azure row contains known dimensions, tags and consumption
- **THEN** the processor promotes them to typed fields and retains only unknown
  values in the additional dimensions object

#### Scenario: Query omits a grouping
- **WHEN** Azure does not return service, project or another optional grouping
- **THEN** its normalized field is null and the processor does not infer a value

### Requirement: Provider alias reconciliation
The processor SHALL map audited EA, FOCUS and Azure Query aliases to the same
normalized field and SHALL reject contradictory aliases in one row.

#### Scenario: Equivalent aliases are received
- **WHEN** two otherwise identical rows use `MeterCategory` and `ServiceName`
- **THEN** their normalized records and source hashes are identical

#### Scenario: Contradictory aliases are received together
- **WHEN** aliases for one concept contain different values in the same row
- **THEN** normalization fails before any partial record is persisted

### Requirement: Cost and consumption fidelity
The processor SHALL preserve finite positive, zero and negative costs and
quantities. Quantity and unit SHALL either both be absent or both be present.

#### Scenario: Credit or zero consumption is returned
- **WHEN** Azure returns a finite zero or negative value
- **THEN** the normalized decimal preserves it without filtering the row

#### Scenario: Incomplete consumption pair is returned
- **WHEN** only quantity or only unit is present
- **THEN** normalization fails with a stable validation error

#### Scenario: Consumption is absent
- **WHEN** a valid cost row has neither quantity nor unit
- **THEN** the row is retained with both consumption fields null

#### Scenario: Invalid numeric input is returned
- **WHEN** a cost or supplied consumption quantity is non-numeric, boolean,
  NaN or infinite
- **THEN** normalization fails before any partial cost records are persisted

### Requirement: Stable tag representation
The processor SHALL parse JSON and legacy EA tag serialization, normalize tag
keys to stable snake case, preserve non-empty values and expose `project` as an
explicit field when that tag exists.

#### Scenario: Legacy public fixture tags are returned
- **WHEN** a row uses comma-separated quoted key/value pairs without braces
- **THEN** all valid pairs are retained in the normalized tag object

### Requirement: Additive persistent schema
CockroachDB SHALL add and backfill the explicit normalized fields without
dropping existing cost records, and SHALL index scope, resource group and
service access paths.

#### Scenario: Migration 003 runs after JUP-077 data exists
- **WHEN** old dimensions contain resource group, service or project values
- **THEN** the new nullable fields are backfilled and the source records remain
  available

#### Scenario: Fresh isolated database receives normalized records
- **WHEN** migrations 001 through 003 run on a fresh isolated CockroachDB
  database and valid normalized records are persisted and fetched
- **THEN** typed FinOps fields, tags, optional consumption, source hashes and
  unknown dimensions round-trip with their normalized values
- **AND** the scope, resource group and service indexes exist

#### Scenario: Upgrade preserves legacy records and costs
- **WHEN** an isolated CockroachDB database with migrations 001/002 contains
  valid legacy rows, including positive, zero and negative costs, and migration
  003 is applied
- **THEN** record identities, record counts, individual costs and cost totals
  per tenant, subscription and currency are unchanged
- **AND** available legacy fields are backfilled, missing optional fields stay
  null, and the original dimensions remain available

#### Scenario: Existing-table DDL is committed before dependent backfill
- **WHEN** migration 003 upgrades migrations 001/002 with the six representative
  legacy rows on isolated CockroachDB 24.1.11
- **THEN** its added columns are visible before backfill executes, without an
  undefined-column error, and all existing upgrade preservation checks pass
- **AND** fresh migration execution continues to pass

#### Scenario: Interrupted migration 003 can resume without false completion
- **WHEN** migration 003 fails after committed additive DDL, after committed
  backfill, or after only some indexes have been created
- **THEN** the runner propagates the failure, stops before later migrations,
  and does not record version 003 as applied
- **AND** a subsequent run after resolving the failure completes the missing
  work, preserves record identities, costs, dimensions, already populated typed
  values and non-empty tags, and creates all required indexes without duplicates
- **AND** version 003 is recorded only after the full upgrade succeeds, and a
  further run skips it without changing records or totals

#### Scenario: Completion recording fails after the upgrade commits
- **WHEN** all migration 003 statements commit but its version insert fails
  before committing
- **THEN** the runner reports failure and leaves 003 pending
- **AND** retry safely repeats the upgrade and records version 003 once
- **AND** if the insert instead committed but its acknowledgement was lost,
  the next run observes the marker and skips the completed upgrade

#### Scenario: Transactional execution remains the default
- **WHEN** a processor migration does not explicitly opt out of transactions
- **THEN** its upgrade and version insert share a transaction and a failure
  rolls back both, propagates the error and stops later migrations
- **AND** successful earlier migrations remain applied, while autocommit from
  migration 003 does not change the default for other migrations or connections

#### Scenario: Numeric and mixed legacy tags remain available
- **WHEN** legacy dimensions contain numeric individual tags or combine
  individual tags with serialized tags, including after a partial backfill
- **THEN** migration 003 completes without applying new-ingestion text rejection
  to the historical numeric values and stores their text representation
- **AND** normalized tags contain the available keys from both sources, retain
  all existing typed key/value pairs, and leave original dimensions unchanged

#### Scenario: Partial consumption is completed only with a matching partner
- **WHEN** migration 003 resumes with only a typed quantity or unit populated
- **THEN** it fills the missing component only when the retained component
  matches the corresponding value in a complete legacy source pair
- **AND** conflicting partial values remain unchanged rather than combining
  a quantity and unit from incompatible sources

### Requirement: Existing ingestion idempotency
Normalization SHALL preserve the existing ingestion identity and atomic
replacement of cost rows for the same tenant, subscription and query.

#### Scenario: Normalized ingestion is repeated
- **WHEN** ingestion runs twice against either isolated database after
  migration 003 with the same tenant, subscription, query and source input
- **THEN** the run identity, source hashes, normalized values, record count and
  cost totals per currency are unchanged and no duplicate cost rows are added
