## ADDED Requirements

Paris Arcos accepted the option-2 minimal executive dashboard and warning-only
MVP overlap handling on 2026-09-27; see [proposal](../../proposal.md#scoped-mvp-decisions).
The full pre-code gate was subsequently APPROVED on 2026-09-27, including
response-v2 strings/null and the technical-contract details below.

### Requirement: Executive cost KPIs consume the billing contract
The executive / view SHALL consume billing response v2 through services/api.ts
for period totals and a selectable five-dimension amount breakdown. It SHALL
show returned currency, period and missing-data information. The legacy overview
SHALL remain compatible; neither view SHALL fabricate savings or fall back to
demo cost. Existing session/tenant protections SHALL remain in force.
This scope SHALL remain limited to totals, period and the selectable table,
retaining /overview-legacy; full dashboards, time series and exports are excluded.
Both views SHALL warn of possible overlap on 409 ambiguous_cost_source without
ambiguous monetary values or any replace/confirm action or overwrite. Future
ingestion replacement is deferred in [RF-026-001](../../../../findings/backlog.md#rf-026-001).

#### Scenario: Live cost and unavailable savings
- **WHEN** billing returns costs for the selected tenant and period
- **THEN** executive totals/breakdown use exact response strings, separate currencies and credits
- **AND** executive/legacy savings are unavailable, without demo percentage or trend substitution

#### Scenario: Selection and tenant transitions
- **WHEN** tenant, dates, grouping or tag key changes while a response is pending
- **THEN** query identity includes those inputs and previous/late results cannot appear as the new selection
- **AND** no request occurs without an active tenant; existing session invalidation remains effective

#### Scenario: Distinct states and retained gaps
- **WHEN** billing is loading, fails (including source conflict), is empty, is partial or has observed zero
- **THEN** the view communicates that state without a fake zero, demo fallback or false service-coverage claim
- **AND** 409 ambiguous_cost_source displays a possible-overlap warning, no ambiguous amounts and no replace/confirm action; it never triggers ingestion writes
- **AND** remaining demo charts/export and inventory stay visibly separate; only evidenced JUP-097 rows change, without closing RF-091-003/RF-095-002 globally
