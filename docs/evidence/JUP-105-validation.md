# Evidencia JUP-105 — Cerrar la épica de migración del frontend

> **Reconciliación 10/10/2026:** el [aporte residual](JUP-105-residual.md) corrige
> el comentario de DashboardPage y dos registros archivados de JUP-097 que aún
> faltaban en el criterio 5. Incorpora la respuesta Codex de Alejandro y la CI
> final de `ca9e67f`. Las salidas de las baterías y el gate del 09/10 se conservan
> como historia; no son pruebas nuevas ni aprobación del aporte residual.

- Fecha: 2026-10-08 (verificación del alcance al proponer) y 2026-10-09 (línea base y consulta al
  equipo).
- Trello: https://trello.com/c/YZvtBdGV/100-jup-105
- Rama: `chore/JUP-105-close-frontend-migration`.
- Base: `develop` en `ff2ea6b`.
- OpenSpec: [jup-105-close-frontend-migration](../../openspec/changes/archive/2026-10-09-jup-105-close-frontend-migration/).
- Pull request: [#86](https://github.com/EconomiconFinOps/tfm-economicon/pull/86), contra `develop`.
- CI sobre `502dd44`: ejecución del `push`
  [38013186253](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38013186253) en
  verde, y la del pull request
  [38013497033](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38013497033); el
  detalle y el estado final están en la sección «Pull request y CI» y en la pestaña de checks del
  propio pull request.

> Estado de este documento: completo salvo lo que solo puede registrarse tras las reviews. Contiene
> la línea base y la consulta al equipo (grupo 1 de `tasks.md`), el endurecimiento de `allowJs`
> (grupo 2), el recuento de pantallas con los textos vivos corregidos (grupo 3), la corrección de los
> enlaces relativos rotos (grupo 4), la retirada de las menciones a configuración local (grupo 5),
> los hallazgos de la épica (grupo 6), el cierre del spike (grupo 7), la batería completa con la
> trazabilidad de los criterios y el archivado (grupo 8) y el pull request con su CI (tarea 8.6).
> Las reviews `Revision JUP-105` y `Validacion JUP-105` viven en el pull request.

## Línea base: antes de cambiar nada

Medida el 2026-10-09 en Windows 11 con Node `v24.15.0`, sobre la rama en `d90df60` (dos commits de
planificación por encima de `ff2ea6b`, sin cambios fuera de la carpeta del change). Todos los
comandos se ejecutan desde la raíz del repositorio.

| Medida | Comando | Resultado |
| --- | --- | --- |
| Valor de `allowJs` | `git grep -n "allowJs" -- apps/frontend/tsconfig.json` | línea 24: `"allowJs": true` |
| Archivos JavaScript en el código fuente y las pruebas | `git ls-files "apps/frontend/src/*.js" "apps/frontend/src/*.jsx" "apps/frontend/src/*.mjs" "apps/frontend/src/*.cjs" "apps/frontend/tests/*.js" "apps/frontend/tests/*.jsx" "apps/frontend/tests/*.mjs" "apps/frontend/tests/*.cjs"` | salida vacía: 0 archivos |
| Enlaces relativos rotos | recorrido de enlaces (ver abajo) | 66 en 26 archivos |
| Menciones a configuración local | búsqueda de menciones (ver abajo) | 42 líneas en 11 archivos |
| Hallazgos de la épica en `Open` | búsqueda de hallazgos (ver abajo) | 21 de 21 |

### Recorrido de enlaces

El recorrido lee cada `.md` versionado, toma los destinos de los enlaces que no son una URL, un
correo ni un ancla, y comprueba que el destino existe en disco. No distingue un enlace real de un
texto con la misma forma dentro de un ejemplo de código: por eso hay dos falsos positivos conocidos.

Para repetirlo, guardar este texto como `links.mjs` en una carpeta fuera del repositorio y ejecutar
`node <carpeta>/links.mjs .` desde la raíz. Con `--detail` lista también los enlaces rotos de fuera
de `openspec/changes/archive/`.

```js
// Recorre los .md versionados y lista los enlaces relativos cuyo destino no existe.
// Uso: node links.mjs <raiz-del-repo> [--detail]
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const root = process.argv[2];
const files = execFileSync("git", ["-C", root, "ls-files", "*.md"], { encoding: "utf8" })
  .split("\n")
  .filter(Boolean);

const broken = [];
let total = 0;
for (const file of files) {
  const lines = readFileSync(resolve(root, file), "utf8").split("\n");
  lines.forEach((line, i) => {
    for (const m of line.matchAll(/\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g)) {
      const target = m[1];
      if (/^(https?:|mailto:|#|<)/.test(target)) continue;
      total += 1;
      const path = decodeURIComponent(target.split("#")[0]);
      if (!path) continue;
      if (!existsSync(resolve(root, dirname(file), path))) {
        broken.push({ file, line: i + 1, target });
      }
    }
  });
}

const byFile = new Map();
for (const b of broken) byFile.set(b.file, (byFile.get(b.file) ?? 0) + 1);
const inArchive = broken.filter((b) => b.file.startsWith("openspec/changes/archive/")).length;
console.log(`relativos=${total} rotos=${broken.length} archivos=${byFile.size} en_archive=${inArchive} fuera=${broken.length - inArchive}`);
for (const [f, n] of [...byFile].sort()) console.log(`${String(n).padStart(3)}  ${f}`);
if (process.argv.includes("--detail")) {
  for (const b of broken.filter((x) => !x.file.startsWith("openspec/changes/archive/"))) {
    console.log(`${b.file}:${b.line} -> ${b.target}`);
  }
}
```

Solo recorre archivos versionados (`git ls-files`): un `.md` nuevo no cuenta hasta que está añadido
al índice.

Resultado de la línea base: `rotos=66 archivos=26 en_archive=53 fuera=13`.

| Enlaces rotos | Archivo |
| ---: | --- |
| 1 | `docs/evidence/JUP-013-validation.md` |
| 8 | `docs/evidence/JUP-085-validation.md` |
| 2 | `docs/evidence/JUP-097-validation.md` |
| 2 | `docs/evidence/JUP-099-validation.md` (falsos positivos, líneas 505 y 793) |
| 2 | `2026-08-31-jup-091-inventory-economicon-frontend` (`design.md` 1, `proposal.md` 1) |
| 1 | `2026-09-01-jup-043-technical-metrics` (`design.md`) |
| 7 | `2026-09-02-jup-092-frontend-typescript-adr` (`design.md` 4, `proposal.md` 3) |
| 14 | `2026-09-07-jup-094-reconcile-package-json` (`design.md` 7, `proposal.md` 4, `review.md` 2, `tasks.md` 1) |
| 11 | `2026-09-12-jup-095-portar-codigo-fuente` (`design.md` 3, `proposal.md` 4, `review.md` 2, `tasks.md` 2) |
| 1 | `2026-09-18-jup-013-normalize-azure-costs` (`review.md`) |
| 1 | `2026-09-19-jup-095-reconciliar-develop` (`proposal.md`) |
| 5 | `2026-09-21-jup-097-reconcile-api-layer` (`proposal.md` 1, `review.md` 4) |
| 11 | `2026-09-24-jup-085-auth-session-contract` (`design.md` 3, `proposal.md` 2, `review.md` 3, `tasks.md` 2, spec delta 1) |

Las carpetas con fecha están en `openspec/changes/archive/`. Los dos falsos positivos son un ejemplo
de código de la evidencia de JUP-099 con un corchete y un paréntesis seguidos; no son enlaces y no se
tocan.

### Búsqueda de menciones

Usa los seis términos y las exclusiones que define la fila `RF-099-001` de
`openspec/findings/backlog.md`. Se excluyen además el backlog y este documento, porque describen el
propio hallazgo y tienen que nombrar los términos. `git grep -c` imprime las líneas por archivo.

```sh
git grep -c -F -e ".claude/" -e "check-dod" -e "stryker.conf" -e "lock-committed" \
  -e "harness/workflow" -e "mutation.md" -- . \
  ":(exclude).gitignore" ":(exclude).dockerignore" ":(exclude)tools/jup-cleanup-check*" \
  ":(exclude)*.test.ts" ":(exclude)*.test.tsx" ":(exclude)*.test.mjs" \
  ":(exclude)openspec/changes/archive/*jup-098-*" ":(exclude)openspec/changes/archive/*jup-099-*" \
  ":(exclude)docs/evidence/JUP-098-*" ":(exclude)docs/evidence/JUP-099-*" \
  ":(exclude)openspec/findings/backlog.md" ":(exclude)docs/evidence/JUP-105-validation.md"
```

En PowerShell, el mismo comando en una sola línea, sin las barras de continuación.

| Líneas | Archivo |
| ---: | --- |
| 1 | `apps/frontend/vite.config.ts` |
| 1 | `docs/evidence/JUP-093-validation.md` |
| 1 | `docs/evidence/JUP-095-validation.md` |
| 3 | `docs/evidence/JUP-097-validation.md` |
| 1 | `openspec/changes/archive/2026-09-02-jup-092-frontend-typescript-adr/review.md` |
| 6 | `openspec/changes/archive/2026-09-06-jup-093-configure-typescript/review.md` |
| 3 | `openspec/changes/archive/2026-09-06-jup-093-configure-typescript/tasks.md` |
| 1 | `openspec/changes/archive/2026-09-07-jup-094-reconcile-package-json/review.md` |
| 17 | `openspec/changes/archive/2026-09-12-jup-095-portar-codigo-fuente/review.md` |
| 1 | `openspec/changes/archive/2026-09-12-jup-095-portar-codigo-fuente/tasks.md` |
| 7 | `openspec/changes/archive/2026-09-21-jup-097-reconcile-api-layer/review.md` |

Total: 42 líneas en 11 archivos. Menciones legítimas que quedan fuera de la búsqueda y no se tocan:
8 líneas en el `review.md` archivado de JUP-099 y 1 en el backlog.

**Corrección de una cifra de la propuesta.** El `design.md` y el `proposal.md` de esta tarjeta decían
41 líneas, «no 42» como la tarjeta de Trello. El error era de la medida hecha al proponer: su filtro
descartaba por el contenido de la línea y no por la ruta del archivo, y eliminó una línea del
`review.md` de JUP-095 que nombra a JUP-099. La tarjeta tenía razón: son 42. Los dos documentos y
`tasks.md` quedan corregidos en este mismo grupo.

### Búsqueda de hallazgos

```sh
git grep -c -E "^\| RF-(091-00[34]|095-002|093-001|098-00[1-4]|099-00[1-4]|103-00[1-5]|104-00[1-4]) " -- openspec/findings/backlog.md
```

Resultado: 21 filas. Las 21 tienen `Open` en la columna de estado (la de `RF-093-001`, con una
aclaración entre paréntesis) y `Equipo Economicon` en la de responsable.

## Consulta al equipo sobre `RF-093-001`

`RF-093-001` quedó en `Open` al cerrar JUP-103 a falta de confirmar en dos máquinas: la consola
externa de Alejandro y la de Paris. Victor les envió la consulta tras el gate pre-código del
2026-10-08, con estos dos comandos desde la raíz de `develop` y en una consola externa:

```sh
corepack pnpm exec pnpm --version
corepack pnpm lint --force
```

Respuestas recogidas el 2026-10-09:

| Persona | Respuesta | Resultado |
| --- | --- | --- |
| Paris | Sí | El fallo no se reproduce en su máquina |
| Alejandro | Sí, diagnóstico en Codex del 09/10; consola externa pendiente | pnpm 11.19.0 y lint 0/4 con `NO_TTY`; no acredita corrección |

**Datos que pasó Paris**, tal como los escribió:

| Dato | Valor |
| --- | --- |
| Sistema operativo y consola | Windows, PowerShell, fuera de Codex |
| `corepack pnpm exec pnpm --version` | `9.0.0` |
| `corepack pnpm lint --force` | `Tasks: 4 successful, 4 total (0 cached)` |
| `where.exe pnpm` | `C:\Users\Trabajo\AppData\Roaming\npm\pnpm.cmd` (único resultado) |
| ¿Necesitó `corepack enable`? | No |
| Otro paso | Instaló las dependencias con `corepack pnpm install --frozen-lockfile`, porque al principio no encontraba turbo |

**Qué acredita y qué no.**

- Acredita que en la máquina de Paris la batería de `lint` desde la raíz pasa con la invocación
  documentada, sin caché, y que el diagnóstico imprime la versión fijada.
- **No acredita la corrección** (`corepack enable`): Paris no la aplicó porque no le hizo falta.
- Deja un dato sin explicar. `where.exe pnpm` devuelve solo el pnpm instalado globalmente con npm, es
  decir, los lanzadores de corepack no están activados, que es la misma situación del `PATH` que en
  las máquinas donde el fallo sí se reproducía. Aun así el diagnóstico imprime `9.0.0`. No se pidió
  la versión de ese pnpm global (`pnpm --version` fuera del repositorio), así que no se sabe si es la
  `9.0.0` o una versión que sí cambia a la fijada. Confirma lo que ya anotó la revisión de JUP-103:
  el síntoma depende de la versión del pnpm que se resuelva, no solo de que haya uno por delante.
- El paso de instalar dependencias no tiene que ver con el hallazgo: sin `node_modules` no hay turbo
  que ejecutar.

**Reconciliación del 10/10.** Alejandro ya entregó el diagnóstico de Codex sobre
`ff2ea6be12abf1bea4789791c34efb46c3b55aa8`: instalación congelada exit 0, pnpm
11.19.0 desde el fallback del runtime y lint exit 1, 0/4 tareas, 0 caché,
`ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`, sin alterar PATH ni Corepack global.
Recibos Trello `6ac84c3f99a6c78a1e5b2a38` y `6ac94909af1d4e6ea614bfb1`,
contrastados mediante la integración oficial. Esto sustituye «Alejandro no
confirmado» para el carril Codex, pero **la consola normal sigue pendiente**.
`RF-093-001` permanece `Open`: falta esa prueba y demostrar una corrección
permanente del runtime. Véase el [detalle y los límites](JUP-105-residual.md).

## Endurecimiento de `allowJs`

Ejecutado el 2026-10-09 sobre la rama en `259f6f9`, con el único cambio de
`apps/frontend/tsconfig.json`: la línea 24 pasa de `"allowJs": true` a `"allowJs": false`.
`checkJs: false` se deja como estaba. `git diff` del archivo: 1 inserción y 1 eliminación.

### Comprobaciones del paquete

Los cuatro comandos se ejecutan desde la raíz con el filtro del paquete, que es el mismo script que
lanza turbo; la batería completa desde la raíz va en su propia sección, más adelante.

| Comprobación | Comando | Resultado |
| --- | --- | --- |
| Type-check (app, Vite y pruebas) | `corepack pnpm --filter @finops/frontend typecheck` | código de salida 0 |
| Lint | `corepack pnpm --filter @finops/frontend lint` | código de salida 0, sin violaciones |
| Build | `corepack pnpm --filter @finops/frontend build` | código de salida 0; 2483 módulos; Vite avisa de que un fragmento supera 500 kB, aviso que no es un error |
| Pruebas | `corepack pnpm --filter @finops/frontend test -- --maxWorkers=1` | 53 archivos y 629 pruebas correctas; 178 s |

Las pruebas se ejecutan con un solo worker porque con los de por defecto fallan por plazos de tiempo
en esta máquina (`RF-098-004`).

### Control positivo

Sin un control, «sigue en verde» no distingue una opción que hace algo de una que no hace nada. Se
crearon dos archivos temporales en `apps/frontend/src/jup105-control/`: `legacy.js`
(`export const legacy = 1;`) y `consumer.ts` (que lo importa con `./legacy.js`), y se ejecutó
`corepack pnpm --filter @finops/frontend exec tsc --noEmit`:

| `allowJs` | Resultado |
| --- | --- |
| `false` | `src/jup105-control/consumer.ts(1,24): error TS7016: Could not find a declaration file for module './legacy.js'`; código de salida 1 |
| `true` (`--allowJs true` en la misma ejecución) | sin salida; código de salida 0 |

Con la opción en `false` el compilador rechaza el import y con `true` lo acepta en silencio, así que
el endurecimiento tiene efecto real. Tras la prueba se borró la carpeta temporal y `git status` solo
muestra los archivos de la tarjeta. Con el error, pnpm imprime además un mensaje propio
(`Command "tsc" not found`) que no procede del compilador: el error del compilador es la línea
`TS7016`.

**Límite.** El compilador rechaza un JavaScript *importado* desde TypeScript. Un `.js` suelto en
`src/` que nadie importe no participa en la aplicación y no hace fallar nada. El bloque de
`eslint.config.js` para los `.js` y `.jsx` de `src/` se conserva a propósito (ADR-0003): es el que
mantendría la validación de props sobre un JSX que alguien añadiera. No se añadió ningún test
guardián (decisión 1 del `design.md`).

### Seguimiento de ADR-0003

La sección de seguimiento de [ADR-0003](../adr/ADR-0003-frontend-typescript.md) recoge la ejecución
de su decisión 2 con fecha y enlace a este documento. El texto de la decisión no se editó.

## Recuento de pantallas (grupo 3, tarea 3.1)

Verificado el 2026-10-09 sobre `develop` en `ff2ea6b`, ruta por ruta contra
`apps/frontend/src/routes.tsx`. Método: para cada pantalla se leyeron sus imports y las llamadas de
sus hooks a `services/api.ts`, se buscó texto visible de demostración en la pantalla y en
`src/components/`, y se contrastó con los puntos de entrada de `api.ts`. La primera búsqueda de
rótulos no devolvió nada ni siquiera para `/anomalies`, que sí lo tiene, así que se descartó y se
repitió con otras rutas de búsqueda.

| Ruta | Pantalla | Origen de los datos | Evidencia | Rótulo de demostración |
| --- | --- | --- | --- | --- |
| `/login` | `LoginPage` | Backend | `login()` → `POST /auth/login` | No aplica |
| `/` | `ExecutiveCostDashboard` | Backend | `useExecutiveCostKpis` → `fetchBillingSummary`; sin imports de `src/data/demo/` | No aplica |
| `/operational` | `OperationalCostDashboard` | Demostración | importa `@/data/demo/operationalCostDashboard`; sin llamadas a la API | No |
| `/cuts` | `ExecutiveCutDashboard` | Demostración | importa `@/data/demo/executiveCutDashboard`; sin llamadas a la API | No |
| `/anomalies` | `AnomaliesPanel` | Demostración | importa `@/data/demo/anomaliesPanel`; sin llamadas a la API | Sí: aviso «Datos de demostración · periodo», leyenda de la tabla y rótulo en la exportación |
| `/recommendations` | `RecommendationsPanel` | Demostración | importa `@/data/demo/recommendationsPanel`; sin llamadas a la API | No |
| `/ingest` | `IngestPage` | Backend | `createIngestJob` → `POST /jobs/ingest` | No aplica |
| `/assistant` | `ConversationsPage` | Backend | `createConversation`, `listConversations`, `getConversation`, `sendConversationMessage` → `/assistant/conversations` | No aplica |
| `/overview-legacy` | `DashboardPage` | Backend | `useDashboardData` → `fetchBillingSummary` y `fetchHealth` (`GET /health`) | No aplica |
| `/system-health` | `SystemHealthDashboard` | Backend | `useSystemHealth` → `GET /health/status` y `POST /health/provider-check` | No aplica; rotula «Datos de ejemplo» por componente cuando su origen es `mock` |

**Resultado: 9 rutas bajo sesión más `/login`; 5 con datos del backend, 4 de demostración, 3 de ellas
sin rótulo** (`/operational`, `/cuts` y `/recommendations`). Coincide con lo que dio la lectura al
proponer. El recuento vive en la sección «Rutas» de `apps/frontend/README.md`, con fecha y commit.

Se repetirá tras traer `develop` (tarea 6.1) por si se fusionan #66 o #69.

## Textos vivos corregidos (grupo 3, tareas 3.2 a 3.6)

| Archivo | Qué decía | Qué dice ahora |
| --- | --- | --- |
| `apps/frontend/README.md`, «Rutas» | Tabla sin `/system-health`, sin distinguir demostración de backend ni rótulo; notas aparte | Tabla con las columnas de origen y de rótulo, fila de `/system-health`, recuento fechado y aviso de que es el único recuento |
| `apps/frontend/src/routes.tsx`, comentario de cabecera | `/overview-legacy` «sigue siendo el único dashboard con datos reales»; «las 8 pantallas portadas»; condición de retirada «todavía no existe» | Remite al README para el recuento; dice que la condición de retirada ya se cumple y que la ruta queda registrada como `RF-105-001`. Solo comentarios: 14 líneas añadidas y 13 eliminadas, sin cambio de código |
| `docs/planning/JUP-097-frontend-data-gap-map.md` | Filas de `/` «implementado localmente, pendiente de integración»; total, serie mensual y desglose como demostración o pendientes; ahorro asignado a `RF-091-004` | Filas de `/` marcadas como resueltas (JUP-026 #52, JUP-055 #77) o retiradas (inventario, C7); ahorro como capacidad ausente en `RF-091-003`; resumen por capacidad al día; enlace al recuento |
| `docs/evidence/JUP-095-validation.md` | `Frontend tests` como check obligatorio; solo `/overview-legacy` con datos reales; CORS pendiente | Nota fechada al inicio, sin reescribir las líneas históricas, que remite a `docs/governance/github-branch-protection.md`, al README y a `RF-095-001` (`Fixed`) |
| `docs/architecture.md`, recuadro de `GET /billing/summary` | «Todavía no lee los costes de Azure»; valores fijos; «ningún endpoint expone `azure_cost_records`» | Lee `azure_cost_records` y devuelve el contrato v2; el ahorro es siempre `null`; el frontend lo consume en `/` y en `/overview-legacy`. Comprobado en `apps/backend/app/db/database.py` (línea 211, lectura de `azure_cost_records`) y en `apps/backend/app/schemas/billing.py` (`savings_identified: None`) |

**Tarea 3.6.** `docs/architecture.md` tenía una afirmación falsa (el recuadro anterior) y se corrigió.
El `README.md` de la raíz no afirma nada desfasado sobre el frontend: sus menciones son de puertos,
de `VITE_API_BASE_URL` y de comandos, y los comandos coinciden con los del repositorio. No se tocó.
Queda sin tocar `docs/planning/JUP-091-economicon-source-inventory.md`, que tiene una fila de
`RF-091-004` con «hardcodeados» y estado `Open`: es el inventario del 31/08 y se deja como registro
de lo que se midió ese día.

### Hallazgos de este grupo para el grupo 6

- **`Layout.tsx` tiene comentarios desfasados** (líneas 53-61, 156-158 y 186-189): hablan de «las 5
  pantallas de demostración» y «las 3 conectadas al backend». Hoy el menú agrupa `/` (que sirve datos
  reales) con las de demostración y tiene 4 entradas del backend. No se corrigen aquí porque el gate
  pre-código limita los archivos de `apps/**` que se tocan; se anotan en el inventario de
  `RF-105-001`, cuya retirada de `/overview-legacy` obliga a tocar esa navegación.
- **`src/hooks/useCostKpis.ts` no lo importa ningún archivo.** Entra en `RF-105-002` junto con
  `src/data/demo/executiveCostDashboard.ts`.
- **`/overview-legacy` la nombran 9 archivos de pruebas** (8 pruebas y `tests/test-support.tsx`),
  cifra que el comentario de `routes.tsx` ya usa.
- **`RF-026-002` sigue `Open`** (Medium, desbordamiento en móvil del `Layout` compartido). No es de la
  épica, pero es una limitación conocida del frontend al cerrarla: el punto 13 del spike (tarea 7.4)
  debe mencionarla.
- **`RF-091-004` se puede cerrar con base comprobada**: el backend ya no devuelve importes fijos ni
  ahorro calculado. Eso adelanta la comprobación de la tarea 6.2.

### Verificación del grupo

| Comprobación | Resultado |
| --- | --- |
| `corepack pnpm --filter @finops/frontend typecheck` tras editar `routes.tsx` | código de salida 0 |
| `corepack pnpm --filter @finops/frontend lint` | código de salida 0 |
| Recorrido de enlaces relativos | 66 rotos en 26 archivos, igual que la línea base: no se introdujo ninguno; los enlaces nuevos (`README.md#rutas`, `backlog.md#rf-026-002`) apuntan a encabezados que existen |
| `corepack pnpm openspec:validate`, `jup:check` y `jup:cleanup:check` | los tres en verde |

**No se validó:** no se volvieron a ejecutar `build` ni `test` del frontend tras este grupo, porque
solo cambió un comentario de `routes.tsx` (sin efecto en el código compilado) y documentación; la
batería completa desde la raíz se ejecuta en el grupo 8. Las filas de `/` del mapa de carencias se
contrastaron con la lectura de `ExecutiveCostDashboard.tsx`, no con una ejecución de la pantalla en
un navegador.

## Deuda documental: enlaces relativos rotos, `RF-099-004` (grupo 4)

Ejecutado el 2026-10-09 sobre un árbol sin cambios pendientes (`git status` vacío, rama en `7c82266`).

### Guion de corrección

Un guion de un solo uso, que no se versiona como herramienta. Lee los `.md` versionados, y para cada
enlace relativo cuyo destino no existe prueba las dos causas que describe el hallazgo:

- **A.** El destino es la carpeta de un change que ahora vive en
  `openspec/changes/archive/<fecha>-<change>/`: se sustituye el nombre por el de la carpeta
  archivada.
- **B.** El enlace está dentro de un documento archivado, que bajó un nivel al archivarse y perdió un
  `../`: se le añade.

Un arreglo solo se aplica si el destino corregido existe. Lo que no tiene arreglo se informa y no se
toca. Modos: `--list` (propone sin escribir), `--dry` (igual) y `--apply`. Para repetirlo, guardar
como `fix-links.mjs` fuera del repositorio y ejecutar `node <carpeta>/fix-links.mjs . --list` desde
la raíz.

```js
// Corrige enlaces relativos rotos de los .md versionados sin cambiar ningun otro texto.
// Uso: node fix-links.mjs <raiz> [--list | --dry | --apply]
//
// Dos causas mecanicas (RF-099-004):
//  A) el destino es la carpeta de un change que ahora vive en openspec/changes/archive/<fecha>-<change>/
//  B) el enlace esta dentro de un documento archivado, que bajo un nivel al archivarse y perdio un "../"
// Un arreglo solo se aplica si el destino corregido existe. Lo que no tiene arreglo se informa y no se toca.
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve, relative, sep } from "node:path";

const root = resolve(process.argv[2]);
const mode = process.argv.includes("--apply") ? "apply" : process.argv.includes("--dry") ? "dry" : "list";
const changesDir = resolve(root, "openspec/changes");
const archiveDir = resolve(changesDir, "archive");

// nombre de change -> carpeta archivada (<fecha>-<nombre>); si hay varias, la mas reciente por fecha
const archived = new Map();
for (const d of readdirSync(archiveDir, { withFileTypes: true })) {
  if (!d.isDirectory()) continue;
  const m = d.name.match(/^\d{4}-\d{2}-\d{2}-(.+)$/);
  if (m) archived.set(m[1], [...(archived.get(m[1]) ?? []), d.name].sort());
}

const files = execFileSync("git", ["-C", root, "ls-files", "*.md"], { encoding: "utf8" }).split("\n").filter(Boolean);
const linkRe = /\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
const isExternal = (t) => /^(https?:|mailto:|#|<)/.test(t);
const exists = (file, target) => existsSync(resolve(root, dirname(file), decodeURIComponent(target)));

// Intenta variantes del destino: 0..2 niveles "../" de mas y, en cada una, la sustitucion por la carpeta archivada
function candidates(file, pathPart) {
  const out = [];
  for (let extra = 0; extra <= 2; extra += 1) {
    const base = "../".repeat(extra) + pathPart;
    out.push({ target: base, cause: extra ? `B(+${extra} ../)` : null });
    const mapped = mapToArchive(base);
    if (mapped) out.push({ target: mapped, cause: extra ? `A+B(+${extra} ../)` : "A" });
  }
  return out.filter((c) => c.cause);
}

// ".../changes/<name>/..." -> ".../changes/archive/<fecha>-<name>/..." (solo si <name> no es ya "archive")
function mapToArchive(target) {
  const m = target.match(/^(.*\/changes\/)([^/]+)(\/.*|)$/);
  if (!m || m[2] === "archive" || !archived.has(m[2])) return null;
  const dirs = archived.get(m[2]);
  return `${m[1]}archive/${dirs[dirs.length - 1]}${m[3]}`;
}

const plan = []; // {file, line, old, neu, cause} | {file, line, old, neu: null}
for (const file of files) {
  const lines = readFileSync(resolve(root, file), "utf8").split("\n");
  lines.forEach((line, i) => {
    for (const m of line.matchAll(linkRe)) {
      const target = m[1];
      if (isExternal(target)) continue;
      const [pathPart, ...frag] = target.split("#");
      if (!pathPart || exists(file, pathPart)) continue;
      const fragment = frag.length ? "#" + frag.join("#") : "";
      const fix = candidates(file, pathPart).find((c) => exists(file, c.target));
      plan.push({
        file, line: i + 1, old: target,
        neu: fix ? fix.target + fragment : null, cause: fix?.cause ?? null,
        index: m.index + 2
      });
    }
  });
}

const fixable = plan.filter((p) => p.neu);
const unfixable = plan.filter((p) => !p.neu);
console.log(`rotos=${plan.length} con_arreglo=${fixable.length} sin_arreglo=${unfixable.length}`);
const byCause = {};
for (const p of fixable) byCause[p.cause] = (byCause[p.cause] ?? 0) + 1;
console.log("por causa:", JSON.stringify(byCause));
if (mode === "list" || mode === "dry") {
  for (const p of plan) console.log(`${p.file}:${p.line}\n   ${p.old}\n   -> ${p.neu ?? "SIN ARREGLO"} ${p.cause ? "[" + p.cause + "]" : ""}`);
}

if (mode === "apply") {
  const byFile = new Map();
  for (const p of fixable) byFile.set(p.file, [...(byFile.get(p.file) ?? []), p]);
  for (const [file, items] of byFile) {
    const abs = resolve(root, file);
    const lines = readFileSync(abs, "utf8").split("\n");
    // de derecha a izquierda dentro de cada linea para no desplazar los indices
    for (const p of items.sort((a, b) => b.line - a.line || b.index - a.index)) {
      const line = lines[p.line - 1];
      if (line.slice(p.index, p.index + p.old.length) !== p.old) throw new Error(`desfase en ${file}:${p.line}`);
      lines[p.line - 1] = line.slice(0, p.index) + p.neu + line.slice(p.index + p.old.length);
    }
    writeFileSync(abs, lines.join("\n"), "utf8");
  }
  console.log(`archivos escritos=${byFile.size} enlaces corregidos=${fixable.length}`);
}
```

El guion conserva los finales de línea de cada archivo (corta por `\n` y deja el `\r` en su sitio) y
solo sustituye el texto del destino dentro de los paréntesis.

### Comprobación de que solo cambian destinos

Segundo guion, también de un solo uso: compara cada archivo modificado con su versión en `HEAD`, con
los finales de línea normalizados, y exige que (a) tengan el mismo número de líneas, (b) cada línea
distinta lo sea únicamente por el destino de uno o más enlaces y (c) ningún archivo con CRLF haya
quedado con finales mezclados.

```js
// Comprueba que la unica diferencia entre HEAD y el arbol de trabajo son destinos de enlaces.
// Uso: node verify-diff.mjs <raiz>
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(process.argv[2]);
const git = (...a) => execFileSync("git", ["-C", root, ...a], { encoding: "utf8", maxBuffer: 1 << 26 });
const changed = git("diff", "--name-only").split("\n").filter(Boolean);
const stripTargets = (l) => l.replace(/\]\([^)\s]+(?:\s+"[^"]*")?\)/g, "]<destino>");

let changedLines = 0, problems = 0, mixedEol = 0, crlfFiles = 0;
for (const file of changed) {
  const oldLines = git("show", `HEAD:${file}`).replace(/\r\n/g, "\n").split("\n");
  const rawNew = readFileSync(resolve(root, file), "utf8");
  const crlf = (rawNew.match(/\r\n/g) ?? []).length;
  const lf = (rawNew.match(/\n/g) ?? []).length;
  if (crlf > 0) { crlfFiles += 1; if (crlf !== lf) mixedEol += 1; }
  const newLines = rawNew.replace(/\r\n/g, "\n").split("\n");
  if (oldLines.length !== newLines.length) { console.log(`LINEAS DISTINTAS ${file}`); problems += 1; continue; }
  oldLines.forEach((o, i) => {
    if (o === newLines[i]) return;
    changedLines += 1;
    if (stripTargets(o) !== stripTargets(newLines[i])) { console.log(`TEXTO CAMBIADO ${file}:${i + 1}`); problems += 1; }
  });
}
console.log(`archivos=${changed.length} lineas_cambiadas=${changedLines} problemas=${problems} archivos_con_CRLF=${crlfFiles} con_EOL_mezclado=${mixedEol}`);
```

### Resultado

| Medida | Antes | Después |
| --- | ---: | ---: |
| Enlaces relativos rotos | 66 en 26 archivos | **2 en 1 archivo** |
| De ellos, dentro de `openspec/changes/archive/` | 53 | 0 |
| De ellos, fuera de `archive/` | 13 | 2 |

- El guion propuso `rotos=66 con_arreglo=64 sin_arreglo=2`: 11 por la causa A y 53 por la B. No hizo
  falta ninguna combinación de las dos.
- Aplicado: `archivos escritos=25 enlaces corregidos=64`. `git diff --stat`: 64 inserciones y 64
  eliminaciones en 25 archivos, una línea por enlace.
- Comprobación de solo destinos: `archivos=25 lineas_cambiadas=64 problemas=0 archivos_con_CRLF=8
  con_EOL_mezclado=0`. Ningún texto cambió salvo el destino de los enlaces.
- Los 2 restantes son los falsos positivos ya identificados: `docs/evidence/JUP-099-validation.md`,
  líneas 505 y 793, un ejemplo de código con un corchete y un paréntesis seguidos que no es un
  enlace. Se dejan como están.
- Anclas: los 64 enlaces cambiados incluyen 3 destinos con ancla distintos; los tres encabezados
  existen (`#autorizacion-de-publicacion-para-revision` en el `review.md` archivado de JUP-085,
  `#incremento-actual-tolerancia-jwt-de-5-s` y `#revalidacion-qa-tras-mitigacion-2309` en la
  evidencia de JUP-085). El guion de corrección solo comprueba que existe el archivo de destino; las
  anclas se comprobaron aparte, solo para estos enlaces.
- Los avisos `CRLF will be replaced by LF` que imprime Git vienen de 8 archivos que tienen CRLF solo
  en la copia de trabajo de Windows (`core.autocrlf=true`): el índice los guarda con LF, como fuerza
  `.gitattributes` (`* text=auto eol=lf`), y el commit los normaliza. El guion conservó los finales
  de línea que había en cada archivo y el diff del commit no contiene cambios de finales de línea.

### Enlaces corregidos por archivo

Causa A (carpeta archivada, 11 enlaces en 3 evidencias):

| Enlaces | Archivo |
| ---: | --- |
| 1 | `docs/evidence/JUP-013-validation.md` |
| 8 | `docs/evidence/JUP-085-validation.md` |
| 2 | `docs/evidence/JUP-097-validation.md` |

Causa B (falta un `../` dentro de un documento archivado, 53 enlaces en 22 archivos). Las carpetas
están en `openspec/changes/archive/`:

| Enlaces | Carpeta y archivo |
| ---: | --- |
| 1 | `2026-08-31-jup-091-inventory-economicon-frontend/design.md` |
| 1 | `2026-08-31-jup-091-inventory-economicon-frontend/proposal.md` |
| 1 | `2026-09-01-jup-043-technical-metrics/design.md` |
| 4 | `2026-09-02-jup-092-frontend-typescript-adr/design.md` |
| 3 | `2026-09-02-jup-092-frontend-typescript-adr/proposal.md` |
| 7 | `2026-09-07-jup-094-reconcile-package-json/design.md` |
| 4 | `2026-09-07-jup-094-reconcile-package-json/proposal.md` |
| 2 | `2026-09-07-jup-094-reconcile-package-json/review.md` |
| 1 | `2026-09-07-jup-094-reconcile-package-json/tasks.md` |
| 3 | `2026-09-12-jup-095-portar-codigo-fuente/design.md` |
| 4 | `2026-09-12-jup-095-portar-codigo-fuente/proposal.md` |
| 2 | `2026-09-12-jup-095-portar-codigo-fuente/review.md` |
| 2 | `2026-09-12-jup-095-portar-codigo-fuente/tasks.md` |
| 1 | `2026-09-18-jup-013-normalize-azure-costs/review.md` |
| 1 | `2026-09-19-jup-095-reconciliar-develop/proposal.md` |
| 1 | `2026-09-21-jup-097-reconcile-api-layer/proposal.md` |
| 4 | `2026-09-21-jup-097-reconcile-api-layer/review.md` |
| 3 | `2026-09-24-jup-085-auth-session-contract/design.md` |
| 2 | `2026-09-24-jup-085-auth-session-contract/proposal.md` |
| 3 | `2026-09-24-jup-085-auth-session-contract/review.md` |
| 1 | `2026-09-24-jup-085-auth-session-contract/specs/demo-auth-session/spec.md` |
| 2 | `2026-09-24-jup-085-auth-session-contract/tasks.md` |

**Qué no resuelve.** Que los enlaces vuelvan a romperse con cada archivado es un problema distinto de
la deuda acumulada, y nada lo impide hoy: no hay comprobación automática. Se registra como
`RF-105-003` en el grupo 6. Esta misma tarjeta corrige sus propios enlaces al archivar (tarea 8.5).

## Deuda documental: menciones a configuración local, `RF-099-001` (grupo 5)

Ejecutado el 2026-10-09 sobre la rama en `2f5237e`.

### Criterio

Es el que aplicó JUP-099 a los documentos de JUP-098 (ver su `review.md` archivado, tarea 2.3):

- Cambia **solo la referencia**: una ruta, un nombre de herramienta o un comando que no se puede
  reproducir desde el repositorio. **Nunca** una cifra, un resultado, un veredicto ni un enlace.
- Donde el texto ya traía comandos reales del repositorio, la referencia se sustituye por ellos
  (`corepack pnpm test`, `lint` y `typecheck` desde la raíz en la evidencia de JUP-095).
- Donde no existe equivalente versionado (el comprobador local de DoD, la protección de tests contra
  edición, el procedimiento local de mutación), la redacción pasa a ser neutral y **no se inventa un
  comando**: se nombra la existencia de una herramienta local sin ruta ni nombre de archivo, como
  hizo JUP-099 con «el test estaba protegido contra edición en el entorno local».
- Donde había un resultado de una herramienta sin equivalente (el escaneo de secretos del comprobador
  local en la evidencia de JUP-097) el resultado se conserva y se dice que no se puede reproducir.
- Este documento y el `design.md` de la tarjeta sí nombran los términos que se retiran de los demás,
  porque describen el propio hallazgo y su búsqueda. Es el caso «legítimo» que ya existe en el
  `review.md` archivado de JUP-099 y en la fila del backlog, y por eso la búsqueda los excluye.

### Sustituciones

| Referencia original | Redacción nueva |
| --- | --- |
| `.claude/harness/check-dod.mjs`, `check-dod.mjs` | «el comprobador local de DoD» (la evidencia de JUP-095 nombra los tres comandos de la raíz) |
| `lock-committed-tests.mjs`, hook con ruta en `.claude/hooks/` | «la protección de tests del entorno local» / «el hook de protección de tests del entorno local» |
| `.claude/settings.json` (vaciado y restaurado durante el bypass) | «la configuración local de esa protección», «archivo local de configuración de la protección» |
| `.claude/` en `.gitignore` y «ningún archivo de `.claude/` colado» | «la carpeta de configuración de agentes» y «ninguna configuración personal de agentes colada» (lo que comprueba `jup:cleanup:check`) |
| `.claude/harness/mutation.md`, `mutation.md` | «el procedimiento local de mutación»; en dos puntos «excepción doc-only», como en JUP-099 |
| `.claude/harness/stryker.conf.mjs` (umbral `break: 80`) | «umbral de 80 que se usa como criterio de lectura del resultado», que es la redacción de JUP-099 |
| `.claude/harness/workflow.md` §5-7, §7 | «el flujo de trabajo del equipo» (pasos 5 a 7 en uno de los dos) |
| Comentario de `apps/frontend/vite.config.ts` | «el mutation testing con Stryker» (se retira la ruta; la explicación de `.stryker-tmp` sigue igual) |

### Líneas con mención sustituidas por archivo

| Menciones | Archivo |
| ---: | --- |
| 1 | `apps/frontend/vite.config.ts` (solo comentario) |
| 1 | `docs/evidence/JUP-093-validation.md` |
| 1 | `docs/evidence/JUP-095-validation.md` |
| 3 | `docs/evidence/JUP-097-validation.md` |
| 1 | `openspec/changes/archive/2026-09-02-jup-092-frontend-typescript-adr/review.md` |
| 6 | `openspec/changes/archive/2026-09-06-jup-093-configure-typescript/review.md` |
| 3 | `openspec/changes/archive/2026-09-06-jup-093-configure-typescript/tasks.md` |
| 1 | `openspec/changes/archive/2026-09-07-jup-094-reconcile-package-json/review.md` |
| 17 | `openspec/changes/archive/2026-09-12-jup-095-portar-codigo-fuente/review.md` |
| 1 | `openspec/changes/archive/2026-09-12-jup-095-portar-codigo-fuente/tasks.md` |
| 7 | `openspec/changes/archive/2026-09-21-jup-097-reconcile-api-layer/review.md` |
| **42** | **11 archivos** |

`git diff --stat`: 47 inserciones y 45 eliminaciones en 11 archivos. Hay más líneas tocadas que
menciones porque en la evidencia de JUP-093 se reajustó el párrafo (4 líneas) y porque las
evidencias de JUP-095 y JUP-097 ganan una línea cada una, al ser más larga la frase nueva (las dos
líneas de diferencia entre inserciones y eliminaciones). Se revisó el diff palabra a palabra
(`git diff --word-diff`): en todas las líneas cambia únicamente el texto de la referencia.

### Resultado

| Comprobación | Antes | Después |
| --- | --- | --- |
| Búsqueda de menciones (misma de la línea base) | 42 líneas en 11 archivos | **0** |
| Menciones legítimas que describen el propio hallazgo (8 en el `review.md` archivado de JUP-099 y 1 en el backlog) | 9 | 9, sin tocar |
| `corepack pnpm --filter @finops/frontend typecheck`, `lint` y `build` tras el cambio de `vite.config.ts` | — | los tres con salida 0 |
| `corepack pnpm --filter @finops/frontend test -- --maxWorkers=1` | — | 53 archivos y 629 pruebas correctas, 160 s |
| `corepack pnpm jup:cleanup:check` | — | `[OK] 930 archivos sin agentes personales, binarios ni tareas paralelas.` |
| `corepack pnpm repository:governance:test` | — | 13 de 13 |

### Lo que este grupo no resuelve ni valida

- **Los registros siguen diciendo que existió una herramienta local.** Es lo que pasó y lo que se
  quiere conservar: lo que se retira es la ruta y el nombre. «El comprobador local de DoD» sigue sin
  poder reproducirse desde el repositorio; lo que ya eran comandos reales se dejó con esos comandos.
- **No se volvió a ejecutar ninguno de los comandos históricos** (mutación, DoD, hooks): las
  sustituciones son de redacción y no acreditan de nuevo ningún resultado de aquellas tarjetas.
- **La palabra «hook» y la expresión «hook-disable dance» se conservan.** No identifican una ruta ni
  un archivo y la búsqueda del hallazgo no las incluye. Si el equipo quiere un criterio más estricto
  que el de JUP-099, es una decisión a tomar aparte.
- **La protección contra reincidencias ya existe**: `tools/jup-cleanup-check.mjs` rechaza configuración
  personal de agentes en el repositorio. Lo que no impide es que un documento nuevo cite esa
  herramienta por su nombre; no se añadió ninguna comprobación de eso.

## Hallazgos de la épica (grupo 6)

### Tras traer `develop` (tarea 6.1)

Ejecutado el 2026-10-09. La rama partía de `ff2ea6b`; `origin/develop` estaba en `ceb6520`, con cuatro
pull requests nuevos: #83 (JUP-108, LiteLLM en el Compose principal), #76 (JUP-064, contribuciones
del equipo), #72 (JUP-061, archivado del registro de decisiones) y #82 (JUP-070, evaluación de las
respuestas del chat). Fusionado con `git merge origin/develop` (commit `ce1a87d`), **sin
conflictos**. El único archivo tocado por las dos partes fue `docs/architecture.md`.

| Comprobación tras la fusión | Resultado |
| --- | --- |
| `develop` toca `apps/frontend` | 0 archivos; `routes.tsx` y las pantallas no cambian |
| #66 (JUP-017) y #69 (JUP-036) | no están en `develop`; el recuento de pantallas no cambia (9 rutas bajo sesión, 5 con backend, 4 de demostración) |
| Enlaces relativos rotos | 2 (los falsos positivos de `JUP-099-validation.md`); lo traído de `develop` no añade ninguno |
| Menciones a configuración local (búsqueda del hallazgo) | 0; lo traído de `develop` no añade ninguna |

### Comprobación de `GET /billing/summary` (tarea 6.2)

Hecha el 2026-10-09 leyendo el código del backend, sin ejecutarlo (no se levantó CockroachDB):

- `apps/backend/app/db/database.py` (líneas 206 a 286): los totales y los grupos salen de una consulta
  que une `azure_cost_records` con `azure_cost_ingestion_runs` completadas, filtradas por cliente, y
  suma `pretax_cost` por moneda; `monthly_spend` es el total único o `None`. No hay ningún importe
  constante.
- `savings_identified` es `None` en la respuesta (línea 285) y el modelo lo declara como `None = None`
  (`apps/backend/app/schemas/billing.py`, línea 43). `open_ingestions` cuenta filas de `jobs`.
- El `README.md` del backend describe el contrato v2 de JUP-026 con el ahorro en `null`.

Con eso `RF-091-004` se cierra por lo que dice: el dato ficticio ya no existe. **No** se cierra la
ausencia de un motor de ahorro, que pasa a `RF-091-003`.

### Disposición de los 21 hallazgos (tareas 6.3 y 6.4)

Cada fila del backlog conserva su descripción original y recibe al final de su última celda una nota
«Cierre de épica (JUP-105, 2026-10-09)» con el motivo; el estado y el responsable se cambian en sus
celdas. Se comprobó fila por fila contra `HEAD` que solo cambian esas tres celdas y que ninguna
celda anterior se altera (21 filas cambiadas, 0 problemas).

| Hallazgo | Antes | Después | Responsable | Motivo |
| --- | --- | --- | --- | --- |
| `RF-091-004` | `Open` | **`Fixed`** | Equipo Economicon | El dato ficticio ya no existe (JUP-026 y JUP-055); el ahorro pasa a `RF-091-003` |
| `RF-099-001` | `Open` | **`Fixed`** | Equipo Economicon | Grupo 5: 42 menciones sustituidas, búsqueda en 0 |
| `RF-099-004` | `Open` | **`Fixed`** | Equipo Economicon | Grupo 4: 64 de 66 enlaces corregidos; prevención en `RF-105-003` |
| `RF-093-001` | `Open` | `Open` | Alejandro (consola externa y corrección permanente pendientes) | Diagnóstico Codex recibido; ver abajo |
| `RF-091-003` | `Open` | `Open`, reformulado | Decisión de producto del equipo | Quedan 4 pantallas de demostración sin contrato, más inventario y ahorro |
| `RF-095-002` | `Open` | `Open`, actualizado | Decisión de producto del equipo | Pasa de «5 pantallas» a 4; enlaza al recuento |
| `RF-104-004` | `Open` | `Open`, frase corregida | Decisión de producto del equipo | Depende de `RF-091-003`; `/` ya no tiene sección de demostración |
| `RF-104-003` | `Open` | `Open` | Decisión de producto del equipo | Capacidad ausente del contrato (leer el estado de un trabajo) |
| `RF-099-002`, `RF-099-003` | `Open` | `Open` | Decisión de producto del equipo | Decisiones de diseño sobre los datos demo y los tonos |
| `RF-098-002` | `Open` | `Open` | Decisión del equipo (técnica) | Exige cambiar un requisito vigente de `demo-auth-session` |
| `RF-098-004`, `RF-103-005` | `Open` | `Open` | Decisión del equipo (técnica) | Plazos de tests bajo carga; el `README.md` documenta las dos mitades |
| `RF-104-001` | `Open` | `Open` | Equipo Economicon (tarjeta pedida) | Único defecto funcional visible; el efecto sigue igual (líneas 52 a 63 de `ConversationsPage.tsx`) |
| `RF-103-001`, `RF-103-002` | `Open` | `Open` | Equipo Economicon (tarjeta pedida) | Una sola tarjeta de tooling de `dev` |
| `RF-098-003` | `Open` | `Open` | Equipo Economicon (tarjeta pedida) | Defecto de presentación; la opción «JUP-099» ya no existe |
| `RF-098-001`, `RF-103-003`, `RF-103-004`, `RF-104-002` | `Open` | `Open` | Equipo Economicon (sin tarjeta; se pide si se prioriza) | Sin riesgo funcional conocido o sin causa verificada |

Resultado: 3 pasan a `Fixed` y 18 siguen `Open`, cada uno con motivo y con quién da el siguiente paso.

**Qué no se hizo con los responsables.** Trello es la fuente de verdad de las personas asignadas y
esta tarjeta no la consulta, así que el backlog no pone nombres de personas salvo en `RF-093-001`,
donde la confirmación que falta es de Alejandro y consta en esta evidencia. En el resto la columna
dice si lo que falta es una decisión (de producto o técnica) o una tarjeta. **Asignar personas queda
para quien lleva el tablero.**

**`RF-093-001` por persona (tarea 6.4).** Estado `Open`, con la frase de estado reformulada:

| Persona | Resultado |
| --- | --- |
| Victor | Reproducido y corregido con `corepack enable` (JUP-103) |
| Lucía | Reproducido y corregido (JUP-103) |
| Paris | **No reproduce el fallo** (2026-10-09): el diagnóstico imprime `9.0.0` y `lint --force` pasa 4 de 4 sin haber hecho `corepack enable`. No acredita la corrección ni explica por qué allí no falla |
| Alejandro | Diagnóstico Codex del 09/10 recibido: pnpm 11.19.0, lint 0/4 `NO_TTY`. Consola normal y corrección permanente pendientes |

No pasa a `Fixed`: faltan la confirmación de Alejandro en consola externa y
evidencia de corrección permanente del runtime que aún falla.

### Hallazgos nuevos (tarea 6.5)

| ID | Qué registra |
| --- | --- |
| `RF-105-001` | Retirar la ruta puente `/overview-legacy`, con el inventario de lo que arrastra (página, hook, pruebas, 9 archivos de pruebas que la nombran en 30 líneas, entrada del menú) y los comentarios desfasados de `Layout.tsx`. Carril `standard` |
| `RF-105-002` | Dos módulos sin importador: `src/data/demo/executiveCostDashboard.ts` y `src/hooks/useCostKpis.ts` |
| `RF-105-003` | No hay comprobación automática de enlaces relativos: volverá a pasar al archivar |

### Tarjetas pedidas al líder (tarea 6.6)

La petición se hace en Trello, de forma independiente de esta rama, por Victor, que es quien lleva el
tablero; esta tarjeta no la ejecuta ni la comprueba. Se dio por hecha el 2026-10-09 por indicación
del líder, y **ningún número de tarjeta consta en el repositorio** (no se ha inventado ninguno). Las
filas del backlog dicen «tarjeta pedida» para estos cuatro hallazgos:

1. `RF-104-001`: conversación nueva que no recibe el mensaje. Es la de mayor valor.
2. `RF-103-001` y `RF-103-002`: `dev` desde la raíz (una sola tarjeta).
3. `RF-098-003`: JSON crudo en el error de credenciales.

`RF-105-001`, `RF-105-002` y `RF-105-003` quedan «sin tarjeta; se pide si se prioriza», como los
demás hallazgos de bajo riesgo.

### Verificación del grupo

| Comprobación | Resultado |
| --- | --- |
| Comparación del backlog con `HEAD` | 21 filas cambiadas, 0 problemas, 18 `Open` y 3 `Fixed` |
| Columnas de las filas nuevas | 10 cada una |
| Referencias a `RF-105-00x` en el repositorio | todas apuntan a un hallazgo definido |
| Recorrido de enlaces | 2 rotos, los falsos positivos conocidos |

**No se validó:** que `GET /billing/summary` devuelva lo descrito (se leyó el código, no se ejecutó
el backend ni sus pruebas); quién es el responsable de cada hallazgo según Trello;
la consola normal de Alejandro ni la corrección permanente de `RF-093-001`.

## Cierre del spike (grupo 7)

Ejecutado el 2026-10-09 sobre la rama tras fusionar `develop`. Es el último archivo compartido que se
edita, como pide la regla 9 de la tarjeta, y el diff es de 122 inserciones y 18 eliminaciones: las 18
líneas eliminadas son todas sustituciones previstas (se listaron una a una).

### Cambios en `docs/spikes/frontend-migration.md`

| Qué | Antes | Ahora |
| --- | --- | --- |
| F1: JUP-090, JUP-091 y JUP-092 | Sin enlace a su change archivado | Enlazados a `openspec/changes/archive/` |
| F3: JUP-095 | Sin enlace | Enlazado, junto con su reconciliación con `develop` (`jup-095-reconciliar-develop`), con PR #36 y fecha |
| F3: JUP-099 | «implementada, validada y archivada el 2026-10-01; integración de PR #54 pendiente» | «fusionada el 2026-10-01 (PR #54)» |
| F4: JUP-103 | «implementada» | «fusionada el 2026-10-07 (PR #75)» |
| F5: JUP-104 | «implementada» | «fusionada el 2026-10-07 (PR #79)» |
| F1: casilla de ADR-0003 en los `design.md` | Sin marcar | Marcada con su comprobación y una salvedad (abajo) |
| F5: marcador provisional de cierre | Una tarjeta con tres casillas sin marcar | `jup-105-close-frontend-migration` con dos casillas marcadas y una pendiente con su explicación; la revisión del equipo se declara como la del propio pull request |
| Afirmaciones históricas «único dashboard con datos reales» | Sin matizar | Tres notas fechadas, sin reescribir el texto |
| Tabla «Contexto: origen vs destino» | Sin aviso de que la columna «Destino actual» era el punto de partida | Nota fechada |
| Plantilla «Checklist operacional» | Casillas sin marcar sin explicación | Declarada plantilla |
| «Próximos pasos» | Terminaba en el punto 12 | Punto 13 con el estado final |

**Fechas de fusión.** Salen de `git log` sobre `origin/develop` (el commit de fusión de cada pull
request) y se dan en UTC. `#75` figura en Git como `2026-10-06T20:27:47-04:00`, que es el 7 de octubre
en UTC y coincide con la fecha de la tarjeta; el resto no cambia de día.

**Salvedad de la casilla de ADR-0003.** Se comprobó con `Select-String` sobre cada `design.md`
archivado de F2 y F3: JUP-093, JUP-094, JUP-095, JUP-098 y JUP-099 enlazan el ADR; **JUP-097 lo cita
tres veces por su identificador pero no lo enlaza**. La casilla se marca con esa salvedad escrita y
no se edita el `design.md` archivado de JUP-097.

**Casillas del marcador de F5.**

| Casilla | Estado | Por qué |
| --- | --- | --- |
| Comandos de la batería (`openspec:validate`, `lint`, `build`, `install --frozen-lockfile`) | **Sin marcar, con explicación** | Se ejecutan en el grupo 8; la tarea 8.1 la marca con el resultado |
| ADR de TS `Accepted` y documentación sincronizada | Marcada | ADR-0003, ADR-0004 y ADR-0012 en `Accepted` en su archivo y en `docs/adr/README.md` (líneas 34, 35 y 43); README del frontend y `docs/architecture.md` corregidos en el grupo 3 |
| Archivado de los cambios OpenSpec de la épica | Marcada | Los doce (JUP-083, 090 a 095, 097, 098, 099, 103 y 104) están en `openspec/changes/archive/`; `openspec list` no muestra ninguno activo |
| Revisión del equipo | No es casilla | Es la del propio pull request de JUP-105; no se puede registrar de antemano |

### Punto 13 del spike: de dónde sale cada afirmación

| Afirmación | Fuente |
| --- | --- |
| TypeScript estricto con `allowJs: false`, 0 archivos `.js` o `.jsx` en `src/` y `tests/` | Grupos 1 y 2 de esta evidencia |
| 629 pruebas en 53 archivos con `--maxWorkers=1` | Grupo 2 y grupo 5; se contrasta de nuevo en el grupo 8 |
| 9 rutas, 5 con backend, 4 de demostración, 3 sin rótulo | Grupo 3 y 6.1 |
| Pull requests y fases | `git log` sobre `origin/develop` por el título de cada fusión |
| 21 hallazgos, 3 `Fixed` y 18 `Open` | Grupo 6, comparación del backlog con `HEAD` |
| Tarjetas pedidas en Trello | Indicación del líder; esta rama no lo comprueba |
| `RF-026-002` como limitación conocida | Backlog (`Open`, Medium) |

### Verificación del grupo

| Comprobación | Resultado |
| --- | --- |
| `git grep -n -e "jup-0xx" -e "\- \[ \]"` sobre el spike | Quedan 3 usos y se revisaron uno a uno: `jup-0xx-verificar-docker-compose` (tarjeta resuelta que nunca tuvo número, y su texto lo dice), la casilla de la batería (con su explicación) y la plantilla, que ahora se declara como tal |
| Recorrido de enlaces relativos | 2 rotos, los falsos positivos conocidos; los enlaces nuevos del spike resuelven |
| `corepack pnpm openspec:validate`, `jup:check` y `jup:cleanup:check` | Los tres en verde |

**No se validó:** que los pull requests se fusionaran en esas fechas según la interfaz de GitHub (se
usó Git, no la API); que las tarjetas de Trello de los hallazgos existan; ni las cifras del punto 13
que dependen de la batería completa (629 pruebas, 0 archivos JavaScript), que se contrastan en el
grupo 8.

## Batería completa (grupo 8, tarea 8.1)

Ejecutada el 2026-10-09 en Windows 11, Node `v24.15.0`, desde la raíz con `corepack pnpm`, sobre la
rama en `364ad7d` (con `develop` en `ceb6520` ya fusionado). Entorno virtual de Python
`C:\Users\victo\Pontia\.venv-tfm` (Python 3.13.7) activado dentro de cada ejecución, porque turbo usa
el `python` del `PATH`. La salida íntegra de cada comando se guardó fuera del repositorio.

**Entorno.** Docker Desktop corría, pero sin ningún proyecto de Compose (`docker compose ls` vacío) y
con un único contenedor: `buildx_buildkit_desktop-linux`, el constructor interno de Docker Desktop,
que no se tocó porque no ocupa ningún puerto de la batería. Había un PostgreSQL nativo de Windows en
el puerto 5432, ajeno a Docker y a este repositorio, que tampoco se tocó. Los puertos que usan
`local:test` y `dev` (5173, 8000, 8001, 8002, 26257, 8080, 5672 y 15672) estaban libres. La batería
no necesita la infraestructura de Compose.

| Comando | Resultado | Tareas forzadas |
| --- | --- | --- |
| `corepack pnpm install --frozen-lockfile` | código 0; `git status` sin cambios (lockfile intacto) | no aplica |
| `corepack pnpm lint --force` | código 0; 4 de 4, 0 en caché | 4 `cache bypass, force executing` |
| `corepack pnpm typecheck --force` | código 0; 1 de 1, 0 en caché | 1 |
| `corepack pnpm build --force` | código 0; 4 de 4, 0 en caché | 4 |
| `TURBO_FORCE=true corepack pnpm run test "--filter=!@finops/frontend"` | **código 1**: 2 de 3 paquetes correctos; falla `@finops/backend` | 3 |
| `TURBO_FORCE=true corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1` | código 0; 53 archivos y 629 pruebas | 1 |
| `corepack pnpm openspec:validate` | código 0; 55 de 55 | no aplica |
| `corepack pnpm jup:check -- --change jup-105-close-frontend-migration` | código 0 | no aplica |
| `corepack pnpm jup:cleanup:check` | código 0; 971 archivos | no aplica |

Ninguna ejecución tuvo `cache hit`. `build` avisa de que los paquetes de Python no declaran salidas en
`turbo.json`, y el frontend de que un fragmento supera 500 kB: ninguno es un error. Tras toda la
batería `git status` está vacío.

### `test` por mitades

`corepack pnpm test` literal, con los cuatro paquetes a la vez, no se ejecutó: falla de forma distinta
en cada ejecución (`RF-103-005`, `RF-098-004`) y el `README.md` indica las dos mitades.

| Paquete | Resultado |
| --- | --- |
| `@finops/azure-cost-api` | 59 pasan |
| `@finops/processor` | 448 pasan, 57 omitidos |
| `@finops/frontend` | 629 pasan en 53 archivos, con `--maxWorkers=1` |
| `@finops/backend` | **753 pasan, 145 fallan**, 34 omitidos (159 s) |

### Los 145 fallos del backend

No son un fallo de la migración ni de esta tarjeta (no se toca ningún archivo del backend), y no son
los plazos de tiempo conocidos. Son de cuatro archivos de JUP-047, fusionado en #81 después de que
JUP-103 ejecutara esta misma batería:

| Archivo | Fallos |
| --- | ---: |
| `tests/test_health_provider_admission_jup047.py` | 72 |
| `tests/test_health_provider_response_jup047.py` | 37 |
| `tests/test_system_health_jup047.py` | 33 |
| `tests/test_health_provider_policy_jup047.py` | 3 |

Dos mensajes: «Only controlled gateway doubles are permitted in Red» (112) y «JUP-047 Red must not
open a socket or spend inference credit» (33). **Causa medida con las trazas:** los 145 fallos pasan
por `asyncio.run` → bucle `Proactor` → `_make_self_pipe` → `socket.socketpair()`; en Windows, este
Python no tiene `AF_UNIX` (`hasattr(socket, "AF_UNIX")` da `False`), así que `socketpair` usa
`_fallback_socketpair`, que hace una conexión TCP a `127.0.0.1`, y el fixture automático `no_network`
de esos archivos sustituye `socket.socket.connect` por un fallo. Hay 145 trazas con
`_fallback_socketpair` para 145 fallos, así que explica todos y los otros 753 tests del paquete
pasan. Registrado como `RF-105-004`.

**Contraste en Linux, añadido tras abrir el pull request:** no se ejecutó en Linux en esta máquina,
pero el check `Python tests (backend)` de la CI pasó sobre este mismo commit (ver «Pull request y
CI»), y ese job ejecuta `python -m pytest tests -q` en `apps/backend`, es decir, también los cuatro
archivos de JUP-047. Lo hace en `ubuntu-latest` con Python 3.12, y la máquina de Windows usa 3.13.7,
así que la CI es coherente con la causa medida pero **no aísla el sistema operativo como única
diferencia**.

## Trazabilidad de los criterios de aceptación (grupo 8, tarea 8.2)

| # | Criterio de la tarjeta | Estado | Evidencia |
| ---: | --- | --- | --- |
| 1 | `openspec:validate`, `jup:check`, `jup:cleanup:check`, `lint`, `typecheck`, `build`, `test` (por mitades) e `install --frozen-lockfile` en verde, desde la raíz | **Cumplido salvo `test` del backend en Windows** | Batería completa. Todo en verde excepto 145 tests de JUP-047 del backend (`RF-105-004`); frontend, `processor` y `azure-cost-api` pasan. No se da por cumplido del todo |
| 2 | `allowJs` en `false` y el frontend compila y pasa sus pruebas | Cumplido | «Endurecimiento de `allowJs`»: diff de una línea, control positivo con `TS7016`, 629 pruebas |
| 3 | El spike sin placeholder `jup-0xx` pendiente ni casilla sin marcar sin explicación, y su último punto declara el estado final | Cumplido | «Cierre del spike»; queda `jup-0xx-verificar-docker-compose` (tarjeta resuelta que nunca tuvo número) y la plantilla del checklist, declarada como tal |
| 4 | Un único recuento de pantallas, fechado y verificado contra el código; README, `RF-095-002`, `RF-091-003` y el mapa de carencias coinciden | Cumplido | «Recuento de pantallas»; vive en la sección «Rutas» del README y los demás enlazan a ella |
| 5 | Ningún documento versionado afirma ya que `/overview-legacy` es el único dashboard con datos reales ni que `Frontend tests` es un check obligatorio, sin una nota que lo corrija | Corregido en el aporte residual del 10/10 | Notas históricas preservadas; comentario de `DashboardPage.test.tsx` corregido y notas añadidas a tasks/review de JUP-097. Ver [comprobación incremental](JUP-105-residual.md) |
| 6 | Cada hallazgo abierto de la épica con responsable y motivo; los que cierra la épica, en `Fixed` con su evidencia | Cumplido | «Hallazgos de la épica»: 3 `Fixed` y 18 `Open`; los responsables son categorías, no personas |
| 7 | Deuda documental resuelta (cero enlaces rotos salvo falsos positivos, cero menciones no legítimas) o `Open` con responsable | Cumplido | Enlaces 66 → 2 (los falsos positivos); menciones 42 → 0 |
| 8 | Decisión sobre `/overview-legacy` y el módulo huérfano registrada | Cumplido | Decisión 5 del `design.md`, aprobada en el gate; `RF-105-001` y `RF-105-002` |
| 9 | Estado final de la épica declarado sin ambigüedad: logrado, no logrado y decisiones de producto pendientes | Cumplido | Punto 13 del spike |

**Sobre el criterio 5.** Al comprobarlo en todo el repositorio, incluidos los registros archivados,
aparecieron afirmaciones que mi búsqueda del grupo 3 había excluido: los cuatro documentos
archivados de JUP-095 (`design.md`, `proposal.md`, `review.md` y `tasks.md`) dicen que `Frontend
tests` se promueve a comprobación obligatoria (12 líneas), y `design.md`, `proposal.md` y `review.md`
de JUP-095 y `proposal.md` de JUP-097 llaman a `/overview-legacy` el único dashboard o la única
pantalla con datos reales (7 líneas). Eran ciertos el día que cada tarjeta los escribió y no se
reescriben. **Por indicación del líder (2026-10-09) se les añadió una nota fechada al inicio**, y
solo se añadieron líneas: 51 insertadas y 0 eliminadas en 5 archivos.

| Archivo archivado | Afirmaciones que anota |
| --- | --- |
| `2026-09-12-jup-095-portar-codigo-fuente/design.md` | `Frontend tests` obligatorio; único dashboard |
| `2026-09-12-jup-095-portar-codigo-fuente/proposal.md` | ambas |
| `2026-09-12-jup-095-portar-codigo-fuente/review.md` | ambas |
| `2026-09-12-jup-095-portar-codigo-fuente/tasks.md` | `Frontend tests` obligatorio (tareas 1.1, 2.4 y 2.5) |
| `2026-09-21-jup-097-reconcile-api-layer/proposal.md` | único dashboard |

Cada nota remite a la guía de gobernanza y a la sección «Rutas» del README del frontend, y sus 8
enlaces resuelven. **Dos búsquedas anteriores fallaron por la misma razón:** las frases partidas entre
dos líneas (por ejemplo, «su único» al final de una línea y «dashboard» al inicio de la siguiente en
el `proposal.md` de JUP-095) no las encuentra una búsqueda por línea; se repitió con búsqueda
multilínea.

**Salvedad registrada el 09/10, subsanada en el aporte del 10/10.** El comentario de cabecera de `apps/frontend/src/pages/DashboardPage.test.tsx`
(línea 6) dice «es la unica pantalla que consume datos reales del backend». Es código de pruebas vivo,
no un documento, y el gate pre-código limita los archivos de `apps/**` que esta tarjeta modifica, así
que no se tocó entonces; se anotó en el inventario de `RF-105-001`. El encargo
posterior autoriza completar el residual: el comentario ya remite al recuento
vigente, sin cambiar el código de la prueba. La retirada de la ruta sigue pendiente.

### Antes y después

| Medida | Línea base (2026-10-09) | Al cerrar |
| --- | --- | --- |
| `allowJs` | `true` | `false` |
| Archivos JavaScript en `src/` y `tests/` | 0 | 0 |
| Pruebas del frontend (un worker) | — | 629 en 53 archivos |
| Lint del frontend | 0 violaciones | 0 violaciones |
| Enlaces relativos rotos | 66 en 26 archivos | 2 en 1 archivo (falsos positivos) |
| Menciones a configuración local | 42 en 11 archivos | 0 |
| Hallazgos de la épica | 21 `Open` | 3 `Fixed` y 18 `Open` |
| Hallazgos nuevos | — | `RF-105-001` a `RF-105-004` |
| Recuentos de pantallas | Tres textos que se contradecían | Uno, en el README del frontend |
| Marcador de cierre en el spike | Sin cerrar | Cerrado, con punto 13 |

### Lo que no se validó

- **`test` del backend en Windows** (`RF-105-004`): 145 fallos de JUP-047; no se ejecutó en Linux
  fuera de la CI, que sí pasa con Python 3.12.
- **El comando literal `corepack pnpm test`** con los cuatro paquetes a la vez (`RF-103-005`).
- **Ninguna pantalla en un navegador.** No se levantó el stack ni se abrió el frontend: el recuento
  de pantallas y el mapa de carencias se contrastaron con el código, y el frontend se comprobó con
  `typecheck`, `lint`, `build` y las pruebas.
- **El backend en ejecución.** Lo de `GET /billing/summary` se leyó en el código.
- **Consola normal de Alejandro y corrección permanente de `RF-093-001`**, y qué versión de pnpm global tiene Paris. El diagnóstico Codex recibido no las sustituye.
- **Los responsables de los hallazgos en Trello** y que las tarjetas pedidas existan.
- **La integración continua del pull request**: se registra al abrirlo (tarea 8.6).
- **`local:doctor` y `local:smoke`**: no se ejecutaron; la tarjeta no toca el entorno de Compose.
- **Que las pruebas de JUP-047 pasen en Linux con la misma versión de Python** que esta máquina: la
  CI las pasa con la 3.12, no con la 3.13.7.

## Gate post-review y archivado (grupo 8, tarea 8.5)

Ejecutado el 2026-10-09.

**Gate post-review.** El líder revisó el `review.md` y fijó tres puntos: `RF-093-001` se queda `Open`
(Alejandro sin confirmar), el comentario de `DashboardPage.test.tsx` se deja como está (anotado en
`RF-105-001`) y los roles del pull request son los vigentes. Se registró como `post-review`,
`approved`, `archive` en el bloque `## Human Approval` del `review.md`, **a partir de su respuesta
«Continúa» y no de una frase aparte de «aprobado»**; el bloque lo dice y se corrige antes de abrir el
pull request si esa lectura fuera incorrecta.

**Comprobaciones previas al archivado:** `corepack pnpm openspec:validate` (55 de 55) y
`corepack pnpm jup:check -- --change jup-105-close-frontend-migration`, las dos en verde.

**Archivado:** `corepack pnpm exec openspec archive jup-105-close-frontend-migration --yes` →
`openspec/changes/archive/2026-10-09-jup-105-close-frontend-migration/`.

| Qué | Resultado |
| --- | --- |
| Spec `frontend-typescript-tooling` sincronizada | 2 requisitos añadidos, 1 modificado y 2 retirados, como el delta; la spec principal queda con 6 requisitos y sin marcador `TBD` en su propósito |
| Avisos del comando (no bloqueantes) | La sección «Why» del `proposal.md` supera los 1000 caracteres; 2 tareas sin marcar (8.5 y 8.6, las que se estaban ejecutando) |
| Enlaces rotos creados por el archivado | 5: 4 dentro del change (bajó un nivel) y 1 en la cabecera de esta evidencia (apuntaba a la carpeta sin archivar) |
| Corrección | Con el guion de enlaces del grupo 4, adaptado para leer también archivos aún sin versionar: 4 archivos escritos, 5 enlaces |
| Comparación del change archivado con su versión en `HEAD` | 6 archivos; cambian 4 líneas, todas destinos de enlace; el `review.md` añade al final las 39 líneas del bloque de aprobación; 0 problemas |
| Recorrido de enlaces relativos | 7 → **2** (los falsos positivos de `JUP-099-validation.md`) |
| Enlace del spike (F5) al change archivado | Añadido |
| `openspec:validate` tras archivar | 54 de 54 |
| `jup:cleanup:check` y `jup:check:all` | En verde |

`jup:check -- --change jup-105-close-frontend-migration` ya no puede ejecutarse tras archivar (falla
con «No existe `openspec/changes/jup-105-close-frontend-migration`», porque solo mira changes
activos); se ejecutó antes, como indica el flujo, y pasó.

## Pull request y CI (grupo 8, tarea 8.6)

Consultado el 2026-10-09 con la API pública de GitHub, sin credenciales.

**Pull request.** [#86](https://github.com/EconomiconFinOps/tfm-economicon/pull/86), abierto por
Victor contra `develop`, con título `chore(JUP-105): cerrar la epica de migracion del frontend` y
rama `chore/JUP-105-close-frontend-migration`. La cabeza es `502dd44` y GitHub cuenta 14 commits y 47
archivos con 2446 inserciones y 256 eliminaciones, que coincide con el diff local frente a `develop`.
La descripción se validó antes con `corepack pnpm pr:check` sobre un evento construido con ese
título, cuerpo, rama y base (`[OK] Pull request enlazado a JUP y preparado para revision`), y un
control negativo con una etiqueta de rol con tilde falló como debía.

**Higiene previa a abrirlo** (paso 7 del flujo): `jup:cleanup:check` (972 archivos),
`jup:check:all`, `openspec:validate` (54 de 54), los tests de `jup:cleanup` (6), de `pr:check` (57) y
de gobernanza (13), y la búsqueda de secretos en las 2072 líneas añadidas (0 coincidencias).

**CI sobre `502dd44`.** Hay dos ejecuciones del workflow `CI` para el mismo commit, porque lo lanzan
el `push` y el pull request:

| Ejecución | Estado al consultar | Jobs |
| --- | --- | --- |
| [CI del `push`, 38013186253](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38013186253) | **Completada con éxito** | `Frontend build`, `Frontend type check`, `OpenSpec`, `Python tests (azure-cost-api)`, `Python tests (backend)` y `Python tests (processor)` en verde; `JUP policy` omitido, porque solo corre en pull requests |
| [CI del pull request, 38013497033](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38013497033) | **En curso** | `JUP policy`, `OpenSpec`, `Frontend build`, `Frontend type check`, `Python tests (processor)` y `Python tests (azure-cost-api)` en verde; `Python tests (backend)` en ejecución |
| [PR reviews, 38013496936](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38013496936) | Completada con fallo | `JUP reviews` en rojo, **como se espera**: faltan las reviews `Revision JUP-105` y `Validacion JUP-105` |

El estado final de la ejecución del pull request no consta aquí, porque seguía en curso al consultar;
se consulta en la pestaña de checks del propio pull request, que además incluirá la CI del commit que
añade este registro.

**Qué acredita y qué no.**

- La CI de Linux pasa `Python tests (backend)` sobre `502dd44`, con los cuatro archivos de JUP-047
  incluidos. Es coherente con la causa de `RF-105-004`, pero la CI usa Python 3.12 y la máquina de
  Windows la 3.13.7, así que no demuestra que el sistema operativo sea la única diferencia.
- El criterio 1 sigue sin darse por cumplido del todo: la batería local con el backend en Windows no
  quedó en verde. Lo que cambia es que el check obligatorio de CI sí lo está.
- `JUP reviews` en rojo no es un fallo de la tarjeta: es la política esperando las dos reviews.
- Las reviews de Lucía y de Paris, y la CI final de la ejecución del pull request, quedan fuera de
  este documento.

**Cuándo se hizo este registro.** Con el pull request ya abierto y **sin reviews ni comentarios
publicados** (0 reviews, 0 comentarios de la conversación y 0 en línea, comprobado con la API justo
antes). El commit que lo añade no invalida ninguna aprobación porque todavía no hay ninguna.
