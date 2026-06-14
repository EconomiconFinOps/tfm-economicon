# Backend

API principal del sistema FinOps, construida con FastAPI.

## Responsabilidades

- healthcheck del stack
- autenticación base
- gestión inicial de tenants
- resumen de billing
- creación de jobs de ingesta
- persistencia en CockroachDB
- publicación de jobs en RabbitMQ

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

## Variables De Entorno

- `API_PORT`
- `DATABASE_URL`
- `RABBITMQ_URL`
- `PROCESSOR_QUEUE_NAME`

## Instalación

```powershell
python -m pip install -r requirements-dev.txt
```

## Ejecución Local

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Tests

```powershell
python -m pytest tests
```

## Docker

```powershell
docker build -t finops-backend .
docker run --rm -p 8000:8000 --env API_PORT=8000 --env DATABASE_URL=postgresql+psycopg://root@localhost:26257/defaultdb?sslmode=disable --env RABBITMQ_URL=amqp://guest:guest@localhost:5672/%2F finops-backend
```

## Endpoints Iniciales

- `GET /health`
- `POST /auth/login`
- `GET /me`
- `GET /tenants`
- `GET /billing/summary`
- `POST /jobs/ingest`

## Arquitectura

- `core/config.py` centraliza configuración.
- `db/database.py` encapsula acceso SQLAlchemy y bootstrap de tablas.
- `services/rabbitmq_queue.py` publica jobs hacia el processor.
- `api/routes/` agrupa la superficie REST por dominio.
