## Why

The FinOps dashboard spans authentication, tenant selection, frontend tabs, backend dashboard contracts, alerts, reports, recommendations, and PDF export.

The team needs a validation HU to prove the user experience works as a complete tenant-scoped flow.

## User / Actor

- Primary actor: QA-minded engineer or implementing teammate.
- Secondary actors: PM and authenticated tenant user.
- Tenant/context: tenant-scoped through the active `X-Tenant-Id`.

## Goal

This HU is successful when:

- The team can validate the dashboard journey from login to PDF export.
- Tenant boundaries are checked across every dashboard API used by the frontend.
- Loading, empty, error, and responsive states are covered.

## What Changes

- Define an integrated dashboard validation scenario.
- Validate login, tenant selection, dashboard tabs, executive data, operational data, anomalies, reports, recommendations, and PDF download.
- Add the minimum practical automated, smoke, or manual checks for the repo.
- Document how seed/mock data should appear for the active tenant.
- Keep performance and production analytics out of scope.

## Out of Scope

- Load testing or performance tuning.
- Real cloud provider cost ingestion.
- Production monitoring dashboards.
- Full visual regression infrastructure unless the team chooses it in design.

## Acceptance Criteria

- **WHEN** the validation scenario runs against local seed/mock data
  **THEN** the dashboard flow can be checked from login through PDF download.

- **WHEN** a user switches tenants
  **THEN** dashboard data, alerts, reports, and recommendations reflect the active tenant only.

- **WHEN** a dashboard endpoint fails or has no data
  **THEN** the UI shows a clear error or empty state without crashing.

## Architectural Impact

- Frontend: yes; validates the integrated dashboard UX and responsive states.
- Backend: yes; validates tenant-scoped dashboard/report/recommendation/PDF endpoints.
- Processor: no direct requirement unless future data generation depends on processed artifacts.
- Infra/DB: limited; relies on local seed/mock data and may use local test services.

## Data / Inputs

- Required data: local user, tenant seed data, dashboard responses, report/recommendation data.
- Optional data: mocked failures or alternate tenants.
- Source: local backend and frontend app.
- Constraints: validation must preserve tenant isolation and avoid external provider requirements.

## UX / API Expectations

- UI expectation: a user can move through the full dashboard experience without hidden setup beyond documented local prerequisites.
- API expectation: all dashboard APIs used by the frontend are authenticated and tenant-scoped.
- Error/empty states: validation covers unavailable backend data and no-data tenant states.

## Capabilities

### New Capabilities

- `finops-dashboard-experience-validation`: Defines how to validate the integrated dashboard user journey.

### Modified Capabilities

- None.

## Impact

- Product area: frontend, backend, docs/tests.
- Users affected: implementing teammates and future dashboard users.
- Permissions/security impact: validates tenant authorization.
- Multi-tenant impact: checks tenant switching and data isolation.
- AI/cost impact: no external AI or billing cost required.
- Backward compatibility: does not change product behavior directly.

## Risks / Unknowns

- Full local validation may require backend and frontend running together.
- If HU-026 to HU-030 are incomplete, this HU should defer dependent assertions rather than inventing behavior.

## Priority / Delivery Notes

- Priority: medium.
- Suggested carril: standard.
- Deadline or dependency: should run after HU-026 to HU-030 are implemented.
- Related issue/design/customer request: integrated FinOps dashboard validation.
