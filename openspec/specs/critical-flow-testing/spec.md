# critical-flow-testing Specification

## Purpose
Define reproducible coverage and honest evidence for critical component boundaries,
infrastructure-dependent journeys and mandatory CI test execution (JUP-054).
## Requirements
### Requirement: Risk and suite traceability
The project SHALL map auth, tenant, Azure, RAG, agent, frontend and Docker runtime
risks to concrete tests, execution commands and their real or simulated boundaries.

#### Scenario: Audit current coverage
- **WHEN** a contributor evaluates critical coverage
- **THEN** the matrix identifies existing suites, added seam regressions and checks requiring external services
- **AND** historical results and skipped tests are not described as fresh passes

### Requirement: Critical component regressions
The test suite SHALL exercise real adjacent components across the Azure
producer/consumer and agent/ingestion boundaries, with explicit external doubles.

#### Scenario: Successful and failing ingestion
- **WHEN** critical ingestion components are run with valid input or a provider failure
- **THEN** tests assert externally observable results and error effects
- **AND** failures cannot silently produce successful ingestion evidence

#### Scenario: Persisted assistant history
- **WHEN** the existing isolated real-service journey creates an assistant response
- **THEN** reading the conversation history preserves its metadata and citations
- **AND** a different tenant cannot read that conversation

### Requirement: Fresh mandatory test execution
CI SHALL execute the frontend runner and the three Python service suites without
accepting Turbo test-cache output as evidence, retaining existing required check names.

#### Scenario: Pull request execution
- **WHEN** the existing frontend build check runs
- **THEN** Vitest executes directly and a test failure blocks the check
- **AND** documentation lists local reproduction commands and opt-in infrastructure checks

### Requirement: Final candidate coverage audit
The project SHALL measure test coverage of a pinned candidate revision for each
application service and SHALL record the revision, runtime, tool versions,
commands and results so that another contributor can repeat the measurement.

#### Scenario: Measure a pinned candidate
- **WHEN** a contributor audits the coverage of the candidate revision
- **THEN** the evidence identifies the audited revision and reports the measured coverage per service
- **AND** the measurement runs the same suites as the required checks on a comparable runtime

#### Scenario: Instrumented run differs from the reference run
- **WHEN** the instrumented run does not reproduce the passed, failed and skipped results of the reference run for that revision
- **THEN** the evidence reports the difference
- **AND** the affected figure is not presented as the coverage of the candidate

#### Scenario: Candidate advances before delivery
- **WHEN** the candidate branch receives application code changes after the audited revision and before delivery
- **THEN** the affected services are measured again or the evidence states which revisions the audit does not cover

### Requirement: Coverage gap disposition
Every gap that the audit identifies in a critical flow SHALL be covered by a
test, accepted with a recorded reason, or registered as a finding.

#### Scenario: Critical gap covered
- **WHEN** a gap is classified as critical
- **THEN** a test exercises that behavior through real application components
- **AND** the test fails when that behavior is deliberately broken

#### Scenario: Gap left uncovered
- **WHEN** a gap is not covered during the audit
- **THEN** the evidence records the reason
- **AND** a deferred gap has a finding identifier in the findings backlog

#### Scenario: Code exercised only by opt-in suites
- **WHEN** code is exercised only by tests that are skipped without external services
- **THEN** it is reported separately from untested code
- **AND** the offline measurement is not presented as verification of that code

#### Scenario: New test exposes a defect
- **WHEN** a new test fails against the unmodified candidate
- **THEN** the defect is registered as a finding with its reproduction
- **AND** the assertion is not weakened to make the test pass

### Requirement: Coverage is diagnostic
Coverage figures SHALL inform the gap audit and SHALL NOT act as a minimum
threshold on any required check.

#### Scenario: Coverage figure does not gate delivery
- **WHEN** a service reports any coverage figure
- **THEN** no required check fails because of that figure
- **AND** the required check names remain unchanged
