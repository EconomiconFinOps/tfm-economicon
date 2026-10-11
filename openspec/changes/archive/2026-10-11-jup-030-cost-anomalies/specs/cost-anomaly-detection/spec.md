## ADDED Requirements

### Requirement: Explicit tenant-scoped anomaly definition
The system SHALL accept an authenticated anomaly evaluation request with one
currency, a supported billing grouping, an explicit UTC date interval and at
least one positive absolute-cost or deviation rule. It SHALL reject invalid
or extra fields before reading billing data.

#### Scenario: Closed equal-duration periods
- **WHEN** deviation is requested for 2026-04-08 through exclusive 2026-04-15
- **THEN** current data covers that interval and baseline covers 2026-04-01 through exclusive 2026-04-08
- **AND** both periods use UTC

#### Scenario: Invalid request
- **WHEN** dates are not explicit ISO dates, the interval is outside 1 to 366 days, its end exceeds today's UTC date, its baseline underflows, no rule is enabled, a rule is nonpositive, the percentage exceeds 1000.00 or an extra field is supplied
- **THEN** the endpoint returns 422 without reading billing data

#### Scenario: Absolute-only evaluation
- **WHEN** only absolute_threshold is enabled
- **THEN** the system reads only the current period and returns null baseline period and quality

### Requirement: Exact independent detection rules
The system SHALL compare observed costs with Decimal arithmetic, preserve
credits and use inclusive thresholds before display rounding. An absolute
rule SHALL compare current group cost to its configured threshold. A deviation
rule SHALL require a positive baseline, the minimum absolute increase and the
configured relative increase. Either rule SHALL produce one candidate.

#### Scenario: Both rules trigger
- **WHEN** current cost is 160.00 EUR, baseline is 100.00 EUR, absolute_threshold is 150.00, deviation_threshold_percent is 50.00 and min_absolute_increase is 1.00
- **THEN** one alert contains both trigger reasons, delta_amount 60.00 and deviation_percent 60.00
- **AND** it identifies the actual group, currency and periods

#### Scenario: Exact rule boundary
- **WHEN** current cost equals the absolute threshold or the increase equals both deviation conditions
- **THEN** the corresponding rule triggers

#### Scenario: Rounded percentage is insufficient
- **WHEN** a percentage rounds to the configured threshold but its exact ratio is below it
- **THEN** the deviation rule remains below

#### Scenario: Large monetary values
- **WHEN** valid monetary values exceed exact IEEE-754 integer precision
- **THEN** comparisons and derived amounts preserve cents using decimal strings and local Decimal precision

### Requirement: Missing data is not a zero observation
The system SHALL assess only current observed groups in the requested currency
and SHALL distinguish absent, nonpositive and valid baselines. It SHALL expose
quality and preserve unknown grouping values without inventing classifications.

#### Scenario: Missing or nonpositive baseline
- **WHEN** an observed current group has no matching baseline or a baseline of zero or negative cost
- **THEN** deviation_status is baseline_missing or baseline_nonpositive and deviation_percent is null
- **AND** deviation does not trigger, while an independently satisfied absolute rule may trigger

#### Scenario: No current groups
- **WHEN** no current groups exist in the selected currency
- **THEN** evaluation_status is unavailable and assessments and alerts are empty

#### Scenario: Partial evaluation
- **WHEN** either queried billing summary is partial or any current group has an unevaluable baseline
- **THEN** a populated evaluation is provisional and retains its data-quality counts and rule states

#### Scenario: Unknown dimension and currency separation
- **WHEN** a current group has a null dimension and records exist in multiple currencies
- **THEN** the null dimension remains explicit and only requested-currency groups are assessed without conversion

### Requirement: Protected and consistent source selection
The system SHALL reuse billing v2 tenant membership, completed-ingestion,
date, grouping and overlap protections. It SHALL reject duplicate internal
group identities rather than silently overwrite observations.

#### Scenario: Unauthorized tenant
- **WHEN** the requester lacks membership of the requested active tenant
- **THEN** access is denied before cost reads

#### Scenario: Ambiguous source in either period
- **WHEN** billing detects overlapping sources in the current or baseline period
- **THEN** evaluation returns 409 with ambiguous_cost_source and no partial financial response

#### Scenario: Resource-group identity
- **WHEN** a resource-group label differs only in case between periods within the same subscription
- **THEN** it matches using billing's lowercase grouping convention
- **AND** the same label in another subscription remains separate

### Requirement: Reusable evidence without causal claims
The system SHALL return a versioned definition, periods, quality, assessments
and triggered candidates with stable selection IDs and evidence IDs. It SHALL
mark causes as not_established and completeness as not_verified, and describe
source freshness, coverage, separate-read and monetary precision limitations.

#### Scenario: Evidence changes
- **WHEN** the same tenant, definition and group are evaluated again with changed observed costs or quality
- **THEN** the stable alert ID remains the same when that group still triggers and its evidence ID changes

#### Scenario: Repeatable evidence
- **WHEN** identical definition, tenant, observations and quality are evaluated again
- **THEN** alert IDs, evidence IDs and deterministic assessment ordering remain the same

#### Scenario: Downstream explanation
- **WHEN** JUP-038 consumes a candidate
- **THEN** the payload provides observed and baseline operands, rules and evidence needed to explain why it was marked
- **AND** the contract does not establish operational cause, savings, daily coverage, statistical confidence or a connected agent tool

#### Scenario: Existing daily rule remains separate
- **WHEN** a consumer reads the JUP-030 contract alongside JUP-084's strict daily double-threshold rule
- **THEN** documentation distinguishes inclusive independent period rules from that daily rule without claiming equivalence
