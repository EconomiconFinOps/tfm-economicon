# Review: HU-004 Add Health Checked At

## Result

Accepted with one unrelated baseline test failure documented.

## Scope Reviewed

- `apps/backend/app/schemas/health.py`
- `apps/backend/app/api/routes/health.py`
- `apps/backend/tests/test_health_schema.py`
- OpenSpec artifacts for `hu-004-add-health-checked-at`

## Findings

- `GET /health` now returns `checked_at` through `HealthResponse`.
- `checked_at` is generated at request time with a UTC-aware timestamp.
- Existing `status` and `services` semantics remain unchanged.
- No frontend or processor files were modified.
- No skills or agents were added.
- No old harness structure was reintroduced.

## Validation

```txt
pnpm install --frozen-lockfile -> passed
pnpm openspec:validate -> passed
pnpm --filter @finops/backend lint -> passed
python -m pytest tests\test_health_schema.py -> passed, 3 tests
Test-Path .sdd -> false
Test-Path packages\sdd-harness -> false
Test-Path SPEC -> false
git ls-files old harness paths -> no matches
```

## Documented Exception

```txt
pnpm --filter @finops/backend test -> failed outside HU-004 scope
```

The failure is in existing `tests/test_auth_schema.py`, where `LoginRequest(email="operator@finops.local")` is rejected by the currently installed `email-validator` because `.local` is a reserved/special-use domain. HU-004 health tests pass. The auth seed/default email issue should be handled as a separate HU.

## Review Findings

| ID | Tipo | Severidad | Scope | Descripción | Acción | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-004-001 | Test drift | Medium | Out of scope | `pnpm --filter @finops/backend test` fails because `operator@finops.local` is rejected by `email-validator` in `tests/test_auth_schema.py`. | Create a follow-up HU to replace the `.local` fixture with a valid test domain. | Added to `openspec/findings/backlog.md` |

## Human Approval

- Pre-code approval: approved
- Post-review approval: approved
- Approver: user
- Date: 2026-06-24
- Notes: Health timestamp implementation reviewed; unrelated auth baseline failure accepted as separate follow-up.
