# Processor

Servicio asíncrono encargado de consumir jobs, ejecutar pipelines LangGraph y producir artefactos operativos.

## Responsabilidades

- consumir jobs desde RabbitMQ
- actualizar estados de ejecución en CockroachDB
- ejecutar pipelines de ingestión
- generar resúmenes e insights mediante el módulo interno `agents`
- exponer healthcheck básico del runtime

## Estructura

```text
apps/processor
|-- app/
|   |-- agents/
|   |-- clients/
|   |-- core/
|   |-- db/
|   |-- graphs/
|   |-- repositories/
|   |-- tasks/
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
- `LLM_PROVIDER`
- `OPENAI_API_KEY`

## Instalación

```powershell
python -m pip install -r requirements-dev.txt
```

## Ejecución Local

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
docker run --rm -p 8001:8001 --env PROCESSOR_PORT=8001 --env DATABASE_URL=postgresql+psycopg://root@localhost:26257/defaultdb?sslmode=disable --env RABBITMQ_URL=amqp://guest:guest@localhost:5672/%2F finops-processor
```

## Arquitectura

- `workers/runner.py` consume la cola de RabbitMQ.
- `tasks/ingest.py` encapsula la lógica de ejecución de jobs.
- `graphs/pipeline.py` define el flujo LangGraph.
- `agents/` encapsula prompts, providers y lógica LangChain interna.
