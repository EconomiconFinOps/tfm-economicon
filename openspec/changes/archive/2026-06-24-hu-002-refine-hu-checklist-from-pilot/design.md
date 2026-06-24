## Context

HU-001 completed the first pilot cycle and archived successfully. Its review documented several concrete lessons:

- OpenSpec `spec-driven` requires `proposal`, `design`, `specs`, and `tasks` even for doc-only changes.
- `archive --skip-specs` is appropriate when the change documents workflow rather than product capability.
- `rg` anti-harness searches can find intentional guardrail references, so path-based structural checks are needed.
- `pnpm openspec:validate` after archiving may report no active items and still be a valid state.

## Goals / Non-Goals

**Goals:**

- Update the HU checklist with HU-001 lessons.
- Make doc-only changes explicit in the workflow.
- Separate structural anti-harness checks from informational text search.
- Keep the process lightweight.

**Non-Goals:**

- No product code changes.
- No new OpenSpec schema customization.
- No new skills or agents.
- No CI/hook enforcement in this phase.

## Decisions

- Keep using OpenSpec `spec-driven` as-is, including a minimal spec for doc-only changes when required.
- Use `--skip-specs` for doc-only/process changes at archive time.
- Treat `rg` anti-harness output as informational; only structural path existence/tracked files should fail the guardrail.
- Add a dedicated "Lecciones de HU-001" section rather than scattering the lessons across the whole document.

## Risks / Trade-offs

- More checklist text could make the flow feel heavier -> Mitigated by keeping the additions focused on real friction only.
- A doc-only spec can look like a product capability -> Mitigated by naming it as process/checklist refinement and skipping spec sync.
- Structural checks may miss renamed harness-like folders -> Mitigated by retaining `rg` as an informational scan.

## Open Questions

- None for phase 2.
