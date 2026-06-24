## ADDED Requirements

### Requirement: HU pre-code check validates readiness before execution

The project SHALL provide a local command that validates an active HU is ready before product code execution begins.

#### Scenario: Contributor checks a HU before implementation

- **WHEN** a contributor runs `pnpm hu:check:pre-code -- --change <change-name>`
- **THEN** the command verifies the active change has proposal, design, tasks, at least one spec, structured pre-code approval, passing OpenSpec validation, anti-harness guardrails, and no product changes under `apps/**` or `packages/**`.

## MODIFIED Requirements

### Requirement: HU check CLI validates active changes

The project SHALL provide a local CLI that validates the required HU/OpenSpec artifacts before a change is archived.

#### Scenario: Contributor checks a complete HU

- **WHEN** a contributor runs `pnpm hu:check -- --change <change-name>`
- **THEN** the CLI validates the active OpenSpec change structure, structured HiTL approvals, tasks, review findings, OpenSpec validation, and anti-harness guardrails.
