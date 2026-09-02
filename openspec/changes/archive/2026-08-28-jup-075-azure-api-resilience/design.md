JUP: JUP-075
ADR: docs/adr/ADR-0001-azure-cost-api-simulation.md

## Context

JUP-074 integrated an isolated FastAPI Azure Cost Management simulator backed
by the public JUP-072 fixture and versioned JUP-073 contract. JUP-075 extends
that existing HTTP boundary with predictable resilience behaviors that future
ingestion clients can test without an Azure tenant.

## Goals / Non-Goals

**Goals:**

- Enforce configurable fake bearer identities and distinguish unauthenticated
  callers from explicitly forbidden identities.
- Return stable fixed-size pages with signed continuations bound to request,
  subscription and dataset content.
- Produce configurable `429`, `500`, delayed success, empty continuation pages
  and non-numeric costs deterministically.
- Keep contract artifacts, automated tests, Docker hardening and OpenSpec
  traceability synchronized with the implementation.

**Non-Goals:**

- Validate real Microsoft Entra tokens, call Azure APIs or require a tenant.
- Build retry, persistence, observability or ingestion-client logic; those
  responsibilities belong to JUP-076 and JUP-077.
- Rewrite, anonymize or otherwise alter Microsoft's public sample data.
- Change existing frontend, backend or processor runtime behavior.

## Decisions

### Authenticate exclusively against configured local fixture tokens

The simulator enables fake bearer authentication by default. Constant-time
token comparisons classify configured allowed identities as successful,
explicitly forbidden identities as `403`, and absent/unknown identities as
`401` with `WWW-Authenticate: Bearer`. `/health` and `/openapi.json` remain
public operational endpoints. Local settings can disable authentication for
isolated compatibility tests; this never grants access to Azure.

### Bind opaque continuation tokens to canonical request and fixture content

Pagination derives a SHA-256 fingerprint from normalized subscription scope,
the canonical validated request and the public fixture's SHA-256 checksum.
Each opaque token contains a versioned offset and fingerprint protected by
HMAC-SHA256. Changed bodies, subscriptions, dataset contents or signatures
return `400 InvalidSkipToken`. The next link retains route and `api-version`;
the final page sets `nextLink: null`.

### Select every failure explicitly through configuration or request header

`X-Fake-Azure-Scenario` overrides the configured default without randomness.
`rate-limit` returns `429` and configured `Retry-After`; `server-error`
returns `500`; `timeout` awaits a bounded configurable delay. `empty-page`
removes rows while retaining the generated continuation; `invalid-data`
replaces the first cost with a non-numeric fixture value. Unsupported scenario
names return Azure-shaped `400 BadRequest` responses.

### Preserve the already integrated JUP-074 security boundary

The service continues validating the pinned OpenAPI operation/version during
startup, rejecting undeclared request fields and running as UID 10001 inside a
healthchecked, read-only, `no-new-privileges` Docker container. The root
`.dockerignore` continues excluding credentials and generated dependencies.

## Risks / Trade-offs

- [A client reuses a continuation for another request] -> Sign and fingerprint
  subscription, canonical body and dataset checksum; cover rejection in tests.
- [Fake tokens are mistaken for Azure credentials] -> Document local-only
  defaults and never contact Microsoft Entra or an external tenant.
- [Random failures make tests flaky] -> Select each scenario explicitly and
  bound timeout/retry configuration.
- [Resilience changes regress JUP-074 hardening] -> Preserve strict startup,
  request, Docker, workspace and shared-contract regression suites.
- [Contract and simulator diverge] -> Extend OpenAPI, shared cases and contract
  tests together and validate the exact served artifact.
