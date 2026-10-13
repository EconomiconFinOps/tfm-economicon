JUP: JUP-051

## Estado actualizado — 2026-10-05

La entrega está en [PR #58](https://github.com/EconomiconFinOps/tfm-economicon/pull/58),
rama `ci/JUP-051-ci-pipeline`, head `1a83c1d862de12c85f0ed36f6a465065d70bef82`,
con `develop c3aa9d68690ae718aecf1bee2f08cd25eb5f704f` incorporado.
Se aplica `CONTRIBUTING.md`, proceso 2026-09-30 (JUP-100).
La tarjeta oficial consultada el 05/10 asigna liderazgo a Paris Arcos Martin,
pairing a Victor Mendez y revisión y validación a Lucia Mateo, con excepción
acordada en Trello el 02/10 y declarada en la PR. Las asignaciones no acreditan
por sí mismas participación realizada.

Esta regularización conserva el alcance y el comportamiento implementados.
Expediente archivado el 05/10/2026 en la entrega de la misma PR; tres requisitos y ocho escenarios promovidos a la especificación consolidada.
La autorización de Paris para corregir el archivado consta el 05/10.
Paris aprobó el cierre documental y ordenó el archivado el 05/10. DoD local final PASS antes del archivo. No se ha integrado la PR.

Las reviews históricas de Lucia y las ejecuciones remotas están enlazadas en
[la evidencia](../../../../docs/evidence/JUP-051-validation.md#actualizacion-del-2026-10-05).
La actualización desde develop añadió tres controles de retrieval al workflow
y sus aserciones. Su revalidación humana incremental sigue pendiente antes de
integrar, aunque la CI actual sea correcta.

## Registro histórico — 2026-10-01

El contenido siguiente describe la preparación original, incluidos roles, hashes,
resultados y pendientes de esa fecha. No representa el estado actual de la PR.
Se conserva íntegra la aprobación pre-code y no se atribuyen nuevas ejecuciones
a los agentes ni a las personas que participaron entonces.

## Context And Decisions

Planning baseline: `ci/JUP-051-ci-pipeline`, HEAD and local `origin/develop`
`1e897dc278c5ac99b0fc3d5e9008702038bec121`. Reuse the existing YAML parser and
Node test suite. The additive `repository-governance` delta extends JUP-079's CI
contract; frontend quality/type requirements stay unchanged.

Add only this event alongside the existing events:

```yaml
push:
  branches:
    - '**'
```

There are no branch exclusions or path filters. According to
[GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
defining only branch filters excludes tag pushes, and multiple matching events
can create multiple runs. Keep PR branches `main`/`develop` and current activity
types, `workflow_dispatch`, and `pr-policy.if` restricted to `pull_request`.
Push/dispatch therefore skip JUP policy without requiring PR metadata.

Preserve `contents: read`, pinned actions, checkout credential handling, job
names, and concurrency group `ci-${{ github.workflow }}-${{ github.ref }}` with
`cancel-in-progress: true`. Branch and PR refs normally use separate groups, so
duplicate push/PR runs are an accepted cost. No deduplication logic is proposed.
Protected branches remain protected; triggering CI does not authorize a push.

## Existing Python Lint And Build

Each of `apps/azure-cost-api`, `apps/backend` and `apps/processor` declares
identical lint/build scripts: `python -m compileall app`. Add one step named
`Check Python syntax (lint/build)` to `python-tests`, after dependency installation
and before pytest, with the existing matrix working directory and command
`python -m compileall -q app`. Quiet mode changes output, not failure handling.
The step and job must not mask failures with `continue-on-error`, conditional
skips or shell success fallbacks. A syntax failure must fail that matrix job.

This uses the existing Python 3.12 setup and standard library, with no manifest
or dependency changes and no duplicate lint/build execution. It checks syntax
and emits bytecode in the disposable runner; it does not check style, imports at
runtime, package artifacts or container images. Implementation validation on
Python 3.12.13 confirmed exit 0 for valid syntax and exit 1 for an invalid
temporary fixture; see the [evidence](../../../../docs/evidence/JUP-051-validation.md).

## Focused Tests And Documentation

After pre-code approval, extend `tools/ci-workflow.test.mjs` using its parsed
workflow, existing assertions and package-manifest reads. Cover the all-branch,
no-tag/no-path-filter trigger, retained PR/manual triggers, PR-only policy and
unchanged concurrency. Add one focused Python step contract assertion for
exactly one compileall invocation per matrix entry, correct working directory,
ordering before pytest and mandatory failure propagation; confirm the package
lint/build scripts remain identical. Reuse existing permissions, names,
frontend and governance coverage without introducing a second test framework.

Demonstrate Red before editing CI and Green afterward. After approval, verify
`python -m compileall -q app` returns 0 for valid code and nonzero for an invalid
syntax fixture in a disposable directory outside the checkout using Python
3.12. Do not alter product files to inject failure or add a permanent fixture
suite for the Python standard library. Report interpreter and observed exits.

Document triggers, commands and limits in README only. Preserve pytest's
existing skips for absent isolated CockroachDB, RabbitMQ and pgvector services.
Record executed/skipped counts and reasons; green CI does not prove those real
integrations, Docker startup, deployment or human acceptance.

## Validation And Coordination

The orchestrator runs `corepack pnpm openspec:validate` and
`corepack pnpm jup:check -- --change jup-051-ci-pipeline`, plus its existing
snapshot guard. These passed during planning and were repeated after implementation;
see the evidence and review artifacts for observed results. After implementation,
run `corepack pnpm ci:check:test` and applicable `CONTRIBUTING.md` checks; record
baseline failures separately and do not repair unrelated behavior in JUP-051.

Only after explicit publish approval, verify a branch-head push run and a PR
run against develop, preserving manual dispatch. Record event, ref, head SHA,
job results and URLs, checking PR policy skips on push and runs on PR. Static
tests cover tag exclusion and cancellation configuration; remote evidence is
needed to establish actual hosted execution. Do not publish deliberate broken
commits or tags for validation. Current handoff reports no JUP-051 PR or remote
branch; remote validation remains pending.

PR #56 changes `tools/ci-workflow.test.mjs` but not `ci.yml` per the handoff.
Do not import it now. If it lands before integration, reconcile the shared test
file with the updated base, preserve both changes and repeat affected tests,
review and validation. It is coordination, not a prerequisite to this proposal.
Refresh process/head/base evidence before human reviews under the proposal's
process contract. Do not reconcile unrelated governance documentation.

## ADR And Escalation

No ADR: this wires existing checks to another event in the existing platform,
without a durable architecture change, dependency, migration or security-policy
change. There is no unresolved product decision in the supplied scope. Escalate
if implementation needs any of those changes, broader coverage or role/process
reconciliation. Archive-order clarification belongs to a separately authorized
archive action and does not authorize an early archive here.
