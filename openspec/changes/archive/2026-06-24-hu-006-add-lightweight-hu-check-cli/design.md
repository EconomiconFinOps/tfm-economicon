## Context

The current flow requires contributors to remember several checks: OpenSpec validation, HiTL approvals, review findings, findings backlog linkage, and anti-harness guardrails. The checks are simple enough to automate locally without creating a heavy harness.

## Goals / Non-Goals

**Goals:**

- Validate the structure of an active OpenSpec HU change before archive.
- Validate the findings backlog format and allowed states.
- Validate anti-harness structural guardrails.
- Keep the CLI local, dependency-free, and easy to run through `pnpm`.

**Non-Goals:**

- No product code changes.
- No automatic product `test`, `lint`, or `build` execution.
- No CI integration, hooks, custom agents, custom skills, or global setup.
- No old SDD harness paths or command names.

## Decisions

- Implement the CLI as `tools/hu-check.mjs` using Node standard library only.
- Expose commands through root `package.json` scripts.
- Keep parser helpers exported so `node:test` can cover them directly.
- Make `hu:check` call `pnpm openspec:validate`, because OpenSpec remains the source of truth for change/spec validity.
- Require `review.md` before `hu:check` passes, because the command is intended as a pre-archive gate.
- Require at least one `specs/*/spec.md` for active changes, matching the current OpenSpec `spec-driven` schema.
- Treat product test/lint/build as review evidence, not as v1 CLI responsibility.

## Validation Rules

`hu:check -- --change <change-name>` validates:

- required change artifacts exist,
- pre-code and post-review HiTL approvals are recorded,
- `tasks.md` has no open `- [ ]` tasks,
- `review.md` contains `## Review Findings`,
- required findings are present in `openspec/findings/backlog.md`,
- `pnpm openspec:validate` passes,
- old harness paths are absent and not tracked by Git.

`hu:check:findings` validates:

- backlog file exists,
- required table columns exist,
- finding IDs match `RF-<hu-number>-<sequence>`,
- finding states are one of the allowed lifecycle values.

`hu:check:anti-harness` validates:

- `.sdd`, `packages/sdd-harness`, and `SPEC` do not exist,
- Git does not track old harness paths.

## Risks / Trade-offs

- `hu:check` cannot pass until review and post-review HiTL exist -> Accepted; this is a pre-archive gate, not an execution-start gate.
- Markdown parsing is intentionally simple -> Accepted; templates keep the table shape stable.
- No CI enforcement yet -> Accepted; local repeatability comes first.

## Open Questions

- None for this phase.
