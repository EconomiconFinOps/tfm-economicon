## Purpose

Identify observed costs with incomplete minimum ownership or classification
metadata as candidates for investigation, without claiming financial allocation
status or counting a cost repeatedly for its several metadata defects.

## ADDED Requirements

### Requirement: Explicit metadata detection basis

The service SHALL expose authenticated `GET /billing/unallocated-cost` with
contract version 1, `detection_basis=observed_required_tags`,
`allocation_status=not_evaluated`, policy version and required tags. Candidate
results SHALL NOT assert financial unallocated status, and complete metadata
SHALL NOT assert verified financial assignment.

#### Scenario: A documented allocation rule could exist elsewhere

- **WHEN** an observed record is missing owner but contains a cost center
- **THEN** it may be a metadata candidate, while the response states financial allocation is not evaluated
- **AND** the response does not override a documented assignment outside the available data

### Requirement: Versioned minimum metadata predicate

The service SHALL use `economicon-minimum-v1` over canonical owner,
environment, application, cost_center and project tags with the same predicate
as JUP-017. It SHALL reject absent, non-string, blank, placeholder and
syntactically invalid values. It SHALL NOT infer semantic aliases, corporate
catalog membership or replace project with the older corpus's businessunit.

#### Scenario: Valid values and an invalid environment

- **WHEN** all five tags satisfy the policy except environment contains `trey`
- **THEN** the full record belongs to a candidate signature containing environment
- **AND** its present owner does not make the missing classification metadata disappear

#### Scenario: Serialized placeholders and extra tags

- **WHEN** owner is `None`, `True`, `False` or another invalid marker and organization is present
- **THEN** owner fails the predicate and organization does not replace it

### Requirement: Disjoint candidate groups

The service SHALL partition records by their exact set of missing or invalid
required tags within each currency. Every record SHALL contribute once to
either complete-metadata amounts or exactly one candidate group. Each group
SHALL provide its ordered defective tags, diagnostic reason, record count,
positive cost, signed negative adjustments and net cost.

#### Scenario: One record has multiple defects

- **WHEN** a 40 EUR record lacks owner, application and project
- **THEN** it contributes 40 EUR once to candidate cost and once to one signature group
- **AND** the group lists all three tags with reason `no_owner_and_unclassified`

#### Scenario: Diagnostic reasons do not assert assignment

- **WHEN** a record has only owner defective, only non-owner tags defective, or both
- **THEN** its reason is respectively `no_owner`, `unclassified`, or `no_owner_and_unclassified`
- **AND** those reasons describe minimum metadata defects rather than financial allocation

### Requirement: Authorized explicit UTC interval

The endpoint SHALL require active-tenant membership and explicit valid
start_date and end_date boundaries with start before end. It SHALL read only
matching-tenant/subscription completed runs and records in the UTC interval
including start and excluding end. Invalid selection or access SHALL be
rejected before the cost query.

#### Scenario: Invalid or missing interval

- **WHEN** a boundary is absent, malformed, not a calendar date, equal to or before the start boundary
- **THEN** the endpoint returns 422 without reading costs

#### Scenario: Other tenant or ineligible records

- **WHEN** costs exist under a foreign tenant, mismatched run subscription, unfinished run or outside the interval
- **THEN** they do not affect counts or amounts

### Requirement: Conservative source overlap rejection

The service SHALL reject more than one distinct completed ingestion ID for an
authorized subscription/day in the selected interval with HTTP 409 and detail
code `ambiguous_cost_source`, without monetary results. It SHALL NOT resolve
overlap using latest-wins, resource identity or row hashes.

#### Scenario: Alternative source covers an observed day

- **WHEN** two eligible ingestion IDs contain records for the same subscription and date
- **THEN** the entire request returns `ambiguous_cost_source` without amounts
- **AND** neither source is selected, modified or deleted

### Requirement: Per-currency positive weighting and reconciliation

The service SHALL aggregate exact decimal amounts separately per currency,
partition positive charges and signed negative adjustments between
complete-metadata and candidate signatures, and expose their net amounts.
Positive charges SHALL form the percentage denominator. Zero-cost and negative
records SHALL remain visible in record counts and applicable groups.

#### Scenario: Credits do not cancel coverage

- **WHEN** 60 EUR has complete metadata, 40 EUR is a candidate and a complete-metadata adjustment is -100 EUR
- **THEN** candidate cost is 40.00 EUR, positive cost is 100.00 EUR, net cost is 0.00 EUR and candidate percentage is 40.00

#### Scenario: Several currencies and large amounts

- **WHEN** EUR and USD costs include values above JavaScript's safe integer limit
- **THEN** each currency has its own results and amounts remain decimal strings without floating-point conversion

### Requirement: Defined display precision and missing denominator

The service SHALL retain unrounded weights until aggregation and SHALL
serialize monetary values as two-decimal HALF_UP strings. To match JUP-017,
candidate_percent SHALL be 100.00 minus the rounded complete-metadata
percentage. Independently rounded amounts SHALL NOT be treated as an exact
display-level reconciliation guarantee. Without positive costs the percentage
SHALL be null with an explicit no_positive_cost_reason.

#### Scenario: Percentage at the complement rounding boundary

- **WHEN** positive cost is 20000 and complete-metadata cost is 19999
- **THEN** the complete-metadata percentage rounds to 100.00 and candidate_percent is 0.00, while candidate_cost remains 1.00

#### Scenario: Fractional charges and net zero

- **WHEN** complete-metadata positive cost is 0.006, candidate positive cost is 0.004 and an adjustment is -0.01
- **THEN** candidate_percent is 40.00 based on unrounded positive charges despite independently rounded displayed costs

#### Scenario: Zero or negative-only costs

- **WHEN** a currency contains only zero costs or only negative adjustments and zero costs
- **THEN** candidate_percent is null and the reason is respectively `zero_cost_only` or `negative_adjustments_only`

### Requirement: Honest available-data limits

The service SHALL report excluded undated records visibly, return no currency
rows for an empty dated scope, and distinguish available, partial and empty
source states. Documentation SHALL identify lost source dimensions, absent
catalogs and absent allocation rules as limits. It SHALL NOT claim invoice
completeness, shared/excluded allocation, or tested integration with pending
JUP-015, JUP-027 or the whole JUP-017 implementation.

#### Scenario: Undated records exist

- **WHEN** authorized completed records include undated rows
- **THEN** those rows are excluded from interval amounts, counted in excluded_undated_count and data_status is partial

#### Scenario: No observed records in the interval

- **WHEN** no dated records match and no eligible undated records exist
- **THEN** currencies is empty and data_status is empty, without inventing a zero-cost currency

#### Scenario: Source query did not retain owner or application

- **WHEN** stored tags lack a dimension that the original source query may have discarded
- **THEN** the results remain observed metadata candidates and documentation does not claim the source resource itself lacked that dimension
