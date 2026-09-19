JUP: JUP-073
Trello: https://trello.com/c/ll3GzmuN

## Why

Economicon needs a shared Azure Cost Management Query contract before implementing its simulated Azure API and ingestion client. The team has no real Azure tenant, so both producer and consumer must agree on a documented, testable subset backed by the public Microsoft dataset integrated in JUP-072.

## What Changes

- Define an OpenAPI 3.1 contract for the Azure subscription-scoped Cost Management Query endpoint using `api-version=2025-03-01`.
- Specify request validation, fixed actual-cost aggregation, supported dimensions/tags, date ranges, grouping, deterministic pagination and simulated bearer authentication.
- Map contractual metrics and dimensions to the canonical `EA-Cost-Actual.sample.csv` fixture without transforming Microsoft's public source values.
- Provide 11 reusable success, pagination, empty-result and error contract cases for downstream fake API and ingestion tests.
- Accept ADR-0001 for an independent simulated Azure Cost Management service without a real Azure tenant.
- Add automated checks for OpenAPI structure, conditional custom time periods, public fixture mappings, known subscriptions, authentication and pagination.

## Capabilities

### New Capabilities

- `azure-cost-query-contract`: Versioned, Azure-compatible HTTP and data contracts define the simulated Cost Management API consumed by downstream Economicon services.

### Modified Capabilities

- None. The existing frontend, backend, processor and JUP-072 dataset runtime behavior is unchanged.

## Impact

- Affected areas: API contract documentation, OpenAPI schemas, dataset mappings, reusable contract cases, ADR-0001 and standalone contract tests.
- Downstream consumers: JUP-074 simulated Azure API, JUP-075 resilience modes, JUP-076 ingestion client and JUP-077 end-to-end tests.
- No real Azure credentials, tenant connection, external cloud service or runtime product code change is required.
