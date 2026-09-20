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

Commit pendiente de este grupo tras revisión del usuario.
