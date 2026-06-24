# Review: HU-006 Add Lightweight HU Check CLI

## Result

Accepted.

## Scope Reviewed

- `tools/hu-check.mjs`
- `tools/hu-check.test.mjs`
- `package.json`
- `docs/openspec-hu-adaptation-plan.md`
- `docs/templates/hu/review.md`
- `docs/templates/hu/hu-checklist.md`
- OpenSpec artifacts for `hu-006-add-lightweight-hu-check-cli`

## Checklist

- [x] CLI exposes local `pnpm hu:*` commands.
- [x] CLI validates active HU structure, HiTL approvals, tasks, review findings, OpenSpec validation, and anti-harness guardrails.
- [x] Findings backlog validation checks required columns, IDs, and states.
- [x] Anti-harness validation checks old paths and tracked files.
- [x] Product test/lint/build suites are not executed by the v1 harness.
- [x] No skills or agents were added.
- [x] No old SDD harness structure was reintroduced.

## Validation

```txt
pnpm install --frozen-lockfile -> passed
pnpm openspec:validate -> passed
pnpm hu:check:test -> passed, 6 tests
pnpm hu:check:findings -> passed
pnpm hu:check:anti-harness -> passed
pnpm hu:check -- --change hu-006-add-lightweight-hu-check-cli -> passed
```

## Review Findings

| ID | Tipo | Severidad | Scope | Descripción | Acción | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-006-001 | Bug | Medium | In scope | `pnpm hu:check -- --change ...` initially failed on Windows/Corepack subprocess handling and `--` argument forwarding. | Fixed before archive. | Not needed |

## Risks / Follow-Ups

- `RF-004-001` remains open and is intentionally not fixed by this HU.
- The harness is Markdown-structure based; if templates change substantially, parser tests should be updated in the same HU.

## Human Approval

- Change: hu-006-add-lightweight-hu-check-cli
- Approval type: pre-code
- Decision: approved
- Approver: user
- Date: 2026-06-24
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: migrated from legacy approval wording
- Required changes before execution: none
- Notes: Historical approval normalized to the structured HiTL format.

## Human Approval

- Change: hu-006-add-lightweight-hu-check-cli
- Approval type: post-review
- Decision: approved
- Approver: user
- Date: 2026-06-24
- Review accepted: yes
- Checks accepted: yes
- Documentation synchronized: yes
- Archive decision: archive
- Notes: Historical approval normalized to the structured HiTL format.
