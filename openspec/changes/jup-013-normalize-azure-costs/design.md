JUP: JUP-013

## Context

Azure Cost Query returns aggregated columns selected by each request. JUP-077
validates those dynamic columns and persists non-core values in JSON. The public
dataset includes EA and FOCUS names for the same concepts, and explicitly warns
that casing and serialized tags vary. A useful common record must normalize
names while preserving source values and optionality.

## Decisions

### Extend the existing record instead of creating another pipeline

`NormalizedCostRecord` remains the single boundary between the client and
CockroachDB. Known aliases are promoted; unrecognized values remain in
`dimensions`. This keeps JUP-076/077 idempotency and failure semantics intact.

### Model aggregation sparsity explicitly

Azure returns only requested groupings. Billing account, subscription name,
resource group, service, project and consumption are therefore nullable. The
scope subscription remains a required repository column supplied by the path,
not copied from an optional response grouping.

### Normalize aliases, not source spelling

EA, FOCUS and Query aliases map to one field. Text is trimmed but its spelling
and case are preserved. Tag keys become stable snake-case names; values remain
source values. The canonical hash uses promoted fields, so equivalent alias
names with equivalent values produce the same hash.

### Require a complete consumption pair

Quantity and unit are both optional, but one without the other is rejected.
Finite zero and negative quantities are retained because adjustments are valid
in the public fixture, just as zero and negative costs are retained.

### Evolve storage in place

Migration 003 adds nullable typed columns and a non-null JSON tag object,
backfills fields available in old `dimensions`, and creates indexes for scope,
resource group and service. The original JSON remains for unknown dimensions.

### Commit migration 003 statements before dependent backfill

The reported real CockroachDB 24.1.11 integration run passes fresh creation but
fails the 001/002 upgrade with six legacy rows: migration 003's backfill raises
`UndefinedColumn` for `records.billing_account_id`. The current processor runner
encloses all pending migrations in one transaction, so the added columns on an
existing table are not visible to the dependent backfill in that transaction.

The [CockroachDB 24.1 online schema change guidance](https://docs.cockroachlabs.com/docs/v24.1/online-schema-changes)
recommends implicit single-statement transactions for schema changes and
describes the exception for tables created in the same transaction. This is
consistent with the observed fresh-create success and existing-table upgrade
failure, and supports the migration-specific autocommit correction below.

Add only a module-level `transactional = False` opt-in to
`apps/processor/app/db/migrations/003_normalized_cost_dimensions.py`, interpreted
by `apps/processor/app/db/migration_runner.py`. An absent flag defaults to true.
Commit version-table initialization before executing pending migrations in their
existing sorted order. For an unmarked migration, execute its upgrade and version
insert together inside `engine.begin()`: a failure rolls back both. This makes
the transaction boundary per migration instead of the entire pending batch;
successful earlier migrations remain recorded if a later migration fails.

For 003, use a dedicated connection configured with
`isolation_level="AUTOCOMMIT"` before its first statement, outside any active
transaction. Execute the existing upgrade in order so the additive DDL commits
before the backfill and indexes. Insert version 003 only after the entire upgrade
returns successfully. Do not change the engine's default isolation or reuse this
connection for transactional migrations. Propagate upgrade or version-insert
errors and stop the run; do not continue to later migrations or report success.

Partial commits are expected for 003. Retry through the normal runner after the
failure is resolved, without deleting rows, dropping columns or manually marking
completion. Existing `IF NOT EXISTS`, typed-field `COALESCE`, and preservation of
non-empty tags make re-execution safe for the same legacy input. A failure before
the version insert leaves 003 pending, including when all upgrade statements
already committed. If the version insert committed but its acknowledgement was
lost, the next run reads that marker and skips the already completed migration.
No automatic retry loop or concurrent-runner coordination is introduced.

This is a correction within the approved PR #14 integration scope. It adds no
new migration, dependency, CI change, shared-database operation, other service
runner change or migration framework. Acceptance belongs in the existing
processor integration tests and focused runner regression coverage during the
implementation and review loop.

### Preserve legacy values when completing a partial backfill

The old dimensional store accepted numeric individual tags. Migration 003 must
retain their source JSON and project their text representation into tags without
applying the stricter new-ingestion text validator to those historical values.
Reconcile serialized tags and individual tag columns together. Add missing keys
to an existing tag object without replacing or removing any existing key/value;
this also completes the incomplete object left by an interrupted SQL backfill.
The new-ingestion validation contract remains unchanged.

Treat consumption as a pair during recovery. When both typed components are
missing, backfill only a complete source pair. When only one is missing, fill it
only if the retained component matches the corresponding source value. Preserve
an incompatible partial pair unchanged rather than inventing a measurement from
two different sources. Keep raw dimensions, record identities and costs intact.

## Risks and mitigations

- A query omits a dimension: keep the field null and never infer it.
- Provider schemas use different aliases: normalize the audited EA/FOCUS set
  and reject conflicting aliases in one row.
- Legacy tag serialization is malformed: parse valid key/value pairs
  tolerantly and preserve recognized content.
- Migration loses prior demo rows: use additive columns and backfill only nulls.

## Rollback

The code can stop reading the new columns while the additive database columns
remain harmless. No destructive down migration is provided because removing
columns would discard evidence and violates the project's migration policy.

## Integration validation

Integrate existing PR #14 before PR #19, retaining the normalization and
migration scope above. Validate the branch updated from `develop` in isolated
CockroachDB databases: one fresh database running migrations 001 through 003,
and one with migrations 001/002 and representative legacy rows before 003.

Compare record identities, individual costs and cost totals per tenant,
subscription and currency before and after the upgrade. Verify typed fields,
tags, optional consumption, unknown dimensions and indexes, then repeat
ingestion with the same scope, query and input to check stable counts, hashes
and totals. Exercise the existing alias, zero, negative and invalid-input
scenarios against the updated branch.

The updated PR must pass all seven existing CI checks: `JUP policy`, `OpenSpec`,
`Python tests (azure-cost-api)`, `Python tests (backend)`,
`Python tests (processor)`, `Frontend build` and `Frontend type check`.
Historical validation tasks do not establish results for this updated branch.

## ADR assessment

ADR: not applicable to this integration. It retains the existing normalization
boundary, CockroachDB storage and additive migration design; it introduces no
new durable architecture decision.
