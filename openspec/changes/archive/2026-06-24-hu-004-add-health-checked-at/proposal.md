## Why

Consumers of `GET /health` can see current service status but cannot tell when that status was evaluated. Adding a server-generated timestamp makes health responses easier to reason about in dashboards, logs, and troubleshooting.

## What Changes

- Add `checked_at` to the backend `GET /health` response.
- Generate `checked_at` at request time in UTC.
- Preserve existing `status` and `services` behavior.
- Add backend tests for schema and route behavior.

## Capabilities

### New Capabilities

- `health-status`: Describes the backend health response contract.

### Modified Capabilities

- None.

## Impact

- Public API response for `GET /health` gains one additive field.
- Backend only: schema, route, and tests.
- No frontend or processor changes.
- Backward compatible for existing clients.

## Human Approval

- Pre-code approval: approved
- Approver: user
- Date: 2026-06-24
- Carril: light
- Notes: Backend-only health response timestamp.
