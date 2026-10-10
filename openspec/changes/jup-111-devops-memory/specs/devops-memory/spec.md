## ADDED Requirements

### Requirement: Evidence-based DevOps section

The memory section f MUST explain version control, CI, tests, containers,
logging, metrics, CD and documentation using traceable dated evidence. It MUST
distinguish verified results, implemented configuration and pending checks.

#### Scenario: Historical runtime evidence is reused

- **WHEN** a Docker or CI result is cited in section f
- **THEN** the evidence identifies its source, version or run, date and environment
- **AND** it is not represented as a new execution of the current source tree

#### Scenario: Monitoring is documented

- **WHEN** logging, metrics or alerts are described
- **THEN** their implemented scope and measurement units are supported by sources
- **AND** synthetic tests are not presented as production performance or response-quality evaluation

### Requirement: Automatic promotion requires distinct evidence

The section MUST distinguish local operator validation from the first automatic
promotion of an integrated develop commit.

#### Scenario: Only local validation is available

- **WHEN** smoke passes but the deployment state has run_id=null
- **THEN** the result is described as local validation
- **AND** automatic promotion remains explicitly pending

#### Scenario: Integrated promotion becomes available

- **WHEN** section f is updated to claim an automatic promotion
- **THEN** the evidence links the eligible CI/CD run, matching deployed commit and run identifier, and successful functional checks
- **AND** green CI or an active timer alone is insufficient

### Requirement: Governed section publication

The section MUST follow project-memory-governance and retain the shared document
as the only editable canonical memory. Proposal prose and exports MUST remain
outside Git, and no publication may be claimed before human review.

#### Scenario: Draft is delivered for review

- **WHEN** the section is proposed
- **THEN** it includes a paragraph coverage map for the brief's deliverables, applicable technical/functional requirements and evaluation
- **AND** uncovered requirements are marked pending and unrelated sections remain unchanged

#### Scenario: Publication or final export is unavailable

- **WHEN** human review, authorized section context or export validation is pending
- **THEN** the evidence records that limitation without declaring canonical delivery or acceptance
- **AND** the change remains active with concrete remaining tasks
