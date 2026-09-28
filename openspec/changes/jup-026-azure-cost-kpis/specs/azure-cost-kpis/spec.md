## ADDED Requirements

Scoped MVP warning/no-replacement handling was accepted by Paris Arcos on
2026-09-27; see [proposal](../../proposal.md#scoped-mvp-decisions). These
requirements retain the technical contract subsequently approved by Paris
on 2026-09-27, including response-v2 strings/null and exact rules.

### Requirement: Scoped period costs from normalized records
The existing billing summary SHALL aggregate normalized pre-tax costs in SQL
under the authorized tenant, using matching tenant/subscription completed runs
and the half-open period defined in design.md. It SHALL preserve existing
authentication/membership behavior without loading the dataset into memory.
GET /billing/summary SHALL remain read-only and SHALL NOT replace ingestion
sources or return ambiguous monetary results alongside a warning.

#### Scenario: Period and tenant boundaries
- **WHEN** records exist inside/outside the period, for another tenant, or inconsistent with their parent run
- **THEN** only matching-tenant/subscription completed records in the period contribute; unauthorized access is rejected before cost reads
- **AND** omitted dates select the current UTC month and invalid pairs return 422

#### Scenario: Alternative ingestions overlap
- **WHEN** multiple completed ingestion IDs contain records for the same selected tenant, subscription and date
- **THEN** the endpoint returns 409 with detail code ambiguous_cost_source and no monetary payload/source IDs
- **AND** same-ID replacement does not cause this conflict
- **AND** this conservative check signals possible overlap, not proof of identical charges; the GET performs no confirmation, replacement or overwrite

### Requirement: Five deterministic cost breakdowns
The summary SHALL support subscription, resource group, service, project and
selected-tag grouping according to design.md. Each included row SHALL contribute
once per currency to both total and chosen breakdown. Missing values SHALL form
a null bucket, never an invented dimension.

#### Scenario: Reference breakdowns
- **WHEN** a normalized reference is queried for each of the five groupings
- **THEN** each result matches independent Decimal expectations, including subscription-scoped resource groups, typed-project precedence and a single selected tag
- **AND** ordering is deterministic and multiple tags do not duplicate cost

#### Scenario: Default input lacks service names
- **WHEN** ResourceId + ResourceGroup ingestion has no service_name
- **THEN** service grouping returns a null bucket, missing count and partial status without inferred names
- **AND** this result is not claimed as named service coverage

### Requirement: Exact money and explicit availability
Response version 2 SHALL follow design.md: per-currency Decimal sums, one final
ROUND_HALF_UP rounding to two-place strings, null savings, period and omission
metadata. It SHALL preserve credits/zero and SHALL NOT certify full coverage
merely because rows are available. Storage errors SHALL remain errors.

#### Scenario: Money and currency
- **WHEN** positive, negative, zero and sub-cent values occur in multiple currencies
- **THEN** each currency is summed separately before rounding, negative zero becomes 0.00, savings is null, and non-unique currency aliases are null
- **AND** rounded groups are not adjusted to force equality with the rounded total

#### Scenario: Empty and incomplete data
- **WHEN** no dated rows exist in the period, or completed tenant rows lack dates or the chosen dimension
- **THEN** undated rows are excluded and counted without assigning a period; missing dimensions use null buckets
- **AND** partial takes precedence for omissions; otherwise empty has empty arrays/null aliases and is distinguishable from an observed zero
