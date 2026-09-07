JUP: JUP-095
Trello: https://trello.com/c/G4FPtBdE/87-jup-095-portar-el-c%C3%B3digo-fuente-del-frontend-de-economicon
Rama: `feat/JUP-095-portar-codigo-fuente`

Documento vivo: se actualiza al cerrar cada grupo de `tasks.md`, no solo al final de la tarjeta.

## Grupo 1 — Gate pre-código y línea base

Doc-only, sin código de producto: sin tester/coder/mutación (excepción documentada en
`.claude/harness/mutation.md`).

- Línea base confirmada antes de tocar nada: 49 violaciones de `react/prop-types` en 9 `.jsx`; bundle
  `203.37 kB` JS / gzip `63.38 kB`, CSS `5.60 kB`; 14 archivos en `src/**`; 7 checks obligatorios en
  CI, ninguno de pruebas de frontend.
- Commit: `89b83ba`.

## Grupo 2 — Runner de pruebas

### 2.1–2.2 (setup, sin comportamiento propio)

- Instalado Vitest + Testing Library + jsdom como devDependencies. El resolutor trajo
  `vitest@5.0.0`, incompatible con el Vite 5 fijado en JUP-094 (exige `vite ^6/^7/^8`) — mismo patrón
  recurrente que `typescript@7` (JUP-093) y `react-router@8` (JUP-094). Fijado `vitest@3.2.7`
  explícito, cuya dependencia regular declara `vite: "^5.0.0 || ^6.0.0 || ^7.0.0-0"`.
- `vite.config.ts`: `defineConfig` importado de `vitest/config`, `test.environment: "jsdom"`,
  `test.setupFiles: ["./src/test/setup.ts"]`. Script `test` → `vitest run`.
- `typecheck` y `build` verificados en verde; bundle sin cambio.
- Commit: `771bb0b`.

### 2.3 — Primer ciclo Red/Green real del frontend

**Objetivo de la tarea:** demostrar de punta a punta que el arnés (Vitest + Testing Library + jsdom)
funciona, con un componente canario de infraestructura (no una pantalla de negocio), y confirmar que
un test fallido detiene la verificación con estado de error.

**Red** (tester, commit `1070a3e`): `apps/frontend/src/test/HarnessSmoke.test.tsx` — importa
`HarnessSmoke` desde `./HarnessSmoke` (inexistente) y consulta
`screen.getByRole("status", { name: "Entorno de pruebas del frontend operativo" })`. Evidencia Red:

```
Error: Failed to resolve import "./HarnessSmoke" from "src/test/HarnessSmoke.test.tsx". Does the file exist?
 Test Files  1 failed (1)
      Tests  no tests
ERR_PNPM_RECURSIVE_RUN_FIRST_FAIL  @finops/frontend@0.1.0 test: `vitest run`
Exit status 1
```

Fallo por el motivo correcto (resolución de módulo, no configuración rota); código de salida 1,
satisfaciendo el escenario "Una prueba fallida detiene la verificación" de
`specs/frontend-typescript-tooling`.

**Green** (coder, commit `a03aa76`): `apps/frontend/src/test/HarnessSmoke.tsx` —
`<p role="status" aria-label="Entorno de pruebas del frontend operativo">`. El coder corrigió un
supuesto incorrecto de mi encargo: el nombre accesible de `role="status"` es `nameFrom: author`
(WAI-ARIA), no se deriva del texto — verificado empíricamente antes de fijar el `aria-label`.
Evidencia Green: `Test Files 1 passed (1)`. `typecheck` sin errores. `lint`: 49/49 sin violaciones
nuevas.

**Mutación** (Stryker efímero vía `pnpm dlx`, acotado a `src/test/HarnessSmoke.tsx`): 1 mutante
generado, 1 matado, 0 supervivientes, **score 100%**. Receta real documentada en
`.claude/harness/mutation.md` tras tres correcciones sobre lo escrito originalmente ahí (sintaxis de
`pnpm dlx --package=` en pnpm 9.0.0, `typescript` fijado explícito para el preprocesador de
`tsconfig` de Stryker, `plugins: ["@stryker-mutator/vitest-runner"]` explícito porque el
descubrimiento automático no ve el sandbox efímero).

**QA — hallazgo y remediación:** primer veredicto `changes-requested`. QA reprodujo la mutación de
forma independiente y detectó que `.stryker-tmp/` (carpeta temporal de Stryker) quedaba en disco tras
la corrida y que Vitest la recogía como archivos de test propios (`Test Files 1 failed | 2 passed`),
contaminando en silencio el conteo de la suite — el `.gitignore` protege el commit pero no el
descubrimiento de archivos de Vitest. Fix (coder, no commiteado como tarea de test): en
`vite.config.ts`, `test.exclude: [...configDefaults.exclude, "**/.stryker-tmp/**"]`, preservando los
excludes por defecto en vez de sobrescribirlos. Verificado por mí y de forma independiente por QA,
simulando el escenario exacto (sandbox falso con copia real del test): `Test Files 1 passed (1)`.
**Veredicto final QA: `accept`.**

**DoD:** `node .claude/harness/check-dod.mjs` falla por `RF-093-001` (preexistente, documentado desde
JUP-093: turbo resuelve pnpm 11.9.0 en subprocesos en esta máquina Windows, afectando también a
`@finops/backend`/`@finops/processor`, ajenos a esta tarea). El escaneo de secretos del propio script
sí pasa (no depende de turbo). Sustituido por `corepack pnpm --filter @finops/frontend
{test,lint,typecheck}`, los tres en verde.

**Findings de esta tarea:** ninguno nuevo abierto contra `openspec/findings/backlog.md` — el
descubrimiento de `.stryker-tmp` se resolvió dentro de la propia tarea, no queda deuda pendiente.

## Grupo 2 — 2.4/2.5 (CI y ruleset)

**Objetivo:** cerrar la excepción al ciclo Red/Green que arrastraban JUP-093 y JUP-094 (el frontend
no tenía test runner) y, además, hacer que ese runner corra en CI y bloquee merges — mismo patrón que
JUP-093 aplicó a *Frontend type check*.

**Descubrimiento relevante:** existe un test real y ya commiteado que valida exactamente `ci.yml` y
los rulesets — `tools/ci-workflow.test.mjs` (introducido en JUP-093). No son tareas doc-only: tienen
comportamiento testeable propio, distinto del de `apps/frontend`.

**Bloqueo de proceso y su resolución.** El hook `.claude/hooks/lock-committed-tests.mjs` bloquea
cualquier escritura sobre un archivo de test ya tracked en git, sin distinguir agente (el propio
comentario del hook explica por qué: no hay forma fiable de verificar identidad desde un hook). Como
`tools/ci-workflow.test.mjs` está commiteado desde JUP-093, el tester no podía extenderlo para el
octavo check. El tester **no rodeó el hook** por su cuenta (nada de `git rm --cached`, ediciones vía
Bash fuera de las tools, ni tocar `.claude/settings.json` sin autorización) y escaló la decisión.
Se presentaron tres opciones al usuario (editar manualmente, desactivar el hook temporalmente, omitir
TDD para estas tareas); **Victor eligió desactivar el hook temporalmente**. Se vació
`.claude/settings.json` a `{"hooks": {}}`, el tester aplicó las dos aserciones nuevas, y el hook se
reactivó **antes** de la fase Green (para que el test recién extendido quedara protegido en cuanto se
commiteara). `.claude/settings.json` no está versionado (`.claude/` en `.gitignore`), así que esta
manipulación fue puramente local y efímera — no dejó rastro en el repo. Verificado de forma
independiente por QA.

**Red** (tester, commit `f07367d`): dos aserciones nuevas en `tools/ci-workflow.test.mjs` —
`workflow.jobs["frontend-tests"].name === "Frontend tests"` y `"Frontend tests"` añadido al array
`expected` del `deepStrictEqual` exhaustivo de checks obligatorios. Evidencia Red: 5 pass / 2 fail,
ambos por el motivo correcto (`workflow.jobs["frontend-tests"]` es `undefined`; el array de rulesets
reales no incluye `"Frontend tests"`).

**Green** (coder, sin commitear aún al escribir esta sección): job `frontend-tests` en
`.github/workflows/ci.yml`, copiado al pie de la letra del patrón de `frontend-typecheck` (mismo
runner, timeout, `actions/checkout`/`actions/setup-node` pineados por el mismo SHA,
`persist-credentials: false`); solo cambia el último paso a `corepack pnpm --filter @finops/frontend
test`. `{ "context": "Frontend tests" }` añadido como último elemento de `required_status_checks` en
`.github/rulesets/develop.json` y `main.json`. `docs/governance/github-branch-protection.md`
actualizado: check listado, motivo de por qué es obligatorio desde el inicio (sin baseline de deuda
que respetar, a diferencia del lint), y nota de activación pendiente por administrador. Evidencia
Green: `node --test tools/ci-workflow.test.mjs` → 7/7 pass.

**Mutación:** N/A — no hay código JS/TS de producto que Stryker pueda mutar (los cambios son
YAML/JSON de configuración declarativa); la cobertura de comportamiento la da el propio test
exhaustivo (`deepStrictEqual` sobre arrays completos, regex sobre SHAs pineados,
`persist-credentials`). Confirmado por QA como caracterización correcta, no como excepción forzada.

**DoD:** `node .claude/harness/check-dod.mjs` falla en `test`/`lint`/`typecheck` por `RF-093-001`
(mismo patrón que en la tarea 2.3, no relacionado con este cambio). Sustituido por: `node --test
tools/ci-workflow.test.mjs` (7/7); `corepack pnpm --filter @finops/frontend {test,lint,typecheck}`
para confirmar que el cambio de CI no rompió nada del paquete que sí toca (1 test pasa, lint 49/49 sin
regresión, typecheck limpio).

**QA:** `accept` en primera pasada. Verificó de forma independiente el hook reactivado, que ningún
otro test quedó tocado, los cuatro diffs, y la caracterización de mutación N/A.

**Findings de este grupo:** ninguno nuevo. La activación remota de *Frontend tests* en los rulesets
de GitHub queda pendiente como acción de administrador, documentada en
`docs/governance/github-branch-protection.md` junto al resto de checks versionados-pero-no-activados.

### Grupo 2 — cierre

F2 original quedó completa en JUP-093/JUP-094; este grupo 2 es interno a JUP-095 y cierra la
excepción al harness que ambas tarjetas dejaron documentada. **Commits del grupo:** `771bb0b` (setup
2.1-2.2), `1070a3e`/`a03aa76`/`2b1347c` (2.3, Red/Green/fix de QA), `f07367d` + el commit pendiente de
2.4-2.5 (Red/Green).
