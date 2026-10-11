JUP: JUP-017
Trello: https://trello.com/c/3wiy5PJS

## Why

Users cannot measure the share of observed Azure spend that satisfies a minimum
tag policy. The public Microsoft dataset has no row containing all five proposed
tags; any-tag presence is not compliance.

## Authorization

On 2026-10-03 the user approved the proposal in chat
`01a0fe4f-8e84-7133-944a-096ec42fd236`: “Paris esta saturado de trabajo da por
buena tu propuesta y continua con la tarea”. This removes the need to wait for
Paris's taxonomy definition before implementation. It is the user's approval,
not approval attributed to Paris. JUP-015 remains separate and is not completed
by this change. Review and validation still follow CONTRIBUTING.md.

## What Changes

- Add a read-only, tenant-authorized /billing/tag-coverage endpoint.
- Evaluate owner, environment, application, cost_center and project using the
  documented version-1 rules; return per-currency spend coverage and signed
  negative adjustments, with N/D when there are no positive charges.
- Add an expandable coverage panel to the existing executive cost dashboard.
- Add explicit synthetic positive/negative controls without altering public CSVs.

## Capabilities

### New Capabilities

- `tagged-cost-coverage`: minimum-policy compliance weighted by positive cost.

### Modified Capabilities

None. The /billing/summary v2 contract is unchanged.

## Impact

Backend query/schema/routes, frontend API/coverage panel and tests; no migration,
new dependency, ingestion overwrite or external provider call.

ADR: [ADR-0013](../../../../docs/adr/ADR-0013-tagged-cost-coverage.md).
