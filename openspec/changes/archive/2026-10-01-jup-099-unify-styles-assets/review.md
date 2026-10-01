# Review — JUP-099 unify-styles-assets

## Grupo 1. Línea base

**1.1 — Línea base de la suite.** Sustituto usado (RF-093-001 sigue abierto: turbo resuelve un pnpm
global en subprocesos por paquete en esta máquina, así que no se pasa por turbo):
`corepack pnpm --filter @finops/frontend test`, sobre `7eef7ca` (`688fe2d` + solo artefactos del
change; `git diff 688fe2d HEAD -- apps/frontend` vacío).

```
Test Files  46 passed (46)
     Tests  261 passed (261)
```

Línea base: **261 PASS / 0 FAIL**, 46 archivos. Cada grupo posterior debe mantener 261 PASS más los
tests nuevos de los grupos 3 en adelante (los guardianes del grupo 3 fallan a propósito hasta que se
migra cada archivo).

**1.2 — Inventario de partida** (`apps/frontend/src`, excluidos los `*.test.*`; ejecutado el
2026-09-29 sobre `7eef7ca`):

| Medida | Resultado | Comando |
| --- | --- | --- |
| Hexadecimales en `.tsx` | **241** en **14** archivos | `grep -rnoE '#[0-9a-fA-F]{3,8}\b' --include=*.tsx . \| grep -v '\.test\.tsx' \| wc -l` (y `grep -rlE` para los archivos) |
| Hexadecimales en datos demo | **4** (`data/demo/executiveCostDashboard.ts`) | `grep -rnoE '#[0-9a-fA-F]{6}\b' data/demo/*.ts \| wc -l` |
| Utilidades de la paleta de Tailwind | **229** en **16** archivos | `grep -rhoE '\b(text\|bg\|border\|ring\|fill\|stroke\|from\|to\|via\|outline\|divide\|placeholder\|shadow\|decoration\|accent\|caret)-(slate\|gray\|zinc\|neutral\|stone\|red\|orange\|amber\|yellow\|lime\|green\|emerald\|teal\|cyan\|sky\|blue\|indigo\|violet\|purple\|fuchsia\|pink\|rose\|white\|black)(-[0-9]{2,3})?(/[0-9]+)?\b' --include=*.tsx . --exclude=*.test.tsx \| wc -l` |
| Referencias a `main.css` | **3** (comentarios de `MetricCard`, `SectionCard`, `StatusPill`) | `grep -rniE 'main\.css' apps/frontend --exclude-dir=node_modules --exclude-dir=dist` |
| Variables declaradas en `theme.css` | **110** (`:root` + `.dark`; 34 expuestas como `--color-*` en `@theme inline`) | `grep -cE '^\s+--[a-z0-9-]+:' src/styles/theme.css` |

Los 241 hexadecimales son 16 valores distintos: `#2d3748` ×68, `#1a1f2e` ×39, `#0078d4` ×32,
`#232834` ×29, `#0f1419` ×19, `#94a3b8` ×16, `#00bcf2` ×12, `#fff` ×9, `#10b981` ×5, `#64748b` ×3 y el
resto ×1-2. Formas de uso: 169 clases arbitrarias (`bg-[#…]`), 42 atributos `fill`/`stroke` de
Recharts, 18 objetos `contentStyle`/`style`, más el HTML de exportación de `ExportButton`. Ninguno
de los 46 archivos de test comprueba clases de color (solo `rounded-md`, `shrink-0`, `text-sm`), así
que la suite no debería cambiar con la migración.

Utilidades de paleta más repetidas: `text-slate-400` ×66, `text-white` ×65, `text-red-400` ×11,
`text-slate-300` ×10, `text-green-400` ×6. `src/components/ui/dialog.tsx` aporta 1 (`bg-black/50`,
excepción prevista, decisión 5 de `design.md`).

**1.3 — Guion de captura preparado.** Proyecto temporal **fuera del repositorio** (`npm install
playwright pixelmatch pngjs`; Playwright 1.63.0, Chromium 1243 ya presente en el caché local, sin
descargas nuevas). Nada entra en `package.json`. Dos archivos: `capture.mjs` (sirve un build de
producción con servidor estático y fallback SPA, API simulada con `page.route`, viewport 1440×900,
`es-ES`, zona `Europe/Madrid`, movimiento reducido, espera fija de 3 s) y `compare.mjs`
(`pixelmatch`, umbral 0, `includeAA`). Se copian íntegros a `docs/evidence/JUP-099-validation.md`
en la tarea 10.3.

Dos problemas del guion descubiertos y corregidos **antes** de dar la referencia por buena (ambos
dejaban las series de Recharts sin pintar, lo que habría hecho inútil la comparación de los
`fill`/`stroke`):

1. `fullPage: true` redimensiona el viewport durante la captura; `ResponsiveContainer` re-renderiza
   y Recharts reinicia su animación justo antes de la foto. Se amplía el viewport a la altura del
   documento, se espera y se captura el viewport tal cual.
2. La fecha del `Layout` (`new Date()`) hace la captura dependiente del día. Se fija solo `new Date()`
   sin argumentos; `Date.now` se deja real (`page.clock.setFixedTime` lo congela, y se descartó por
   sospecha de afectar a la animación; el arreglo real fue el punto 1).

**1.4 — Referencia "antes" capturada** sobre el build de `7eef7ca` (frontend idéntico a `688fe2d`).
14 capturas cubriendo las 9 pantallas y sus estados con color propio:

| Captura | Pantalla / estado |
| --- | --- |
| `login`, `login-invalid-credentials`, `login-session-expired` | `/login`; error en rojo (`text-red-400`); aviso ámbar de JUP-098 (`text-amber-400`) |
| `executive-cost`, `executive-cost-export-menu`, `executive-cost-tenant-select-focus` | `/`; menú de `ExportButton` abierto; foco del selector de ámbito (`focus:border-[#00bcf2]`) |
| `operational-cost`, `executive-cuts`, `anomalies`, `recommendations` | `/operational`, `/cuts`, `/anomalies`, `/recommendations` |
| `overview-legacy` | `/overview-legacy` |
| `ingest`, `ingest-error` | `/ingest`; error de la mutación en rojo |
| `assistant` | `/assistant` con conversación seleccionada y borrador |

**Determinismo verificado:** dos pasadas seguidas sobre el mismo build → `TOTAL 0` píxeles distintos
en las 14 capturas (`node compare.mjs shots-before-1 shots-before-2`). Sin esto no se podría atribuir
ninguna diferencia posterior a la migración.

**Diferencia esperada anotada desde ya (para explicarla en 8.1, no es un fallo del guion):** en las
pantallas más cortas que el viewport (`ingest`, `ingest-error`, `assistant`, `overview-legacy`) la
franja bajo el contenido es el fondo del `body`, hoy `#0a0a0a` (`oklch(0.145 0 0)` de shadcn). El
`Layout` pinta `#0f1419` solo hasta donde llega su contenido. Al mapear `background` a `#0f1419`, la
franja pasará a `#0f1419`: cambio visible, deliberado y coherente con el resto de la pantalla, pero
una diferencia real que se declarará y aceptará en la tarea 8.1.

**Checkpoint:** grupo sin código de producto ni tests nuevos (solo medición y capturas fuera del
repositorio) → sin ciclo Red/Green ni mutación (excepción doc-only). Único cambio en el repositorio:
este `review.md` y las casillas de `tasks.md`.

## Grupo 2. Arrastre de JUP-098 (documentación)

**2.1 — Descartada por decisión de Victor (2026-09-29).** El plan de la tarjeta pedía preguntar a
Lucía qué quiso decir con "los tests del frontend no corren en CI" antes de escribir nada sobre CI.
Victor considera que es un malentendido y decide no preguntar. Consecuencia: ni `RF-098-004` ni
ningún otro documento de esta tarjeta hacen afirmación alguna sobre CI (ni a favor ni en contra). El
bloque `## Human Approval` de `proposal.md` conserva su redacción original ("hasta la respuesta de
Lucía"), que queda superada por esta decisión; `proposal.md` (What Changes), `design.md` (decisión 9)
y `tasks.md` (2.1, 2.2) se han ajustado en consecuencia.

**2.2 — `RF-098-004` registrado** en `openspec/findings/backlog.md` (tras `RF-098-003`). Contenido:
fallos por el límite de 1 s de `findBy*`/`waitFor` con suites en paralelo o máquina cargada; arreglo
posible `configure({ asyncUtilTimeout: 3000 })` en `apps/frontend/src/test/setup.ts` como decisión de
equipo; **no se corrige aquí**. Dos precisiones de honestidad incluidas en la fila: (a) el fallo se
recoge tal como se observó en la revisión del PR #50 y **no se reprodujo en JUP-099** (la suite
completa ejecutada sola pasa 261/261); (b) el pool por defecto de Vitest 3 es `forks`, donde la
opción `poolOptions.threads.maxThreads` de la observación original podría no tener efecto, punto a
confirmar cuando alguien aborde el finding. Severidad `Medium` porque afecta a la verificación de
todas las tarjetas de frontend; el dueño real lo decide el equipo.

**Checkpoint:** tareas doc-only, sin Red/Green ni mutación (excepción doc-only). Ningún archivo de
producto ni de test tocado.

**2.3 — Referencias a configuración local del agente retiradas de la documentación de JUP-098.**
Sustituidas las 9 menciones (más el aviso "harness local, no se commitea") en
`docs/evidence/JUP-098-validation.md` (3) y en el `review.md` archivado de JUP-098 (6):

- **Stryker:** la invocación con archivo de configuración local pasa a la invocación sin archivo
  (`--mutate`, `--testRunner vitest`, `--plugins`, `--reporters`, `--coverageAnalysis perTest`,
  `--concurrency 2`). **Verificada de nuevo en esta tarjeta** (2026-09-29, `--dryRunOnly` desde
  `apps/frontend`): "No config file specified. Running with command line arguments.", 109 mutantes
  en `api.ts` y pasada inicial de 233 tests en verde. El umbral 80 se documenta como criterio de
  lectura del resultado (no tiene opción de línea de comandos); se indica borrar `.stryker-tmp`
  al terminar (borrado tras la verificación; el repositorio queda limpio).
- **Comprobador local de DoD:** sustituido por los comandos reales del repositorio
  (`corepack pnpm test/lint/typecheck` desde la raíz, que fallan por RF-093-001, y el sustituto
  `--filter @finops/frontend`). La línea del "escaneo de secretos" se elimina: no tiene equivalente en
  el repositorio, y `jup:cleanup:check` ya consta en la evidencia.
- **Excepción y protección de tests:** redacción neutral ("excepción doc-only"; "el test estaba
  protegido contra edición en el entorno local y se editó con autorización del usuario").

Verificación: `git grep` de `.claude/`, `check-dod`, `stryker.conf`, `lock-committed`,
`harness/workflow` y `mutation.md` sobre ambos archivos devuelve **0** resultados. No se ha tocado
ningún otro contenido de esos documentos (cifras, veredictos, enlaces).

**Hallazgo al verificar (no se corrige en esta tarea):** la misma deuda existe **fuera de JUP-098**.
La búsqueda sobre todos los archivos versionados encuentra referencias equivalentes en los
documentos archivados de JUP-092 a JUP-097 (`review.md`, `tasks.md`) y en las evidencias de JUP-093,
JUP-095 y JUP-097, además de un comentario en `apps/frontend/vite.config.ts` (línea 40, cita
`.claude/harness/mutation.md`) y en comentarios de test. El arrastre acordado solo cubre JUP-098: por decisión
de Victor (2026-09-29) **no se amplía** y se registra como `RF-099-001` en el backlog, con el recuento
medido (42 menciones en 11 archivos) y las sustituciones ya probadas en esta tarea.

**Observaciones sobre lo que ya decía la evidencia de JUP-098 (no modificadas):** (a) la frase "en
los tres archivos el score global queda por debajo del umbral" contradice la fila de `api.ts`
(88.99%, por encima del 80); (b) cita `RF-093-001` como "pendiente de JUP-102", pero tras la
renumeración del 2026-09-29 el turbo es JUP-101.

**Checkpoint:** doc-only, sin Red/Green ni mutación. `openspec:validate`, `jup:check` y
`jup:cleanup:check` en verde.

**Finding `RF-099-001` registrado** en `openspec/findings/backlog.md` (decisión de Victor, 2026-09-29):
la deuda de referencias a configuración local del agente fuera de JUP-098 se registra y no se corrige
aquí. Recuento medido con `git grep -F` de `.claude/`, `check-dod`, `stryker.conf`, `lock-committed`,
`harness/workflow` y `mutation.md`, excluyendo tests, `.gitignore`, `.dockerignore`,
`tools/jup-cleanup-check.mjs` y los documentos de JUP-098/099: **42 menciones en 11 archivos** (36 en
7 archivos archivados de JUP-092 a JUP-097, 5 en 3 evidencias, 1 comentario en
`apps/frontend/vite.config.ts`). Corrección sobre un primer borrador de la fila, que citaba
recuentos escritos sin medir (21 archivos / 45 menciones) y un patrón con `|` que rompía la tabla;
se retiró y se rehízo con cifras medidas y 12 campos.

**2.4 — Enlaces rotos y fila duplicada.** Comprobación previa con un script que resuelve cada enlace
relativo de los dos archivos: exactamente los 3 del plan (`docs/spikes/frontend-migration.md`
líneas 185 y 206, `openspec/findings/backlog.md` línea 23). Corregidos a
`openspec/changes/archive/2026-09-07-jup-094-reconcile-package-json/`,
`.../2026-09-21-jup-097-reconcile-api-layer/` y `.../2026-09-24-jup-085-auth-session-contract/`
(existen). Fila `RF-090-003` duplicada: las dos filas eran idénticas byte a byte (mismo `md5sum`), se
elimina la segunda y queda 1. Resultado: **0 enlaces rotos** en ambos archivos tras los cambios.

**Checkpoint:** doc-only, sin Red/Green ni mutación.

**2.5 — Comentarios de test neutralizados (con autorización expresa de Victor, 2026-09-29).**
Reescritos los comentarios de 10 archivos de test que citaban el hook o el harness local, cambiando
"bloqueado por el hook del harness" (y variantes: `lock-committed-tests.mjs`, "harness TDD bloquea su
edicion", la ruta de la configuración de Stryker) por "protegido contra edición en el entorno local":
`label.mutation`, `select.mutation`, `separator.mutation` (en `components/ui/`), `Layout.selector`,
`SessionGate.mutation`, `SessionGate.profile`, `SessionGate.validation`, `DashboardPage.mutation`,
`api.session-generation-advance` y `tests/dashboard-tenant-transition`.

- **Solo comentarios:** `git diff -U0 -- apps/frontend` filtrando las líneas que no empiezan por `//`
  devuelve **0** líneas; 10 archivos, 16 inserciones y 17 eliminaciones. Ninguna aserción ni código de
  test tocado.
- **Sin menciones restantes:** `git grep` de `hook`, `harness`, `lock-committed`, `.claude` y
  `stryker.conf` sobre esos 10 archivos y sobre todos los tests del frontend (salvo `HarnessSmoke`,
  que nombra el arnés de pruebas de Vitest, no el entorno local) devuelve 0.
- **Suite intacta:** `typecheck` (3 configs) y `lint` sin salida; `test` → **46 archivos, 261/261
  PASS**, idéntico a la línea base de 1.1.
- **Sobre la protección de tests:** las 10 ediciones se aplicaron sin necesidad de desactivar ningún
  mecanismo, así que no hubo nada que restaurar. Un primer intento sobre `SessionGate.validation`
  falló por un desajuste de texto mío (la primera línea del bloque tiene texto delante) y se repitió
  sobre la segunda línea; no fue un bloqueo.
- Los avisos del IDE sobre `toBeVisible`/`toBeInTheDocument` en
  `tests/dashboard-tenant-transition.test.tsx` no proceden de la edición (cambio solo de comentario)
  ni del `typecheck` de la tarjeta, que pasa con exit 0: el IDE no resuelve los tipos de jest-dom de
  ese directorio.

**Cierre del grupo 2:** arrastre de JUP-098 resuelto: A (`RF-098-004`), B (9 referencias), y de C los
enlaces rotos, la fila duplicada y los comentarios de test; `RF-098-003` fuera de alcance y el resto
de la deuda registrada como `RF-099-001`. Todo doc-only o solo comentarios: sin Red/Green ni mutación.

## Grupo 3. Tests guardianes en Red

**3.1 — Red: `apps/frontend/src/test/color-tokens.guard.test.ts` (nuevo, 61 casos).** Escrito por el
agente `tester`; verificado por el orquestador ejecutándolo. Escanea los `*.tsx` de `src/` y los
`*.ts` de `src/data/`, sin tests ni `src/test/`, en busca de hexadecimales y de utilidades de la
paleta de Tailwind, con lista de excepciones `{ file, value, reason }`: `ExportButton.tsx`
(`#1e40af`, `#ddd`: el `<style>` del documento HTML autónomo que no carga `theme.css`) y
`ui/dialog.tsx` (`bg-black/50`, primitivo copiado tal cual). Casos: 1 por archivo escaneado, 1 por
excepción (falla si queda obsoleta), 29 del detector en memoria y 1 de descubrimiento de archivos
(evita el falso verde de un recorrido roto).

- **Red:** `16 failed | 45 passed`. Fallan exactamente los archivos con colores literales: `Layout`,
  `SessionGate`, `ExportButton`, `MetricCard`, `SectionCard`, `StatusPill`, `AnomaliesPanel`,
  `ConversationsPage`, `DashboardPage`, `ExecutiveCostDashboard`, `ExecutiveCutDashboard`,
  `IngestPage`, `LoginPage`, `OperationalCostDashboard`, `RecommendationsPanel` y
  `data/demo/executiveCostDashboard.ts`. `dialog.tsx` pasa por su excepción. `ExportButton` falla por
  sus clases, no por las dos excepciones. El mensaje de fallo da archivo, línea y valor.
- **Detalle de diseño del test:** el detector exige tono de escala salvo para `white`/`black`
  (`text-neutral` es un token semántico de la decisión 1 y no debe marcarse; `text-neutral-500` sí).
  Límite conocido: no detecta `rgb(`/`hsl(` ni palabras de color (`color: white`) dentro del `<style>`
  de `ExportButton`; no hay `rgb`/`hsl`/`oklch` literales en los `.ts/.tsx` no test.

**3.2 — Red: `apps/frontend/src/test/theme-palette.test.ts` (nuevo, 94 casos).** Contrato del tema:
(a) sin bloque `.dark` y `@custom-variant dark` exactamente `(&)`; (b) cada token declarado una sola
vez; (c) cada `var(--x)` de `@theme inline` apunta a un token declarado; (d) un caso por token
`--color-*` que exige al menos un consumidor en `src/`; (e) `<html>` sin la clase `dark`. Un
consumidor es una utilidad con el nombre del token (variantes y `/opacidad` opcionales) o
`var(--nombre)`/`var(--color-nombre)`, con frontera a ambos lados (`bg-primary-foreground` no
cuenta para `primary`; `border`/`border-b` no cuentan para `border`; `var(--chart-10)` no cuenta
para `chart-1`). De `theme.css` solo cuenta lo que queda fuera de `:root` y `@theme inline`.

- **Red:** `25 failed | 69 passed`: (a) 3 de 3 (bloque `.dark`, `@custom-variant` con `.dark`, y no
  es `&`), (b) 1 (34 nombres repetidos entre `:root` y `.dark`), (e) 1 (`<html class="dark">`), y
  (d) 20 tokens sin consumidor hoy: `card`, `card-foreground`, `muted`, `secondary`,
  `secondary-foreground`, `destructive-foreground`, `switch-background`, `chart-1..5` y los 8
  `sidebar-*`. Pasa (c) (41 alias correctos) y los casos autocontenidos.
- **Qué cabe esperar del Green:** `card`, `muted` y `chart-*` pasarán al migrar las pantallas
  (grupos 5-7), no al retirar el token; `secondary`, `secondary-foreground`,
  `destructive-foreground` y los `sidebar-*` no tendrán consumidor y se retirarán en 8.3;
  `switch-background` también.
- **Test retirado con autorización expresa de Victor (2026-09-29):**
  `apps/frontend/src/test/index-html-dark-scope.test.ts` (JUP-095, 1 caso) exigía `class="dark"` en
  `<html>` y contradice al caso (e). Se borra en este mismo commit Red para que el Green del grupo 4
  no toque ningún test. Su cobertura la sustituye (e), que además comprueba el atributo como
  conjunto de palabras. No hubo que desactivar ningún mecanismo de protección.

**Corrección de diseño descubierta por el `tester` (mi error, decisión 3 de `design.md`):** la
primera redacción retiraba `input-background`, pero `src/components/ui/select.tsx` lo consume
(`bg-input-background`) y la decisión 2 prohíbe editar los primitivos. Se **conserva** con su valor
actual `#f3f3f5`, sin efecto visible (`dark:bg-input/30`, siempre activo con `@custom-variant dark
(&)`, prevalece; ninguna pantalla usa `Select`). `design.md` corregido con nota. Lo detectó el propio
caso (d), que sin esa comprobación habría dejado un `bg-input-background` sin efecto.

**Conteos del Red (verificados por el orquestador):** suite completa `Test Files 2 failed | 45
passed (47)`, `Tests 41 failed | 374 passed (415)`. Los 374 = 260 previos (261 menos el caso del test
retirado) + 45 + 69; **los 41 fallos son todos casos Red de los dos archivos nuevos**. `typecheck`
(3 configs) y `lint` sin errores. Sin `.skip`, `.only` ni `xit`.

**Checkpoint:** commit **Red** (2 archivos nuevos + 1 test borrado + `design.md`, `review.md` y
`tasks.md`). Sin mutación en este grupo (solo tests; la de los grupos de migración está exenta por
la decisión 5 de `design.md`). El siguiente grupo es el Green.

## Grupo 4. Paleta única en el tema (Green)

**4.1 — Green: `apps/frontend/src/styles/theme.css` reescrito** por el agente `coder` (revisado por el
orquestador). Un solo bloque `:root` con 4 tokens no cromáticos (`--font-size`, dos pesos de fuente,
`--radius`) y 41 de color con los valores de la decisión 1; `@theme inline` con un `--color-*` por
token y los 4 `--radius-*`; `@layer base` idéntico; sin bloque `.dark`; cabecera en español con el
porqué; `@custom-variant dark (&);`. **4.2:** `class="dark"` retirado de `<html>` en `index.html`
(único cambio del archivo). No se ha tocado ningún test ni ningún archivo más.

Desviaciones respecto al encargo, todas sin cambio de valores y recogidas en `design.md`:
`card-foreground`, `secondary*`, `destructive-foreground`, `sidebar-*` y `switch-background` no se
definen (sin consumidor); `border` es la definición literal y `muted`/`input` son alias de
`var(--border)`.

**¿Acepta Tailwind `@custom-variant dark (&);`? Sí, verificado compilando.** Build fuera del repo
(2478 módulos, CSS 41,77 kB) sin errores; las variantes de los primitivos salen bien formadas, sin
`.dark` como ancestro ni `prefers-color-scheme`:
`.dark\:bg-input\/30{background-color:var(--input)}` (con su rama `color-mix(in oklab, var(--input)
30%, transparent)`), `.dark\:hover\:bg-input\/50:hover{…}`,
`.dark\:aria-invalid\:ring-destructive\/40[aria-invalid=true]{--tw-ring-color:var(--destructive)}` y
`.dark\:bg-black\/50{background-color:#00000080}`. (La parte `.dark\:` es el nombre de la clase de
utilidad, no un selector de ancestro.)

**4.3 — Verificación (ejecutada por el orquestador):**

| Comprobación | Resultado |
| --- | --- |
| `theme-palette.test.ts` | **82 pasan / 28 fallan** (110). Pasan (a) sin `.dark` y `@custom-variant` exacto, (b) tokens únicos, (c) alias resueltos, (e) `<html>` sin `dark`, y los (d) de los 14 tokens con consumidor hoy: `background`, `foreground`, `border`, `ring`, `primary`, `primary-foreground`, `popover`, `popover-foreground`, `accent`, `accent-foreground`, `destructive`, `input`, `input-background`, `muted-foreground` |
| Casos (d) aún en Red (28) | `card`, `muted`, `subtle-foreground`, `neutral`, `highlight`, `positive`, los 14 de estados (`success*`, `danger*`, `info*`, `warning*`, `attention-*`) y los 8 `chart-*`: sin consumidor hasta migrar pantallas (grupos 5-7), como estaba previsto |
| `color-tokens.guard.test.ts` | 16 fallan / 45 pasan, sin cambios (no depende del tema) |
| Suite completa | `Tests 44 failed \| 387 passed (431)`, `Test Files 2 failed \| 45 passed`. 387 = 260 previos + 45 + 82: **ningún test previo se rompe**; los 44 fallos son los 16 del guardián y los 28 (d) |
| `typecheck` / `lint` | exit 0 / exit 0 |

**Captura visual intermedia (no exigida por `tasks.md`; decisión del orquestador).** El Green cambia
el tema pero aún no migra ninguna pantalla, así que cualquier diferencia visual ahora es atribuible
solo al tema. `node compare.mjs shots-before-1 shots-g4` (umbral 0) → `login`, `login-*` y
`operational-cost`: **0 px**. El resto tiene diferencias, analizadas por caja envolvente y pares de
color (`analyze.mjs`); solo hay **tres causas**:

| Causa | Píxeles y color | Dónde | Origen |
| --- | --- | --- | --- |
| Fondo del `body` | `#0a0a0a → #0f1419` en el **100 %** de los píxeles distintos: 455 040 (`assistant`, 316 filas), 270 720 (`ingest`, 188), 218 880 (`ingest-error`), 267 840 (`overview-legacy`, 186) | franja bajo el contenido en pantallas más cortas que el viewport | `background` pasa de `oklch(0.145)` a `#0f1419`. Es lo que ya se anticipó en el grupo 1 |
| Color heredado por los iconos | `#fafafa → #ffffff` (más sus antialias, p. ej. `#c3c4c7 → #c7c8cb`) | 549-761 px en `executive-cost` (×3 capturas), `executive-cuts`, `recommendations` y 71 en `anomalies`; siempre en una caja de ≈30-40 filas, los iconos de las tarjetas KPI | los iconos de Lucide usan `currentColor` y heredan `foreground`, que era `oklch(0.985)` = `#fafafa` y ahora es `#ffffff` |
| Borde por defecto | `#262626 → #2d3748` (88 px, más antialias) | `executive-cuts`, caja de un icono de tarjeta | un elemento con `border` sin color usaba el borde por defecto de la capa base (`oklch(0.269)` de shadcn); ahora usa el token `border` de la aplicación |

Ninguna de las tres es un color de pantalla migrado: son efectos del cambio de tema sobre lo que
**no** lleva color propio. Se consideran deliberadas y coherentes con la paleta de la aplicación (el
fondo y el borde adoptan el color que el resto de la interfaz ya usaba; los iconos pasan a ser del
blanco del texto). Son **cinco niveles de luminancia** en los iconos: imperceptibles a simple vista,
pero reales, así que constan para su aceptación explícita en la tarea 8.1.

**Invariante para los grupos 5-7:** `shots-g4` pasa a ser la referencia intermedia. Migrar clases y
atributos de color a tokens con el mismo valor debe dar **exactamente 0 px** de diferencia contra
`shots-g4`; cualquier otro resultado es una regresión de la migración y no del tema. En 8.1 se
compararán ambas: `shots-before-1` → final (las tres causas de arriba, aceptadas) y `shots-g4` →
final (0).

**Checkpoint:** commit **Green**. Sin mutación (exención de la decisión 5 de `design.md`: código de
producto = valores CSS, que ninguna prueba unitaria de comportamiento ejerce; protegen los dos tests
estáticos y la comparación visual).

## Grupo 5. Armazón y componentes compartidos

**Antes de migrar: el guion pasa de 14 a 20 escenarios.** `SessionGate` tiene dos estados con color
propio que las capturas no veían (carga y error del bootstrap de tenants) y otras pantallas tienen
estados de error/éxito igual de ciegos. Se añaden 6: `session-tenants-loading`,
`session-tenants-error`, `overview-legacy-loading`, `overview-legacy-error`, `ingest-success` y
`assistant-send-error`. Se recapturó el baseline (`dist-before`) y el estado del grupo 4 (`dist-g4`)
con los 20. Determinismo del baseline verificado con dos pasadas: 0 px en los 20. Las diferencias
del tema en los 4 escenarios nuevos que cambian son solo la franja `#0a0a0a → #0f1419`
(`assistant-send-error` 403 200 px, `ingest-success` 8 640, `overview-legacy-error` 901 440,
`overview-legacy-loading` 452 160; 100 % del mismo par de colores); `session-tenants-*` dan 0.

**5.1, 5.2 — Green: 6 archivos migrados** por el agente `coder` (revisado por el orquestador):
`layouts/Layout.tsx` (41 utilidades), `layouts/SessionGate.tsx` (14), `components/ExportButton.tsx`
(13), `components/MetricCard.tsx` (8), `components/SectionCard.tsx` (5), `components/StatusPill.tsx`
(3). Solo cambian utilidades de color con la tabla de sustitución, sin tocar orden de clases,
modificadores de opacidad, variantes, lógica, props ni estructura JSX; el filtro de líneas
cambiadas que no son clase ni comentario devuelve 0. Ningún color quedó sin token. La excepción de
`ExportButton` (`#1e40af`, `#ddd` del `<style>` del documento de impresión) se conserva.

**5.3 — Trasladada al grupo 7.** La constante compartida del `contentStyle` de los tooltips de
Recharts no tiene consumidor hasta que se migren las gráficas (grupo 7); crearla ahora habría dejado
código sin uso. Se hará en la tarea 7.1, donde se consume.

**5.4 — Sin referencias al sistema anterior.** Reescritas las cabeceras de `MetricCard`, `SectionCard`
y `StatusPill`: ya no citan `main.css`, `metric-card`, `tone-*`, `status-pill` ni "la versión .jsx" como
origen de clases; conservan el porqué del mapa cerrado de clases de `MetricCard` (Tailwind no detecta
clases construidas por interpolación). `grep -rniE 'main\.css|status-pill|metric-card|tone-'` sobre
`apps/frontend` (sin tests) devuelve **0**. Criterio 3 de la tarjeta cumplido.

**5.5 — Verificación (ejecutada por el orquestador):**

| Comprobación | Resultado |
| --- | --- |
| Guardián de colores | **51 pasan / 10 fallan** (antes 45 / 16). Pasan los 6 archivos migrados y las excepciones de `ExportButton` y `dialog`; siguen en Red solo `pages/*` (9) y `data/demo/executiveCostDashboard.ts` |
| `theme-palette.test.ts` | **92 pasan / 18 fallan** (antes 82 / 28). Todos los fallos son casos (d). Pasan a verde `card`, `muted`, `success`, `success-tint`, `success-foreground`, `info-tint`, `warning`, `positive`, `highlight`… Siguen sin consumidor: `subtle-foreground`, `neutral`, `danger-tint`, `danger-foreground`, `info`, `info-foreground`, `warning-tint`, `warning-foreground`, `attention-tint`, `attention-foreground`, `chart-1..5`, `chart-negative`, `chart-baseline`, `chart-axis` |
| Suite completa | `Tests 28 failed \| 403 passed (431)`, `Test Files 2 failed \| 45 passed`. 403 = 260 previos + 51 + 92: ningún test previo se rompe. Los 28 fallos son 10 del guardián + 18 (d), todos aserciones Red, sin timeouts |
| `typecheck` / `lint` | exit 0 / exit 0 |
| Diff | 6 archivos, 66 inserciones y 69 eliminaciones |

**Primera ejecución anómala, no reproducida.** Mi primera ejecución de la suite tras el Green dio
`14 failed files | 55 failed tests` (no los 28 esperados), lanzada mientras otro comando corría en
paralelo y con la CPU de la máquina entre el 38 % y el 74 % por procesos ajenos (los `chrome` en
marcha son del navegador del usuario, ninguno de Playwright). No guardé qué tests fallaron en esa
pasada, así que **no puedo demostrar la causa**. Lo único comprobado: repetida en solitario, con el
mismo código, da exactamente 28/403 con los fallos esperados; es coherente con `RF-098-004`
(tiempos de espera de `findBy*` bajo carga) pero no lo confirma. Se anota sin más conclusión.

**Verificación visual del grupo 5 (contra la referencia del grupo 4, 20 escenarios):** 19 de 20 dan
**0 px**; `ingest-success` daba 11 px. Analizado por color: `#272f3f → #262f3e`, `#2a3444 → #2a3344`…,
todos de 1 nivel de canal en píxeles de degradado. Control: **el mismo build `dist-g4` capturado dos
veces** difiere en `assistant` (4 px) e `ingest-success` (11 px), también de 1 nivel. Es ruido del
rasterizador, no regresión. Consecuencia: el criterio "umbral 0" a secas no era honesto, así que
`compare.mjs` ahora separa píxeles **reales** (algún canal distinto en ≥ 2 niveles) de los de 1
nivel, y el criterio pasa a ser **0 reales y ≤ 50 px de 1 nivel por escenario** (`design.md`,
decisión 6). Con él, comparando entre las tres pasadas disponibles: `g4b → g4c` 0 reales (15 px de
ruido), `g4c → g5` 0 reales (4 px), `g4b → g5` **0 reales** (11 px). **La migración del armazón y
los componentes no cambia ningún píxel de forma real.** El invariante del grupo 4 se cumple.

Límite conocido de esta prueba: un cambio de 1 nivel sobre un color plano de área pequeña quedaría
clasificado como ruido si no supera los 50 px. Lo mitiga que los valores de los tokens se comprueban
contra su origen en `theme.css` (mismo texto que el literal sustituido) y que un token equivocado
altera áreas enteras, no una decena de píxeles.

**Checkpoint:** commit **Green**. Sin mutación (exención de la decisión 5).

## Grupo 6. Pantallas conectadas al backend

**Antes de migrar: el guion pasa de 20 a 25 escenarios.** Se añaden 5 estados de estas pantallas que
no se veían: `assistant-empty` (lista vacía), `assistant-create-error` (error al crear conversación
en rojo) y las tres ramas "sin tenant" (`no-tenant-ingest`, `no-tenant-assistant`,
`no-tenant-overview`, con `GET /tenants` vacío). Determinismo de los 5 sobre el baseline: dos
pasadas, 0 px. Contra el baseline, el tema solo cambia la franja `#0a0a0a → #0f1419` (100 % de los
píxeles distintos en los 5). Comparados con la referencia del grupo 5: 0 reales. Referencias
consolidadas a 25 escenarios (`ref-before`, `ref-g4`, `ref-g5`).

**6.1 — Green: 4 archivos migrados** por el agente `coder` (revisado por el orquestador):
`LoginPage.tsx` (22 utilidades, incluido el aviso ámbar de sesión expirada, `text-amber-400` →
`text-warning`, sin tocar `role="status"` ni su lógica), `IngestPage.tsx` (19), `ConversationsPage.tsx`
(27) y `DashboardPage.tsx` (15): 83 utilidades en 59 líneas. Todos los colores estaban en la tabla; el
filtro de líneas que no son clases de color devuelve 0. (El `coder` señaló que su recuento por archivo
difería en una unidad de mi inventario previo en dos archivos; los totales por color sí cuadran.)

**6.2 — Verificación (ejecutada por el orquestador, cada comando en solitario):**

| Comprobación | Resultado |
| --- | --- |
| Guardián de colores | **55 pasan / 6 fallan** (antes 51 / 10). Los 6 restantes son justo los del grupo 7: `AnomaliesPanel`, `ExecutiveCostDashboard`, `ExecutiveCutDashboard`, `OperationalCostDashboard`, `RecommendationsPanel` y `data/demo/executiveCostDashboard.ts` |
| `theme-palette.test.ts` | **92 pasan / 18 fallan**, sin cambios: todos (d). Este grupo no cierra ningún (d) porque los tokens que usa (`muted-foreground`, `danger`, `warning`, `primary`…) ya tenían consumidor desde el grupo 5; los 18 restantes son `subtle-foreground`, `neutral`, `danger-tint`, `danger-foreground`, `info`, `info-foreground`, `warning-tint`, `warning-foreground`, `attention-*`, `chart-*` (8), que consumen los dashboards |
| Suite completa | `Tests 24 failed \| 407 passed (431)`, `Test Files 2 failed \| 45 passed`. 407 = 260 previos + 55 + 92: ningún test previo se rompe (incluidos `login-session-expired-notice*`, sesión, ingesta, conversaciones, dashboard y tenant). 0 mensajes de timeout. Los 24 fallos son 6 del guardián + 18 (d) |
| `typecheck` / `lint` | exit 0 / exit 0 |
| Diff | 4 archivos, 59 inserciones y 59 eliminaciones; sin cambios de lógica, texto ni JSX |

**Nota de proceso:** para comprobar que el grupo no cerraba ningún (d), el `coder` usó `git stash`
sobre el árbol de trabajo. Verificado después por el orquestador: `git stash list` vacío y
`git status` con exactamente los 4 archivos esperados; no quedó nada escondido.

**Verificación visual (25 escenarios, contra la referencia del grupo 5):** **0 píxeles reales**
(delta ≥ 2). Solo reaparece el ruido de rasterizado ya caracterizado, idéntico en cantidad:
`assistant` 4 px e `ingest-success` 11 px, ambos de 1 nivel y por debajo del umbral de 50. Es decir,
la migración de `LoginPage` (incluido el aviso ámbar y el error en rojo), `IngestPage`,
`ConversationsPage` (vacía, con error y con conversación) y `DashboardPage` (cargando, en error,
sin tenant y con datos) no cambia ningún píxel de forma real.

**Checkpoint:** commit **Green**. Sin mutación (exención de la decisión 5).

## Grupo 7. Dashboards de demostración

**Antes de migrar: el guion pasa de 25 a 34 escenarios.** Los 9 nuevos son los **tooltips de
Recharts**: su `contentStyle` (9 usos) solo se pinta al pasar el ratón, así que sin captura de hover un
"0 px" no habría dicho nada de él. Se abre con el ratón en el centro de cada `.recharts-wrapper`, tras
esperar a que termine la animación, con un gancho `after` en el guion. Comprobado a ojo que el
tooltip aparece (con el color de cada serie y el cursor de barras). Determinismo del baseline en los 9:
dos pasadas, 0 px. Contra el baseline, el tema cambia en ellos solo lo ya conocido: los iconos
`#fafafa → #ffffff` y el borde `#262626 → #2d3748`, con las mismas cantidades que en las pantallas
sin tooltip (el tooltip en sí no cambia con el tema).

**7.1, 7.2, 7.3 — Green: 5 dashboards, datos demo y `chartTheme.ts`** por el agente `coder`
(revisado por el orquestador):

| Archivo | Clases | Atributos Recharts | Tooltips |
| --- | --- | --- | --- |
| `ExecutiveCostDashboard.tsx` | 37 | 16 | 3 |
| `OperationalCostDashboard.tsx` | 63 | 15 | 2 |
| `ExecutiveCutDashboard.tsx` | 53 | 19 | 2 |
| `AnomaliesPanel.tsx` | 49 | 8 | 1 |
| `RecommendationsPanel.tsx` | 60 | 3 | 1 |
| `data/demo/executiveCostDashboard.ts` | – | – | 4 colores → `var(--chart-1..4)` |

(Recuentos de clases aproximados, del `coder`; el diff exacto es `git diff`.) `fill`/`stroke` de
Recharts pasan a `var(--token)` (`--border` para la rejilla, `--chart-axis`, `--highlight`, `--primary`,
`--chart-baseline`, `--chart-2`, `--chart-negative`, `--chart-5`). Nuevo
`apps/frontend/src/components/chartTheme.ts` con `chartTooltipStyle` (4 propiedades, mismo orden que el
literal original, comentario en español), usado en las 9 gráficas (**tarea 5.3, trasladada**).
**Confirmado por la comparación visual:** Recharts resuelve `var(--…)` en atributos SVG y en
`contentStyle`; series, ejes, rejilla, leyendas, sectores y tooltips son idénticos.

**`#8884d8` (7.3):** el `coder` eliminó el atributo `fill` del `<Pie>` con un comentario en español.
34 capturas sin diferencia real: no se pintaba. Resuelto.

**Hallazgo del `coder`, decisión de diseño (ver `design.md`, decisión 4): clases interpoladas.** Cuatro
pantallas construían clases con `text-${color}-400`, `bg-${color}-500/20 border-${color}-500/30` y
`font-bold text-${color}-400`. Tailwind no las detecta; existían **por casualidad**, porque el literal
completo aparecía en otra línea. Migrar esos literales a tokens las habría dejado de generar, y las
pantallas habrían cambiado sin que ninguna prueba lo detectara. Se sustituyen por mapas cerrados
(`toneIconClass`, `toneBoxClass`, `toneTextClass`, `Record<string, string>`, con `?? ''`) en
`ExecutiveCostDashboard`, `ExecutiveCutDashboard`, `AnomaliesPanel` y `RecommendationsPanel`. Los
tonos que antes no generaban clase (`purple` siempre; `orange` en texto de icono y valor) siguen sin
ella. Es un cambio de estructura más allá de "cambiar el color", justificado y verificado por las
capturas (0 reales); revisado por el orquestador: solo quedan las interpolaciones citadas en
comentarios. Se registra `RF-099-002` (aspecto sin color de esos tonos, preexistente).

**7.4 — Verificación (ejecutada por el orquestador, cada comando en solitario):**

| Comprobación | Resultado |
| --- | --- |
| Guardián de colores | **61/61 pasan.** Solo quedan las excepciones declaradas (`#1e40af`, `#ddd` de `ExportButton`; `bg-black/50` de `dialog`) |
| `theme-palette.test.ts` | **110/110 pasan**: todos los casos (d) en verde |
| Suite completa | **`Test Files 47 passed`, `Tests 431 passed (431)`**, 0 timeouts. 431 = 260 previos + 61 + 110. Es la primera vez que la suite queda entera en verde tras el Red del grupo 3 |
| `typecheck` / `lint` | exit 0 / exit 0 |
| Búsqueda de hex en `src` (sin tests) | solo las 3 líneas de la excepción de `ExportButton` (45, 47, 48) |

**Comprobación adicional: ¿el (d) verde es genuino?** El `tester` avisó de que un token citado solo
en un comentario contaría como consumidor. Se repitió el análisis **ignorando comentarios**
(`consumers.mjs`): 42 tokens `--color-*`, **0 sin consumo real**. (Un primer intento dio 7 tokens sin
consumo, `chart-*`; era un fallo de mi script, no del código: el shell colapsó las barras `\` de una
expresión regular escrita en un heredoc y `var\(--chart-axis\)` nunca casaba. Un `grep` directo ya
mostraba 30+ usos. El script se reescribió con la herramienta de archivos y el resultado es el
anterior.) Mínimo de consumidores: 1 archivo en 11 de los tokens (los de los primitivos de shadcn
`select`/`tooltip`, `positive`, `warning-foreground`, `chart-1`, `chart-3`).

**Verificación visual (34 escenarios, contra la referencia del grupo 6): 0 píxeles reales.**
Diferencias de 1 nivel de canal en dos escenarios, **de naturaleza distinta**, comprobado capturando
cada build dos veces:

- **`ingest-success`: ruido aleatorio.** 31 px en esta pasada; entre pasadas del mismo build da 7
  (g6 vs g6) y 24 (g7 vs g7); entre builds distintos dio 0 en la repetición. Cambia de una pasada a
  otra. Dentro del criterio (≤ 50).
- **`recommendations` (y `tooltip-recommendations-0`, la misma zona): diferencia sistemática de
  1 nivel, 1 410 px.** g6 vs g6 = 0, g7 vs g7 = 0, g6 vs g7 = 1 410 **las dos veces**. Caja x 29-1404,
  y 1737-1879: el panel de agentes, un degradado (`from-primary/20 to-chart-4/20`; antes
  `from-[#0078d4]/20 to-[#8b5cf6]/20`). No es ruido: es reproducible, así que **no la doy por
  buena por el umbral**, la explico. Causa, leída en el CSS generado: para un hex arbitrario con
  opacidad Tailwind calcula el color **en tiempo de build** y escribe un literal redondeado
  (`oklab(56.7687% -.0533597 -.157766/.2)`); con un token emite `color-mix(in oklab, var(--primary)
  20%, transparent)`, que el navegador evalúa con precisión completa. Es el mismo color con otro
  redondeo: **1 nivel de canal**, imperceptible, solo visible en un degradado. Es inherente al
  mecanismo que pide la tarjeta (usar el token en lugar del literal), no un error de migración.
  Consta para su **aceptación explícita en la tarea 8.1**.

**Diferencias del tema ya acumuladas para 8.1 (grupo 4), sin cambios en este grupo:** franja
`#0a0a0a → #0f1419`, iconos `#fafafa → #ffffff` y un borde `#262626 → #2d3748`. Más la de arriba.

**Checkpoint:** commit **Green**. Sin mutación (exención de la decisión 5).

## Grupo 8. Verificación visual final, propagación y tokens sin consumidor

**8.1 — Comparación final (34 escenarios): las cuatro diferencias, ACEPTADAS por Victor.** Build del estado
final (`81a5e69`, CSS 41,83 kB) capturado con el mismo guion y comparado con las tres referencias:

| Comparación | Resultado |
| --- | --- |
| Grupo 4 → final (solo migración de pantallas) | **0 píxeles reales** (delta ≥ 2). Los 2 820 px de 1 nivel son exactamente 2 × 1 410: el degradado de `recommendations` y su tooltip. **Invariante del grupo 4 cumplido** |
| Grupo 6 → final | 0 píxeles reales (2 824 px de 1 nivel: los mismos 2 820 más 4 de ruido) |
| Baseline original → final | 26 escenarios con diferencias, **8 con 0 exacto**. Todos los píxeles distintos (7 356 701) caen en **una de cuatro causas**, medido con `classify.mjs`: franja 7 346 880 + degradado 2 820 + otros 7 001 (iconos y borde) |

Los 8 escenarios sin ninguna diferencia: `login`, `login-invalid-credentials`, `login-session-expired`,
`operational-cost`, `tooltip-operational-cost-0`, `tooltip-operational-cost-1`,
`session-tenants-error` y `session-tenants-loading`.

Tabla por escenario (píxeles distintos baseline → final; F = franja, D = degradado, O = otros):

| Escenario | Total | F | D | O |
| --- | ---: | ---: | ---: | ---: |
| `anomalies`, `tooltip-anomalies-0` | 71 | – | – | 71 |
| `executive-cost`, `…-export-menu`, `…-tenant-select-focus`, `tooltip-executive-cost-0/1/2` | 615 | – | – | 615 |
| `executive-cuts`, `tooltip-executive-cuts-0/1` | 549 | – | – | 549 |
| `recommendations`, `tooltip-recommendations-0` | 2 171 | – | 1 410 | 761 |
| `assistant` | 455 040 | 455 040 | – | – |
| `assistant-empty` | 852 480 | 852 480 | – | – |
| `assistant-create-error` | 812 160 | 812 160 | – | – |
| `assistant-send-error` | 403 200 | 403 200 | – | – |
| `ingest` | 270 720 | 270 720 | – | – |
| `ingest-error` | 218 880 | 218 880 | – | – |
| `ingest-success` | 8 640 | 8 640 | – | – |
| `overview-legacy` | 267 840 | 267 840 | – | – |
| `overview-legacy-loading` | 452 160 | 452 160 | – | – |
| `overview-legacy-error`, `no-tenant-ingest`, `no-tenant-assistant`, `no-tenant-overview` | 901 440 | 901 440 | – | – |

**Las cuatro causas** (imágenes de revisión `1…4-*.png` entregadas a Victor: arriba antes, medio
después, abajo diferencia amplificada):

1. **Franja bajo el contenido, `#0a0a0a → #0f1419`** (7 346 880 px, 100 % de los píxeles distintos en
   14 escenarios de páginas más cortas que el viewport). El fondo del `body` era el `oklch(0.145)` de
   shadcn y ahora es el `background` de la aplicación, el mismo color del resto de la pantalla. Efecto
   directo y deseado del tema; es la que más píxeles cambia y la más visible.
2. **Iconos sin color propio, `#fafafa → #ffffff`** (5 niveles; 549–761 px por pantalla en
   `executive-cost`, `executive-cuts`, `anomalies` y `recommendations`). Los iconos de Lucide usan
   `currentColor` y heredan `foreground`, que era `oklch(0.985)` y ahora es blanco. Conseguir que
   sigan en `#fafafa` exigiría separar "texto heredado" de "blanco explícito" con un token nuevo y
   revertir unas 65 sustituciones `text-white → text-foreground` (grupos 5-7).
3. **Un borde por defecto, `#262626 → #2d3748`** (88 px + antialias, en `executive-cuts`): la caja del
   icono de la tarjeta "Alcanzado" lleva `border` sin color (su tono `purple` no genera clase, ver
   `RF-099-002`) y usaba el borde por defecto de shadcn; ahora usa el token `border` de la aplicación.
4. **Degradado del panel de agentes de Recomendaciones, 1 nivel de canal** (1 410 px, sistemático y
   reproducible). Tailwind resuelve `from-[#0078d4]/20` en tiempo de build a un literal
   `oklab(56.7687% -.0533597 -.157766/.2)` redondeado, y con un token emite
   `color-mix(in oklab, var(--primary) 20%, transparent)` que el navegador evalúa con precisión
   completa: mismo color con otro redondeo. Imperceptible (la imagen 4 solo lo muestra con la
   diferencia ×80).

Ninguna de las cuatro es un color de pantalla migrado con un token equivocado; son efectos del cambio
de tema y del mecanismo de tokens sobre lo que no llevaba color propio o lo llevaba con opacidad.

**Decisión de Victor sobre 8.1 (2026-09-29): acepta las cuatro diferencias.** Primero pidió revisarlas;
se le entregaron las cuatro imágenes (antes / después / diferencia amplificada) y una explicación de
qué se compara: la misma pantalla, con los mismos datos y el mismo navegador, antes y después de la
migración. Tras verlas acepta explícitamente (1) la franja, (2) los iconos, (3) el borde y (4) el
degradado. Entiende que solo la primera es visible a simple vista y que es una mejora deliberada; las
otras tres son de 1 a 5 niveles de canal o de un elemento diminuto. **Criterio 4 de la tarjeta
cumplido** ("sin regresión visual, verificado pantalla por pantalla y registrado en `review.md`"),
con estas cuatro diferencias aceptadas una a una.

**8.2 — Demostración de propagación (criterio 2 y requisito "Un cambio de token se propaga…").**
Se cambian **dos tokens en `theme.css`**, y solo ese archivo: `--primary: #0078d4 → #ff00ff` y
`--card: #1a1f2e → #3a003a` (este último para cubrir también los tooltips, cuyo `contentStyle` es un
`style` en línea con `var(--card)`). Build fuera del repositorio, `theme.css` restaurado y verificado
con `md5` idéntico y `git diff` vacío; durante la prueba `git status` mostró un único archivo
modificado (`theme.css`); ningún archivo de pantalla ni de componente cambió.

- **Cambian 34 de 34 escenarios**, y el `#3a003a` exacto aparece en los 34 (superficies sólidas de
  tarjeta, login, tooltips…): un solo token llega a toda la interfaz.
- **Propagación por utilidades y por `var()` de Recharts:** `#ff00ff` exacto aparece justo en los
  escenarios con un `bg-primary` sólido o un `var(--primary)` de gráfica: `login` (13 434 px),
  `login-session-expired`, `ingest`/`ingest-error` (49 380), `assistant*` (2 057–28 347),
  `session-tenants-error` (3 603), `executive-cost` (59 099, barras y área de Recharts) y
  `operational-cost` (16 835). **No** aparece en los que no usan `primary` sólido: `executive-cuts`,
  `anomalies`, `overview-legacy*`, `no-tenant-*` (coherente con el código: `DashboardPage`,
  `ExecutiveCutDashboard` y `AnomaliesPanel` no lo usan). Los ceros de `ingest-success`,
  `assistant-create-error` y `login-invalid-credentials` son porque el ratón queda sobre el botón tras
  el clic (`hover:bg-primary/80`, translúcido).
- **Propagación a estilos en línea (tooltips):** en cada pantalla con gráficas, el escenario con
  tooltip tiene más píxeles `#3a003a` exactos que el mismo sin tooltip (`anomalies` +20 262,
  `executive-cost` +9 044 / +5 312 / +20 217, `operational-cost` +9 801 / +19 105,
  `executive-cuts` +20 178 / +21 913, `recommendations` +11 731): el `contentStyle` con `var(--card)`
  sigue al tema.

**8.3 — Tokens sin consumidor.** Inventario final de `theme.css`: `:root` con **46** variables (4 no
cromáticas, 42 de color) y `@theme inline` con 42 `--color-*` y 4 `--radius-*`; contando las
declaraciones como al inicio, **110 → 92**. **Retirados 13 tokens** sin consumidor (cada uno también
como `--color-*`): los 8 `sidebar-*`, `card-foreground`, `destructive-foreground`, `secondary`,
`secondary-foreground` y `switch-background`. Añadidos 21 con nombre de función. `theme-palette.test.ts`
(caso d) **110/110**, y el análisis ignorando comentarios (`consumers.mjs`) confirma **42 tokens, 0 sin
consumo real**. Se conservan con **un solo consumidor** 11 tokens, justificados: los de los primitivos
de shadcn `select`/`tooltip` (`popover`, `popover-foreground`, `accent-foreground`, `input`,
`input-background`, `primary-foreground`, `destructive`), y `positive`, `warning-foreground`, `chart-1`
y `chart-3` (usados una vez, en `MetricCard`, `AnomaliesPanel` y datos demo).

**8.4 — Tonos casi iguales no consolidados**, registrados como **`RF-099-003`** en el backlog por
decisión de Victor: grises `#94a3b8`/`slate-400` v4 y `#64748b`/`slate-500` v4; cuatro verdes
(`chart-2`, `success`, `success-tint`, `positive`); rojos, azules (con las marcas `primary` y
`highlight`), ámbares y naranjas. Consolidar sería rediseño y cambia píxeles.

**Comprobación de mi propio trabajo en este grupo:** el guion tiene ahora 34 escenarios y
determinismo verificado en los añadidos; los conteos de las tablas salen de `classify.mjs` y
`propagation.mjs` (suma de causas = 7 356 701 = total de `compare.mjs`).

## Grupo 9. Licencias, ADR y documentación

Grupo doc-only (sin código de producto ni tests): sin Red/Green ni mutación (excepción doc-only).

**9.1 — `apps/frontend/ATTRIBUTIONS.md` creado** (decisión 7). Qué aplica y qué no, verificado:

- **Código copiado de shadcn/ui (MIT): sí aplica.** 5 primitivos (`src/components/ui/dialog`, `label`,
  `select`, `separator`, `tooltip`) y el helper `cn` de `src/lib/utils.ts`. Se incluye el texto de la
  licencia **copiado literalmente** de `LICENSE.md` del repositorio de shadcn/ui, descargado con `curl` el
  2026-09-29 (`Copyright (c) 2023 shadcn`); un `diff` del bloque del archivo contra el descargado da
  **vacío**. (`WebFetch` devolvió un resumen y no el texto literal, así que no se usó para copiar.)
- **Fotos de Unsplash: no aplica.** `apps/frontend` no contiene imágenes (`.png`, `.jpg`, `.svg`,
  `.ico`…), ni `src/assets`, ni `public/`; ningún archivo de `src/` ni `index.html` las referencia.
- **Fuentes: no aplica.** 0 `@font-face` en el código y **en el CSS final**; la fuente sale de la pila del
  sistema que aplica Tailwind (`-apple-system`, `Segoe UI`, `Roboto`, `Arial`…). El único `font-family`
  del código es el `Arial` del documento de impresión de `ExportButton`.
- **Dependencias npm: no se copian, cada una lleva su licencia.** Licencias leídas del `package.json` de
  las versiones instaladas, no supuestas: `lucide-react` 0.487.0 ISC; `recharts` 2.15.2, `@radix-ui/*` (5
  paquetes), `tailwindcss` 4.3.3, `tw-animate-css` 1.4.0, `clsx` 2.1.1 y `tailwind-merge` 3.6.0 MIT.
  `class-variance-authority` (Apache-2.0) está declarado pero ningún archivo de `src/` lo importa, así
  que no se lista. El archivo avisa de que el bundle incorpora ese código y de que no sustituye a un
  inventario de licencias si la aplicación se distribuyera fuera del equipo.
- Corregí sobre la marcha una frase mía ("usa la pila de fuentes por defecto del navegador"): comprobé
  en el CSS generado que la pila viene de Tailwind y la reescribí con datos.

**9.2 — `docs/adr/ADR-0010-frontend-color-tokens.md`** redactado con el formato de ADR-0003/0004, en
estado **`Proposed`** durante la revisión (pasa a `Accepted` con la aprobación del PR). Recoge contexto
medido (241 + 229 + tokens sin consumo), ocho decisiones (sin colores literales, nombres por función y
valor exacto, paleta única en `:root` con `@custom-variant dark (&)`, valores v4 literales, formas de uso,
sin clases interpoladas, excepciones declaradas, cumplimiento por tests), consecuencias (incluidos los
puntos ciegos del guardián y el redondeo de opacidades), alternativas y evidencia. **Índice:**
`docs/adr/README.md` no lista los ADR (solo describe convenciones), así que no hay entrada que añadir.
Enlazado desde el seguimiento de `ADR-0004` junto con `ATTRIBUTIONS.md`.

**Corrección menor en `ADR-0004`:** el enlace de la línea 20 apuntaba a
`openspec/changes/jup-094-reconcile-package-json/design.md` (sin `archive/`), roto por el archivado de
JUP-094. Corregido a `.../archive/2026-09-07-jup-094-reconcile-package-json/design.md` (existe). Solo
un enlace, sin tocar la decisión del ADR.

**9.3 — `apps/frontend/README.md`:** stack (enlace a ADR-0010 y a la sección nueva), estructura
(`chartTheme.ts`, `theme.css` como única paleta, los dos tests de reglas de color y `ATTRIBUTIONS.md`) y
una sección nueva **"Estilos y colores"** con la regla (ningún color literal), una tabla "necesitas →
escribe", cómo cambiar y añadir un token, la prohibición de clases interpoladas, las excepciones y los
tests que lo hacen cumplir. Comprobado que todos los tokens de la tabla existen en `theme.css` y que los
enlaces del README resuelven.

**9.4 — `docs/spikes/frontend-migration.md`:** la tarjeta `jup-0xx-unificar-estilos-assets` pasa a
`JUP-099` / `jup-099-unify-styles-assets`, carril `standard`, con las casillas marcadas con el alcance
real (más de lo que el spike describía: tres fuentes de color, 241 + 229 ocurrencias; nada que migrar
en assets pero sí atribución de shadcn/ui; verificación visual de 34 escenarios; hallazgos nuevos), y
una entrada 10 en la lista numerada que cuenta cómo el spike se quedó corto y que con esta tarjeta F3
queda completa. El enlace al change apunta a la carpeta **activa**
(`openspec/changes/jup-099-unify-styles-assets/`): **hay que corregirlo a `archive/<fecha>-…` en el
mismo paso del archivado**, lección de JUP-098.

**Observación: más deuda de enlaces rotos por archivados. Registrada como `RF-099-004` por decisión de
Victor (2026-09-29); no se corrige aquí.** Un primer chequeo de los `.md` de `docs/` y de los README
encontró **18 enlaces rotos** (tras la corrección de `ADR-0004`): `docs/evidence/JUP-085-validation.md`
(8), `docs/adr/ADR-0007-backend-cors-policy.md` (5), `docs/evidence/JUP-097-validation.md` (2),
`docs/planning/JUP-097-frontend-data-gap-map.md` (1), `docs/evidence/JUP-013-validation.md` (1) y
`docs/adr/ADR-0003-frontend-typescript.md` (1). (Mi primer desglose de esta nota decía 4 para
`JUP-085-validation.md` y omitía los dos ADR; lo corregí tras el recuento por archivo.)

Para el finding amplié la medición a **todos los `.md` versionados** y **clasifiqué la causa** en vez de
suponerla (`brokenlinks.mjs`): hay **71 enlaces rotos = 18 + 53, 0 sin explicar**. **(A) 18**: el destino es
la carpeta de un change que ahora vive en `openspec/changes/archive/<fecha>-<change>/` (los 18 de
arriba). **(B) 53**: enlaces dentro de documentos ya archivados a los que les falta un `../` porque la
carpeta bajó un nivel; por change archivado: JUP-094 (14), JUP-085 (11), JUP-095 portar (11), JUP-092 (7),
JUP-097 (5), JUP-091 (2), JUP-095 reconciliar (1), JUP-013 (1) y JUP-043 (1). En ambos casos el script
comprobó que el destino corregido **existe**, así que el arreglo es mecánico. JUP-099 corrige solo 4 (los
3 del arrastre de JUP-098 y el de `ADR-0004`). Mi hipótesis inicial ("por archivado") resultó correcta
pero incompleta: dos tercios de los casos (B) no eran del tipo que yo había mirado al principio.

## Grupo 10. Cierre

Grupo doc-only y de verificación (sin código de producto ni tests nuevos): sin Red/Green ni mutación.

**10.1 — Ningún archivo de `apps/backend` ni de `apps/processor` en el diff.**
`git diff origin/develop...HEAD --name-only | grep -E '^apps/(backend|processor)/'` → **0** coincidencias,
sobre 46 archivos (+3 038 / −511; 14 commits propios): 30 en `apps/frontend/src`, 1 en `apps/frontend/tests`,
`index.html`, `README.md` y `ATTRIBUTIONS.md` del frontend, 7 en `openspec/changes`, 2 en `docs/adr`, y uno
en cada uno de `openspec/findings`, `docs/spikes` y `docs/evidence`.

**Estado de `develop` antes del PR.** `develop` ha avanzado un commit desde nuestra base (`688fe2d` →
`2efef1a`, `docs(JUP-053)`: propuestas OpenSpec, sin código): no hay ningún archivo tocado en ambos
lados y `git merge-tree --write-tree` simula la fusión **sin conflictos**. **Sin colisión de numeración
de ADR:** `develop` llega hasta `ADR-0009`, así que `ADR-0010` está libre (no se puede excluir que otro PR
abierto lo reclame).

**10.2 — Batería completa** (cada comando en solitario, sobre `6060993`):

| Comando | Resultado |
| --- | --- |
| `corepack pnpm install --frozen-lockfile` | `Done in 1.4s`, exit 0; el árbol queda limpio (lockfile sin cambios) |
| `corepack pnpm openspec:validate` | 35 passed, 0 failed |
| `corepack pnpm jup:check -- --change jup-099-unify-styles-assets` | `[OK]` enlazado con Trello y completo |
| `corepack pnpm jup:cleanup:check` | `[OK]` 683 archivos (684 tras añadir la evidencia) sin agentes personales, binarios ni tareas paralelas |
| `corepack pnpm jup:check:test`, `jup:cleanup:test` | exit 0 ambos |
| `… --filter @finops/frontend lint` | exit 0 |
| `… --filter @finops/frontend typecheck` (3 configs) | exit 0 |
| `… --filter @finops/frontend test` | **47 archivos / 431 tests pasan**, 0 timeouts (50,8 s) |
| `… --filter @finops/frontend build` | correcto, 2 479 módulos; CSS 41,83 kB (gzip 7,99), JS 768,89 kB (gzip 217,26) |

`corepack pnpm lint/test/typecheck` desde la **raíz** siguen sin funcionar en esta máquina por
`RF-093-001` (turbo resuelve un pnpm global); se usa el sustituto `--filter`, igual que en las tarjetas
anteriores. No se ha vuelto a reproducir aquí; consta como limitación conocida.

**10.3 — `docs/evidence/JUP-099-validation.md` creado** (738 líneas): cabecera con Trello, rama, base y
estado verificado; fuentes verificadas; trazabilidad con los 4 requisitos nuevos; **los 8 criterios uno a
uno** con el comando y su resultado (los criterios 1 y 3 ejecutados de nuevo el mismo día: el 1 devuelve
solo las 3 líneas del documento de impresión de `ExportButton` y el `bg-black/50` de `dialog`, ambos
excepciones declaradas; el 3 devuelve 0); decisiones; ciclo Red/Green con los conteos de cada grupo
(41/374 → 44/387 → 28/403 → 24/407 → 0/431); suite, type-check, lint, build e instalación; exención de
mutación justificada; verificación visual completa (método, 34 escenarios, criterio de ruido frente a
diferencia sistemática, tabla de píxeles por escenario, las cuatro causas aceptadas y la demostración de
propagación); tokens; arrastre de JUP-098; hallazgos `RF-098-004` y `RF-099-001…004`; incidencias del
proceso; cómo reproducir; pendientes con los enlaces que hay que corregir al archivar; y el **apéndice con
los 5 scripts**. Comprobado que los 5 scripts del apéndice son **idénticos byte a byte** a los ejecutados
(se leen de sus archivos al ensamblar, no se reescriben).

Limitaciones honestas de la evidencia: la comparación visual usa datos simulados de `tests/fixtures.ts`
y datos de demostración estáticos, no el backend real (E2E = JUP-102); un cambio de 1 nivel sobre un color
plano de área pequeña quedaría clasificado como ruido (mitigado porque los valores de los tokens son el
texto exacto que sustituyen y un token equivocado cambia áreas enteras); y el `RF-098-004` observado durante
el grupo 5 no se pudo diagnosticar.

**Falso positivo de mi comprobador de enlaces:** marca `route` en la línea 359 de la evidencia; es texto
de código dentro del bloque de `capture.mjs` (la llamada al manejador que se busca en el objeto de
sustituciones por escenario, donde un corchete de cierre va seguido de un paréntesis), no un enlace. Un
comprobador que no ignore los bloques de código lo marcará; no se altera el script porque el apéndice
reproduce exactamente lo ejecutado.

**Checkpoint:** todas las tareas de `tasks.md` marcadas (36/36). Siguiente: gate post-review, archivado
(corrigiendo los enlaces que bajan un nivel en el mismo paso), `jup:cleanup:check`, `pr:check` y PR.

## Human Approval

- Change: jup-099-unify-styles-assets
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-09-29
- Archive decision: archive
- Scope reviewed: las 36 tareas de `tasks.md` (10 grupos), cada una con su resumen y su commit; este
  `review.md`; las cuatro imágenes antes/después de las diferencias visuales; la evidencia
  `docs/evidence/JUP-099-validation.md` y la batería final (`openspec:validate`, `jup:check`,
  `jup:cleanup:check`, `test`/`typecheck`/`lint`/`build` vía `--filter @finops/frontend` e
  `install --frozen-lockfile`).
- Resultado verificado: los 8 criterios de aceptación de la tarjeta verificados uno a uno en la
  evidencia. Una única paleta en `theme.css` con 42 tokens de color, sin colores literales en pantallas
  (solo las 3 líneas del documento de impresión de `ExportButton` y el `bg-black/50` del primitivo
  `Dialog`, excepciones declaradas), protegida por dos tests estáticos; suite **431/431** (los 260 previos
  intactos); 34 escenarios visuales sin píxeles reales de diferencia frente al estado con el tema nuevo;
  propagación de tokens demostrada cambiando solo `theme.css`; ningún archivo de `apps/backend` ni de
  `apps/processor` en el diff; `develop` avanzado un commit de documentación sin conflicto.
- Aceptaciones explícitas dadas durante la revisión: las **cuatro diferencias visuales** frente al
  original (franja del `body`, iconos `#fafafa → #ffffff`, un borde por defecto y el redondeo de un
  degradado), tras revisar las imágenes; descartar la consulta sobre "los tests del frontend no corren
  en CI"; dejar `RF-098-003` fuera de esta tarjeta; y registrar como findings, sin corregir aquí, la
  deuda de referencias locales (`RF-099-001`), las clases interpoladas (`RF-099-002`), los tonos casi
  iguales (`RF-099-003`) y los enlaces rotos por archivados (`RF-099-004`).
- Decisiones y límites que se aprueban con el cierre: **sin mutación de Stryker** sobre la migración
  (exención justificada: literales de clase y valores CSS que ninguna prueba de comportamiento
  ejercita), **sin afirmar cobertura de mutación**; verificación visual con datos simulados, no con el
  backend real (el E2E es JUP-102); `ADR-0010` en `Proposed`, que pasa a `Accepted` con la aprobación del
  PR; `RF-098-004` y `RF-099-001` a `RF-099-004` quedan `Open` sin dueño asignado.
- Notes: (1) al archivar hay que corregir **en el mismo paso** los enlaces que bajan un nivel: el del
  change en `docs/spikes/frontend-migration.md` y en `docs/evidence/JUP-099-validation.md`, y los
  relativos del propio `review.md`, `design.md` y `proposal.md` archivados (lección de JUP-098,
  `RF-099-004`). (2) La ejecución de la suite que dio 14 archivos fallando durante el grupo 5 no se
  reprodujo y su causa no está demostrada; es coherente con `RF-098-004` pero no lo confirma. (3) El PR
  lo abre Victor directamente (no este agente).

## Fusión con `develop` tras abrir el PR #54 (2026-09-30)

Posterior al gate post-review de arriba; no lo sustituye. `develop` incorporó
JUP-026 (`openspec/changes/jup-026-azure-cost-kpis/`) (#52, Paris Arcos: KPIs de costes de Azure y
pantalla ejecutiva conectada a datos reales), que solapa con esta rama. GitHub marcó **3 conflictos**.

**Estado de partida.** La rama remota ya tenía una fusión previa de `develop` hecha por Victor
(`2684610`, que traía `2efef1a`); la copia local iba 2 commits por detrás. Se igualó con un
*fast-forward* puro (`git merge --ff-only`, sin commit nuevo) y después se fusionó `develop`
(`1e897dc`) con `git merge --no-commit --no-ff`, sin crear el commit, para resolver y verificar antes de
confirmar. Convención ya usada en JUP-098 (fusionar `develop` en la rama).

**Conflictos de texto (3 archivos, 6 bloques) y resolución:**

| Archivo | Bloques | Resolución |
| --- | --- | --- |
| `openspec/findings/backlog.md` | 1 | Se conservan **ambos lados**: nuestras 5 filas de tabla (`RF-098-004`, `RF-099-001…004`) primero, para que la tabla siga contigua, y después las secciones de prosa de JUP-026 (`RF-026-001`, `RF-026-002` y la actualización técnica). Comprobado: las 8 filas `RF-098`/`RF-099` de la tabla (las 3 previas y las 5 nuestras) tienen 12 campos, y las 2 secciones `RF-026` siguen íntegras |
| `apps/frontend/src/pages/DashboardPage.tsx` | 1 | Su lógica nueva (`role="alert"` y el aviso de solapamiento de fuentes) con nuestro token de color. Frente a `develop` el archivo queda con **solo el cambio de color** |
| `apps/frontend/src/pages/ExecutiveCostDashboard.tsx` | 4 | JUP-026 reescribió la pantalla (quitó el gráfico circular y las tarjetas KPI demo, añadió la sección de costes reales y una sección de demostración). Se toma **su estructura y lógica** en los 4 bloques y se **vuelve a aplicar la migración de color** sobre su código. Frente a `develop` el archivo queda con solo: los colores a tokens, el `import` del tooltip compartido y los atributos de las gráficas a `var(--…)` |

**Problemas que Git no marca como conflicto y que se resolvieron:**

1. **Colisión de ADR.** JUP-026 añadió `docs/adr/ADR-0010-azure-cost-source-overlap.md`, ya `Accepted`
   (aprobación final de Paris, 2026-09-28). Nuestro `ADR-0010-frontend-color-tokens.md` es un archivo
   distinto, así que Git los fusiona sin aviso y quedarían **dos ADR-0010**. Se **renumera el nuestro a
   `ADR-0011`** (archivo, título y todas las referencias vivas: `design.md`, `tasks.md`, parte del
   `proposal.md`, README del frontend, `ADR-0004`, spike y evidencia). El ADR de JUP-026 queda intacto
   (0 líneas de diferencia frente a `develop`). **Se dejan sin cambiar** los bloques de aprobación ya
   firmados (`proposal.md` y este `review.md`) y las frases históricas de los grupos 9 y 10 (p. ej. "ADR-0010
   está libre", cierta cuando se escribió): todas se refieren a este mismo ADR con su número original. En el
   gate del grupo 10 ya se había advertido de que no se podía excluir esa colisión.
2. **Código huérfano nuestro.** El mapa `toneIconClass` de `ExecutiveCostDashboard` (clases que sustituían
   una interpolación) dejó de tener uso porque JUP-026 eliminó las tarjetas KPI que lo consumían: se
   retira, y se añade el `import` de `chartTooltipStyle`, que sus gráficas siguen usando.
3. **Colores literales nuevos en su código**, sin conflicto textual: la sección de costes reales
   introduce `text-slate-300` (8), `text-white` (6), `text-slate-400` (4), `border-[#2d3748]` (4),
   `bg-[#0f1419]` (1) y **`text-amber-300` (3), un tono que no existía en nuestra paleta**. Se migran con
   la tabla de siempre. Para `amber-300` (`oklch(87.9% 0.169 91.605)`, verificado en Tailwind 4.3.3) se
   añade **un token nuevo con nombre de función, `warning-text`** (texto de aviso suelto, distinto de
   `warning-foreground`, que es texto sobre fondo translúcido), en vez de reutilizar `warning`
   (amber-400) y cambiar píxeles. **Es una decisión de diseño visible: consolidarlo con `warning` es un
   cambio de una línea** y queda anotado en `RF-099-003` (par `warning-text`/`warning`) y en la tabla
   del `design.md`.

**Verificación sobre el árbol fusionado** (cada comando en solitario):

| Comprobación | Resultado |
| --- | --- |
| `color-tokens.guard.test.ts` + `theme-palette.test.ts` | 173/173; ningún color literal nuevo de JUP-026 se escapa; el caso de consumo de `warning-text` pasa |
| `typecheck` (3 configs) / `lint` | exit 0 / exit 0 |
| `test` | **47 archivos, 437/437**, 0 timeouts (la rama tenía 431; el resto viene de JUP-026 y de los casos de nuestros tests por archivo y por token) |
| `build` | correcto, 2 480 módulos; CSS 43,37 kB (gzip 8,25), JS 746,77 kB (gzip 214,05) |
| `install --frozen-lockfile` | `Done in 1.3s`, exit 0 |
| `openspec:validate` | 36 passed, 0 failed (entran el change y las specs de JUP-026) |
| `jup:check` de `jup-099-unify-styles-assets` y de `jup-026-azure-cost-kpis` | `[OK]` ambos |
| `jup:cleanup:check` | `[OK]` 707 archivos |
| Archivos de `apps/backend` o `apps/processor` en `git diff origin/develop` | **0** (el PR sigue sin tocar backend: lo de JUP-026 ya está en `develop`) |

**Verificación visual sobre el resultado de la fusión: `develop` frente al estado fusionado.** El "antes"
correcto ya no es el original de la rama sino `develop` tal cual (construido desde `git archive
origin/develop` en una carpeta temporal fuera del repositorio). El guion se adaptó al **contrato v2 de
`/billing/summary`** (totales y desglose reales) y gana 4 escenarios de la pantalla ejecutiva (datos
parciales, sin datos, solapamiento de fuentes y solapamiento en `/overview-legacy`); los tooltips de la
pantalla ejecutiva pasan de 3 a 2 porque JUP-026 retiró el gráfico circular. **37 escenarios** por lado.

- **La pantalla ejecutiva completa, con la sección de costes reales de JUP-026 ya migrada a tokens, da 0
  píxeles de diferencia frente a `develop` en sus 8 escenarios** (base, menú de exportación, foco del
  selector, datos parciales, sin datos, solapamiento y 2 tooltips), incluidos los tres mensajes con el
  token `warning-text`.
- El resto de diferencias son **las mismas cuatro causas ya aceptadas** y nada más, medido con
  `classify.mjs`: franja del `body` 8 184 960 px, degradado de Recomendaciones 2 820 px (los mismos
  2 × 1 410) y 3 322 px en "otros", que son **3 311 de iconos y borde** (las mismas cifras por pantalla:
  71, 549 y 761, contando los escenarios con tooltip) **más 11 px de ruido de rasterizado** (4 en
  `assistant` y 7 en `ingest-success`, los dos escenarios habituales). **La integración de JUP-026 no
  añade ninguna diferencia visual nueva.**

**Tropiezos del proceso durante la fusión** (resueltos): PowerShell corrompe la salida binaria de
`git archive` al pasarla por tubería (se repitió desde Bash); al limpiar la carpeta temporal de `develop`
se retiró **primero el enlace simbólico a `node_modules`** con `rmdir` (borrar con `-Recurse` un directorio
que contiene un *junction* puede vaciar su destino; se comprobó que `node_modules` seguía con las mismas
26 entradas); y el guion de capturas se cortó en el escenario 27 porque pedía una tercera gráfica que ya
no existe (se ajustó con un comentario, no se ocultó).

**Pendiente de Victor:** confirmar la fusión (`git add` de los archivos resueltos y `git commit`, que crea
el commit de fusión), `git push`, y actualizar la descripción del PR (ADR-0011, 437 tests y la nota de la
fusión). Decidir si `warning-text` se queda como token propio o se consolida con `warning`.

## Observaciones de la revisión del PR #54 (Paris, 2026-09-30)

Posteriores a la fusión con `develop`; tres observaciones, las tres atendidas.

**1. (P3) Receta de reproducción de la evidencia.** `docs/evidence/JUP-099-validation.md` conservaba
`688fe2d` como estado original en un único procedimiento, pero el guion vigente incluía escenarios
exclusivos de JUP-026 y un mock del contrato v2 de `/billing/summary` que no funciona contra esa base.
**Confirmado por inspección** (el revisor no ejecutó la receta): el paso 2 decía `688fe2d` y el guion
vigente añade 4 escenarios y cambia el mock. Corrección:

- La sección "Reproducir la verificación visual" se divide en **dos recetas**. **A (original, 34
  escenarios):** `688fe2d` → `81a5e69` (último commit con código de frontend antes de la fusión; se
  comprobó que entre `81a5e69` y `6060993` no cambia ningún archivo de `src`, `tests` ni `index.html`),
  con el guion original. **B (posterior a la fusión, 37 escenarios):** `1e897dc` (`develop` con
  JUP-026) → estado fusionado (`c449196`), con el guion vigente.
- El apéndice incluye ahora también **`capture.v1.mjs`**, el guion original, leído de su archivo (idéntico
  byte a byte al ejecutado); `capture.mjs` queda como el vigente. Se comprobó que el original es el
  guion de 34 escenarios con el contrato antiguo.
- La reverificación fija `git archive 1e897dc` como base de la comparación posterior a la fusión (antes
  decía `origin/develop`, que se mueve).
- Nota: el comprobador de enlaces marca ahora 2 falsos positivos en la evidencia (una llamada de
  JavaScript en cada uno de los dos scripts); no se altera el texto porque el apéndice reproduce lo
  ejecutado.

**2. Coordinación documental: dos `ADR-0011`.** El PR #51 (lmatsan, JUP-096, `64fdfab`, aún sin integrar)
añade `ADR-0011-single-owner-per-table.md`, `Accepted` y fechado el 2026-09-30, referenciado desde su
`architecture.md`, su evidencia y su change ya archivado. No había duplicado dentro de esta rama, pero sí
entre ramas. Se comprobaron las cabezas de los PR #49 a #56: **solo #51 y este PR usan números ≥ 0011**,
así que `ADR-0012` está libre. Decisión: **renumerar el nuestro a `ADR-0012`** (está `Proposed` y tiene
pocas referencias; el de #51 está `Accepted` y ya referenciado en documentos archivados, más caro de
mover). Renombrado el archivo y su título y actualizadas todas las referencias vivas (`design.md`,
`tasks.md`, parte del `proposal.md`, README del frontend, `ADR-0004`, spike y evidencia). **Se dejan sin
cambiar** los bloques de aprobación firmados y las frases históricas de este `review.md` (que citan
`ADR-0010` y `ADR-0011`: son los números que tuvo antes). La historia del número es 0010 → 0011 → 0012.
**Pendiente de coordinar con el responsable del PR #51** que mantiene `0011`; si finalmente su ADR se
renumerase, ya no habría ningún conflicto con este. La consecuencia de la elección es un hueco
temporal en la numeración (`0011`) si este PR se integra antes que #51.

**3. Descripción del PR desactualizada.** Citaba `ADR-0010` y 431 pruebas y decía que `develop` solo
había avanzado un commit documental. Se prepara un cuerpo actualizado: **`ADR-0012`**, **437 pruebas**,
CSS 43,37 kB y JS 746,77 kB, la integración de JUP-026 (conflictos, el token `warning-text` y la
verificación visual `develop` frente al resultado) y la nota de la numeración del ADR. Lo aplica Victor en
GitHub (aquí no hay `gh` para editar el PR); debe conservar los nombres de los roles ya asignados.

## Validación independiente y archivado — 2026-10-01

- Revisión técnica favorable de Paris: [revisión incremental](https://github.com/EconomiconFinOps/tfm-economicon/pull/54#pullrequestreview-5372668227).
- Validación de Alejandro publicada como **APPROVED** sobre `ad128da`:
  [review de GitHub](https://github.com/EconomiconFinOps/tfm-economicon/pull/54#pullrequestreview-5384048039). Ejecución local sobre `f914d68`; el frontend es idéntico
  al de `ad128da` (árbol `21e522760011968b553da9a6b9ffc20a39de1369`). No se afirma una nueva ejecución.
- Evidencia: [validación independiente](../../../../docs/evidence/JUP-099-validation.md#validación-independiente-y-archivado-2026-10-01).
  437/437 tests en serial, 37/37 escenarios visuales y propagación 37/37. Incluye los siete fallos
  de la primera ejecución paralela, la captura interrumpida y la repetición completa; en Chromium
  149 se observan redondeos adicionales de un nivel de canal en navegación y conversación.
  En la pantalla ejecutiva el contenido coincide, pero no la captura completa (5.610 píxeles de
  navegación por escenario). No se atribuye a Victor aceptación nueva de esas ubicaciones.
- Autorización posterior del usuario en la sesión de validación: «Vale completa, aprueba y archiva».
  Se conserva arriba el gate post-review original de Victor de 2026-09-29 sin reescribir su firma.
- Archivado mediante `corepack pnpm openspec:archive jup-099-unify-styles-assets --yes` a
  `openspec/changes/archive/2026-10-01-jup-099-unify-styles-assets/`. Cuatro requisitos y siete escenarios promovidos;
  ADR-0012 aceptado y enlaces corregidos en el mismo cambio. Sin modificaciones funcionales.
- La integración sigue pendiente: `develop` tiene `dismiss_stale_reviews_on_push=true` y
  `require_last_push_approval=true`. El commit de archivado necesita aprobación posterior de otra
  persona y CI vigente. No se marca Trello como terminado ni se afirma un merge.

### Comprobaciones posteriores al archivado

Ejecutadas el 2026-10-01 sobre el cambio documental, antes de publicarlo:

| Comprobación | Resultado |
| --- | --- |
| `corepack pnpm openspec:validate` | 35/35, estricto, sin fallos |
| `corepack pnpm jup:check:all` | Ocho cambios activos completos; JUP-099 ya archivado |
| `corepack pnpm jup:cleanup:check` | 700 archivos, correcto |
| `git diff --cached --check` | Correcto |
| Revisión independiente del diff | Favorable; 80 enlaces relativos de los documentos afectados resuelven |
| Conservación de la spec | Ocho requisitos y 16 escenarios anteriores intactos, más el delta exacto de cuatro y siete: total 12/23 |
| Alcance de archivos | Solo documentación y especificaciones; fuentes, tests, configuración, dependencias y CI sin cambios |

La suite funcional y las capturas no se repiten para este diff documental. La CI del commit publicado
se consulta en la PR y no se anticipa como resultado de estas comprobaciones locales.
