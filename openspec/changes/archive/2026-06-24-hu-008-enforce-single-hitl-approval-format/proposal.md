## Why

The current harness validates the structured HiTL format for future HUs, but legacy approval wording still exists in archived OpenSpec changes and one test fixture. That creates search noise and leaves two visible patterns in the repository.

This change makes the structured HiTL format the only valid path and adds a harness check to prevent the legacy format from coming back.

## What Changes

- Add `pnpm hu:check:approval-format`.
- Integrate approval-format validation into pre-code and pre-archive checks.
- Migrate archived HU approval sections to the structured format.
- Remove direct legacy approval literals from tests and documentation.
- Update the HU check CLI spec and templates.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `hu-check-cli`: Enforces the single structured HiTL approval format and blocks legacy approval wording.

## Impact

- Tooling and documentation only.
- No product behavior changes.
- No new dependencies, skills, agents, hooks, or CI.
- `RF-004-001` remains open.

## Human Approval

- Change: hu-008-enforce-single-hitl-approval-format
- Approval type: pre-code
- Decision: approved
- Approver: user
- Date: 2026-06-24
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: archived HU approvals are normalized from legacy wording
- Required changes before execution: none
- Notes: Make structured HiTL the only valid approval path.
