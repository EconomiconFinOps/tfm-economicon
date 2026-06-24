## Why

Reviews can already document findings inside each HU, but that is not enough for operational follow-up. Once several HUs exist, pending bugs, drift, and accepted exceptions become hard to track if they only live in archived `review.md` files.

This change adds a lightweight central findings backlog while preserving the HU review as the audit trail.

## What Changes

- Add `openspec/findings/README.md` with the findings workflow.
- Add `openspec/findings/backlog.md` as the operational backlog.
- Register the real HU-004 backend test drift finding as `RF-004-001`.
- Update the HU review template to classify findings precisely.
- Update the HU checklist and adaptation plan with backlog rules.
- Link the HU-004 archived review to the central backlog entry.

## Capabilities

### New Capabilities

- `findings-backlog`: Defines a lightweight process for registering, tracking, and closing HU review findings.

### Modified Capabilities

- None.

## Impact

- Documentation and process only.
- No product code changes.
- No custom skills, agents, hooks, CI harness, or global tool configuration.
- No old SDD harness structure is reintroduced.

## Human Approval

- Change: hu-005-add-trackable-findings-backlog
- Approval type: pre-code
- Decision: approved
- Approver: user
- Date: 2026-06-24
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: migrated from legacy approval wording
- Required changes before execution: none
- Notes: Historical approval normalized to the structured HiTL format.
