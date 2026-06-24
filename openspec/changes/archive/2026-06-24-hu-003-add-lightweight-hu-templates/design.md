## Context

HU-001 validated the lightweight OpenSpec flow and HU-002 refined the checklist with pilot friction. The next repeated need is template consistency: every HU needs the same approval, review, hotfix, and checklist shape without asking contributors to reconstruct it from prose.

## Goals / Non-Goals

**Goals:**

- Provide copyable Markdown templates for the recurring HU artifacts.
- Keep templates small, explicit, and easy to paste into an OpenSpec change.
- Point the HU adaptation plan to the canonical template location.
- Avoid any automation that would recreate a heavy harness.

**Non-Goals:**

- No product code changes.
- No custom OpenSpec schemas.
- No new skills or agents.
- No CI or hook enforcement.

## Decisions

- Store templates in `docs/templates/hu/` because they are project documentation, not executable tooling.
- Use clear placeholders such as `<change-name>`, `<approver>`, and `<date>`.
- Keep templates generic enough for `light`, `standard`, and `hotfix` HUs.
- Keep HiTL approvals separate from review so the two human checkpoints remain visible.
- Archive this change with `--skip-specs` because it documents process and templates, not product capability.

## Risks / Trade-offs

- Templates can become stale -> Mitigated by linking them from the HU adaptation plan.
- Too many fields can make the flow heavy -> Mitigated by keeping each template short and optional fields explicit.
- Templates are not enforcement -> Accepted; enforcement can be evaluated in a later phase after real HUs.

## Open Questions

- None for phase 3.
