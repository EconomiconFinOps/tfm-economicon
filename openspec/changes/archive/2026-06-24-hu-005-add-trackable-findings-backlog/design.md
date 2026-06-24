## Context

The current HU flow keeps review evidence inside each OpenSpec change. That is useful for audit history, but it does not provide a single place to see unresolved findings or follow-up fixes. HU-004 exposed this gap: a backend baseline test failure was correctly documented as out of scope, but there was no central backlog to track the follow-up.

## Goals / Non-Goals

**Goals:**

- Keep the HU `review.md` as the historical source for what was found during a review.
- Add a central backlog for findings that need a decision, fix, or explicit closure.
- Make findings searchable and stable through IDs.
- Keep the process Markdown-only and lightweight.

**Non-Goals:**

- No product code changes.
- No executable harness, hooks, CI enforcement, skills, or agents.
- No issue tracker replacement beyond a small project-local backlog.
- No one-file-per-finding structure until volume justifies it.

## Decisions

- Store the backlog under `openspec/findings/` because findings are part of the OpenSpec-governed change process.
- Use `openspec/findings/backlog.md` as a single table for now.
- Use stable IDs in the format `RF-<hu-number>-<sequence>`, for example `RF-004-001`.
- Require every out-of-scope finding to be added to the central backlog before HiTL final.
- Allow in-scope findings to stay out of the backlog only if they are resolved before closure and documented in the review.
- Keep closed entries in the backlog instead of deleting them.
- Archive this change with `--skip-specs` because it changes process documentation, not product behavior.

## Finding Lifecycle

1. Detect finding during review.
2. Record it in the HU `review.md`.
3. If it is out of scope, unresolved, or deferred, add it to `openspec/findings/backlog.md`.
4. If it becomes a HU, set `Estado` to `Planned` or `In progress` and fill `Change/Fix`.
5. When fixed or accepted, update `Estado` and keep the row for history.

## Risks / Trade-offs

- A central backlog can become stale -> Mitigated by adding backlog checks to the HU checklist.
- Too many columns can add friction -> Mitigated by using a single compact table with required fields only.
- A Markdown backlog is not automatic enforcement -> Accepted for now; agents or automation can be considered after more HUs.

## Open Questions

- None for this phase.
