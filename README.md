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
|   `-- turborepo_use.md
|-- packages/
|   `-- shared-config/
|-- docker-compose.yml
|-- package.json
|-- pnpm-workspace.yaml
`-- turbo.json
```

## Como correrlo

### Con Docker Compose

Desde la raiz del repo:

```powershell
docker compose up --build
```

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
Set-Location ../..
pnpm dev
```

Esto levanta `frontend`, `backend` y `processor` en paralelo.

Puertos visibles:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Processor health: `http://localhost:8001/health`

### Individualmente

Puedes ejecutar cada submodulo por separado desde su propia carpeta:

- `apps/frontend`
- `apps/backend`
- `apps/processor`

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

Copiar `.env.example` a `.env` antes de arrancar el stack:

```powershell
Copy-Item .env.example .env
```

Variables principales:

- `DATABASE_URL`: conexion hacia CockroachDB
- `RABBITMQ_URL`: conexion hacia RabbitMQ
- `VECTOR_DATABASE_URL`: conexion hacia PostgreSQL con pgvector
- `PROCESSOR_QUEUE_NAME`: nombre logico de la cola de jobs
- `AUTH_SECRET_KEY`: secreto para firmar tokens propios del backend
- `AUTH_TOKEN_TTL_MINUTES`: vida util del token
- `EMBEDDING_PROVIDER`: provider configurado para embeddings
- `VITE_API_BASE_URL`: URL base consumida por el frontend
- `LLM_PROVIDER`: provider configurado para el modulo de agentes

## Comandos Principales

- `pnpm dev`: arranca frontend, backend y processor en paralelo
- `pnpm build`: ejecuta las tareas de build declaradas por cada app
- `pnpm lint`: ejecuta las tareas de lint declaradas por cada app
- `pnpm test`: ejecuta los tests disponibles
- `pnpm docker:build`: construye las imagenes Docker de las apps

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

## Estado Actual

Esta base prioriza:

- estructura clara del monorepo
- separacion simple de responsabilidades
- auth minima propia
- contexto de tenant obligatorio
- migraciones formales para CockroachDB y pgvector
- persistencia operativa
- cola local para jobs
- almacenamiento vectorial basico
- chat con retrieval minimo por tenant
- documentacion suficiente para arrancar el proyecto

No incluye todavia:

- CI/CD
- despliegue cloud
- observabilidad avanzada
- autenticacion con IdP externo
