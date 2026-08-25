# Backend

## Descripcion

`apps/backend` es la API principal del sistema.

Su trabajo es recibir peticiones HTTP, validar datos, guardar informacion operativa en CockroachDB y publicar jobs en RabbitMQ para que el `processor` los ejecute en segundo plano.

Responsabilidades principales:

- healthcheck del stack
- autenticacion propia minima con token
- gestion inicial de tenants
- resumen de billing
- creacion de jobs de ingesta
- conversaciones y chat con retrieval
- persistencia operativa
- publicacion de jobs asincronos

## Stack

- `Python`
- `FastAPI`
- `SQLAlchemy`
- `CockroachDB`
- `RabbitMQ`
- `Pydantic`
- `PyJWT`

## Estructura

```text
apps/backend
|-- app/
|   |-- api/
|   |-- core/
|   |-- db/
|   |-- models/
|   |-- schemas/
|   `-- services/
|-- tests/
|-- Dockerfile
|-- package.json
|-- requirements.txt
`-- requirements-dev.txt
```

## Como correrlo

### Con Docker Compose

Desde la raiz del repo:

```powershell
docker compose up --build backend
```

Puerto visible:

- `http://localhost:8000`

### Con Turborepo

Desde la raiz del repo:

```powershell
pnpm dev
```

Esto levanta `frontend`, `backend` y `processor` a la vez.

Puerto visible del backend:

- `http://localhost:8000`

### Individualmente

Desde `apps/backend`:

```powershell
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Puerto visible:

- `http://localhost:8000`

## Variables De Entorno

- `API_PORT`
- `DATABASE_URL`
- `RABBITMQ_URL`
- `VECTOR_DATABASE_URL`
- `PROCESSOR_QUEUE_NAME`
- `EMBEDDING_DIMENSION`
- `AUTH_SECRET_KEY`
- `AUTH_TOKEN_TTL_MINUTES`

## Tests

```powershell
python -m pytest tests
```

## Endpoints Iniciales

- `GET /health`
- `POST /auth/login`
- `GET /me`
- `GET /tenants`
- `GET /billing/summary`
- `POST /jobs/ingest`
- `GET /assistant/conversations`
- `POST /assistant/conversations`
- `GET /assistant/conversations/{conversation_id}`
- `POST /assistant/conversations/{conversation_id}/messages`

`POST /jobs/ingest` requiere `text_content` como fuente principal del pipeline de embeddings.

La cuenta seed local para pruebas es:

- email: `operator@example.com`
- password: `secret`

## Notas

- `db/database.py` encapsula el acceso a CockroachDB y ejecuta migraciones.
- `services/rabbitmq_queue.py` publica jobs hacia el `processor`.
- `services/vector_store.py` consulta el contexto vectorial en pgvector.
- `api/routes/` agrupa la superficie REST.
