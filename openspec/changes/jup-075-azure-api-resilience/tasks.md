## 1. Add Controlled Authentication And Pagination

- [x] 1.1 Configure fake bearer identities and return Azure-shaped `401`/`403`
  responses without exposing configured tokens.
- [x] 1.2 Paginate successful queries using configurable page sizes and opaque
  HMAC-signed continuations bound to request, subscription and fixture checksum.
- [x] 1.3 Reject malformed, manipulated, cross-query and stale continuations
  while preserving complete deterministic row traversal.

## 2. Add Deterministic Failure Scenarios

- [x] 2.1 Implement explicit rate-limit, server-error and bounded timeout
  scenarios with contractual error bodies and response headers.
- [x] 2.2 Implement empty-page and invalid-data scenarios for ingestion-client
  robustness without modifying the public fixture.
- [x] 2.3 Extend the shared OpenAPI, contract cases, environment examples,
  Compose configuration and architecture documentation.

## 3. Verify And Integrate

- [x] 3.1 Preserve all JUP-074 strict validation, contract startup checks and
  unprivileged read-only container hardening.
- [x] 3.2 Validate service, shared-contract, OpenSpec, workspace and external
  Docker smoke suites against `dockerserver`.
- [x] 3.3 Publish `feat/JUP-075-azure-api-resilience` and open a pull request
  targeting `develop` with linked Trello evidence.
