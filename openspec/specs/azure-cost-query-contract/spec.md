# azure-cost-query-contract Specification

## Purpose
TBD - created by archiving change jup-073-azure-cost-query-contract. Update Purpose after archive.
## Requirements
### Requirement: The Azure Cost Management Query operation is explicitly versioned

The project SHALL define a machine-readable OpenAPI 3.1 contract for `POST /subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query` using required query parameter `api-version=2025-03-01`.

#### Scenario: Contributor inspects the supported query route

- **WHEN** a contributor reads the versioned OpenAPI document
- **THEN** it defines exactly the documented subscription-scoped query path, the fixed `2025-03-01` API version and responses `200`, `400`, `401` and `404`.

#### Scenario: The query does not require a real Azure tenant

- **WHEN** a contributor implements or validates the documented operation
- **THEN** the contract uses an independent configurable simulator and does not require Azure credentials, a live tenant or Entra ID token validation.

### Requirement: Requests constrain actual-cost queries and custom date ranges

The contract SHALL restrict query types, timeframes, actual-cost aggregation, dimensions, tags, grouping and filters to the versioned Economicon Azure subset.

#### Scenario: Custom timeframe includes explicit boundaries

- **WHEN** a query uses `timeframe: Custom`
- **THEN** the OpenAPI schema requires `timePeriod` with `from` and `to` timestamps.

#### Scenario: Supported dimensions and tags match the documented subset

- **WHEN** a contract case groups or filters Azure dimensions or tags
- **THEN** its names are declared in the versioned fixture mapping and unsupported names are represented by a `400 BadRequest` scenario.

### Requirement: Contractual values map to the public JUP-072 actual-cost fixture

The project SHALL define a machine-readable mapping from contract metrics, dimensions, tags, dates and currency to the versioned `EA-Cost-Actual.sample.csv` fixture integrated by JUP-072.

#### Scenario: Fixture mappings remain valid

- **WHEN** automated contract checks inspect the canonical CSV header
- **THEN** every mapped source column exists and the fixture is present in the versioned JUP-072 manifest.

#### Scenario: Known subscription exists in the public dataset

- **WHEN** contract cases identify their known subscription ID
- **THEN** that original public identifier exists unchanged in the canonical CSV fixture.

### Requirement: Query responses preserve ordered data and deterministic pagination

The contract SHALL return Azure-shaped query resources containing ordered `columns`, positional `rows` and a nullable `nextLink`; subsequent pages SHALL use an opaque `$skiptoken`.

#### Scenario: Example rows match their columns

- **WHEN** a contributor inspects the successful OpenAPI response example
- **THEN** each row has exactly one value per declared column and the final column identifies `Currency`.

#### Scenario: Pagination distinguishes intermediate and final pages

- **WHEN** reusable contract cases represent intermediate and final result pages
- **THEN** intermediate pages expect a non-null `nextLink`, final pages expect `null` and invalid skip tokens yield `400 InvalidSkipToken`.

#### Scenario: Valid query has no matching data

- **WHEN** a request uses a valid date range without matching fixture records
- **THEN** its contract scenario expects `200`, zero rows and `nextLink: null`.

### Requirement: Optional simulator authentication and errors are explicit

The contract SHALL define optional local bearer-token authentication and Azure-shaped errors without claiming real Entra ID, tenant or OAuth validation.

#### Scenario: Simulated bearer authentication is enabled

- **WHEN** a request omits or supplies an incorrect configured fake bearer token
- **THEN** the contract describes `401 AuthenticationFailed` and the `WWW-Authenticate` challenge.

#### Scenario: Unsupported scope or request is rejected

- **WHEN** contract cases use an unknown subscription, unsupported API version, invalid dimension or incorrect skip token
- **THEN** they define the corresponding `404 SubscriptionNotFound`, `400 BadRequest` or `400 InvalidSkipToken` response.

### Requirement: Simulator architecture remains traceable to an accepted ADR

The decision to implement a standalone simulated Azure Cost Management service SHALL be documented in ADR-0001 and linked to JUP-073, its Trello card and its OpenSpec change.

#### Scenario: Contributor reviews the durable service-boundary decision

- **WHEN** a contributor reads ADR-0001 and the JUP-073 design
- **THEN** they identify the independent simulator boundary, the canonical public fixture, the absence of real Azure credentials and the downstream JUP-074/JUP-075/JUP-076 responsibilities.
