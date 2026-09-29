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
