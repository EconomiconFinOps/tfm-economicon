# Evidencia JUP-104 — Validación E2E del recorrido completo

- Fecha: 2026-10-05 (línea base, grupo 1).
- Trello: https://trello.com/c/lVvZa7P5/96-jup-104
- Rama: `feat/JUP-104-e2e-validation`.
- Base: `develop` en `0488372`; la rama en `b687e2a` al registrar la línea base (dos commits propios:
  la propuesta y la aprobación pre-código).
- OpenSpec: [jup-104-e2e-validation](../../openspec/changes/jup-104-e2e-validation/).
- Spec que valida: `operator-journey-validation` (nueva; se promueve al archivar).
- Pull request: pendiente de abrir.
- CI: pendiente.

> Estado de este documento: **en curso.** Están registrados los grupos 1 y 2 de `tasks.md`. Las demás
> secciones figuran con su estado real, que es «no ejecutado».

## Entorno de la máquina de validación (tarea 1.1)

| Dato | Valor |
| --- | --- |
| Sistema operativo | Windows 11 Home, versión `10.0.26200` |
| Node | `v24.15.0` |
| corepack | `0.34.6` |
| pnpm (`corepack pnpm --version`) | `9.0.0` |
| Diagnóstico de JUP-103 (`corepack pnpm exec pnpm --version`) | `9.0.0`, código de salida 0 |
| Docker | `29.8.1` (build `4a63305`) |
| Docker Compose | `v5.5.1` |
| Daemon de Docker | `29.8.1` (linux). Estaba parado en la primera consulta y respondió tras arrancar Docker Desktop (ver «Estado de Docker», tarea 1.4) |

## Variables de entorno por nombre (tarea 1.2)

Comparación de `.env` con `.env.example` **solo por nombre de variable**. Los valores de las
variables secretas no se leen ni se registran; de ellas solo consta si están definidas.

- Variables en ambos archivos: 29.
- Variables en `.env` que no existen en `.env.example`: ninguna.
- Variables en `.env.example` que faltan en `.env`: 34. El `.env` es del 2026-09-29, anterior a
  JUP-022 y JUP-023. Compose les aplica su valor por defecto:

| Grupo | Variables que faltan en `.env` |
| --- | --- |
| Proveedor de embeddings y modelo | `EMBEDDING_PROVIDER`, `EMBEDDING_DIMENSION`, `EMBEDDING_MODEL`, `EMBEDDING_CHUNK_SIZE`, `EMBEDDING_CHUNK_OVERLAP`, `EMBEDDING_TIMEOUT_SECONDS`, `EMBEDDING_MAX_RETRIES` |
| Modelo de lenguaje del processor | `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`, `LLM_MAX_OUTPUT_TOKENS`, `AI_EXECUTION_MODE` |
| Gateway | `LITELLM_BASE_URL`, `LITELLM_API_KEY`, `BACKEND_LITELLM_API_KEY` |
| Recuperación | `RETRIEVAL_TOP_K`, `RETRIEVAL_MAX_DISTANCE` |
| Processor | `PROCESSOR_CONCURRENCY`, `PROCESSOR_QUEUE_NAME` |
| Sesión | `AUTH_TOKEN_TTL_MINUTES` |
| Simulador de Azure y cliente | `AZURE_COST_DEFAULT_SCENARIO`, `AZURE_COST_PAGE_SIZE`, `AZURE_COST_FAKE_TIMEOUT_SECONDS`, `AZURE_COST_RETRY_AFTER_SECONDS`, `AZURE_COST_SKIPTOKEN_SECRET`, `AZURE_COST_API_BASE_URL`, `AZURE_COST_API_TOKEN`, `AZURE_COST_API_VERSION`, `AZURE_COST_API_TIMEOUT_SECONDS`, `AZURE_COST_API_MAX_RETRIES`, `AZURE_COST_API_RETRY_BACKOFF_SECONDS`, `AZURE_COST_API_MAX_RETRY_AFTER_SECONDS`, `AZURE_COST_API_MAX_PAGES` |

Variables que fijan el modo, tal como están en `.env`:

| Variable | Valor en `.env` |
| --- | --- |
| `RUNTIME_ENVIRONMENT` | `development` |
| `ALLOW_INSECURE_LOCAL_DATABASE` | `true` |
| `DEMO_SEED_ENABLED` | `true` |
| `EMBEDDING_PROVIDER` | ausente: toma `mock` por defecto de Compose |
| `LLM_PROVIDER` | ausente: toma `mock` por defecto de Compose |
| `AI_EXECUTION_MODE` | ausente: toma `development` por defecto de Compose |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` |
| `VITE_API_BASE_URL` | `http://localhost:8000` |
| Puertos (`API_HOST_PORT`, `FRONTEND_HOST_PORT`, `PROCESSOR_HOST_PORT`, `AZURE_COST_API_HOST_PORT`) | `8000`, `5173`, `8001`, `8002` |
| `COMPOSE_PROJECT_NAME` | ausente |

Variables secretas, solo si están definidas:

| Estado | Variables |
| --- | --- |
| Definidas | `AUTH_SECRET_KEY`, `DEMO_PASSWORD`, `DATABASE_URL`, `VECTOR_DATABASE_URL`, `RABBITMQ_URL`, `RABBITMQ_DEFAULT_PASS`, `RABBITMQ_ERLANG_COOKIE`, `POSTGRES_PASSWORD`, `GRAFANA_ADMIN_PASSWORD` |
| Vacías | `OPENROUTER_API_KEY`, `LITELLM_MASTER_KEY` |

Lectura: con este `.env` el proveedor de embeddings efectivo es `mock`, como fija la decisión 1 del
`design.md`, y no hay claves del gateway, así que el modo `litellm` no se puede ejecutar en esta
máquina. Que el valor efectivo sea realmente `mock` se comprueba al arrancar el backend (tarea 2.4);
aquí consta solo lo que dicen los archivos.

## `local:test` sin infraestructura de Compose (tarea 1.3)

`corepack pnpm local:test`, desde la raíz, con ningún servicio de Compose en marcha (el daemon de
Docker no respondía): **74 de 74 correctas**, 0 falladas, 0 omitidas, 8,4 s.

Se ejecuta ahora porque falla si CockroachDB, RabbitMQ o pgvector de Compose están levantados
(`RF-103-004`, registrado en el PR #75): después de levantar el stack ya no daría este resultado.

## Estado de Docker (tarea 1.4)

**Acreditado en la segunda consulta**, con Docker Desktop arrancado. La primera, con el daemon
parado, no pudo conectar (`open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file
specified`) y no se da por válida.

Con el daemon respondiendo, `docker ps -a`, `docker compose ls -a`, `docker volume ls`,
`docker network ls` y `docker images`:

| Qué | Resultado |
| --- | --- |
| Proyecto por defecto `tfm-economicon` | **Existe y está parado** (`exited(3)`): 3 contenedores, `cockroachdb`, `rabbitmq` y `postgres-pgvector`, terminados hace unas 45 h (`Exited (137)`, `Exited (0)`, `Exited (137)`). No hay contenedores de `backend`, `processor`, `azure-cost-api` ni `frontend` |
| Volúmenes del proyecto por defecto | `tfm-economicon_cockroach-data`, `_pgvector-data`, `_rabbitmq-data`, `_prometheus-data` y `_grafana-data`: **existen y se conservan** |
| Red del proyecto por defecto | `tfm-economicon_default` |
| Imágenes del proyecto por defecto | `tfm-economicon-backend`, `-processor`, `-frontend` y `-azure-cost-api`, todas con la etiqueta `latest` y creadas **hace unos 6 días**, es decir, de otra rama: no sirven para esta validación y hay que reconstruirlas con `--build` (tarea 2.2) |
| Otros proyectos de Compose en la máquina | `actividadfinalmodulo3` y `aurum-market`, ambos parados y ajenos a esta tarjeta |
| Procesos escuchando en 5173, 8000, 8001, 8002, 8080, 26257, 5672, 15672, 5433, 3000 y 9090 | Ninguno |

Conclusión: el proyecto por defecto **no está levantado**, así que no ocupa ningún puerto y no hizo
falta pararlo. Sus volúmenes y datos no se han tocado. La validación usará un proyecto propio
(`COMPOSE_PROJECT_NAME=jup104-e2e`, decisión 2 del `design.md`), con volúmenes nuevos, de modo que
esos datos quedan intactos y no influyen en el resultado.

## Stack local aislado (grupo 2)

Todos los comandos, desde la raíz del repositorio y con `COMPOSE_PROJECT_NAME=jup104-e2e` definido en
la consola (no en `.env`). Commit del que se construyeron las imágenes: `6dd5d5b` (rama
`feat/JUP-104-e2e-validation`, sobre `develop` en `0488372`; la rama no cambia código de producto).

### Diagnóstico (tarea 2.1)

`corepack pnpm local:doctor`, código de salida 0:

```
[INFO] Instalacion nueva del proyecto "jup104-e2e": no hay volumenes previos.
[OK] El entorno local esta listo para `docker compose up --build --wait`.
```

### Arranque (tarea 2.2)

`docker compose up --build --wait`, código de salida 0. Duración: 5 min 33 s
(`2026-10-05T23:43:41Z` a `23:49:14Z`), incluidas la construcción de las imágenes y la primera
migración de las bases de datos.

| Servicio | Estado | Imagen |
| --- | --- | --- |
| `cockroachdb` | `running`, `healthy` | `cockroachdb/cockroach:v24.1.11` (por huella) |
| `rabbitmq` | `running`, `healthy` | `rabbitmq:3-management` (por huella) |
| `postgres-pgvector` | `running`, `healthy` | `pgvector/pgvector:pg17` (por huella) |
| `azure-cost-api` | `running`, `healthy` | `jup104-e2e-azure-cost-api` |
| `backend` | `running`, `healthy` | `jup104-e2e-backend` |
| `processor` | `running`, `healthy` | `jup104-e2e-processor` |
| `frontend` | `running`, `healthy` | `jup104-e2e-frontend` |
| `prometheus` | `running`, `healthy` | `prom/prometheus:v2.55.1` |
| `grafana` | `running` (sin healthcheck) | `grafana/grafana:11.3.0` |

- Imágenes de aplicación: construidas con `--build` y con el nombre del proyecto
  (`jup104-e2e-*`), distintas de las `tfm-economicon-*` de hace 6 días del proyecto por defecto, que
  no se usan ni se modifican. `backend`, `processor` y `frontend` figuran creadas durante este
  arranque; la de `azure-cost-api` figura «de hace 6 días» (BuildKit reutilizó sus capas de la caché,
  lo que indica que su código no ha cambiado desde entonces; es una inferencia, no una comprobación).
- Volúmenes nuevos: `jup104-e2e_cockroach-data`, `_pgvector-data`, `_rabbitmq-data`,
  `_prometheus-data` y `_grafana-data`. Red: `jup104-e2e_default`.
- El backend arrancó antes de que existiera la tabla de vectores y lo registró
  (`embedding_dimension_check_skipped`, `reason: table_missing`): es la ventana descrita por
  `RF-096-002`, sin consecuencias aquí porque no se usa el asistente hasta que el processor está sano.

### Smoke (tarea 2.3)

`corepack pnpm local:smoke`, **una sola vez** (33 s, `23:49:41Z` a `23:50:14Z`), código de salida 0:

```
[OK] 1/5 Salud de backend, processor, Azure Cost API y frontend
[OK] 2/5 Login del usuario demo
[OK] 3/5 Ingesta de costes desde la Azure Cost API simulada
[OK] 4/5 Resumen de costes con datos
[OK] 5/5 Job de documento publicado en RabbitMQ y completado por el processor
[OK] Recorrido minimo verificado.
```

No se vuelve a ejecutar: cada ejecución añade un fragmento al corpus de `tenant-core`.

Estado de los datos después del smoke, que es la línea base de los grupos 5 y 6 (consultas de solo
lectura):

| Almacén | Contenido |
| --- | --- |
| CockroachDB, `jobs` | 1 trabajo, `completed` |
| CockroachDB, `azure_cost_records` | 38 registros, todos de `tenant-core` |
| CockroachDB, `conversations` y `messages` | 0 y 0 |
| pgvector, `knowledge_documents` | 1 documento: `tenant-core`, origen `local-smoke`, 1 fragmento («Smoke del entorno local.») |
| pgvector, `chunk_embeddings` | 1 vector, proveedor `mock`, dimensión 8 |

`tenant-growth` no tiene costes ni documentos: todo fragmento que el asistente devuelva allí
después de la ingesta del grupo 5 procede del documento del recorrido.

### Proveedor de embeddings (tarea 2.4)

| Comprobación | Resultado |
| --- | --- |
| Evento de arranque del backend `embedding_configuration` | `embedding_provider: mock`, `embedding_model: economicon-embedding`, `embedding_dimension: 8` |
| Entorno efectivo del backend | `RUNTIME_ENVIRONMENT=development`, `EMBEDDING_PROVIDER=mock`, `EMBEDDING_DIMENSION=8`, `RETRIEVAL_TOP_K=4`, `RETRIEVAL_MAX_DISTANCE` vacío (sin umbral de distancia) |
| Entorno efectivo del processor | `LLM_PROVIDER=mock`, `AI_EXECUTION_MODE=development`, `EMBEDDING_PROVIDER=mock`, `EMBEDDING_DIMENSION=8` |
| Columna `chunk_embeddings.embedding` | `vector(8)` |

Criterio de la tarea cumplido: `mock` y 8, como fija la decisión 1 del `design.md`. Queda
acreditado que la validación se ejecuta con el modo que **no** mide pertinencia semántica; el modo
`litellm` no se puede ejecutar en esta máquina (sin claves de gateway).

## Recorrido (grupos 3 a 8)

No ejecutado.

## Batería del carril (grupo 9)

No ejecutada.

## Archivos compartidos (grupo 10)

No modificados.

## No validado

Todo lo que no consta arriba como ejecutado. La lista final se redacta en la tarea 8.3.
