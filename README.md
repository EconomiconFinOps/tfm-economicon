# FinOps Assistant Monorepo

Monorepo base para un asistente FinOps con `Turborepo`, `pnpm`, `pip`, `Docker Compose`, `RabbitMQ`, `CockroachDB` y `Postgres + pgvector`.

## Arquitectura

- `apps/frontend`: dashboard React para operadores y usuarios.
- `apps/backend`: API principal en FastAPI para auth, tenants, billing y publicacion de jobs.
- `apps/processor`: servicio Python para orquestacion de pipelines, ingestion, embeddings y ejecucion de agentes internos.
- `apps/processor/app/agents`: modulo interno LangChain para razonamiento LLM y generacion de insights.
- `packages/shared-config`: paquete reservado para utilidades y convenciones compartidas del workspace JS.

## Flujo Entre Servicios

1. El `frontend` consume la API HTTP expuesta por `backend`.
2. El `backend` persiste metadata operativa en CockroachDB.
3. El `backend` publica jobs en RabbitMQ para procesamiento asincrono.
4. El `processor` consume la cola, ejecuta el grafo de trabajo, persiste embeddings en `Postgres + pgvector` y actualiza resultados en CockroachDB.
5. El modulo interno `agents` aporta generacion de insights y resumenes FinOps dentro del `processor`.

## Estructura

```text
.
|-- apps/
|   |-- backend/
|   |-- frontend/
|   `-- processor/
|-- docs/
|   |-- architecture/
|   `-- use/
|-- packages/
|   `-- shared-config/
|-- docker-compose.yml
|-- package.json
|-- pnpm-workspace.yaml
`-- turbo.json
```

## Requisitos

- `pnpm` 9+
- `Docker` y `Docker Compose`
- `Python` 3.12
- `Node.js` 20

## Variables De Entorno

Copiar `.env.example` a `.env` antes de arrancar el stack:

```powershell
Copy-Item .env.example .env
```

Variables principales:

- `DATABASE_URL`: conexion SQLAlchemy/psycopg hacia CockroachDB.
- `RABBITMQ_URL`: URL de RabbitMQ usada por backend y processor.
- `VECTOR_DATABASE_URL`: conexion hacia PostgreSQL con pgvector para embeddings.
- `PROCESSOR_QUEUE_NAME`: nombre logico de la cola de jobs.
- `EMBEDDING_PROVIDER`: provider configurado para generar embeddings.
- `VITE_API_BASE_URL`: base URL consumida por el frontend.
- `LLM_PROVIDER`: provider configurado para el modulo interno de agentes.

## Desarrollo Local

### Todo el stack con Docker Compose

```powershell
docker compose up --build
```

Puertos por defecto:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Processor health: `http://localhost:8001/health`
- RabbitMQ Console: `http://localhost:15672`
- pgvector Postgres: `localhost:5433`
- Cockroach SQL: `localhost:26257`
- Cockroach Console: `http://localhost:8080`

### Orquestacion con Turborepo

Instalar dependencias JS del workspace:

```powershell
pnpm install
```

Instalar dependencias Python por servicio:

```powershell
Set-Location apps/backend; python -m pip install -r requirements-dev.txt
Set-Location ../processor; python -m pip install -r requirements-dev.txt
```

Volver a la raiz y ejecutar:

```powershell
Set-Location ../..
pnpm dev
```

## Comandos Principales

- `pnpm dev`: arranca frontend, backend y processor en paralelo.
- `pnpm build`: ejecuta las tareas de build declaradas por cada app.
- `pnpm test`: ejecuta los tests disponibles.
- `pnpm docker:build`: construye las imagenes Docker de las apps.

## Estado De La V1

Esta base prioriza:

- estructura clara del monorepo
- contratos iniciales entre servicios
- persistencia operativa, cola local y almacenamiento vectorial basico
- documentacion suficiente para arrancar sin pasos implicitos

No incluye todavia:

- CI/CD
- migraciones formales
- despliegue cloud
- observabilidad avanzada
- autenticacion real con identidad externa
