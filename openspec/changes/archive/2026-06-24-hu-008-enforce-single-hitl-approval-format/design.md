## Context

HU-007 introduced structured HiTL validation, but legacy approval wording remains in archived changes. The harness rejects legacy approvals for active checks, yet the old wording can still be copied from history or appear in search results.

## Goals / Non-Goals

**Goals:**

- Normalize archived approval sections to the structured format.
- Add a dedicated approval-format check to the harness.
- Make pre-code and pre-archive checks fail if legacy approval wording appears.
- Keep test fixtures from storing legacy literals directly.

**Non-Goals:**

- No product code changes.
- No migration of business specs unrelated to `hu-check-cli`.
- No CI, hooks, skills, or agents.

## Decisions

- Scan `docs`, `openspec`, `tools`, and root `package.json` for legacy approval labels.
- Build legacy labels from string fragments in the harness and tests so the repository does not contain the exact legacy literals.
- Keep archived HUs under `openspec/changes/archive/`, but normalize their approval sections.
- Use ASCII-only findings headers: `Descripcion` and `Accion`.

## Risks / Trade-offs

- Migrating archived reviews changes historical wording -> Accepted because the user wants a single visible path and the approval decisions remain approved.
- The check is text-based -> Accepted because the legacy risk is textual copy/paste drift.

## Open Questions

- None for this phase.
