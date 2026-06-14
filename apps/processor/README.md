# Processor

Servicio asincrono encargado de consumir jobs, ejecutar pipelines LangGraph, generar embeddings y producir artefactos operativos.

## Responsabilidades

- consumir jobs desde RabbitMQ
- actualizar estados de ejecucion en CockroachDB
- generar chunks y embeddings desde `text_content`
- persistir embeddings en Postgres con pgvector
- ejecutar pipelines de ingestion
- generar resumenes e insights mediante el modulo interno `agents`
- exponer healthcheck basico del runtime

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

## Instalacion

```powershell
python -m pip install -r requirements-dev.txt
```

## Ejecucion Local

```powershell
python -m app.run_all
```

## Tests

```powershell
python -m pytest tests
```

## Docker

```powershell
docker build -t finops-processor .
docker run --rm -p 8001:8001 --env PROCESSOR_PORT=8001 --env DATABASE_URL=postgresql+psycopg://root@localhost:26257/defaultdb?sslmode=disable --env RABBITMQ_URL=amqp://guest:guest@localhost:5672/%2F --env VECTOR_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/embeddings finops-processor
```

## Arquitectura

- `workers/runner.py` consume la cola de RabbitMQ.
- `embeddings/` encapsula chunking y providers de embeddings.
- `vector_store/pgvector_store.py` persiste documentos, chunks y vectores.
- `tasks/ingest.py` encapsula la logica de ejecucion de jobs.
- `graphs/pipeline.py` define el flujo LangGraph.
- `agents/` encapsula prompts, providers y logica LangChain interna.
