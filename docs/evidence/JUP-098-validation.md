# Evidencia JUP-098 — Reconciliar el ciclo de sesión con la expiración del backend

- Fecha: 2026-09-27.
- Trello: https://trello.com/c/YqgPReKN/90-jup-098
- Rama: `feat/JUP-098-reconcile-auth-session`.
- Base: `origin/develop` en `d9271fdb7c0236b43511759c35fca109984c264d`.
- OpenSpec: [jup-098-reconcile-auth-session](../../openspec/changes/archive/2026-09-27-jup-098-reconcile-auth-session/) (archivado).
- Pull request: [#50](https://github.com/EconomiconFinOps/tfm-economicon/pull/50).
- CI de implementación: pestaña Checks del PR #50.

## Fuentes verificadas

- `apps/frontend/src/services/api.ts` — `fetchJson`, `invalidateSession`,
  `subscribeSessionInvalidation` (código real, verificado línea a línea antes de proponer).
- `apps/frontend/src/layouts/SessionGate.tsx` — suscriptor de invalidación, `handleLogout`, efecto
  de error de `/me`, redirección a `/login`.
- `apps/frontend/src/pages/LoginPage.tsx` — lectura del estado de navegación, aviso.
- `openspec/changes/archive/2026-09-24-jup-085-auth-session-contract/` — el change ya archivado que
  resolvió los criterios 1, 3, 4, 5 y 6 antes de que esta tarjeta se propusiera; verificado que su
  código sigue intacto en `develop` y que sus pruebas (`tests/auth-session.test.tsx`) no se tocaron.
- `apps/frontend/tests/test-support.tsx` y las suites de integración que lo consumen.

## Trazabilidad con requisitos

Capacidad modificada `demo-auth-session` (1 requisito añadido, 8 escenarios,
[spec.md](../../openspec/changes/archive/2026-09-27-jup-098-reconcile-auth-session/specs/demo-auth-session/spec.md)):
comunicar al operador que su sesión expiró cuando la invalidación la provoca un `401`, distinguible
del cierre manual y de los fallos que no son de autenticación, sin persistir el aviso.

## Los 8 criterios de aceptación de la tarjeta, uno a uno

| # | Criterio | Estado | Evidencia |
| --- | --- | --- | --- |
| 1 | Un `401` en cualquier operación autenticada limpia la sesión persistida y devuelve al operador al acceso, sin token muerto en `localStorage` | Cumplido (JUP-085, reafirmado) | `fetchJson` (`api.ts:105-108`) invalida con motivo `"expired"`; `SessionGate` limpia `SESSION_KEY`/`TENANT_KEY` y ambas cachés (`SessionGate.tsx:89-97`) |
| 2 | El operador ve un mensaje que identifica la expiración de sesión, distinguible de "el backend no responde" | **Implementado en esta tarjeta** | `LoginPage.tsx`: región `role="status"`, texto exacto "Your session has expired. Sign in again to continue."; `tests/login-session-expired-notice.test.tsx` (9 tests) |
| 3 | Un fallo que no sea `401` (`500`, red, `503`) conserva el comportamiento actual | Cumplido (JUP-085, reafirmado) | `tests/login-session-expired-notice.test.tsx` tarea 4.5 (`403`/`503`/red nunca muestran el aviso ni cierran sesión) |
| 4 | La distinción vive en la capa de acceso centralizada, no repetida en cada pantalla | Cumplido | Único punto de detección: `fetchJson`; el motivo tipado (`SessionInvalidationReason`) viaja por el mismo canal centralizado (`invalidateSession`/`subscribeSessionInvalidation`) hasta `LoginPage` |
| 5 | Pruebas de expiración en vuelo sobre `/overview-legacy` y sobre una pantalla con mutación pendiente, ambas Red antes de Green | Cumplido en esta tarjeta | Tareas 4.1 (`/overview-legacy`, `GET /billing/summary` → `401`) y 4.2 (ingesta, `POST /jobs/ingest` → `401`); Red demostrado en commit `32db55c`, Green en `27f5cd7` |
| 6 | Se decide y se registra si el `403` de tenant recibe el mismo trato que el `401` o uno propio | Decidido: **trato distinto**, conserva la sesión | `design.md` decisión 4; reafirma sin cambios la política ya especificada por JUP-085 |
| 7 | Cobertura de mutación sobre lo tocado por encima del umbral 80 | Cumplido sobre lo tocado (corregido tras la revisión del PR #50) | Ver sección de mutación abajo: todos los mutantes de Stryker en código tocado muertos o justificados como equivalentes; la revisión encontró un mutante escrito a mano que sobrevivía, ya cubierto |
| 8 | Ningún archivo de `apps/backend` en el diff de la rama | Cumplido | `git diff develop...HEAD --stat -- apps/backend/` → vacío (tarea 5.4) |

## Decisiones

Las 5 decisiones del `design.md` (motivo tipado con valor neutro por defecto; el motivo viaja como
estado de navegación consumido una sola vez, sustituyendo la entrada del historial; cuenta como
expiración el `401` dentro y fuera de `/me`; el `403` de tenant conserva la sesión; presentación con
`role="status"` oculta al reintentar) — todas aprobadas en el bloque `Human Approval` de
`proposal.md` (`Approval type: pre-code`, Victor, 2026-09-27) junto con la reducción de alcance
frente al texto original de la tarjeta Trello (JUP-085 ya cumplía los criterios 1, 3, 4, 5 y 6).
Ejecutadas tal cual: ningún desvío de lo aprobado durante el `apply`.

## Validación ejecutada

### Tests (Vitest, `apps/frontend`)

Progresión por grupo (conteos acumulados al cierre de cada uno):

| Momento | Archivos | Tests |
| --- | --- | --- |
| Línea base (heredado de JUP-085/097, antes de esta tarjeta) | 39 | 235 |
| Tras grupo 2 (motivo tipado en `invalidateSession`) | 41 | 241 |
| Tras grupo 3 (propagación desde `SessionGate`) | 43 | 250 |
| Tras grupo 4 (aviso en `LoginPage`) | 45 | 260 |
| **Final (tras la revisión del PR #50: test nuevo del intento pendiente, test 3.1 reescrito)** | **46** | **261** |

Comando: `corepack pnpm vitest run` desde `apps/frontend` (equivalente a
`pnpm --filter @finops/frontend test`, sustituto de `pnpm test` por `RF-093-001`).

**Nota de entorno, no de producto:** a partir del grupo 3, la corrida con el paralelismo por defecto
de Vitest empezó a producir timeouts intermitentes en archivos no relacionados con los cambios
(`tenant-switching.test.tsx`, `ingestion.test.tsx`, `conversations.test.tsx`), por contención de
recursos de esta máquina (memoria libre observada ~2 GB de 16 GB). Reproducido y descartado como
regresión: los mismos archivos pasan limpio en aislamiento y con concurrencia reducida
(`--poolOptions.threads.maxThreads=2`, luego `=1` a partir del grupo 4, cuando `=2` también empezó a
ser intermitente). Detalle completo en `review.md`, grupos 3-5.

**Corrección tras la revisión del PR #50:** no todos los fallos intermitentes eran ambientales. El
test 3.1 de `session-expiry-notice.test.tsx` tenía una carrera real: leía la marca del historial en
`/login` justo cuando `LoginPage` (grupo 4) la borra a propósito. La carga solo la destapaba.
Reescrito para comprobar el aviso visible; 5/5 seguidas. Detalle en `review.md`, sección
"Correcciones tras la revisión del PR #50".

### Mutación (Stryker, acotada por archivo)

| Archivo mutado | Score del archivo completo | Supervivientes en código tocado | Remediación |
| --- | --- | --- | --- |
| `services/api.ts` (grupo 2) | 88.99% (11 supervivientes + 1 sin cobertura) | 2 (línea 37 y 50) | 1 mutante equivalente (dirección del incremento de generación, solo se compara con `!==`); 1 gap real remediado (`api.session-generation-advance.test.ts`) |
| `layouts/SessionGate.tsx` (grupo 3) | 77.93% (44 supervivientes + 3 timeout + 5 sin cobertura) | 1 (línea 86) | 1 gap real remediado (`session-expiry-notice.fresh-mount.test.tsx`, valor inicial de `sessionExpired`) |
| `pages/LoginPage.tsx` (grupo 4) | 77.08% (11 supervivientes + 2 timeout) | 3 (líneas 57-58) | 1 mutante equivalente (array de dependencias, `navigate` estable); 2 gaps reales remediados (`login-session-expired-notice.history-replace.test.tsx`, `replace: true` en la corrección de historial) |

En los tres archivos, el score global queda por debajo del umbral 80 (criterio de lectura del
resultado: la invocación de Stryker sin archivo de configuración, ver el `review.md` archivado, no
tiene opción de corte automático) **solo por deuda preexistente de JUP-085/097 fuera del código que
esta tarjeta modificó** (código no tocado por las tareas 2.3/3.3/4.6: `fetchJson`, `isSession`,
`loadStoredSession`, el bootstrap de tenants, la reconciliación de identidad, el callback `onSuccess`
del login, etc.), explícitamente fuera de alcance por `proposal.md` ("no se reimplementa nada de
JUP-085"). Sobre lo realmente tocado por esta tarjeta, **todos los mutantes que genera Stryker**
están muertos o justificados (4 gaps reales remediados con tests nuevos, 2 mutantes equivalentes).
Deuda registrada en `openspec/findings/backlog.md` (`RF-098-001`), decisión confirmada con el usuario.

**Corrección tras la revisión del PR #50:** esta evidencia afirmaba "100% de los mutantes no
equivalentes". Era cierto solo para los operadores de Stryker, que sustituyen expresiones por
`true`/`false`/negación. La revisora escribió a mano un mutante plausible (`mutation.isIdle` →
`!mutation.isError` en `LoginPage.tsx`) que sobrevivía: el aviso seguía visible durante
"Signing in...", contra el requisito "SHALL disappear once a new sign-in attempt starts". Cubierto con
`tests/login-session-expired-notice.pending-attempt.test.tsx`, que falla con ese mutante.

### Type-check y lint

`corepack pnpm --filter @finops/frontend typecheck` (3 configs: app, node, test) y
`... lint` (`eslint src tests`) — limpios en cada checkpoint de commit de la tarjeta (grupos 2-4),
confirmados de nuevo al cierre (grupo 5).

### Build

`corepack pnpm --filter @finops/frontend build` (Vite 5) — `built in 6.00s`, bundle `768.08 kB` JS /
gzip `217.20 kB`, CSS `39.72 kB` / gzip `7.88 kB`. El aviso de chunk >500kB es preexistente a esta
tarjeta (no se investiga, fuera de alcance).

### Batería de validación del frontend

Desde la raíz, `corepack pnpm test/lint/typecheck` fallan por `RF-093-001` (preexistente, pendiente
de JUP-102, ajeno a este cambio): pasan por turbo, que resuelve pnpm v11.9.0 en subprocesos pese a
`packageManager: pnpm@9.0.0`. Sustituto verificado en su lugar (mismo criterio que JUP-093/094/095/097):
`corepack pnpm --filter @finops/frontend {test,typecheck,lint,build}`, los cuatro en verde — ver
arriba. La higiene del repositorio (`corepack pnpm jup:cleanup:check`) consta en la sección
siguiente.

### Checks de trazabilidad OpenSpec/Trello

```
corepack pnpm openspec:validate       → 35 passed, 0 failed
corepack pnpm jup:check -- --change jup-098-reconcile-auth-session  → [OK] enlazado con Trello y completo
corepack pnpm jup:cleanup:check       → [OK] 648 archivos sin agentes personales, binarios ni tareas paralelas
corepack pnpm install --frozen-lockfile → Done, sin error (lockfile reproducible)
```

## Pendiente

- Pull request: [#50](https://github.com/EconomiconFinOps/tfm-economicon/pull/50). CI: ver la
  pestaña Checks del PR.
- `RF-098-001` (cobertura de mutación preexistente fuera de alcance) queda `Open`, sin dueño
  asignado, disponible para quien quiera subir la cobertura de `api.ts`/`SessionGate.tsx`/
  `LoginPage.tsx` en conjunto.
- `RF-098-002` (aviso con ~7 s de retraso cuando el único `401` es el de `/me`) y `RF-098-003` (JSON
  crudo del backend en el error de credenciales): observaciones preexistentes de la revisión del PR
  #50, registradas como `Open`.
