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

Requiere preparar primero los secretos y la excepcion local del
[README raiz](../../README.md#variables-de-entorno). Copiar el ejemplo vacio
no basta; no sobrescribir un `.env` existente.

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
$env:ECONOMICON_ENV_FILE = (Resolve-Path ../../.env).Path
python -m app.run --reload
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
- `RUNTIME_ENVIRONMENT`
- `CORS_ALLOWED_ORIGINS`

## CORS Y Sesion Demo

`CORS_ALLOWED_ORIGINS` es una lista JSON, vacia por defecto (`[]`). Ausente
no concede acceso cross-origin; una cadena vacia no equivale a `[]` y Compose
la conserva para que falle la validacion. El arranque rechaza JSON invalido,
tipos incorrectos, `null`, comodines, regex y origenes no canonicos mediante
`StartupError` generico sin mostrar el input.

Usar origenes exactos `scheme://host[:port]`, en minusculas, sin puerto por
defecto del esquema, `/` final, path, credenciales, query ni fragmento.
En `production` se exige HTTPS y el operador aporta los origenes. Solo en
`development`/`test` se permite HTTP, por ejemplo
`CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]`.
Son hosts distintos; ajustar el puerto al `FRONTEND_HOST_PORT` que realmente
usa el navegador y recrear el backend. El bind de Docker no configura CORS.
El ejemplo mantiene `production` y `[]` por defecto.

La politica permite GET/POST y Authorization, Content-Type, X-Tenant-Id junto
a las cabeceras safelisted del framework. OPTIONS termina sin consultar JWT,
usuarios o tenants; max-age 600, sin permisos de cookies y sin cabeceras
expuestas adicionales. CORS no sustituye JWT ni autorizacion tenant: una
peticion simple de origen denegado puede ejecutarse sin Allow-Origin.

Settings se carga al construir la pila ASGI, conservando el import sin
secretos y la API FastAPI/state/overrides/lifespan. Orden: ServerError > CORS >
Metrics > RequestId > rutas. Un origen permitido recibe Allow-Origin exacto
y Vary: Origin en 200/401/403/422 y 500 de ruta/DB sanitizado antes de headers.
No se garantiza CORS en 500 producido fuera de esa capa, fallo de arranque o
streaming ya iniciado. Preflight no pasa por metricas/logs de acceso interiores;
las peticiones reales conservan ambos.

El cliente valida storage, login y el perfil directo de `/me`; consulta `/me`
y `/tenants` en paralelo tambien tras login. Cualquier error de la query
`/me`, incluso transitorio, cierra la sesion sin cambiar retries/refetch.
Fuera de `/me`, un 401 autenticado vigente limpia sesion, tenant y caches
antes de leer el body; otros errores conservan la sesion. Logout es local:
no revoca JWT en servidor. Las respuestas de generaciones abandonadas se
descartan, incluso con el mismo token/usuario. Estas pruebas no sustituyen
QA con navegador real en el stack canonico.

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

`GET /billing/summary` devuelve hoy `monthly_spend` y `savings_identified` con valores fijos de
demostracion; solo `open_ingestions` se calcula de verdad. No lee las tablas de coste Azure que
alimenta el `processor` (`azure_cost_ingestion_runs`, `azure_cost_records`). Verificado en JUP-091:
ver `RF-091-004` en `openspec/findings/backlog.md`.

La cuenta demo solo se crea con `DEMO_SEED_ENABLED=true` y una
`DEMO_PASSWORD` externa no heredada:

- email: `operator@example.com`
- password: introducir manualmente el valor configurado para una cuenta nueva.

El seed esta apagado por defecto. Una cuenta existente conserva hash,
identidad y roles; cambiar `DEMO_PASSWORD` no los actualiza. Si el arranque
detecta la password demo heredada fuera de test, se detiene incluso con el
seed apagado. Aplicar la [rotacion manual parametrizada](../../docs/manuals/python-service-conventions.md#rotacion-de-la-cuenta-demo)
sin borrar usuarios o volumenes.

`AUTH_SECRET_KEY`, `DATABASE_URL`, `RABBITMQ_URL` y
`VECTOR_DATABASE_URL` son obligatorias, tambien en test. Python solo carga
dotenv al seleccionar `ECONOMICON_ENV_FILE`; el entorno prevalece. Adaptar
los hosts/puertos del fichero para clientes nativos. La configuracion valida
antes de construir recursos; el import no conecta. Las fixtures de pytest
aportan credenciales sinteticas explicitas y no necesitan servicios reales.

## Notas

- Convenciones de código Python (logging, etc.): ver `docs/manuals/python-service-conventions.md`.
- `db/database.py` encapsula el acceso a CockroachDB y ejecuta migraciones.
- `services/rabbitmq_queue.py` publica jobs hacia el `processor`.
- `services/vector_store.py` consulta el contexto vectorial en pgvector.
- `api/routes/` agrupa la superficie REST.
