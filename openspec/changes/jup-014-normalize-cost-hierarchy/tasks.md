## 1. Contract and reconciliation

- [x] 1.1 JUP-014 confirm which anomaly-signal persistence shape to use
  (dedicated column vs. JSONB detail vs. counter/metric), informed by how
  JUP-047's future health dashboard might consume it. Decided: nullable
  JSONB column `resource_group_conflicts`, see design.md.
- [x] 1.2 JUP-014 audit `docs/api/azure-cost-query-mapping.json` and
  `apps/azure-cost-api/app/repository.py` to confirm adding `ResourceId`,
  `ResourceName` and `BillingAccountId` needs no Python changes. Confirmed:
  no dimension name is hardcoded anywhere in `apps/azure-cost-api/app/*.py`.

## 2. Simulated API and ingestion client

- [x] 2.1 JUP-014 add `ResourceId`, `ResourceName` and `BillingAccountId` as
  queryable dimensions in `docs/api/azure-cost-query-mapping.json`
- [x] 2.2 JUP-014 verify existing `azure-cost-api` tests still pass and add
  coverage for querying/filtering by the new dimensions. 59/59 passed
  (RGR: RED confirmed at 400 before the mapping change, GREEN after).
- [x] 2.3 JUP-014 extend `DEFAULT_DEFINITION.dataset.grouping` in
  `apps/processor/app/run_azure_cost_ingestion.py` to request the resource
  level. RGR: new test asserted `ResourceId` present, failed, then passed
  after adding it. 264/264 processor tests green, no regressions.
  **Corrected during task 6.3**: the API caps grouping at 2 dimensions;
  dropped `ServiceName` to keep `ResourceId` + `ResourceGroup`. See
  design.md risks.

## 3. Normalizer

- [x] 3.1 JUP-014 promote `resource_id` and `resource_name` to typed fields
  in `AzureCostNormalizer`, following the existing `_DIMENSION_ALIASES`
  pattern
- [x] 3.2 JUP-014 implement non-blocking detection of a `resource_id`
  reported under more than one `resource_group` within one `normalize()`
  call, case-insensitive, preserving original casing per row
- [x] 3.3 JUP-014 add unit tests: resource fields promoted/omitted correctly,
  consistent resource across rows produces no signal, inconsistent resource
  produces a signal without rejecting any row, case-only differences produce
  no signal. RGR: 4 new tests RED before implementation, GREEN after.
  268/268 processor tests green (one existing fixture updated to include
  the two new required fields).

## 4. Persistence

- [x] 4.1 JUP-014 add a new additive migration (next number after 003):
  `resource_id`, `resource_name` and the chosen anomaly-signal shape, all
  nullable. Added `004_resource_hierarchy.py` with `resource_id`,
  `resource_name`, `resource_group_conflicts` (JSONB).
- [x] 4.2 JUP-014 backfill existing rows' `resource_id`/`resource_name` from
  the legacy `dimensions` JSONB, following 003's backfill approach.
  `resource_group_conflicts` is a newly computed signal, not backfillable
  from raw dimensions of legacy rows — left NULL for pre-existing data,
  noted as a limitation.
- [x] 4.3 JUP-014 add an index on `resource_id` if repository queries will
  filter/group by it. Added `idx_azure_cost_records_resource_id`.
- [x] 4.4 JUP-014 declare `transactional = False` for this migration from
  the start, given the column-add + same-file-backfill shape that caused
  JUP-013's `UndefinedColumn` defect. Repository INSERT/SELECT updated to
  persist/fetch the three new columns. RGR: migration + repository tests
  RED before implementation, GREEN after. 269/269 processor tests green.

## 5. Migration safety guardrail

- [x] 5.1 JUP-014 add a test that scans `apps/processor/app/db/migrations/`
  for a migration that adds a column and modifies data in the same file
  without declaring `transactional = False`, and fails when found
  unaccompanied by that flag. Implemented as a pure function
  (`app/db/migration_safety.py`) plus a test asserting zero violations
  across the real migrations directory.
- [x] 5.2 JUP-014 verify the new guardrail test fails against a
  reconstructed version of JUP-013's original (pre-fix) migration 003, and
  passes against the corrected one. Both reconstructed as inline fixtures
  in the test file (not real migration files) and asserted directly.
- [x] 5.3 JUP-014 document the migration convention (when to use
  `transactional = False` and why) in
  `docs/manuals/python-service-conventions.md`. RGR: 4 new tests RED before
  implementation, GREEN after. 273/273 processor tests green.

## 6. Validation and publication

- [x] 6.1 JUP-014 run all service, governance and build validations. Fixed
  two stale local venvs (missing `prometheus_client`) unrelated to this
  change. `openspec:validate` 30/31 (`containerized-runtime` pre-existing
  failure on `develop`, not introduced here); 56/56 governance/CI node
  tests; frontend lint/typecheck/build green; backend 115/115;
  azure-cost-api 59/59; processor 273/273.
- [ ] 6.2 JUP-014 validate fresh-database and upgrade-from-003 migration
  paths on a disposable CockroachDB 24.1.11 container, following the same
  procedure used for JUP-013's functional validation
- [ ] 6.3 JUP-014 verify real ingestion end-to-end with the expanded
  grouping and record the resulting row-volume increase in evidence
- [x] 6.4 JUP-014 register the cross-run hierarchy validation finding in
  `openspec/findings/backlog.md` as explicitly out of scope. Registered as
  RF-014-001.
- [ ] 6.5 JUP-014 publish a pull request toward `develop` and pass remote CI
