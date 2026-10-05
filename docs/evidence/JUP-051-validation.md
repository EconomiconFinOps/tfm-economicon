# JUP-051: CI Validation

El registro original del 01/10 se conserva como evidencia histórica. Los hashes,
conteos y pendientes de aquella sección no son una ejecución del head actual.
El estado posterior está en [Actualización del 2026-10-05](#actualizacion-del-2026-10-05).

## Registro histórico del 2026-10-01

- Trello: https://trello.com/c/MklqbF5b
- Date: 2026-10-01. Branch: `ci/JUP-051-ci-pipeline`.
- HEAD/base: `1e897dc278c5ac99b0fc3d5e9008702038bec121`, plus working diff.
- Executor: automated local tooling under Paris's implementation approval,
  not Alejandro's review or Lucia's functional validation.
- Local checks passed; hosted runs, human reviews and final approval pending.
- [Proposal](../../openspec/changes/archive/2026-10-05-jup-051-ci-pipeline/proposal.md) and
  [review](../../openspec/changes/archive/2026-10-05-jup-051-ci-pipeline/review.md).

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

## Actualizacion del 2026-10-05

### Revision y alcance actual

- PR: [#58](https://github.com/EconomiconFinOps/tfm-economicon/pull/58).
- Rama publicada: `ci/JUP-051-ci-pipeline`; head `1a83c1d862de12c85f0ed36f6a465065d70bef82`.
- Base incorporada: `c3aa9d68690ae718aecf1bee2f08cd25eb5f704f` (`develop`).
- Proceso: `CONTRIBUTING.md`, 2026-09-30 (JUP-100).
- Fuente operativa consultada el 05/10: [tarjeta JUP-051](https://trello.com/c/MklqbF5b),
  P0, 40 En revisión. Paris lidera, Victor tiene pairing, Lucia revisión y
  validación, con la excepción acordada en la tarjeta el 02/10.
- Regularización exclusivamente documental; no modifica workflow, pruebas,
  README, dependencias ni producto respecto a ese head.

El Update branch del 05/10 incorporó `retrieval-labels:validate`,
`retrieval-labels:test` y `retrieval-calibration:test` al job OpenSpec y a
`tools/ci-workflow.test.mjs`. Conserva push por rama y compileall antes de pytest.
Los hashes de los tres archivos de implementación registrados el 01/10 son
históricos y no se presentan como los del head actual.

### Evidencia remota observada por coordinación

| Evento / referencia de entrega | Head de entrega | Ejecución | Resultado observado |
| --- | --- | --- | --- |
| pull_request, PR #58 desde ci/JUP-051-ci-pipeline hacia develop | 1a83c1d | [CI 37303424060](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37303424060) | 7 jobs correctos, incluido JUP policy |
| push, rama ci/JUP-051-ci-pipeline | 1a83c1d | [CI 37303417458](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37303417458) | 6 jobs correctos; JUP policy omitido |
| pull_request, PR #58 | 1a83c1d | [PR reviews 37303424084](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37303424084) | correcto |

El head identifica la entrega. No se confunde con un posible commit sintético
de checkout del evento pull_request. Los resultados se observaron en GitHub el
05/10; no son nuevas ejecuciones locales ni sustituyen la validación humana.

### Revision y validacion humanas publicadas

| Fecha UTC | Actor y alcance | Evidencia |
| --- | --- | --- |
| 02/10 | Lucia, revisión sobre eb91515, COMMENT sin cambios pedidos | [Revision JUP-051](https://github.com/EconomiconFinOps/tfm-economicon/pull/58#pullrequestreview-5389281875) |
| 02/10 | Lucia, validación sobre eb91515, APPROVE | [Validacion JUP-051](https://github.com/EconomiconFinOps/tfm-economicon/pull/58#pullrequestreview-5389283109) |
| 02/10 | Lucia, revalidación incremental sobre f6c072b, APPROVE | [Revalidación incremental](https://github.com/EconomiconFinOps/tfm-economicon/pull/58#pullrequestreview-5396631649) |
| 04/10 | Lucia, revalidación incremental sobre 6f4db85, APPROVE | [Revalidación tras Update branch](https://github.com/EconomiconFinOps/tfm-economicon/pull/58#pullrequestreview-5406806519) |

Coordinación leyó todas las reviews y comentarios generales; no constaban
comentarios inline pendientes. La última validación cubre `6f4db85`, no las
incorporaciones de retrieval en `1a83c1d`. Conserva como límite que
`local:test` dio 73/74 en el entorno de Lucia por puertos ocupados, mientras
el paso remoto pasó. No se presenta ese resultado local como 74/74.

### Criterios de la tarjeta y cobertura disponible

| Criterio oficial | Evidencia disponible / estado |
| --- | --- |
| Resultado funcional verificable | Runs push/PR actuales y validaciones enlazadas; compileall local correcto en tres servicios y caso inválido rechazado |
| Pruebas necesarias añadidas y en verde | Red/Green y mutaciones originales conservados; CI actual correcta y 12/12 tests workflow locales del Validador, sin sumar repeticiones a los totales históricos |
| Documentación y decisiones actualizadas | Expediente actualizado, alcance original conservado; revisión y validación locales favorables; archivo pendiente del gate humano final |
| Pull request revisado y vinculado | PR #58 enlaza la tarjeta y contiene Revision de Lucia; no hay cambios pedidos en esa review |
| Validación funcional y evidencia enlazadas | Reviews y evidencia enlazadas; revalidación humana de lo incorporado desde develop pendiente antes de merge |

### Preparacion del archivo

Se promoverán únicamente los tres requisitos y ocho escenarios ADDED de
`jup-051-ci-pipeline` a `openspec/specs/repository-governance/spec.md`.
La especificación consolidada aún no existe. El delta de JUP-079 permanece
fuera de esta regularización. Tras mover la carpeta se corregirán los enlaces
relativos afectados y se repetirán OpenSpec estricto, trazabilidad, higiene y
comprobación de enlaces.

La evidencia de comportamiento solo se reutiliza para archivos sin cambios
respecto al head probado. No se declaran ensayados los servicios reales
omitidos, despliegue, ejecución manual remota ni un fallo de sintaxis publicado.
La revisión y validación locales de esta preparación se documentan debajo.
La aprobación posterior de Paris y el cierre local final siguen pendientes
antes de ejecutar el archivo.

### Revision tecnica interna de la regularizacion

El 05/10, el Revisor interno devolvió REVIEW_PASS sobre head 1a83c1d más
los cinco documentos preparados. Node 22.23.3, comandos directos equivalentes a
los scripts de package.json:

| Comprobación local | Resultado observado |
| --- | --- |
| node --test tools/ci-workflow.test.mjs tools/repository-governance.test.mjs tools/retrieval-labels.test.mjs | 42/42, salida 0 |
| node tools/jup-check.mjs --all | 11 cambios, salida 0 |
| node tools/jup-cleanup-check.mjs | 817 archivos, salida 0 |
| node tools/retrieval-labels.mjs validate | 28 etiquetas, salida 0 |
| openspec validate --all --strict --no-interactive, CLI instalado | 45/45, salida 0 |
| git diff --check y enlaces Markdown locales/anchors | Correctos; 9 enlaces |

La invocación de Python 3.12 para calibración falló antes de ejecutar los tests
por permisos del lanzador; no es un fallo de la suite ni una ejecución pasada.
Se reutiliza la [ejecución remota de OpenSpec](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37303424060/job/111741316062),
donde el registro contiene 27 tests de calibración y job correcto, además de
74/74 en local:test. El checkout remoto de PR fue refs/pull/58/merge,
commit sintético 58de02d4c72fe2db18ca96aff11b26c74f6ceb1b, que combina head
1a83c1d y base c3aa9d6. No se confunde con el SHA de entrega.

El control independiente al retorno del Revisor confirmó estado de repositorio
y Git intacto. La incorporación de este informe solo cambia evidencia.

### Validacion local incremental — 2026-10-05

Validador interno, VALIDATION_PASS sobre 1a83c1d más el expediente preparado.
Los cinco criterios de la tabla anterior se comprobaron para este alcance
local; no se declara aceptación humana del head actual ni archivado realizado.

| Ejecución propia | Resultado |
| --- | --- |
| node --test tools/ci-workflow.test.mjs (Node 22.23.3) | 12/12, salida 0 |
| openspec validate --all --strict --no-interactive | 45/45, salida 0 |
| node tools/jup-check.mjs --change jup-051-ci-pipeline y --all | JUP-051 y 11 cambios correctos |
| node tools/jup-cleanup-check.mjs | 817 archivos correctos |
| Enlaces Markdown/anchors y git diff --check | 9/9 enlaces, diff correcto |
| Python 3.12.13: python -m compileall -q app en los tres servicios | 3/3, salida 0 |
| Fixture externo válido / inválido con el mismo compileall | Salidas 0 / 1; SyntaxError observado |

La invocación de Python con acceso autorizado funcionó. Emitió un aviso no
fatal _virtualenv.pth / ModuleNotFoundError: _virtualenv, conservado en los
registros; no fue necesario reparar el entorno para estos ensayos. No acredita
una nueva ejecución local de pytest ni calibración. La CI detallada aporta
la regresión de comportamiento conservado. No se han ejecutado servicios
reales, Docker, despliegue ni un commit remoto roto para esta regularización.

El Coordinador verificó el control original del Validador el 05/10 a las
12:08:41 UTC: estado de archivos y Git sin cambios durante el encargo.
La consolidación posterior modifica únicamente review, tasks y esta evidencia.
La aprobación local final de Paris continúa pendiente. El cierre documental
reutiliza Red/Green/mutación históricos, sin presentarlos como resultados nuevos.


### Archivado ejecutado — 2026-10-05

Paris aprobó el cierre documental tras los resultados internos y ordenó el archivado. El DoD local final pasó antes de mover el cambio. OpenSpec archivó jup-051-ci-pipeline en 2026-10-05-jup-051-ci-pipeline y promovió sus tres requisitos y ocho escenarios a repository-governance. Los apartados de preparación anteriores describen el estado previo a esta ejecución. La publicación de este cambio documental sigue pendiente; no se ha integrado la PR.
