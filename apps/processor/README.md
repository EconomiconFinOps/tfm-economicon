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
- `python -m app.run_azure_cost_ingestion --tenant-id <tenant> --subscription-id <subscription>`

La ingesta de Azure Cost recorre todas las páginas, normaliza el coste y las
dimensiones y persiste una ejecución reproducible en CockroachDB. Una segunda
ejecución con la misma combinación de tenant, suscripción y consulta reemplaza
atómicamente sus filas en vez de duplicarlas.

## Variables De Entorno

- `PROCESSOR_PORT`
- `PROCESSOR_CONCURRENCY`
- `PROCESSOR_QUEUE_NAME`
- `DATABASE_URL`
- `RABBITMQ_URL`
- `VECTOR_DATABASE_URL`
- `EMBEDDING_PROVIDER`
- `EMBEDDING_DIMENSION`
- `EMBEDDING_MODEL`
- `EMBEDDING_CHUNK_SIZE`
- `EMBEDDING_CHUNK_OVERLAP`
- `LLM_PROVIDER`
- `LLM_MODEL`
- `AI_EXECUTION_MODE`
- `LITELLM_BASE_URL`
- `LITELLM_API_KEY`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_RETRIES`
- `LLM_MAX_OUTPUT_TOKENS`
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

- Convenciones de código Python (logging, etc.): ver `docs/manuals/python-service-conventions.md`.
- `workers/runner.py` consume la cola de RabbitMQ.
- `db/migration_runner.py` y `vector_store/migrations/` aplican migraciones formales.
- `embeddings/` encapsula chunking y providers de embeddings.
- `vector_store/pgvector_store.py` persiste documentos, chunks y vectores.
- `graphs/pipeline.py` define el flujo de procesamiento.
- `clients/azure_cost.py` consume todas las páginas de Azure Cost Management,
  valida `columns/rows`, aplica reintentos acotados y evita reenviar el bearer a
  otro origen, ruta, versión contractual o redirección HTTP.
- `tasks/azure_cost_ingest.py`, `normalization/azure_cost.py` y
  `repositories/azure_cost.py` implementan el recorrido API → normalización →
  persistencia. Las tablas son `azure_cost_ingestion_runs` y
  `azure_cost_records`. JUP-013 promueve las dimensiones FinOps conocidas a
  columnas tipadas y conserva el resto en JSON; consulta
  [`docs/architecture/azure-cost-normalization.md`](../../docs/architecture/azure-cost-normalization.md).
- `docs/api/azure-cost-ingestion-client.md` describe configuración, errores,
  observabilidad y límites del cliente sin requerir un tenant Azure.
