# hu-check-cli Specification

## Purpose
Define the lightweight project-local CLI used to validate HU/OpenSpec process guardrails before archiving changes.

## Requirements
### Requirement: HU check CLI validates active changes

The project SHALL provide a local CLI that validates the required HU/OpenSpec artifacts before a change is archived.

#### Scenario: Contributor checks a complete HU

- **WHEN** a contributor runs `pnpm hu:check -- --change <change-name>`
- **THEN** the CLI validates the active OpenSpec change structure, structured HiTL approvals, tasks, review findings, OpenSpec validation, approval-format validation, and anti-harness guardrails.

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

### Requirement: HU pre-code check validates readiness before execution

The project SHALL provide a local command that validates an active HU is ready before product code execution begins.

#### Scenario: Contributor checks a HU before implementation

- **WHEN** a contributor runs `pnpm hu:check:pre-code -- --change <change-name>`
- **THEN** the command verifies the active change has proposal, design, tasks, at least one spec, structured pre-code approval, passing OpenSpec validation, approval-format validation, anti-harness guardrails, and no product changes under `apps/**` or `packages/**`.

### Requirement: HU check CLI enforces one HiTL approval format

The project SHALL provide a local command that rejects legacy HiTL approval wording and accepts only the structured approval format.

#### Scenario: Contributor checks approval format

- **WHEN** a contributor runs `pnpm hu:check:approval-format`
- **THEN** the command scans HU process sources and fails if legacy approval wording is present.
