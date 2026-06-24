## Why

The HU/OpenSpec flow is documented and now has a central findings backlog, but the required guardrails are still manual. A small local CLI can catch missing HU artifacts, missing HiTL approvals, untracked findings, and old harness paths before a change is archived.

This keeps the process lightweight while making it more repeatable.

## What Changes

- Add a project-local Node CLI at `tools/hu-check.mjs`.
- Add parser tests at `tools/hu-check.test.mjs`.
- Add `pnpm` scripts for HU checks, findings checks, anti-harness checks, and CLI tests.
- Update HU documentation and templates to run `pnpm hu:check -- --change <change-name>` before archive.

## Capabilities

### New Capabilities

- `hu-check-cli`: Provides a lightweight project-local CLI for validating HU/OpenSpec process guardrails.

### Modified Capabilities

- None.

## Impact

- Tooling and documentation only.
- No product behavior changes.
- No new runtime dependencies.
- No product test/lint/build runner in v1.
- No skills, agents, hooks, CI harness, `.sdd`, `packages/sdd-harness`, or `SPEC`.

## Human Approval

- Change: hu-006-add-lightweight-hu-check-cli
- Approval type: pre-code
- Decision: approved
- Approver: user
- Date: 2026-06-24
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: migrated from legacy approval wording
- Required changes before execution: none
- Notes: Historical approval normalized to the structured HiTL format.
