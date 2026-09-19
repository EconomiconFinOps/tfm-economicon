## 1. Implement Configurable Contract Consumption

- [x] 1.1 Add processor settings for validated endpoint, masked bearer, API
  version, request timeout, bounded retry policy and page limit.
- [x] 1.2 Implement injectable HTTP transport and Azure Cost Query requests
  with configurable subscription scope and deterministic body serialization.
- [x] 1.3 Follow contractual absolute/relative continuations while enforcing
  exact origin, subscription route and API version without redirects.

## 2. Validate Responses And Failures

- [x] 2.1 Normalize positional columns/rows and reject missing, duplicate,
  unstable, incorrectly typed or non-finite contractual cost values.
- [x] 2.2 Implement bounded `429`/`500` retries, safe `Retry-After`, explicit
  timeout/authentication errors, cycle limits and empty-page detection.
- [x] 2.3 Emit structured counters and retry events without tokens, request
  bodies, query strings or raw Azure cost values.

## 3. Document, Verify And Integrate

- [x] 3.1 Wire processor Compose configuration and simulator health dependency
  while excluding local secrets/dependencies from its Docker context.
- [x] 3.2 Validate processor, simulator, shared-contract, OpenSpec and
  workspace suites plus real Docker ingestion smoke on `dockerserver`.
- [x] 3.3 Publish `feat/JUP-076-azure-cost-ingestion-client` as a pull request
  targeting `develop` and link its Trello evidence.
