# JUP-026 Validation

Date: 2026-09-27. [Official card](https://trello.com/c/anUswta8).
[Proposal and approval](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/proposal.md),
[design](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/design.md),
[review](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/review.md),
[ADR-0010](../adr/ADR-0010-azure-cost-source-overlap.md).

## PR52 Corrections 2026-09-30

Current local result: functional checks and independent technical review PASS;
QA PASS_WITH_APPROVED_EXCEPTIONS; final human approval APPROVED by Paris Arcos
on 2026-09-30 ("apruebo el resultado"). Paris separately authorized publication
and checking CI with "subelo"; no merge is authorized. This section supersedes historical current
status below, not the dated evidence. Paris approved the three corrections and
local develop incorporation with "hazlo por favor" on 2026-09-30.

Tested identity: `feat/JUP-026-azure-cost-kpis`, merge HEAD
`9bab4059adb1e04bc4cfe9096f4b979cb16c9cca` plus the four-file product/test diff.
Parents are proposal commit `38f3e45` and develop `2efef1a`. Only backlog.md
needed manual merge resolution; all previous finding rows and all three
RF-098 rows survive unchanged, the latter exactly once. The frontend api.ts
merge combines the two nonoverlapping changes. Independent review verified both.

| Acceptance | Observed result |
|---|---|
| Case-insensitive resource group, deterministic label | Real SQL combines Shared/shared in sub-a EUR as Shared, 12.01, two records; swapping their stored spelling leaves the result unchanged. Other subscriptions/currencies and missing dimensions remain separate. |
| Ingestion-equivalent tag keys | CostCenter/costcenter/cost_center resolve to cost_center; Environment/spaces/env and cost_centre/org aliases match ingestion. Stored Prod/prod and other value-case pairs remain separate. Unknown canonical keys retain null groups. |
| Invalid controls and empty canonical key | URL-decoded NUL, tab, LF, unit separator and DEL return 422 with zero billing reads, before normalization; empty canonical keys also return 422. Validation uses a read spy, not SQL execution. |
| Existing frontend accepts the canonical response | Bounded check through the existing consumer: CostCenter -> cost_center and Environment with a leading space -> environment accepted; empty response key rejected. Three checks PASS, network stubbed, not a browser acceptance run. |

Commands used Python 3.12.13 and installed workspace tools, without installing
dependencies. From apps/backend, with PYTHONDONTWRITEBYTECODE=1:

```text
python -B -m pytest tests/test_billing_summary.py -q -ra -p no:cacheprovider --basetemp <unique-temporary-directory> --junitxml <receipt.xml>
python -B -m pytest tests -q -ra -p no:cacheprovider --basetemp <temporary-regression-directory> --junitxml <receipt.xml>
```

Focused runs set JUP086_COCKROACH_TEST_URL to the owned loopback-only port 55841
on CockroachDB 24.1.11, container jup026-review-20260930-crdb. It uses an in-memory
store, no volumes, and organization marker processor-integration-tests. Fixtures
verify isolation and create/drop their own database. No shared data, clock or
runtime credentials changed; the fixture timeout remains 60 seconds.

- Before test edits: 15 PASS. Adapted tests before the fix: 4 FAIL/11 PASS,
  zero errors/skips, covering all three defects and canonical unknown-key echo.
- After the two-module fix: 15 PASS/0 SKIP, including seven real SQL cases.
  Reused cases add seven invalid-input selections, nine tag-key selections and
  the label swap assertion: no new collected cases, not zero new assertions.
  The JUP-026 permanent delta stays 19 cases (15 backend, four frontend).
- Focused runtime mutation: seven semantic faults detected, zero survivors;
  both surrounding baselines 15 PASS/0 SKIP. Faults cover split groups, wrong
  label, casefold/alias loss, controls checked too late, DEL and empty-key
  acceptance. SQL faults use Cockroach; validation faults use read-spy assertions.
  All 689 repository file hashes were unchanged by this campaign.
- General backend regression: 329 PASS/17 SKIP, exit 0. This separate run omitted
  external-service configuration; seven skipped billing SQL cases are covered
  by the focused run above. The other ten skips are not claimed as passes.
- Frontend after develop integration: 265 PASS in 46 files, exit 0, using
  `node node_modules/vitest/vitest.mjs run --reporter=default --reporter=json`.
  All three `node node_modules/typescript/bin/tsc --noEmit` configurations
  (default, `-p tsconfig.node.json`, `-p tsconfig.test.json`),
  `node node_modules/eslint/bin/eslint.js src tests`, and
  `node node_modules/vite/bin/vite.js build` exit 0. Existing >500 kB bundle
  warning retained; no new frontend product or test edits in this correction.

Local raw receipts under TEMP (not repository artifacts):
`jup026-pr52-red-20260930-8159d81286654acd8fe7e14425aa5e81`,
`jup026-pr52-green-20260930-3c637a5d231249f593ab1da3c6fcc2ae`,
`jup026-pr52-mutation-20260930-fcebf17d917d4dca95ef9623dd02a5ed`,
`jup026-pr52-backend-20260930.xml`, `jup026-pr52-frontend-20260930.json`.
Mutation results.json records each exact invocation and JUnit failure; matching
hashes establish the reviewed tree. Initial sandbox Python/dependency read
failures were rerun successfully with approved access, not counted as Red.

Independent technical review: REVIEW_PASS, no introduced blocker, no file edits.
Read-only QA verified the receipts and four tested file hashes, returned
PASS_WITH_APPROVED_EXCEPTIONS with only the existing RF-026-002 mobile deferral,
and passed its no-change guard. Fresh strict OpenSpec 35/35, all eight JUP
traceability checks, hygiene 689 files, 16 current local links, diff check and
entry-to-QA DoD passed. No product checks were relabelled as fresh QA runs.
The owned in-memory Cockroach container was removed after verifying its ID,
ownership label and absence of mounts. Test receipts remain locally available.
No fresh browser, RabbitMQ/pgvector, processor/Azure suite, remote CI or human
reapproval claimed. Lucia's 29/09 review/validation remains attributable only to
c1e7f7f. RF-098-002 retries remain Open; RF-026-002's approved mobile deferral
and RF-014-002's broader Unicode limitation are unchanged. The official card
link, PR participation confirmation and human re-review are pending. The approved
result is authorized for publication; this record does not claim remote CI success.

## Scope And Identity

Branch: `feat/JUP-026-azure-cost-kpis`. Historical validation base:
`847fa3cf5857f33e680089b25dbffd149e5a15ac`, the approved local combination of
JUP-086 `1c866cc` and JUP-014 `b1aef6e`. Validation used an uncommitted diff;
this base SHA alone does not identify that tested work. Local validation
snapshots retain the file fingerprints, preserved when packaging the changes
for the authorized publication below. No remote CI success, merge, deployment,
tracker update or operational closure is claimed by these local results.

Historical integration HEAD on 2026-09-28 was `4eb942720e3baf6ed05c4fb5dfa0dff87d83b77a`, after
the authorized merge of develop `d244278` (merged PR47/JUP-086) into `d86eb4e`;
see [merged dependency reconciliation](#merged-jup-086-develop-reconciliation).
Both JUP-014 and JUP-086 dependencies are incorporated. The prior source fix
integration remains recorded under [source fix synchronization](#jup-086-source-fix-synchronization).
The prior develop `65fcd6b` merge is recorded under [JUP-014 synchronization](#jup-014-synchronization).
The local merge is not a merge of JUP-026 into develop or a publication.

Nine approved product files changed (one opening comment only). Permanent
test delta: **19 cases, 15 backend and four frontend**, plus adaptations of
existing billing expectations. Inherited dependency tests are not new JUP-026
tests. Mutation and browser checks below add no permanent cases.

Acceptance: real Azure totals by currency and five groupings, UTC half-open
periods, exact decimal strings, tenant isolation, explicit missing/empty states,
unavailable savings, conservative overlap warning without amounts or writes,
and minimal executive/legacy consumers. Ingestion replacement, full dashboards,
savings calculation, dependencies and migrations remain excluded.

## Red And Green

Initial Red: backend 8 FAIL/8 SKIP; frontend 6 FAIL/1 PASS. The seven new SQL
cases were not executable then; no SQL Red is claimed. Once Paris started
Docker, all nine previously skipped focused integration cases executed.

| Validation | Observed result | Exit |
| --- | --- | --- |
| Focused billing and tenant API, real CockroachDB | 24 PASS, 0 SKIP; 13.71 s | 0 |
| Full backend, same isolated database | 338 PASS, 5 SKIP; 91.29 s | 0 |
| Full frontend | 239 PASS in 39 files, 0 SKIP; 48.97 s | 0 |
| Frontend typecheck, lint, build | PASS; existing large-chunk warning retained | 0 each |
| Processor regression | 323 PASS, 49 SKIP; 14.75 s | 0 |
| Simulated Azure API regression | 59 PASS, 0 SKIP; 0.78 s | 0 |
| Repository Node tools | 91 PASS | 0 |
| Collaboration tooling | 12 PASS | 0 |
| Strict OpenSpec / active traceability | 35/35 / 12 changes PASS | 0 each |
| Hygiene / corpus / validation questions | PASS; 668 files before these reports; 28 questions, seven categories | 0 each |
| Diff whitespace check | PASS | 0 |

Backend skips are four RabbitMQ and one pgvector cases without those unrelated
services. The untouched processor's 49 opt-in Cockroach/vector cases were not
enabled. These skips are not successful integrations. Corpus/question validation
does not execute LLM answers. The existing frontend bundle warning remains
(745.30 kB, gzip 213.73 kB); it was not corrected by JUP-026.

Python 3.12.13 used the existing temporary validation environment. From each
Python app's directory, the native command was `python -B -m pytest -q -ra
-p no:cacheprovider --basetemp <unique-temp-dir>`; backend runs also emitted
JUnit with `--junitxml <temp-file>`. Focused backend added
`tests/test_billing_summary.py tests/test_tenant_isolation_api.py`.
`PYTHONDONTWRITEBYTECODE=1`; backend integration additionally set
`JUP086_COCKROACH_TEST_URL=cockroachdb+psycopg://root@127.0.0.1:60058/defaultdb?sslmode=disable`.
This URL is only for the disposable, insecure, loopback-bound test instance.

From `apps/frontend`: `corepack pnpm test`, `corepack pnpm typecheck`,
`corepack pnpm lint`, `corepack pnpm build`. From repository root:

```text
openspec validate --all --strict --no-interactive
node tools/jup-check.mjs --all
node tools/jup-cleanup-check.mjs
node --test tools/*.test.mjs
node tools/assistant-corpus.mjs validate
node tools/validation-questions.mjs validate
python -B -m unittest discover -s tools/collaboration/tests -v
git diff --check
```

OpenSpec used the existing installed executable and `OPENSPEC_TELEMETRY=0`.
No dependency or lockfile changes. SQL logs/JUnit remain locally in TEMP
`jup026-green-sql-2-focused-6d1e6a0eea18494e8a7b2ae54fd0d1bb` and
`jup026-green-sql-2-full-55030d9b0af34251b33fc3db9d6f75ee`.

## Focused Mutation

Ten non-equivalent faults were detected: round-before-sum, half-even rounding,
lost subscription identity, lost tenant scope, inclusive period end, bypassed
overlap, equal-period acceptance, invalid group/tag combination, lost frontend
query identity and stale placeholder acceptance. Existing assertions detected
wrong values/statuses, not merely setup failures.

One equivalent survivor removes only `r.tenant_id=:tenant_id`. The remaining
`i.tenant_id=:tenant_id` and inner join `i.tenant_id=r.tenant_id` still imply it.
No uncovered behavioral survivor or mutation exception is claimed. This is a
focused risk sample, not a comprehensive mutation-score percentage.

Initial API mutants hit unsupported SQLite SQL (500); those runs were excluded.
A temporary adapter returned the existing fixture summary from its billing spy;
unchanged assertions then demonstrated incorrect 200 versus required 422.
Baselines before/after: backend 15 PASS, controlled API 7 PASS, frontend 5 PASS;
zero skips/errors. All 668 repository file hashes stayed unchanged.

Supplementary local reports are in TEMP `jup026-mutation-runtime-20260927`:
`MUTATION-HANDOFF.md`, `backend-results.json`, `api-controlled-results.json`,
`frontend-results.json`, exact substitutions in `*-mutation.json`, and
`unchanged-verification.json`. Temporary runner command: `mutation.ps1 -Phase`
`Backend`, `ApiControls`, `Frontend`, then `Verify`; each report records the
native commands, working directories, exit codes and logs. Local runners are
not repository artifacts or production tooling.

## Real Browser Acceptance

Original API and lifespan, real CockroachDB, current frontend source and existing
Vite configuration; no monetary-response mocks. Playwright/Chromium ran at
1440x1000 and 390x844: **15 temporary smoke checks PASS**, no page errors,
12 accepted state screenshots plus two diagnostic screenshots.

Observed exact EUR 9.01, GBP 0.00 and USD 9007199254740993.01, current UTC month
and June 2024, all five groupings, credits, null/case/subscription distinctions,
zero versus empty, tenant B EUR 42.42, late-response isolation, unavailable
savings and real 409 warnings in both views without live amounts/replacement
controls. Demo content stays separate. Unused broker/vector health is degraded;
billing still renders. The 64 API requests and 38 billing responses include
retries/selections and are not additional test cases. Only login used POST.

Changed content fits both viewports; mobile table scrolls inside its container.
**Whole-page mobile visual acceptance is not PASS:** unchanged shared header/nav
extends to 1026 px on a 390 px screen. [RF-026-002](../../openspec/findings/backlog.md#rf-026-002)
records the inherited limitation and Paris's approved deferral on 2026-09-27.
The finding stays Open for review before P1, without a fix. Layout has no
diff against the base; removing only main content leaves identical overflow.
This is not a full historical-app replay. No shared-shell repair is included.

Supplementary reports in the same TEMP directory: `BROWSER-HANDOFF.md`,
`browser-results.json`, `browser-shell-comparison.json`, `browser-unchanged.json`
and desktop/mobile PNGs for current-partial, June-tag, empty, overlap and legacy
partial/overlap. Commands: `node browser-acceptance.cjs`,
`node browser-visual-boundary.cjs`, `runtime.ps1 -Action Fingerprint`,
`runtime.ps1 -Action Stop`, `browser-boundary.ps1 -Phase After` (all exit 0).
An initial selector timeout was a temporary automation error; only its corrected
rerun is accepted. Primary inspected desktop/mobile screenshots.

## Isolation, Review And Remaining Gates

Only `jup026-crdb-20260927` was created: project-pinned CockroachDB 24.1.11,
in-memory store, no mounts, SQL on loopback, no shared services or clock changes.
Browser seed contained 22 cost records/five runs; before/after hashes matched.
All 668 repository hashes matched across browser validation. Temporary API,
frontend and browser helpers are stopped; their ports 8026/5196 are released.
After QA confirmed it needed no further database inspection, the owned container
was stopped and auto-removed; a filtered Docker listing confirmed it absent.
Only container `cd578dd57ab01dd2dbc8c9f66fff1e3193c862128d9fa2f2b705a417967659e9`
was targeted, after verifying its validation label, image, no mounts and memory
store. Its synthetic database is gone; no shared data was affected. The
pre-existing preview on 5187 was untouched and is not the live-API acceptance.

Two incomplete packages in the temporary Python environment were reinstalled
offline at the same versions (h11 0.16.0, websockets 16.1.1, no dependencies).
The original API then started normally. This was not a product defect or a
dependency upgrade; initial failure logs are retained, not counted as tests.

Independent technical review: **REVIEW_PASS**, no introduced in-scope blocker;
19-case coverage considered sufficient. Sequential role guards pass. QA examined
the evidence without changing files: initial **QA_FAIL** for missing human
disposition of RF-026-002, not a cost-implementation failure. Paris subsequently
approved its deferral on 2026-09-27 ("si, aplazalo en un finding"); documentary
QA reevaluation returned **PASS_WITH_APPROVED_EXCEPTIONS**, superseding that
initial FAIL. Paris gave the separate post-QA approval on 2026-09-28, including
ADR-0010, now Accepted; see the approval update below. Existing findings/gaps remain
open where integration or unrelated capabilities are outstanding.

QA reran strict OpenSpec (35/35), all traceability (12), hygiene (670 files),
`git diff --check 847fa3cf5857f33e680089b25dbffd149e5a15ac` and the entry-to-QA
DoD check, all exit 0. Initial Corepack sandbox permission failures were setup
failures; the installed OpenSpec executable passed via
`node node_modules/@fission-ai/openspec/bin/openspec.js validate --all --strict --no-interactive`.
QA verified source/test fingerprints against browser receipts and checked 75
local link targets; only the already-broken JUP-097 change-directory link was
missing. A stale browser-review sentence in the gap map was then synchronized;
this documentary correction adds no test/code work or new product blocker.

Following explicit RF-026-002 deferral, read-only QA rechecked approval/status
coherence, strict OpenSpec (35/35), JUP-026 traceability and entry-to-QA DoD,
all PASS; guard confirmed no changed paths. The exception is precisely the
inherited mobile shell overflow, still Open/Medium/unfixed and scheduled for
review before the P0-to-P1 transition, without an assigned delivery date or JUP.
No functional tests, mutation, runtime or technical review were repeated.
QA passes with that approved exception, not with global mobile visual acceptance.

## Develop Synchronization

On 2026-09-27 Paris explicitly requested incorporation of teammates' develop
merges before the PR. `git fetch origin` confirmed local/remote develop at
`d9271fdb7c0236b43511759c35fca109984c264d` (zero divergence). The incoming commits
are `0bc2e04` (PR44, CORS finding closure) and `d9271fd` (PR45, JUP-085 archive
and spec promotion), both documentary. No application, tests, dependencies,
tooling or CI changed in this synchronization.

Local work was preserved with an include-untracked stash, retained as
`41b58196bf37f9ba7be9039bbdecb0f9b70c5ca4`. `git merge --no-edit origin/develop`
created `4eace5f071abd2c9eff940d2ef13b251fa34dc7b`, with parents `847fa3c` and
`d9271fd`; subsequent stash apply restored all 32 local files without conflicts.
31 files were byte-identical to the pre-merge fingerprints. The only difference,
backlog.md, contains exactly the two incoming CORS closure rows; local findings,
including RF-026-001/002 and their dispositions, are preserved. No paths were
lost or added by restoration, and the index has no unmerged entries.

Observed exit 0: ancestry checks for develop and the old local base, empty
`git diff 847fa3c HEAD -- apps packages pnpm-lock.yaml package.json tools .github`,
`git diff --check`, strict OpenSpec 35/35, all active JUP traceability 11/11,
and hygiene 671 files. One active JUP became an archived change with a promoted
spec, explaining the count change. Independent bounded review: REVIEW_PASS.
Prior functional, mutation and browser evidence remains applicable by unchanged
source/test identity; those executions were not repeated on the new merge SHA.

At that 2026-09-27 checkpoint, JUP-086 `1c866cc` and JUP-014 fix `b1aef6e`
were in local ancestry but not yet included in fetched develop. Reconcile dependencies before
presenting a JUP-026-only PR diff. RF-026-002's approved exception and publication
restrictions are unchanged. The then-pending human/ADR approval was subsequently
given as recorded below. No push or PR.

## Final Human Approval

On 2026-09-28 Paris Arcos explicitly approved the final result, including
ADR-0010, while clarifying that integration of JUP-086 and the JUP-014 fix is
not his individual pending action. The exact reply and scope are recorded in
[review.md](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/review.md#post-qa-human-approval).
These were team dependencies at approval time; they need not prevent preparing a dependent PR,
but its inherited scope must be identified and reconciled before final merge.
This update only records approval, changes no code/tests or acceptance outcomes,
and does not authorize publication, external tracker changes, merge or archive.

## JUP-014 Synchronization

On 2026-09-28 Paris explicitly requested incorporation of develop with merged
JUP-014. Fetch confirmed `65fcd6bb146cb9655e133ea177697f7c5e592fd7` (PR48).
Clean local develop advanced to that commit using `git merge --ff-only
origin/develop`. The JUP-026 branch then merged it as
`795a981f66382d8bd14b373e43ff96d0921d68e0`, parents `4eace5f` and `65fcd6b`.

There were no conflicts and no merge content changes: both old and new HEAD
trees are `f050a72ae14226a88213599df81f19b9b52ddef3`. The existing local JUP-014
fix and JUP-086 adaptations were retained. A fresh include-untracked stash,
`0295b25483c2979982af3bc4064b07de66d442b4`, remains available; all 32 local
files were restored byte-identically, without missing or added paths.

Ancestry verification confirms origin/develop is now included; local develop
and origin/develop have zero divergence, and no unmerged entries remain.
The earlier review, QA exception, functional evidence and human approval are
preserved on identical product/test content. No new tests, mutations, runtime
or technical review were necessary or claimed for this ancestry-only merge.
Only this metadata update follows it. **JUP-014 is no longer a pending
dependency; JUP-086 remains pending integration into develop.** No push or PR.

## JUP-086 Source Fix Synchronization

Paris requested "ok lleva los cambios a la rama de la jup-026" on 2026-09-28.
Fetch showed exactly one incoming commit, `57fac34c557df9988c3dabb264525f0acd664d80`.
It rejects blank ingestion source before side effects, adds three inherited
regression cases and records RF-086-004/005. Its [CI run](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/36409569470)
passed seven checks before synchronization; this is not CI for JUP-026.

The local merge is `d86eb4e17dffdcff4c3510490bb27df4bffd85ea`, parents
`795a981f66382d8bd14b373e43ff96d0921d68e0` and `57fac34`. No cherry-pick,
rebase, force-push or merge into develop. The working implementation remains
uncommitted. Backup of all 32 local files and include-untracked stash
`935fa36d8b59e682c9948382ab61d39bc1239112` are retained.

Before metadata updates, 30 files restored byte-identically. The tenant API
test merged automatically; only findings had a conflict, resolved by retaining
all four RF-026-001/002 and RF-086-004/005 rows verbatim. The original and
restored local deltas of those two files have identical `git patch-id --stable`
with `git diff --unified=0`: `0daa98d0feb3c93ca4e2729c073c5106cbcdf276`.
The source commit and incoming merge delta likewise both produce
`189fcb3dc62ab8cd872ff84c1b97db60a753ce8c`. No unresolved entries remain;
all local changes are unstaged as before. The first automated boundary check
could not resolve this worktree inside the sandbox and was not a PASS; Git
patch identities and backups establish conflict preservation. The later
metadata-only boundary check uses authorized worktree access.

Full backend regression on the merged working tree: **329 PASS, 17 SKIP,
0 FAIL/ERROR**, exit 0, 67.85 seconds, 346 collected cases. Thirteen skipped
cases require CockroachDB, three RabbitMQ and one pgvector. No services were
started or new tests written; the three extra cases belong to JUP-086, not
the 19-case JUP-026 delta. Frontend, real-service and browser tests were not
repeated; no fresh whole-stack QA or mutation result is claimed.

From `apps/backend`, using the existing Python 3.12 environment:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$out = 'C:/Users/Trabajo/AppData/Local/Temp/jup026-sync-jup086-a8de569f37c143de9eb77a97a76e9bef'
& 'C:/Users/Trabajo/AppData/Local/Temp/jup086-20260924-0031895a-py312/Scripts/python.exe' -B -m pytest tests -q -ra -p no:cacheprovider --basetemp "$out/pytest-backend" --junitxml "$out/backend.xml"
```

`backend.log`/`backend.xml`, `before.json`, file copies and `restoration.json`
remain in that TEMP directory. Final checks: `corepack pnpm openspec:validate`
35/35, `corepack pnpm jup:check -- --change jup-026-azure-cost-kpis` and
`git diff --check` all exit 0; metadata boundary check passes for four documents.
No publication, PR, tracker update, closure or
archive. JUP-086/PR47 still needs human re-review and merge into develop.

## Merged JUP-086 Develop Reconciliation

On 2026-09-28 Paris requested "ok reconcilia develop con la 026 por favor".
Fetch confirmed develop `d244278c5560fe57ef4b433fc212eb491968d5e1`, the merged
[PR47](https://github.com/EconomiconFinOps/tfm-economicon/pull/47). Local develop
already matched it and the fast-forward check reported "Already up to date".
The JUP-086 remote branch had been deleted; develop was fetched successfully.

JUP-026 merge `4eb942720e3baf6ed05c4fb5dfa0dff87d83b77a` has parents
`d86eb4e17dffdcff4c3510490bb27df4bffd85ea` and `d244278`. Before, incoming and
merged trees all equal `00b400a0420f02660c243c647eb39384bf8712ba`: this records
ancestry, not a new product change. All 32 local files (20 tracked changes,
12 untracked files) were backed up and restored byte-identically. The full
1,234-line tracked patch also matches; the index is empty and no conflicts
remain. Stash `850d43fb34d327e372677ec22469bbafa9638ef8` and the local backup
`jup026-merged086-sync-4f497d5d357540e290356622d5080022` in TEMP are retained.

An independent bounded review verified these identities and returned
REVIEW_PASS; its guard recorded no changed paths. The only subsequent edits
update proposal, tasks, review and this evidence. Earlier dependency-pending
statements are historical: both dependency PRs are now integrated. Existing
functional/mutation/browser evidence and the RF-026-002 deferral are retained
with their original limits; no functional suites or services were started,
and no new tests or fresh whole-stack acceptance are claimed. Initial local
permission failures were retried with authorized access, not counted as passes.

JUP-026 remains local and uncommitted apart from its integration history.
No push, PR, Trello update, merge into develop or OpenSpec archive was performed.

Read-only documentary QA on Windows, 2026-09-28, recorded:

- `corepack pnpm openspec:validate`: 35/35 PASS, exit 0 after an authorized retry
  of an initial Corepack cache permission failure; no repair or installation.
- `node tools/jup-check.mjs --all`: 11/11 active changes PASS, exit 0.
- `node tools/jup-cleanup-check.mjs`: 671 files PASS, exit 0.
- `git diff --check`: PASS, exit 0; 36 local links including 19 fragments resolve.
- Entry-to-QA DoD: PASS, zero missing/invalid events or artifact errors.
- Snapshot/guard: 32/32 files unchanged during QA. Against the pre-merge backup,
  28/32 remain byte-identical and only the four metadata documents differ.

Verdict: PASS_WITH_APPROVED_EXCEPTIONS, limited to synchronization, retaining
the existing RF-026-002 deferral. These result notes do not change code or the
reviewed contract and do not establish the team's human review or validation.

## Publication Authorization

Paris authorized commit, push, PR against develop and CI verification on
2026-09-28: "abre pr y mira a ver si pasa el CI". The final local DoD passed
with no missing/invalid events or artifact errors. This publication packages
the already reviewed implementation without new functionality or tests.
CI results must be read from the resulting PR/run for its exact commit;
they are not inferred from these historical local runs. Merge, archive and
Trello updates remain separately authorized operations, and required human
review/validation are not credited by this publication.

## Archivo y cierre documental (06/10/2026)

El PR #52 se integró en develop el 30/09/2026 (`1e897dc`). El change se archiva el 06/10/2026 en [2026-10-06-jup-026-azure-cost-kpis](../../openspec/changes/archive/2026-10-06-jup-026-azure-cost-kpis/review.md#human-approval), con la aprobación humana de Lucia registrada, y sus specs quedan promovidas a `openspec/specs/azure-cost-kpis/` y `openspec/specs/frontend-api-layer/`. Los enlaces a la ruta del change activo se han apuntado a la ruta archivada. Siguen abiertos RF-026-001 (diferido) y RF-026-002 (aplazamiento aprobado). La validación funcional atribuible y la revisión de otros miembros se siguen registrando en Trello. La ejecución de archivo no repite pruebas de producto.
