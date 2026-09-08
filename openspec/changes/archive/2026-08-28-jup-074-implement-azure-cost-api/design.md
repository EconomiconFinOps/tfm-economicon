JUP: JUP-074
ADR: docs/adr/ADR-0001-azure-cost-api-simulation.md

## Context

JUP-072 integrated 11 deterministic public Microsoft Azure fixtures and selected `EA-Cost-Actual.sample.csv` as the canonical actual-cost source. JUP-073 accepted ADR-0001 and versioned an OpenAPI 3.1 query contract, source mapping and 11 reusable scenarios. JUP-074 implements only the contract's normal service behavior; later tasks own pagination, configured failures and ingestion.

## Goals / Non-Goals

**Goals:**

- Run an independent FastAPI service on port 8002 with health and contractual OpenAPI endpoints.
- Validate and load all 50 canonical fixture rows in memory without transforming public values.
- Implement supported subscription scope, timeframes, aggregation, grouping, filtering, output ordering and Azure-shaped errors.
- Keep results deterministic and validate implementation/contract API-version alignment at startup.
- Run in a non-root, healthchecked Docker container with a read-only Compose filesystem.

**Non-Goals:**

- Calling a real Azure endpoint, validating Entra ID or representing access to an Azure tenant.
- Implementing `$skiptoken` pagination, simulated bearer enforcement, `429`/timeout failures or corrupted data modes; these belong to JUP-075.
- Persisting cost rows, wiring the processor ingestion client or executing the full database flow; these belong to JUP-076/JUP-077.
- Modifying or anonymizing Microsoft's public fixture values.

## Decisions

### Load the canonical fixture and contract during FastAPI lifespan

The service constructs an immutable in-memory repository during startup. It rejects missing required columns, invalid dates/costs, empty fixtures, unreadable mappings and OpenAPI version/operation drift. Health only becomes available after all required artifacts load successfully.

### Use strict Pydantic models for the accepted subset

Request models forbid fields not declared by JUP-073 and validate timezone-aware custom intervals, supported enum values, one/two aggregations, at most two groupings and recursive filters. FastAPI validation errors are normalized to `400 BadRequest` rather than exposing framework details.

### Aggregate Decimal costs before JSON conversion

Repository records retain exact `Decimal` costs, original dimension spelling and parsed public tag values. The engine filters case-insensitively, groups deterministically, sums negative/zero/positive values exactly and converts only final totals to JSON numbers.

### Reserve pagination and fake authentication explicitly

Normal responses always return `nextLink: null`. Supplying `$skiptoken` returns a clear `400` until JUP-075 implements the contract's opaque pagination. No real or simulated bearer is enforced in JUP-074, consistent with the optional JUP-073 security mode and the JUP-075 allocation.

### Isolate the service in Docker without root privileges

The image contains only the service, contractual OpenAPI/mapping and canonical fixture. A root `.dockerignore` excludes credentials, local dependencies, caches and full ZIP archives from the build context. The image runs as UID 10001 and defines its own healthcheck. Compose applies `read_only`, a temporary `/tmp` filesystem and `no-new-privileges` while exposing configurable host port 8002.

## Risks / Trade-offs

- [The public fixture or mapping changes] -> Fail startup on missing/invalid fields and cover mapping/row integrity in repository and JUP-072/JUP-073 tests.
- [Runtime behavior diverges from OpenAPI] -> Load the exact versioned contract, verify API version/operation at startup and execute shared contract cases.
- [Floating-point conversion changes exact display] -> Sum with `Decimal` and convert only final response numbers; assert aggregate results against independent fixture sums.
- [Clients assume pagination is already implemented] -> Reject `$skiptoken` explicitly and document JUP-075 ownership.
- [Container writes unexpected state or executes as root] -> Use an unprivileged image user, read-only Compose filesystem and no-new-privileges.
