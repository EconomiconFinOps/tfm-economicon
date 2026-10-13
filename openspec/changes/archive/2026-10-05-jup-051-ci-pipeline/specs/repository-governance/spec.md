## ADDED Requirements

### Requirement: Branch heads receive the existing CI checks automatically
CI SHALL trigger on pushes to every branch without path filters, exclude
tag-only pushes, and retain existing pull-request and manual triggers.
Every commit SHALL mean the pushed branch head, not offline commits or a
separate execution for every intermediate commit in one push.

#### Scenario: Branch head is pushed without a pull request
- **WHEN** a head is pushed to any branch, including a slash-separated task branch
- **THEN** CI schedules existing frontend lint/tests/build, frontend type checking, Python matrix checks and governance for that head
- **AND** PR policy is skipped because the event is not a pull request

#### Scenario: Only a tag is pushed
- **WHEN** the update is a tag push without a branch update
- **THEN** the push trigger does not start CI

#### Scenario: Existing PR and manual entry points are used
- **WHEN** an existing configured PR activity targets main or develop, or manual dispatch is requested
- **THEN** the corresponding CI entry point remains available
- **AND** PR policy runs only for the pull-request event

### Requirement: Python matrix jobs enforce existing lint and build semantics
Each Python service matrix job SHALL run `python -m compileall -q app` exactly
once in its service directory before pytest, covering the identical existing
lint/build scripts without new dependencies. Compilation errors SHALL fail the
job without failure suppression. This check SHALL be described as syntax and
bytecode checking, not style lint, runtime integration or packaging.

#### Scenario: Python syntax is valid
- **WHEN** each service contains syntactically valid Python under app
- **THEN** its compileall step succeeds and the existing pytest step remains enabled

#### Scenario: Python syntax is invalid
- **WHEN** compileall encounters invalid Python syntax under app
- **THEN** it returns nonzero and fails that matrix job
- **AND** neither the step nor the job masks that failure

### Requirement: CI expansion preserves existing behavior and reports limits
CI SHALL retain current permissions, pinned actions, check names, governance,
test commands and service-dependent skips. It SHALL keep the current concurrency
group and cancellation setting. Acceptance evidence SHALL distinguish executed,
failed, cancelled, skipped and unverified checks.

#### Scenario: A branch with an open PR receives another push
- **WHEN** both push and PR events apply to the update
- **THEN** both runs may be created with unchanged branch/PR concurrency groups
- **AND** a superseded run in the same group may cancel without claiming every intermediate commit was validated

#### Scenario: Real services are unavailable
- **WHEN** existing tests skip because isolated CockroachDB, RabbitMQ or pgvector is absent
- **THEN** the skips remain visible and are recorded as unexercised real-service coverage
- **AND** success does not certify those integrations, Docker runtime or deployment

#### Scenario: Only local checks have run
- **WHEN** explicit publication approval and hosted-run evidence are absent
- **THEN** local results may establish configuration correctness but remote push/PR execution and actual human acceptance remain pending
