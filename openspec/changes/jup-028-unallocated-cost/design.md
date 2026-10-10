JUP: JUP-028
Trello: https://trello.com/c/RG9O2Ltx

## Context

The normalized billing records contain optional canonical tags and signed
`pretax_cost`. They do not contain an authoritative allocation-rule registry,
approved ownership catalog or verified financial allocation status. Existing
business rules distinguish tagging compliance from allocation: a documented
cost-center rule can assign a cost whose owner tag is absent, and a governed
shared cost is different from an unallocated cost.

The endpoint identifies metadata gaps for investigation. Its response states
`detection_basis=observed_required_tags` and
`allocation_status=not_evaluated`. The route name follows the Trello card;
monetary fields use `complete_metadata` and `candidate`, not financial
assignment labels.

## Policy And Dependency Contract

Reuse `apps/backend/app/core/tag_policy.py` byte-for-byte from JUP-017 PR #66,
with `policy_version=economicon-minimum-v1` and this fixed order:

1. `owner`
2. `environment`
3. `application`
4. `cost_center`
5. `project`

A value must be a JSON string, trimmed for validation. Non-environment values
must match `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`. Empty values, absent keys,
non-strings and the case-insensitive markers `unknown`, `n/a`, `null`, `none`,
`true`, `false`, `undefined`, `unassigned`, `-` fail the rule. Environment
accepts dev/development, test/testing, staging/stage and prod/production,
case-insensitively. Values are not rewritten and no catalog membership is
claimed. Arbitrary extra tags do not replace required tags.

JUP-015's card supplies these five dimensions. The older corpus's
`businessunit` proposal is explicitly not used; correcting its separate
content contract is outside this change. JUP-015 catalogs can later introduce
a new explicit policy version. No implementation from JUP-027 is assumed.
The reused predicate aligns candidate detection with JUP-017 metadata
noncompliance, not with financial assignment or a sum of showback dimensions.

## API And Access

`GET /billing/unallocated-cost?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
requires both dates and active-tenant membership through the existing
dependencies. Dates are valid calendar dates with `start_date < end_date`.
The range is UTC, start-inclusive and end-exclusive; no server-local current
month is inferred. Invalid or missing dates yield 422 without reading costs.

The response includes contract version 1, policy identifiers, the period,
availability and undated-record count. Per-currency results include:

- `record_count` and `candidate_record_count`;
- `positive_cost`, `complete_metadata_cost`, `candidate_cost`;
- `negative_adjustments`, `complete_metadata_negative_adjustments`,
  `candidate_negative_adjustments`;
- `net_cost`, `complete_metadata_net_cost`, `candidate_net_cost`;
- `candidate_percent`, `no_positive_cost_reason` and disjoint `groups`.

Each group exposes the ordered set `missing_or_invalid_tags`, a diagnostic
`reason`, `record_count`, positive cost, signed negative adjustments and net.
No raw tag value, resource identifier, ingestion identifier or other tenant's
data is returned.

## Source Scope And Overlap

Follow the accepted
[ADR-0010](../../../docs/adr/ADR-0010-azure-cost-source-overlap.md). Join each
record to its ingestion run by ingestion ID, tenant and subscription, restrict
both sides to the authorized tenant, and require run status `completed`.
Apply the requested interval to dated records.

Before returning money, reject any subscription/day with more than one distinct
completed ingestion ID. Return HTTP 409 with
`detail.code=ambiguous_cost_source` and no amounts. This conservative check can
also reject valid disjoint filtered sources. It neither proves duplicate
charges nor repairs them. Do not apply latest-wins, deduplicate by resource or
row hash, or sum overlapping sources with a warning.

Count undated records in the completed authorized scope separately. They cannot
be assigned to the requested interval, so they are excluded from monetary
results and `excluded_undated_count` makes that limit visible. `data_status` is
`partial` if that count is nonzero, otherwise `available` when dated records
exist and `empty` when none exist. Metadata defects themselves are measured
results, not a reason to mark the source scope partial.

## Exclusive Defect Signatures

Assign one bit to each required tag in the fixed policy order. A valid tag
contributes zero; a missing or invalid tag contributes its bit. Signature zero
means complete metadata. Each nonzero signature is one candidate group.

The SQL groups by currency and signature before returning results: at most 32
groups per currency, of which at most 31 are candidates. A record missing
owner, application and project belongs to one group and contributes its cost
once. No cost is duplicated per missing tag or per diagnostic reason.

Reasons describe the observed signature:

| Signature defects | Reason |
| --- | --- |
| Only owner | `no_owner` |
| One or more non-owner tags | `unclassified` |
| Owner and one or more non-owner tags | `no_owner_and_unclassified` |

Here `unclassified` means incomplete minimum classification metadata, including
environment; it does not mean there is no usable organizational dimension or
that a documented allocation rule cannot assign the cost. A missing
environment alone can therefore produce a candidate while owner and project
remain present. A future showback view must retain this distinction.

## Monetary Arithmetic And Reconciliation

Aggregate exact database decimal values within the same currency. For each
currency, partition both positive charges and signed negative adjustments
between signature zero and nonzero signatures. Zero-cost records still affect
record counts and diagnostic groups. Before display rounding:

```text
positive_cost = complete_metadata_cost + candidate_cost
negative_adjustments = complete_metadata_negative_adjustments
                     + candidate_negative_adjustments
net_cost = positive_cost + negative_adjustments
candidate_net_cost = candidate_cost + candidate_negative_adjustments
```

Use positive charges for coverage, so credits do not cancel the denominator or
produce unbounded percentages. Match JUP-017's displayed complement:

```text
complete_percent = round_half_up(100 * complete_metadata_cost / positive_cost, 2)
candidate_percent = 100.00 - complete_percent
```

The division uses unrounded costs. Amounts and percentages are serialized as
two-decimal strings with HALF_UP rounding; values above JavaScript's safe
integer range remain exact strings. Aggregates are rounded independently, so
displayed groups or subtotals can differ from their displayed total by cents.
Consumers must not recompute authoritative totals from rounded groups. The
complement rule intentionally avoids a 100.01% sum at a rounding boundary.

If no positive charges exist, `candidate_percent` is null. The reason is
`negative_adjustments_only` if signed negative adjustments exist, otherwise
`zero_cost_only`. A truly empty result has no currency rows. Net zero with
positive charges still has a defined percentage.

## Limits And Future Integration

- Results describe stored observed costs, not a complete invoice or live Azure.
- The existing query mapping supports CostCenter, Project, env and org as tag
  groupings. A source query can discard owner/application detail. Absence in
  stored tags is not proof of absence on the source resource.
- Normalization can stringify source null/boolean values; the reused predicate
  rejects their common serialized markers. It cannot recover lost source type
  information or validate corporate catalog membership.
- Do not infer owner from organization or application from project. Tags named
  shared/excluded do not constitute an approved assignment or exclusion rule.
- Financial `allocated/shared/unallocated/excluded` status remains unevaluated.
  No eligibility exclusions or shared-cost allocations are invented.
- No frontend, resource list, automated remediation, new persistence or
  integrated JUP-015/JUP-027/JUP-017 end-to-end flow is claimed.

## Verification And Delivery

Verify the predicate with missing, invalid, placeholder and valid values;
verify exclusive grouping with multiple defects; verify multi-currency,
credits, zero and fractional costs, large values, empty/partial data and
percentage rounding. Exercise real compatible SQL for tenant, run and period
scope and overlapping-source rejection. Route checks must prove denied access
and invalid dates cannot read costs. Any use of doubles or skipped database
checks must remain explicit in evidence.

Technical test results are recorded separately after execution. Human roles
remain those in Trello; pairing, review and validation are not inferred from
the implementation or from these tests. No completion or acceptance is claimed
until the required independent evidence exists.
