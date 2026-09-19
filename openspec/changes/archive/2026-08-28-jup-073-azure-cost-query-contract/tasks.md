## 1. Define The Azure-Compatible Contract

- [x] 1.1 Document the subscription-scoped Cost Management Query endpoint, fixed API version, request validation, supported responses and simulated bearer authentication.
- [x] 1.2 Define actual-cost aggregation, date ranges, nine Azure dimensions, four supported tags, grouping and ordered response columns/rows.
- [x] 1.3 Specify deterministic opaque-token pagination, empty results and Azure-shaped error responses.

## 2. Connect The Public Dataset And Architecture

- [x] 2.1 Map every contractual metric, dimension, tag and system column to the canonical JUP-072 public actual-cost fixture.
- [x] 2.2 Publish 11 reusable contract scenarios covering successful queries, filtering, pagination and error behavior.
- [x] 2.3 Record and accept ADR-0001 for an independent fake Azure Cost Management service without real Azure credentials.

## 3. Verify And Deliver

- [x] 3.1 Add tests covering the fixed API version, custom timeframe conditions, mapping integrity, known subscription, simulated authentication and pagination.
- [x] 3.2 Validate OpenAPI, strict OpenSpec, JUP traceability, public dataset tests, repository hygiene and existing project build/tests.
- [x] 3.3 Publish `docs/JUP-073-azure-cost-query-contract` as a pull request targeting `develop`.
