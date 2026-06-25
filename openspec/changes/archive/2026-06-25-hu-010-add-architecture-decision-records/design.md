## Context

The project uses OpenSpec as the source of truth for HU planning, requirements, tasks, reviews, approvals, findings, and archive history. Engram is auxiliary local memory only. `design.md` currently captures technical decisions inside a specific HU, while `docs/architecture.md` describes the current system.

The missing piece is a durable decision log for architecture choices that remain relevant after the HU is archived.

## Goals / Non-Goals

**Goals:**

- Give agents a clear ADR threshold.
- Make ADRs easy to create from a template.
- Keep ADRs linked to OpenSpec/HU context.
- Keep Engram explicitly auxiliary for architecture decisions.
- Integrate the protocol into agent-facing docs and templates.

**Non-Goals:**

- No executable ADR validator in this HU.
- No change to product architecture.
- No migration of historical decisions into ADRs.
- No new agent or skill.

## Decisions

- Store ADRs under `docs/adr/`.
- Use `ADR-0001-short-slug.md` naming.
- Use statuses `Proposed`, `Accepted`, `Superseded`, and `Deprecated`.
- Use `docs/templates/adr.md` as the template.
- Treat `design.md` as the HU-local technical design and ADRs as the durable cross-HU architecture decision record.
- Keep `docs/architecture.md` as the current-state architecture overview; ADRs explain why important architecture choices were made.
- Allow Engram to remember gotchas or context, but require accepted architecture decisions to be reflected in Git/OpenSpec/ADR.

## Risks / Trade-offs

- ADRs could add ceremony for small changes -> Mitigated by documenting when ADRs are not required.
- Agents could duplicate `design.md` and ADR content -> Mitigated by defining `design.md` as HU-local and ADR as durable/cross-cutting.
- No automated check means missed ADRs remain possible -> Accepted for this light documentation HU; review checklist covers the manual gate.

## Open Questions

- None.
