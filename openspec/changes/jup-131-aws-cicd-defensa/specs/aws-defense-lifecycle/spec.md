## ADDED Requirements

### Requirement: Manual reproducible AWS cycle
The system SHALL keep the documented AWS topology and execute deployment only
from a manually started pipeline pinned to a reviewed source revision and cycle configuration.

#### Scenario: Missing application acceptance
- **WHEN** the release recipe or PostgreSQL/Cognito/Bedrock evidence is absent
- **THEN** validation rejects the cycle before provisioning demo resources

#### Scenario: Configuration or plan is modified
- **WHEN** the configuration hash, source SHA or saved plan binding differs
- **THEN** the runner rejects the operation

### Requirement: Isolated recoverable teardown
The system SHALL preserve bootstrap independently and remove only the disposable
cycle resources recorded in its Terraform state, after stopping writers.

#### Scenario: Partial infrastructure creation
- **WHEN** creation fails after only some resources exist
- **THEN** teardown uses the same state without creating missing resources

#### Scenario: Expired approval
- **WHEN** infrastructure approval arrives after cycle expiry
- **THEN** apply is rejected and cleanup remains available

#### Scenario: Concurrent up and down
- **WHEN** up and down executions target the same public domain
- **THEN** the shared runner, domain lease and state locking prevent conflicting mutation

### Requirement: Offline rehearsal preparation
The system SHALL generate local rehearsal configuration and launch requests
without contacting AWS or claiming deployability when required inputs are missing.

#### Scenario: Example configuration
- **WHEN** the user prepares ensayo1 from the example without real account inputs
- **THEN** files are generated with explicit blockers and no AWS resources are created

### Requirement: Approved regional and quota contract
The system SHALL deploy the application in Ireland, preserve Paris control and
Virginia edge, and verify effective Fargate6vCPU/CodeBuild Medium1 quotas before
provisioning the disposable cycle. A pending increase SHALL NOT satisfy this gate.

#### Scenario: Quota request is pending
- **WHEN** the effective quota is below the required value despite a pending request
- **THEN** validation rejects the cycle before acquiring the deployment lease

#### Scenario: Cross-region configuration is supplied
- **WHEN** the application region, CA, endpoint or Bedrock source contract differs from the reviewed Ireland configuration
- **THEN** the corresponding validator rejects it rather than falling back to another region
