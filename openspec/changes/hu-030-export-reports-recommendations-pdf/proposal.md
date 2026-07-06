## Why

Users need to share FinOps reports and recommendations outside the application.

PDF export should be generated from backend-authorized tenant data so downloaded documents do not rely on mutable browser state or expose data from another tenant.

## User / Actor

- Primary actor: FinOps operator.
- Secondary actors: executive reviewer and authenticated tenant user.
- Tenant/context: tenant-scoped through the active `X-Tenant-Id`.

## Goal

This HU is successful when:

- Users can download a report PDF for an active tenant report.
- Users can download a recommendations PDF for the active tenant.
- The backend enforces tenant access before generating any PDF.

## What Changes

- Add backend PDF export for reports and recommendations.
- Add APIs `GET /reports/{report_id}/export.pdf` and `GET /recommendations/export.pdf`.
- Add frontend download actions from the Reports tab.
- Ensure generated PDFs include tenant, period, report/recommendation content, generated timestamp, and currency context when relevant.
- Return appropriate PDF content type and filename.

## Out of Scope

- Advanced PDF branding and custom templates.
- Emailing reports.
- Scheduled exports.
- Digital signatures or audit-grade document retention.
- Browser-side PDF generation with jsPDF/html2canvas.

## Acceptance Criteria

- **WHEN** a user downloads an accessible report
  **THEN** the backend returns a PDF file for that tenant report.

- **WHEN** a user requests a report from another tenant
  **THEN** the backend denies access and does not generate the PDF.

- **WHEN** a user downloads recommendations
  **THEN** the PDF contains the active tenant recommendations and relevant savings context.

## Architectural Impact

- Frontend: yes; adds download buttons and handles binary responses/errors.
- Backend: yes; adds PDF generation endpoints and tenant authorization around export.
- Processor: no direct change expected.
- Infra/DB: limited; may add a PDF generation dependency, but no external service is required.

## Data / Inputs

- Required data: active tenant id, report id for report export, recommendations for recommendations export.
- Optional data: generated_at, period, currency, summary metadata.
- Source: backend report/recommendation data.
- Constraints: PDF content must come from backend-authorized tenant data.

## UX / API Expectations

- UI expectation: download actions on report and recommendations areas, with loading/error feedback.
- API expectation: `GET /reports/{report_id}/export.pdf` and `GET /recommendations/export.pdf`.
- Error/empty states: show export errors without breaking the dashboard page.

## Capabilities

### New Capabilities

- `tenant-pdf-exports`: Allows reports and recommendations to be exported as tenant-safe PDFs.

### Modified Capabilities

- `tenant-reports-recommendations-panel`: Adds PDF download actions to report and recommendation views.

## Impact

- Product area: frontend and backend.
- Users affected: tenant users who share reports and recommendations.
- Permissions/security impact: tenant authorization is required before export.
- Multi-tenant impact: PDF generation must not mix or leak tenant data.
- AI/cost impact: none unless future recommendation generation uses AI.
- Backward compatibility: adds endpoints without changing existing dashboard endpoints.

## Risks / Unknowns

- Choosing a PDF library may affect backend dependency size and deployment behavior.
- Tests should verify PDF headers and tenant authorization without depending on exact PDF byte output.

## Priority / Delivery Notes

- Priority: medium.
- Suggested carril: standard.
- Deadline or dependency: depends on HU-029 report/recommendation data.
- Related issue/design/customer request: export reports and recommendations to PDF.
