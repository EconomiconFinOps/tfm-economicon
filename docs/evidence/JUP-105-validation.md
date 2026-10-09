# Evidencia JUP-105 — Cerrar la épica de migración del frontend

- Fecha: 2026-10-08 (verificación del alcance al proponer) y 2026-10-09 (línea base y consulta al
  equipo).
- Trello: https://trello.com/c/YZvtBdGV/100-jup-105
- Rama: `chore/JUP-105-close-frontend-migration`.
- Base: `develop` en `ff2ea6b`.
- OpenSpec: [jup-105-close-frontend-migration](../../openspec/changes/jup-105-close-frontend-migration/).
- Pull request: pendiente.
- CI: pendiente.

> Estado de este documento: en curso. Contiene la línea base y la consulta al equipo (grupo 1 de
> `tasks.md`), el endurecimiento de `allowJs` (grupo 2) y el recuento de pantallas con los textos
> vivos corregidos (grupo 3). El resto de secciones se añade según avanza la tarjeta.

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
| Alejandro | No | **No confirmado** |

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

**Consecuencia para el hallazgo.** Con una de las dos confirmaciones pendientes sin respuesta,
`RF-093-001` no pasa a `Fixed`. Se registra en el backlog en el grupo 6 de `tasks.md`, con el
resultado por persona y Alejandro como «no confirmado».

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
