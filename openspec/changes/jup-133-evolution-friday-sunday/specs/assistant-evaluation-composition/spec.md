## ADDED Requirements

### Requirement: Descriptive evolution with explicit protocol boundaries
The dashboard SHALL display the existing Friday23 and Sunday25 observations as
a descriptive comparison of44common case IDs, with132and44operations respectively,
without altering the existing strict comparability guards.

#### Scenario: Unequal repetitions and different timing methods
- **WHEN** both projections are loaded
- **THEN** the dashboard displays repetitions, denominators, terminal counts and observed median/P95
- **AND** it identifies different timing methods and disclaims causal improvement and acceptance

#### Scenario: Functional judgment and incomplete cost
- **WHEN** the Sunday50case projection is loaded
- **THEN** completion and agent PASS/PARTIAL/FAIL are displayed separately
- **AND** observed incomplete chat cost is not presented as confirmed invoice or savings against Friday

#### Scenario: Missing projection
- **WHEN** either projection is absent
- **THEN** its observations remain absent rather than becoming zeros or values copied from another run

### Requirement: Additive publication preserves existing evidence
The supplementary SQL SHALL add only absent identities and SHALL preserve all
existing historical runs, results and access configuration.

#### Scenario: Repeating the same supplement
- **WHEN** both identities and their complete content already match
- **THEN** the transaction changes no data

#### Scenario: Identity collision
- **WHEN** an existing identity has different metadata or missing, extra or changed result rows
- **THEN** the whole transaction aborts without inserting even the other absent identity
