JUP: JUP-031
Trello: https://trello.com/c/uV9ywMry

## Why

Finance needs an explicit, testable estimate of future Azure spend by subscription,
service or project. Existing billing totals and tool run rate do not evaluate prediction error.

## What Changes

- Add an authenticated, tenant-scoped monthly forecasting API using completed ingestions.
- Compare last-month reference and linear trend on three temporal holdouts.
- Report empirical uncertainty, currency, missing history and source limitations explicitly.
- Provide synthetic arithmetic, HTTP and opt-in real CockroachDB tests and reproducible evidence.

## Capabilities

### New Capabilities

- `azure-spend-forecast`: monthly estimates, baseline evaluation and data sufficiency.

### Modified Capabilities

None. Anomaly detection JUP-030, run rate tools, budgets, ingestion and frontend are unchanged.

## Impact

Backend read-only endpoint, one SQL reader, pure Decimal service, schemas and documentation.
No migration, new dependency, Azure request, model-provider call or persisted prediction.
Roles remain those assigned in Trello; technical contribution does not certify human pairing,
review or acceptance. Source card verified via official DockerServer integration on 2026-10-10.
