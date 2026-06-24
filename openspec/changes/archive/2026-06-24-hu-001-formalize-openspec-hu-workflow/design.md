## Context

`tfm-economicon` uses OpenSpec as the project-local planning workflow and Engram as local-only memory. The project intentionally avoids reintroducing the previous SDD harness because that would duplicate OpenSpec and increase operational weight.

The HU adaptation plan in `docs/openspec-hu-adaptation-plan.md` defines the desired flow:

```txt
HU/PRD+TD/TASKs/HiTL/Execution/Review/HiTL
```

## Goals / Non-Goals

**Goals:**

- Validate a complete OpenSpec change lifecycle with a low-risk documentation HU.
- Keep the implementation lightweight and aligned with OpenSpec primitives.
- Require human approval before changing documentation/code and after review.
- Preserve Git/OpenSpec documents as the source of truth.

**Non-Goals:**

- No product behavior changes.
- No custom harness or CI enforcement in this phase.
- No specialized agents or auditors.
- No global Codex or Engram configuration.

## Decisions

- Use one OpenSpec change named `hu-001-formalize-openspec-hu-workflow`.
- Treat this as a `light` carril because it is doc-only and low risk.
- Use a single documentation capability, `openspec-hu-workflow`, only to satisfy the OpenSpec spec-driven workflow. It does not represent a product feature.
- Use `--skip-specs` during archive because this change documents process, not a runtime product capability.
- Keep Engram optional and local-only; final decisions remain in Git/OpenSpec.

## Risks / Trade-offs

- Process drift -> Mitigated by linking setup documentation to the HU adaptation plan.
- Workflow becoming too heavy -> Mitigated by keeping phase 1 doc-only and using the `light` carril.
- Reintroducing old SDD concepts -> Mitigated by explicitly banning `.sdd`, `packages/sdd-harness`, `SPEC`, and old harness commands.
- OpenSpec requiring a spec artifact for doc-only work -> Mitigated by creating a narrow process capability and skipping spec sync on archive.

## Open Questions

- None for phase 1.
