# Processor

## Descripcion

`apps/processor` es el servicio de trabajo en segundo plano.

Consume jobs desde RabbitMQ, ejecuta el pipeline de ingestion, genera chunks y embeddings desde `text_content`, guarda los vectores en `Postgres + pgvector` y actualiza el estado del job en CockroachDB.

Responsabilidades principales:

- consumir jobs desde RabbitMQ
- ejecutar pipelines de ingestion
- generar chunks
- generar embeddings
- persistir embeddings en pgvector
- producir insights y resumenes
- actualizar estados de ejecucion

## Stack

- `Python`
- `FastAPI`
- `LangGraph`
- `LangChain`
- `RabbitMQ`
- `CockroachDB`
- `Postgres + pgvector`

## Estructura

```text
apps/processor
|-- app/
|   |-- agents/
|   |-- api/
|   |-- clients/
|   |-- core/
|   |-- db/
|   |-- embeddings/
|   |-- graphs/
|   |-- repositories/
|   |-- tasks/
|   |-- vector_store/
|   `-- workers/
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
docker compose up --build processor
```

Puerto visible:

- `http://localhost:8001/health`

### Con Turborepo

Desde la raiz del repo:

```powershell
pnpm dev
```

Esto levanta `frontend`, `backend` y `processor` a la vez.

Puerto visible del processor:

- `http://localhost:8001/health`

### Individualmente

Desde `apps/processor`:

```powershell
python -m pip install -r requirements-dev.txt
python -m app.run_all
```

Puerto visible:

- `http://localhost:8001/health`

Entry points adicionales:

- `python -m app.run_worker`
- `python -m app.run_api`

## Variables De Entorno

- `PROCESSOR_PORT`
- `PROCESSOR_CONCURRENCY`
- `PROCESSOR_QUEUE_NAME`
- `DATABASE_URL`
- `RABBITMQ_URL`
- `VECTOR_DATABASE_URL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_DIMENSION`
- `EMBEDDING_CHUNK_SIZE`
- `EMBEDDING_CHUNK_OVERLAP`
- `LLM_PROVIDER`
- `OPENAI_API_KEY`
- `AZURE_COST_API_BASE_URL`
- `AZURE_COST_API_TOKEN`
- `AZURE_COST_API_VERSION`
- `AZURE_COST_API_TIMEOUT_SECONDS`
- `AZURE_COST_API_MAX_RETRIES`
- `AZURE_COST_API_RETRY_BACKOFF_SECONDS`
- `AZURE_COST_API_MAX_RETRY_AFTER_SECONDS`
- `AZURE_COST_API_MAX_PAGES`

## Tests

```powershell
python -m pytest tests
```

## Notas

- `workers/runner.py` consume la cola de RabbitMQ.
- `db/migration_runner.py` y `vector_store/migrations/` aplican migraciones formales.
- `embeddings/` encapsula chunking y providers de embeddings.
- `vector_store/pgvector_store.py` persiste documentos, chunks y vectores.
- `graphs/pipeline.py` define el flujo de procesamiento.
- `clients/azure_cost.py` consume todas las páginas de Azure Cost Management,
  valida `columns/rows`, aplica reintentos acotados y evita reenviar el bearer a
  un `nextLink` de otro origen.
