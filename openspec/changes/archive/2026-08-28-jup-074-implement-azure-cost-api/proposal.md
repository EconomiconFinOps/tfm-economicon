JUP: JUP-074
Trello: https://trello.com/c/g94u3J8S

## Why

Economicon must exercise a realistic Azure Cost Management HTTP integration without a real Azure tenant. JUP-072 supplies a reproducible public Microsoft dataset and JUP-073 defines the shared query contract; JUP-074 must implement the normal request/response path as an independently runnable service before resilience and ingestion work can proceed.

## What Changes

- Add an independent FastAPI service in `apps/azure-cost-api` implementing the subscription-scoped JUP-073 query route.
- Load and validate the canonical JUP-072 `EA-Cost-Actual.sample.csv` fixture and its machine-readable mapping at startup.
- Implement actual-cost aggregation, custom and relative date ranges, recursive dimension/tag filters, up to two groupings and ordered Azure-shaped columns/rows.
- Return deterministic query identifiers, empty results and Azure-shaped `400`/`404` errors while reserving pagination and simulated authentication for JUP-075.
- Serve the versioned contractual OpenAPI and fail startup when its API version or operation differs from the implementation.
- Add local/Docker execution, healthchecks, a non-root container, a safe minimal Docker build context and Compose hardening.
- Add implementation, repository, configuration and API tests linked to the versioned JUP-073 contract cases.

## Capabilities

### New Capabilities

- `simulated-azure-cost-api`: A deterministic local HTTP service implements the normal Azure Cost Management Query subset over the approved public dataset.

### Modified Capabilities

- None. Existing frontend, backend, processor, data fixtures and their runtime behavior remain unchanged.

## Impact

- Affected areas: new `apps/azure-cost-api` workspace, root Docker Compose and environment examples, architecture documentation, JUP-074 evidence and tests.
- Downstream consumers: JUP-075 simulator resilience, JUP-076 ingestion client and JUP-077 end-to-end flow.
- No live Azure tenant, Azure credentials, production data, database schema or external runtime cloud dependency is introduced.
