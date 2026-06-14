# FinOps Assistant Monorepo

Monorepo base para un asistente FinOps con `Turborepo`, `pnpm`, `pip`, `Docker Compose`, `RabbitMQ` y `CockroachDB`.

## Arquitectura

- `apps/frontend`: dashboard React para operadores y usuarios.
- `apps/backend`: API principal en FastAPI para auth, tenants, billing y publicación de jobs.
- `apps/processor`: servicio Python para orquestación de pipelines, ingestión y ejecución de agentes internos.
- `apps/processor/app/agents`: módulo interno LangChain para razonamiento LLM y generación de insights.
- `packages/shared-config`: paquete reservado para utilidades y convenciones compartidas del workspace JS.

## Flujo Entre Servicios

1. El `frontend` consume la API HTTP expuesta por `backend`.
2. El `backend` persiste metadata operativa en CockroachDB.
3. El `backend` publica jobs en RabbitMQ para procesamiento asíncrono.
4. El `processor` consume la cola, ejecuta el grafo de trabajo y actualiza resultados en CockroachDB.
5. El módulo interno `agents` aporta generación de insights y resúmenes FinOps dentro del `processor`.

## Estructura

```text
.
|-- apps/
|   |-- backend/
|   |-- frontend/
|   `-- processor/
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

- `DATABASE_URL`: conexión SQLAlchemy/psycopg hacia CockroachDB.
- `RABBITMQ_URL`: URL de RabbitMQ usada por backend y processor.
- `VITE_API_BASE_URL`: base URL consumida por el frontend.
- `PROCESSOR_QUEUE_NAME`: nombre lógico de la cola de jobs.
- `LLM_PROVIDER`: provider configurado para el módulo interno de agentes.

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
- Cockroach SQL: `localhost:26257`
- Cockroach Console: `http://localhost:8080`

### Orquestación con Turborepo

Instalar dependencias JS del workspace:

```powershell
pnpm install
```

Instalar dependencias Python por servicio:

```powershell
Set-Location apps/backend; python -m pip install -r requirements-dev.txt
Set-Location ../processor; python -m pip install -r requirements-dev.txt
```

Volver a la raíz y ejecutar:

```powershell
Set-Location ../..
pnpm dev
```

## Comandos Principales

- `pnpm dev`: arranca frontend, backend y processor en paralelo.
- `pnpm build`: ejecuta las tareas de build declaradas por cada app.
- `pnpm test`: ejecuta los tests disponibles.
- `pnpm docker:build`: construye las imágenes Docker de las apps.

## Estado De La V1

Esta base prioriza:

- estructura clara del monorepo
- contratos iniciales entre servicios
- persistencia y cola local
- documentación suficiente para arrancar sin pasos implícitos

No incluye todavía:

- CI/CD
- migraciones formales
- despliegue cloud
- observabilidad avanzada
- autenticación real con identidad externa
