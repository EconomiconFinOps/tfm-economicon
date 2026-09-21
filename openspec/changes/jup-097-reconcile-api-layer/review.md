JUP: JUP-097
Trello: https://trello.com/c/dsBZ7y0S/89-jup-097-reconciliar-la-capa-de-datos-del-frontend-con-los-contratos-del-backend
Rama: `feat/JUP-097-reconcile-api-layer`

Documento vivo: se actualiza al cerrar cada grupo de `tasks.md`, no solo al final de la tarjeta.

## Grupo 1 — Auditoría de contratos

Doc-only en su mayor parte (investigación + verificación), sin código de producto propio: sin
tester/coder/mutación para este grupo (excepción documentada en `.claude/harness/mutation.md`). Las
correcciones que la auditoría exija, si las hay, van al ciclo Red/Green del grupo 2.

### 1.1 — Backend levantado y `/health` confirmado

`docker compose up -d --wait backend` (con dependencias `cockroachdb`, `rabbitmq`,
`postgres-pgvector`), `.env` local aislado y desechable (`RUNTIME_ENVIRONMENT=development`,
`ALLOW_INSECURE_LOCAL_DATABASE=true`, `DEMO_SEED_ENABLED=true`, DSN local aprobado del README).

Dos incidencias puramente operativas de mi entorno de pruebas, ninguna es un hallazgo de la
tarjeta ni cambia el alcance:

1. **Credencial demo heredada.** El volumen `tfm-economicon_cockroach-data` es persistente de una
   sesión anterior (verificación manual E2E de JUP-095, `RF-095-001`) y ya tenía
   `operator@example.com` con la password legacy `secret` documentada en el spike. El backend
   bloqueó el arranque a propósito (`DemoRotationRequired`, `app/core/runtime_secrets.py`) exigiendo
   rotación explícita — protección de seguridad real, funcionando como se documenta en
   `docs/manuals/python-service-conventions.md#rotacion-de-la-cuenta-demo`. Resuelto rotando la
   password del usuario `user-finops-admin` con el procedimiento oficial (adaptado a modo no
   interactivo, password generada con `secrets.token_urlsafe`, transportada solo por variable de
   entorno, nunca impresa ni versionada); confirmado con login real (`200`, token válido). Decisión
   consultada y aprobada por Victor antes de ejecutar (frente a la alternativa de borrar el volumen).
2. **`VECTOR_DATABASE_URL` con dialecto y password incorrectos.** Mi DSN inicial usaba
   `postgresql://` (dialecto `psycopg2`, no instalado; el backend trae `psycopg` v3) y una password
   que no coincidía con la que ya tenía el volumen `pgvector-data` de una sesión anterior (Postgres
   solo aplica `POSTGRES_PASSWORD` en la inicialización del volumen, no en arranques posteriores —
   documentado en el mismo manual). Corregido el DSN a `postgresql+psycopg://` y alineada la
   password con `ALTER USER postgres WITH PASSWORD ...` vía el socket local (`trust`) del propio
   contenedor.

`GET /health` confirmado: `{"status":"ok","services":{"database":"ok","rabbitmq":"ok","vector_store":"ok"}}`
(`HTTP 200`).

### 1.2 — Referencia real de contratos (lectura de código)

Extraída de `apps/backend/app/api/routes/*.py` y `apps/backend/app/schemas/*.py`. **Son 10 endpoints,
no 9** como decían el spike y, arrastrado de él, los propios `proposal.md`/`design.md`/`tasks.md` de
esta tarjeta antes de esta auditoría (corregido en los tres tras confirmarlo aquí; el README de
`apps/frontend` ya los listaba bien, 10, sin necesitar corrección — tarea 1.6/2.4).

| # | Método | Ruta | Auth | Response model |
| - | - | - | - | - |
| 1 | GET | `/health` | ninguna | `HealthResponse` |
| 2 | POST | `/auth/login` | ninguna (body `LoginRequest`) | `LoginResponse` |
| 3 | GET | `/me` | Bearer | `UserProfile` |
| 4 | GET | `/tenants` | Bearer | `TenantCollection` |
| 5 | GET | `/billing/summary` | Bearer + X-Tenant-Id | `BillingSummary` |
| 6 | POST | `/jobs/ingest` | Bearer + X-Tenant-Id (body `IngestJobRequest`) | `IngestJobResponse` (202) |
| 7 | GET | `/assistant/conversations` | Bearer + X-Tenant-Id | `ConversationCollection` |
| 8 | POST | `/assistant/conversations` | Bearer + X-Tenant-Id (body `ConversationCreateRequest`) | `ConversationRecord` (201) |
| 9 | GET | `/assistant/conversations/{id}` | Bearer + X-Tenant-Id | `ConversationDetail` |
| 10 | POST | `/assistant/conversations/{id}/messages` | Bearer + X-Tenant-Id (body `MessageCreateRequest`) | `AssistantReply` (201) |

`X-Tenant-Id` se valida contra `user_has_tenant` (`app/api/dependencies.py:get_active_tenant`): 403
si el tenant no pertenece al usuario, 400 si falta la cabecera.

### 1.3 — Comparación código a código (`services/api.ts` vs. referencia real)

Las 10 funciones exportadas de `api.ts` (`fetchHealth`, `fetchProfile`, `fetchTenants`,
`fetchBillingSummary`, `login`, `createIngestJob`, `listConversations`, `createConversation`,
`getConversation`, `sendConversationMessage`) coinciden exactamente con la tabla anterior en ruta,
método y transporte de `Authorization`/`X-Tenant-Id`. **Cero desviaciones** por lectura de código.

`services/contracts.ts` comparado campo a campo contra los 10 `response_model`/schemas de request
del backend (incluida `BillingSummary.currency`, que sí está presente en ambos lados). **Cero
desviaciones de forma** por lectura de código — resultado que la decisión 1 del `design.md` ya
advertía como insuficiente por sí solo, de ahí la tarea 1.4.

### 1.4 — Verificación contra el backend en ejecución (fuera del navegador)

Las 10 operaciones probadas con `curl` (sin CORS: `RF-095-001` no aplica a este método, decisión 5
del diseño) contra el backend real, con el seed local. Nota de desviación respecto al seed que
documentaba el spike: la password real usada fue la rotada en 1.1, no `secret` — es la contraseña
que ahora protege esa cuenta en este volumen local, coherente con lo hecho en esa tarea.

| Operación | Resultado | Forma de respuesta |
| - | - | - |
| `fetchHealth` | 200 | Coincide con `HealthResponse` |
| `login` | 200 | Coincide con `LoginResponse` (incluye `UserProfile` completo) |
| `fetchProfile` | 200 | Coincide con `UserProfile` |
| `fetchTenants` | 200, 2 tenants (`tenant-core`, `tenant-growth`) | Coincide con `TenantCollection` |
| `fetchBillingSummary` | 200 | Coincide con `BillingSummary`, incluido `currency` |
| `createIngestJob` | 202 | Coincide con `IngestJobResponse` |
| `listConversations` | 200 (vacío antes de crear) | Coincide con `ConversationCollection` |
| `createConversation` | 201 | Coincide con `ConversationRecord` |
| `getConversation` | 200 | Coincide con `ConversationDetail` |
| `sendConversationMessage` | 201 tras resolver incidencia (ver abajo) | Coincide con `AssistantReply`, incluido `retrieved_context` |

**Incidencia operativa en `sendConversationMessage` (no es desviación de contrato):** primer intento
devolvió `500` (`ProgrammingError` en logs estructurados). Investigado: las migraciones del esquema
de `pgvector` (`knowledge_documents`, `document_chunks`, `chunk_embeddings`) las corre `processor`
(`apps/processor/app/vector_store/migrations/`), no `backend`, y no había levantado ese servicio
para esta auditoría. Backend solo consulta (`app/services/vector_store.py` es query-only). Levantado
`processor` (+ su dependencia `azure-cost-api`), confirmadas las 4 tablas creadas, reintentada la
llamada: `201`, forma correcta. No se registra como finding porque no es una desviación entre
frontend y backend — es un servicio de la topología que faltaba levantar en mi propio entorno de
prueba.

**Conclusión del grupo 1: cero desviaciones de contrato**, ni por lectura de código ni por
verificación contra el backend en ejecución. Único hallazgo real: el error de conteo "9→10" ya
corregido en los tres documentos de planificación de esta tarjeta.

### 1.5 — Consolidación

Ver tablas de 1.2/1.3/1.4 arriba. Resultado consolidado: **10/10 operaciones correctas**, sin
corrección de código pendiente para el grupo 2 (que queda cerrado explícitamente sin cambios de
`api.ts`/`contracts.ts` más allá de lo que exija RF-090-003 en el grupo 3, que es una conexión
nueva, no una corrección de desviación).

### 1.6 — Contraste con `apps/frontend/README.md`

`apps/frontend/README.md` sección "Contratos Esperados Del Backend" (líneas 152-162) ya lista los
10 endpoints correctamente, sin el error de conteo de los documentos de planificación. **Sin cambios
necesarios** en el README.

## Grupo 2 — Corrección de las desviaciones encontradas

**Doc-only: grupo cerrado sin código de producto**, excepción documentada aquí (equivalente a
`.claude/harness/mutation.md` para el caso "no hay nada que corregir"). El grupo 1 concluyó con
**cero desviaciones de contrato** en las 10 operaciones, tanto por lectura de código como por
verificación contra el backend real. En consecuencia:

- **2.1/2.2 (Red/Green):** no aplican. No existe ninguna operación desviada de 1.3/1.4 sobre la que
  escribir una prueba que fije "la forma correcta" — la forma ya vigente en `api.ts`/`contracts.ts`
  es la correcta, confirmada contra el backend en ejecución. Escribir una prueba aquí sería fijar un
  comportamiento que nadie cambió, sin relación con ningún defecto encontrado.
- **2.3:** no aplica. Sin desviaciones, no hay nada que registrar como finding de contrato — y en
  particular ningún finding nuevo sobre `apps/backend/**`, coherente con el criterio de aceptación 8
  (ningún archivo de backend en el diff de la rama).
- **2.4:** ya resuelto en 1.6 (grupo 1): el README ya listaba los 10 endpoints correctamente y no
  requería corrección.
- **2.5:** esta misma nota es la constancia explícita que pide la tarea, en vez de marcar el grupo
  sin explicación.

Commit pendiente de este grupo tras revisión del usuario.

## Grupo 3 — `RF-090-003`: conectar `fetchProfile`

Ciclo Red/Green/mutación/DoD/QA completo (primera tarea con código de producto real de esta
tarjeta). Ver decisión 2 de `design.md` para la justificación completa.

**Red** (tester): `apps/frontend/src/layouts/SessionGate.profile.test.tsx`, 2 tests —
"expone la identidad devuelta por el servidor, no la guardada en localStorage" (tarea 3.1) y
"limpia la sesion y redirige al acceso cuando /me rechaza el token" (tarea 3.2). Confirmado Red por
el motivo correcto: `SessionGate` no invocaba `fetchProfile`, así que ambos tests fallaban por
aserción/timeout, no por error de módulo. Los 4 tests ya existentes de `SessionGate.test.tsx` y
`SessionGate.validation.test.tsx` seguían intactos.

**Green** (coder): `apps/frontend/src/layouts/SessionGate.tsx` — añadido `profileQuery` (mismo
`enabled: Boolean(session?.accessToken)` que `tenantsQuery`, para que ambas se emitan en paralelo al
arrancar, tarea 3.4) y un `useEffect` que llama a `handleLogout()` (envuelto en `useCallback` sin
cambio de comportamiento, ver comentario en el propio archivo sobre un bug de
`eslint-plugin-react-hooks@4.6.2` con ESLint 9) cuando `profileQuery.isError`. El contexto expuesto
pasa de `user: session.user` a `user: profileQuery.data`. El bloque de carga existente se amplía con
`profileQuery.isLoading || profileQuery.isError` para no dejar pasar un frame con `user` a medio
limpiar. Frontera de la decisión 2 respetada íntegramente: sin tocar login, `isSession`,
`loadStoredSession`, guard de rutas ni semántica de logout — confirmado en la revisión QA con
`git diff` línea por línea.

**Incidencia real durante Green, escalada correctamente (no improvisada):** conectar `/me` rompió 26
tests en 4 suites de integración (`tests/{session-and-dashboard,conversations,ingestion,
tenant-switching}.test.tsx`) que usan el fixture compartido `mockBackend()`
(`apps/frontend/tests/test-support.tsx`), cuyas rutas por defecto no incluían `GET /me`. El coder
detectó la causa exacta pero **no la tocó** (fixture de test, fuera de su rol) y escaló el bloqueo tal
como exige la tarea 3.7. Resuelto por el tester ampliando `mockBackend()` con
`"GET /me": () => jsonResponse(operator)` (mismo `UserProfile` que ya usaba `session.user`, así que
ninguna de las 26 aserciones necesitó cambiar) — más una segunda ronda: un test de
`session-and-dashboard.test.tsx` verificaba explícitamente que sin tenant activo solo se emitían
`/tenants` y `/health`; ampliada la lista blanca a `+"/me"` (no depende de tenant, la intención
original del test —ninguna petición *tenant-scoped* sin tenant activo— queda intacta). Ambos archivos
estaban commiteados: **hook-disable dance** autorizado explícitamente por Victor en cada caso
(`.claude/settings.json`, `PreToolUse` vacío durante el cambio puntual, reactivado y verificado con
una invocación directa del hook antes de continuar). Ningún archivo de `.claude/` quedó modificado al
cerrar el grupo (es local, no se commitea).

**No se activó la parada de control (tarea 3.7) por rediseño de sesión**: el único bloqueo real fueron
fixtures de test, ya resuelto arriba — la implementación de producto no exigió tocar login,
persistencia, guard ni logout más allá de lo previsto en la decisión 2.

**Mutación** (tester, Stryker efímero acotado a `SessionGate.tsx`): score inicial 68.16% (51
supervivientes) → tras 17 casos nuevos en `SessionGate.mutation.test.tsx` (MC/DC de `isSession`,
`loadStoredSession`, límites de `handleLogout`), **score final 84.36%** (≥ threshold `break: 80`,
gate en verde). Supervivientes restantes (23 + 5 no-cov) clasificados como mutantes equivalentes o
código muerto defensivo preexistente (guardas de estrechamiento de tipos de TS bajo `enabled:
Boolean(...)`, claves de caché de React Query sin colisión posible en el flujo real, redundancia
entre el efecto de auto-selección de tenant y `handleLogout` al limpiar `TENANT_KEY`) — sin hueco de
cobertura real, sin tocar `SessionGate.tsx`.

**DoD**: `node .claude/harness/check-dod.mjs` falla — pero por `RF-093-001` (preexistente, turbo
resuelve pnpm v11.9.0 en subprocesos pese a `packageManager: pnpm@9.0.0`), no por esta tarea: falla
en los 4 paquetes del monorepo (`backend`, `frontend`, `processor`, `azure-cost-api`), incluidos los
que esta tarjeta no toca. Sustituto verificado (mismo criterio que JUP-093/094/095):
`pnpm --filter @finops/frontend {test,typecheck,lint,build}`, los cuatro en verde
(35 archivos/88 tests, typecheck limpio, lint limpio, build correcto — el aviso de tamaño de chunk
>500kB ya existía antes de esta tarea). Escaneo de secretos: `[PASS]`.

**QA**: primera pasada `changes-requested` — (1) lint en rojo por comillas sin escapar en JSX en
`SessionGate.mutation.test.tsx:259`, corregido por el tester (`&quot;`); (2) tarea 3.6 sin completar
(`RF-090-003` seguía `Open`), completado actualizándolo a `Fixed` en
`openspec/findings/backlog.md` (las dos filas duplicadas preexistentes de esa fila, ambas
actualizadas de forma consistente) citando esta decisión. Segunda pasada: **`accept`**, confirmado con
ejecución independiente de lint/test/typecheck y `git diff` del backlog.

Archivos de este grupo: `SessionGate.tsx` (producto), `SessionGate.profile.test.tsx` +
`SessionGate.mutation.test.tsx` (tests nuevos), `tests/test-support.tsx` +
`tests/session-and-dashboard.test.tsx` (fixture/aserción ampliados), `openspec/findings/backlog.md`
(`RF-090-003` → `Fixed`).

Commit pendiente de este grupo tras revisión del usuario.

## Grupo 4 — Capa de acceso única

**Doc-only: sin código de producto ni tests nuevos**, excepción documentada aquí. Las 4 tareas se
resuelven con verificación (grep exhaustivo + lectura de cobertura existente), sin encontrar nada
que corregir.

### 4.1 — Enumeración de puntos de red

```
grep -rn "fetch(\|axios\|XMLHttpRequest\|EventSource\|WebSocket" apps/frontend/src --include=*.ts --include=*.tsx
```

Único resultado en código de producto: `apps/frontend/src/services/api.ts:37` (el `fetch` dentro de
`fetchJson`). Las otras 3 coincidencias son comentarios explicativos en archivos `.test.tsx`
(`SessionGate.test.tsx`, `DashboardPage.test.tsx`, `IngestPage.test.tsx`), no llamadas reales.
**Cero accesos de red fuera de la capa declarada.**

### 4.2 — Consecuencia de 4.1

No aplica: 4.1 no encontró ningún acceso fuera de `services/api.ts` que mover.

### 4.3 — Direcciones de backend fijadas en pantallas

```
grep -rn "VITE_API_BASE_URL" apps/frontend/src --include=*.ts --include=*.tsx
grep -rn "localhost\|http://\|https://" apps/frontend/src --include=*.ts --include=*.tsx | grep -v "services/api.ts"
```

`VITE_API_BASE_URL` solo se lee en `api.ts:18` (con *fallback* `http://localhost:8000`) y se declara
su tipo en `vite-env.d.ts`. El segundo grep, excluyendo `api.ts`, no devuelve nada: **ninguna
pantalla fija una dirección de backend**, todas dependen de la capa centralizada.

### 4.4 — Cobertura de credencial + ámbito de cliente en peticiones autenticadas

De las 10 operaciones (grupo 1), 6 exigen `X-Tenant-Id` además de `Authorization: Bearer`:
`/billing/summary`, `/jobs/ingest` y las 4 de `/assistant/conversations*`. Verificado que **ya
tenían cobertura real** (heredada, no de esta tarjeta) antes de escribir nada nuevo:

- `tests/conversations.test.tsx`: `for (const request of requests.filter(p => p.path.startsWith(collectionPath))) { expectTenantRequest(request); }` — cubre las 4 operaciones de asistente en una sola pasada (`expectTenantRequest` verifica `Authorization: Bearer <token>` + `X-Tenant-Id` + `Content-Type`).
- `tests/session-and-dashboard.test.tsx`: `expectTenantRequest(billingRequests[0/1], ...)` sobre `/billing/summary`.
- `tests/ingestion.test.tsx`: `expectTenantRequest(submitted!, tenants[1].id)` sobre `/jobs/ingest`.
- **Sin ámbito seleccionado no se emite petición tenant-scoped**: `tests/session-and-dashboard.test.tsx`, caso "handles an empty tenant list without issuing tenant-scoped product requests" — sin tenant activo, clic en Ingestions/Assistant muestra "Tenant required" y la aserción final confirma que ninguna petición fuera de `/tenants`, `/health`, `/me` se emitió (ampliada en el grupo 3 para incluir `/me`). A nivel de código, la guarda vive en `useDashboardData.ts` (`enabled: Boolean(token && tenantId)`) y equivalentes en `IngestPage.tsx`/`ConversationsPage.tsx`.

**No se escribe test nuevo**: añadir uno duplicaría cobertura ya real y verificada, sin ganar nada —
la spec `frontend-api-layer` (escenarios "Una petición autenticada lleva credencial y ámbito" / "Sin
ámbito seleccionado no se consulta un contrato que lo exige") ya está satisfecha por la suite
existente, confirmado por lectura línea a línea, no por suposición.

Ningún archivo tocado en este grupo. Sin cambios que verificar con test/lint/typecheck/build más
allá de lo ya confirmado al cerrar el grupo 3.

Commit pendiente de este grupo tras revisión del usuario.

## Grupo 5 — Estados observables de las pantallas servidas

Sobre `/overview-legacy` (`DashboardPage.tsx` + `useDashboardData.ts`), la única ruta con datos
reales. **Sin corrección de código de producto**: los tres comportamientos exigidos ya eran
correctos por diseño; el trabajo del grupo fue verificar y, donde faltaba, reforzar cobertura.

### 5.1 (carga / fallo) — ya cubierto, sin test nuevo

- Carga visible: `tests/session-and-dashboard.test.tsx` → "keeps a visible loading state until
  billing is available" (confirma `queryByText("Monthly Spend")` ausente mientras carga).
- Fallo comunicado, no disfrazado de vacío: mismo archivo → "surfaces %s failures and keeps
  navigation available" (`/billing/summary`, `/health`) — muestra "Backend unavailable" + el mensaje
  real del error, y confirma que "Monthly Spend" no aparece (el fallo no se confunde con ausencia de
  datos).

Confirmado además por lectura de `DashboardPage.tsx`: el bloque `if (loading || (!error && !payload))`
antecede estructuralmente a cualquier render de montos, así que un fallo o una carga en curso nunca
puede mostrar datos parciales o del error como si fueran cero.

### 5.1 (reconsulta al cambiar de ámbito) + 5.3 — matiz sin cubrir, test nuevo

La reconsulta en sí (2 peticiones con `X-Tenant-Id` distinto, nuevo valor visible al final) ya la
cubría `tests/session-and-dashboard.test.tsx` ("replaces a stale tenant selection..."). Pero ningún
test inspeccionaba el **frame de transición**: si durante la ventana en que la petición del tenant
nuevo sigue en vuelo, el dashboard sigue mostrando (aunque sea un instante) el monto del tenant
anterior.

Test nuevo: `apps/frontend/tests/dashboard-tenant-transition.test.tsx` — usa `deferredResponse()`
para congelar la respuesta de `/billing/summary` del segundo tenant, y verifica **antes** de
resolverla que el monto del primer tenant ya no está en el documento y que se muestra el estado de
carga ("Connecting to the FinOps control plane..."); luego resuelve y confirma el valor correcto del
segundo tenant. **Pasa sin tocar código de producto**: confirma lo que el diseño ya garantizaba
(`queryKey: ["billing-summary", tenantId]` cambia con el tenant; `payload` es `null` hasta que la
key nueva tiene datos, así que `DashboardPage` nunca alcanza el bloque de render de montos con datos
del tenant anterior).

### 5.4 — Mutación sobre `useDashboardData.ts` + `DashboardPage.tsx`

Stryker acotado a ambos archivos. **Score inicial 75.00%** (44 killed, 12 survived, 1 timeout, 3
no-coverage) — bajo el umbral. Añadidos `useDashboardData.mutation.test.tsx` (4 casos, hook aislado
con `renderHook`) y `DashboardPage.mutation.test.tsx` (3 casos, complementarios a
`DashboardPage.test.tsx` sin duplicar sus aserciones). **Score final 83.33%** (50 killed, 0 timeout,
7 survived, 3 no-coverage), por encima de `break: 80`.

Mutantes matados incluyen: `queryKey` de billing/health, las tres ramas de `enabled`/`loading`/
`payload` de `useDashboardData` (incluida la distinción `&&` vs. `||` en `loading`, que exigió un
caso con billing resuelto y health aún pendiente), `user?.full_name` (optional chaining),
`tenants.map(...)` y las dos ramas de la condición de bootstrapping de `DashboardPage`.

Supervivientes restantes, clasificados como código muerto/inalcanzable dado el contrato público (no
exigen cambio de producto): el `throw` de `queryFn` sin `tenantId` (`useDashboardData.ts:15-16`) es
inalcanzable porque `enabled: Boolean(token && tenantId)` nunca deja invocar `queryFn` sin tenant, y
el hook no expone `refetch` manual que pudiera burlar ese `enabled`; el `if (!payload) return null`
de `DashboardPage.tsx:63` es inalcanzable porque el guard anterior (bootstrapping) ya intercepta todo
estado con `payload` falso y sin error.

### Verificación

Confirmado por el tester y, de forma independiente, por mí: `pnpm typecheck` y `pnpm lint` limpios;
`vitest run` **38 archivos / 96 tests en verde**. Ningún archivo de producto en el diff del grupo —
solo 3 archivos de test nuevos: `dashboard-tenant-transition.test.tsx`,
`useDashboardData.mutation.test.tsx`, `DashboardPage.mutation.test.tsx`.

**Nota sobre *flakiness* de entorno, no relacionada con esta tarea:** una corrida serial mía
(`--no-file-parallelism`) dio un único fallo puntual en `tests/tenant-switching.test.tsx:51`
(archivo del grupo 3, ya cerrado, sin relación con `DashboardPage`/`useDashboardData`) por timeout
de `findByText`. Reproducido en aislamiento (mismo archivo, solo, mismo comando): falló una vez y
pasó la siguiente, sin ningún cambio entre medias — confirma *flakiness* real de la máquina
(coincide con lo que ya reportó el tester: contención de recursos, no defecto). Una corrida completa
en paralelo, posterior, dio 38/38 y 96/96 limpio.

Commit pendiente de este grupo tras revisión del usuario.

## Grupo 6 — Mapa de carencias por pantalla

**Doc-only: solo documentación y comentarios, sin comportamiento nuevo**, excepción documentada
aquí. No se toca ningún archivo de `apps/backend/**` (confirmado abajo).

### 6.1 — Capacidad ausente por pantalla

Apoyado en `RF-091-003` y en
[docs/planning/JUP-091-economicon-source-inventory.md](../../../docs/planning/JUP-091-economicon-source-inventory.md)
(sección "Mapeo de pantallas a contratos del backend", que ya hizo este análisis sobre el código del
origen antes de portar). Traducido dato a dato a los 5 módulos ya portados en JUP-095
(`apps/frontend/src/data/demo/*.ts`), verificando variable a variable que los nombres coinciden con
el código real (no con el inventario de memoria).

### 6.2 — Comentarios ampliados

Los 5 módulos de `src/data/demo/` (`executiveCostDashboard.ts`, `operationalCostDashboard.ts`,
`executiveCutDashboard.ts`, `anomaliesPanel.ts`, `recommendationsPanel.ts`) tienen ahora, junto al
comentario "DATOS DE DEMOSTRACION (sustituibles)" ya existente, la capacidad concreta de
`RF-091-003` que le falta a cada export, con referencia al documento del mapa. Caso particular:
`executiveCostDashboard.ts` distingue explícitamente los dos KPIs que sí tienen contrato parcial
(`GET /billing/summary`, bloqueados por `RF-091-004`, no por ausencia de capacidad) de los dos que
no tienen ninguno (`C7`, `C2`).

### 6.3 — Documento del mapa

[docs/planning/JUP-097-frontend-data-gap-map.md](../../../docs/planning/JUP-097-frontend-data-gap-map.md):
tabla de 16 filas (pantalla → dato → capacidad ausente → finding), más el resumen por capacidad (C1-C7)
con las pantallas ya portadas que la necesitan, y una sección explícita de qué hacer cuando una
capacidad se construya (para que el mapa no envejezca en silencio).

### 6.4 — `RF-095-002` refinado

Actualizado en `openspec/findings/backlog.md`: enlaza el mapa nuevo, **permanece `Open`**
deliberadamente (JUP-097 no conecta ninguna pantalla, decisión de alcance previa a proponer) — el
refinamiento es el insumo accionable, no un cierre.

### 6.5 — Confirmación de que backend no se tocó

```
git diff origin/develop...HEAD --stat -- apps/backend/
```
Sin salida: **ningún archivo de `apps/backend/**` en el diff de la rama completa** (no solo de este
grupo). `RF-091-003` y `RF-091-004` verificados sin cambio en el mismo diff — solo aparecen como
contexto, ninguna línea añadida/modificada les pertenece.

### Verificación

`vitest run`: primera corrida tras los cambios mostró 20 fallos en 8 archivos, con tiempos de
`environment`/`setup` muy elevados (contención de recursos de la máquina, mismo patrón ya
documentado en el grupo 5). Re-ejecutada sin ningún cambio de por medio: **38/38 archivos, 96/96
tests en verde**. `typecheck` y `lint` limpios en ambas corridas — confirma que los comentarios
nuevos (JS/TS válido) no afectan compilación. Los cambios de este grupo son comentarios y
documentación exclusivamente; no hay mecanismo por el que pudieran causar un fallo de test real.

Archivos de este grupo: 5 módulos de `src/data/demo/` (comentarios), `openspec/findings/backlog.md`
(`RF-095-002` refinado), `docs/planning/JUP-097-frontend-data-gap-map.md` (nuevo).

Commit pendiente de este grupo tras revisión del usuario.
