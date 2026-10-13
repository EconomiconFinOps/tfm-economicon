# ADR-0010: Conservative Azure cost source overlap handling

- Status: Accepted
- Date: 2026-09-27
- Accepted: 2026-09-28, Paris Arcos, final JUP-026 approval
- Related JUP/OpenSpec: JUP-026, [jup-026-azure-cost-kpis](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/proposal.md), [design](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/design.md#sql-and-missing-data)
- Trello: https://trello.com/c/anUswta8
- Supersedes: none
- Superseded by: none

## Context

Azure ingestion IDs include tenant, subscription and the full query definition.
Different periods, groupings or filters can retain multiple completed sources
for the same dates. Summing them can double-count charges; neither matching
dates nor row hashes with different dimensions establish charge identity.
This is a durable FinOps aggregation policy shared by the API and its consumers.

## Decision

Within the requested date range, multiple completed ingestion IDs containing
records for the same authenticated tenant, subscription and day cause
GET /billing/summary to return 409 with detail code `ambiguous_cost_source`,
without amounts or source IDs. The executive and legacy views show a warning
of possible source overlap without ambiguous monetary results.

The query remains read-only. This policy introduces no overwrite, confirmation,
source picker, automatic latest-wins selection, deduplication engine or ingestion
changes. Existing replacement within the same ingestion ID is unaffected.

## Consequences

- Avoids returning ambiguous sums while retaining existing data and boundaries.
- Does not prove duplicate charges: valid, disjoint filtered datasets for the
  same subscription and day can also be blocked. Availability is sacrificed
  when source compatibility cannot be established by this conservative rule.
- The warning explains the conflict but does not resolve it or certify that
  otherwise available data has complete cost coverage.

## Alternatives Considered

- Sum every completed source with a warning: can expose double-counted costs.
- Latest-wins or a source picker: introduces a source-selection contract and
  can omit valid data; outside the approved scope.
- Deduplicate records: query-dependent row identity cannot prove charge identity.
- Replace ingestion sources after explicit confirmation: deferred in
  [RF-026-001](../../openspec/findings/backlog.md#rf-026-001); requires separately
  agreed ingestion scope and is not authorized implementation in JUP-026.

## Evidence And Follow-up

The functional contract was approved by Paris Arcos on 2026-09-27 in the existing
[pre-code approval](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/proposal.md#local-pr48-integration-and-pre-code-approval).
Paris Arcos accepted this ADR with the final JUP-026 approval on 2026-09-28,
recorded in the [post-QA gate](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/review.md#post-qa-human-approval).
The decision and functional scope are unchanged; this does not authorize
ingestion replacement or establish integration into develop.
The [technical review](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/review.md)
and [validation evidence](../evidence/JUP-026-validation.md) record the SQL,
mutation, browser and delivery-gate results without changing the approved scope.

Existing acceptance covers the
[API conflict](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/specs/azure-cost-kpis/spec.md#scenario-alternative-ingestions-overlap)
and [frontend warning](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/specs/frontend-api-layer/spec.md#scenario-distinct-states-and-retained-gaps).
The [RF-026-001 detail](../../openspec/findings/backlog.md#rf-026-001) describes
future replacement with explicit confirmation, not current behavior or a new
JUP-026 delivery requirement.

## Integración verificada — 01/10/2026

[PR #52](https://github.com/EconomiconFinOps/tfm-economicon/pull/52) se integró en
develop el 30/09. La frase anterior sobre no establecer integración describe
el gate del 28/09. Se conservan aceptación, alcance conservador y RF-026-001.
