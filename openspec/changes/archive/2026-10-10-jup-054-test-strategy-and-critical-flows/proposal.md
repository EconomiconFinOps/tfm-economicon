JUP: JUP-054
Trello: https://trello.com/c/ZsxwmagI

## Why

The August baseline of 194 service tests predates the frontend quality work and
tenant isolation suites. Repeating those suites would obscure the remaining
integration gaps. Critical component boundaries and infrastructure skips need
explicit coverage and reproducible evidence.

## What Changes

- Map auth, tenant, Azure, RAG, agent, frontend and Docker risks to existing suites.
- Add regression coverage for Azure producer/consumer and agent/ingestion seams.
- Extend the existing real-service tenant journey with persisted history checks.
- Run frontend tests directly in CI so Turbo cannot substitute cached output.
- Document local commands, mandatory CI gates, doubles, skips and limitations.

## Capabilities

### New Capabilities

- `critical-flow-testing`: auditable, reproducible testing of critical boundaries.

### Modified Capabilities

- None.

## Impact

Tests, CI frontend command and technical documentation only. No new application
functionality, production deployment or paid model calls. Initial human role
assignments are retained as historical planning; the user-authorized overdue-MVP
exception and actual attribution are recorded in the delivery evidence.
JUP-087 is reused; real infrastructure checks stay opt-in and are never equated
with offline results. This contribution does not constitute independent review
or validation of its own changes.
