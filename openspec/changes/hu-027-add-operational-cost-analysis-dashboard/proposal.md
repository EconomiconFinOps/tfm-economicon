## Why

Operators need more detail than executive users: they need to inspect cost breakdowns, categories, sources, and trends to understand what is driving spend.

The current dashboard does not provide operational analysis beyond a basic billing summary.

## User / Actor

- Primary actor: FinOps operator.
- Secondary actors: authenticated tenant user and technical reviewer.
- Tenant/context: tenant-scoped through the active `X-Tenant-Id`.

## Goal

This HU is successful when:

- The Operational tab shows detailed cost analysis for the active tenant.
- Users can inspect breakdowns by service, category, or source.
- The view supports basic filtering without requiring real cloud provider integration.

## What Changes

- Add an Operational dashboard tab or complete the placeholder from HU-025.
- Add backend contract `GET /dashboard/operational`.
- Return tenant-scoped breakdowns, trend points, detailed rows, and filter metadata.
- Support basic filters such as period, category, service, or source if the design confirms available data.
- Use deterministic seed/mock data where real cost ingestion does not yet exist.

## Out of Scope

- Real-time cost streaming.
- Forecasting, anomaly detection, or recommendation generation.
- External BI embeds.
- Full historical warehouse modeling.

## Acceptance Criteria

- **WHEN** a user opens the Operational tab
  **THEN** they see cost breakdowns, trend information, and a detailed table for the active tenant.

- **WHEN** the user changes a supported filter
  **THEN** the visible data refreshes while keeping the active tenant boundary.

- **WHEN** the backend has no operational data
  **THEN** the UI shows a useful empty state and does not collapse layout.

## Architectural Impact

- Frontend: yes; adds operational analysis UI, filters, tables, and data fetching.
- Backend: yes; adds a tenant-scoped `GET /dashboard/operational` route/schema/service or equivalent.
- Processor: no direct change expected unless later design reuses processed billing artifacts.
- Infra/DB: limited; may use seed/mock data or existing stored artifacts, no warehouse required.

## Data / Inputs

- Required data: active tenant id, cost breakdown rows, trend points, period/currency.
- Optional data: filters for service, source, category, and period.
- Source: backend dashboard endpoint.
- Constraints: all rows and aggregates must be tenant-scoped and internally consistent.

## UX / API Expectations

- UI expectation: operational dashboard with filters, charts or chart-like summaries, and a scan-friendly table.
- API expectation: `GET /dashboard/operational` with auth and `X-Tenant-Id`.
- Error/empty states: filters should remain usable or reset clearly when data is unavailable.

## Capabilities

### New Capabilities

- `operational-cost-analysis-dashboard`: Shows detailed tenant cost breakdowns and trend analysis.

### Modified Capabilities

- None.

## Impact

- Product area: frontend and backend.
- Users affected: FinOps operators and authenticated tenant users.
- Permissions/security impact: requires tenant authorization.
- Multi-tenant impact: must not mix rows or aggregates across tenants.
- AI/cost impact: no AI calls required.
- Backward compatibility: does not replace existing billing summary endpoint.

## Risks / Unknowns

- The repo has limited real cost data today, so the design must define deterministic demo data or a lightweight storage model.
- Adding a chart library should be considered only if native layout is not enough for v1.

## Priority / Delivery Notes

- Priority: high.
- Suggested carril: standard.
- Deadline or dependency: depends on HU-025 dashboard tabs.
- Related issue/design/customer request: operational FinOps analysis.
