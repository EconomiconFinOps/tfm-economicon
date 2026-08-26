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
