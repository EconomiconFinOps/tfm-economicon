# simulated-azure-api-resilience Specification

## Purpose
TBD - created by archiving change jup-075-azure-api-resilience. Update Purpose after archive.
## Requirements
### Requirement: Simulated identities authenticate locally

The query service SHALL require a configurable local bearer token by default,
distinguish explicitly forbidden identities, never validate a real Microsoft
Entra identity and keep operational endpoints publicly readable.

#### Scenario: Allowed simulated identity queries public costs

- **WHEN** a valid contractual query includes a configured allowed bearer token
- **THEN** the service returns `200` with deterministic public fixture costs.

#### Scenario: Missing or unknown identity requests costs

- **WHEN** authentication is enabled and a query omits its bearer or sends an
  unknown token
- **THEN** the service returns `401 AuthenticationFailed` with
  `WWW-Authenticate: Bearer` and does not expose configured token values.

#### Scenario: Explicitly forbidden identity requests costs

- **WHEN** a query includes a configured forbidden bearer token
- **THEN** the service returns `403 AuthorizationFailed`.

#### Scenario: Operational endpoints remain available

- **WHEN** an unauthenticated caller requests `/health` or `/openapi.json`
- **THEN** the service returns the operational status or exact pinned contract.

### Requirement: Continuation pages are signed and query-bound

The service SHALL divide ordered rows into configurable fixed-size pages and
generate opaque HMAC-signed `$skiptoken` links bound to the canonical request,
subscription and public fixture checksum.

#### Scenario: Caller follows all continuation links

- **WHEN** the caller resubmits the identical contractual body for every
  generated `nextLink`
- **THEN** every original row is returned once, intermediate pages respect the
  configured size and the last page sets `nextLink: null`.

#### Scenario: Caller manipulates or reuses a continuation

- **WHEN** a continuation signature changes or the same token is used with
  another body, subscription, signing secret or dataset checksum
- **THEN** the service returns `400 InvalidSkipToken` without exposing internals.

#### Scenario: Query has no matching public rows

- **WHEN** an authorized contractual query has no matching fixture rows
- **THEN** the service returns `200`, `rows: []` and `nextLink: null`.

### Requirement: Failure scenarios are explicitly reproducible

The service SHALL select exactly one deterministic resilience scenario from
`X-Fake-Azure-Scenario` or configured default settings without random failures.

#### Scenario: Rate limiting is requested

- **WHEN** the caller selects `rate-limit`
- **THEN** the service returns `429 TooManyRequests` with configured
  `Retry-After` seconds.

#### Scenario: Internal failure is requested

- **WHEN** the caller selects `server-error`
- **THEN** the service returns `500 InternalServerError` using the Azure error
  shape.

#### Scenario: Timeout simulation is requested

- **WHEN** the caller selects `timeout`
- **THEN** the service waits for the bounded configured interval and returns
  the otherwise successful contractual response.

#### Scenario: Empty continuation page is requested

- **WHEN** the caller selects `empty-page` for an intermediate result page
- **THEN** the response contains no rows while preserving its signed
  continuation link.

#### Scenario: Invalid cost data is requested

- **WHEN** the caller selects `invalid-data`
- **THEN** the first positional cost cell is non-numeric while the original
  public fixture remains unchanged.

#### Scenario: Request selects an unsupported failure mode

- **WHEN** the scenario header contains an unsupported value
- **THEN** the service returns Azure-shaped `400 BadRequest`.

### Requirement: Existing simulator hardening remains enforced

The service SHALL preserve strict JUP-074 request validation, versioned
contract startup validation, healthchecks, unprivileged container execution,
read-only root filesystem and `no-new-privileges`.

#### Scenario: Resilient simulator starts inside Docker

- **WHEN** the configured service is built and launched on `dockerserver`
- **THEN** its healthcheck reports 50 public rows and four subscriptions while
  the container runs without root privileges or a writable root filesystem.
