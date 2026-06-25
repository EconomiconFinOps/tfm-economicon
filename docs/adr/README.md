# Architecture Decision Records

This directory is the project decision log for durable architecture choices.

Use ADRs for decisions that should remain understandable after the originating HU is archived. `design.md` captures HU-local technical design. ADRs capture cross-cutting or long-lived architecture rationale. `docs/architecture.md` describes the current architecture; ADRs explain why important choices were made.

## Naming

- Store ADRs in `docs/adr/`.
- Name files as `ADR-0001-short-slug.md`.
- Increment the number sequentially.
- Keep the slug short, lowercase, and descriptive.

## Status

- `Proposed`: written for review, not final.
- `Accepted`: final decision for the current architecture.
- `Superseded`: replaced by a newer ADR; link the replacement.
- `Deprecated`: no longer recommended, but not directly replaced.

## When An ADR Is Required

Create or update an ADR when a HU decides or changes:

- service or application boundaries
- persistence strategy, database choice, queues, vector stores, or synchronization
- auth, security, permissions, tenancy, or identity architecture
- critical external providers or integration ownership
- LLM, RAG, agent, or cost architecture
- shared patterns that affect multiple modules, apps, packages, or future HUs

## When An ADR Is Not Required

Do not create an ADR for:

- local implementation details
- small refactors
- documentation-only edits without architecture impact
- choices fully captured in one HU `design.md` with no durable cross-HU value

When no ADR is needed, record `ADR: not applicable` in the HU review checklist.

## Workflow

1. During proposal/design, decide whether the HU needs an ADR.
2. If needed, copy `docs/templates/adr.md` into `docs/adr/ADR-NNNN-short-slug.md`.
3. Link the ADR from the HU `design.md`.
4. Keep the ADR status `Proposed` until the decision is accepted.
5. During review, confirm `ADR created/updated` or `ADR not applicable`.
6. Before archive, make sure accepted architecture decisions are in Git/OpenSpec/ADR.

Engram may store gotchas or context, but it is auxiliary memory only. Final architecture decisions must be reflected in Git-tracked OpenSpec, ADR, or project documentation.
