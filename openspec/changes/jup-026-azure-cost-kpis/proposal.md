JUP: JUP-026
Trello: https://trello.com/c/anUswta8

## Why

JUP-026 requires total Azure cost and cost by subscription, resource group,
service, project and tag. At the starting baseline, normalized fields existed,
but /billing/summary and the executive frontend contained fixed KPI values.

## What Changes

- Extend GET /billing/summary with period and one selected SQL breakdown.
  Proposed v2 returns per-currency decimal strings, missing-data states and
  savings_identified: null. No new endpoint.
- Connect the existing executive / total and five-dimension selector/table;
  retain /overview-legacy compatibility. This minimal frontend scope (option 2)
  is accepted below; exact paths are in [design](design.md).
- Retain the proposed conservative 409 ambiguous_cost_source response without
  ambiguous monetary results. The accepted MVP frontend warns of possible
  overlap, with no replace/confirm action or ingestion overwrite.

Excluded: full JUP-055/five-dashboard integration, consumption quantities,
recommendations, anomalies, budgets, savings engine, multi-cloud, active inventory,
time series, source replacement/confirmation, new dependencies, migrations,
infrastructure or auth controls.
The external plan step 5 (line 1232) is backend-only; the minimal frontend
extension is now explicitly accepted as option 2 in the scoped decision below.
That initial scoped acceptance alone did not authorize coding; the subsequent
full pre-code approval is recorded below.

## Capabilities

### New Capabilities

- azure-cost-kpis: scoped totals/five groupings and period/money/missing-data rules.

### Modified Capabilities

- frontend-api-layer: executive/legacy billing consumption with honest states
  and existing session/tenant isolation.

## Impact

The change includes the approved product paths, focused tests, the existing
OpenSpec documents and [RF-026-001](../../findings/backlog.md#rf-026-001).
After verified implementation, update only
evidenced total/executive-C2 rows in the JUP-097 gap map; savings-unavailable
does not deliver a savings engine. Retain remaining gaps and existing findings;
never close RF-091-003/RF-095-002 globally. Tasks are [here](tasks.md).

ADR: [ADR-0010](../../../docs/adr/ADR-0010-azure-cost-source-overlap.md)
(Accepted, Paris Arcos, 2026-09-28) records the durable conservative cost-source
overlap policy. Final human approval is recorded in
[the post-QA gate](review.md#post-qa-human-approval). Technical review passes;
RF-026-002 deferral is approved.
The current QA result is recorded in [review.md](review.md).
The stacked base includes ADR-0001 through 0009, including JUP-086's 0008/0009.
No existing decision or approval is changed.

## Source Baseline And Risks

- Original validation base: 847fa3cf5857f33e680089b25dbffd149e5a15ac on
  feat/JUP-026-azure-cost-kpis, combining JUP-086 1c866cc and JUP-014 b1aef6e.
  Initial preparation used develop 3a1001db857191f7abb6bb025e2fe8b04a50fe56.
- Current integration HEAD: 4eb942720e3baf6ed05c4fb5dfa0dff87d83b77a, after the
  user-authorized merge of develop d244278 on 2026-09-28. PR47/JUP-086 is now
  integrated in develop, including the source fix already present locally.
  Both JUP-014 and JUP-086 dependencies are incorporated. This ancestry-only
  merge changes no committed content; all 32 local files were restored
  byte-identically before these metadata updates. No scope expansion or
  publication of JUP-026. See [synchronization evidence](../../../docs/evidence/JUP-026-validation.md#merged-jup-086-develop-reconciliation).
- Official scope: historical 26/09 export, CawMVPoy - economicon (26-09).json,
  card anUswta8. Official live get failed; no live official verification claimed.
  The orchestrator directly read private mirror https://trello.com/c/R85OnDmu
  through the Trello connector on 27/09/2026 and confirmed it matches the export.
  Operational roles/status remain in Trello without reassignment.
- At the original 2026-09-27 checkpoint, primary verified both dependencies
  open/unmerged: [PR47](https://github.com/EconomiconFinOps/tfm-economicon/pull/47)
  at 1c866cc3c66e967199871cd1cefd0cc8364f1f8a, run 36280350957, seven successful
  checks; [PR48](https://github.com/EconomiconFinOps/tfm-economicon/pull/48)
  at b1aef6e0001d0cfdf4732b4f94a8baa9e9db7099, run 36314531995, seven successful
  checks. Neither result establishes corrections in current develop.
- Default ResourceId + ResourceGroup ingestion may omit service_name; report
  missing coverage, never infer service names. Different query definitions
  create different ingestion IDs and can retain the same charges twice; see
  the bounded conflict proposal in design.

## Scoped MVP Decisions

On 2026-09-27 Paris Arcos explicitly accepted "ok para el MVP avisar" and
"opcion 2 me parece correcto":

- Option 2: a minimal real executive dashboard with total(s), period and one
  table selectable across the five groupings, retaining /overview-legacy
  compatibility. Full dashboards, time series and exports remain excluded.
- Possible source overlap: warn in the frontend, without replacement,
  confirmation or overwrites. Retain the proposed conservative 409 and no
  ambiguous monetary result; a warning does not authorize summing overlaps.
  GET /billing/summary remains read-only.
- Defer confirmed replacement of ingestion sources to
  [RF-026-001](../../findings/backlog.md#rf-026-001). It expands ingestion and
  requires a separately agreed scope before implementation; it is not a
  JUP-026 blocker provided the warning/no ambiguous sums acceptance is met.

Those initial scoped decisions did not constitute full pre-code approval.
Paris subsequently approved the full contract and tests/implementation in the
explicit confirmation recorded below. Ingestion replacement remains excluded.

## Pre-Code Review

Initial planning validation recorded on 2026-09-27: strict OpenSpec 35/35 PASS,
`node tools/jup-check.mjs --change jup-026-azure-cost-kpis` PASS and
`node tools/jup-cleanup-check.mjs` PASS (641 files), all exit 0.
The initial traceability check found missing `.openspec.yaml`; spec-planner
added the required metadata and the rerun passed. Both role guards passed;
six planning files and two local links checked without errors. These are
documentary checks, not product tests, technical review or final QA.

### Authorized Branch Base

On 2026-09-27 Paris explicitly requested JUP-026 to branch from JUP-086
because develop does not yet contain it. The unpublished JUP-026 branch had
no commits of its own and was advanced directly from 3a1001d to 1c866cc,
without rewriting history or changing develop/the original JUP-086 branch.
All six proposal files retained identical SHA-256 hashes across that move.
This authorizes the alternate dependency base only, not the proposed contract,
new tests, implementation, publication, merge, tracker updates or PR48 inclusion.
JUP-014's repair remains a separate prerequisite. Before a later PR to develop,
reconcile with the eventual JUP-086 integration, especially after squash, so
inherited work is not presented as new JUP-026 scope.

Revalidation on the stacked base: strict OpenSpec 35/35 PASS, JUP-026 traceability
PASS and repository hygiene 664 files PASS, all exit 0. Billing summary's
existing method/contract are unchanged by the inherited branch; no functional
change to the proposal was required. No new product tests were run.

### Local PR48 Integration And Pre-Code Approval

On 2026-09-27 origin was refreshed and PR48 verified open at
b1aef6e0001d0cfdf4732b4f94a8baa9e9db7099. The local merge into JUP-026
completed as 847fa3cf5857f33e680089b25dbffd149e5a15ac with parents
1c866cc3c66e967199871cd1cefd0cc8364f1f8a and b1aef6e0001d0cfdf4732b4f94a8baa9e9db7099.
Product/tests merged without conflicts. Restoring the local finding conflicted
only at the end of backlog.md; both RF-014-002/003 and RF-026-001 were retained.
Backup stash e5e3c4f103a7f7552ac63b68162e2d58c64a7c25 remains available.
Develop and the original branches are unchanged; no remote publication or
merge into develop occurred, and this does not claim team validation of PR48.

The initial approval-record write was blocked because the user's reply ended
as a question. No tester/coder was dispatched on that ambiguous reply. Paris
then explicitly confirmed: "Si, apruebo el contrato y autorizo las pruebas y
la implementacion" in response to the complete contract confirmation question.

Pre-code approval: **APPROVED**, Paris Arcos, 2026-09-27. Recorded at
13:53:53 +01:00 (recording time, not an inferred message timestamp).
Approval covers response-v2 exact per-currency strings and null compatibility
with coordinated consumers; final two-decimal rounding; UTC current-month
default and selectable half-open dates; explicit empty/partial states and null
savings; conservative possible-overlap 409 for multiple completed sources of
one tenant/subscription/date, including its disclosed disjoint-input limitation;
and minimal option-2 executive frontend with legacy compatibility.

Tester/coder may proceed sequentially on the existing design's paths, with
focused reused coverage. Ingestion replacement, broader dashboards, new
dependencies/migrations, publishing, external tracker changes, merge into
develop and archive remain excluded. Any scope/contract change requires a new
explicit decision; this approval does not waive final review or QA.

JUP-086 and PR48 are now present in the local combined base; their merges
into develop remain separate. Do not duplicate either correction. The combined
base passed strict OpenSpec 35/35, JUP-026 traceability and hygiene 664 before
tester/coder handoff. No JUP-026 product tests or implementation had run at
the time of the approval record above.
External plan/card updates have separate authorization and remain pending;
no tracker was changed during this preparation.

## Initial Execution Checkpoint 2026-09-27

Implementation is local and incomplete in validation, not ready for closure.
Tester added 19 cases (15 backend, 4 frontend) and adapted existing coverage;
inherited JUP-014/JUP-086 cases are not counted as new. Red was demonstrated:
backend 8 FAIL/8 SKIP, frontend 6 FAIL/1 PASS. The prior backend baseline was
7 PASS/2 SKIP. Seven new SQL cases have not run, so no SQL Red is claimed.

Coder changed eight approved product files. Available checks reported:
- Backend focused billing/tenant API: 15 PASS/9 SKIP, exit 0.
- Frontend five affected suites: 158 PASS, no skips, exit 0.
- Frontend typecheck, lint and build: exit 0; bundle-size warning retained.
- Diff check and tester/coder role guards: PASS; no manifest/lockfile changes.

Docker is stopped. Starting it and a disposable isolated CockroachDB was
requested separately and remains pending. Nine skipped backend cases require
CockroachDB: seven new SQL cases and two existing cases. SQLAlchemy binding
inspection is not SQL execution. Full Green, mutation, independent technical
review, browser desktop/mobile acceptance and QA remain pending; no waiver or
completion is claimed. Resume with real SQL validation, then the remaining
sequential gates. Frontend preview was started locally on 127.0.0.1:5187;
HTTP 200 alone does not validate the backend or authenticated KPI workflow.

## SQL And Mutation Checkpoint 2026-09-27

This checkpoint supersedes the initial Docker/SQL blocker above. Paris started
Docker and requested continuation. An isolated, disposable CockroachDB 24.1.11
instance, using the project's pinned image, ran with an in-memory store and a
loopback-only SQL port. No shared data, clocks or production configuration changed.

- Focused billing/tenant API: 24 PASS, zero skips, including all nine previously
  skipped cases; full backend: 338 PASS, five unrelated RabbitMQ/pgvector skips.
- Full frontend: 239 PASS; typecheck, lint and build PASS, retaining the existing
  bundle-size warning. Processor: 323 PASS/49 opt-in integration skips;
  simulated Azure API: 59 PASS. These are existing regressions, not new tests.
- Focused mutation: ten non-equivalent faults detected, one equivalent survivor
  explained by the remaining tenant predicate and inner join. Baselines before
  and after pass. Initial API failures caused by unsupported SQLite cost SQL
  were excluded; controlled reruns prove the expected 422 versus faulty 200.
- The permanent test delta remains 19 cases: 15 backend and four frontend.
  Product/test hashes were unchanged during mutation; no behavior fix was needed
  for real SQL acceptance. The demo module received only a comment correction.

The [JUP-097 gap map](../../../docs/planning/JUP-097-frontend-data-gap-map.md)
now distinguishes local real totals/dimension breakdowns from remaining demo
charts, inventory and unavailable savings. Related findings remain open with
the local progress distinguished from integration or team acceptance.

Real-API browser acceptance reports 15 temporary smoke checks PASS and zero
page errors on desktop/mobile. Independent technical review is REVIEW_PASS,
with no introduced in-scope blocker and no request for more permanent tests.
The inherited mobile shell overflow is [RF-026-002](../../findings/backlog.md#rf-026-002),
explicitly deferred by Paris on 2026-09-27 for review before P1; whole-page
mobile visual acceptance is not claimed.
See [review](review.md) and [evidence](../../../docs/evidence/JUP-026-validation.md).
QA verified the evidence and native gates; its initial QA_FAIL concerned only
the then-missing disposition of inherited Medium RF-026-002. Paris now approves
deferral outside this JUP ("si, aplazalo en un finding"); reevaluation is recorded
in review.md. No new product defect or additional tests were requested.
At this 2026-09-27 checkpoint, final human approval remained pending; Paris
subsequently gave it on 2026-09-28 as recorded in review.md.
This checkpoint does not authorize publication, tracker changes, merge,
source replacement or archival.
ADR-0010 was Proposed at this checkpoint and is now Accepted under that approval.
