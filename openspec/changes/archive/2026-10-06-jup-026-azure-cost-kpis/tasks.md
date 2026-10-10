JUP: JUP-026

## PR52 Proposed Amendment Tasks

**PRE-CODE APPROVED, Paris Arcos, 2026-09-30.** Amendment tests/code are authorized.
Tasks A.1-A.5 track the amendment; the older numbered tasks remain historical.
The Lucia/`lmatsan` review is a correction request; Paris approved its bounded correction;
see [proposal](proposal.md#pr52-review-amendment-2026-09-30). No roles are reassigned.

- [x] A.1 Adapt the existing resource-group case and implement SQL lower-key grouping with binary-minimum labels within subscription/currency.
- [x] A.2 Reuse tag cases and implement exact processor key canonicalization/aliases and canonical response, retaining case-sensitive values and unknown-key null buckets.
- [x] A.3 Extend the existing invalid-selection case for controls and empty canonical keys; implement 422 before the billing read and normalization, without a blanket space/comma ban.
- [x] A.4 Demonstrate Red (4 FAIL/11 PASS), Green (15 PASS/0 SKIP), real SQL aggregation and directed mutation (7/7 detected, pre/post 15 PASS). No new collected cases. See [evidence](../../../../docs/evidence/JUP-026-validation.md#pr52-corrections-2026-09-30).
- [x] A.5 Complete affected technical review and acceptance/QA, including the bounded frontend consumer checks. REVIEW_PASS and QA_PASS_WITH_APPROVED_EXCEPTIONS recorded; evidence ready for final human approval. Human PR re-review/revalidation is not replaced by these internal checks.

Final human approval: APPROVED, Paris Arcos, 2026-09-30 ("apruebo el resultado").
Publication authorized separately by Paris on 2026-09-30 ("subelo"), including
checking CI, without merge. Human PR re-review, remote CI, integration and
archive remain separate gates.

Retry-policy work stays with [RF-098-002](../../../findings/backlog.md#rf-098-002-observation-in-jup-026),
registration-only for JUP-026; the official-card PR52 link is pending access.
Paris also authorized incorporating current develop locally and subsequently
publishing the approved correction. Merge into develop, tracker updates,
dependencies and archive remain excluded.

Pre-code approval is APPROVED by Paris Arcos on 2026-09-27. PR48 is integrated
locally in the validated combined base 847fa3c. Checked tasks are supported by
[evidence](../../../../docs/evidence/JUP-026-validation.md); integration and final
human approval are not implied. RF-026-002 deferral is explicitly approved;
QA is PASS_WITH_APPROVED_EXCEPTIONS. Paris Arcos gave the separate final human
approval on 2026-09-28, including ADR-0010; see the post-QA gate in review.md.
The historical integration on 2026-09-28 was local HEAD 4eb9427, merging develop
d244278 (merged PR47/JUP-086) into d86eb4e. Both JUP-014 and JUP-086 dependencies
are now incorporated. The merge changes ancestry only and preserves all 32
local files byte-identically before metadata updates; no new functional run
is claimed. The prior backend 329 PASS/17 external-service SKIP remains
historical evidence. See [reconciliation](../../../../docs/evidence/JUP-026-validation.md#merged-jup-086-develop-reconciliation).
This synchronization does not publish or integrate JUP-026 into develop.

Paris Arcos accepted option 2 (minimal executive totals, period and five-grouping
table, retaining /overview-legacy) and warning-only overlap handling on
2026-09-27; see [scoped decisions](proposal.md#scoped-mvp-decisions). Keep the
proposed 409 ambiguous_cost_source without ambiguous amounts, frontend warning,
no replace/confirm action or overwrites, and read-only GET /billing/summary.
The full technical contract, including response-v2 strings/null, was approved
subsequently; see the proposal's pre-code gate.
[RF-026-001](../../../findings/backlog.md#rf-026-001) defers source replacement;
it adds no implementation tasks or test expansion to JUP-026 and is not a
blocker if warning/no ambiguous sums acceptance is met. Tester/coder may now
proceed sequentially, with no implementation of the deferred enhancement.

## 1. Test First And Implement

- [x] 1.1 Refresh PR47/PR48 status, retaining the approved JUP-086 stacked base and PR48 as a separate prerequisite; confirm the full approved contract/paths and existing 003/004 schema.
- [x] 1.2 Add focused backend billing API/repository checks against independent Decimal reference totals/five groups, period/money/omissions, tenant predicates and the approved conflict rule. Reuse existing auth/normalization/isolated-Cockroach patterns.
- [x] 1.3 Extend ExecutiveCostDashboard.test.tsx using existing frontend test-support/fixtures for consumption, states and deferred tenant/filter transitions; adapt legacy billing contract expectations without removing their behavioral coverage. The already planned conflict-state scenario covers the possible-overlap warning, no ambiguous amounts and no replace/confirm action; no new scenario matrix.
- [x] 1.4 Implement only the design's backend/frontend paths and update only evidenced JUP-097 rows, preserving unresolved gaps/findings.

## 2. Verify And Review

- [x] 2.1 Compare production SQL/API with the reference on disposable CockroachDB, including service-present and default missing-service inputs. Run focused frontend tests, lint/typecheck/build and affected session/tenant regressions.
- [x] 2.2 Perform focused mutation/sensitivity checks for changed logic: incorrect sum/group or rounding, omitted tenant predicate, bypassed period/group validation, and stale frontend response acceptance. Reuse existing mutation/deferred-response coverage where effective; require semantic failures, with no broad matrix, new mutation dependency or arbitrary count target.
- [x] 2.3 Reviewer checks the scoped diff, contract compatibility and focused evidence; resolve findings before QA.
- [x] 2.4 QA verifies approved acceptance on / and /overview-legacy, desktop/mobile and tenant transitions, including honest missing/savings/demo states and the existing conflict scenario's warning/no ambiguous amounts/no replacement boundary. Present evidence for separate final human approval.

Task 2.3: independent review PASS; inherited Medium RF-026-002 is explicitly
deferred by Paris on 2026-09-27, outside JUP-026, for review before P1. Task 2.4:
real browser smoke passed and QA verified the evidence; its documentary
reevaluation returned PASS_WITH_APPROVED_EXCEPTIONS after that approval.
Whole-page mobile acceptance remains limited by the unfixed finding.
Final human approval was given on 2026-09-28. Publication, CI, team PR review,
validation and JUP-026 integration remain separate; none is implied by checked tasks.

## Reuse And Handoff

Reuse processor test_azure_cost_ingestion.py, test_azure_cost_normalized_schema.py
and test_azure_cost_cockroach_integration.py for input/schema/idempotency;
they do not prove the new backend SQL. Reuse frontend session/dashboard,
tenant-transition and existing mutation tests; adapt only billing expectations.
Report actual unique collected/executed cases and skips after approval, with no
invented executed count. Keep backend/processor test processes separate.

Primary owns spec-1 guard, corepack pnpm openspec:validate and
corepack pnpm jup:check -- --change jup-026-azure-cost-kpis.
The original planning phase ran no product tests or fixtures; subsequent
execution and validator results are recorded in the linked evidence.
