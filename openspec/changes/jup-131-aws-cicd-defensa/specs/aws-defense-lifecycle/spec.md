## ADDED Requirements

### Requirement: Chat startup capacity compatibility
When chat is enabled, the AWS release recipe SHALL use the runtime-supported
capacity of 5 to 8 simultaneous chats. Backend and processor SHALL agree on the
effective capacity when both enable chat. An omitted value SHALL retain the
runtime default of 8. Local preparation SHALL reject an invalid recipe without
AWS calls. The release runner SHALL reject it before planning or provisioning;
its identity and configuration reads MAY precede validation. This does not prove
live application readiness.

#### Scenario: Recipe repeats the observed startup failure
- **WHEN** chat is enabled with CHAT_MAX_ACTIVE=2 in either component
- **THEN** preparation and the runner reject the recipe before provisioning resources

#### Scenario: Enabled components disagree
- **WHEN** backend and processor enable chat with different effective capacities
- **THEN** the recipe is rejected even when each value is individually supported

#### Scenario: Runtime contract changes
- **WHEN** the versioned recipe is checked in CI
- **THEN** a regression test exercises the actual runtime capacity reader with the recipe value

### Requirement: Additive Atlas evaluations
The private bootstrap SHALL verify the exact Atlas SQL digest, load the 19 runs
and 1688 results transactionally, preserve unrelated history, and reject identity
or result conflicts without partial updates. It SHALL NOT call a model or invoke
the destructive general evaluation loader.

#### Scenario: Repeated import with additional history
- **WHEN** the approved artifact is imported twice into a database with another run
- **THEN** the approved runs exist once and the additional run and results remain

#### Scenario: Conflicting run or changed artifact
- **WHEN** an existing run differs or the packaged SQL digest changes
- **THEN** bootstrap fails without overwriting existing evaluations

### Requirement: Private authenticated monitoring
The release SHALL package Grafana 11.3.0 and Prometheus 2.55.1 as immutable images,
retain all three dashboards, expose Grafana under `/grafana/` without prefix
rewriting or caching, deny anonymous access, and use a SELECT-only evaluation
role. Metadata SHALL persist in a separate database on existing RDS with verified
TLS. Prometheus history MAY be ephemeral and bounded to 24h/256MB for each cycle.

#### Scenario: Restart and constrained rolling deployment
- **WHEN** monitoring restarts or application services roll to new tasks
- **THEN** Grafana metadata survives, monitoring uses one 0.5vCPU/1GiB task,
  and the aggregate configured rolling maximum remains at most six vCPU

#### Scenario: Offline preparation and live acceptance
- **WHEN** CI tests the candidate
- **THEN** isolated PostgreSQL and Grafana verify the SQL, TLS, authentication,
  three dashboards and datasource queries without AWS or inference
- **AND** real release acceptance still checks monitoring through the public route

### Requirement: Thirty euro project budget
The controller SHALL reject a project ceiling above 30 EUR and any cycle estimate
above verified remaining funds. Unknown amounts SHALL block launch. This gate
SHALL NOT be described as an AWS billing cap; expiry and cleanup remain required.

#### Scenario: Old sixty euro configuration
- **WHEN** an operator supplies the former 60 EUR ceiling or an unknown balance
- **THEN** preparation remains blocked until a verified configuration within 30 EUR is supplied

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

#### Scenario: Tag inventory retains retired resources
- **WHEN** the tagging API still returns a deleted resource
- **THEN** only an authoritative terminal state or the exact supported absence error for the queried operation establishes retirement
- **AND** the AWS CLI error prefix `aws: [ERROR]: ` is accepted without accepting denials, unrelated operations or quoted diagnostic text
- **AND** ECS services and tasks must match the inspected account, region, cycle and cluster; services must be INACTIVE with zero desired, running and pending tasks, and tasks must have both desired and actual STOPPED state
- **AND** unknown responses and resources with activity continue to block successful retirement

### Requirement: Offline rehearsal preparation
The system SHALL generate local rehearsal configuration and launch requests
without contacting AWS or claiming deployability when required inputs are missing.

#### Scenario: Example configuration
- **WHEN** the user prepares ensayo1 from the example without real account inputs
- **THEN** files are generated with explicit blockers and no AWS resources are created

#### Scenario: Application changes after evidence was recorded
- **WHEN** controller CI runs against application bytes newer than the versioned release evidence
- **THEN** CI verifies the evidence files and controller behavior without renewing acceptance
- **AND** preparation reports the application digest mismatch as a deployment blocker
- **AND** the deployment runner rejects that recipe until matching acceptance is supplied

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
