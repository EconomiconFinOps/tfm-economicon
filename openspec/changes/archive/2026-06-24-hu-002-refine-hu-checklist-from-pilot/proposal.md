## Why

HU-001 validated the lightweight OpenSpec workflow, but it exposed practical friction that should be captured before the team uses the process for real product work. The checklist must distinguish product changes from doc-only changes and avoid treating intentional guardrail references as harness regressions.

## What Changes

- Add lessons learned from HU-001 to the HU adaptation plan.
- Refine doc-only workflow guidance for OpenSpec `spec-driven` changes.
- Clarify that `archive --skip-specs` is the correct closure for process/documentation changes.
- Replace text-only anti-harness detection with structural checks plus informational search.
- Keep the workflow lightweight and defer skills/agents until more real HUs produce patterns.

## Capabilities

### New Capabilities

- `hu-checklist-refinement`: Defines checklist refinements learned from HU-001.

### Modified Capabilities

- None.

## Impact

- Documentation only: `docs/openspec-hu-adaptation-plan.md`.
- No product code changes.
- No custom skills, agents, hooks, CI harness, or global tool configuration.

## Human Approval

- Pre-code approval: approved
- Approver: user
- Date: 2026-06-24
- Notes: Doc-only phase 2; refine checklist from HU-001 friction.
