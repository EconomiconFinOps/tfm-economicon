## ADDED Requirements

### Requirement: Simulated Azure Cost API starts only with valid versioned artifacts

The service SHALL load the JUP-072 canonical fixture, JUP-073 source mapping and JUP-073 OpenAPI contract during FastAPI startup and SHALL fail startup when required artifacts are unreadable, invalid or version-incompatible.

#### Scenario: Valid public fixture initializes the service

- **WHEN** the service starts with the versioned `EA-Cost-Actual.sample.csv`, mapping and OpenAPI
- **THEN** health reports 50 loaded rows, four subscriptions and the canonical fixture name.

#### Scenario: Fixture is missing required contract columns

- **WHEN** startup receives a CSV without every mapped source column
- **THEN** initialization fails with a configuration error and the query endpoint never becomes ready.

#### Scenario: Contract API version drifts from implementation

- **WHEN** the OpenAPI extension identifies an API version other than `2025-03-01`
- **THEN** initialization fails instead of serving behavior under a mismatched contract.

### Requirement: Normal query requests implement the JUP-073 subset strictly

The service SHALL accept the supported subscription-scoped actual-cost query model and SHALL reject undeclared request fields, invalid enums, missing custom time periods and unsupported dimensions/tags as `400 BadRequest`.

#### Scenario: Request contains an undeclared field

- **WHEN** a query body adds a property absent from the OpenAPI schema at the root or nested dataset level
- **THEN** the service returns `400` with Azure-shaped error code `BadRequest`.

#### Scenario: Unsupported API version is supplied

- **WHEN** a caller sends any `api-version` other than `2025-03-01`
- **THEN** the service returns `400 BadRequest` without querying fixture records.

#### Scenario: Subscription is absent from the public fixture

- **WHEN** a valid request targets an unknown subscription ID
- **THEN** the service returns `404 SubscriptionNotFound`.

### Requirement: Query results aggregate public costs deterministically

The service SHALL filter, group and sum the original public fixture records according to JUP-073 while preserving negative and zero amounts during `Decimal` aggregation.

#### Scenario: Actual costs are grouped daily

- **WHEN** a valid custom query groups a known subscription by resource group with daily granularity
- **THEN** response rows follow `PreTaxCost`, `ResourceGroup`, `UsageDate`, `Currency` column order and every row has matching arity.

#### Scenario: Query requests total subscription cost

- **WHEN** a valid custom query uses no grouping and no daily granularity
- **THEN** its single total equals an independent sum of all matching public `CostInBillingCurrency` values, including negative and zero records.

#### Scenario: Relative timeframe uses the fixture clock

- **WHEN** the caller uses `MonthToDate` or `TheLastMonth`
- **THEN** boundaries are deterministic relative to the maximum date in the fixture rather than the host clock.

#### Scenario: Valid query returns no matching records

- **WHEN** filters or dates select no public records
- **THEN** the service returns `200`, the contractual columns, `rows: []` and `nextLink: null`.

### Requirement: Filtering and grouping follow the public mapping

The service SHALL support recursive `and`/`or` expressions, case-insensitive `In` comparisons and up to two versioned dimension/tag groupings while preserving source spelling in output.

#### Scenario: Nested dimension and tag filter matches public records

- **WHEN** a query combines a case-insensitive service dimension with nested tag alternatives
- **THEN** only matching records contribute to the deterministic aggregate.

#### Scenario: Two groupings are requested

- **WHEN** a query groups by one supported dimension and one supported tag
- **THEN** their response columns retain request order before `UsageDate` and `Currency`.

### Requirement: JUP-074 exposes operations endpoints and reserves later resilience

The service SHALL expose `/health` and the exact contractual `/openapi.json`, return `nextLink: null` for normal responses and reject supplied `$skiptoken` until JUP-075 implements pagination.

#### Scenario: Caller inspects the contractual OpenAPI

- **WHEN** `/openapi.json` is requested after successful startup
- **THEN** the response equals the versioned JUP-073 OpenAPI artifact.

#### Scenario: Caller supplies a skip token before JUP-075

- **WHEN** `$skiptoken` is supplied to JUP-074
- **THEN** the service returns an explicit `400 BadRequest` rather than pretending pagination is supported.

### Requirement: Service runs as an isolated healthchecked container

The project SHALL provide a Docker image and Compose service running the simulator on container port 8002 without root privileges or a writable root filesystem.

#### Scenario: Compose service becomes healthy

- **WHEN** the `azure-cost-api` service is built and started
- **THEN** its healthcheck reaches `/health`, it runs as UID 10001, its root filesystem is read-only and a contractual query succeeds.
