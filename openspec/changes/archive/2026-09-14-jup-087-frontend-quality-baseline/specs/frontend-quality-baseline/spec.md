## ADDED Requirements

### Requirement: Frontend lint is a zero-error quality gate

The frontend SHALL complete its configured lint task with zero errors and SHALL
retain explicit component prop contracts through PropTypes or an approved typed
alternative.

#### Scenario: Existing components are linted

- **WHEN** the repository runs `pnpm lint`
- **THEN** no `react/prop-types` or other frontend lint error remains.

#### Scenario: A global rule suppression is proposed

- **WHEN** configuration disables `react/prop-types` for the whole frontend
  without an approved typed migration
- **THEN** the JUP-087 quality gate fails even if the linter exits successfully.

### Requirement: Workspace tests execute real frontend tests

`pnpm test` SHALL run a reproducible frontend test runner and SHALL fail when a
frontend test fails; a placeholder success message is not a test suite.

#### Scenario: Workspace tests run in CI

- **WHEN** CI executes the root test command
- **THEN** frontend test cases are discovered, executed and included in the exit status.

### Requirement: Critical MVP journeys have positive and failure coverage

The frontend suite SHALL cover login/session, tenant loading and selection,
dashboard data, ingestion creation and basic conversation behavior with at least
one successful and one user-visible failure scenario per journey.

#### Scenario: Login succeeds and fails

- **WHEN** login receives a valid response or an authentication error
- **THEN** tests verify session creation in the first case and an actionable
  error without session creation in the second.

#### Scenario: Tenant bootstrap succeeds and fails

- **WHEN** the authenticated tenant request returns available tenants or an error
- **THEN** tests verify valid selection/persistence or the reset-session recovery path.

#### Scenario: Product requests succeed and fail

- **WHEN** dashboard, ingestion or conversation requests resolve or reject
- **THEN** tests verify the expected result and a visible non-crashing error state.

### Requirement: Frontend tests are isolated from external services

The test suite SHALL use deterministic request fixtures and SHALL reset browser
storage and query cache between cases.

#### Scenario: Tests run without Docker or network access

- **WHEN** the frontend suite executes in a clean CI worker
- **THEN** it completes using controlled HTTP fixtures and leaves no session or tenant state between tests.
