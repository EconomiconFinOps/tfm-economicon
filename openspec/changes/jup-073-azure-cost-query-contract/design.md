JUP: JUP-073
ADR: docs/adr/ADR-0001-azure-cost-api-simulation.md

## Context

JUP-072 integrated Microsoft FinOps Toolkit v14 public Azure cost fixtures into `develop`, including the canonical `EA-Cost-Actual.sample.csv` dataset. Economicon has no Azure tenant and cannot validate its ingestion pipeline against live Azure. JUP-073 therefore fixes a bounded, versioned HTTP contract shared by the simulated Azure API and its future ingestion client.

## Goals / Non-Goals

**Goals:**

- Define the subscription-scoped Azure Cost Management Query route, fixed API version, request shape and ordered response columns/rows.
- Map supported cost metrics, dimensions and tags directly to the canonical public fixture.
- Specify deterministic aggregation, filtering, grouping, pagination, optional fake bearer authentication and machine-readable error responses.
- Provide reusable contract cases and tests independently of a live Azure tenant.
- Record the durable standalone simulator boundary in ADR-0001.

**Non-Goals:**

- Implementing the fake API service, persistent ingestion, retries or end-to-end infrastructure in this documentation change.
- Emulating billing-account, management-group, resource-group or amortized-cost query scopes.
- Validating Microsoft Entra ID tokens, OAuth permissions, Azure tenancy or a real Azure endpoint.
- Redacting or anonymizing the public Microsoft sample values already approved in JUP-072.

## Decisions

### Pin one subscription-scoped Azure query operation

The OpenAPI 3.1 artifact defines `POST /subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query` with required `api-version=2025-03-01`. The response statuses are `200`, `400`, `401` and `404`. Request bodies accept only the documented actual-cost subset, and a JSON Schema condition requires `timePeriod` whenever `timeframe` is `Custom`.

### Map contractual values to the canonical public actual-cost fixture

`docs/api/azure-cost-query-mapping.json` translates `PreTaxCost`, supported Azure dimensions, tags, `UsageDate` and `Currency` to the integrated `EA-Cost-Actual.sample.csv` columns. Public source values remain unchanged, including the known subscription identifier and negative/zero costs. Contract tests reject mappings whose source columns are absent from the fixture.

### Keep transport behavior deterministic and Azure-shaped

The simulator contract exposes ordered `columns` and positional `rows`, case-insensitive dimension/tag filters, optional fake bearer authentication and Azure-shaped error objects. Pagination uses an opaque `$skiptoken` linked to request content, subscription and dataset checksum; `nextLink` is `null` on the last page.

### Preserve producer/consumer independence through reusable contract cases

Eleven versioned scenarios cover aggregation, grouping, dimension filters, tag filters, intermediate/last pages, empty results, invalid scope, unsupported versions, invalid tokens and missing fake authentication. Both the later simulator and ingestion client can consume these cases without direct knowledge of the dataset internals.

### Record the simulator as an independent service boundary

ADR-0001 accepts an independent `apps/azure-cost-api` service for JUP-074. This preserves realistic HTTP behavior while allowing the future client to switch its base URL to Azure configuration later. It does not claim compatibility beyond the explicitly documented subset or access to a real Azure tenant.

## Risks / Trade-offs

- [The official Azure API evolves beyond the chosen subset] -> Pin `2025-03-01` and update OpenAPI, mappings, cases and tests together when the supported contract changes.
- [Fixture schema drift silently breaks ingestion] -> Verify all mapped columns and the known subscription against the JUP-072 canonical fixture in automated tests.
- [Producer and consumer diverge on pagination or errors] -> Version opaque-token expectations, `nextLink` semantics, response schemas and reusable contract cases.
- [A simulated token is confused with real Azure authentication] -> Document that bearer validation is local and does not validate Entra ID, tenants or OAuth scopes.
- [A custom timeframe omits date boundaries] -> Express the conditional `timePeriod` requirement directly in the OpenAPI 3.1 schema and verify it in contract tests.
