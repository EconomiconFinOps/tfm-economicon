## Why

The HU harness currently validates a change before archive, but it does not provide a gate for the earlier moment where the process requires human approval before code changes. A pre-code command makes that rule executable without adding a heavy harness.

## What Changes

- Add `pnpm hu:check:pre-code -- --change <change-name>`.
- Validate active HU proposal, design, tasks, specs, structured pre-code approval, OpenSpec validation, anti-harness guardrails, and absence of product changes before execution.
- Update `hu:check` to require the structured HiTL approval format used by the templates.
- Update HU docs and templates to run the pre-code gate before execution.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `hu-check-cli`: Adds a pre-code validation gate and structured HiTL approval validation.

## Impact

- Tooling and documentation only.
- No product behavior changes.
- No new dependencies, skills, agents, hooks, or CI.
- No old SDD harness paths or command names.

## Human Approval

- Change: hu-007-add-pre-code-hu-check
- Approval type: pre-code
- Decision: approved
- Approver: user
- Date: 2026-06-24
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: strict approval format requires future HUs to use the templates
- Required changes before execution: none
- Notes: Add a local pre-code gate before product execution.
