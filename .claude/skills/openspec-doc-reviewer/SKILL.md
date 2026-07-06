---
name: openspec-doc-reviewer
description: Review documentation drift after an OpenSpec change is archived. Use when a change has just been archived, when the user asks for a post-archive documentation review, or when Claude needs to update docs/architecture.md, app READMEs, docs/hu-release-notes.md, manuals, and ADR recommendations based on completed implementation.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
  generatedBy: "1.4.1"
---

Run a post-archive documentation review for an OpenSpec change.

The goal is to keep durable documentation aligned with the behavior that was actually implemented and accepted. Treat the archived change as evidence, not as a planning request.

## Inputs

Accept either:

- a change name, such as `hu-012-strengthen-tenant-isolation`
- an archive path, such as `openspec/changes/archive/YYYY-MM-DD-<change-name>`
- no input, only if the just-archived change is clear from the conversation

If the target is ambiguous, list likely archived changes and ask the user to choose.

## Workflow

1. **Resolve the archived change**
   - Prefer the concrete archive path reported by `openspec-archive-change`.
   - If only a name is provided, search `openspec/changes/archive/*-<change-name>`.
   - Read available artifacts: `proposal.md`, `design.md`, `tasks.md`, `review.md`, and `specs/**/spec.md`.
   - If artifacts are missing, continue with what exists and say which evidence was unavailable.

2. **Understand the accepted behavior**
   - Extract completed behavior, affected subsystems, new or changed APIs, data model changes, queues, auth/tenant rules, AI/RAG behavior, observability behavior, and operational assumptions.
   - Prefer `review.md`, completed tasks, synced specs, and code diffs over original intent if they disagree.
   - Do not revive rejected or deferred scope as documented current behavior.

3. **Inspect live documentation**
   - Always inspect `docs/architecture.md`.
   - Always inspect `docs/hu-release-notes.md`.
   - Inspect app-level READMEs when affected, especially `apps/frontend/README.md`, `apps/backend/README.md`, and `apps/processor/README.md` if present.
   - Inspect `docs/adr/` when the change touches durable architecture.
   - Use `rg` to find obsolete terms, endpoint names, old diagrams, or future-tense statements contradicted by the completed change.

4. **Apply documentation updates**
   - Update `docs/architecture.md` when the change affects system responsibilities, data flows, storage, queues, auth/tenancy, assistant/RAG behavior, observability, or public service boundaries.
   - Update app READMEs or manuals when setup, contracts, local workflow, or user-facing behavior changed.
   - Keep docs junior-friendly, factual, and current-state oriented.
   - Do not edit product code, migrations, tests, archived artifacts, or OpenSpec specs during this review unless the user explicitly asks.

5. **Assess ADR need**
   - Suggest an ADR when the change introduced or changed a durable/cross-cutting decision, such as:
     - database or persistence strategy
     - auth, security, permissions, or tenant boundaries
     - asynchronous messaging or job lifecycle policy
     - AI/RAG, embeddings, model/provider, or cost architecture
     - observability, alerting, or logging architecture
     - deployment, runtime topology, or external service integration
   - If an ADR already exists and still matches, cite it.
   - If an ADR is missing, recommend a concise title and rationale.
   - Create or edit ADR files only when the user explicitly asks for that, or when the invoking workflow explicitly requires ADR creation.

6. **Update HU release notes history**
   - Update `docs/hu-release-notes.md` for every successfully archived HU.
   - Add exactly one row per archived change if it is not already present.
   - Keep rows chronological by archive date and HU number.
   - Use this table shape: `Date | HU | Release note | Review | ADRs`.
   - Keep the release note to one brief sentence focused on accepted behavior.
   - Link `Review` to the archived `review.md`.
   - Link `ADRs` to any ADR files created or updated by the HU; write `None` only when the review/design explicitly marks ADR not applicable or no ADR exists.
   - Do not duplicate rows when rerunning the reviewer for the same archive.

7. **Validate the review**
   - Run targeted `rg` checks for phrases or endpoint names that should have changed.
   - Check that `docs/hu-release-notes.md` contains the archived change name and its `review.md` link.
   - Use `git diff -- docs` or equivalent to review documentation edits.
   - Do not run product tests for documentation-only changes unless the docs include generated artifacts that require validation.

## Output

Report:

- archived change reviewed
- documentation files updated
- drift fixed
- ADR recommendation: `none`, `existing ADR ok`, or `suggest new ADR: <title>`
- HU release notes: `updated` or `already current`
- checks run
- remaining documentation risks or follow-up HUs, if any

If no edits are needed, say that clearly and include the evidence used.

## Guardrails

- Keep documentation aligned to implemented behavior, not future plans.
- Do not document secrets, credentials, internal URLs, or raw tenant data.
- Preserve unrelated user changes.
- Prefer small documentation edits over broad rewrites.
- If code and archived artifacts conflict, pause and report the conflict before updating docs.
