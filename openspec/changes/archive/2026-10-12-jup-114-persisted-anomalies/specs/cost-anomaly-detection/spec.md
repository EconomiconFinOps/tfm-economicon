## MODIFIED Requirements

### Requirement: Reusable evidence without causal claims
The system SHALL return a versioned definition, periods, quality, assessments
and triggered candidates with stable selection IDs and evidence IDs. It SHALL
mark causes as not_established and completeness as not_verified, and describe
source freshness, coverage, separate-read and monetary precision limitations.
This evaluation SHALL remain an unpersisted test query with caller-supplied
rules: it SHALL NOT create, change or read stored anomaly episodes, and its IDs
SHALL NOT be used as episode identities.

#### Scenario: Evidence changes
- **WHEN** the same tenant, definition and group are evaluated again with changed observed costs or quality
- **THEN** the stable alert ID remains the same when that group still triggers and its evidence ID changes

#### Scenario: Repeatable evidence
- **WHEN** identical definition, tenant, observations and quality are evaluated again
- **THEN** alert IDs, evidence IDs and deterministic assessment ordering remain the same

#### Scenario: Downstream explanation
- **WHEN** JUP-038 explains an anomaly to a user
- **THEN** it uses stored episodes from `cost-anomaly-episodes` and not candidates of this test query
- **AND** this contract does not establish operational cause, savings, daily coverage, statistical confidence or a connected agent tool

#### Scenario: Existing daily rule remains separate
- **WHEN** a consumer reads the JUP-030 contract alongside the JUP-019 daily double-threshold rule applied by stored episodes
- **THEN** documentation distinguishes inclusive independent period rules from that strict daily rule without claiming equivalence

#### Scenario: Test query does not touch episodes
- **WHEN** an increase of exactly 20 % with enough absolute increase is evaluated with deviation_threshold_percent 20.00
- **THEN** this query reports a triggered candidate, no episode is created or changed, and the same day evaluated by the business rule opens no episode
