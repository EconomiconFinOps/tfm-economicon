JUP: JUP-033
Trello: https://trello.com/c/ndrittYl

## Why

Users need actionable next steps supported by their observed costs and business
context. The stored billing data can identify missing project attribution and
projects worth investigating, but it cannot demonstrate resource waste or an
achievable saving. A reproducible recommendation contract must preserve that
distinction before estimates, assistant answers or a frontend consume it.

## What Changes

- Add authenticated GET /billing/recommendations for an explicit UTC date
  interval of at most 366 days and the active tenant.
- Reuse the existing billing summary grouped by project to propose fixing
  missing attribution and investigating the highest positive named-project
  cost in each currency.
- Distinguish a supported tagging recommendation from an investigation
  candidate; include evidence, assumptions, limitations and unevaluated rules.
- Return a versioned, deterministic contract with at most 50 recommendations,
  explicit truncation and null savings fields.
- Document the consumer boundary for JUP-034, JUP-039 and JUP-058 and provide
  calculation and HTTP acceptance tests.

This delivery does not infer utilization, recommend rightsizing, shutdown or
reservations, estimate savings, persist recommendations, invoke an LLM or change
cloud resources. Data comes from stored simulated Azure ingestions, not a live
Azure assessment. Consumer integration and independent human acceptance remain
separate pending checks.

## Capabilities

### New Capabilities

- `optimization-recommendations`: Evidence-backed proposals over tenant billing
  data, with explicit applicability and missing-input boundaries.

### Modified Capabilities

None. The billing summary and its existing source-ambiguity behavior are reused
without changing their contract.

## Impact

Backend billing route, recommendation schemas/service/tests and focused API,
verification and continuity documentation. No new database schema, SQL reader,
cloud permission, processor or frontend dependency is required.

The card retains P1 priority and its assigned roles: Alejandro Aguado leadership,
Lucia Mateo pairing, Paris Arcos Martin PR review and Victor Mendez validation,
tests and documentation. These are assignments, not evidence of participation.
The card's generic acceptance criteria require functional evidence, necessary
tests, updated documentation, a reviewed linked PR and independent validation;
this proposal does not mark any of them accepted.
