JUP: JUP-030

## Boundary and inputs

Reuse billing v2 through `get_active_tenant` and `fetch_billing_summary`.
The body never selects an arbitrary tenant or provides financial observations.
Accept explicit `[start_date, end_date)` UTC dates, 1 to 366 closed days,
one uppercase three-letter currency, and grouping by subscription, resource
group, service or project (default service). Reject extra fields and invalid
definitions before any billing read. Require at least one positive rule:
absolute_threshold or deviation_threshold_percent (at most 1000.00).
Amounts use canonical two-decimal strings, up to 26 integer digits;
min_absolute_increase defaults to 0.01 and must be positive.

For deviation, derive the immediately preceding period of equal duration.
Reject baseline date underflow. Otherwise do not query a baseline. Both reads
retain completed-ingestion and tenant predicates, separated currencies and
source-ambiguity checks. A conflict in either returns the existing 409.
Reads use separate transactions; no atomic two-period snapshot is claimed.

## Deterministic evaluation

Operate on the selected currency's current billing groups, preserving null
dimensions. Service and project are tenant-wide aggregates; subscription and
resource group retain subscription identity. Resource-group keys use lower()
to match billing's case-insensitive group convention within a case-sensitive
subscription. Reject duplicate keys rather than overwrite. Validate period,
grouping, tag selection, unique currencies and positive group record counts.

For C=current cost, B=baseline, T=absolute threshold, P=deviation percentage
and M=minimum increase, trigger absolute_threshold when C>=T. Trigger
period_increase when B>0, C-B>=M and (C-B)*100>=B*P. Either rule creates a
single candidate; trigger_reasons lists all matching rules. Use Decimal with
local precision; compare before percentage display rounding. Preserve credits.
The billing source already rounded group amounts to cents; output uses HALF_UP
at two decimal places and normalizes negative zero.

Missing baseline is not zero; zero/negative baseline is not a meaningful
percentage denominator. Expose baseline_missing/baseline_nonpositive and null
percentage. Retain an available signed delta with a nonpositive baseline.
Groups absent from the current period are not assessed or invented as zero.

## Evidence and uncertainty

Return contract_version=1, source=billing_summary_v2, normalized definition,
periods, quality for each read, all assessments and triggered alerts. Each
assessment retains group identity, currency, group counts, current/baseline
costs, delta, percentage and rule statuses. Alerts add cause_status=
not_established, a stable cost- ID and a separate evidence- ID.

Canonical JSON and SHA-256 identify version+authenticated tenant+definition+
group for the stable ID. Evidence hashes additionally include the assessment
and both quality objects. Changing evidence changes its ID while retaining
the same selection identity. Neither ID authorizes access nor references a
persisted record; there is no evidence lookup API. Consumers must retain the
payload and preserve tenant authorization when storing or displaying it.

Without current groups, evaluation is unavailable. Partial billing data or
any missing/nonpositive baseline makes an otherwise populated evaluation
provisional. Evaluated means enabled rules were evaluable over observed data;
completeness always remains not_verified. Quality record_count is for the
selected currency, missing_dimension_count is for all period currencies and
excluded_undated_count is tenant-wide for completed ingestions. There is no
verified day coverage, ingestion freshness, source-row trace or causal context.
Return explicit limitations; empty alerts do not certify normal expenditure.

## Downstream compatibility

[API contract](../../../docs/api/cost-anomalies.md) gives reproducible inputs,
sample evidence and JUP-038 usage. The consumer explains the observed threshold
crossing and cites evidence, keeping limitations; it must not attribute a cause
or savings. Actual tool registration, common envelope adaptation and agent
integration tests remain outside this change. JUP-057 remains labelled demo.

The existing JUP-084 daily rule (`relative_delta >20% AND absolute_delta
>100 EUR/day`) is distinct from configurable, inclusive period rules. It is
not replaced or declared implemented; its future adapter must explicitly
resolve daily coverage, boundaries and rule conjunction.

## Architecture and validation

ADR: not applicable to this local stateless calculation over the established
billing boundary. [ADR-0010](../../../docs/adr/ADR-0010-azure-cost-source-overlap.md)
continues to govern overlapping source rejection.

Test inclusive thresholds, rounded-percentage boundaries, large amounts,
credits, missing/zero/negative baselines, currencies, null dimensions, group
identity/collisions, evidence determinism/change, partial/empty data, invalid
dates/rules/extra fields, authenticated tenant propagation and 409 in either
period. Database tests must distinguish real Cockroach evidence from mocked
repository calls. Automated evidence is not assigned human validation.
