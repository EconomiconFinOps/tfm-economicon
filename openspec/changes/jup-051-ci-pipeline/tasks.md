JUP: JUP-051

Pre-code human approval was granted by Paris on 2026-10-01; see the proposal.
Assignments and actual review participation are described in [proposal](proposal.md);
unchecked items are technical deliverables, not a duplicate operational backlog.

## 1. Specification Gate

- [x] 1.1 Orchestrator validates this change with `corepack pnpm openspec:validate`, `corepack pnpm jup:check -- --change jup-051-ci-pipeline` and the existing spec-planner boundary guard; present scope and limits for explicit human approval before tests/code.

## 2. Focused Implementation After Approval

- [x] 2.1 Extend existing `tools/ci-workflow.test.mjs` assertions for branch-only push, retained PR/manual triggers, PR-only policy, unchanged concurrency and exactly one mandatory Python compileall step with matrix working directory before pytest; reuse existing coverage and demonstrate Red (8 pass, 2 expected failures via direct Node because Corepack cache access was restricted).
- [x] 2.2 Add `push.branches: ['**']` and `python -m compileall -q app` once per Python matrix job in `.github/workflows/ci.yml`; preserve existing jobs, check names, permissions, cancellation, tests and skip behavior.
- [x] 2.3 Add a focused README CI section with commands, pushed-head semantics, cancellation/duplicate runs, Python syntax-only lint/build and real-service coverage limits; leave governance docs and JUP-050/JUP-100 work untouched.

## 3. Local Verification And Review

- [x] 3.1 Demonstrate Green with `corepack pnpm ci:check:test`; run applicable CONTRIBUTING checks and per-service compileall/pytest with Python 3.12, recording exact commands, revision, results, skips and any baseline/environment limitations.
- [x] 3.2 In a disposable directory outside the checkout, verify compileall returns zero for valid syntax and nonzero for invalid syntax; confirm focused assertions detect removal of the push trigger or masking/removal of the compileall step. Use no new dependency or product fixture.
- [x] 3.3 Review the scoped diff and acceptance evidence, then validate the scenarios separately; local reviewer and QA passed. Actual human review/validation and hosted runs remain pending in section 4. PR #56 remained open; if it lands, reconcile the overlapping test file and repeat affected checks/review/validation without importing unrelated work.

## 4. Remote Acceptance After Explicit Publish Approval

- [ ] 4.1 After separately authorized publication, record push and PR CI event/ref/SHA/run links and actual results, including push policy skip, PR policy execution, existing job coverage and any cancellations or duplicates; do not claim remote success from local tests.
- [ ] 4.2 Obtain separate human `Revision JUP-051` and `Validacion JUP-051` reviews under the applicable process, with acceptance-to-evidence mapping and at least the syntax-failure edge case; present final QA for explicit human approval. Publication does not authorize tracker updates, merge or archive.
