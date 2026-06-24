# HU Review

Use this after execution and before final human approval.

```md
# Review: <change-name>

## Result

Accepted | Changes requested | Rejected

## Scope Reviewed

- <files, areas, or artifacts reviewed>

## Checklist

- [ ] Implementation matches acceptance criteria.
- [ ] Tasks are marked accurately in `tasks.md`.
- [ ] Tests/checks were executed or exceptions are documented.
- [ ] `proposal.md`, `design.md`, `specs`, and `tasks.md` match the final state.
- [ ] No product decision exists only in Engram.
- [ ] No old harness structure was reintroduced.

## Validation

```txt
pnpm install --frozen-lockfile -> <result>
pnpm openspec:validate -> <result>
pnpm test -> <result or documented exception>
pnpm lint -> <result or documented exception>
pnpm build -> <result or documented exception>
structural anti-harness checks -> <result>
rg anti-harness search -> <result and interpretation>
```

## Review Findings

Use `None.` when there are no findings.

| ID | Tipo | Severidad | Scope | Descripción | Acción | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-<hu>-001 | <bug/test drift/doc drift/guardrail/debt/risk> | <Low/Medium/High/Critical> | <In scope/Out of scope> | <description> | <fix/defer/accept/create HU> | <Added/Not needed> |

Rules:

- Every `Out of scope` finding must be added to `openspec/findings/backlog.md`.
- Every unresolved or deferred finding must be added to `openspec/findings/backlog.md`.
- Every `In scope` finding must be fixed before HiTL final or explicitly accepted by the human approver.
- Link backlog entries using stable IDs such as `RF-004-001`.

## Risks / Follow-Ups

- <risk/follow-up or "none">
```
