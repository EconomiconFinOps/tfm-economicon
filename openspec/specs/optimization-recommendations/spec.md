# optimization-recommendations Specification

## Purpose
Define evidence-backed, read-only optimization proposals from tenant-scoped
project costs, preserving business context and separating observed cost from
unavailable savings estimates (JUP-033).
## Requirements
### Requirement: Explicit authenticated recommendation selection
The system SHALL generate recommendations only for the authenticated active
tenant and a required UTC interval of 1 through 366 days, inclusive of the
start date and exclusive of the end date, through the existing project billing
summary boundary.

#### Scenario: Valid selected period
- **WHEN** an authorized user selects 2026-09-01 through 2026-10-01
- **THEN** the billing read uses that user's active tenant, includes September 1, excludes October 1 and groups by project without a tag-key selection

#### Scenario: Invalid or omitted period
- **WHEN** either date is missing or invalid, the end does not follow the start, or the interval exceeds 366 days
- **THEN** the endpoint returns 422 without fetching billing costs

#### Scenario: Unauthorized tenant selection
- **WHEN** a user has no valid session or no membership of the selected tenant
- **THEN** existing authentication and membership enforcement deny access before the billing read and disclose no recommendation evidence

### Requirement: Evidence-backed project attribution action
The system SHALL recommend assigning missing project attribution when observed
records lack a project, including zero or credit net costs, and SHALL preserve
business ownership checks in the proposed action.

#### Scenario: Unassigned credit
- **WHEN** records without a project net to -5.00 EUR in the selected interval
- **THEN** a supported `missing_project` recommendation asks for business attribution, cites the observed credit and reports no estimated saving

#### Scenario: Zero-cost attribution gap
- **WHEN** observed records without a project net to 0.00 EUR
- **THEN** the attribution gap is still actionable and is not discarded as absent data

#### Scenario: Project tag fallback
- **WHEN** billing resolves a project through its existing `tags.project` fallback
- **THEN** the recommendation evaluation uses that resolved project instead of inventing a missing-project finding

### Requirement: Conservative investigation of observed project cost
The system SHALL consume each named project's billing aggregate across
subscriptions in the active tenant and select the highest positive aggregate separately for each
currency as an `investigation_candidate`, without asserting waste.

#### Scenario: Shared project across subscriptions
- **WHEN** project Alpha has 60.00 EUR in each of two subscriptions and project Beta has 100.00 EUR in one subscription
- **THEN** Alpha is selected with observed cost 120.00 EUR and an action to examine business purpose, usage and cost drivers before choosing an optimization

#### Scenario: Equal projects and independent currencies
- **WHEN** two projects tie for the largest positive EUR cost and another project has a positive USD cost
- **THEN** a deterministic project-name tie-break selects one EUR candidate and a separate USD candidate without comparing or converting their amounts

#### Scenario: No positive named project
- **WHEN** observed named projects have only zero or negative net costs
- **THEN** no `largest_project_cost` candidate is produced and the report does not infer an optimization saving

### Requirement: Honest applicability and financial boundary
The system SHALL distinguish supported tagging recommendations, investigation
candidates and rules that were not evaluated, and SHALL keep observed costs
separate from null estimated savings.

#### Scenario: Missing utilization and commitment data
- **WHEN** only existing billing records are available
- **THEN** `not_evaluated` lists rightsizing, scheduling, orphan cleanup, rate optimization and savings impact with their missing inputs, and produces no shutdown, reservation or other resource-change recommendation

#### Scenario: Observed amount is not an estimated saving
- **WHEN** a candidate cites 120.00 EUR of observed project cost
- **THEN** `estimated_savings` and savings `currency` remain null, and the report identifies the amount as observed cost without a monthly, annual or realized-savings claim

#### Scenario: Simulated source and business assumptions
- **WHEN** recommendations are generated from the current stored ingestion source
- **THEN** the report identifies `azure_cost_records`, the simulated-source limitation and the business checks needed before action

### Requirement: Explicit data quality and source ambiguity
The system SHALL return `available` or `insufficient_data` with source quality
and limitations, preserve partial coverage signals and reject ambiguous source
data under the existing billing policy.

#### Scenario: Empty source data
- **WHEN** no observed billing groups are available for the selected interval
- **THEN** the report has `insufficient_data`, no invented recommendation and no claim of zero waste or zero savings

#### Scenario: Partial observed data
- **WHEN** the billing summary is partial with excluded or unclassified records
- **THEN** applicable proposals retain the source quality and omission context, and limitations prevent representing the result as complete tenant coverage

#### Scenario: Overlapping sources
- **WHEN** billing rejects source ambiguity for the selected interval
- **THEN** the endpoint returns 409 with `ambiguous_cost_source` and no recommendation amounts

### Requirement: Stable bounded consumer contract
The system SHALL expose contract version 1, deterministic scoped recommendation
identifiers, content-addressed evidence, assumptions and limitations, and no more
than 50 returned candidates with explicit truncation.

#### Scenario: Equivalent input in another order
- **WHEN** equivalent project groups are supplied in a different order for the same tenant and interval
- **THEN** selection, ordering and recommendation identifiers remain unchanged

#### Scenario: Observation changes within the same scope
- **WHEN** an observed cost changes for the same tenant, interval, rule, currency and project while the candidate remains applicable
- **THEN** the recommendation retains its identifier and references a different evidence identifier

#### Scenario: Comparison data changes
- **WHEN** another project's cost changes without displacing the same highest-cost candidate
- **THEN** the candidate retains its identifier and its evidence identifier changes to reflect the changed comparison data

#### Scenario: Identical observations in separate tenants
- **WHEN** two tenants have the same project names, amounts and selected interval
- **THEN** their recommendation identifiers remain tenant-scoped and neither report exposes the other tenant's evidence

#### Scenario: Candidate limit
- **WHEN** eligible candidates exceed 50
- **THEN** the report returns the first 50 by currency, rule ID and project value, reports the full `total_candidates` count and sets `truncated` to true

#### Scenario: Consumers preserve producer limits
- **WHEN** JUP-034, JUP-039 or JUP-058 consumes a version 1 report
- **THEN** the contract supplies evidence and applicability without asserting that savings estimation, assistant wiring or frontend integration has been verified

### Requirement: Read-only recommendation generation
The system SHALL generate recommendations without persisting recommendation
state, invoking a language model or applying changes to cloud resources.

#### Scenario: Repeated generation
- **WHEN** an authorized user requests the same recommendation report repeatedly
- **THEN** generation performs only the existing billing read and in-memory evaluation and initiates no resource change or recommendation workflow write
