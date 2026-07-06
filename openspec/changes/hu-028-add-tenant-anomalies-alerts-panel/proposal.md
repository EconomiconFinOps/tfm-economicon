## Why

Users need to distinguish tenant cost anomalies from application health alerts.

The tenant dashboard should surface business alerts such as unusual spend, high-impact services, and cost changes without reusing the system observability alert model.

## User / Actor

- Primary actor: FinOps operator.
- Secondary actors: executive reviewer and authenticated tenant user.
- Tenant/context: tenant-scoped through the active `X-Tenant-Id`.

## Goal

This HU is successful when:

- The Alerts tab shows anomalies and alerts for the active tenant's cost data.
- Each alert explains severity, impact, period, and likely cause.
- Tenant business alerts remain separate from application/system health alerts.

## What Changes

- Add an Alerts dashboard tab or complete the placeholder from HU-025.
- Add backend contract `GET /dashboard/anomalies`.
- Return tenant-scoped anomaly and alert items with severity, status, estimated impact, period, explanation, and affected dimension.
- Use deterministic rules or seed/mock anomalies in v1.
- Keep alerting in-app only; no external notifications.

## Out of Scope

- System health alerts for the application.
- Email, Slack, webhooks, PagerDuty, or Alertmanager.
- Machine-learning anomaly detection.
- Alert assignment, comments, or incident workflow.

## Acceptance Criteria

- **WHEN** a user opens the Alerts tab
  **THEN** they see active tenant cost anomalies and business alerts.

- **WHEN** no anomalies exist
  **THEN** the UI shows a positive empty state for the active tenant.

- **WHEN** a tenant anomaly is severe
  **THEN** the UI makes severity and estimated impact easy to scan.

## Architectural Impact

- Frontend: yes; adds alert/anomaly list, severity treatment, and tenant empty states.
- Backend: yes; adds a tenant-scoped `GET /dashboard/anomalies` route/schema/service or equivalent.
- Processor: no direct change expected in v1.
- Infra/DB: limited; may use deterministic rules or seed/mock tenant data, no external alerting infrastructure.

## Data / Inputs

- Required data: active tenant id, anomaly id, severity, status, period, estimated impact, explanation.
- Optional data: affected service/category/source and recommended next action.
- Source: backend dashboard endpoint.
- Constraints: alerts are tenant business alerts, not app health alerts.

## UX / API Expectations

- UI expectation: alert panel with severity, impact, explanation, and empty state.
- API expectation: `GET /dashboard/anomalies` with auth and `X-Tenant-Id`.
- Error/empty states: separate no-anomalies, unavailable, and denied states.

## Capabilities

### New Capabilities

- `tenant-cost-anomalies-panel`: Shows cost anomalies and business alerts for the active tenant.

### Modified Capabilities

- None.

## Impact

- Product area: frontend and backend.
- Users affected: FinOps operators and tenant stakeholders.
- Permissions/security impact: requires tenant authorization.
- Multi-tenant impact: anomalies must never combine tenant data.
- AI/cost impact: no AI calls required in v1.
- Backward compatibility: separate from system observability alerts.

## Risks / Unknowns

- Alert severity should be simple and explainable while the data model is still basic.
- The UI copy must not imply external notification support.

## Priority / Delivery Notes

- Priority: high.
- Suggested carril: standard.
- Deadline or dependency: depends on HU-025 dashboard tabs.
- Related issue/design/customer request: tenant anomalies and cost alerts.
