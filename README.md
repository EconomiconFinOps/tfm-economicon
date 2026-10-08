# FinOps Assistant Monorepo

## Descripcion

Este repositorio contiene un monorepo para un asistente FinOps dividido en varios submodulos que trabajan juntos.

El objetivo del proyecto es separar responsabilidades de forma clara:

- `frontend` para la interfaz web
- `backend` para la API principal
- `processor` para trabajo asincrono, pipelines y embeddings
- `azure-cost-api` para simular el subconjunto de Azure Cost Management Query
- `shared-config` para configuracion compartida del workspace JavaScript

Ademas, el proyecto usa servicios de infraestructura para mensajeria, persistencia operativa y almacenamiento vectorial.

## Stack

- `Turborepo`
- `pnpm`
- `React`
- `FastAPI`
- `Python`
- `RabbitMQ`
- `CockroachDB`
- `Postgres + pgvector`
- `Docker Compose`
- `TanStack Query`

## Estructura

```text
tfm-economicon
|-- apps/
|   |-- backend/
|   |-- frontend/
|   |-- processor/
|   `-- azure-cost-api/
|-- docs/
|   |-- architecture.md
|   `-- manuals/turborepo_use.md
|-- packages/
|   `-- shared-config/
|-- docker-compose.yml
|-- package.json
|-- pnpm-workspace.yaml
`-- turbo.json
```

## Como correrlo

### Requisito previo: pnpm con corepack

El repositorio fija `pnpm@9.0.0` en `packageManager`. Los scripts de la raiz (`lint`, `build`, `test`,
`typecheck`, `dev`) pasan por turbo, que lanza `pnpm run <script>` en cada paquete buscando `pnpm` en el
`PATH`. Si en la maquina no estan activados los lanzadores de corepack, turbo encuentra otro pnpm (por
ejemplo uno global instalado con `npm install -g pnpm`, o uno que aporta el entorno de ejecucion de un
asistente de codigo) y falla. Con un pnpm global `11.9.0` o `11.1.3` el mensaje es
`This project is configured to use 9.0.0 of pnpm. Your current pnpm is v...`; con otras versiones el
sintoma puede ser distinto (con una `11.19.0` las tareas abortan con
`ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`). CI no lo sufre porque ejecuta `corepack enable` antes de
usar pnpm.

Una vez por maquina:

```powershell
corepack enable
```

- En Windows, ejecutalo en una consola de PowerShell **como administrador**: escribe en
  `C:\Program Files\nodejs`. No importa desde que carpeta lo lances. No imprime nada si funciona.
  Esta verificado en Windows; en macOS y Linux puede necesitar `sudo` segun donde este instalado Node.
- No hace falta desinstalar un pnpm global: el lanzador de corepack tiene prioridad si el directorio de
  Node va antes que el de npm global en el `PATH`. Comprueba el orden con `where.exe pnpm` (Windows) o
  `which -a pnpm` (macOS y Linux).
- Fuera del repositorio, `pnpm --version` pasara a mostrar la version por defecto de corepack y no la
  de tu pnpm global. No afecta al repositorio.

Para comprobar que funciona, desde la raiz y en una consola nueva:

```powershell
corepack pnpm exec pnpm --version
```

Debe imprimir exactamente `9.0.0`. Cualquier otra salida (el error de version de arriba, o una version
distinta como `11.x`) significa que falta `corepack enable` o que hay otro `pnpm` por delante en el
`PATH`, por ejemplo uno global de npm o uno que aporta el entorno de ejecucion de un asistente de
codigo; en ese ultimo caso `corepack enable` puede no bastar si su carpeta va antes que la de Node
(no verificado). Como salida de emergencia, `pnpm <script>` sin `corepack` funciona si
el pnpm global es lo bastante reciente para cambiar de version por si mismo (verificado con `11.9.0`),
pero no es la forma documentada y depende de lo que haya instalado en cada maquina.

turbo cachea los resultados sin tener en cuenta la version de pnpm. Si cambias la configuracion de la
maquina y quieres comprobar que los scripts funcionan de verdad, anade `--force` (por ejemplo
`corepack pnpm lint --force`): una ejecucion con `cache hit` no lanza ningun subproceso y no demuestra
nada. Origen: [RF-093-001](openspec/findings/backlog.md) y [JUP-103](docs/evidence/JUP-103-validation.md).

### Con Docker Compose

Desde la raiz de un clon limpio, con Docker y Node instalados (en Linux o macOS, el primer comando es `cp -n .env.example .env`):

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Completa en .env los secretos y opt-ins descritos en "Variables De Entorno".
corepack pnpm install --frozen-lockfile
corepack pnpm local:doctor
docker compose up -d --build --wait
corepack pnpm local:smoke
```

1. `.env.example` deja vacios los secretos a proposito: copiarlo no basta.
   Rellena los valores de [Variables De Entorno](#variables-de-entorno).
2. `corepack pnpm install --frozen-lockfile` instala las dependencias del workspace
   (`local:doctor` y `local:smoke` las necesitan; unos 36 s en un host de prueba).
   Despues, `local:doctor` revisa `.env` antes de arrancar y lista todo lo que falta:
   variables obligatorias de `docker-compose.yml` vacias, credenciales de
   `RABBITMQ_URL` y `VECTOR_DATABASE_URL` que no coinciden con las del servicio,
   valores que el backend rechazaria al arrancar (esquemas de las DSN,
   passwords de ejemplo o por defecto, `AUTH_SECRET_KEY` corta), el opt-in de
   la CockroachDB local, puertos del host ocupados y si la instalacion es nueva
   o existente. Resuelve `.env` como Compose (`${VAR}`, comillas, entorno
   primero). Nombra variables, nunca valores, y no crea ni modifica `.env`.
   Repitelo hasta que termine en `[OK]`.
   Limites conocidos: `[OK]` no garantiza que el backend arranque, porque no valida `DEMO_SEED_ENABLED`, `CORS_ALLOWED_ORIGINS`, `AUTH_TOKEN_TTL_MINUTES` ni los ajustes propios del processor; no entiende valores multilinea entre comillas ni los operadores `${VAR:+x}` y `${VAR:?msg}` de Compose; ante un listener solo en `::1` puede no ver el puerto ocupado; y los espacios en blanco poco comunes (`` a ``) se interpretan distinto que en el backend.
3. El primer arranque, con build y volumenes nuevos, tarda varios minutos
   (unos 8 en la validacion de JUP-050, de ellos unos 2 en las migraciones del
   processor); los siguientes, menos de 2. `--wait` termina cuando todos los
   servicios estan sanos.
4. `local:smoke` recorre el camino minimo: salud de las cuatro aplicaciones,
   login del usuario demo, una ingesta de costes del simulador, el resumen de
   costes con datos y un job de documento que pasa por RabbitMQ hasta el
   processor. Necesita `DEMO_SEED_ENABLED=true` y `DEMO_PASSWORD`, escribe datos
   de prueba en el tenant `tenant-core` y se puede repetir.

Las cuatro aplicaciones se construyen desde Dockerfiles versionados. Las
imagenes ejecutan como usuarios sin privilegios, con filesystem raiz de solo
lectura, `/tmp` temporal, `no-new-privileges` y healthchecks. Las dependencias
de infraestructura y las imagenes base estan fijadas por digest; una
actualizacion exige cambiar de forma explicita el tag y el digest en el mismo
pull request.

`VITE_API_BASE_URL` se incorpora al build del frontend. Si cambia, reconstruir
esa imagen antes de arrancarla:

```powershell
docker compose build frontend
docker compose up -d --wait frontend
```

Los puertos de CockroachDB, RabbitMQ y pgvector se enlazan exclusivamente a
loopback. `COCKROACH_SQL_PORT`, `COCKROACH_HTTP_PORT`, `RABBITMQ_PORT`,
`RABBITMQ_MANAGEMENT_PORT` y `PGVECTOR_PORT` permiten ejecutar proyectos
aislados sin colisionar con otro stack del mismo host.

Los puertos publicados de las aplicaciones se configuran por separado mediante
`API_HOST_PORT`, `PROCESSOR_HOST_PORT`, `FRONTEND_HOST_PORT` y
`AZURE_COST_API_HOST_PORT`. Los procesos conservan siempre sus puertos internos
8000, 8001, 5173 y 8002, por lo que cambiar un puerto del host no invalida su
healthcheck.

Para detener este entorno y conservar los volumenes de datos:

```powershell
docker compose down
```

| Comando | Que conserva | Que borra |
| --- | --- | --- |
| `docker compose stop` / `down` | Los volumenes con nombre: CockroachDB, pgvector, RabbitMQ (incluidos los mensajes que sigan en cola), Prometheus y Grafana | Los contenedores (`down`) |
| `docker compose down -v` | Nada del proyecto | Todos los volumenes: la siguiente vez es una instalacion nueva |

RabbitMQ guarda su estado en el volumen `rabbitmq-data` desde JUP-050. En una
instalacion anterior, el primer arranque crea ese volumen vacio: lo que hubiera
en el volumen anonimo previo no se migra. El cookie de Erlang sigue saliendo de
`RABBITMQ_ERLANG_COOKIE`, que prevalece sobre el guardado en el volumen.

El usuario y la password de RabbitMQ (`RABBITMQ_DEFAULT_USER` y `RABBITMQ_DEFAULT_PASS`) se fijan en el primer arranque del volumen: cambiarlos despues en `.env` no cambia los del broker, el stack sigue "sano" pero el backend y el processor no se autentican y los jobs responden 503. Lo mismo ocurre con `POSTGRES_PASSWORD` y `GRAFANA_ADMIN_PASSWORD`: conserva sus valores, o usa `docker compose down -v` en un entorno desechable, que borra todos los datos. Para cambiar solo las credenciales de RabbitMQ en un entorno desechable: `docker compose down`, `docker volume rm <proyecto>_rabbitmq-data` (se pierden los mensajes en cola) y `docker compose up -d --wait`; esa receta no cambia las de los otros servicios.

Puertos visibles:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Processor health: `http://localhost:8001/health`
- Azure Cost API: `http://localhost:8002/health`
- RabbitMQ Console: `http://localhost:15672`
- pgvector Postgres: `localhost:5433`
- Cockroach SQL: `localhost:26257`
- Cockroach Console: `http://localhost:8080`

### Con Turborepo

Necesita el [requisito previo de corepack](#requisito-previo-pnpm-con-corepack). Desde la raiz del repo,
preferiblemente dentro de un entorno virtual de Python (`turbo` usa el `python` que encuentra en el
`PATH`, asi que activalo en la misma consola que lanza pnpm):

```powershell
corepack pnpm install --frozen-lockfile
Set-Location apps/backend; python -m pip install -r requirements-dev.txt
Set-Location ../processor; python -m pip install -r requirements-dev.txt
Set-Location ../azure-cost-api; python -m pip install -r requirements-dev.txt
Set-Location ../..
```

`corepack pnpm dev` lanza en paralelo `frontend`, `backend`, `processor` y `azure-cost-api`. **Por si
solo no deja sirviendo al backend ni al processor**, y en cuanto uno falla turbo termina todos:
`backend` y `processor` leen su configuracion solo del entorno del proceso, y turbo (modo `strict`)
no le pasa a las tareas las variables del shell. Ademas, el `.env` de Compose usa los nombres
internos de los servicios (`cockroachdb`, `rabbitmq`, `postgres-pgvector`), que tu maquina no resuelve.
Para que queden las cuatro aplicaciones sirviendo (verificado en Windows):

1. Levanta solo la infraestructura de Compose, sin los servicios de aplicacion:
   `docker compose up -d --wait cockroachdb rabbitmq postgres-pgvector`.
2. Crea un archivo de entorno **fuera del repositorio**: copia de tu `.env` con `DATABASE_URL`,
   `RABBITMQ_URL` y `VECTOR_DATABASE_URL` apuntando a `127.0.0.1` y a los puertos publicados
   (`26257`, `5672` y `5433` por defecto, o los de `COCKROACH_SQL_PORT`, `RABBITMQ_PORT` y
   `PGVECTOR_PORT`). Usa `127.0.0.1` y no `localhost`: con `localhost` el backend se quedo bloqueado
   en el arranque en la maquina verificada (causa sin determinar).
3. Lanza `dev` indicando ese archivo y el modo de entorno `loose`:

```powershell
$env:ECONOMICON_ENV_FILE = "C:\ruta\fuera\del\repo\local-dev.env"
corepack pnpm dev --env-mode=loose
```

Es una limitacion conocida del repositorio, no de tu maquina; el seguimiento esta en
[RF-103-001](openspec/findings/backlog.md). Para el stack completo en contenedores, usa Docker Compose.

Puertos visibles:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Processor health: `http://localhost:8001/health`
- Azure Cost API: `http://localhost:8002/health`

### Individualmente

Puedes ejecutar cada submodulo por separado desde su propia carpeta:

- `apps/frontend`
- `apps/backend`
- `apps/processor`
- `apps/azure-cost-api`

Los detalles concretos estan explicados en los README de cada submodulo.

Puertos habituales:

- Frontend: `5173`
- Backend: `8000`
- Processor: `8001`
- Azure Cost API: `8002`

## Variables De Entorno

La Azure Cost API simulada exige por defecto el bearer local
`jupiter-local-token`, pagina resultados y permite activar fallos deterministas
con `X-Fake-Azure-Scenario`. Consulta `apps/azure-cost-api/README.md` para la
configuración completa; estos tokens son fixtures locales, no credenciales Azure.

Preparar `.env` local ignorado antes de arrancar el stack, sin sobrescribir uno existente (en Linux o macOS: `cp -n .env.example .env`):

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Variables principales:

Los campos secretos del ejemplo estan vacios: copiarlo no permite arrancar.
Preparar JWT (al menos 32 caracteres, generado externamente), credenciales
independientes de RabbitMQ y pgvector, y sus DSN con passwords URL-encoded.
`RABBITMQ_DEFAULT_USER/PASS` deben coincidir con `RABBITMQ_URL`;
`POSTGRES_PASSWORD` con `VECTOR_DATABASE_URL` (usuario `postgres`,
base `embeddings` en este Compose). No usar los defaults guest/guest o postgres.
RabbitMQ tambien exige `RABBITMQ_ERLANG_COOKIE` privado externo, sin fallback.
En una instalacion existente, el operador aporta el cookie privado ya usado;
una instalacion nueva requiere un valor privado externo. No se genera, rota
ni sustituye el cookie ni se modifican volumenes como parte de este cambio.
Consultar el [procedimiento del operador](docs/manuals/python-service-conventions.md#secretos-y-arranque).
Grafana exige `GRAFANA_ADMIN_PASSWORD`: trasladar su valor existente al
`.env` ignorado conservandolo, sin generar otro ni resetear cuenta/volumen.
La precedencia del entorno se conserva. Mover una password debil no la fortalece.

`RUNTIME_ENVIRONMENT` vale `production` por defecto y es independiente de
`AI_EXECUTION_MODE`. Este Compose contiene un CockroachDB sin autenticacion:
solo arranca con `RUNTIME_ENVIRONMENT=development|test` y
`ALLOW_INSECURE_LOCAL_DATABASE=true`, tras confirmar que el proyecto, datos
y puertos loopback son aislados y desechables. El opt-in esta apagado por
defecto y no autoriza uso compartido o produccion. El DSN local aprobado es
`cockroachdb+psycopg://root@cockroachdb:26257/defaultdb?sslmode=disable`;
para clientes nativos, usar el puerto publicado y un destino loopback exacto.
TLS y provisioning productivo requieren otro alcance.

Python no lee `.env` implicitamente. Para procesos nativos, seleccionar
`ECONOMICON_ENV_FILE` con la ruta absoluta a un fichero preparado para esos
clientes, o inyectar las variables directamente; el entorno tiene precedencia.
Compose lee su propio `.env` para interpolacion y pasa solo las variables
declaradas. No pasar secretos mediante `VITE_*`, ARG o ENV de imagen.
Los contextos Docker excluyen dotenv raiz/anidados y sus variantes.

El backend recibe `CORS_ALLOWED_ORIGINS` como lista JSON de origenes exactos.
Ausente o `[]` no concede acceso cross-origin; texto vacio, JSON mal formado,
`null`, comodines, regex o entradas no canonicas impiden arrancar con un error
generico sin mostrar el valor. Compose conserva un valor vacio como invalido.
Cada origen es `scheme://host[:port]`, sin ruta ni `/` final, credenciales,
query o fragmento; usar minusculas y omitir el puerto por defecto del esquema.
`production` exige HTTPS aportado por el operador. Para desarrollo local con
`RUNTIME_ENVIRONMENT=development` o `test`, el ejemplo es
`CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]`.
Ambos hosts son distintos y el puerto debe coincidir con el navegador: si
cambia `FRONTEND_HOST_PORT`, actualizar la lista y recrear el backend. No se
deriva del bind de Docker ni se cambia automaticamente el entorno production.

CORS permite GET/POST, Authorization, Content-Type, X-Tenant-Id y cabeceras
safelisted del framework; OPTIONS no requiere JWT, no habilita cookies ni
expone cabeceras adicionales y su max-age es 600 segundos. No sustituye la
autenticacion ni la autorizacion tenant. Las respuestas 200/401/403/422 y los
500 de ruta/DB sanitizados antes de headers son legibles desde un origen
permitido. Los 500 del middleware exterior, fallos de arranque y streaming
ya iniciado quedan fuera de esa garantia. El preflight termina antes de las
metricas y logs de acceso interiores; las peticiones reales los conservan.
Mas detalles en [el backend](apps/backend/README.md#cors-y-sesion-demo).

El seed demo esta desactivado. Activarlo exige `DEMO_SEED_ENABLED=true`
y `DEMO_PASSWORD` externa no heredada. El email sigue siendo
`operator@example.com`; introducir manualmente la password en el formulario.
En reinicios, el seed solo crea lo ausente y no sobrescribe passwords,
identidades ni roles existentes. Cambiar env no rota datos persistentes.
Consultar [configuracion y rotacion](docs/manuals/python-service-conventions.md)
antes de preparar una instalacion existente.

- `DATABASE_URL`: conexion hacia CockroachDB
- `RABBITMQ_URL`: conexion hacia RabbitMQ
- `VECTOR_DATABASE_URL`: conexion hacia PostgreSQL con pgvector
- `PROCESSOR_QUEUE_NAME`: nombre logico de la cola de jobs
- `AUTH_SECRET_KEY`: secreto para firmar tokens propios del backend
- `AUTH_TOKEN_TTL_MINUTES`: vida util del token
- `CORS_ALLOWED_ORIGINS`: lista JSON de origenes del navegador permitidos
- `EMBEDDING_PROVIDER`: provider de embeddings (`mock` solo con `RUNTIME_ENVIRONMENT=development` o `test`; `litellm` en el resto)
- `BACKEND_LITELLM_API_KEY`: clave virtual propia del backend, obligatoria solo con `EMBEDDING_PROVIDER=litellm`
- `EMBEDDING_TIMEOUT_SECONDS` y `EMBEDDING_MAX_RETRIES`: plazo y reintentos de la llamada de embedding del backend
- `RETRIEVAL_TOP_K` y `RETRIEVAL_MAX_DISTANCE`: fragmentos recuperados por pregunta (por defecto 4) y distancia coseno maxima (0.6 por defecto con `litellm`, sin umbral con `mock`)
- `VITE_API_BASE_URL`: URL base consumida por el frontend
- `LLM_PROVIDER`: provider configurado para el modulo de agentes

## Comandos Principales

Con el [requisito previo de corepack](#requisito-previo-pnpm-con-corepack) cumplido, `pnpm <script>` y
`corepack pnpm <script>` ejecutan lo mismo; el resto del documento usa `corepack pnpm` porque es la forma
que usan CI y la guia de contribucion.

- `pnpm dev`: lanza en paralelo el proceso de desarrollo de frontend, backend, processor y Azure Cost API
  (backend y processor necesitan configuracion adicional, ver "Con Turborepo")
- `pnpm build`: ejecuta las tareas de build declaradas por cada app
- `pnpm lint`: ejecuta las tareas de lint declaradas por cada app
- `pnpm typecheck`: ejecuta la verificacion de tipos; solo la declara el frontend
- `pnpm test`: ejecuta los tests disponibles. Con los cuatro paquetes a la vez, algunos tests con
  plazos de tiempo (frontend, backend y processor) pueden fallar segun la maquina, y no siempre los
  mismos (`RF-098-004`, `RF-103-005`); aislados y por mitades pasan. Si te ocurre, ejecutalos asi:
  `corepack pnpm run test "--filter=!@finops/frontend"` y
  `corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1`
- `pnpm docker:build`: construye las imagenes Docker de las apps
- `pnpm docker:validate`: valida topologia, digests, healthchecks y privilegios
  sin necesitar un daemon Docker
- `pnpm local:doctor`: diagnostica `.env`, puertos y volumenes antes de arrancar
  Compose, sin mostrar valores secretos
- `pnpm local:smoke`: verifica el recorrido minimo contra el stack ya arrancado
- `pnpm local:test`: tests de las dos herramientas anteriores

## Integracion Continua

El workflow [CI](.github/workflows/ci.yml) se ejecuta con cada push a cualquier
rama (`branches: ['**']`, sin filtros de rutas), con pull requests hacia `main`
o `develop` en eventos `opened`, `synchronize`, `reopened`, `edited` y
`ready_for_review`, y manualmente mediante `workflow_dispatch`. Un push solo
de tags no lo activa. No requiere configurar `.gitconfig` ni hooks locales.

Cada push valida el ultimo head enviado: los commits locales sin push y los
commits intermedios de un push multiple no tienen ejecuciones individuales.
Una ejecucion posterior del mismo grupo de concurrencia puede cancelar la
anterior. Con un PR abierto pueden ejecutarse tanto el evento push como el
evento PR; sus refs normalmente pertenecen a grupos distintos.

Los jobs instalan las dependencias del workspace con
`corepack pnpm install --frozen-lockfile` y ejecutan:

- Frontend: `corepack pnpm lint --filter=@finops/frontend`,
  `corepack pnpm test --filter=@finops/frontend`,
  `corepack pnpm --filter @finops/frontend build` y, en otro job,
  `corepack pnpm --filter @finops/frontend typecheck`.
- Python 3.12: en cada directorio `apps/azure-cost-api`, `apps/backend` y
  `apps/processor`, `python -m pip install -r requirements-dev.txt`, despues
  `python -m compileall -q app` y finalmente `python -m pytest tests -q`.
  Compileall cubre una sola vez los scripts identicos de lint/build; un error
  de sintaxis falla el job. Comprueba sintaxis y genera bytecode, pero no
  comprueba estilo, imports en runtime ni construye paquetes.
- Gobernanza: los comandos del job `OpenSpec` en el workflow enlazado,
  incluidos `corepack pnpm ci:check:test`, `corepack pnpm jup:check:all`,
  `corepack pnpm docker:validate` y `corepack pnpm openspec:validate`.
- Solo en PR: `node tools/pr-policy.mjs --event "$GITHUB_EVENT_PATH"`.
  Este job se omite en push y ejecuciones manuales.

Los tests que requieren CockroachDB, RabbitMQ o pgvector aislados pueden
quedar omitidos si esos servicios no estan disponibles. Esos skips no validan
integraciones reales. `docker:validate` es una comprobacion estatica; CI verde
no acredita arranque de contenedores, despliegue ni aceptacion humana. Los
tests locales del workflow tampoco acreditan ejecuciones alojadas en GitHub.

## Planificacion de entrega

El roadmap versionado hasta la entrega del 23/10/2026 y la defensa del
29/10/2026 se mantiene en
[`docs/planning/JUP-080-delivery-roadmap.md`](docs/planning/JUP-080-delivery-roadmap.md).
Trello conserva el estado operativo; las fechas masivas solo se aplican despues
de que el equipo apruebe el plan.

## Colaboracion

El repositorio canonico es `EconomiconFinOps/tfm-economicon`. Todo cambio nace
en una tarjeta Trello `JUP-XXX`, se desarrolla en una rama corta desde
`develop` y se integra mediante pull request. Consulta [CONTRIBUTING.md](CONTRIBUTING.md)
y [la estrategia de repositorio y ramas](docs/governance/repository-and-branch-strategy.md)
antes de comenzar una tarea.

## Relacion Entre Submodulos

El flujo principal del sistema es este:

1. El usuario entra en `frontend`
2. `frontend` llama al `backend`
3. `backend` autentica al usuario, resuelve su `tenant_id` activo y guarda datos operativos en `CockroachDB`
4. `backend` publica jobs en `RabbitMQ`
5. `processor` consume esos jobs
6. `processor` genera embeddings y los guarda en `Postgres + pgvector`
7. `backend` recupera contexto vectorial filtrado por tenant para responder en el chat
8. `processor` actualiza el estado del job en `CockroachDB`

## Documentacion Util

- [Arquitectura](docs/architecture.md)
- [Manual de Turborepo](docs/manuals/turborepo_use.md)
- [Dataset público de Azure](docs/data/azure-sample-dataset.md)
- [Contrato Azure Cost Management Query](docs/api/azure-cost-query-contract.md)
- [OpenAPI contractual](docs/api/azure-cost-query.openapi.json)
- [API Azure Cost simulada](apps/azure-cost-api/README.md)
- [Cliente de ingesta Azure Cost Management](docs/api/azure-cost-ingestion-client.md)
- [Batería de preguntas FinOps (JUP-069)](docs/validation/README.md)

## Estado Actual

Esta base prioriza:

- estructura clara del monorepo
- separacion simple de responsabilidades
- auth minima propia
- contexto de tenant obligatorio
- migraciones formales para CockroachDB y pgvector
- persistencia operativa
- cola local para jobs
- API Azure Cost simulada y cliente de ingesta paginado
- normalizacion y persistencia idempotente de costes por tenant
- almacenamiento vectorial basico con provider mock por defecto en development y test, y recuperacion semantica del backend con `litellm` (ver [apps/backend/README.md](apps/backend/README.md))
- chat con retrieval minimo por tenant y respuesta determinista, todavia sin LLM real
- CI en GitHub Actions con validaciones de gobernanza, OpenSpec, pruebas y build
- documentacion versionada de arquitectura, ADR, roadmap y evidencias

No incluye todavia:

- despliegue continuo hacia `dockerserver`
- despliegue cloud
- observabilidad avanzada
- autenticacion con IdP externo
- vertical RAG con embeddings y LLM reales validado de extremo a extremo

Los contratos residuales de autenticacion demo, aislamiento completo por tenant
y calidad minima del frontend se mantienen en JUP-085, JUP-086 y JUP-087. Que
exista un prototipo o un provider mock no acredita el cierre de esas tarjetas.
