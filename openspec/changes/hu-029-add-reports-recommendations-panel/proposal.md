## Why

Users need a place to review generated reports and actionable FinOps recommendations for the active tenant.

The current app has assistant conversations and ingestion, but no structured panel for report outputs or recommendations.

## User / Actor

- Primary actor: FinOps operator.
- Secondary actors: executive reviewer and authenticated tenant user.
- Tenant/context: tenant-scoped through the active `X-Tenant-Id`.

## Goal

This HU is successful when:

- The Reports tab lists available reports and recommendations for the active tenant.
- Recommendations show priority, estimated savings, status, and explanation.
- Users can identify which items are ready for export in a later HU.

## What Changes

- Add a Reports dashboard tab or complete the placeholder from HU-025.
- Add backend contracts `GET /reports` and `GET /recommendations`.
- Return tenant-scoped report metadata and recommendation items.
- Include recommendation fields such as priority, estimated savings, status, title, explanation, and related service/category.
- Use deterministic seed/mock data if real recommendation generation is not available.

## Out of Scope

- PDF export, covered by HU-030.
- Recommendation approval workflows.
- Automatic remediation.
- Real AI-based recommendation generation if it requires provider cost or keys.

## Acceptance Criteria

- **WHEN** a user opens the Reports tab
  **THEN** they see tenant reports and recommendations in a scan-friendly layout.

- **WHEN** there are no reports or recommendations
  **THEN** the UI shows a useful empty state for the active tenant.

- **WHEN** a recommendation has estimated savings
  **THEN** the UI displays the amount with currency and priority.

## Architectural Impact

- Frontend: yes; adds report and recommendation lists, loading/error/empty states, and future export entry points.
- Backend: yes; adds tenant-scoped report and recommendation endpoints.
- Processor: limited; future report/recommendation generation may depend on processed artifacts, but v1 can use seed/mock data.
- Infra/DB: limited; may need lightweight seed data or read models depending on design.

## Data / Inputs

- Required data: active tenant id, report metadata, recommendation items.
- Optional data: report period, generated_at, source, recommendation impact and status.
- Source: backend endpoints.
- Constraints: all report and recommendation data must be tenant-scoped.

## UX / API Expectations

- UI expectation: Reports tab with report list and recommendation list in the same product area.
- API expectation: `GET /reports` and `GET /recommendations` with auth and `X-Tenant-Id`.
- Error/empty states: clear empty messages for no reports and no recommendations separately.

## Capabilities

### New Capabilities

- `tenant-reports-recommendations-panel`: Lists reports and recommendations for the active tenant.

### Modified Capabilities

- None.

## Impact

- Product area: frontend and backend.
- Users affected: FinOps operators and executive reviewers.
- Permissions/security impact: requires tenant authorization.
- Multi-tenant impact: no report or recommendation can cross tenant boundaries.
- AI/cost impact: no provider calls unless a future design explicitly adds them.
- Backward compatibility: does not change assistant conversation behavior.

## Risks / Unknowns

- The source of recommendation data may need to be clarified when moving beyond deterministic demo data.
- Reports and recommendations should not duplicate assistant messages unless a clear relationship is designed.

## Priority / Delivery Notes

- Priority: medium.
- Suggested carril: standard.
- Deadline or dependency: depends on HU-025 dashboard tabs.
- Related issue/design/customer request: reports and recommendations panel.
