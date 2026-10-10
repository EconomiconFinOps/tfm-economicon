# ownership-cost-query Specification

## Purpose
Define authenticated, bounded ownership cost questions with exact billing amounts,
explicit data gaps and persistent financial evidence (JUP-037).
## Requirements
### Requirement: Authorized ownership queries

The system SHALL accept a bounded ownership selection for project, application,
owner, cost_center or a canonical tag, scoped to the authenticated tenant and
conversation owner, with an exclusive UTC end date.

#### Scenario: Exact selection and period
- **WHEN** project Foo has EUR 100 and -20, Bar 40 and missing project 10 in June
- **THEN** selecting Foo returns 80.00 EUR, context 130.00 EUR and missing 10.00 EUR as distinct amounts

#### Scenario: Invalid or unauthorized query
- **WHEN** dates are incomplete, controls or extra fields are supplied, or the conversation belongs to another user or tenant
- **THEN** the request is rejected before financial reads and message writes

### Requirement: Independent dimensions and observed values

The system SHALL read application and owner only from their own tags, preserve
case-sensitive values and existing key aliases, and SHALL NOT infer ownership or
catalog validity from project, organization or placeholder values.

#### Scenario: Distinct dimensions
- **WHEN** a row has project P, application A, cost_center C, owner T and organization O
- **THEN** queries use each named dimension and do not substitute P for A or O for T

#### Scenario: Literal markers
- **WHEN** application values include App, app and Unknown
- **THEN** they remain distinct observed values without asserting valid ownership

### Requirement: Explicit absence and exact money

The system SHALL preserve missing-dimension cost and signed amounts per currency,
sum before rounding and distinguish empty period, absent selection, insufficient
dimension data and actual zero. Source capability SHALL remain unknown without
source metadata.

#### Scenario: No application data
- **WHEN** all period records lack application
- **THEN** the response reports insufficient_data, preserves context and missing costs, and does not assert zero application spend

#### Scenario: Empty selection and zero
- **WHEN** the period is empty, a currency or value is absent, or a matching group nets to zero
- **THEN** distinct reasons identify the first three cases while the actual zero retains its record count

#### Scenario: Precision, currency and overlap
- **WHEN** same-group rows sum to 0.008, negative adjustments exist and currencies differ
- **THEN** the group is 0.01 with signed amounts and separate currencies; overlapping completed ingestion sources instead fail with ambiguous_cost_source before message writes

### Requirement: Persistent financial evidence

The system SHALL persist resolved selection, billing result, source ingestion IDs,
observed days, limitations and reproducible tenant-bound evidence separately from
document citations, without invoking embeddings or generation for ownership queries.

#### Scenario: Reload and mixed conversation
- **WHEN** ownership and document queries share a conversation and it is reopened
- **THEN** each message retains its distinct evidence and financial amounts remain unchanged

#### Scenario: Source snapshot
- **WHEN** provenance is requested
- **THEN** completed source IDs and observed dates come from the same scoped SQL snapshot as the amounts

#### Scenario: Bounded evidence
- **WHEN** the result exceeds 1000 groups or 256 KiB of encoded evidence
- **THEN** it fails explicitly before persistence rather than silently truncating the evidence

#### Scenario: Tenant change or failed request
- **WHEN** tenant or conversation changes while sending, or a new selection fails
- **THEN** stale mutations do not affect the new composer and no previous answer is presented as the failed selection's result
