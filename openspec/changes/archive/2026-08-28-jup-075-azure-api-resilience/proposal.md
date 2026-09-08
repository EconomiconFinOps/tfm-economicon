JUP: JUP-075
Trello: https://trello.com/c/tIJgZo6y

## Why

The JUP-074 Azure Cost Management simulator already reproduces successful
queries over Microsoft's public fixture, but downstream ingestion cannot verify
continuation handling, access failures, retry behavior, timeouts or malformed
responses until those transport conditions are deterministic and reproducible.

## What Changes

- Require configurable local bearer authentication by default and return
  Azure-shaped `401 AuthenticationFailed` and `403 AuthorizationFailed` errors.
- Paginate normal query results using signed opaque `$skiptoken` continuations
  bound to the subscription, canonical request and public dataset checksum.
- Support deterministic `rate-limit`, `server-error`, `timeout`, `empty-page`
  and `invalid-data` scenarios through a request header or default setting.
- Extend the shared OpenAPI contract, reusable contract cases, Compose
  configuration, automated tests and external Docker smoke verification.
- Preserve JUP-074 strict request validation, contract startup checks,
  non-root execution, read-only filesystem and original public fixture values.

## Capabilities

### New Capabilities

- `simulated-azure-api-resilience`: Deterministic simulated authentication,
  signed pagination and controlled transport/data failures for ingestion tests.

### Modified Capabilities

- None. JUP-074's normal query operation keeps its contractual column and row
  shape; JUP-076 owns the downstream ingestion client.

## Impact

- Affected areas: `apps/azure-cost-api`, shared OpenAPI/contract cases, Docker
  Compose, root environment examples, evidence and external smoke scripts.
- Downstream consumers: JUP-076 resilient ingestion client and JUP-077
  end-to-end integration tests.
- No Azure tenant, Microsoft Entra authentication, real cloud credentials,
  fixture anonymization or external runtime cloud dependency is introduced.
