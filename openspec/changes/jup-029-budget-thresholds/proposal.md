JUP: JUP-029
Trello: https://trello.com/c/pBICTDDh

## Why

FinOps users need a reproducible definition of budget, period and thresholds
before adding persistence or alerts. The user requested this first increment on
2026-10-01: define those inputs and test consumption and deviations.

## What Changes

- Add a stateless authenticated POST /billing/budget/evaluate for the active
  tenant, using the existing billing summary and its source-overlap guard.
- Define one positive amount, one currency, an explicit UTC date interval and
  ordered percentage thresholds (defaults 80 and 100).
- Return observed consumption, remaining amount, signed deviation and reached
  thresholds, with exact decimal arithmetic and explicit missing/partial data.
- Add calculation and API acceptance tests and reproducible examples.

This increment does not store budgets, emit notifications, impose spending
limits, extrapolate forecasts, or add frontend/agent integration. Those remain
future scope for the parent card; this PR cannot close JUP-029 by itself.

## Impact

Backend billing route, new budget schemas/service/tests and documentation.
Existing billing v2, database schema and processor contracts remain compatible.
Roles remain those of Trello: Alejandro leadership, Lucia pairing, Paris review,
Victor validation. Assignment is not evidence of completed participation.
