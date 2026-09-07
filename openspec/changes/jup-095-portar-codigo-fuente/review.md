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

Pendiente al momento de escribir esta sección — se completa en el mismo grupo antes del commit final.
