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

### Con Docker Compose

Desde la raiz de un clon limpio, con Docker y Node instalados:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Completa en .env los secretos y opt-ins descritos en "Variables De Entorno".
corepack pnpm local:doctor
docker compose up -d --build --wait
corepack pnpm local:smoke
```

1. `.env.example` deja vacios los secretos a proposito: copiarlo no basta.
   Rellena los valores de [Variables De Entorno](#variables-de-entorno).
2. `local:doctor` revisa `.env` antes de arrancar y lista todo lo que falta:
   variables obligatorias de `docker-compose.yml` vacias, credenciales de
   `RABBITMQ_URL` y `VECTOR_DATABASE_URL` que no coinciden con las del servicio,
   `AUTH_SECRET_KEY` corta, el opt-in de la CockroachDB local, puertos del host
   ocupados y si la instalacion es nueva o existente. Nombra variables, nunca
   valores, y no crea ni modifica `.env`. Repitelo hasta que termine en `[OK]`.
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

Desde la raiz del repo:

```powershell
pnpm install
Set-Location apps/backend; python -m pip install -r requirements-dev.txt
Set-Location ../processor; python -m pip install -r requirements-dev.txt
Set-Location ../azure-cost-api; python -m pip install -r requirements-dev.txt
Set-Location ../..
pnpm dev
```

Esto levanta `frontend`, `backend`, `processor` y `azure-cost-api` en paralelo.

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

Preparar `.env` local ignorado antes de arrancar el stack, sin sobrescribir uno existente:

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
- `EMBEDDING_PROVIDER`: provider configurado para embeddings
- `VITE_API_BASE_URL`: URL base consumida por el frontend
- `LLM_PROVIDER`: provider configurado para el modulo de agentes

## Comandos Principales

- `pnpm dev`: arranca frontend, backend, processor y Azure Cost API en paralelo
- `pnpm build`: ejecuta las tareas de build declaradas por cada app
- `pnpm lint`: ejecuta las tareas de lint declaradas por cada app
- `pnpm test`: ejecuta los tests disponibles
- `pnpm docker:build`: construye las imagenes Docker de las apps
- `pnpm docker:validate`: valida topologia, digests, healthchecks y privilegios
  sin necesitar un daemon Docker
- `pnpm local:doctor`: diagnostica `.env`, puertos y volumenes antes de arrancar
  Compose, sin mostrar valores secretos
- `pnpm local:smoke`: verifica el recorrido minimo contra el stack ya arrancado
- `pnpm local:test`: tests de las dos herramientas anteriores

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
- almacenamiento vectorial basico con provider mock por defecto
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
