# JUP-051: Local CI Validation

- Trello: https://trello.com/c/MklqbF5b
- Date: 2026-10-01. Branch: `ci/JUP-051-ci-pipeline`.
- HEAD/base: `1e897dc278c5ac99b0fc3d5e9008702038bec121`, plus working diff.
- Executor: automated local tooling under Paris's implementation approval,
  not Alejandro's review or Lucia's functional validation.
- Local checks passed; hosted runs, human reviews and final approval pending.
- [Proposal](../../openspec/changes/jup-051-ci-pipeline/proposal.md) and
  [review](../../openspec/changes/jup-051-ci-pipeline/review.md).

Fetch succeeded before implementation with no newer develop commits. PR #56
remained open at `cd535fc79d39a4ad59f58ce04d32adae7d094e48` on recheck;
JUP-100 was not imported or duplicated. JUP-050 remains with the teammate.

## Tested Scope

Six workflow lines add branch pushes and mandatory Python compilation. Two new
workflow tests (8 -> 10), one strengthened existing assertion and README coverage
documentation complete the implementation. No application code, dependencies,
lockfile, `.gitconfig`, hooks, Docker runtime, rulesets or APIs changed.

SHA-256 of tested raw working-tree files:

| File | SHA-256 |
| --- | --- |
| `.github/workflows/ci.yml` | `EBF29BD27C4A87E0BCAA0A3AA3DAA288169365BA09A027BC0750C1D41CD4518A` |
| `tools/ci-workflow.test.mjs` | `29092D4C9A22B6E93EFAD8D556ACF9EFBDBC16727AE67AB7A4996DE71EBFCCD7` |
| `README.md` | `63E8930EAA799D0B5932C26B0F86276D53D4F575D41BA48A825745DE8A195304` |

## Environment And Commands

Windows PowerShell, Node 22.23.3, pnpm 9.0.0, existing isolated Python 3.12.13.
CI uses Ubuntu, Node 22 and Python 3.12: local success is not a hosted Ubuntu
run or proof of identical Python dependency resolution. No real-service opt-ins.

```powershell
$nodeBin = 'C:/Users/Trabajo/AppData/Local/npm-cache/_npx/52027bd8fc0022aa/node_modules/node/bin'
$pythonBin = 'C:/Users/Trabajo/AppData/Local/Temp/jup086-20260924-0031895a-py312/Scripts'
$env:PATH = "$nodeBin;$pythonBin;" + $env:PATH
```

Node 22 was prepared with `npm exec --yes --package=node@22 -- node --version`
in npm's cache, not as a project dependency. Corepack cache/Python trampoline
access needed authorized execution outside the sandbox; those failures were not
test failures or meaningful Red. Initial frontend lint lacked a locally installed
`typescript-eslint`; `corepack pnpm install --frozen-lockfile` repaired the local
installation and the unchanged lint command passed. Manifests/lockfile unchanged.

| Application command/check | Observed result, exit 0 |
| --- | --- |
| `corepack pnpm lint --filter=@finops/frontend` | PASS, uncached |
| `corepack pnpm test --filter=@finops/frontend` | 265 passed, 46 files |
| `corepack pnpm --filter @finops/frontend build` | PASS, 2479 modules |
| `corepack pnpm --filter @finops/frontend typecheck` | PASS, three TS projects |
| `python -m compileall -q app` in all three Python service directories | 3/3 passed |
| Azure Cost API pytest | 59 passed |
| Backend pytest | 329 passed, 17 skipped, 594 warnings |
| Processor pytest | 323 passed, 49 skipped, 322 warnings |

Python tests ran from each respective service directory with:

```powershell
& "$pythonBin/python.exe" -B -m pytest tests -q -ra -p no:cacheprovider --basetemp "$env:TEMP/jup051-SERVICE-20261001"
```

`SERVICE` was `azure-api`, `backend` or `processor`. Existing suites were not
expanded: 976 application cases passed, with 66 real-service cases skipped.

Every governance command below ran using `corepack pnpm SCRIPT`:

| Script | Observed result, exit 0 |
| --- | --- |
| `ci:check:test` | 10 passed |
| `jup:check:test` | 7 passed |
| `pr:check:test` | 11 passed |
| `roadmap:test` | 5 passed |
| `repository:governance:test` | 5 passed |
| `jup:check:all` | 9 active changes linked and complete |
| `jup:cleanup:test` | 6 passed |
| `jup:cleanup:check` | 694 paths initially; 696 after adding evidence/review |
| `assistant-corpus:test` | 8 passed |
| `assistant-corpus:validate` | Valid manifest |
| `validation-questions:validate` | 28 questions, 7 categories |
| `validation-questions:test` | 8 passed |
| `llm-gateway:test` | 6 passed |
| `docker:validate` | 27 static tests, no daemon |
| `collaboration:test` | 12 passed |
| `openspec:validate` | 36 passed, 0 failed |

Tooling adds 105 passing test cases, including the two new cases. Combined:
1081 passed and 66 skipped, excluding repeated control runs, mutations and
non-test validators. `git diff --check` passed.

## Red, Green And Mutation

`node --test tools/ci-workflow.test.mjs`: baseline 8/8; after test edits,
8 passes and two expected failures (absent push, zero compileall steps).
After the six-line workflow change: 10/10. Initial direct runs used default
Node 24; Green was repeated with Node 22 above.

Disposable-copy mutation commands used Node 22.23.3:
`node --test --test-reporter=tap tools/ci-workflow.test.mjs`.

| Mutation | Result |
| --- | --- |
| Green control | 10 passed, exit 0 |
| Remove push trigger | 9 passed, 1 failed, exit 1 |
| Remove compileall step | 9 passed, 1 failed, exit 1 |
| Compileall `continue-on-error: true` | 9 passed, 1 failed, exit 1 |

3/3 planned mutants detected, not a whole-repository mutation score. Logs remain
in `%TEMP%/jup051-mutation-1-uR4ZP2`. There, Python 3.12.13 compileall returned 0
for `syntax/valid` and 1 with `SyntaxError` for `syntax/invalid`. The tester
verified all 689 tracked file hashes and staged state unchanged. No broken commit
was published and no permanent product fixture was added.

## Acceptance And Remaining Gates

| Criterion | Expected and observed evidence |
| --- | --- |
| Automatic lint/tests/build on branch push | All-branch/no-tag/no-path-filter configuration tested; hosted scheduling pending |
| PR/manual behavior retained | Trigger, PR-only policy and concurrency assertions pass; remote runs pending |
| Python lint/build mandatory | Once per service, correct directory/order, failure not suppressed; actual syntax checks and invalid fixture pass |
| Existing controls retained | Frontend/Python suites, typecheck, governance, permissions and action-pin assertions pass |
| Tests/docs updated | Two new cases, README, Red/Green and mutations recorded |
| PR reviewed and functionally validated | Pending authorized publication and separate human reviews; internal agents do not substitute |

The 66 skips require isolated CockroachDB, RabbitMQ or pgvector. Existing JWT
test-key and SQLite adapter warnings remain; Vite warns about a 745.81 kB JS
chunk. No application changes were made to silence warnings. Compileall is syntax
and bytecode checking, not style lint or packaging.

Duplicate push/PR runs and superseded-run cancellation are approved limits.
Only the pushed head is tested, not every intermediate/offline commit. After
publication authorization, capture push/PR event, ref, SHA, run/job links and
results, including skipped versus executed JUP policy. Hosted CI, remote
protections, deployment, human acceptance and closure are not claimed.

Live Trello read still failed. Assignments come from the official export: Paris
leads, Victor pairs, Alejandro reviews, Lucia validates. Confirm current roles
and actual participation before publication. No tracker write, commit, push, PR,
merge or archive occurred during this implementation phase.

## Local QA Closeout

Read-only QA Raman returned QA_PASS with no blockers or exceptions. QA verified
all three implementation hashes, mutation logs and local gate records; reran
workflow tests (10), OpenSpec (36), traceability (9), hygiene (696 paths) and
diff checks. These reruns are not additional unique tests in the totals above.
Its stale design-wording observation was corrected in documentation only.
Local QA does not replace the remaining hosted runs or human review/validation.
