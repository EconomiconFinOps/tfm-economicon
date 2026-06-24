## Why

The project now has OpenSpec and Engram installed, but the team needs a lightweight operating model for completing HUs without recreating the old SDD harness. This pilot validates that an HU can be managed as an OpenSpec change with explicit human review before documentation/code changes and after review.

## What Changes

- Formalize the HU pilot as a doc-only OpenSpec change.
- Keep the flow lightweight: HU, PRD/TD, tasks, HiTL, execution, review, HiTL, archive.
- Confirm Engram remains local-only memory and not a source of truth.
- Link the OpenSpec/Engram setup document to the HU adaptation plan.
- Add explicit human approvals inside this change before execution and after review.

## Capabilities

### New Capabilities

- `openspec-hu-workflow`: Defines the lightweight HU workflow expectations for this project.

### Modified Capabilities

- None.

## Impact

- Documentation only.
- No application code changes.
- No global tool configuration.
- No `.sdd`, `packages/sdd-harness`, `SPEC`, or previous harness commands.

## Human Approval

- Pre-code approval: approved
- Approver: user
- Date: 2026-06-24
- Notes: Doc-only pilot; no product code changes.
