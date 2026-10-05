## ADDED Requirements
### Requirement: Trusted integrated revision eligibility
JUP-052 SHALL deploy only the current canonical develop SHA after the latest
CD workflow run for develop completes successfully with all applicable CI jobs.

#### Scenario: Eligible integrated commit
- **WHEN** the latest canonical CD run succeeds for the current develop SHA
- **THEN** the agent SHALL fetch that exact SHA and verify it remains current
- **AND** it SHALL recheck develop after preparation and functional checks before promotion

#### Scenario: Ineligible or unavailable result
- **WHEN** the latest run fails, is cancelled or pending, targets another SHA,
  repository or branch, or the API/fetch cannot be verified
- **THEN** the agent SHALL NOT promote any release

### Requirement: Private isolated development runtime
The agent SHALL generate local secrets and enforce loopback published ports
for an explicitly disposable development runtime with mock AI providers.

#### Scenario: Initial configuration
- **WHEN** the operator initializes a new runtime root
- **THEN** secrets SHALL be random, private and outside Git
- **AND** initialization SHALL NOT overwrite existing secrets

#### Scenario: Shared server deployment
- **WHEN** a candidate starts on DockerServer
- **THEN** its project and volumes SHALL be separate from other SHAs and stacks
- **AND** its published ports SHALL bind only to 127.0.0.1

### Requirement: Verified promotion and recovery
The agent SHALL serialize deployment and change its current pointer only after
health, demo login, simulator ingestion, billing totals and document-job checks pass.

#### Scenario: Successful candidate
- **WHEN** build, Compose wait and all functional checks pass
- **THEN** state SHALL identify the SHA and originating run id
- **AND** the prior release SHALL be stopped without deleting its volumes

#### Scenario: Candidate fails
- **WHEN** build, readiness or functional verification fails
- **THEN** current SHALL remain unchanged and candidate cleanup SHALL be attempted
- **AND** the prior release SHALL remain running
- **AND** failure evidence SHALL persist independently of cleanup success

#### Scenario: Interrupted cleanup or preparation
- **WHEN** cleanup fails or a process stops after promotion or during preparation
- **THEN** the next locked poll SHALL reconcile inactive releases and incomplete copies
- **AND** an inactive slot SHALL NOT be reused until cleanup succeeds
- **AND** sources and named volumes SHALL be preserved
- **AND** cleanup SHALL attempt all managed releases and copies before reporting errors

#### Scenario: Eligibility unavailable after successful smoke
- **WHEN** the final eligibility check fails due to an API or network error
- **THEN** the candidate SHALL NOT be promoted and cleanup SHALL be attempted
- **AND** the healthy SHA SHALL NOT be permanently quarantined
- **AND** a superseded head SHALL be recorded distinctly from a functional failure

#### Scenario: Current recovery fails
- **WHEN** restoring the current release fails
- **THEN** the failure SHALL be recorded without preventing eligibility evaluation
- **AND** pending recovery status SHALL clear only when recovery and cleanup succeed

#### Scenario: Failed SHA retry
- **WHEN** a previously failed SHA is still the eligible candidate
- **THEN** it SHALL NOT rebuild until the operator resumes retries
- **AND** resume SHALL preserve the failure evidence

#### Scenario: Manual recovery
- **WHEN** the operator requests rollback to a previous verified release
- **THEN** its existing images SHALL start and pass functional checks before promotion
- **AND** automatic promotion SHALL pause until explicitly resumed
- **AND** rollback SHALL NOT claim to reverse or restore another release's data
