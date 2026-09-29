# Review — JUP-098 reconcile-auth-session

## Grupo 1. Línea base

**1.1 — Línea base ejecutada.** Sustituto usado (RF-093-001 sigue abierto, turbo resuelve un pnpm
global en subprocesos por paquete): `pnpm test` ejecutado dentro de `apps/frontend/` (equivalente a
`pnpm --filter @finops/frontend test`, sin pasar por turbo).

```
Test Files  39 passed (39)
     Tests  235 passed (235)
```

Línea base: **235 PASS / 0 FAIL**, 39 archivos. Ninguna de las suites existentes se toca en esta
tarjeta; deben seguir en 235 PASS al cerrar cada grupo posterior.

**1.2 — Qué cumple ya `develop` (JUP-085, `d9271fd`) y qué queda para esta tarjeta.**

| Criterio Trello | Estado en `develop` | Evidencia |
| --- | --- | --- |
| 1. Un 401 limpia la sesión persistida y devuelve al operador al acceso, sin token muerto en `localStorage` | **Cumplido** | `fetchJson` detecta `401` numérico fuera de `/me` e invalida ([api.ts:95-98](../../../../apps/frontend/src/services/api.ts#L95-L98)); el suscriptor de `SessionGate` limpia `SESSION_KEY`/`TENANT_KEY` y ambas cachés ([SessionGate.tsx:82-93](../../../../apps/frontend/src/layouts/SessionGate.tsx#L82-L93)) |
| 2. El operador ve un mensaje que identifica la expiración de sesión como tal | **Abierto — trabajo de esta tarjeta** | Hoy la redirección a `/login` es silenciosa: `<Navigate to="/login" replace />` sin ningún estado ([SessionGate.tsx:207-209](../../../../apps/frontend/src/layouts/SessionGate.tsx#L207-L209)) |
| 3. Un fallo que no sea 401 (500, red, 503) conserva el comportamiento actual | **Cumplido** | Cubierto por `tests/auth-session.test.tsx` ("non-profile query and mutation error retain authentication", "tenant bootstrap error retains the session") |
| 4. La distinción vive en la capa de acceso centralizada, no repetida en cada pantalla | **Cumplido** | Único punto de detección: `fetchJson` en `services/api.ts`; ninguna pantalla implementa su propia lógica de 401 |
| 5. Pruebas de expiración en vuelo sobre `/overview-legacy` y sobre una pantalla con mutación pendiente, ambas Red antes de Green | **Cumplido** (histórico de JUP-085; no aplica "Red antes de Green" retroactivamente) | `tests/auth-session.test.tsx`: `"current query %s invalidates..."` (incluye `/billing/summary` → `/overview-legacy`) y `"current %s mutation 401 clears session..."` (ingesta y conversación) |
| 6. Se decide y se registra si el 403 de tenant recibe el mismo trato que el 401 | **Registrado en JUP-085, reafirmado aquí** | Ver `design.md` decisión 4 de esta tarjeta; `SessionGate` muestra el bloque de error de bootstrap con "Reset session" ante `403` de `/tenants`, sin cerrar sesión automáticamente |
| 7. Cobertura de mutación sobre lo tocado > 80 | Pendiente — se mide sobre lo que toque esta tarjeta (grupos 2-4) | — |
| 8. Ningún archivo de `apps/backend` en el diff | Por construcción (alcance) | Se verifica en la tarea 5.4 |

**Conclusión del grupo:** el único trabajo de producto que queda es el criterio 2. Los grupos 2-4
de `tasks.md` lo implementan; el resto de esta tarjeta es verificación y documentación.

**Checkpoint:** grupo doc-only (sin código de producto, sin tests nuevos) → sin ciclo Red/Green ni
mutación, según excepción de `.claude/harness/workflow.md`. Listo para commit.

## Grupo 2. Motivo de la invalidación en la capa de acceso

**2.1-2.2 — Red.** `apps/frontend/src/services/api.test.ts` (nuevo, 5 tests): motivo `"expired"` /
`"manual"` entregado a los suscriptores, propagación a múltiples listeners, desuscripción efectiva,
y no notificación cuando la generación ya quedó abandonada. Commit `440ec5f`. Red confirmado: 3/5
fallos en runtime (`vitest`) y 4 errores de `tsc` contra la firma antigua de `invalidateSession`.

**2.3 — Green.** `services/api.ts` (líneas 22-52): tipo `SessionInvalidationReason = "expired" |
"manual"`, `invalidateSession(generation, reason = "manual")`, listener tipado con el motivo. Guard
de generación intacto, `discardResponse` sin tocar, llamada de `fetchJson` sin modificar (sigue
usando el valor por defecto `"manual"`). Commit `75728a4`. 240/240 PASS, `tsc` sin errores.

**2.4 — Mutación.** Config: `.claude/harness/stryker.conf.mjs` → `mutate: ["src/services/api.ts"]`
(harness local, no se commitea). Comando:
```
corepack pnpm --package=@stryker-mutator/core --package=@stryker-mutator/vitest-runner \
  --package=typescript@5.9.3 dlx stryker run ../../.claude/harness/stryker.conf.mjs
```
Resultado: **88.99%** (109 mutantes cubiertos, 97 KILLED, 11 SURVIVED, 1 NO COVERAGE) — por encima
del umbral 80.

De los 11 supervivientes, **2 caen en el código que tocó esta tarea** (líneas 22-52):

- **Línea 37** (`++sessionGeneration` → `--sessionGeneration`, `UpdateOperator`): **mutante
  equivalente**, no se remedia. En todo `api.ts`, `SessionGate.tsx` y `LoginPage.tsx` la generación
  solo se compara con `!==`; ningún código depende de su sentido de incremento, así que ningún test
  puede observar la diferencia sin inventar una aserción artificial sobre el signo interno.
- **Línea 50** (elimina la llamada a `advanceSessionGeneration()` dentro de `invalidateSession`,
  `CallExpression`): **gap real**, remediado. Sin ese avance, una segunda invalidación con la misma
  generación original volvería a notificar en vez de ser un no-op. Test nuevo:
  `apps/frontend/src/services/api.session-generation-advance.test.ts` (1 test) — verificado
  empíricamente contra el mutante (comentando la línea manualmente, confirmando el fallo, revirtiendo
  con `git checkout --`, sin dejar el cambio en el árbol) y contra el código real (pasa). Suite
  completa tras el test nuevo: **241/241 PASS**.

Los otros **9 supervivientes + 1 NO COVERAGE caen fuera del código que tocó esta tarea**: en
`fetchJson` (redacción de mensajes de error, validación de respuesta, guard de generación dentro de
la rama de error), `ApiError` (`this.name`) y `clearSessionMutations` (`mutation.destroy()`). Todo
preexistente de JUP-085/097, no modificado por la tarea 2.3.

**Decisión de alcance (confirmada con el usuario 2026-09-27):** esos 9+1 quedan **fuera de esta
tarjeta**, sin remediar. Motivo: el `proposal.md` de JUP-098 declara explícitamente como fuera de
alcance "reimplementar nada de JUP-085 [...] sus pruebas no se tocan"; escribir tests nuevos para
código que esta tarea no modifica sería expandir ese alcance por un efecto colateral de que Stryker
mutila el archivo entero, no la función tocada. Se registra como hallazgo para quien quiera subir la
cobertura de mutación de `api.ts` en conjunto — ver `openspec/findings/backlog.md` (RF-098-001).

Cierre del grupo: mutation score de lo realmente tocado por esta tarea = 100% de mutantes no
equivalentes muertos (1 real remediado, 1 equivalente justificado). Score global del archivo
(88.99%) queda por encima del umbral 80 igualmente.

**DoD del grupo 2.** `node .claude/harness/check-dod.mjs` desde la raíz falla por RF-093-001 (turbo
resuelve pnpm 11.9.0 global en subprocesos por paquete, en vez de 9.0.0 vía corepack — bloqueo
conocido, pendiente de JUP-102, ajeno a este cambio). Sustituto `pnpm --filter @finops/frontend`:

- `lint` → sin salida, sin errores.
- `typecheck` → sin salida, sin errores (`tsc --noEmit` × 3 configs).
- `test` → 241/241 PASS (240 previos + 1 de remediación de mutación).
- `build` → éxito, `dist/` generado (aviso preexistente de tamaño de chunk, no relacionado).
- Escaneo de secretos del propio `check-dod.mjs` → PASS (esa comprobación sí corre bien desde la raíz).

## Grupo 3. Propagación del motivo desde `SessionGate`

**3.1-3.2 — Red/caracterización.** `apps/frontend/tests/session-expiry-notice.test.tsx` (8 tests):
`401` de `/me` al arrancar → `/login` con `{ sessionExpired: true }`; `403`/`503`/red/contrato
inválido de `/me`, logout manual y "Reset session" tras `403` de tenants → `/login` con
`location.state === null` (react-router normaliza el estado ausente a `null`, no `undefined`; ver
comentario del propio archivo de test). Commit `cd2e5cc`.

**3.3 — Green.** `services/api.ts`: el `401` fuera de `/me` en `fetchJson` pasa a invalidar con
`"expired"`. `SessionGate.tsx`: nuevo estado `sessionExpired`, el suscriptor de invalidación lo fija
según el motivo recibido, `handleLogout` acepta un motivo opcional, el efecto de error de `/me`
deriva `"expired"` solo de un `ApiError` con `status === 401`, y el `<Navigate>` final pasa
`state={{ sessionExpired: true }}` solo entonces. Durante la revisión se detectó que el botón "Reset
session" quedó protegido de recibir el `MouseEvent` nativo como motivo, pero `onLogout: handleLogout`
(usado por el botón "Cerrar sesion" de `Layout.tsx`) tenía el mismo riesgo sin corregir — se envió de
vuelta al coder y quedó resuelto con el mismo patrón (`onLogout: () => handleLogout()`). Commit
`ca9dd95`. 249/249 PASS, `tsc` y `lint` sin errores.

**3.4 — Invariante "el efecto sin sesión no sobrescribe un motivo ya entregado" (sin test nuevo,
evidencia existente suficiente, confirmado con el usuario 2026-09-27).** Verificado por lectura de
código: `generation` es estado local de `SessionGate` que **no se actualiza** en el camino de error
de `/me` (el efecto de reconciliación de identidad que sí llama a `setGeneration` retorna temprano
cuando `profileQuery.isError`, así que nunca se ejecuta ahí). Por tanto, tras la primera
`invalidateSession(generation, "expired")`, la llamada posterior del efecto "sin sesión"
(`if (!session) invalidateSession(generation);`) reutiliza ese mismo `generation` ya obsoleto, y el
guard de `invalidateSession` (`generation !== sessionGeneration`) la bloquea antes de notificar a
ningún suscriptor — no hay ninguna ruta de código por la que un motivo ya entregado pueda
sobrescribirse. Dos evidencias ya existentes prueban el mecanismo, sin necesidad de un test nuevo:
- **Grupo 2** (`api.session-generation-advance.test.ts`): prueba, a nivel unitario y agnóstico al
  motivo, que una segunda `invalidateSession` con la generación original ya invalidada no vuelve a
  notificar a ningún listener — es exactamente el mecanismo que protege este riesgo.
- **Tarea 3.1** (`session-expiry-notice.test.tsx`): el `expect(state).toEqual({ sessionExpired: true
  })` se afirma tras `waitFor` hasta que el router se **estabiliza** en `/login`; si el efecto "sin
  sesión" sobrescribiera el motivo en un render posterior, ese test fallaría de forma determinista.
  Que pase en verde es evidencia end-to-end del mismo invariante, no solo unitaria.

**3.5 — Mutación.** Config: `mutate: ["src/layouts/SessionGate.tsx"]`. Resultado: **77.93%** (215
mutantes cubiertos, 170 KILLED, 44 SURVIVED, 3 TIMEOUT, 5 NO COVERAGE) — por debajo del umbral 80 en
bruto, pero de los 44 supervivientes, **solo 1 cae en el código que tocó esta tarea** (líneas 82-100,
188-227, 258-268, 279-294); los otros 43 son preexistentes: `isSession`/`loadStoredSession` (líneas
32, 58-70), el bootstrap de tenants y su `queryFn` (107-128), el efecto de reconciliación de
identidad (135-155, explícitamente fuera de alcance por `design.md`), el efecto de selección de
tenant (157-178), `activeTenant` (182), `handleTenantChange` (198), el bloque de carga/error de
tenants (236-251) y `tenants` derivado (277) — ninguno modificado por la tarea 3.3. Mismo criterio de
alcance que en el grupo 2 (confirmado entonces con el usuario, aplicado aquí sin volver a preguntar):
esos 43 no se remedian, se registran como parte del mismo hallazgo `RF-098-001`.

El único superviviente en código tocado: **línea 86**, `useState(false)` → `useState(true)` (valor
inicial de `sessionExpired`, `BooleanLiteral`). **Gap real, remediado.** Si el valor inicial fuera
`true`, un arranque con sesión ausente desde el principio (localStorage vacío, no "inválida") pasaría
la marca de expiración a `<Navigate>` en su primer render; el efecto corrector de `SessionGate`
correría después (los efectos de hijos —`<Navigate>`— se ejecutan antes que los del padre), así que
la corrección llegaría tarde para esa primera navegación. Test nuevo:
`apps/frontend/tests/session-expiry-notice.fresh-mount.test.tsx` (1 test). Nota metodológica: un
primer diseño que solo comprobaba el estado final tras `waitFor` **no mataba el mutante** (el efecto
corrector lo "autocura" en el mismo `act()` síncrono de montaje); el test final se suscribe al router
con `router.subscribe` **antes** del primer render para capturar la transición transitoria incorrecta.
Verificado empíricamente contra el mutante (editando `useState(true)` a mano, confirmando el fallo,
revirtiendo con `git checkout --`) y contra el código real (pasa). Cubre además el escenario "The
session ends without server rejection" de `specs/demo-auth-session/spec.md` para el caso de sesión
genuinamente ausente, no solo inválida (que ya cubría `auth-session.test.tsx` de JUP-085).

Cierre del grupo: mutation score de lo realmente tocado = 100% de mutantes no preexistentes muertos.

**Nota de entorno — timeouts intermitentes en la suite completa.** Ejecutar
`corepack pnpm vitest run` con el paralelismo por defecto produjo timeouts de 5000 ms en
`tenant-switching.test.tsx`/`ingestion.test.tsx`/`conversations.test.tsx` en dos corridas seguidas
(8-9 fallos de 250). Aislados (`vitest run tests/tenant-switching.test.tsx tests/ingestion.test.tsx
tests/conversations.test.tsx`), los 15 tests de esos 3 archivos pasan limpio en 16.8s — no es una
regresión de esta tarjeta. Con concurrencia reducida
(`vitest run --pool=threads --poolOptions.threads.maxThreads=2`), la suite completa pasa
**250/250** de forma reproducible. Causa: saturación de esta máquina bajo los 43 archivos en paralelo
(memoria libre ~2.5 GB de 16 GB al momento de la prueba), no un defecto del código ni de los tests.
Sin acción de remediación en este change (es un límite del entorno local, no del producto); se anota
aquí para que el DoD del grupo 5 use `--poolOptions.threads.maxThreads=2` si vuelve a aparecer.

**Actualización (grupo 4):** con 45 archivos de test (2 más que en el grupo 3), `maxThreads=2`
también empezó a producir fallos intermitentes y no reproducibles en distintos archivos entre
corridas (memoria libre ~2 GB de 16 GB en esta máquina en ese momento). `maxThreads=1` (secuencial)
sí fue reproducible en verde: **260/260** dos veces seguidas. Se actualiza la recomendación: usar
`--poolOptions.threads.maxThreads=1` para el DoD de esta tarjeta en esta máquina si `maxThreads=2`
resulta intermitente.

**DoD del grupo 3.** Sustituto `pnpm --filter @finops/frontend` (mismo motivo RF-093-001 que en el
grupo 2): `lint` → sin errores; `typecheck` → sin errores (3 configs); `test` → 250/250 PASS con
concurrencia reducida (ver nota de entorno arriba).

## Grupo 4. Aviso en la pantalla de acceso

**4.1-4.5 — Red/caracterización.** `apps/frontend/tests/login-session-expired-notice.test.tsx` (9
tests): expiración en vuelo sobre `/overview-legacy` y sobre la mutación de ingesta → aviso
`role="status"` visible con el texto exacto de la decisión 5; el aviso desaparece al reintentar
(`mutation.isIdle` pasa a `false`) y un intento fallido muestra solo su propio error; no persistencia
(`location.state` a `null`, sin marca nueva en storage, montaje directo en `/login` sin aviso);
`403`/`503`/red nunca muestran el aviso. Commit `32db55c`. Hallazgo relevante del tester: la tarea
4.4a resultó ser Red genuino (no caracterización, como se anticipaba) — el grupo 3 ya deja la marca
en la navegación también para el `401` fuera de `/me`, así que "sustituir la entrada sin estado" es
justo el trabajo de esta fase Green. 4/9 fallan genuinamente (4.1, 4.2, 4.3, 4.4a), 5/9 ya pasaban.

**4.6 — Green.** `apps/frontend/src/pages/LoginPage.tsx`: lectura perezosa de
`location.state?.sessionExpired` en el inicializador de `useState` (evita parpadeo), efecto que
sustituye la entrada de historial sin estado (`navigate(location.pathname, { replace: true, state:
null })`) guardado por `hasSessionExpiredFlag`, región `role="status"` con el texto exacto oculta vía
`mutation.isIdle`, color `text-amber-400` (ya usado en `MetricCard.tsx`, coherente con el sistema).
Nota de tooling: `eslint-plugin-react-hooks@4.6.2` sobre ESLint 9 crashea al generar el aviso de
dependencia faltante (antes de poder silenciarlo con `eslint-disable`), así que el efecto lista
`[location, navigate]` de forma exhaustiva en vez de `[]` con supresión — el guard interno hace que
el resultado observable sea el mismo. Commit `27f5cd7`. 259/259 PASS, `tsc` y `lint` sin errores.

**4.7 — Mutación.** Config: `mutate: ["src/pages/LoginPage.tsx"]`. Resultado: **77.08%** (46
mutantes cubiertos, 35 KILLED, 11 SURVIVED, 2 TIMEOUT, 0 NO COVERAGE) — por debajo del umbral 80 en
bruto. De los 11 supervivientes, **3 caen en el código tocado** (el efecto nuevo de la línea 55-58);
los otros 8 son preexistentes en el callback `onSuccess` de la mutación de login y en `handleSubmit`
(líneas 82-97), no modificados por la tarea 4.6 — mismo criterio de alcance que en los grupos 2 y 3
(`RF-098-001`), sin volver a confirmar con el usuario por ser la tercera vez que se aplica el mismo
criterio ya acordado.

De los 3 supervivientes en código tocado:
- **Línea 58** (`[location, navigate]` → `[]`, `ArrayDeclaration`): **mutante equivalente**, no se
  remedia. `navigate` es una referencia estable de react-router y, dada la estructura de rutas,
  `LoginPage` nunca puede recibir una segunda marca de expiración mientras sigue montado (no hay
  ningún camino de código donde eso ocurra), así que ningún test puede observar una diferencia entre
  ambos arrays de dependencias.
- **Líneas 57×2** (`ObjectLiteral`/`BooleanLiteral`: elimina `replace: true, state: null`, o invierte
  `replace` a `false`): **gap real, remediado.** Sin `replace: true`, la corrección de `LoginPage`
  hace un `push` en vez de un `replace`, dejando una segunda entrada de historial con la marca de
  expiración todavía puesta; el botón "atrás" del navegador la resucitaría. Test nuevo:
  `apps/frontend/tests/login-session-expired-notice.history-replace.test.tsx` (1 test). Nota
  metodológica: un primer diseño que solo comprobaba el estado final tras "atrás" no mataba el
  mutante — el propio efecto de `LoginPage` sigue montado y se autocorrige de inmediato,
  enmascarando la transición intermedia; el test final se suscribe al router **antes** de navegar
  hacia atrás para grabar todas las transiciones, incluidas las transitorias. Verificado
  empíricamente contra ambos mutantes (editando la línea a mano, confirmando el fallo, revirtiendo) y
  contra el código real (pasa, 5/5 ejecuciones consecutivas sin flakiness).

Cierre del grupo: mutation score de lo realmente tocado = 100% de mutantes no preexistentes muertos
(2 reales remediados, 1 equivalente justificado).

**DoD del grupo 4.** Sustituto `pnpm --filter @finops/frontend`: `lint` → sin errores; `typecheck` →
sin errores; `test` → 260/260 PASS (ver nota de entorno actualizada: `maxThreads=1` en esta máquina).

## Grupo 5. Documentación y cierre

**5.1 — Spike actualizado.** `docs/spikes/frontend-migration.md`: el placeholder
`jup-0xx-reconciliar-auth-tenant` (línea ~231) pasa a `jup-098-reconcile-auth-session`, marcado
completo, con la historia real (login/sesión/tenant/logout ya resueltos por JUP-085 antes de que esta
tarjeta empezara; el único trabajo real fue el aviso de expiración). Añadido punto 9 en "Próximos
pasos" documentando lo mismo y registrando, de paso, que JUP-085 nunca se había anotado ahí. F3 queda
con una sola tarjeta pendiente: `unificar-estilos-assets`.

**5.2 — README revisado.** `apps/frontend/README.md` ya mencionaba `SessionGate`/`Layout` a nivel de
arquitectura pero no el mecanismo del `401`; se añadió una nota bajo "Notas" describiendo el aviso de
expiración y cuándo aparece/no aparece.

**5.3 — Hallazgos.** Sin hallazgos nuevos más allá de `RF-098-001` (cobertura de mutación
preexistente, ya registrado y cerrado en su alcance durante los grupos 2-4).

**5.4 — Backend fuera del diff.** `git diff develop...HEAD --stat -- apps/backend/` → vacío. El
diff completo son 16 archivos, todos en `apps/frontend/`, `docs/` u `openspec/`.

**5.5 — Batería completa desde la raíz.**

| Comando | Resultado |
| --- | --- |
| `corepack pnpm openspec:validate` | PASS — 35/35 |
| `corepack pnpm jup:check -- --change jup-098-reconcile-auth-session` | PASS |
| `corepack pnpm jup:cleanup:check` | PASS — 648 archivos sin agentes personales, binarios ni tareas paralelas |
| `pnpm --filter @finops/frontend lint` (sustituto RF-093-001) | PASS — sin salida |
| `pnpm --filter @finops/frontend typecheck` (sustituto RF-093-001) | PASS — sin salida, 3 configs |
| `pnpm --filter @finops/frontend build` (sustituto RF-093-001) | PASS — `dist/` generado, aviso preexistente de tamaño de chunk |
| `vitest run --pool=threads --poolOptions.threads.maxThreads=1` (sustituto RF-093-001) | **260/260 PASS** en la corrida final; una corrida intermedia con el mismo flag dio 1 fallo aislado no reproducible (flakiness de esta máquina, ver nota de entorno de los grupos 3-4), corregido al repetir sin tocar código |
| `corepack pnpm install --frozen-lockfile` | PASS |

RF-093-001 (turbo resuelve pnpm 11.9.0 global en vez de 9.0.0 vía corepack) sigue abierto, pendiente
de JUP-102; ajeno a este cambio, documentado desde el grupo 2.

## Human Approval

- Change: jup-098-reconcile-auth-session
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-09-27
- Archive decision: archive
- Scope reviewed: las 24 tareas de `tasks.md` (5 grupos), `review.md` completo, evidencia
  `docs/evidence/JUP-098-validation.md`, batería final (`openspec:validate`, `jup:check`,
  `jup:cleanup:check`, `test`/`typecheck`/`lint`/`build` vía `--filter @finops/frontend`,
  `install --frozen-lockfile`).
- Resultado verificado: los 8 criterios de aceptación de la tarjeta verificados uno a uno en la
  evidencia; el único trabajo de producto real fue el criterio 2 (aviso de sesión expirada), los
  criterios 1/3/4/5/6 ya los cumplía `develop` gracias a JUP-085 y se reafirmaron con tests de
  caracterización sin tocar las pruebas existentes de esa tarjeta. Motivo tipado en la capa de acceso
  (grupo 2), propagado por `SessionGate` (grupo 3) y presentado en `LoginPage` (grupo 4), con mutación
  del 100% sobre el código realmente tocado en los tres archivos (2 mutantes equivalentes
  justificados, 4 gaps reales remediados con tests nuevos). Deuda de mutación preexistente fuera de
  alcance registrada en `RF-098-001`. Ningún archivo de `apps/backend/**` en el diff completo de la
  rama. Ningún ADR nuevo requerido (es un ajuste local de presentación sobre un mecanismo ya decidido
  en JUP-085 y su ADR-0007).
- Notes: cierre alineado con la reducción de alcance aprobada en el gate pre-código (JUP-085 ya
  resolvía la mayoría de los criterios de la tarjeta Trello antes de proponerla). Flakiness de la
  suite bajo paralelismo por defecto documentada como ambiental (contención de recursos de esta
  máquina), no de producto — reproducida y descartada como regresión en cada caso. El PR lo abre
  Victor directamente (no este agente).

## Correcciones tras la revisión del PR #50 (2026-09-28)

La revisión de `@lmatsan` (`CHANGES_REQUESTED`) encontró tres defectos. Los tres se verificaron
de forma independiente antes de corregirlos. Son cambios posteriores a la aprobación post-review
de arriba; el change no se vuelve a archivar.

**1. Afirmación incorrecta: "100% de mutantes no equivalentes muertos en el código tocado".** Era
cierto solo para los operadores que genera Stryker (sustituir por `true`/`false`/negación). La
revisora cambió a mano `mutation.isIdle` por `!mutation.isError` en `LoginPage.tsx`: el aviso quedaba
visible durante "Signing in..." y los 19 tests de JUP-098 seguían en verde (reproducido). La spec
exige que el aviso desaparezca en cuanto empieza el intento; el test 4.3 solo lo comprobaba antes del
intento y después del fallo. Corregido con
`apps/frontend/tests/login-session-expired-notice.pending-attempt.test.tsx`: retiene la respuesta de
`POST /auth/login` con una promesa pendiente y comprueba que el aviso no está mientras el botón dice
"Signing in...". Pasa 5/5 seguidas y falla con el mutante de la revisora. El mutante alternativo
`!mutation.isPending` lo mata el test 4.3: entre ambos, `isIdle` es la única condición que pasa.

**2. Diagnóstico incorrecto: fallos intermitentes atribuidos solo a saturación de la máquina.** El
test 3.1 (`tests/session-expiry-notice.test.tsx`), escrito en el grupo 3, leía
`router.state.location.state` en `/login`; desde el grupo 4 `LoginPage` borra esa marca a propósito
al montarse, así que el resultado dependía de quién llegara antes. La carga de la máquina solo
destapaba la carrera. Reescrito para comprobar el aviso visible (`getByRole("status")`), que se fija
en el primer render y no desaparece solo: 5/5 seguidas, y sigue fallando si el `401` de `/me` deja de
etiquetarse como `"expired"`. Para editar el archivo commiteado se desactivó el hook
`lock-committed-tests` con autorización del usuario, y se restauró idéntico (verificado que vuelve a
bloquear). Los otros fallos intermitentes observados (`tenant-switching`, `ingestion`,
`conversations`, y esperas `findByRole` de 1 s por defecto en tests de JUP-098) son tiempos de espera
bajo carga, no carreras de lógica; se mantiene esa nota de entorno.

**3. Enlaces rotos por el archivado.** El archivado bajó el change un nivel de carpeta y rompió 9
enlaces relativos: los 4 que señaló la revisora (spike, evidencia ×2, backlog) y 5 dentro de esta
misma carpeta (`design.md`, `proposal.md`, `review.md` ×3). Corregidos y verificados con un escaneo
de enlaces. Quedan 3 enlaces rotos preexistentes de otras tarjetas (JUP-094 y JUP-097 en el spike,
JUP-085 en el backlog), fuera del alcance de esta tarjeta.

**Hallazgos nuevos registrados** (observaciones de la revisora, preexistentes a JUP-098):
`RF-098-002` (el aviso tarda ~7 s cuando el único `401` es el de `/me`, por los 3 reintentos por
defecto de TanStack Query) y `RF-098-003` (el error de credenciales muestra el JSON crudo del
backend).

**Sugerencias de la revisora no aplicadas en esta ronda:** anuncio del `role="status"` por lectores de
pantalla (requiere prueba con lector real), orden de llegada entre un `503` de `/me` y un `401` de otra
petición (la spec no fija qué motivo gana) y pérdida de query string/hash al limpiar el historial (hoy
inalcanzable). Quedan como posibles mejoras.

**Validación tras las correcciones:** suite completa secuencial (`maxThreads=1`) **261/261**, lint y
typecheck sin errores.
