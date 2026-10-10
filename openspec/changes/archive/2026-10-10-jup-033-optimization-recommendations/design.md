JUP: JUP-033
Trello: https://trello.com/c/ndrittYl

## Context and boundary

JUP-026 provides a tenant-scoped billing summary with decimal amounts, separate
currencies, a selected UTC period, missing dimensions and data-quality signals.
JUP-033 consumes that boundary to suggest a next investigation or attribution
action. The current ingestion source is `azure_cost_records` populated by the
simulated Azure path; a stored observation is not proof of live Azure coverage.

No new durable architecture decision is introduced. The established
[simulation boundary](../../../../docs/adr/ADR-0001-azure-cost-api-simulation.md),
[tenant boundary](../../../../docs/adr/ADR-0008-tenant-isolation-boundaries.md) and
[source-overlap policy](../../../../docs/adr/ADR-0010-azure-cost-source-overlap.md)
continue to apply. The local recommendation rules and contract live here.

## HTTP and data access

GET `/billing/recommendations` requires `start_date` and `end_date` in ISO
`YYYY-MM-DD` form. The interval is `[start_date, end_date)` in UTC; its duration
must be from 1 through 366 days. Missing, malformed, impossible, equal, reversed
or overlong dates return 422 before any billing fetch.

Authentication and membership use the existing `get_active_tenant` dependency.
The service uses that trusted tenant identifier, never a tenant supplied as
recommendation evidence. One call to `fetch_billing_summary` passes both selected
dates, `group_by="project"` and `tag_key=None`. There is no new SQL path and no
unfiltered read. The existing billing interpretation of project and its
`tags.project` fallback is inherited. Ambiguous sources return the same 409
`ambiguous_cost_source` error as the summary endpoint, with no proposals.

The billing layer consolidates project costs across subscriptions within the
active tenant by project value and currency. The recommendation service consumes
those unique aggregates, preserving decimal arithmetic and credits without
converting or comparing unlike currencies. It uses the already rounded billing
group amounts rather than reconstructing underlying unrounded rows. Duplicate
project/currency groups or subscription-specific groups violate this boundary
and fail instead of silently double-counting costs.

## Rules and business context

`missing_project` applies when observed records lack project attribution. It
returns a supported tagging recommendation even when the affected group's net
cost is zero or negative. The action is to identify the responsible business
application/project and correct attribution after checking ownership. A credit
does not establish that classification is complete, and missing project does
not establish that every other business tag is absent.

`largest_project_cost` selects the highest positive named-project aggregate per
currency. Equal costs use a deterministic project-name ordering. Its status is
`investigation_candidate`: ask the owner to verify workload purpose, service
criticality, usage and cost drivers before selecting an optimization. High cost
alone does not establish inefficiency or justify reducing a resource.

The `not_evaluated` section contains `rightsizing`, `scheduling`,
`orphan_cleanup`, `rate_optimization` and `savings_impact`, with missing inputs
stated explicitly: utilization and performance needs, business operating
schedules, verified inventory/ownership, commitment and pricing information,
or a comparable baseline and versioned impact assumptions. Shutdown and
reservation actions are never emitted merely because a project is expensive.

## Response and reproducibility

The report has `contract_version: 1`, `source: "azure_cost_records"`,
`cloud: "azure"`, `data_environment: "simulated"` and retains the requested
period and billing `data_status`. Its `status` is `available` when there is observed
data for the implemented evaluation, or `insufficient_data` when there is not.
An available report can legitimately contain no recommendation, for example
when all named projects have nonpositive net costs. Empty data is not a finding
of zero waste. Partial billing coverage remains visible and limits conclusions.

Each proposal contains its rule/version, project scope, `qualification`,
actionable explanation and evidence reference. `estimated_savings` and the
savings `currency` are null. Observed cost amount/currency appear separately in
evidence and must never be relabeled as a monthly, annual or realized saving.
Assumptions and limitations explain the source, missing telemetry, business
checks and lack of savings estimation. `requires_human_approval` is true;
confidence describes the rule's conclusion, low risk describes the proposed
review rather than a cloud modification, and implementation difficulty is
unknown. These fields are not a deployment permission or a savings ranking.

A recommendation ID derives deterministically from tenant, period, rule,
currency and project. It represents a proposal in that scope, not a persisted
workflow or authorization token. Evidence IDs are content-addressed and cover
the entire sorted comparison set and source-quality signals. A changed
observation or competing project can retain a recommendation's identity while
changing its evidence reference. Evidence includes the query's period,
`group_by: "project"` and null `tag_key`, rule/version, scope and observed cost.
Each returned proposal refers to its matching evidence; no unreferenced evidence
is returned. Reordering equivalent input groups must not change output identity
or selection. Tenant scoping participates in identity even when two tenants
have otherwise identical project names and costs.

Return at most 50 candidates ordered lexicographically by currency, rule ID
and project value; this is presentation order, not a ranking across currencies
or by savings. `total_candidates` reports the full count, and `truncated` is
true when it exceeds the returned count. Consumers must not represent that
bounded list as exhaustive. No persistence, acknowledgement or cloud write is
performed by generating a report.

## Consumer dependencies

JUP-034 can consume proposal identity, observed cost evidence and limitations
when it defines an estimation method and its additional inputs. Null savings
are not an estimate of zero. JUP-039 can explain the returned recommendations
with their evidence and applicability; JUP-058 can display the versioned report,
empty/partial state and truncation. None of those integrations is implemented
or claimed tested by this backend increment. Contract tests and explicit
doubles can verify this producer independently of those consumers.

## Validation plan

Exercise separate tenants and denied membership, all invalid period forms and
the inclusive-start/exclusive-end selection passed to billing. Verify a
cross-subscription project aggregate, missing projects with zero and credit
net cost, two currencies, equal-cost projects in shuffled input and observed
empty/partial data. Test recommendation identity stability, changed evidence,
the 50-item bound and ambiguity propagation. Assert null savings and explicit
missing inputs, and prove no billing fetch occurs on invalid or unauthorized
requests. Use clearly labeled database doubles for HTTP boundaries; distinguish
any real database exercise and live-cloud checks from those tests in evidence.

This document records intended verification, not completed test results. Human
pairing, review and validation must be evidenced independently under
`CONTRIBUTING.md` before the card can be accepted.
