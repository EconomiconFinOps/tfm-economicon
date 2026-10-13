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

Preparar los secretos y la excepcion local del [README raiz](../../README.md#variables-de-entorno).
El ejemplo deja las credenciales vacias y no permite arrancar por si solo.

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
$env:ECONOMICON_ENV_FILE = (Resolve-Path ../../.env).Path
python -m app.run_all
```

La tabla `jobs` la crea el backend. `GET /health` del processor solo comprueba sus propias dependencias, asi que no depende de que el backend haya migrado.

Puerto visible:

- `http://localhost:8001/health`

Entry points adicionales:

Todos validan antes de construir recursos o arrancar workers. El import de
`app.main` no requiere secretos ni conecta. Ajustar hosts/puertos del fichero
seleccionado para clientes nativos; el entorno precede a dotenv.

- `python -m app.run_worker`
- `python -m app.run_api`
- `python -m app.run_azure_cost_ingestion --tenant-id <tenant> --subscription-id <subscription>`

La ingesta de Azure Cost recorre todas las páginas, normaliza el coste y las
dimensiones y persiste una ejecución reproducible en CockroachDB. Una segunda
ejecución con la misma combinación de tenant, suscripción y consulta reemplaza
atómicamente sus filas en vez de duplicarlas.

## Variables De Entorno

### Contrato de ingesta documental (JUP-020)

La API publica un envoltorio con `id`, `tenant_id`, `source`, `artifact_uri`,
`status` y `payload`. El documento vive en `payload.text_content` y sus
metadatos en `payload.metadata`. `IngestTask` adapta esos campos al estado
del grafo y convierte `id` en `job_id`, conservando la identidad del
envoltorio. El worker mantiene `request_id` en el contexto de los logs.

Las peticiones normales a `POST /jobs/ingest` no necesitan aplanar el mensaje
ni publicar directamente en RabbitMQ. Los llamadores directos de
`PipelineRunner.run` siguen utilizando el estado plano del grafo.

La correccion del contrato y sus limites se documentan en
[JUP-020](../../openspec/changes/archive/2026-09-14-jup-020-document-embedding-pipeline/design.md).
El proveedor de embeddings actual sigue siendo `mock`; esta correccion no
acredita calidad semantica ni la politica completa de reprocesado del corpus.

Prueba HTTP y resultados con RabbitMQ, CockroachDB y pgvector reales:
[evidencia JUP-020](../../docs/evidence/JUP-020-validation.md).

### Fallos, reintentos y descarte (JUP-113)

El worker consume `processor:jobs` con un único hilo. Tras contrastar el mensaje con el job guardado,
trata cada entrega así:

| Qué ocurre | Estado del job | Mensaje |
| --- | --- | --- |
| Termina bien | `completed` | `ack` |
| Mensaje inválido (identidad, creador, membresía o payload), o el resultado guardado de un job `completed` no es un objeto | sin cambios | `nack` sin reencolar |
| `ProviderError` | `failed` | `nack` sin reencolar |
| El guardrail de entrada rechaza el trabajo, por ejemplo un `source` que no cumple `^[a-z0-9][a-z0-9._-]{0,63}$` tras `strip().lower()` | `failed` | `nack` sin reencolar; evento `job_input_rejected` |
| Fallo no clasificado, primera entrega | `failed` | `nack` con reencolado; el bucle registra `worker_loop_failed` y espera 2 s |
| Fallo no clasificado, reentrega (marca `redelivered` de RabbitMQ) | `failed` | `nack` sin reencolar; evento `job_retry_exhausted` |
| No se puede leer el job o registrar su estado (base caída) | el que tuviera | `nack` con reencolado, **sin tope** |

El tope es **una reentrega como máximo**, no «dos intentos siempre»: una primera entrega interrumpida
(reinicio del worker, conexión perdida sin responder) ya llega marcada como reentrega, y su primer fallo
descarta. El último caso no tiene tope a propósito: descartar dejaría el job en `queued` o `running` sin
mensaje y sin que nadie lo vea. Los eventos `job_input_rejected` y `job_retry_exhausted` son fijos y
llevan solo el `request_id`: nunca el `source`, el contenido ni la causa.

**Resultado guardado de un job `completed`.** En CockroachDB `jobs.result` es `JSONB` y llega ya decodificado, así que un `str` es una cadena JSON y se rechaza siempre, tenga el contenido que tenga (incluidos `{}` o `null`). Solo SQLite, que se usa en pruebas y guarda el objeto serializado como texto, lo decodifica; `JobRepository.json_stored_as_text` dice cuál de las dos representaciones se recibe.

**Coste a tener presente.** Si pgvector o el proveedor de embeddings caen el tiempo suficiente para que
fallen los dos intentos, los jobs que lleguen en ese intervalo quedan `failed` y **hay que volver a enviarlos**;
no se reprocesan solos. Con pgvector parado se midieron unos 10 s hasta el descarte (dos intentos de unos 4 s
y 2 s de espera), y el worker se recupera solo al volver el servicio. No existe una lectura del estado de un
job (`RF-104-003`): el fallo se ve en la base, en los registros y en la alerta de fallos de ingesta. El
contador `processor_ingest_jobs_failed_total` suma cada marca de `failed`, así que un job con un fallo no
clasificado cuenta hasta 2.

Decisión y alternativas en [ADR-0019](../../docs/adr/ADR-0019-ingestion-retry-policy.md); evidencia, con
RabbitMQ, CockroachDB y pgvector reales, en [JUP-113](../../docs/evidence/JUP-113-validation.md).

### Configuracion

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

El chat JUP-035 usa una recuperacion documental y una generacion estructurada
por intento. `CHAT_MAX_OUTPUT_TOKENS` admite 1–6400 (6400 por defecto),
incluyendo razonamiento; ingesta conserva `LLM_MAX_OUTPUT_TOKENS` y resumen
su presupuesto separado. Ambos servicios reservan la salida configurada.
El semaforo de coste no asignado se publica mediante un segmento privado
verificado: formula y bandas del corpus autorizado habilitan el catalogo
versionado; el servidor aplica los limites antes de redondear y publica sus
citas autenticas. Rechaza citas entregadas con pasajes o metadatos incorrectos.
Un ejercicio con cifras del usuario sigue siendo hipotetico, no coste verificado.

`DATABASE_URL`, `RABBITMQ_URL` y `VECTOR_DATABASE_URL` son obligatorias,
tambien en test. `RUNTIME_ENVIRONMENT` vale production por defecto:
`AI_EXECUTION_MODE=test` no evita estas validaciones. Las fixtures pytest
inyectan credenciales sinteticas y no cargan dotenv real. Los tests de
integracion Cockroach requieren su opt-in independiente y una instancia aislada.

Mocks no necesitan `LITELLM_API_KEY`. Seleccionar LiteLLM conserva los
validadores de clave, URL, alias, dimensiones y evaluation, sin acreditar un
cliente/proveedor real desplegado. Las claves upstream/master solo pertenecen
al gateway; consultar [su propuesta](../../infra/litellm/README.md).

El processor y el backend usan claves virtuales distintas: la del backend (`BACKEND_LITELLM_API_KEY`) no se configura aqui. `EMBEDDING_PROVIDER` es una unica variable de Compose compartida: ingesta y consulta deben usar el mismo proveedor (ver [ADR-0017](../../docs/adr/ADR-0017-backend-query-embedding-own-key.md)).

Los tokens `AZURE_COST_*` del simulador son fixtures locales, no credenciales Azure.

Errores persistidos de jobs usan `ingestion_failed`, sin texto crudo de
excepciones. La salida JSON conserva diagnosticos saneados y correlacion;
ver [limites y rotacion](../../docs/manuals/python-service-conventions.md).

```powershell
python -m pytest tests
```

## Notas

- Convenciones de código Python (logging, etc.): ver `docs/manuals/python-service-conventions.md`.
- `workers/runner.py` consume la cola de RabbitMQ; su política de fallos y reintentos está en «Fallos, reintentos y descarte (JUP-113)».
- `db/migration_runner.py` y `vector_store/migrations/` aplican migraciones formales. El runner exige indicar su tabla de versiones, y las migraciones del processor solo pueden tocar sus propias tablas (`tests/test_schema_ownership_static.py`).
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
