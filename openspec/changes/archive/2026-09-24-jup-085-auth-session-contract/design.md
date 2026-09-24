JUP: JUP-085
ADR: [ADR-0007: Backend CORS policy](../../../docs/adr/ADR-0007-backend-cors-policy.md), Accepted. Gate pre-code registrado en proposal.md el 23/09/2026 a las 13:05:53 UTC. Residual/CORS REVIEW_PASS; QA_BLOCKED_ENV por RF-085-002; gate humano pendiente.

## Context

Incremento autorizado de 5 s: [addendum literal](proposal.md#addendum-tolerancia-jwt-de-5-segundos).
Red/Green y mutacion completados; REVIEW_PASS incremental y navegador 8/8
sobre la imagen actualizada. QA_PASS acotado al incremento; no se levanta el bloqueo
ambiental ni se intervienen relojes. Resultados propios en
[evidencia incremental](../../../docs/evidence/JUP-085-validation.md#incremento-actual-tolerancia-jwt-de-5-s)
y [review](review.md). Los inventarios y resultados previos conservan su fecha.

Estado del 2026-09-23: HEAD del worktree es
`3a08d60ddd48a8693a95025948bc941a0e54b7de`, tras fast-forward desde `1ff8e071`
preservando los 15 archivos sucios existentes entonces, segun el orquestador.
Los inventarios siguientes son antecedentes anteriores a la implementacion,
no una evaluacion actual de gaps. Fuentes y estado en [proposal.md](proposal.md).
Se conserva JUP-097: perfil y tenants en paralelo, logout ante cualquier error
de la query `/me`. No se afirma mayor seguridad. La aprobacion del 10/09 es
historica y no aprueba este residual revisado.

Inventario backend historico del 10/09, anterior a su implementacion local:

| Superficie en la base | Entregado / observado | Residual JUP-085 |
|---|---|---|
| `apps/backend/app/schemas/auth.py:4` | EmailStr y password string; perfil de cuatro campos | Password no tiene longitud minima; falta caso vacio y negativos HTTP |
| `apps/backend/app/api/routes/auth.py:12` | Login devuelve token bearer y `user`; email desconocido/password incorrecta comparten `401` | Conservar contrato y probarlo via HTTP con fixtures sinteticas |
| `apps/backend/app/api/routes/auth.py:39` | `/me` devuelve perfil directo | Verificar perfil actual y ausencia de hash/password, sin envolver en `user` |
| `apps/backend/app/core/security.py:25` | HS256, `sub`, `exp`; decode limita algoritmo | Falta `iat`; decode no exige claims ni valida tipos/relaciones de forma explicita |
| `apps/backend/app/api/dependencies.py:27` | Bearer ausente/esquema incorrecto y excepciones de decode dan `401`; usuario ausente da `401` con mensaje distinto | `payload["sub"]` fuera del try permite KeyError; falta clasificar claims antes de acceder a DB y normalizar usuario ausente |
| `apps/backend/app/core/config.py:19` | Clave externa y TTL 480 configurable | TTL no exige ser positivo; conservar las validaciones de secretos |
| `apps/backend/app/db/database.py:50`, `apps/backend/tests/test_demo_seed.py:75` | Seed desactivado por defecto, password externa, cuentas/roles existentes preservados; pruebas de rotacion/login | Reutilizar como regresion, sin volver a implementar JUP-053 |

El avance backend del 10/09 y sus limites constan en [review.md](review.md):
169 tests correctos, 54 nuevos; 13 variantes de mutacion, 12 detectadas y una
equivalente. Son resultados historicos; los actuales figuran en tasks.md.
La tabla anterior describe gaps de
la base, no defectos nuevamente constatados en el trabajo local ya implementado.

PyJWT y FastAPI ya figuran en `apps/backend/requirements.txt`; pytest/httpx en
`requirements-dev.txt`. El decode de aquella base no pasaba `options.require`: no basta
verificar expiracion si existe para exigirla. Un JWT firmado sin `exp` puede
eludir expiracion; uno sin `sub` llega a una lectura no protegida y al `500`
sanitizado de `core/request_context.py:21`. Los tipos aceptados por defecto
dependen de la version de PyJWT; el contrato no dependera de coerciones o de
su minimo abierto `>=2.8.0`. No se cambia la dependencia.

Las pruebas de aquella base `test_auth_schema.py:4` y `test_security_utils.py:16` cubrian exito
de schema y roundtrip con `sub`; no prueban `iat`, expiracion ni el contrato HTTP
negativo. `test_demo_seed.py:126` prueba login como funcion y rotacion de clave.
`test_secret_boundaries.py:215` proporciona el patron httpx/ASGI y verifica
errores `422`/`500` sin datos sensibles; no sustituye la matriz auth.

Inventario frontend pre-code, leido en upstream (rutas bajo `apps/frontend/src/`):

| Superficie | Entregado / observado el 23/09 | Residual propuesto, pendiente de gate |
|---|---|---|
| `layouts/SessionGate.tsx` | Guard estructural de storage; `/me` y `/tenants` con el mismo enabled por token; identidad de `profileQuery.data` en Outlet | Rechazo de strings vacios, contratos runtime y limpieza completa de storage invalido no acreditados |
| `layouts/SessionGate.tsx` | `profileQuery.isError` llama `handleLogout` sin filtro de causa; retira sesion/tenant y ejecuta `queryClient.clear()` | Proteccion de generaciones y respuestas/callbacks tardios no acreditada |
| `layouts/SessionGate.tsx` | Query keys `["profile", session?.accessToken]` y `["tenants", session?.user?.id]`; seleccion de tenant puede ocurrir mientras `/me` esta pendiente | No cambiar silenciosamente las claves; resolver limpieza de identidad discrepante y carreras del bootstrap paralelo |
| `services/api.ts`, `services/contracts.ts` | Capa unica tipada; `fetchProfile` ya se consume; error generico pierde status y JSON se tipa sin validacion runtime | Error estructurado y `401` global fuera de `/me`, sin alterar su politica estricta |
| `pages/LoginPage.tsx` | Password vacia; persiste respuesta y navega al armazon, que lanza ambas queries | Validacion runtime del wrapper y control de callbacks de login pendientes |

JUP-087/PR #29 (`1de7b16`), JUP-095/PR #36 (`cb4edc3`) y JUP-097/PR #42
(`3a08d60`) ya estan fusionados. Se leyeron `frontend-api-layer/spec.md` y el
archivo `2026-09-21-jup-097-reconcile-api-layer`: la capa API sigue siendo unica,
`/me` mantiene su consumidor y no exige X-Tenant-Id. RF-090-003 figura Fixed en
upstream. No se atribuyen nuevos resultados de prueba a esta lectura estatica.

## Goals / Non-Goals

**Goals:**

- Hacer explicitos request, response, claims, TTL y errores de login/perfil.
- Preservar la revalidacion paralela y el logout estricto de JUP-097; el residual
  aprobado de validacion, expiracion y limpieza esta implementado y REVIEW_PASS.
- Conservar las garantias de secretos y credenciales de JUP-053.
- Permitir pruebas positivas y negativas reproducibles.

**Non-Goals:**

- Integrar un IdP externo, refresh tokens, MFA o revocacion distribuida.
- Declarar la autenticacion propia adecuada para produccion publica.
- Implementar autorizacion por tenant, que pertenece a JUP-086.
- Port visual JUP-095, pipeline JUP-020/RF-053-004, cambios generales de API,
  CI, migraciones o nuevas dependencias.

## Decisions

Formulacion tecnica previa, salvo el incremento temporal autorizado de 5 s
que actualiza exclusivamente la validacion del token descrita debajo. Las
referencias a propuesta o pendiente en su redaccion original describen el
momento de planificacion, no gates actuales; la implementacion residual/CORS
esta completada y REVIEW_PASS tras RF-085-001 Fixed local, sin integrar.
`discardResponse` mantiene pending las promesas abandonadas retenidas externamente.
`clearSessionMutations` retira mutaciones de cache y dispone solo esos objetos
con APIs publicas: `setOptions` con `gcTime: Infinity` y `destroy` cancelan el
timer sin rearmarlo al desmontar observadores. No cambia el GC de mutaciones
activas ni aborta transporte. Dos regresiones Red pasan en Green dentro de las
tres superficies frontend originales. Reviewer: 135 hashes y guard PASS.

### Contrato HTTP aprobado

`POST /auth/login` acepta email valido y password string de longitud al menos
uno, sin recortarla ni normalizarla. Ausencia, null, tipo incorrecto, email
invalido o password vacia producen `422` con el handler sanitizado existente,
sin eco de input/password. Una password de espacios se compara literalmente;
no se introduce otra politica de contrasenas. En exito devuelve
`access_token`, `token_type: bearer` y `user`, un perfil con `id`, `email`,
`full_name` y `role`. Credenciales sintacticamente validas pero incorrectas
devuelven `401`, `{"detail":"Invalid email or password."}` tanto para email
desconocido como password incorrecta. No se promete igualdad de tiempos.

`GET /me` acepta exactamente una cabecera Authorization con esquema Bearer
insensible a mayusculas y un token no vacio sin segmentos extra. Cabecera
ausente, duplicada, esquema incorrecto o bearer mal formado: `401` con
`{"detail":"Missing or invalid bearer token."}`. JWT corrupto, algoritmo no
HS256, firma incorrecta, claims invalidos/ausentes, expiracion o usuario
inexistente: `401` con `{"detail":"Invalid access token."}`. No exponer causa
de parsing, token, sujeto ni existencia del usuario. Validar antes de llamar
`fetch_user_by_id`; la ausencia de usuario devuelve `401`, pero un fallo de DB
sigue siendo error de servicio sanitizado, no una credencial rechazada.

En exito `/me` devuelve directamente ese perfil, sin el envoltorio `user`
de login; resuelve los campos actuales de DB, sin confiar en perfil/role
guardados en navegador ni requerir X-Tenant-Id. Se toca solo autenticacion de
`get_current_user`; `get_active_tenant` y sus `400`/`403` permanecen bajo JUP-086.

### Token de acceso acotado

Emitir `sub` como id no vacio, `iat` y `exp` como segundos UTC enteros, desde
un mismo instante: `exp = iat + AUTH_TOKEN_TTL_MINUTES * 60`. TTL entero positivo,
default 480 sin cambiar emision ni TTL. Decode exige los tres claims, `sub`
string no vacio, `iat`/`exp` enteros (no bool, string o float), `iat >= 0`,
`exp > iat`, `iat <= now + 5` y `exp > now - 5`. La igualdad `iat == now + 5`
se acepta; `exp == now - 5` se rechaza. `now == exp` puede aceptarse dentro
del margen si el resto es valido. No admitir iat/exp negativos ni relajar
firma HS256, claims requeridos o lookup de usuario.

Usar `jwt.decode(..., leeway=5)` nativo en
`apps/backend/app/core/security.py`, con constante local de segundos si ayuda;
conservar `algorithms=["HS256"]`, `options.require` y guardas estrictas actuales.
PyJWT aplica el mismo margen a `nbf` opcional: para un valor entero,
`nbf <= now + 5` pasa el control temporal, por encima falla. No emitir/exigir
`nbf` ni alterar su parsing nativo.
No crear validacion de reloj paralela ni desactivar verificaciones PyJWT.
La condicion `exp > iat` sigue siendo independiente y obligatoria: rechazar
`iat=now+4, exp=now-4` aunque ambos pasen sus limites contra `now`.

Antecedente tecnico hasta este addendum: `0 <= iat <= now < exp`, leeway cero
con expiracion exacta. Se conserva como historia, no como norma vigente ni
eleccion humana especifica. BE1 era equivalente en esa ronda porque el orden
contra `now` implicaba `exp > iat`; con 5 s ya no lo implica. BE1 deja de ser
equivalente para el incremento y fue reevaluado: KILLED por dos casos, sin
reescribir su dictamen historico. No implementar criptografia ni interpretar el JWT en frontend.

Tokens anteriores sin `iat` dejan de ser aceptados y requieren nuevo login.
Esta consecuencia fue aprobada expresamente; no hay migracion ni backfill de
sesiones, endpoint de logout, blacklist o refresh. Clave externa y controles
de JUP-053/ADR-0006 se conservan sin cambios.

### Revalidacion integrada por JUP-097: politica a conservar

`SessionGate` ya consulta `/me` y `/tenants` en paralelo cuando hay token,
tambien al montar despues de login. Ambas llamadas usan bearer sin X-Tenant-Id;
los contratos que exigen tenant siguen esperando seleccion. Durante la carga
inicial el armazon no expone Outlet ni datos autenticados. El perfil expuesto
procede de `/me`; no se da por hecho que tambien se reescriba localStorage.
La seleccion/cache interna de tenants puede avanzar en paralelo: no confundir
ocultar la UI con prohibir peticiones o escrituras internas de bootstrap.

Todo `profileQuery.isError` llama `handleLogout`, incluso con red, `403`, `422`,
`5xx` o fallo de parsing. Esto aplica al arranque y a las revalidaciones que
ejecute la query; una identidad previamente obtenida no exceptua un error
posterior. En el frame entre error y efecto se bloquea Outlet. Un fallo de DB
puede seguir siendo `5xx` sanitizado en backend y causar logout en frontend:
la politica de cliente no reclasifica ese fallo como credenciales invalidas.

El disparador es el estado de error de la query. No se prescribe logout en
el primer intento fallido previo a ese estado, ni se cambia la configuracion
existente de retry/refetch. No se anade polling de perfil, refresh o temporizador
cliente que interprete el JWT. Los errores de `/me` no pasan a un estado de
sesion conservada con reintento explicito por introducir errores estructurados.

### Restauracion y contratos runtime: residual aprobado e implementado

Los siguientes puntos excedian lo demostrado por JUP-097; el gate residual
esta resuelto y se han implementado. Este turno solo sincroniza estado:

1. Reforzar el guard existente: `accessToken` e id/email/role strings no vacios,
   full_name string. JSON roto, null, primitivas, arrays o estructura incompleta
   limpian sesion, tenant y cache antes del login, sin peticiones autenticadas.
   Aplicar la limpieza si no hay sesion pero quedan tenant/cache antiguos.
2. Con sesion valida, conservar el arranque paralelo de `/me` y `/tenants`.
   La UI autenticada y billing/jobs/assistant esperan perfil confirmado y
   bootstrap utilizable; una respuesta de tenants temprana no acredita identidad.
3. Validar el perfil directo de `/me` y proponer actualizar el perfil persistido
   tras exito de la generacion vigente. Un `200` invalido, incluido `{user: ...}`,
   se convierte en error de revalidacion y usa el mismo logout estricto. Tenants
   puede estar en vuelo o resuelto: retirar tambien sus efectos locales y no
   iniciar peticiones de producto a partir de esos resultados.
4. Si el id confirmado difiere del persistido, proponer descartar seleccion y
   cache asociados a la identidad anterior, incluidos resultados de tenants
   iniciados en paralelo con ella; reconciliar identidad y repetir el bootstrap
   de tenants antes de exponer datos. Esta recuperacion excepcional no serializa
   el arranque normal. Persistencia del perfil, limpieza y generacion en este
   caso son parte del residual pendiente, no garantias ya entregadas por JUP-097.
5. Validar login (`access_token` no vacio, bearer, `user` valido) antes de
   persistir y navegar. Al montar `SessionGate`, mantener `/me` y `/tenants`
   en paralelo; no omitir `/me` por considerar suficiente el wrapper de login.
   Una respuesta login invalida no crea sesion ni dispara el bootstrap.

### Logout y carreras: residual aprobado e implementado

Proponer status numerico y errores acotados en `fetchJson`, sin bearer en
errores o logs. El perfil ya usa `["profile", session?.accessToken]` y tenants
`["tenants", session?.user?.id]`. Se reconoce ese estado sin prohibir la clave
existente, retirarla o migrarla como efecto implicito de este cambio. Comparar
token/user id o conservar esas claves no prueba aislamiento entre logins con
los mismos valores. Cualquier cambio de claves que resulte necesario debera
explicitarse en el alcance antes de implementar.

La propuesta de aislamiento usa una generacion en memoria capturada al
despachar y comprobada antes de efectos, incluidos lectura tardia del body y
callbacks de login. Avanza al aceptar login, reemplazar identidad o invalidar
sesion. Implementacion completada y REVIEW_PASS; QA_BLOCKED_ENV.

Para peticiones autenticadas distintas de `/me`, proponer que un `401` de la
generacion vigente dispare limpieza antes de parsear el body, sin retry de ese
`401`, cubriendo `/tenants`, billing, ingesta y conversaciones, incluidas
mutaciones. La limpieza retira sesion/tenant de memoria/storage, detiene o
cancela consultas cuando sea posible, vacia cache de consultas/mutaciones y
desmonta estado de paginas antes del login. Es idempotente.

`/me` conserva su camino de revalidacion estricto ante CUALQUIER error de query,
no solo `401`. La normalizacion comun no consume/silencia sus errores, no los
convierte en exito ni aplica la politica recuperable de otros endpoints. La
propuesta de generacion evita que una query abandonada afecte a otra sesion;
no filtra errores transitorios de la revalidacion vigente. Logout cancela o
descarta tambien el `/tenants` concurrente, aunque hubiera resuelto antes.

Ignorar exito, error y callbacks de una generacion anterior tras logout o
nuevo login, incluso `/me` con token/usuario repetidos: no repoblar
cache/UI/storage, disparar consultas ni invalidar la nueva sesion. Una
cancelacion causada por abandonar la generacion no es un fallo de `/me` de
la nueva sesion. Abortar en cliente no revierte operaciones aceptadas en
servidor. Mantener regresiones de cambio de tenant de JUP-087 sin ampliar
autorizacion backend.

Solo fuera de `/me`, `403`, red, `422` y `5xx` conservan sesion y muestran el
error del flujo. Login/health sin bearer no invalidan otra sesion por `401`.
No inferir expiracion del texto de error. Tras logout local el JWT puede seguir
aceptandose mientras `now < exp + 5` si el resto es valido; no hay revocacion remota.

## Reuse And Bounded Paths

Sobre la base ya sincronizada `3a08d60`, se reutilizan
Vitest/Testing Library/jsdom, `deferredResponse`, `mockBackend`, QueryClient
aislado y regresiones de tenants. El helper actual `tests/test-support.tsx` ya
simula `GET /me`; no crear otro runner. `LoginPage.tsx` conserva password vacia.
Las pruebas de JUP-097 son regresiones a preservar, no evidencia de que el
residual runtime y todas sus carreras esten cubiertos.

Limite de escritura de este turno: exclusivamente los cuatro documentos
`proposal.md`, `design.md`, `tasks.md` y `specs/demo-auth-session/spec.md` bajo
este cambio; no se edita ADR-0007. En el incremento completado, producto limitado
a `apps/backend/app/core/security.py` y pruebas existentes
`apps/backend/tests/test_security_utils.py` y `apps/backend/tests/test_auth_api.py`.
Solo `test_auth_api.py` necesito cambios; `test_security_utils.py` se conservo.
Reutilizar reloj fijo/fixtures, actualizar solo expectativas temporales y anadir
fronteras/relacion exp-iat; sin configurar entorno, dependencias, endpoints,
frontend, CORS, Windows/WSL/Docker/reloj DB. La tabla siguiente
conserva el inventario de planificacion aprobado; no habilita edicion de producto hoy:

| Limite | Archivos |
|---|---|
| Backend auth historico | `apps/backend/app/schemas/auth.py`, `core/security.py`, `core/config.py` (solo TTL), `api/dependencies.py` (solo get_current_user), `api/routes/auth.py` (solo contrato auth); todos bajo `apps/backend/app/` |
| Backend tests historicos | `apps/backend/tests/test_auth_schema.py`, `test_security_utils.py`, `test_auth_api.py`, `test_secret_config.py` (solo TTL); reutilizar regresiones JUP-053 |
| Frontend auth propuesto sobre JUP-095/097 | `apps/frontend/src/layouts/SessionGate.tsx`, `services/api.ts`, `services/contracts.ts`, `pages/LoginPage.tsx` (solo validacion/estado auth); todos bajo `apps/frontend/src/`; no tratar App.jsx/App.tsx como propietario actual de sesion |
| Frontend tests propuestos | `apps/frontend/tests/session-and-dashboard.test.tsx`, `fixtures.ts`, `test-support.tsx`, posible nuevo `auth-session.test.tsx`; tambien regresiones existentes `src/layouts/SessionGate.test.tsx`, `SessionGate.profile.test.tsx` y `SessionGate.validation.test.tsx` bajo `apps/frontend/src/layouts/` si el alcance revisado las autoriza |

Las rutas abreviadas de cada fila comparten su directorio indicado. El residual
usa `apps/frontend/tests/auth-session.test.tsx` y `tests/test-support.tsx`.
Se corrigieron cuatro fixtures legacy invalidas, sin cambiar alcance:
una en `apps/frontend/src/layouts/SessionGate.test.tsx`, dos en
`apps/frontend/src/routes.integration.test.tsx` (respuestas distintas para
`/me` y `/tenants`) y una en `apps/frontend/src/pages/LoginPage.test.tsx`
(contrato login completo y password sintetica introducida explicitamente).
Son ajustes de datos/mocks al contrato, no requisitos ni runner nuevos.
Otras paginas, setup, manifests, CI, DB/seed, logging o
docs externos al cambio requieren decision antes de editar. CORS no se agrega
implicitamente al limite backend auth. No se presenta el backend historico
como cierre de JUP-085 ni como permiso para reanudar producto hoy.

## CORS: Direction Chosen, Concrete Policy Pending

Se conserva este encabezado para mantener su anchor y los enlaces existentes.
Estado actual: gate concreto aprobado, ADR-0007 Accepted y CORS implementado en
`apps/backend/app/main.py`; la base upstream no lo configuraba. Paris eligio
backend, no proxy. El [review actual](review.md) registra QA_BLOCKED_ENV tras
la mitigacion temporal insuficiente; RF-087-001/RF-095-001 siguen Open;
no se editan findings aqui. Los parametros/limites siguientes no cambian.

### Parametros aprobados

- Reutilizar `CORSMiddleware` de FastAPI/Starlette, ya disponible; sin nueva
  dependencia. Mantener frontend/API en puertos separados, 5173/8000 por defecto.
- `Settings.cors_allowed_origins: list[str]` desde `CORS_ALLOWED_ORIGINS`, JSON
  estructurado via pydantic-settings y validador de origen con parser de URL,
  sin split/ad hoc ni coercion de entradas. Ausente o `[]`: lista vacia, sin
  permisos cross-origin. Valor vacio, JSON mal formado, tipo distinto de lista
  o elementos no string/origen valido: fallo de arranque por `get_settings()`
  y su `StartupError` generico existente, sin input, secretos ni cadena de causas.
- Exigir origen serializado exacto `scheme://host[:port]`, sin path (ni `/`
  final), userinfo, query, fragmento, espacios o puerto invalido. Rechazar `*`,
  patrones, regex y `null`; no reflejar origenes fuera de la allowlist ni
  normalizar silenciosamente una entrada no canonica. HTTPS en production;
  HTTP solo en development/test, segun `runtime_environment` existente.
- `.env.example` propuesto: `CORS_ALLOWED_ORIGINS=[]` y ejemplo comentado
  `CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]`,
  solo development/test; no habilitarlo con el default production. Un
  `FRONTEND_HOST_PORT` distinto exige actualizar los origenes del navegador;
  no derivarlos del bind de Docker. Operador aporta origenes HTTPS de produccion,
  sin inventar dominios. Compose pasara la variable al backend con default `[]`
  solo si esta ausente, preservando un valor vacio para que validacion lo rechace.
  `.env` ignorado no se edita, copia ni sobrescribe; no retirar valores secretos.
- `allow_methods=["GET","POST"]`; OPTIONS preflight nativo, sin JWT ni lookup
  de usuario/tenant. `allow_headers=["Authorization","Content-Type","X-Tenant-Id"]`
  segun `services/api.ts`, ademas de las cabeceras safelisted normales del
  framework; no afirmar exclusividad de esas tres. Sin wildcard de cabeceras.
- `allow_credentials=false`, sin auth por cookies ni `credentials: "include"`;
  conservar fetch actual. Bearer proporcionado explicitamente se permite por
  su cabecera, no por el flag de cookies. `expose_headers=[]`, sin consumidor
  actual de cabeceras adicionales; conservar `max_age=600` del middleware.
- CORS regula lectura por navegador, no autenticacion ni autorizacion servidor.
  Preflight denegado no concede la combinacion solicitada; una peticion simple
  de origen no permitido puede ejecutarse pero no recibe Allow-Origin. JWT y
  autorizacion tenant siguen intactos, tambien en clientes sin Origin.

### Cableado y limite de errores

Conservar `app.main.app` como FastAPI con `state`, `router`,
`dependency_overrides`, lifespan y middleware nativos. Los tests de
`test_secret_boundaries.py` exigen importar sin secretos ni cargar Settings;
`test_request_id_middleware.py` inspecciona `user_middleware`. Proponer un
adaptador local de inicializacion de CORSMiddleware en `main.py`, registrado
con `add_middleware`, que obtenga Settings al construirse la pila ASGI, no al
importar ni mediante `add_middleware` dentro del lifespan ya iniciado.

Orden propuesto: ServerErrorMiddleware > CORS > MetricsMiddleware >
RequestIdMiddleware > ExceptionMiddleware/rutas. Mantener recursos/lifespan,
metricas y contexto/tracing de las peticiones reales; preflights terminan en
CORS y no recorren metricas/log de acceso interiores. Esta diferencia forma
parte del gate aprobado. No reemplazar el export por un wrapper ASGI sin API FastAPI.
La separacion de la capa exterior se apoya en el
[contrato de Starlette](https://starlette.dev/middleware/#corsmiddleware-global-enforcement).

Para Origin permitido, probar Allow-Origin exacto y `Vary: Origin` en exito,
`401` auth, `403` tenant existente, `422` del handler y `500` de fallo de ruta/DB
convertido por RequestIdMiddleware antes de comenzar respuesta; status y cuerpo
sanitizado se conservan. Origin denegado: sin Allow-Origin en esos mismos casos.
No prometer CORS para `500` generado por ServerErrorMiddleware fuera de CORS
(p.ej. fallo del middleware exterior), fallo de arranque o streaming tras headers.
Probar ese limite con inyeccion aislada; ampliar a todos los `500` exigiria otra
decision de cableado y gate, no un wrapper ni refactor de tests globales implicito.

### Superficies aprobadas y aceptacion sin cambios

| Superficie del plan aprobado, sin permiso de edicion hoy | Cambio acotado |
|---|---|
| `apps/backend/app/main.py`, `apps/backend/app/core/config.py` | Registro diferido, lista tipada y validacion; preservar import/lifespan y secretos |
| `.env.example`, `docker-compose.yml` | Ejemplos y paso de la variable exclusivamente al backend |
| `apps/backend/README.md`, `README.md` | Variable y runbook existente de arranque/puertos/entorno; sin crear otro runbook |
| `apps/backend/tests/test_cors.py` (nuevo), `apps/backend/tests/test_secret_config.py` (si necesita casos Settings) | Matriz focalizada de origenes, preflight, auth y errores sobre app real con fixtures sinteticas; sin ampliar conftest global |
| `apps/frontend/src/layouts/SessionGate.profile.test.tsx`, `apps/frontend/tests/session-and-dashboard.test.tsx`, `apps/frontend/tests/test-support.tsx` | Reutilizar casos/helpers nativos de JUP-087/097; cambios solo si faltan regresiones, sin nuevo runner |

Aceptar tras gate: configuracion valida/ausente/vacia/malformada/wildcard;
preflight permitido/denegado (origen, metodo y cabeceras), publicos y bearer sin
JWT en OPTIONS; peticiones reales, auth no eludida y matriz de errores anterior.
Conservar regresiones nativas de import, lifespan/state, overrides, secretos,
metricas y tracing. Navegador real en stack canonico: login, `/me` y `/tenants`
paralelos, logout, con seguridad normal y sin proxy. Cualquier error de query
`/me`, incluso transitorio/CORS, sigue causando logout, sin cambiar retries.
No inferir reparacion de RF-087-002 historico ni ampliar JUP-086. Ningun cambio
de CI, runner, dependencias, migraciones o seed; sin reasignar trabajo operativo.

## Verification Plan

Plan de verificacion de la ronda previa; Red, Green, mutacion y recorrido de
navegador constan en tasks.md. El incremento de 5 s completo Red/Green,
mutacion, review y auditoria QA de la seccion 6, con QA_PASS incremental.
QA final bloqueada por entorno y gate humano post-QA pendiente. No se
reejecuta producto hoy; la unica modificacion temporal implementada es `leeway=5`
segun el addendum, sin intervenir en el reloj ni alterar JUP-097.
Revalidar backend con pytest/httpx sobre rutas reales con DB falsa y
config sintetica existente, sin lifespan conectado a DB/cola/proveedores.
Probar diferencias de status/cuerpo y ausencia de consulta de usuario para
claims invalidos; controlar reloj sin sleeps. Usar Vitest integrado de JUP-087
con HTTP interceptado y promesas diferidas para restauracion, errores y carreras.
Casos ya satisfechos son regresiones; registrar Red solo para gaps observados,
con comando, fallo esperado y requisito, sin exigir que fallen todos los casos.

Green aplica el minimo cambio en las superficies acordadas y ejecuta positivos,
negativos y regresiones de secretos/frontend. Mutation dirigida, sin herramienta
nueva: retirar validacion de vacio, omitir iat/require/exp/firma, cambiar el
wrapper de `/me`, serializar perfil/tenants, conservar sesion ante error de
`/me`, omitir su llamada tras login o permitir efectos de tenants despues de
fallo de perfil. Fuera de `/me`, clasificar `403` como logout, ignorar `401`
en mutacion o suprimir limpieza/generacion tambien debe detectarse.
Cada mutante necesita fallo semantico de un escenario, no fallo de import/build;
restaurar solo la edicion propia y revalidar Green. La mutacion backend del
10/09 se ejecuto en memoria sin editar producto; la ronda residual del 23/09
completo 37 variantes (35 detectadas, 2 equivalentes, 0 pendientes).
Las pruebas de error `/me` deben distinguir intento fallido de query en error;
no deducir el retry de produccion del QueryClient de tests con retry desactivado.

Todos los comandos parten de la raiz del worktree salvo indicacion:

| Fase | Comando | Criterio |
|---|---|---|
| Pre-code | `corepack pnpm openspec:validate` | Validacion de todo OpenSpec, estricta y no interactiva, exit 0 |
| Pre-code | `corepack pnpm jup:check -- --change jup-085-auth-session-contract` | Identificador, URL y artefactos validos, exit 0 |
| Pre-code, fallback sin instalar | CLI OpenSpec 1.8.0 ya disponible: `openspec validate --all --strict --no-interactive`; `node tools/jup-check.mjs --change jup-085-auth-session-contract` | Resolver herramientas existentes conservando cwd; registrar comando real y exitcode, no presentar error de entorno como PASS |
| Backend focalizado | Desde `apps/backend`: `python -m pytest tests/test_auth_schema.py tests/test_security_utils.py tests/test_auth_api.py tests/test_secret_config.py tests/test_cors.py` | Red explica gaps; Green todos correctos, con entorno existente y aislado |
| Frontend sobre base sincronizada y gate aprobado | `corepack pnpm --filter @finops/frontend test` | Suite real Vitest incluidas regresiones JUP-087/095/097, sin objetivo numerico arbitrario |
| Green / revision / QA | `corepack pnpm test`, `corepack pnpm lint`, `corepack pnpm build`, `corepack pnpm --filter @finops/frontend typecheck` | Cada comando con resultado y commit; ningun placeholder cuenta como prueba |
| Gates del repositorio | `corepack pnpm openspec:validate`, `corepack pnpm jup:check -- --change jup-085-auth-session-contract`, `corepack pnpm jup:cleanup:check` | Documentar resultados reales; gestion independiente de esta fase |

Esta sincronizacion ejecuta OpenSpec estricto, trazabilidad, diff-check y guard
de cuatro rutas; no amplia el QA_PASS acotado ya registrado. Resultados historicos
anteriores al incremento: backend 245 PASS con pydantic-settings 2.15; tambien
76 CORS PASS con el minimo 2.3.4, sin cambiar dependencias. Frontend 235 PASS;
resultado incremental y resto de validaciones en tasks.md. Review/evidencia/findings
ya actualizados por el orquestador se leen sin editar aqui.

## Risks / Trade-offs

- [JWT robado puede aceptarse hasta `exp + 5`, exclusivo] -> margen autorizado
  inferior a 5 s despues de expirar; TTL emitido intacto y auth solo de demo.
- [JWT en localStorage accesible a JavaScript/XSS] -> riesgo demo existente;
  no declarar idoneidad productiva ni introducir cookies/IdP sin decision nueva.
- [Re-login por exigir iat] -> consecuencia del alcance backend historico;
  revalidar compatibilidad tras sincronizar, sin migracion de tokens.
- [Logout por errores transitorios de /me] -> politica de JUP-097 que el usuario
  pide conservar el 23/09; tiene coste de disponibilidad y no prueba que las
  credenciales sean invalidas ni una mejora de seguridad.
- [Respuestas tardias repueblan sesion/cache] -> generacion capturada y escenarios
  implementados/probados y REVIEW_PASS, con mismo usuario/token y
  `/tenants` paralelo que resuelve antes o despues del error de perfil.
- [Base local atrasada, antecedente resuelto] -> HEAD `3a08d60` y resultados
  frescos, sin reutilizar el PASS historico ni alterar trabajo previo.
- [CORS en navegador real] -> implementado y review runtime entregado;
  hallazgos Open hasta completar QA final.
- [RF-085-002, High, entorno] -> Open; mitigacion temporal insuficiente;
  alcance temporal y limites en [evidencia](../../../docs/evidence/JUP-085-validation.md#revalidacion-qa-tras-mitigacion-2309).
- [Compatibilidad CORS] -> lista vacia no habilita navegador entre puertos;
  production con origen HTTP fallara al arrancar. Operador debe configurar
  HTTPS o elegir explicitamente development/test para entorno local; no cambiar
  automaticamente el default production ni afirmar hardening productivo completo.
- [500 exterior sin CORS] -> limite documentado del cableado propuesto; no
  garantizar observabilidad de todos los fallos ni ampliar scope para conseguirla.

Codigo REVIEW_PASS tras RF-085-001 Fixed local; RF-085-002 Open, QA_BLOCKED_ENV.
Intervencion del reloj excluida; tolerancia 5 s implementada y REVIEW_PASS,
auditoria QA incremental PASS y gate humano post-QA pendiente. No es una excepcion
ni reparacion del entorno. El gate del residual/CORS ya consta en proposal.md.
Cambiar almacenamiento, TTL, revocacion, dependencias, migraciones o autorizacion
sigue fuera de alcance. La reconciliacion documental conserva la aprobacion
historica; no registra, invalida ni deduce otra aprobacion.
