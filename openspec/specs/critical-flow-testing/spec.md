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
