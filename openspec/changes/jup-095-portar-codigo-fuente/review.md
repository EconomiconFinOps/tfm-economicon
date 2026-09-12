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
2.1-2.2), `1070a3e`/`a03aa76`/`2b1347c` (2.3, Red/Green/fix de QA), `f07367d`/`24427b5` (2.4-2.5,
Red/Green).

## Grupo 3 — Estilos, Tailwind y alias

**Objetivo:** cablear el sistema de estilos del origen sin activarlo todavía (`main.css` sigue
gobernando el render hasta que el grupo 6/7 reconcilie el entrypoint) y dejar el alias `@/` listo para
los primitivos de shadcn/ui del grupo 4.

### 3.1, 3.2, mitad de 3.4 — setup sin comportamiento propio testeable

- `apps/frontend/vite.config.ts`: plugin `tailwindcss()` de `@tailwindcss/vite` añadido junto a
  `react()` (mismo orden que el origen); `resolve.alias["@"]` apuntando a `./src`.
- `apps/frontend/src/styles/{tailwind,theme}.css`: copia literal del origen (verificada byte a byte
  por QA contra `../Economicon/frontend/src/styles/`, commit `1fe0030`). `fonts.css` (vacío) y
  `postcss.config.mjs` (stub innecesario con el plugin) **no** se copian.
- `apps/frontend/src/styles/index.css`: nuevo, importa `tailwind.css` + `theme.css`.
- `apps/frontend/tsconfig.json`: `paths`/`baseUrl` para el mismo alias `@/`.
- Verificado sin regresión: `build` (bundle idéntico, 203.37 kB JS / 5.60 kB CSS — nada consume aún
  las hojas nuevas), `typecheck` limpio, `dev` arranca.
- Commit: `10e63b3` (mezclado con el Red de 3.3, ver más abajo).

**Decisión de alcance sobre el alias (3.4):** se deja declarado en ambos sitios pero **sin
consumidor real** en este grupo. La prueba de resolución de extremo a extremo se difiere al grupo 4
(primer `@/lib/utils` real, primer componente de shadcn/ui). QA evaluó esta interpretación y la
confirmó razonable: coincide con la separación de slices del propio `design.md` (decisión 8) y evita
inventar un consumidor artificial solo para probar el alias antes de tiempo.

### 3.3 — Ámbito oscuro declarado (Red/Green real)

**Por qué es testeable y no config inerte:** a diferencia de 3.1/3.2, esto es una aserción concreta y
verificable sobre un archivo real (`index.html`), con un motivo técnico claro (`theme.css` solo activa
sus tokens oscuros bajo `.dark`) — se le dio el mismo tratamiento Red/Green que a HarnessSmoke.

**Red** (tester, commit `10e63b3`): `apps/frontend/src/test/index-html-dark-scope.test.ts` — lee
`index.html` del disco, aísla el tag `<html ...>` por regex, extrae su atributo `class` y verifica que
`dark` está entre las clases (parseado como conjunto de palabras, no `.includes` ingenuo). Evidencia
Red: `<html lang="en">` no tiene atributo `class`; `HarnessSmoke` sigue en verde (aislamiento
confirmado).

**Green** (coder): `index.html` — `<html lang="en">` → `<html lang="en" class="dark">`. Diff mínimo,
ningún otro atributo tocado. Evidencia Green: `Test Files 2 passed (2)`. `typecheck`, `build` (bundle
sin cambio, solo `dist/index.html` refleja el atributo) y `lint` (49/49) sin regresión.

**Mutación:** N/A para todo el grupo — 3.1/3.2 son config/CSS sin lógica JS/TS; 3.3 es un atributo
HTML estático; el alias de 3.4 es una entrada de objeto declarativa sin ramas. Ninguno tiene AST de
producto que Stryker pueda instrumentar. Confirmado por QA.

**QA:** `accept` en primera pasada, con verificación byte a byte de las hojas de estilo contra el
origen y confirmación de que `main.jsx` sigue intacto (3.5).

**Findings de este grupo:** ninguno nuevo.

### Grupo 3 — cierre

Commits del grupo: `10e63b3` (setup 3.1/3.2/mitad de 3.4 + Red de 3.3) y `774a4d2` (Green de 3.3,
`index.html`). Deja el sistema de estilos del origen y el alias listos, pero **inactivos** hasta que
el grupo 6/7 reconcilie el entrypoint; `main.css` sigue gobernando el render.

## Grupo 4 — Primitivos de shadcn/ui

**Objetivo:** portar el subconjunto de 6 paquetes Radix que
[ADR-0004](../../../docs/adr/ADR-0004-frontend-shadcn-ui.md) autorizó, con el primer consumidor real
del alias `@/` del grupo 3.

**Red** (tester, commit `5d27677`): 6 tests reales que fallaban porque el código de producto no
existía — `src/lib/utils.test.ts` (deduplicación de clases Tailwind en conflicto vía
`tailwind-merge`) y `src/components/ui/{label,separator,select,dialog,tooltip}.test.tsx`
(comportamiento ARIA real de cada wrapper: rol del separador según `decorative`, `role="combobox"`
del select, estado cerrado por defecto de dialog/tooltip). Evidencia Red: `6 failed | 2 passed (8)`.

**Green** (coder): copia literal del origen (`../Economicon/frontend/src/app/components/ui/`, commit
`1fe0030`) de `utils.ts` → `src/lib/utils.ts` y los 5 componentes → `src/components/ui/`, con una
única adaptación mecánica: `import { cn } from "./utils"` → `import { cn } from "@/lib/utils"` (en el
origen `utils.ts` vive dentro de `ui/`; en destino vive en `src/lib/`, siguiendo la convención
estándar de shadcn/ui que motivó el alias). Verificado por `diff` —por mí y por QA— que cada archivo
es idéntico al origen salvo esa línea. Sin archivo para `@radix-ui/react-slot`: ninguno de los 5
componentes lo importa, no hay bloque que portar.

**Hallazgo de infraestructura durante Green:** los dos `it()` de `separator.test.tsx` se contaminaban
entre sí (el primero dejaba su DOM montado, el segundo lo heredaba). Causa raíz: `@testing-library/react`'s
auto-cleanup depende de un `afterEach` global, y este proyecto usa `test.globals: false` desde el
grupo 2 (imports explícitos de vitest) — sin registrar `afterEach(cleanup)` de forma explícita, nunca
se desmontan los árboles entre tests. `apps/frontend/src/test/setup.ts` ya estaba commiteado (grupo 2,
`771bb0b`): arreglarlo requirió el mismo procedimiento que en el grupo 2 para
`tools/ci-workflow.test.mjs` — Victor autorizó desactivar `lock-committed-tests.mjs` temporalmente, se
añadió `afterEach(cleanup)` (patrón oficial de Testing Library para proyectos sin `globals: true`), y
el hook se reactivó antes de continuar. Diff de `setup.ts`: exactamente 3 líneas (import + llamada).

**Mutación** (Stryker efímero, acotado a los 6 archivos de producto): primera corrida, **19.35%** — 7
`Survived`, 43 `NoCoverage`. Decisión presentada a Victor: matar solo los supervivientes, cobertura más
profunda, o bajar el umbral. **Elegido: matar solo los supervivientes.** El tester (en 3 archivos
nuevos: `label.mutation.test.tsx`, `select.mutation.test.tsx`, `separator.mutation.test.tsx`, sin
tocar los 6 tests ya commiteados) mató 4 de los 7. Score final: **25.81%**, 3 supervivientes:

- `separator.tsx:10` (`orientation = "horizontal"` → `""`): **mutante equivalente**, verificado
  leyendo `@radix-ui/react-separator/dist/index.mjs` — `isValidOrientation(orientationProp) ?
  orientationProp : DEFAULT_ORIENTATION` normaliza cualquier valor inválido de vuelta a
  `"horizontal"`; el DOM es idéntico con o sin el mutante. Verificado de forma independiente por mí y
  por QA leyendo el mismo código fuente. Ningún test podría matarlo.
- `tooltip.tsx:42` y `tooltip.tsx:49`: solo observables mostrando el tooltip (hover/focus), fuera del
  alcance de "prueba de render" decidido para esta tarea. No remediados.

Los **43 `NoCoverage`** (subcomponentes como `SelectContent`, `SelectItem`, `DialogHeader`,
`DialogFooter`, `DialogTitle`, `DialogDescription`, el `Arrow` interno de `TooltipContent`,
`SelectScrollUp/DownButton`) quedan como brecha aceptada y documentada: son subcomponentes que solo se
montan al interactuar o que las pantallas reconstruidas del grupo 6 renderizarán con props reales —
cubrirlos ahora habría exigido tests de interacción muy por encima del alcance de "prueba de render"
de la tarea 4.3.

**DoD:** `check-dod.mjs` falla en `test`/`lint`/`typecheck` por `RF-093-001` (mismo patrón, no
relacionado). Sustituido por `--filter`: `test` 15/15, `typecheck` limpio, `lint` 49/49 sin regresión.
Escaneo de secretos en verde.

**QA:** `accept` en primera pasada. Verificó de forma independiente los 6 diffs contra el origen, que
los 6 tests originales no fueron tocados, el fix de `setup.ts`, el mutante equivalente (leyendo el
código fuente de Radix), y que los 3 tests de mutación citan líneas reales del producto.

### 4.4 — Primitivos sin consumidor (peso muerto aceptado por ADR-0004)

Verificado con `grep` sobre `apps/frontend/src/**` (excluidos los propios archivos de test): **ninguno
de los 5 componentes copiados (`Label`, `Separator`, `Select*`, `Dialog*`, `Tooltip*`) tiene consumidor
real** fuera de sus propios tests. `@radix-ui/react-slot` tampoco tiene archivo `ui/` ni consumidor.
Es exactamente el riesgo que ADR-0004 aceptó por escrito ("si al terminar alguno sigue sin consumidor,
se declara como peso muerto identificado"): los consumidores reales (login, selector de ámbito de
cliente en el `Layout`, ingesta, chat del asistente) se construyen en el **grupo 6** de esta misma
tarjeta, cuando se reconstruyan las pantallas del destino sobre el sistema de estilos nuevo.

**Findings de este grupo:** ninguno nuevo — el peso muerto ya estaba documentado como riesgo aceptado
en ADR-0004, no es un hallazgo nuevo que requiera entrada en el backlog.

### Grupo 4 — cierre

Commits del grupo: `5d27677` (Red) y `56b1b28` (Green: `utils.ts` + 5 componentes + fix de `setup.ts`
+ 3 tests de mutación).

## Grupo 5 — Componentes del origen y datos de demostración

**Objetivo:** portar los 8 `.tsx` vivos del origen (5 dashboards, `Layout`, `ExportButton`,
`routes.tsx`), con los datos estáticos aislados en `src/data/demo/`, sin montar todavía el enrutado
(eso es el grupo 6).

**Prerrequisito resuelto antes del Red** (commit `f646ef0`, working-tree separado, ya commiteado):
jsdom no implementa `ResizeObserver`; `recharts`'s `ResponsiveContainer` lo referencia sin comprobar
existencia y revienta el render sin él. Verificado con un spike antes de comprometer al tester/coder.
Mock mínimo (`observe`/`unobserve`/`disconnect` no-op) añadido a `setup.ts`, mismo procedimiento de
desactivar/reactivar el hook, autorizado por Victor.

**Red** (tester, commit `e128fcd`): 7 tests reales — `src/pages/{ExecutiveCostDashboard,
OperationalCostDashboard,ExecutiveCutDashboard,AnomaliesPanel,RecommendationsPanel}.test.tsx`,
`src/layouts/Layout.test.tsx`, `src/components/ExportButton.test.tsx`. Cada dashboard verifica su
encabezado y un KPI/stat con valor exacto de los datos de demostración.
`OperationalCostDashboard` calcula el string de `toLocaleString()` dinámicamente en el propio test
para no depender del locale del entorno. `Layout` envuelto en `MemoryRouter` (usa `NavLink`/`Outlet`
de react-router 7), verifica los 5 enlaces de navegación. `ExportButton` verifica el menú cerrado por
defecto y su apertura real al hacer clic (`fireEvent`). Evidencia Red: `7 failed | 11 passed (18)`.

**Green** (coder): 13 archivos portados del origen (`../Economicon/frontend/src/app/components/`,
commit `1fe0030`):
- 5 módulos en `src/data/demo/` (uno por dashboard), constantes extraídas tal cual, comentario de
  cabecera "DATOS DE DEMOSTRACION (sustituibles)" grep-able.
- 5 dashboards en `src/pages/`, idénticos al origen salvo el bloque de imports (datos desde
  `@/data/demo/...`, `ExportButton` desde `@/components/ExportButton`). Verificado por QA archivo a
  archivo, no solo una muestra.
- `Layout.tsx` → `src/layouts/Layout.tsx`, **copia literal**, verificada byte a byte por QA.
- `ExportButton.tsx` → `src/components/ExportButton.tsx`, con la adaptación de tipado que exige la
  tarea 5.3: el origen usa `data: any`/`row: any`; el destino usa `type ExportRow = Record<string,
  string | number>` en todo el archivo. Sin `any` real ni `@ts-ignore` (verificado por grep, por mí y
  por QA).
- `routes.tsx` → `src/routes.tsx`, las 5 rutas del origen bajo `Layout`, imports reajustados a las
  nuevas ubicaciones, **sin montar** en `App.jsx`/`main.jsx` (confirmado por grep — el enrutado es
  tarea del grupo 6, `tasks.md` 6.1).

Evidencia Green: `Test Files 18 passed (18)` / `Tests 23 passed (23)`. `typecheck` limpio.
`lint` 49/49 sin regresión. `build`: bundle idéntico (`203.37 kB` / `5.60 kB`) porque nada importa
todavía los archivos portados.

**Mutación** (Stryker, acotado a los 7 archivos de comportamiento — no los módulos de datos, literales
sin lógica): resultado muy distinto al del grupo 4. Score global **12.11%** — 35 killed, **198
survived**, 56 NoCoverage. Desglose:

- Los 5 dashboards rondan el **5% de cobertura real** cada uno: la única prueba de render por
  dashboard apenas toca el encabezado y un KPI/stat, dejando sin ejercitar el resto de tarjetas KPI,
  todas las filas de tabla salvo ninguna, y los estilos condicionales (`row.uso > 80 ? 'bg-red-500' :
  ...`, colores por proveedor/severidad/estado).
- `Layout`: **56% cubierto**, 14 supervivientes — sobre todo el `path`/`end` de cada `NavLink` y las
  clases condicionales de estado activo (el test solo verifica que los 5 textos de enlace existen, no
  su comportamiento de navegación).
- `ExportButton`: **87% cubierto**, 1 superviviente — el `onClick` del overlay que cierra el menú al
  hacer clic fuera, que ninguno de los 2 tests dispara.

**Decisión presentada a Victor**, explícitamente distinta a la del grupo 4 (allí 7 supervivientes
remediables con poco esfuerzo; aquí 198, desproporcionado para "prueba de render" tal como lo pide la
tarea 5.4). Opciones: aceptar tal cual, cobertura media (todos los KPIs/stats + una fila representativa
por tabla), o cobertura profunda (cada fila, cada estilo condicional). **Elegido: aceptar tal cual.**
Motivo: son 5 pantallas de origen con datos 100% estáticos que probablemente cambien de forma
sustancial en el grupo 6 (paridad de rutas del destino) y dependen de `RF-091-003` (7 capacidades de
backend ausentes, decisión de épica sobre qué conectar) — invertir en cobertura exhaustiva ahora sobre
código que puede reescribirse pronto tiene bajo retorno. No se hizo remediación adicional, ni siquiera
de los supervivientes de `Layout`/`ExportButton` (que quedan documentados igual que los de los
dashboards, sin distinción especial pese a su mejor cobertura de partida).

**DoD:** `check-dod.mjs` falla por `RF-093-001` (mismo patrón, no relacionado). Sustituido por
`--filter`: `test` 23/23, `typecheck` limpio, `lint` 49/49. Escaneo de secretos en verde.

**QA:** `accept` en primera pasada. Verificó de forma independiente los 5 dashboards completos contra
el origen (no solo una muestra), `Layout` byte a byte, el tipado de `ExportButton`, que `routes.tsx`
no está montado, y reprodujo dos supervivientes citados (`Layout`, `ExportButton`) leyendo el código
fuente para confirmar que el 12.11% no oculta nada.

**Findings de este grupo:** ninguno nuevo — la baja cobertura de mutación de los dashboards es una
decisión de alcance documentada aquí y en `tasks.md`, no un defecto sin registrar.

### Grupo 5 — cierre

Commits del grupo: `f646ef0` (prerrequisito ResizeObserver), `e128fcd` (Red), `bdc75bf` (Green: 13
archivos portados + `tasks.md`/`review.md`).

## Grupo 6 — Enrutado y armazón

**Arquitectura acordada con Victor antes de implementar cualquier código**: `SessionGate` (nuevo) como
ruta padre de `Layout`, pasando `{ token, user, tenants, activeTenant, activeTenantId,
onTenantChange, onLogout }` a las rutas hijas vía `<Outlet context={...} />` de react-router —
mecanismo nativo, no `Context API` propio (Victor confirmó explícitamente esta opción frente a la
alternativa). Documentado como "Addendum: arquitectura del grupo 6" en `design.md`, con el mapa
completo de componentes nuevos/modificados y la razón de cada uno, antes de invocar al tester.
Implementado en **4 sub-rondas**, cada una con su propio Red/Green: (a) `SessionGate` + `Layout`
extendido + `routes.tsx`; (b) `LoginPage`; (c) `IngestPage` + `ConversationsPage`; (d)
`DashboardPage`/`overview-legacy` + `MetricCard`/`SectionCard`/`StatusPill` + simplificación de
`App.jsx` y retirada de `AppShell.jsx`.

### Sub-ronda (a) — `SessionGate`, `Layout` extendido, `routes.tsx`

**Red** (tester, commit `861355b`): `SessionGate.test.tsx` (sin sesión redirige a `/login` sin llamar
a `fetch`; con sesión, bootstrap de tenants real con `fetch` mockeado vía `vi.stubGlobal`, expone el
tenant auto-seleccionado vía `Outlet context`, verificado con `createMemoryRouter`/`RouterProvider`
reales) y `Layout.selector.test.tsx` (nuevo, complementario a `Layout.test.tsx` del grupo 5 —
**no tocado**: sin contexto no muestra selector/panel, con contexto sí, montado vía un
`ContextProvider` de prueba). Evidencia Red: `2 failed | 18 passed (20)`.

**Prerrequisito descubierto durante el Green**: jsdom sombrea `AbortController`/`AbortSignal` con su
propia implementación (`class AbortSignal extends globalObject.EventTarget`), pero `Request` se queda
nativo de Node (undici, jsdom no implementa Fetch) y valida `signal instanceof AbortSignal` contra su
propia clase interna — distinta de la de jsdom. `react-router` 7 construye exactamente eso en
`createClientSideRequest` en **cualquier navegación real**, incluso sin loaders: verificado con un
repro mínimo sin código de producto (`<Navigate>` desnudo dentro de `createMemoryRouter` ya revienta).
Sin arreglarlo, ninguna prueba de enrutado real —tampoco las que pide la tarea 6.5— podría funcionar.
No hay forma de recuperar el `AbortController` nativo desde `setup.ts` (ya está sombreado cuando
arranca el entorno). Fix: `Proxy` sobre `Request` en `setup.ts` que solo interviene si la construcción
falla por el `signal`, reintentando sin él — verificado que el `catch` relanza (`throw error`) para
cualquier otro fallo, no es un polyfill permisivo. Mismo procedimiento de desactivar/reactivar el hook,
autorizado por Victor.

**Green** (coder): `SessionGate.tsx` (nuevo) reproduce **verbatim** la lógica de `App.jsx` — bootstrap
de tenants (`useQuery`), auto-selección (`useEffect`), `activeTenant` (`useMemo`), `handleLogout`,
`handleTenantChange` — solo tipada y trasladada de sitio (verificado línea a línea por QA). Los
estados de carga/error del bootstrap son armazón nuevo, reconstruidos sobre Tailwind. `Layout.tsx`
lee `useOutletContext()` de forma defensiva (`?? {}`, tipado `Partial<SessionOutletContext>`),
añade selector de tenant + panel de sesión cuando hay datos, **conserva la fecha del header del
origen** (reubicada, no eliminada — verificado por QA), reenvía el contexto con
`<Outlet context={ctx} />`. `routes.tsx`: `SessionGate` insertado como padre de `Layout`.

**Nota de transparencia sobre el commit `d040272`**: su mensaje describe solo el fix de `Request`,
pero el diff incluye también el Green completo de `SessionGate.tsx`/`Layout.tsx`/`routes.tsx` (el
usuario commiteó todo el working tree de una vez). El contenido es correcto y fue verificado en su
totalidad por mí y por QA de forma independiente — es un problema de mensaje incompleto, no de
contenido oculto. Se deja registrado aquí para que el historial de commits tenga su explicación
correcta pese al mensaje parcial.

**Fix de lint sobre el propio parche** (commit separado): el `Proxy` de `Request` introdujo
`'_signal' is assigned a value but never used` al desestructurar solo para descartar el campo.
Corregido construyendo `rest` con spread + `delete rest.signal`. Lint de vuelta a 49/49.

**Evidencia Green:** `Test Files 20 passed (20)` / `Tests 27 passed (27)`. `typecheck` limpio.
`lint` 49/49. `build`: bundle idéntico (89 módulos, `203.37 kB`/`5.60 kB`) — `App.jsx`/`main.jsx`
todavía no importan `routes.tsx`.

**Mutación** (Stryker, acotado a `SessionGate.tsx` + `Layout.tsx`): **51.15%** (67 killed, 50
survived, 14 NoCoverage — sobre todo los estados de carga/error del bootstrap, que ningún test monta
todavía, más parte de la lógica de auto-selección de tenant, que el único test con sesión no ejercita
a fondo por usar un solo tenant). Presentado a Victor como decisión de alcance explícita: **aceptar y
documentar**. Motivo: es código de armazón que las sub-rondas b/c/d seguirán tocando (`Layout` ganará
más UI; `SessionGate` no cambia más), y la prueba de enrutado real de la tarea 6.5 (al final del
grupo 6) ejercitará el flujo completo de forma más realista que mutantes aislados en esta pieza
intermedia.

**DoD:** `check-dod.mjs` falla por `RF-093-001` (mismo patrón, no relacionado). Sustituido por
`--filter`: los cuatro comandos en verde. Escaneo de secretos en verde.

**QA:** `accept` en primera pasada. Verificó de forma independiente la fidelidad verbatim de
`SessionGate` contra `App.jsx` línea a línea, que el parche de `Request` es proporcionado (no
permisivo), que `Layout.test.tsx` del grupo 5 sigue sin tocarse, que la fecha del header se conserva,
y reprodujo la mutación de forma independiente.

**Findings de esta sub-ronda:** ninguno nuevo.

### Sub-ronda (b) — `LoginPage` reconstruida

**Red** (tester, commit `c7bc733`): `LoginPage.test.tsx` — monta con `createMemoryRouter`/
`RouterProvider`/`QueryClientProvider`, `fetch` mockeado, verifica que tras un login exitoso navega a
`/` (ruta de sonda) y persiste `{ accessToken, user }` en `localStorage["finops.session"]`. Evidencia
Red: `1 failed | 20 passed (21)` — `LoginPage.jsx` actual depende del prop `onLogin` (`undefined` al
montarse como componente de ruta sin props), así que `onSuccess` nunca se invoca.

**Green** (coder): `LoginPage.tsx` (nuevo) reemplaza a `LoginPage.jsx` (eliminado). Ya no recibe
`onLogin`: en el `onSuccess` de su mutación reproduce **verbatim** `App.jsx.handleLogin` (construir
`{ accessToken, user }`, persistir en `localStorage`) y navega con `useNavigate()`. `SESSION_KEY`
pasa a exportarse desde `SessionGate.tsx` en vez de duplicar el string en dos sitios. Lógica de
formulario conservada tal cual; solo cambian tipado (TS estricto, sin `any`) y presentación
(Tailwind, tema oscuro coherente con `SessionGate`/`Layout`). `App.jsx` queda con un import roto a
`./pages/LoginPage` — **deuda esperada y documentada**, no detectada por `typecheck` (`checkJs:
false`) ni por los tests (ninguno ejecuta `App.jsx`); se resuelve en la sub-ronda (d). Evidencia
Green: `21/21 pass`. `typecheck` limpio. `lint`: 49 → **48** (desaparece la violación de
`react/prop-types` de `LoginPage.jsx`, uno de los 9 archivos de la línea base original).

**Mutación**: primera corrida acotada a `LoginPage.tsx`, **43.48%** (8 survived, 5 NoCoverage) — el
único test no escribía en los campos ni inspeccionaba el cuerpo enviado a `fetch`. A diferencia de
las sub-rondas anteriores, **Victor eligió reforzar** (archivo pequeño, refuerzo barato): tester
añadió `LoginPage.mutation.test.tsx` (nuevo, sin tocar `LoginPage.test.tsx`) con dos casos que
inspeccionan el `body` real de `fetch` — (A) formulario sin tocar envía los valores por defecto
exactos; (B) campos editados (`fireEvent.change`) envían esos valores, no los por defecto. Score
final: **82.61%** (19 killed, 3 survived, 1 NoCoverage), por encima del umbral de corte. No atacados
deliberadamente: `navigate("/", { replace: true })` mutado a `{}`/`{replace: false}` (difícil de
observar sin inspeccionar el historial del router en este entorno), `event.preventDefault()`
eliminado (jsdom no navega páginas reales, efecto no observable), y el texto `"Signing in..."` del
botón pendiente (NoCoverage, riesgo mínimo de UI).

**DoD:** `check-dod.mjs` falla por `RF-093-001` (mismo patrón, no relacionado). Sustituido por
`--filter`: los cuatro comandos en verde. Escaneo de secretos en verde.

**QA:** `accept` en primera pasada. Verificó de forma independiente que `handleLogin` está preservado
verbatim, que `SESSION_KEY` no quedó duplicado, que los tests de mutación inspeccionan el cuerpo real
de `fetch` (no tautológicos), y reprodujo la mutación desde cero con el comando documentado en
`mutation.md`.

**Findings de esta sub-ronda:** ninguno nuevo.

### Sub-ronda (c) — `IngestPage`, `ConversationsPage`, `SectionCard`

**Red** (tester, commit `5a5b873`): `IngestPage.test.tsx` (sin tenant activo no muestra el campo
"Source" — aserción negativa robusta, no atada al texto del mensaje; con tenant activo, envía el
formulario por defecto y verifica que `fetch` llega a `/jobs/ingest` con la cabecera `X-Tenant-Id`
del tenant del contexto) y `ConversationsPage.test.tsx` (con tenant activo, lista las conversaciones
existentes vía `fetch` mockeado). Evidencia Red: `2 failed | 22 passed (24)`.

**Green** (coder): `SectionCard.tsx` (nuevo, reemplaza al `.jsx`) reconstruido sobre Tailwind con el
lenguaje visual de los dashboards, primer consumidor compartido entre pantallas. `IngestPage.tsx` y
`ConversationsPage.tsx` (nuevos, reemplazan a sus `.jsx`) migran de props a
`useOutletContext<SessionOutletContext>()`; lógica preservada verbatim (estado de formulario,
mutación de ingesta; dos queries, `useEffect` de auto-selección, dos mutaciones de conversaciones),
verificado línea a línea por QA. Único cambio funcional: `activeTenant.id` → `activeTenant?.id`, sin
efecto observable (ambas rutas de código solo se alcanzan tras el guard de tenant). `App.jsx` sigue
con imports rotos a ambos `.jsx` — deuda esperada, se resuelve en la sub-ronda (d). Evidencia Green:
`24/24 pass`. `typecheck` limpio. `lint`: 48 → **28** (caída de 20, no solo los 2 estimados al
encargar la tarea — verificado por QA que se debe enteramente a que ambos archivos desaparecen por
completo, `ConversationsPage.jsx` tenía muchas más violaciones de las estimadas por su uso repetido
de `activeTenant`/`token` en múltiples queries/mutaciones).

**Mutación**: acotada a los 3 archivos, **18.66%** global (25 killed, 67 survived, 42 NoCoverage).
Desglose: `SectionCard.tsx` **100%** (trivial, sin lógica condicional). `IngestPage.tsx` **30%** (su
flujo principal de envío ya cubierto por el Red). `ConversationsPage.tsx` **14.56%** (la más
compleja: dos queries, dos mutaciones, un efecto de auto-selección, y el único test solo verifica el
listado inicial). Presentado a Victor como decisión de alcance: **aceptar y documentar**. Motivo:
son pantallas con backend real que JUP-096 reconectará pronto, y el flujo completo (crear
conversación, enviar mensaje) se prueba mejor de forma end-to-end en la tarea 6.6 (verificación
manual con el seed) que con mutantes aislados aquí — mismo criterio ya aplicado en el grupo 5 y en la
sub-ronda (a) de este grupo.

**DoD:** `check-dod.mjs` falla por `RF-093-001` (mismo patrón, no relacionado). Sustituido por
`--filter`: los cuatro comandos en verde. Escaneo de secretos en verde.

**QA:** `accept` en primera pasada. Verificó de forma independiente la preservación verbatim de la
lógica (línea a línea contra los `.jsx` originales), que la caída de lint de 20 no oculta ningún
archivo tocado por error, y reprodujo la mutación de forma independiente sin indicio de bug real
oculto entre los supervivientes.

**Findings de esta sub-ronda:** ninguno nuevo.
