JUP: JUP-026

## PR52 Proposed Corrections

**APPROVED, Paris Arcos, 2026-09-30.** The historical contract below
explicitly preserves case and requires a literal canonical tag key. Only the
following exceptions supersede those historical rules under the new approval.
Review actor, HEAD, approval and exclusions are in the [amendment](proposal.md#pr52-review-amendment-2026-09-30).

- Resource groups: within the existing tenant/period SQL, group by currency,
  subscription and `lower(present(resource_group))`; display
  `min(present(resource_group))` under existing binary string ordering.
  `Shared`/`shared` display as `Shared`; `DevTestLab`/`devtestlab` as `DevTestLab`.
  Null/blank buckets, tenant/currency separation, totals and overlap checks
  retain their rules. Return aggregates only, without loading raw records.
  SQL `lower` guarantees the requested ASCII case matching; it is not Python
  `casefold` or a claim of Azure ordinal Unicode equivalence. Non-ASCII names
  follow database `lower` semantics only;
  the whole-repository Unicode decision remains [RF-014-002](../../findings/backlog.md).
- Tag keys: mirror processor `apps/processor/app/normalization/azure_cost.py`
  `_canonical_tag_key` exactly in a small billing-route helper: `strip()`,
  `casefold()`, replace each `[^a-z0-9]+` run with `_`, strip edge `_`, then
  aliases `costcenter`/`cost_centre` -> `cost_center`, `env` -> `environment`,
  `org` -> `organization`. Thus `CostCenter`/`costcenter` select `cost_center`
  and `Environment`/` Environment` select `environment`. Bind and echo the
  canonical key; reject an empty canonical result with 422. Unknown nonempty
  canonical keys retain the null bucket. Stored tag VALUES remain case-sensitive.
- Validate the URL-decoded tag key before normalization: any character with
  `ord < 32` or `ord == 127`, including `%00`, returns 422 before
  `fetch_billing_summary`/billing SQL. This reuses only the control-character
  criterion in `apps/backend/app/api/dependencies.py` for `X-Tenant-Id`, not
  its whitespace/comma bans or 400 status. Ordinary spaces reach normalization;
  existing group/key combination rules and auth/membership checks remain intact.

After approval, product scope is only `apps/backend/app/api/routes/billing.py`
and the billing method in `apps/backend/app/db/database.py`. Mirror the existing
algorithm without importing the processor service or creating a shared package.
No frontend product change is expected: `isBillingSummary` requires a nonblank
response key, not equality with the raw request key. Retry policy remains outside
JUP-026. No new ADR or processor change is proposed.

## Proposed Contract

Reuse GET /billing/summary and Database.fetch_billing_summary over existing
002/003/004 normalized schema/indexes. Keep bearer, X-Tenant-Id and integrated
JUP-086 tenant checks. No new endpoint, schema, dependency or security setting.
ADR: [ADR-0010](../../../docs/adr/ADR-0010-azure-cost-source-overlap.md)
(Accepted, Paris Arcos, 2026-09-28) records the conservative overlap policy below.
Final human approval, technical review and QA status are recorded in [review.md](review.md).
The approved functional contract is unchanged.

Paris Arcos accepted the minimal option-2 frontend and
warning-only MVP scope on 2026-09-27; see [scoped decisions](proposal.md#scoped-mvp-decisions).
The full technical contract below, including response-v2 strings/null, was
subsequently approved at the proposal's pre-code gate on 2026-09-27.
Source replacement is deferred in
[RF-026-001](../../findings/backlog.md#rf-026-001). It tracks future ingestion
replacement with explicit confirmation, outside the current contract and
implementation authorization.

- start_date/end_date: optional ISO-date pair, inclusive start/exclusive end.
  Both omitted means current UTC calendar month; invalid/incomplete pairs or
  start >= end return 422. Stored DATE values are not timezone shifted.
- group_by: subscription (default), resource_group, service, project or tag.
- tag_key: required only for tag, nonblank literal stored canonical key.
  Unknown key means null bucket; invalid combinations return 422.

Response shape:

```text
contract_version: 2
period: { start_date: ISO-date, end_date: ISO-date, timezone: "UTC" }
group_by: subscription | resource_group | service | project | tag
tag_key: string | null
data_status: available | partial | empty
totals: [{ currency: string, cost: DecimalString, record_count: integer }]
groups: [{ currency: string, subscription_id: string | null,
           value: string | null, cost: DecimalString, record_count: integer }]
missing_dimension_count: integer
excluded_undated_count: integer
monthly_spend: DecimalString | null
currency: string | null
savings_identified: null
open_ingestions: integer
```

Sum DECIMAL(38,12) at stored precision; quantize each final aggregate once with
ROUND_HALF_UP and sufficient Decimal precision to exactly two fractional digits.
Keep credits/zero, normalize negative zero to "0.00", separate currencies and
never use FX/binary-float arithmetic. Independently rounded groups may differ
from the rounded total; no balancing adjustment. Single-currency totals populate
monthly_spend/currency aliases for the returned period; otherwise both are null.
This breaks integer/number compatibility: update backend and both consumers
together. open_ingestions retains existing tenant job count across all statuses,
outside the cost period. No consumption or savings engine is proposed.

## SQL And Missing Data

Use completed runs only, joining records/runs by ingestion ID, tenant AND
subscription with authorized tenant bound on both. One parameterized cost query
using scoped CTEs and GROUPING SETS or aggregate UNION returns totals, selected
groups and omission/conflict counts; retain the job-count query in the same
consistent read transaction. Bind dates/tenant/tag; dimension SQL comes from an
enum map. Return only aggregates, never load raw records or query per group.

Inspected ingestion_run_id hashes tenant, subscription and the entire query
definition; complete_run replaces rows only for that run. Changing timePeriod
or grouping therefore creates another retained run which can represent the same
charges on the same dates. Summing every completed run can double-count them;
row hashes include differing dimensions and cannot establish charge identity.
Proposed minimum guard: multiple completed ingestion IDs for one subscription/
date in the requested period return 409, detail code ambiguous_cost_source,
without amounts/source IDs. Same-ID replacement is unaffected. This conservative
rule also rejects genuinely disjoint filtered inputs: the same date does not
establish identical charges. Paris accepted this exact predicate and its
disclosed limitation at the pre-code gate. The accepted MVP treatment is a
frontend warning of possible overlap with no ambiguous monetary result, never
a warning alongside a sum of ambiguous sources. GET /billing/summary is
read-only: no replacement, confirmation, automatic latest-run selection,
deduplication engine or ingestion change is authorized. Future confirmed
replacement is deferred to [RF-026-001](../../findings/backlog.md#rf-026-001)
and is not a JUP-026 blocker when the
warning/no ambiguous sums acceptance is met.

Group by subscription_id; (subscription_id, resource_group); service_name;
typed project with tags.project fallback only when blank/absent; or one selected
tag value. Each row contributes once, never once per tag. Group subscription_id
is null for service/project/tag. Preserve stored spelling/case; null/blank/
whitespace values share NULL, distinct from literal "Unknown". Sort by currency,
subscription_id, value in stable binary order, nulls last.

Exclude undated rows from amounts and count all completed undated tenant rows
separately, since no period can be assigned. Count missing selected dimensions
among included dated rows. Either omission count makes status partial; otherwise
no dated rows means empty arrays/null aliases, else available. Observed zero
retains its record count and "0.00". Available does not certify full coverage;
DB errors remain errors. Default resource grouping may have no service names:
show partial/null bucket. Named-service acceptance needs a populated reference,
not inferred names or another ingestion feature.

## Minimal Frontend And Exact Paths

This option-2 boundary is accepted by Paris Arcos on 2026-09-27; it does not
include full dashboards, time series or exports. The full API contract and
the details below were subsequently approved at the pre-code gate.

On /, replace kpiData[0], kpiData[1] and serviceData with live total(s) and one
five-dimension amount table (initially service), period inputs and conditional
tag-key input. Display exact strings/currency, null buckets and partial counts.
No fabricated trend/pie percentage; kpiData[2] savings becomes unavailable.
Remaining monthlyData charts/export and kpiData[3] inventory stay visibly
separate as demo, never KPI fallback. Remove multi-provider wording from the
live Azure section. No extra export capability or other-dashboard integration.

Use outlet context and a billing-only React Query hook through services/api.ts.
Key by tenant, version, dates, grouping/tag; retain generation/401 handling and
hide old-selection values. No tenant means no request. Distinguish loading,
error/409, empty, partial and observed zero. On 409 ambiguous_cost_source, both
views warn of possible overlapping ingestion sources without showing ambiguous
amounts or offering replace/confirm controls. Preserve /overview-legacy and its
hook, adapting totals/currency strings and unavailable savings as approved.

Exact approved product files:

- apps/backend/app/api/routes/billing.py
- apps/backend/app/schemas/billing.py
- apps/backend/app/db/database.py (billing method only)
- apps/frontend/src/services/api.ts (billing operation only)
- apps/frontend/src/services/contracts.ts (billing types/validation only)
- apps/frontend/src/hooks/useCostKpis.ts (new)
- apps/frontend/src/pages/ExecutiveCostDashboard.tsx
- apps/frontend/src/pages/DashboardPage.tsx
- apps/frontend/src/data/demo/executiveCostDashboard.ts (replaced constants/comments)

Later update only evidenced rows in docs/planning/JUP-097-frontend-data-gap-map.md.
Keep operational C2+C3, other capabilities and existing findings open. Retain
JUP-086 through the expressly approved stacked base; its integration into develop
remains separate. PR48 was integrated locally as 847fa3c; its merge into develop
remains separate. Revalidate the combined base; do not duplicate either correction. Use
existing migrations in an isolated validation DB, not shared data.
Public default data is June 2024: select its actual period for reference checks.
