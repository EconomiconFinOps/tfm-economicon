# tagged-cost-coverage Specification

## Purpose
Measure the share of observed positive Azure cost that satisfies Economicon's
five-tag minimum policy, with per-currency precision and separate signed
adjustments, under the authenticated tenant and nonduplicated source scope.
## Requirements
### Requirement: Versioned minimum tag compliance
The service SHALL require owner, environment, application, cost_center and project
to satisfy economicon-minimum-v1 rules, and SHALL report the policy version and
required tags. Identifier rules SHALL validate syntax without claiming approved
organization-catalog membership. Extra tags SHALL NOT replace a required tag.

#### Scenario: Fully compliant and partially compliant rows
- **WHEN** 60 EUR has all five valid tags and 40 EUR has only three
- **THEN** compliant coverage is 60.00% and noncompliant coverage is 40.00%

#### Scenario: Empty or invalid values
- **WHEN** a required tag is absent, JSON null, non-string, whitespace, a placeholder or an invalid environment
- **THEN** the entire row is noncompliant and its defective tags are counted

### Requirement: Coverage of positive observed costs
The service SHALL weight coverage by unrounded positive pretax_cost per currency,
and SHALL expose signed negative adjustments and net reconciliation separately.
It SHALL return null percentages when there are no positive charges.

#### Scenario: Adjustments do not distort coverage
- **WHEN** 80 EUR complies, 20 EUR does not and a compliant adjustment is -30 EUR
- **THEN** coverage is 80.00% / 20.00%, adjustments -30.00 and net 70.00

#### Scenario: Net zero with positive charges
- **WHEN** 60 EUR complies, 40 EUR does not and an adjustment is -100 EUR
- **THEN** coverage is 60.00% / 40.00% despite net zero

#### Scenario: Zero and negative-only periods
- **WHEN** the period has only zero costs or only negative adjustments
- **THEN** percentages are null and the reason distinguishes the two cases

#### Scenario: Multiple currencies and large amounts
- **WHEN** EUR and USD costs exceed JavaScript integer precision
- **THEN** amounts remain decimal strings and each currency has separate percentages

### Requirement: Authorized nonduplicated source scope
The endpoint SHALL enforce active-tenant membership and use only completed
matching-tenant/subscription runs in the selected UTC interval. It SHALL exclude
undated rows visibly and reject overlapping completed sources with 409.

#### Scenario: Other tenants and unfinished runs
- **WHEN** matching records exist outside the selected tenant, period or completed runs
- **THEN** they do not affect the coverage result

#### Scenario: Ambiguous source
- **WHEN** multiple completed runs cover a selected subscription/date
- **THEN** the endpoint returns ambiguous_cost_source without monetary results

#### Scenario: Missing or invalid dates
- **WHEN** only one interval boundary is supplied or the interval is invalid
- **THEN** validation returns 422 before querying costs

### Requirement: Honest dashboard coverage states
The executive dashboard SHALL show per-currency coverage for the selected tenant
and period, with explicit loading, error, empty and N/D states. It SHALL retain
exact amount strings and SHALL NOT show a previous tenant's result.

#### Scenario: Selection changes during a pending request
- **WHEN** the user switches tenant or period before the response arrives
- **THEN** the previous response is not displayed for the new selection

#### Scenario: No positive cost and API error
- **WHEN** coverage has null percentages or the API rejects the query
- **THEN** the panel shows N/D or an error respectively, without inventing zero coverage
