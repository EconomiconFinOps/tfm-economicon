## ADDED Requirements

### Requirement: HU check CLI validates active changes

The project SHALL provide a local CLI that validates the required HU/OpenSpec artifacts before a change is archived.

#### Scenario: Contributor checks a complete HU

- **WHEN** a contributor runs `pnpm hu:check -- --change <change-name>`
- **THEN** the CLI validates the active OpenSpec change structure, HiTL approvals, tasks, review findings, OpenSpec validation, and anti-harness guardrails.

### Requirement: Findings backlog is validated

The project SHALL provide a local command that validates the findings backlog format.

#### Scenario: Contributor checks findings

- **WHEN** a contributor runs `pnpm hu:check:findings`
- **THEN** the command verifies that `openspec/findings/backlog.md` exists, has required columns, uses valid finding IDs, and uses allowed states.

### Requirement: Old SDD harness paths are blocked

The project SHALL provide a local command that validates the old SDD harness structure has not been reintroduced.

#### Scenario: Contributor checks anti-harness guardrails

- **WHEN** a contributor runs `pnpm hu:check:anti-harness`
- **THEN** the command verifies that `.sdd`, `packages/sdd-harness`, and `SPEC` are absent and not tracked by Git.

### Requirement: HU check CLI stays lightweight

The project SHALL keep the HU check CLI dependency-free and limited to process guardrails in v1.

#### Scenario: Contributor runs the CLI

- **WHEN** any HU check command runs
- **THEN** it does not run product test, lint, or build suites automatically.
