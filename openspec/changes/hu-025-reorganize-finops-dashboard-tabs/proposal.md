## Why

The current dashboard mixes a small billing summary, tenant information, and system health in a single overview.

Users need a clearer FinOps workspace before adding executive cost views, operational analysis, tenant anomalies, reports, and recommendations.

## User / Actor

- Primary actor: authenticated tenant user.
- Secondary actors: operators and PM/engineering team validating the demo workflow.
- Tenant/context: tenant-scoped through the active `X-Tenant-Id`.

## Goal

This HU is successful when:

- The dashboard has clear internal tabs for executive, operational, alerts, and reports views.
- The existing login, tenant selector, and main navigation keep working.
- The first version can host future dashboard slices without making the overview page harder to maintain.

## What Changes

- Reorganize the current dashboard into a FinOps dashboard surface with internal tabs.
- Add tab labels for Executive, Operational, Alerts, and Reports.
- Keep current tenant context visible and respected across all tabs.
- Preserve existing billing summary behavior until deeper dashboard APIs are added by follow-up HUs.

## Out of Scope

- New deep analytics data.
- PDF export.
- Tenant anomaly rules.
- New backend dashboard endpoints beyond what is needed to avoid breaking the current page.

## Acceptance Criteria

- **WHEN** an authenticated user opens the dashboard with an active tenant
  **THEN** they can switch between Executive, Operational, Alerts, and Reports tabs.

- **WHEN** the active tenant changes
  **THEN** the dashboard remains tenant-scoped and tab content refreshes or resets consistently.

- **WHEN** no tenant is active
  **THEN** the dashboard shows a clear tenant-required state instead of partial data.

## Architectural Impact

- Frontend: yes; dashboard page, UI state, API hook organization, and styling are the main implementation surface.
- Backend: limited; no new analytical contracts are required unless the design needs a compatibility endpoint.
- Processor: no; this is a user dashboard structure change.
- Infra/DB: no direct change expected.

## Data / Inputs

- Required data: authenticated session, active tenant, existing billing summary if still displayed.
- Optional data: tenant metadata for display.
- Source: frontend state and backend tenant/billing APIs.
- Constraints: all visible data must follow the active tenant context.

## UX / API Expectations

- UI expectation: one Dashboard entry with internal tabs, not four separate sidebar routes.
- API expectation: existing calls can remain until the follow-up HUs add dedicated dashboard endpoints.
- Error/empty states: tenant-required, loading, and backend-unavailable states remain visible and professional.

## Capabilities

### New Capabilities

- `finops-dashboard-tabs`: Provides the dashboard shell for executive, operational, alerts, and reports areas.

### Modified Capabilities

- None.

## Impact

- Product area: frontend.
- Users affected: authenticated tenant users.
- Permissions/security impact: must preserve current auth and tenant requirements.
- Multi-tenant impact: active tenant selection drives all dashboard content.
- AI/cost impact: none.
- Backward compatibility: compatible with existing dashboard data while the new slices are implemented.

## Risks / Unknowns

- The current CSS may need cleanup to avoid a crowded dashboard as tabs are added.
- The UI should avoid implying that future tabs have full analytics before their APIs exist.

## Priority / Delivery Notes

- Priority: high.
- Suggested carril: standard.
- Deadline or dependency: should be completed before HU-026 to HU-030.
- Related issue/design/customer request: FinOps user dashboard expansion.
