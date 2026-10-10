JUP: JUP-030
Trello: https://trello.com/c/ScxJi1TO

## Why

Users need reproducible candidates for investigation when observed costs reach
a configured threshold or increase against a comparable prior period. JUP-057
provides a labelled demonstration panel, while JUP-026 already supplies
tenant-scoped billing aggregates. JUP-038 needs explicit operands and rule
evidence to explain a detection without claiming a demonstrated cause.

## What Changes

- Add authenticated, stateless `POST /billing/anomalies/evaluate` over billing
  v2, scoped to the active tenant, currency and supported grouping.
- Evaluate independent absolute-cost and prior-period increase rules using
  exact decimal calculations and explicit missing/partial-data states.
- Return assessments and triggered candidates with stable identity, changing
  evidence identity, periods, counts, quality and causal limitations.
- Document a reproducible synthetic example, JUP-038 consumption boundary and
  the distinction from the existing JUP-084 daily candidate rule.
- Add focused service, input, authentication and integration-boundary tests.

## Capabilities

### New Capabilities

- `cost-anomaly-detection`: evidence-backed evaluation of configured period
  cost thresholds and increases on observed billing groups.

### Modified Capabilities

None. The JUP-057 demo and JUP-084 daily tool contract remain unchanged.

## Impact

Backend billing route, new anomaly schemas/service/tests and API documentation.
No database migration, scheduled delivery, persistence, external notification,
frontend connection, statistical model, savings estimate or causal diagnosis.
JUP-038 receives a reusable contract; its actual integration is separate.

Trello assignments remain Lucia Mateo leadership, Paris Arcos Martin pairing,
Victor Mendez PR review and Alejandro Aguado validation/tests/documentation.
This technical contribution does not certify their participation or replace
independent review and validation. The card is not claimed closed by this change.
