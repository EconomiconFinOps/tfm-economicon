# Evidencia JUP-097 — Reconciliar la capa de datos del frontend con los contratos del backend

- Fecha: 2026-09-21.
- Trello: https://trello.com/c/dsBZ7y0S/89-jup-097-reconciliar-la-capa-de-datos-del-frontend-con-los-contratos-del-backend
- Rama: `feat/JUP-097-reconcile-api-layer`.
- Base: `origin/develop` en `cb4edc3889ca440e04989bfecd4c0855248bb610`.
- OpenSpec: [jup-097-reconcile-api-layer](../../openspec/changes/jup-097-reconcile-api-layer/).
- Pull request: pendiente de abrir (tarea 8.7).
- CI de implementación: pendiente (se enlaza tras abrir el PR).

## Fuentes verificadas

- `apps/backend/app/api/routes/*.py` y `apps/backend/app/schemas/*.py` — código real del backend,
  no su documentación derivada (decisión 1 del `design.md`).
- Backend levantado con `docker compose up -d --wait backend` (más `processor` para las migraciones
  de pgvector, necesarias para `sendConversationMessage`) contra un `.env` local aislado y desechable.
- `apps/frontend/src/services/api.ts` y `contracts.ts` — las 10 operaciones exportadas, comparadas
  código a código y, para cada una, verificadas con `curl` contra el backend en ejecución.
- `apps/frontend/src/layouts/SessionGate.tsx`, `src/hooks/useDashboardData.ts`,
  `src/pages/DashboardPage.tsx` — código de producto tocado o auditado.
- `docs/planning/JUP-091-economicon-source-inventory.md` — mapeo de pantallas a contratos ya hecho
  sobre el origen, reutilizado para el mapa de carencias de esta tarjeta.
- `apps/frontend/tests/test-support.tsx` y las 4 suites de integración que lo consumen.

## Trazabilidad con requisitos

Capacidad nueva `frontend-api-layer` (6 requisitos, 14 escenarios,
[spec.md](../../openspec/changes/jup-097-reconcile-api-layer/specs/frontend-api-layer/spec.md)):

| Requisito | Cómo se verifica |
| --- | --- |
| El acceso al backend ocurre por un único punto declarado | Tarea 4.1: único `fetch(` en código de producto es `services/api.ts:37`; `VITE_API_BASE_URL` solo se lee ahí |
| Cada operación expuesta corresponde a un contrato real del backend | Grupo 1: 10/10 operaciones auditadas, cero desviaciones, código y backend en ejecución |
| Ninguna operación expuesta queda sin consumidor | `RF-090-003` resuelto: `fetchProfile` conectado (era la única huérfana) |
| Toda petición autenticada transporta identidad y ámbito de cliente | Grupo 4.4: cobertura ya existente heredada (`expectTenantRequest`) verificada línea a línea sobre las 6 operaciones tenant-scoped |
| Las pantallas servidas por el backend comunican carga y error | Grupo 5: cobertura heredada + test nuevo de transición sin fuga cruzada entre tenants |
| Cada pantalla sin contrato declara la capacidad que le falta | Grupo 6: mapa de 16 filas en `docs/planning/JUP-097-frontend-data-gap-map.md`, comentarios ampliados en los 5 módulos demo |

## Decisiones

Las 6 decisiones del `design.md` (auditoría contra backend real no README; `RF-090-003` resuelto
conectando `fetchProfile`, no retirándolo, con frontera explícita frente a `reconcile-auth-tenant`;
mapa de carencias en dos sitios con papeles distintos; forma de respuestas fijada con pruebas, no
validador en runtime; verificación asume navegador bloqueado por `RF-095-001`; **sin ADR nuevo**) —
todas aprobadas en el bloque `Human Approval` de `proposal.md` (`Approval type: pre-code`, Victor,
2026-09-20) y ejecutadas tal cual: ningún desvío de lo aprobado durante el `apply`.

## Validación ejecutada

### Tests (Vitest, `apps/frontend`)

Progresión por grupo (conteos acumulados al cierre de cada uno que tocó tests):

| Momento | Archivos | Tests |
| --- | --- | --- |
| Antes de esta tarjeta (heredado de JUP-095/JUP-087) | 33 | 71 |
| Tras grupo 3 (`RF-090-003`: `SessionGate.profile.test.tsx` + `SessionGate.mutation.test.tsx`) | 35 | 88 |
| Tras grupo 5 (`dashboard-tenant-transition.test.tsx` + 2 archivos de mutación) | 38 | 96 |
| **Final (grupo 8, tras las correcciones del grupo 7)** | **38** | **96** |

Comando: `corepack pnpm vitest run` desde `apps/frontend` (equivalente a
`pnpm --filter @finops/frontend test`, sustituto de `pnpm test` por `RF-093-001`: turbo resuelve
pnpm v11.9.0 en subprocesos pese a `packageManager: pnpm@9.0.0`).

Resultado final: `Test Files 38 passed (38)` / `Tests 96 passed (96)`.

**Nota de entorno, no de producto:** durante los grupos 5 y 6 se observaron dos corridas puntuales
con *flakiness* (contención de recursos de la máquina: decenas de procesos Chrome/VSCode activos
simultáneamente) — timeouts intermitentes en archivos no relacionados con los cambios de cada grupo
(`tenant-switching.test.tsx`), reproducidos y descartados como regresión al repetir la misma corrida
sin ningún cambio de por medio (falla una vez, pasa la siguiente). Documentado en detalle en
`review.md`, grupos 5 y 6.

### Mutación (Stryker, acotada por tarea)

| Archivo(s) mutados | Score inicial | Casos añadidos | Score final |
| --- | --- | --- | --- |
| `SessionGate.tsx` (grupo 3) | 68.16% (51 supervivientes) | 17 (`SessionGate.mutation.test.tsx`) | **84.36%** |
| `useDashboardData.ts` + `DashboardPage.tsx` (grupo 5) | 75.00% (12 supervivientes) | 7 (2 archivos `.mutation.test.tsx`) | **83.33%** |

Ambos por encima del umbral `break: 80` de `.claude/harness/stryker.conf.mjs`. Supervivientes
restantes en ambos casos clasificados y justificados como mutantes equivalentes o código muerto
defensivo (guardas de estrechamiento de tipos de TypeScript ya inalcanzables dado el contrato
público, claves de caché de React Query sin colisión posible en el flujo real) — detalle completo en
`review.md`, grupos 3 y 5, verificado de forma independiente por el agente QA en el grupo 3.

### Type-check y lint

`corepack pnpm typecheck` (3 proyectos: app, node, test) y `corepack pnpm lint` (`eslint src tests`)
— limpios en cada checkpoint de commit de la tarjeta (7 grupos con cambios de código o comentarios),
confirmados de nuevo al cierre.

### Build

`corepack pnpm build` (Vite 5) — `built in 6.12s`, bundle `765.73 kB` JS / gzip `216.31 kB`, CSS
`39.69 kB` / gzip `7.87 kB`. El aviso de chunk >500kB es preexistente a esta tarjeta (no se investiga,
fuera de alcance).

### DoD (`node .claude/harness/check-dod.mjs`)

Falla por `RF-093-001` (preexistente, documentado en `openspec/findings/backlog.md`): `corepack pnpm
test/lint/typecheck` desde la raíz pasan por turbo, que resuelve pnpm v11.9.0 en subprocesos pese a
`packageManager: pnpm@9.0.0`, y fallan en los 4 paquetes del monorepo (incluidos `backend`,
`processor`, `azure-cost-api`, que esta tarjeta no toca). Sustituto verificado en su lugar (mismo
criterio que JUP-093/094/095): `corepack pnpm --filter @finops/frontend {test,typecheck,lint,build}`,
los cuatro en verde — ver arriba. Escaneo de secretos del propio `check-dod.mjs`: `[PASS]`.

### Checks de trazabilidad OpenSpec/Trello

```
corepack pnpm openspec:validate       → 32 passed, 0 failed
corepack pnpm jup:check -- --change jup-097-reconcile-api-layer  → [OK] enlazado con Trello y completo
corepack pnpm jup:cleanup:check       → [OK] 594 archivos sin agentes personales, binarios ni tareas paralelas
corepack pnpm install --frozen-lockfile → Done, sin error (lockfile reproducible)
```

### Verificación directa contra el backend en ejecución (grupo 1)

Las 10 operaciones de `services/api.ts` probadas con `curl` contra el backend real (`docker compose
up -d --wait backend` + `processor` para las migraciones de pgvector), con el seed local rotado
(ver incidencia operativa abajo). Las 10 respuestas coinciden campo a campo con `contracts.ts`.
Detalle completo, con cada respuesta real, en `review.md`, sección 1.4.

Dos incidencias puramente operativas del entorno de pruebas local, sin relación con el código de
producto ni con el alcance de la tarjeta (documentadas en detalle en `review.md`, grupo 1):
rotación de una credencial demo heredada de un volumen Docker anterior (bloqueada a propósito por
`app/core/runtime_secrets.py`, resuelta con el procedimiento oficial del manual, consultada y
autorizada por Victor antes de ejecutar) y corrección del DSN de `pgvector` (dialecto `psycopg2` no
instalado, password desalineada con el volumen existente).

## Pendiente

- **E2E en navegador real: pendiente, no verificado en esta tarjeta** (decisión 5 del `design.md`).
  `RF-095-001`/`RF-087-001` (backend sin `CORSMiddleware`) bloquea el recorrido completo entre
  `localhost:5173` y `localhost:8000` en un navegador real. La verificación de esta tarjeta se apoyó
  en pruebas Vitest (comportamiento observable, `fetch` sustituido) y verificación directa contra el
  backend por fuera del navegador (`curl`, donde CORS no aplica) — declarado explícitamente aquí para
  no presentar como verificado un recorrido que no se probó.
- Enlaces de PR y CI: se rellenan tras abrir el pull request (tarea 8.7).
