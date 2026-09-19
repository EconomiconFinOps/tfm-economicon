JUP: JUP-076
Trello: https://trello.com/c/2EuI8tsV

## Why

JUP-073 through JUP-075 established a versioned Azure Cost Management HTTP
contract and a deterministic simulator, but Economicon's processor cannot
ingest costs until it has an independent configurable client that follows
continuations, handles bounded retries and validates responses securely.

## What Changes

- Add a processor-side Azure Cost Management client using configurable base
  URL, bearer, API version, timeout, retry policy and pagination limits.
- Retrieve all contractual pages, normalize positional rows into named values
  and validate column stability, types, finite costs and continuation safety.
- Retry deterministic `429`/`500` responses using bounded `Retry-After` or
  exponential backoff; classify authentication, timeout and malformed data.
- Prevent bearer exposure through cross-origin/cross-path continuations, HTTP
  redirects, invalid configuration, response errors and structured logs.
- Wire the processor to the simulator through Compose environment and healthy
  service dependencies, preserving future endpoint configurability.
- Add client tests, remote smoke validation, architecture documentation,
  Docker build-context protection and OpenSpec traceability.

## Capabilities

### New Capabilities

- `azure-cost-ingestion-client`: Configurable, paginated and defensive HTTP
  consumption of the approved Azure Cost Management Query contract.

### Modified Capabilities

- None. Existing processor embeddings, frontend/backend behavior and the
  simulated Azure service remain unchanged.

## Impact

- Affected areas: processor HTTP clients/configuration/tests, Docker Compose,
  environment examples, architecture, evidence and smoke scripts.
- Downstream consumers: JUP-077 normalization, persistence and end-to-end
  ingestion workflow.
- No Azure tenant, real Microsoft Entra authentication, dataset rewriting,
  storage migration or end-to-end persistence is introduced.
