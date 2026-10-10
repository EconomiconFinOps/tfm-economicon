JUP: JUP-017

## Contract and policy

GET /billing/tag-coverage accepts start_date/end_date as a paired ISO interval,
inclusive/exclusive; omission selects current UTC month. Invalid selections are
422. Reuse authenticated active-tenant membership and ADR-0010's completed-source
overlap rejection (409 ambiguous_cost_source), even for disjoint resources.
Undated completed rows are excluded and counted.

Response version 1: period, policy_version, required_tags, data_status,
excluded_undated_count and a currencies array. Each currency has record counts,
positive_cost, compliant_cost, noncompliant_cost, negative_adjustments,
compliant_negative_adjustments, noncompliant_negative_adjustments, net_cost,
compliant_net_cost, noncompliant_net_cost, compliant_percent,
noncompliant_percent, no_positive_cost_reason and missing_or_invalid_tag_counts.
Amounts and percentages are Decimal strings rounded once with ROUND_HALF_UP to
two decimals; no JS conversion of amounts. Percentages use unrounded SQL sums.
Each amount is rounded independently; displayed subtotals can differ by rounding,
while raw aggregates reconcile. The panel states this limitation explicitly.
Round compliant_percent and derive its displayed complement to ensure 100.00.
N/D reason: zero_cost_only or negative_adjustments_only; no rows means currencies
empty and empty data_status unless undated rows make it partial.

Policy economicon-minimum-v1 requires canonical normalized tags owner,
environment, application, cost_center and project. Four identifier values must
match [A-Za-z0-9][A-Za-z0-9_.:-]{0,127} after edge whitespace removal; they are
syntactically valid IDs, not verified membership of a corporate catalog.
Blank, JSON null/non-string, unknown/n/a/null/none/true/false/undefined/unassigned/-
are invalid. None/True/False are also rejected as normalized serialization artifacts.
Environment is matched case-insensitively against dev/development, test/testing,
staging/stage, prod/production. Aliases are validation-only; stored data unchanged.
This explicit rule set supplies MVP validation while JUP-015's organizational
catalogs remain separate. Future catalogs require a new policy version.

Use the processor's canonical stored keys; do not infer owner from organization
or ProjectOwner, or application from project/resource names. Legacy/unmaterialized
keys remain missing until source normalization is fixed. Extra tags do not
compensate. Partial coverage invalidates the entire row.

## Calculation and implementation

P=sum positive costs, T=sum positive costs with every rule satisfied, U=P-T.
Percentages T/P and U/P; no positive costs yields null. Signed negative costs
stay separate regardless of tags; N=P+C. A zero net with P>0 still has coverage.
Negative cost is called an adjustment: source does not necessarily prove credit.
Count defects independently per tag; counts can overlap and are not additive.
Keep non-taggable/shared charges in P/U absent the required tags.

Aggregate on CockroachDB within the same scoped query pattern as billing,
without fetching raw rows. No sum across currencies or overlapping source views.
An ingestion must preserve the full tag combination at sufficient granularity;
summary groupings cannot reconstruct absent tags. UI reports observed metadata
compliance rather than proof of financial allocation.

## Frontend

Expandable panel under the executive period selector; loading/error/N-D,
per-currency positive compliant/noncompliant charges, percentages, adjustments
and net reconciliation. Query cache key includes tenant, session generation,
policy contract and period. AbortSignal propagates; terminal 409/422 are not
retried. Do not show stale values after selection changes or error.

ADR: [ADR-0013](../../../../docs/adr/ADR-0013-tagged-cost-coverage.md).
