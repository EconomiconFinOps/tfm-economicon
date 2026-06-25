# Agent Instructions

## HU/OpenSpec Workflow

- Use OpenSpec as the source of truth for HU planning, implementation tasks, reviews, approvals, and archive history.
- Read `docs/openspec-hu-adaptation-plan.md` for the full workflow and `docs/templates/hu/` for reusable approval, review, hotfix, and checklist snippets.
- Do not reintroduce the old SDD harness paths: `.sdd`, `packages/sdd-harness`, or `SPEC`.
- Use `pnpm exec openspec ...` for direct OpenSpec CLI calls such as `status`, `instructions`, and other commands not exposed as package scripts.
- Run the local HU checks when working through a change:
  - `pnpm hu:check:pre-code -- --change <change-name>` before product code changes.
  - `pnpm hu:check -- --change <change-name>` before archive.
  - `pnpm hu:check:findings` when `openspec/findings/backlog.md` changes.
- Do not edit product code or execution-relevant product files before `pnpm hu:check:pre-code -- --change <change-name>` passes.
- Do not archive a change before `pnpm hu:check -- --change <change-name>` passes.

## Happy Path For HU Changes

1. Check active work with `pnpm openspec:list`.
2. Create or propose the HU with `/opsx:propose "<description>"` or `pnpm exec openspec new change "<change-name>"`.
3. Complete `proposal.md`, `design.md`, `specs/*/spec.md`, and `tasks.md`.
4. Assess whether the HU needs an ADR; create or link it before implementation when the decision is durable or cross-cutting.
5. Record structured pre-code HiTL approval in the change.
6. Run `pnpm openspec:validate`.
7. Run `pnpm hu:check:pre-code -- --change <change-name>` and stop if it fails.
8. Implement with `/opsx:apply <change-name>` or equivalent task-by-task edits.
9. Mark each completed task in `tasks.md`.
10. Run the required checks for the selected carril and record exact commands/results in `review.md`.
11. Record review findings in `review.md`; update `openspec/findings/backlog.md` when required.
12. Record `ADR created/updated` or `ADR not applicable` in review.
13. Record structured post-review HiTL approval.
14. Run `pnpm hu:check -- --change <change-name>` and stop if it fails.
15. Sync specs if applicable.
16. Archive the change.

## Harness Issues

- Any problem, failure, drift, or workaround involving the HU/OpenSpec harness or local HU checks must be documented in the HU `review.md`.
- If the harness issue is unresolved, deferred, out of scope, or accepted as risk, also add it to `openspec/findings/backlog.md` with a stable `RF-<hu-number>-<sequence>` ID.
- Do not leave harness problems only in chat, terminal output, or local memory.

## Engram Usage For Agents

- Use Engram only as auxiliary local memory for gotchas, recurring decisions, and operational context.
- Do not use Engram as the only source for requirements, approvals, review results, findings, acceptance criteria, or final decisions.
- If Engram context affects a HU, reflect that information in the relevant OpenSpec artifact or Git-tracked documentation.

## Architecture Decision Records

- Use `docs/adr/` for durable architecture decisions and `docs/templates/adr.md` for new ADRs.
- Name ADRs as `ADR-0001-short-slug.md` and use the statuses `Proposed`, `Accepted`, `Superseded`, or `Deprecated`.
- Create or update an ADR when a HU changes service/app boundaries, persistence, queues, vector stores, sync, auth/security/tenancy, critical external providers, LLM/RAG/cost architecture, or shared patterns that affect multiple modules or future HUs.
- Do not create an ADR for local implementation details, small refactors, docs-only edits without architecture impact, or choices fully captured in one HU `design.md`.
- `design.md` records HU-local technical design; ADRs record durable cross-HU architecture rationale.
- `docs/architecture.md` describes the current architecture; ADRs explain why important choices were made.
- Link applicable ADRs from the HU `design.md` or `review.md`.
- Before archive, accepted architecture decisions must be reflected in Git/OpenSpec/ADR, not only in Engram.
