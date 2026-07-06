## Why

The system can create ingestion jobs, but users and operators need better visibility into the job lifecycle after a job is queued.

Without query endpoints, the frontend cannot reliably show whether an ingestion is queued, running, completed, or failed.

## What Changes

- Add backend APIs to list ingestion jobs for the active tenant.
- Add a backend API to fetch one job by id for the active tenant.
- Return status, source, artifact URI, timestamps, and result/error information where available.
- Keep cancellation and manual retries out of scope.

## Capabilities

### New Capabilities

- `job-lifecycle-visibility`: Defines how clients inspect ingestion job status and results.

### Modified Capabilities

- None.

## Architectural Impact

- Frontend: likely downstream; this HU enables a UI to show job state, but the first implementation may expose only the backend contract.
- Backend: yes; adds job read APIs, schemas, and tenant-scoped database queries.
- Processor: no direct behavior change; it remains responsible for updating job statuses consumed by the new read APIs.
- Infra/DB: yes; reads from the operational `jobs` table and must preserve tenant isolation.

## Impact

- Backend jobs API, schemas, and database access.
- Frontend may consume the new APIs in a later HU, but this HU only needs the backend contract unless implementation chooses otherwise.
- No change to job creation semantics.

## Risks / Unknowns

- Job result payloads may vary by processor output; schema should expose them without overfitting early.
- Tenant isolation must be preserved for job reads.
