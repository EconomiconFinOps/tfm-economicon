# Review: HU-008 Enforce Single HiTL Approval Format

## Result

Accepted.

## Scope Reviewed

- `tools/hu-check.mjs`
- `tools/hu-check.test.mjs`
- `package.json`
- `docs/openspec-hu-adaptation-plan.md`
- `docs/templates/hu/`
- `openspec/changes/archive/`
- OpenSpec artifacts for `hu-008-enforce-single-hitl-approval-format`

## Checklist

- [x] Structured HiTL is the only approval format in active docs and archived HUs.
- [x] The harness exposes `hu:check:approval-format`.
- [x] Pre-code and pre-archive gates run approval-format validation.
- [x] Legacy approval fixtures are built dynamically in tests.
- [x] Findings headers stay ASCII-only.
- [x] No product code was modified.
- [x] No skills or agents were added.
- [x] No old SDD harness structure was reintroduced.

## Validation

```txt
pnpm install --frozen-lockfile -> passed
pnpm openspec:validate -> passed
pnpm hu:check:test -> passed, 9 tests
pnpm hu:check:findings -> passed
pnpm hu:check:anti-harness -> passed
pnpm hu:check:approval-format -> passed
pnpm hu:check:pre-code -- --change hu-008-enforce-single-hitl-approval-format -> passed
pnpm hu:check -- --change hu-008-enforce-single-hitl-approval-format -> passed
legacy literal search -> no matches
```

## Review Findings

None.

## Risks / Follow-Ups

- Archived HU approval wording was normalized intentionally to remove alternate examples.
- `RF-004-001` remains open and is intentionally not fixed by this HU.

## Human Approval

- Change: hu-008-enforce-single-hitl-approval-format
- Approval type: post-review
- Decision: approved
- Approver: user
- Date: 2026-06-24
- Review accepted: yes
- Checks accepted: yes
- Documentation synchronized: yes
- Archive decision: archive
- Notes: Single HiTL approval format enforcement reviewed and accepted.
