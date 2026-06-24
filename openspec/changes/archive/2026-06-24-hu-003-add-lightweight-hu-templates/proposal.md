## Why

The HU workflow now exists, but repeated manual snippets for approvals, reviews, hotfixes, and checklists would create drift and inconsistent execution. Lightweight templates make the process repeatable without adding a custom harness.

## What Changes

- Add reusable HU templates under `docs/templates/hu/`.
- Link the HU adaptation plan to the templates.
- Keep templates as plain Markdown documentation, not enforcement logic.
- Preserve the lightweight OpenSpec approach and defer custom skills or agents.

## Capabilities

### New Capabilities

- `hu-templates`: Defines reusable lightweight templates for HU approvals, reviews, hotfixes, and operational checklists.

### Modified Capabilities

- None.

## Impact

- Documentation only.
- No product code changes.
- No custom skills, agents, hooks, CI harness, or global tool configuration.

## Human Approval

- Change: hu-003-add-lightweight-hu-templates
- Approval type: pre-code
- Decision: approved
- Approver: user
- Date: 2026-06-24
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: migrated from legacy approval wording
- Required changes before execution: none
- Notes: Historical approval normalized to the structured HiTL format.
