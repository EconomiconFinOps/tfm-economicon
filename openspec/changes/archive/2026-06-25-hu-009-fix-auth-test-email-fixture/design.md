## Context

HU-004 documented `RF-004-001`: `pnpm --filter @finops/backend test` fails because `LoginRequest(email="operator@finops.local")` is rejected by `email-validator`. The same `.local` value is also used by backend seed data, frontend login defaults, and README examples, so fixing only the test would leave the demo flow inconsistent.

## Goals / Non-Goals

**Goals:**

- Use one valid demo operator email everywhere the seeded demo login is referenced.
- Make the auth schema test pass under the installed `email-validator` behavior.
- Keep the change small enough for the light HU lane.
- Close or update `RF-004-001` with the HU that fixed it.

**Non-Goals:**

- Change auth semantics, password handling, JWT behavior, tenant authorization, or user roles.
- Add migrations or alter persisted schema.
- Introduce a configurable demo user system.
- Broaden auth test coverage beyond the fixture drift.

## Decisions

- Use `operator@example.com` as the replacement demo email.
  - Rationale: `example.com` is reserved for documentation/examples and is accepted by normal email validators.
  - Alternative considered: `operator@finops.example`. Rejected because some validators treat non-public or uncommon example-style TLDs differently.

- Update all active demo credential references in product code and docs, not only the failing test.
  - Rationale: the frontend default login, backend seed, and README examples describe one demo account; leaving them split would create process and user confusion.
  - Alternative considered: limit the HU to `apps/backend/tests/test_auth_schema.py`. Rejected because the seeded login would still advertise an invalid email.

- Do not add a new shared constant in this HU.
  - Rationale: the value appears in a small number of files across backend, frontend, and docs; a shared cross-package constant would add more structure than this fix needs.
  - Alternative considered: create a shared fixture/config module. Deferred until demo credentials become more complex.

## Risks / Trade-offs

- Existing local databases seeded with `operator@finops.local` may still contain the old user until re-seeded or updated.
  - Mitigation: this project uses idempotent seed `UPSERT` keyed by user id, so initialization updates the seeded user's email to the new value.

- Documentation or inactive/rejected design notes may still mention `.local`.
  - Mitigation: update active product docs and code paths only; rejected architecture notes are historical and not runtime guidance.

- The change touches backend, frontend, docs, and backlog.
  - Mitigation: keep the implementation mechanical and verify with focused backend auth tests plus OpenSpec and HU checks.
