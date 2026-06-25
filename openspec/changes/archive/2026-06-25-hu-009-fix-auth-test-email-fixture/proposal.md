## Why

The backend auth test suite currently fails because the demo operator email uses the `.local` domain, which `email-validator` rejects as a special-use domain. This blocks the HU flow from using the backend baseline tests as a reliable validation step.

## What Changes

- Replace the demo operator email with a standards-safe example domain value.
- Keep backend seed data, backend auth tests, frontend login defaults, and user-facing demo documentation aligned on the same demo credential.
- Update the findings backlog entry `RF-004-001` when the fix is implemented and verified.
- Preserve the existing demo password, user identity, tenant relationships, and auth behavior.

## Capabilities

### New Capabilities

- `demo-auth-credentials`: Defines the validity and consistency requirements for demo auth credentials used by seeds, tests, UI defaults, and documentation.

### Modified Capabilities

- None.

## Impact

- Backend seed data and auth schema tests.
- Frontend demo login default value.
- Backend/frontend documentation that shows demo credentials.
- Findings backlog status for `RF-004-001`.
- No database schema, API contract, dependency, security model, or tenant access changes.

## Human Approval

- Change: hu-009-fix-auth-test-email-fixture
- Approval type: pre-code
- Decision: approved
- Approver: user
- Date: 2026-06-25
- Carril: light
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Main risks: local DBs antiguas pueden tener el email viejo; aceptado
- Required changes before execution: none
- Notes: Approved by user before implementation.
