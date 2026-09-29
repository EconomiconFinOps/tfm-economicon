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
