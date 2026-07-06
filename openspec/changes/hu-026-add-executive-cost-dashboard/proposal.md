## Why

Decision makers need a fast view of global cost posture for the active tenant.

The current billing summary is too small to explain spend, savings, variation, and the main drivers behind the tenant's cost position.

## User / Actor

- Primary actor: executive or manager reviewing tenant cost posture.
- Secondary actors: FinOps operator and authenticated tenant user.
- Tenant/context: tenant-scoped through the active `X-Tenant-Id`.

## Goal

This HU is successful when:

- The Executive tab shows global cost metrics for the active tenant.
- The user can understand spend, savings, variation, and top cost drivers at a glance.
- The data comes from a backend-owned tenant-scoped endpoint.

## What Changes

- Add an Executive dashboard tab or complete the existing placeholder from HU-025.
- Add backend contract `GET /dashboard/executive`.
- Return tenant-scoped executive metrics such as total spend, savings identified, spend variation, currency, top drivers, and summary period.
- Use deterministic seed/mock data if real cloud cost ingestion is not available yet.
- Keep the view focused on tenant-level cost, not system health.

## Out of Scope

- Real cloud provider billing integration.
- Multi-tenant rollups across all tenants.
- Predictive forecasting or budget automation.
- PDF export.

## Acceptance Criteria

- **WHEN** a user opens the Executive tab for an active tenant
  **THEN** they see global spend, savings, variation, currency, period, and top drivers.

- **WHEN** the user lacks access to a tenant
  **THEN** the backend denies the request using the existing tenant boundary.

- **WHEN** there is no executive data for a tenant
  **THEN** the UI shows a clear empty state rather than fake loaded metrics.

## Architectural Impact

- Frontend: yes; adds the Executive tab content, data hook, loading/error/empty states, and cost-focused presentation.
- Backend: yes; adds a tenant-scoped `GET /dashboard/executive` route/schema/service or equivalent.
- Processor: no direct change expected.
- Infra/DB: limited; may use seed/mock data or existing operational tables, with no new cloud provider integration.

## Data / Inputs

- Required data: active tenant id, authenticated user, executive cost summary.
- Optional data: top drivers, variation percentage, comparison period.
- Source: backend dashboard endpoint.
- Constraints: all values must be scoped to the active tenant and include currency/period context.

## UX / API Expectations

- UI expectation: executive summary cards plus a short driver list designed for quick scanning.
- API expectation: `GET /dashboard/executive` with auth and `X-Tenant-Id`.
- Error/empty states: show denied, unavailable, and no-data states distinctly.

## Capabilities

### New Capabilities

- `executive-cost-dashboard`: Shows global cost posture for the active tenant.

### Modified Capabilities

- None.

## Impact

- Product area: frontend and backend.
- Users affected: authenticated tenant users, especially executive personas.
- Permissions/security impact: requires tenant authorization.
- Multi-tenant impact: no cross-tenant aggregation in this HU.
- AI/cost impact: cost data is surfaced but no AI provider cost is introduced.
- Backward compatibility: existing `/billing/summary` can remain available.

## Risks / Unknowns

- Seed/mock data should be clearly deterministic and tenant-safe.
- The dashboard should not imply live cloud billing integration if data is not live.

## Priority / Delivery Notes

- Priority: high.
- Suggested carril: standard.
- Deadline or dependency: depends on HU-025 dashboard tabs.
- Related issue/design/customer request: executive cost dashboard.
