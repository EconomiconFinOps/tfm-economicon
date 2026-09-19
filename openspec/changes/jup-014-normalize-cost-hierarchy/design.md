JUP: JUP-014
ADR: not applicable. Extends an already-accepted normalized-record shape
(JUP-013) with additional fields and a non-blocking data-quality signal;
introduces no new gateway, storage engine, auth boundary or provider.

## Context

JUP-013 (merged in `develop`, PR #14) added `AzureCostNormalizer`
(`apps/processor/app/normalization/azure_cost.py`), promoting
`billing_account_id`, `subscription_name`, `resource_group`, `service_name`
and `project` as explicit typed fields, persisted via migration 003.

Investigation during exploration for this change found the hierarchy is
incomplete in three ways:

1. The source dataset (`fixtures/azure-cost/EA-Cost-Actual.sample.csv`) has
   `ResourceId`, `ResourceName` and `BillingAccountId` columns, but the
   simulated Azure Cost API's mapping (`docs/api/azure-cost-query-mapping.json`)
   does not expose `ResourceId`/`ResourceName` as queryable dimensions.
2. The real ingestion entrypoint (`apps/processor/app/run_azure_cost_ingestion.py`,
   `DEFAULT_DEFINITION`) only requests `ResourceGroup` + `ServiceName` as
   grouping. `SubscriptionName`/`BillingAccountId` are supported by the
   normalizer's aliases but never actually populated outside unit-test
   fixtures, because they are never requested from the API.
3. Nothing validates that the hierarchy is internally consistent — e.g. that
   a given resource stays under the same resource group.

Separately, `tenant -> subscription` is already guaranteed structurally:
`AzureCostIngestionService.ingest(tenant_id, subscription_id, definition)`
fixes `subscription_id` as a scope parameter for the whole run, independent
of row data. It does not need validation here.

## Goals / Non-Goals

**Goals:**
- Make `ResourceId`/`ResourceName`/`BillingAccountId` reachable end-to-end:
  simulated API mapping -> ingestion grouping -> normalizer typed fields.
- Detect, within a single normalization batch, a `resource_id` reported
  under more than one `resource_group` (case-insensitive), without failing
  the batch or dropping the row.
- Add an automated check that prevents a migration from combining
  column-adding DDL and same-file backfill without the `transactional = False`
  opt-out, closing a gap found during exploration (no team convention
  documents this today).

**Non-Goals:**
- Validating hierarchy consistency **across** ingestion runs (e.g. the same
  resource group appearing under a different subscription in a past run).
  This needs querying persisted history via the repository, which the
  stateless `AzureCostNormalizer.normalize()` call does not have access to.
  Tracked as a new finding in `openspec/findings/backlog.md`, out of scope.
- Re-validating `tenant -> subscription`: already enforced by ingestion scope.
- Changing `azure-cost-ingestion-client`'s transport/pagination/retry
  contract: unaffected, this only changes which dimensions are requested.

## Decisions

### Expose resource-level dimensions via mapping config, not code

`CostRepository` (`apps/azure-cost-api/app/repository.py`) is fully
data-driven from `docs/api/azure-cost-query-mapping.json` — no dimension name
is hardcoded in Python. Adding `ResourceId`, `ResourceName` and
`BillingAccountId` is a mapping-file change only.

**Alternative considered:** hardcode the new dimensions in the simulator's
Python code. Rejected — breaks the existing config-driven design for no
benefit, and risks a second source of truth for supported dimensions.

### Treat cross-resource-group movement as a non-blocking signal, not an error

Azure resource groups are mutable; a resource can legitimately move to a
different resource group during the time window a cost query covers (the
real ingestion queries a 20-day period). JUP-013 already rejects genuine
data contradictions (e.g. conflicting aliases for the same concept in one
row) as hard errors — that pattern does not fit here, because the
inconsistency is not necessarily bad data.

**Alternative considered:** hard error, matching JUP-013's other conflict
checks. Rejected — would risk failing a legitimate ingestion for real-world
resource reorganization, and there is no way to distinguish "moved
resource" from "bad data" without cross-referencing timestamps per row,
which the current per-batch view does not need for anything else.

**Alternative considered:** silently ignore. Rejected — defeats the purpose
of this change (detecting hierarchy inconsistencies) and contradicts the
project's established pattern of surfacing findings instead of hiding them
(`openspec/findings/backlog.md`).

**Chosen:** persist the row as normalized, and record the anomaly as a
visible signal (exact persistence shape — column vs. separate table vs.
counter/metric — decided during implementation; must be queryable without
re-scanning raw dimensions).

### Automated migration-safety check as a small in-scope task

JUP-014 introduces a new migration with the same column-add + same-file
backfill shape that caused JUP-013's `UndefinedColumn` defect (DDL not yet
visible to the same transaction when the backfill runs immediately after).
`MigrationRunner` already supports a `transactional = False` per-migration
opt-out, but nothing enforces choosing it correctly — the rule lives only in
a code comment and in JUP-013's evidence, not in
`docs/manuals/python-service-conventions.md` or in an automated check.

**Alternative considered:** add a delay/sleep before backfilling. Rejected —
this is not a timing/latency issue: within the same uncommitted transaction,
the connection cannot see its own uncommitted DDL regardless of elapsed
time. A delay would be non-deterministic, would not fix the actual cause,
and would slow down every migration run unconditionally.

**Alternative considered:** document the convention only. Rejected as
insufficient on its own — relies on every future migration author reading
and remembering it. Kept as a complement (documenting the rule) but paired
with an automated test as the actual guarantee.

**Chosen:** add a test that inspects migration files for "adds a column"
followed by a same-file data-modifying statement, and fails unless
`transactional = False` is declared; document the rule in
`docs/manuals/python-service-conventions.md`.

## Risks / Trade-offs

- [Risk] Requesting `ResourceId` as a grouping dimension multiplies row
  volume (many resources per resource group; the sample has 233 resource
  groups) → Mitigation: no batching/pagination change needed for the
  simulator (already paginated per JUP-075); note the expected volume
  increase in evidence when validating.
- [Risk] The new migration hits the same DDL-visibility defect as JUP-013 if
  `transactional = False` is forgotten → Mitigation: the automated check
  above catches this before merge, not just before release.
- [Risk] The non-blocking anomaly signal could go unnoticed if not surfaced
  anywhere visible (dashboards, evidence) → Mitigation: document its
  persistence shape and confirm it is queryable in the acceptance criteria
  for this change; not required to build a dashboard here (JUP-047 exists
  for system health dashboards).
- [Trade-off] Leaving cross-run hierarchy validation out of scope means a
  genuine data-quality issue (e.g. a resource_group name colliding across
  subscriptions due to bad source data) would not be caught until a later
  card picks up the new finding.
- [Risk, discovered during validation] The simulated Azure Cost API caps
  `grouping` at 2 dimensions (`apps/azure-cost-api/app/models.py`,
  `Field(max_length=2)`, a real Azure Cost Management limit the simulator
  replicates). The proposal originally assumed `ResourceId` could be added
  as a third grouping alongside the existing `ResourceGroup` +
  `ServiceName`; a live end-to-end run against the API returned 400
  (`List should have at most 2 items after validation, not 3`). Resolved by
  dropping `ServiceName` from `DEFAULT_DEFINITION`, keeping `ResourceId` +
  `ResourceGroup` — the pair this change actually needs for hierarchy
  detection. `service_name` stops populating in the default ingestion,
  joining `subscription_name`/`billing_account_id` in the same
  already-existing situation (promoted by the normalizer, but not
  requested by the default query) rather than a new regression; nothing
  in the codebase reads it today (`GET /billing/summary` still returns
  mock figures per RF-091-004). `ServiceName` was itself only added in
  JUP-013, exactly filling the 2-dimension cap that already existed since
  JUP-074 — not a deliberate priority decision that this change overrides.

## Migration Plan

New additive migration (next sequential number after 003), following the
003 pattern exactly:
1. `ALTER TABLE azure_cost_records ADD COLUMN IF NOT EXISTS resource_id
   STRING, ADD COLUMN IF NOT EXISTS resource_name STRING` plus whatever
   column/shape is chosen for the anomaly signal — all nullable, additive.
2. Backfill from existing `dimensions` JSONB for already-ingested rows,
   same approach as 003's `_legacy_tags`/backfill CTE.
3. Declare `transactional = False` for this migration, matching 003's fix,
   and covered from day one by the new automated check.
4. Add an index on `resource_id` if resource-level queries are expected to
   be common (mirrors 003's `idx_azure_cost_records_resource_group`).
5. Validate fresh-database and upgrade-from-003 paths on a disposable
   CockroachDB 24.1.11 container, same procedure used for JUP-013's
   functional validation this session.

No rollback beyond standard additive-migration handling: nothing here drops
or renames existing columns.

## Open Questions

None. Resolved during implementation (task 1.1):

**Anomaly-signal persistence shape:** a nullable JSONB column
`resource_group_conflicts` on `azure_cost_records`. When a row's
`resource_id` was seen under more than one `resource_group` within the same
normalization batch, this column stores the other `resource_group` value(s)
observed for that resource; `NULL` when there is no conflict. Rejected a
boolean flag (loses which groups conflicted, forcing a re-scan of raw
dimensions to investigate) and a metric/counter alone (good for alerting
aggregate counts, not for drilling into which specific resource/row is
affected). The JSONB column supports both: `WHERE resource_group_conflicts
IS NOT NULL` gives a countable signal a future JUP-047 dashboard could use,
while the row still carries full investigation detail.
