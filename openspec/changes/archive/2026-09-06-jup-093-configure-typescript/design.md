JUP: JUP-093

## Context

Ver [proposal.md](proposal.md) — Why. Aquí solo el estado que condiciona el enfoque, verificado sobre
el repo:

**Decisión vinculante.** [ADR-0003](../../../../docs/adr/ADR-0003-frontend-typescript.md) (`Accepted`,
JUP-092) es la fuente de autoridad de esta tarjeta y sus cuatro decisiones no se reabren aquí:
`strict: true` desde el inicio (1), `allowJs: true` durante la migración y `false` al cerrar F5 (2),
type-check como check obligatorio en CI (3), y `tsconfig` a nivel de `apps/frontend` y no en
`packages/shared-config` (4). El [spike](../../../../docs/spikes/frontend-migration.md) (línea 170)
exige que las tarjetas de F2 y F3 enlacen el ADR desde su `design.md`; este documento lo hace.

**Punto de partida.**

- `apps/frontend/src/**` son **14 archivos**, todos `.js`/`.jsx`. Ninguno `.ts`/`.tsx`.
- `package.json` de `@finops/frontend`: `vite ^5.3.3`, `eslint ^9.5.0` con **flat config**
  (`eslint.config.js` exporta un array), scripts `lint: eslint src --ext js,jsx`,
  `test: echo "No frontend tests configured yet"`. Sin `typescript` ni `@types/*`.
- `eslint.config.js` aplica `js.configs.recommended` global y un bloque `files: ["src/**/*.{js,jsx}"]`
  con las reglas recomendadas de `react` y `react-hooks`, más `react/react-in-jsx-scope: off`.
- `vite.config.js` son 5 líneas: `defineConfig({ plugins: [react()] })`. El host `0.0.0.0` y el puerto
  `5173` **no** viven ahí, sino en los flags del script `dev`.
- `.github/workflows/ci.yml` tiene 4 jobs; el único del frontend es `frontend-build` (nombre
  `Frontend build`), que solo ejecuta `build`. No hay lint ni type-check del frontend en CI.
- Las seis check contexts obligatorias están **versionadas en tres sitios a la vez**:
  `.github/rulesets/develop.json`, `.github/rulesets/main.json` y
  [docs/governance/github-branch-protection.md](../../../../docs/governance/github-branch-protection.md),
  y `tools/ci-workflow.test.mjs` las asevera (`keeps the six branch-protection check contexts
  stable`). Cualquier context nueva obliga a tocar los cuatro de forma coherente.
- El frontend **no tiene runner de tests**. La verificación ejecutable de esta tarjeta recae en
  `typecheck`, `lint`, `build` y el test de nodo `ci:check:test`.

## Goals / Non-Goals

**Goals:**

- Dejar `apps/frontend` capaz de compilar, tipar y lintear TypeScript **sin migrar un solo archivo**,
  de modo que el primer `.tsx` que llegue en F3 esté verificado desde su primer commit.
- Materializar la decisión 3 de ADR-0003 con una check context real, no con un script que nadie
  ejecuta.
- No mover la línea base de lint: exactamente las mismas 49 violaciones antes y después.

**Non-Goals (además de los de la propuesta):**

- **No se activa el ruleset en vivo.** Esta tarjeta versiona la nueva context en los JSON, el test y
  la documentación; aplicarla sobre GitHub es acción de administrador, siguiendo el mismo patrón de
  "Administrator activation checklist" que estableció JUP-079.
- **No se introduce runner de tests** en el frontend (Vitest o similar): es tarjeta propia, no
  prerequisito del tooling de tipos.
- **No se decide Vite 5 vs 6** (única dependencia `SUSTITUIR` del inventario de JUP-091): es de
  `reconciliar-package-json`.
- **No se activa `checkJs`** sobre el JavaScript existente — ver decisión 2.

## Decisions

### 1. Un `tsconfig.json` para `src/` y un `tsconfig.node.json` para la config de Vite

`tsconfig.json` cubre `src/**` con destino navegador (`lib` DOM, `jsx: react-jsx`,
`moduleResolution: Bundler`, `noEmit: true`, `strict: true`). `tsconfig.node.json` cubre
`vite.config.ts` con destino Node y `@types/node`. Ambos viven en `apps/frontend/`.

*Por qué:* `src/` y la config del bundler se ejecutan en runtimes distintos con librerías globales
distintas; un único `tsconfig` obliga a mezclar `DOM` y `node` en el mismo `lib`, y a que el código de
producto vea globales de Node que no tendrá en el navegador.

*Alternativas descartadas:* (a) el layout de tres archivos con `references` de la plantilla oficial
`react-ts` de Vite (`tsconfig.json` solución + `tsconfig.app.json` + `tsconfig.node.json`) — más
ceremonia de la que justifican 14 archivos, y los project references complican el comando de
type-check sin aportar aquí; (b) un único `tsconfig.json` para todo — el problema de `lib` descrito
arriba.

### 2. `allowJs: true` **con `checkJs: false`**

Es la lectura precisa de la decisión 2 de ADR-0003. `allowJs` permite que TypeScript *resuelva* los
`.js`/`.jsx` aún sin migrar, para que el primer slice de F3 no rompa el grafo de módulos. `checkJs`
es una opción distinta: activaría la verificación de tipos **sobre esos 14 archivos JavaScript nunca
tipados**.

*Por qué separar las dos:* con `checkJs: true`, `tsc --noEmit` fallaría en el primer commit de esta
tarjeta y F2 se convertiría de facto en F3 — exactamente el "big bang" que el spike prohíbe. La
tarjeta quedaría bloqueada por trabajo que pertenece a otra fase.

*Consecuencia honesta:* hasta que F3 migre archivos, el type-check pasará en verde **sin verificar
nada de sustancia**. Es lo correcto: el valor de esta tarjeta es que la red esté puesta y sea
obligatoria antes de que llegue el código, no que encuentre errores hoy.

*Alternativa descartada:* `checkJs: true` con `// @ts-nocheck` en los 14 archivos — tocaría todos los
archivos fuente (Non-Goal explícito) y dejaría supresiones que alguien tendría que retirar en F3.

### 3. `vite.config.js` → `vite.config.ts`

*Por qué:* mantener el único archivo de configuración del frontend en JavaScript mientras se exige
TypeScript al resto es incoherente, son 5 líneas, y el origen ya llega con su config en TS — hacerlo
ahora evita repetirlo en F3. El host y el puerto no se tocan porque **no están en este archivo**:
viven en los flags del script `dev` (`--host 0.0.0.0 --port 5173`), que se conserva literal.

*Alternativa descartada:* dejarlo en `.js`. Evitaría `tsconfig.node.json` y `@types/node`, pero
traslada la conversión a F3 mezclada con el porte de código, donde es más difícil de revisar.

### 4. ESLint: `typescript-eslint` en modo **no type-aware**, y la selección de archivos pasa a la config

Se añade `typescript-eslint` (paquete unificado v8, compatible con flat config y con `eslint ^9`) y se
aplica su configuración recomendada a un bloque nuevo `files: ["src/**/*.{ts,tsx}"]`, con
`react/prop-types: "off"` **solo en ese bloque**. El bloque existente `src/**/*.{js,jsx}` se deja
**intacto**.

Además, la selección de extensiones se mueve del script a `eslint.config.js`: el script pasa de
`eslint src --ext js,jsx` a `eslint src`, y los globs `files` de la flat config deciden qué se
analiza.

*Por qué no type-aware:* `recommendedTypeChecked` exige que el linter levante el programa de
TypeScript en cada ejecución — mucho más lento, y acopla el lint a la resolución del `tsconfig`. El
type-check ya corre por separado como check propio (decisión 5); duplicar esa comprobación dentro del
lint paga el coste dos veces. Se puede endurecer más adelante si aparece la necesidad.

*Por qué mover las extensiones a la config:* deja de depender de `--ext`, cuyo soporte en flat config
es tratado como legado, y hace que la fuente de verdad de qué se lintea sea un único archivo.

*Sobre `RF-082-002`:* al no tocar el bloque `{js,jsx}`, las 49 violaciones de `react/prop-types` en
los 9 archivos `.jsx` **siguen reportándose**. Es el resultado deseado, no un descuido: así lo corrigió
la revisión de PR de JUP-092. El finding se cierra en F3/F5, cuando esos archivos se tipen de verdad.

### 5. Check context propia `Frontend type check`, versionada pero no activada

Se añade el script `typecheck` a `@finops/frontend` y un job nuevo `frontend-typecheck` (nombre
`Frontend type check`) a `ci.yml`. Esa context se añade a `.github/rulesets/develop.json`, a
`.github/rulesets/main.json`, a la lista de "Required status checks" del documento de gobernanza, y a
las aserciones de `tools/ci-workflow.test.mjs` — que hoy fija seis y pasará a fijar siete.

*Por qué job separado y no un paso dentro de `Frontend build`:* un paso extra dentro del job existente
también bloquearía el merge y no tocaría gobernanza, que es más barato. Se descarta porque el
repositorio enumera sus verificaciones como contexts nombradas (es la convención que fijó JUP-079), y
porque un fallo de build y un fallo de tipos son señales distintas: fundirlas obliga a abrir los logs
para saber cuál de las dos se rompió.

*Coste asumido:* esto entra en territorio de JUP-079. Se mitiga manteniendo los cuatro sitios
coherentes en el mismo commit y dejando la aplicación en vivo del ruleset como paso de administrador
documentado, igual que hizo JUP-079. No hay riesgo de auto-bloqueo del propio PR: el workflow de la
rama publica la context, y el ruleset solo pasa a exigirla cuando un administrador lo reaplica.

### 6. Orden de ejecución: tooling primero, CI después

Instalar dependencias y crear `tsconfig` antes de tocar `ci.yml`, para que el job nuevo se añada
cuando el comando que invoca ya existe y pasa en local. Añadir la context a los rulesets es lo último.

## Risks / Trade-offs

- **El type-check pasa en verde sin verificar nada real** (consecuencia de `checkJs: false`) → se
  documenta explícitamente en `review.md` como limitación conocida y esperada; el valor se materializa
  en F3, cuando el primer `.tsx` entre bajo una red ya obligatoria.
- **`typescript-eslint` entra en conflicto con `eslint-plugin-react` o cambia la línea base de lint**
  → criterio de aceptación medible: `pnpm lint` debe reportar **exactamente 49** violaciones, ni una
  más ni una menos. Si sube, se ajusta el alcance de los globs; no se silencian reglas para cuadrar el
  número.
- **`vite.config.ts` no resuelve tipos y arrastra más configuración de la prevista** → si el coste
  supera lo trivial, se revierte a `.js` y se registra el motivo; la conversión es la parte más
  prescindible del alcance (decisión 3) y no bloquea nada más.
- **Deriva entre el ruleset versionado y el ruleset vivo en GitHub** → riesgo heredado del patrón de
  JUP-079, no introducido aquí; se mitiga dejando el paso de administrador escrito en el `review.md` y
  en el PR, y no dando por obligatoria la context hasta que alguien confirme la reaplicación.
- **`@types/node` amplía la superficie de tipos globales** en `tsconfig.node.json` → queda acotado a
  ese proyecto; `src/**` no lo ve.
- **Sin tests de frontend, la única red de este cambio son los comandos** → se compensa con el test de
  nodo existente (`ci:check:test`), que sí cubre la parte de CI y rulesets y da un ciclo Red/Green
  real a la decisión 5.

## Migration Plan

1. `pnpm --filter @finops/frontend add -D typescript @types/react @types/react-dom @types/node typescript-eslint` desde la raíz; commitear `pnpm-lock.yaml`.
2. Crear `tsconfig.json` y `tsconfig.node.json`; añadir el script `typecheck`; verificar en verde.
3. Convertir `vite.config.js` → `.ts`; verificar `pnpm dev` y `pnpm build`.
4. Migrar `eslint.config.js`; ajustar el script `lint`; verificar el recuento de 49.
5. Añadir el job `frontend-typecheck` a `ci.yml` y la context a rulesets, gobernanza y
   `tools/ci-workflow.test.mjs`.
6. Verificación final: `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm build`,
   `pnpm ci:check:test`, `pnpm openspec:validate`, `pnpm jup:check`, `pnpm jup:cleanup:check`.

**Rollback:** todo el cambio es tooling reversible con un revert del commit; no hay migración de datos
ni de código fuente. El único efecto que sobrevive a un revert es el ruleset vivo, si un administrador
ya lo hubiera reaplicado — en ese caso se retira la context del ruleset antes de revertir.

## Open Questions

- Si `tsconfig.node.json` acaba siendo innecesario porque `vite.config.ts` type-checkea limpio bajo la
  configuración de `src/`, se omite. Es detalle de ejecución: no cambia las specs, el enfoque ni el
  desglose de tareas.
- La versión exacta a fijar de `typescript` y `typescript-eslint` se resuelve al instalar, tomando la
  estable compatible con `eslint ^9.5`.
