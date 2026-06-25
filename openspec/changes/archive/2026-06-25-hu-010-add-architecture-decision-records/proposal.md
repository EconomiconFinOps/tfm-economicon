## Why

The HU/OpenSpec harness already records requirements, technical design, review, findings, and human approvals. Architecture decisions can currently be captured in `design.md`, but the project does not yet have a durable ADR protocol for decisions that outlive one HU or affect multiple areas.

Agents need an explicit rule for when to create an ADR, where to put it, how it relates to OpenSpec, and why Engram cannot be the only record of architectural decisions.

## What Changes

- Add `docs/adr/README.md` as the project ADR index and operating guide.
- Add `docs/templates/adr.md` as the reusable ADR template.
- Update `AGENTS.md`, the HU adaptation plan, HU templates, and Codex/Claude OpenSpec instructions with ADR rules.
- Add an OpenSpec process capability, `architecture-decisions`, describing the ADR expectations.
- Keep the harness implementation unchanged in this iteration.

## Capabilities

### New Capabilities

- `architecture-decisions`: Defines when and how durable architecture decisions are recorded.

### Modified Capabilities

- None.

## Impact

- Documentation and process instructions only.
- No product behavior changes.
- No changes to `tools/hu-check.mjs`.
- No old SDD harness paths or commands.

## Human Approval

- Change: hu-010-add-architecture-decision-records
- Approval type: pre-code
- Decision: approved
- Approver: user
- Date: 2026-06-25
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: current working tree has unrelated in-progress HU/doc changes; accepted because this HU is doc/process only and will avoid product code.
- Required changes before execution: none
- Notes: User explicitly requested implementation of the approved ADR protocol plan.
