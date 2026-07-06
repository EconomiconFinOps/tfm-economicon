## Why

The application is multi-tenant. Tenant isolation must be explicit and test-covered before more features are built on top of billing, ingestion, and assistant workflows.

The current backend uses `X-Tenant-Id` for tenant-scoped routes. This HU makes that contract visible and verifies that users cannot access data from tenants they do not belong to.

## What Changes

- Require tenant-scoped backend endpoints to validate `X-Tenant-Id`.
- Add tests for missing tenant header, allowed tenant access, and denied tenant access.
- Review billing, jobs, and assistant routes for consistent tenant enforcement.
- Keep tenant administration out of scope.

## Capabilities

### New Capabilities

- `tenant-isolation`: Defines tenant header requirements and access boundaries for tenant-scoped APIs.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: yes; tenant-scoped requests must consistently send the selected `X-Tenant-Id`.
- Backend: yes; shared tenant dependencies and tenant-scoped route behavior are the main implementation surface.
- Processor: no direct user-facing auth impact; processor jobs should continue to receive tenant context from backend-created payloads.
- Infra/DB: yes; relies on `tenants` and `user_tenants` membership data to enforce boundaries.

## Impact

- Backend dependencies and route tests for tenant-scoped endpoints.
- Existing local seed tenants remain valid.
- No role hierarchy, tenant creation UI, or admin workflow.

## Risks / Unknowns

- Some routes may currently assume a tenant implicitly; this HU should make the intended boundary explicit.
- Tests should avoid broad integration setup if route-level dependency tests are enough.
