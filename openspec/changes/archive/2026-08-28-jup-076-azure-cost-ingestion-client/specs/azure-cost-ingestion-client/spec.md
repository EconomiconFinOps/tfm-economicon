## ADDED Requirements

### Requirement: Azure query endpoint is entirely configurable

The processor SHALL consume the approved Azure Cost Management Query contract
using configurable HTTP(S) base URL, masked bearer, API version, subscription,
timeout, retry limits and pagination bounds without reading the source CSV.

#### Scenario: Configured simulator returns public cost rows

- **WHEN** the client sends a contractual request to the configured simulator
  with its allowed local bearer
- **THEN** it receives named cost rows and stable contractual column metadata.

#### Scenario: Future provider endpoint changes

- **WHEN** the environment replaces simulator URL and bearer with another
  compatible Azure Cost Query endpoint
- **THEN** the same client and downstream pipeline operate without code or
  fixture changes.

#### Scenario: Unsafe operational settings are provided

- **WHEN** configuration contains credential-bearing/query/fragment URLs,
  invalid ports, empty/injected bearers or unbounded timeout/retry/page values
- **THEN** settings validation rejects the configuration before transport.

### Requirement: Pagination never exposes credentials

The client SHALL follow every absolute or relative contractual continuation
while keeping the same origin, subscription route, single fixed API version,
request body and configured bearer; HTTP redirects SHALL NOT be followed.

#### Scenario: Multiple valid pages are returned

- **WHEN** the simulator produces three contractual pages of ten public rows
- **THEN** the client returns all 30 rows once, reports three pages and sends
  the same body for each request.

#### Scenario: Continuation targets an untrusted endpoint

- **WHEN** `nextLink` changes scheme, authority, subscription path, API
  version or includes a fragment
- **THEN** the client rejects it before issuing another authenticated request.

#### Scenario: Remote endpoint responds with a redirect

- **WHEN** an authenticated query receives an HTTP redirect
- **THEN** the transport does not follow the destination or forward the bearer.

#### Scenario: Pagination repeats or exceeds configured bounds

- **WHEN** a continuation forms a cycle or requests more than the page limit
- **THEN** the client fails with a safe actionable pagination error.

### Requirement: Transient failures use bounded retries

The client SHALL retry only `429 TooManyRequests` and `500
InternalServerError`, honor bounded finite `Retry-After`, apply exponential
fallback and fail explicitly on timeout or non-retryable authentication errors.

#### Scenario: Throttled request succeeds after one retry

- **WHEN** the first attempt returns `429` with a valid `Retry-After` and the
  second attempt succeeds
- **THEN** the client waits no longer than its configured ceiling, returns the
  public rows and reports exactly one retry.

#### Scenario: Server-error retries are exhausted

- **WHEN** repeated `500` responses exceed the configured retry allowance
- **THEN** the client raises an Azure-shaped HTTP error without leaking bearer
  values or request bodies.

#### Scenario: Retry header is malformed or non-finite

- **WHEN** `Retry-After` contains non-numeric, `NaN` or infinite data
- **THEN** the client uses bounded configured backoff instead of an unsafe
  sleep duration.

#### Scenario: Authentication or timeout fails

- **WHEN** the service returns `401`/`403` or exceeds the configured timeout
- **THEN** the client fails without silently retrying or exposing credentials.

### Requirement: Contractual columns and rows remain trustworthy

The client SHALL require stable unique positional columns, mandatory numeric
finite `PreTaxCost`, string `Currency`, matching row arity and explicit
`nextLink` semantics on every page.

#### Scenario: Final result contains no rows

- **WHEN** a valid response contains no matching rows and `nextLink: null`
- **THEN** the client returns an empty successful result.

#### Scenario: Intermediate page contains no rows

- **WHEN** a response returns an empty page with a continuation
- **THEN** the client raises a dedicated empty-page anomaly.

#### Scenario: Remote response violates cost semantics

- **WHEN** columns change between pages, required types are incorrect or costs
  are non-numeric/non-finite
- **THEN** the client rejects the response before downstream persistence.

### Requirement: Observability excludes secrets and public row contents

The client SHALL emit structured request, retry, page and completion events
containing paths, counters, statuses and delays without bearer values, request
bodies, query strings, continuation tokens or raw cost rows.

#### Scenario: A paginated retry is recorded

- **WHEN** ingestion completes after a retry and multiple pages
- **THEN** logs contain only operational event fields while configured tokens
  and public response values remain absent.
