JUP: JUP-051
Trello: https://trello.com/c/MklqbF5b

## Why

The card requires automatic lint, tests and build on every commit. At develop
`1e897dc278c5ac99b0fc3d5e9008702038bec121`, CI runs on pull requests and manual
dispatch but not branch pushes. The three Python packages define both lint and
build as `python -m compileall app`; CI currently runs their pytest suites only.

Scope and P0 priority come from the supplied Trello export
`CawMVPoy - economicon (6).json`; live connector access is denied. This is a
source snapshot, not verification of current tracker status or participation.

## What Changes

- Add `push.branches: ['**']` to the existing CI workflow, excluding tag-only
  pushes and retaining pull-request and manual triggers.
- Run `python -m compileall -q app` once per existing Python matrix job as a
  mandatory step, covering the identical package lint/build commands.
- Retain frontend lint/tests/build, frontend type checking, Python tests,
  governance, permissions, check names and cancellation behavior.
- Extend the existing workflow tests minimally and document actual CI coverage,
  trigger semantics and limits in a focused README section after approval.

Here, every commit means the head delivered by a branch push. Offline commits
and every intermediate commit in a multi-commit push are not separately tested.
Superseded runs may cancel; an open PR can produce both push and PR runs.
Python compileall is syntax/bytecode checking, not style lint or packaging.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- repository-governance: add branch-push CI and existing Python lint/build
  coverage. Reuse the capability introduced by active JUP-079, which is not yet
  in `openspec/specs/`; the delta adds uniquely named requirements and does not
  rewrite JUP-079 or its approvals.

## Impact And Exclusions

This planning phase writes only this OpenSpec change. Proposed later paths are
`.github/workflows/ci.yml`, `tools/ci-workflow.test.mjs` and a focused `README.md`
section. No product changes, new dependencies, Python lint toolchain, Docker
build/smoke, deployment, migration, ruleset/policy changes or JUP-100 review
workflow implementation. JUP-050 stays with its teammate. Existing static
`docker:validate` remains; it is not a container build or runtime smoke test.
Service-dependent skips remain visible and do not prove real-service coverage.
The stale Frontend tests bullet in governance documentation is outside scope;
PR #56 already edits that document.

## Process And Human Gate

Apply current unversioned `CONTRIBUTING.md` and the locally adopted
2026-09-30 JUP-100 process. The handoff reports
[PR #56](https://github.com/EconomiconFinOps/tfm-economicon/pull/56) OPEN at
`cd535fc`; neither merged policy nor remotely activated rules are inferred.
Export assignments: leadership Paris Arcos Martin; pairing Victor Mendez;
review Alejandro Aguado; validation Lucia Mateo. Actual participation is pending.

Required human deliverables are separate `Revision JUP-051` and
`Validacion JUP-051` GitHub reviews: first favorable submission COMMENT,
second APPROVE toward develop when both are satisfactory and no blocker remains.
Reviewer/validator do not commit or push fixes; internal verdicts are not human
approval. Publication and remote verification require explicit publish approval.

Pre-code human approval: **APPROVED** by Paris Arcos Martin on 2026-10-01;
recorded at 2026-10-01T09:34:27Z. Paris approved the scope and then explicitly
requested implementation of the complete JUP-051 plan. This authorizes the
focused tests, workflow changes and documentation described above.
OpenSpec validation passed (36 items), traceability and the spec-planner guard
passed before approval. Final QA/human approval, publication, tracker writes,
merge and archive remain separate gates; none is granted here.
