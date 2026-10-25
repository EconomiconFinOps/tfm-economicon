# Evidencia JUP-104 — Validación E2E del recorrido completo

- Fecha: 2026-10-05 (línea base y stack) y 2026-10-06 (recorrido y pasada manual), en UTC.
- Trello: https://trello.com/c/lVvZa7P5/96-jup-104
- Rama: `feat/JUP-104-e2e-validation`.
- Base: `develop` en `0488372` al empezar; se fusionó `develop` en `f0cacdd` (JUP-067) durante el grupo 10.
  El recorrido y la batería se ejecutaron con la rama en `139650c` (guion) y `0b68434` (batería); ver cada
  sección.
- OpenSpec: [jup-104-e2e-validation](../../openspec/changes/archive/2026-10-06-jup-104-e2e-validation/).
- Spec que valida: `operator-journey-validation` (nueva; se promueve al archivar).
- Pull request: [#79](https://github.com/EconomiconFinOps/tfm-economicon/pull/79), contra `develop`.
- CI sobre `339a157`: [7 de 7 jobs correctos](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37548790297). La del estado fusionado con `develop` (`b3716f7`) se
  consulta en la pestaña de checks del PR.

> Estado de este documento: **completo.** Están registrados los 11 grupos de `tasks.md`, el change está
> **archivado** (2026-10-06) y el PR #79 tiene sus dos reviews. El 2026-10-07 se fusionó `develop` (con
> JUP-103) para resolver el conflicto: ver «Pull request, reviews e integración con `develop`». Quedan la
> CI de ese estado y la relectura de las reviews.

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

## Guion de navegador (grupo 3)

### Proyecto externo (tarea 3.1)

Proyecto propio **fuera del repositorio**, con sus resultados y capturas también fuera.

| Dato | Valor |
| --- | --- |
| Playwright | `1.63.0` (instalado con `npm` en esa carpeta; la regla de pnpm del repositorio no le afecta) |
| Chromium | `153.0.8010.12` (revisión `1243`), ya presente en la caché de Playwright de la máquina: no se descargó nada |
| Node | `v24.15.0` |
| `git status` del repositorio tras instalarlo | Sin cambios: no deja nada dentro |

### Guion (tareas 3.2 y 3.3)

El guion cumple la decisión 4 del `design.md`: Chromium en modo headless con perfil vacío, sin
`page.route` (no intercepta ni responde peticiones), sin escribir la sesión en el almacenamiento
(entra por el formulario), contraseña leída de `E2E_PASSWORD`, esperas por condición, y falla ante
un error de página, un error de CORS en la consola o un paso incumplido; los pasos que dependen de
uno fallido quedan como `not_run`. Las consultas a CockroachDB y pgvector y la lectura de los
registros del backend y del processor son de solo lectura y van dentro del propio guion, de modo que
el recorrido se repite con un solo comando.

Versionado, con su texto íntegro y cómo ejecutarlo, en
[JUP-104-browser-recipe.md](JUP-104-browser-recipe.md). El texto de la receta es byte a byte el del
guion que se ejecuta.

### Ensayo de solo lectura (no es la evidencia del recorrido)

Antes de la ejecución completa se ensayaron, con `E2E_PHASE=read`, solo los pasos que no modifican
datos (`0.1` y el grupo 4) para depurar selectores sin ensuciar el stack. Sobre el commit `729d4ba`:
5 de 5 pasos correctos, 0 errores de página, 0 errores de consola y 0 de CORS. Las observaciones de
ese ensayo **no** se usan como resultado del recorrido: el registro de los grupos 4 a 6 sale de la
ejecución completa.

Tres hechos del ensayo que sí afectan a la receta:

- **`chrome://version` no se puede abrir con Playwright** (`net::ERR_INVALID_URL`). Para acreditar
  que no se relajan protecciones, el paso `0.1` lee la **línea de comandos real del proceso** del
  navegador (PowerShell en Windows). Tiene 44 opciones y ninguna de `--disable-web-security`,
  `--allow-running-insecure-content`, `--disable-site-isolation-trials` ni
  `--ignore-certificate-errors`.
- **Playwright añade sus opciones estándar de automatización**, entre ellas `--no-sandbox`,
  `--disable-popup-blocking`, `--disable-extensions` y `--headless`. Ninguna afecta a CORS ni a la
  política de mismo origen, pero **no es el navegador de una persona**. Por eso existe la pasada
  manual de la tarea 7.1, y esta limitación consta también en la receta.
- **Una petición `GET /billing/summary` termina en `net::ERR_ABORTED`.** Es la capa API cancelando la
  consulta en curso cuando cambia la selección al rellenar las fechas, no un fallo. Se anota en el
  recorrido para que no se confunda con uno.

Dos cambios al guion durante el ensayo: el paso `0.1` pasó de abrir `chrome://version` a leer la
línea de comandos del proceso, y el paso `4.2` añadió el desglose por grupo de recursos porque el
agrupado por defecto (Servicio) deja los 38 registros sin dimensión.

## Recorrido en navegador (grupos 4 a 6)

### Ejecuciones del guion

Todas sobre el mismo stack (`jup104-e2e`), el mismo 2026-10-06, con el repositorio en `139650c` (el
guion es el de la receta de la versión que incluye este registro). Cada pasada es **una sola sesión de
navegador**, del acceso al cierre de sesión. Se registran las cinco porque las cuatro primeras
descubrieron defectos del guion o del producto, y porque dejan datos en el stack (ver «Residuo»).

| Pasada | Hora UTC | Resultado | Qué pasó |
| --- | --- | --- | --- |
| 1 | 00:17:56 a 00:18:24 | 10 correctos, 1 fallido (`6.1`), 3 no ejecutados | **Defecto de mi comprobación, no del producto**: comparaba cada fragmento con el documento tal cual, y el chunker normaliza los espacios (`" ".join(text.split())`), así que los fragmentos guardados no tienen saltos de línea. La ingesta y el aislamiento por ámbito sí quedaron acreditados |
| 2 | 00:20:24 a 00:20:58 | 14 de 14 | Comprobación corregida: comparación exacta con los primeros 140 caracteres de los fragmentos guardados en pgvector. Reveló que el mensaje se había enviado a otra conversación (la reabierta tenía 4 mensajes, no 2) |
| 3 | 00:22:16 a 00:22:52 | 14 correctos, 1 fallido (`6.3b`) | Añadido el paso `6.3b`, que reproduce a propósito lo anterior. Fallo del producto, ver «Asistente» |
| 4 | 00:23:37 a 00:24:12 | 14 correctos, 1 fallido (`6.3b`) | El paso `4.4` atribuía a una pantalla una petición en vuelo de la anterior (TanStack Query muestra datos en caché y refresca en segundo plano) |
| **5** | **00:24:48 a 00:25:26** | **14 correctos, 1 fallido (`6.3b`)** | **Versión final del guion** (espera de red en calma entre pantallas). Es la que se usa como evidencia |

Pasada 5: 0 errores de página, 0 errores de consola, 0 de CORS, **0 respuestas 4xx y 0 respuestas
5xx** del backend (todas las respuestas observadas fueron 2xx). Una petición abortada
(`GET /billing/summary`, `net::ERR_ABORTED`): es la aplicación cancelando la consulta en curso al
cambiar la selección. Ningún registro de nivel `error`, `critical` ni `warning` en el backend y el
processor durante las pasadas, salvo el ruido de `pika` que se describirá entre las observaciones
fuera del recorrido (grupo 8).

El paso que falla por el producto (`6.3b`) hace terminar el guion con código de salida 1, como indica
la receta. Capturas y `results.json` de cada pasada, **fuera del repositorio**.

**Residuo en el stack tras las cinco pasadas** (consultas de solo lectura). El recorrido final no
parte de un Growth Ops vacío:

| Almacén | Contenido |
| --- | --- |
| CockroachDB, `jobs` | 6 trabajos `completed`: el del smoke (`tenant-core`) y uno por pasada, todos de `tenant-growth` (`5c8541af`, `0b471344`, `8b87a62f`, `d1e6af46`, `82b49a42`) |
| pgvector, `tenant-growth` | **5 documentos** `assistant-corpus` con el mismo contenido, 95 fragmentos en total; la pasada 5 ingirió `82b49a42` |
| pgvector, `tenant-core` | Solo el documento `local-smoke` del smoke, con 1 fragmento |
| CockroachDB, conversaciones | 12: 8 en `tenant-growth` (7 vacías) y 4 en `tenant-core` (3 vacías); **10 vacías en total**. Solo dos tienen mensajes: `fc77bad7` (Growth Ops, 16 mensajes) y `461a1c7d` (Core Finance, 8) |

Consecuencia para leer los resultados: en Growth Ops hay copias idénticas del mismo documento, así que
la respuesta del asistente puede traer fragmentos duplicados con la misma distancia. Lo que se acredita
es que el fragmento procede **de un documento ingerido desde la interfaz en estas pasadas**, y se
comprueba contra todos ellos; no se afirma que sea el de la pasada 5 salvo donde se diga. Un recorrido
sin residuo exigiría un stack con volúmenes nuevos.

### Navegador (paso 0.1 del guion)

Chromium `153.0.8010.12` (Playwright `1.63.0`), modo headless, perfil vacío. El paso lee la línea de
comandos real del proceso: **44 opciones, ninguna** de `--disable-web-security`,
`--allow-running-insecure-content`, `--disable-site-isolation-trials` ni
`--ignore-certificate-errors`. Incluye las opciones estándar de automatización de Playwright, entre
ellas `--no-sandbox` y `--disable-popup-blocking`, que no afectan a CORS ni a la política de mismo
origen. El frontend se sirve desde `http://localhost:5173` y el backend desde `http://localhost:8000`:
**orígenes distintos**, de modo que el navegador aplica CORS en cada petición. Sin `page.route`:
ninguna respuesta del backend se sustituye ni se intercepta.

### Acceso, ámbito y costes (grupo 4), pasada 5

**4.1 Acceso por el formulario: acreditado.**

- La pantalla de acceso trae `operator@example.com` precargado; la contraseña la aporta el guion desde
  `E2E_PASSWORD` (el valor de `DEMO_PASSWORD`, solo por nombre aquí).
- `POST /auth/login` → 200 desde el navegador. La sesión la crea la aplicación (existe
  `finops.session`; solo se comprueba que existe, no su valor).
- `GET /me` → 200 y `GET /tenants` → 200. Ámbitos del selector: `Core Finance` y `Growth Ops`.
  Identidad mostrada en la cabecera: `operator@example.com`.
- Sin errores de CORS en la consola con orígenes distintos: el acceso funciona sin desactivar ninguna
  protección.

**4.2 Costes de Core Finance, `2024-06-01` a `2024-06-21` (fin exclusivo): acreditado.** El guion
fija el periodo a mano; no se comprobó qué muestra el periodo inicial (el mes en curso).

| Dato | Pantalla | Respuesta de `GET /billing/summary` (`X-Tenant-Id: tenant-core`) |
| --- | --- | --- |
| Agrupado por Servicio (por defecto) | `0.06 USD`, 1 fila, aviso «Datos parciales» | `totals` `0.06 USD`, `data_status: partial`, 1 grupo, 38 registros sin dimensión, 0 sin fecha |
| Agrupado por Grupo de recursos | 8 filas | `totals` `0.06 USD`, `data_status: available`, 8 grupos, 0 sin dimensión |

- El total mostrado coincide con el de la respuesta que recibió la propia interfaz.
- Con el agrupado por defecto, los 38 registros de la muestra simulada no traen la dimensión Servicio:
  la pantalla muestra una sola fila «Sin dimensión» y el aviso de datos parciales. Es una propiedad del
  conjunto de datos simulado, no un fallo observado. El reparto con sentido sale agrupando por Grupo de
  recursos (8 grupos), que coincide con lo que anota el preflight de JUP-065 en su PR #63, aún sin
  fusionar.
- «Ahorro potencial: no disponible.», como corresponde (no hay motor de ahorro, `RF-091-004`).

**4.3 Cambio de ámbito: acreditado.**

- Con Growth Ops y el mismo periodo, la sección de costes reales muestra «Sin datos de costes para
  este periodo.» y el periodo se conserva.
- Al volver a Core Finance se recupera `0.06 USD`. La separación visual por ámbito funciona; esto no
  sustituye a una prueba de autorización contra ámbitos ajenos (JUP-086).

**4.4 Origen de los datos por pantalla: acreditado.** Peticiones al backend observadas en cada
visita, con la red en calma antes de entrar, y si la interfaz lo rotula:

| Pantalla | Título | Peticiones al backend en la visita | ¿Rotulada como demostración? |
| --- | --- | --- | --- |
| `/operational` | Dashboard Operativo - Coste Detallado | ninguna | **No** |
| `/cuts` | Dashboard Ejecutivo - Corte Global | ninguna | **No** |
| `/anomalies` | Panel de Anomalías y Alertas | ninguna | Sí: región «Datos de demostración» y rótulo repetido (2 apariciones) |
| `/recommendations` | Panel de Recomendaciones | ninguna | **No** |
| `/overview-legacy` | FinOps Operator / Tenants | `GET /billing/summary` 200, `GET /health` 200 | No aplica: datos del backend |
| `/` | Dashboard Ejecutivo - Coste Global | `GET /billing/summary` 200 | **Mixta**: costes reales arriba y una sección «Datos de demostración» rotulada (evolución, inventario, exportación) |

Recuento para JUP-105 (pantallas con ruta, sin `/login`) a partir de este recorrido: **4 consumen el
backend** (`/`, en su sección de costes; `/overview-legacy`; y `/ingest` y `/assistant`, estas dos en
los grupos 5 y 6) y **4 son solo demostración y no hacen ninguna petición** (`/operational`, `/cuts`,
`/anomalies` y `/recommendations`). De esas cuatro, **tres no avisan en la interfaz** de que sus datos
son de demostración (`/operational`, `/cuts` y `/recommendations`); solo `/anomalies` lo rotula. Esto
no contradice la spec vigente (el origen de demostración está declarado en `src/data/demo/`), pero un
operador no lo distingue a simple vista; se relaciona con `RF-095-002`.

Capturas de la pasada 5 (fuera del repositorio): acceso, costes de Core Finance (por Servicio y por
Grupo de recursos), costes de Growth Ops y las seis pantallas.

### Ingesta extremo a extremo (grupo 5), pasada 5

**5.1 Envío desde la interfaz: acreditado.** Con Growth Ops seleccionado, en `/ingest`:

| Campo | Valor |
| --- | --- |
| Source | `assistant-corpus` |
| Artifact URI | `docs/assistant-corpus/finops/azure-finops-mvp.md` |
| Text content | El documento íntegro: 8696 bytes, SHA-256 `94ca7a74ab02d18c6edc31a32ad7bc91362875fdd0445075b1d6323573a49c90` |

- `POST /jobs/ingest` → **202**, con `X-Tenant-Id: tenant-growth`.
- La interfaz muestra «Job accepted» con **Job ID** `82b49a42-548a-45d8-abce-ebf9a268af3d`,
  **Status** `queued` y **Queue** `processor:jobs`. El identificador mostrado coincide con el de la
  respuesta.
- Esa confirmación **no cuenta como prueba de procesado**: por lectura de `IngestPage.tsx`, la
  pantalla no vuelve a consultar el estado y no puede llegar a mostrar `completed`. La prueba está
  fuera de la interfaz (5.2 y 5.3).

**5.2 Trabajo completado en CockroachDB: acreditado.** El guion consulta
`SELECT status FROM jobs WHERE id = '<job_id>'` con un plazo de 120 s y obtiene `completed`.
Comprobación independiente de la fila completa:

| Campo de `jobs` | Valor |
| --- | --- |
| `status` | `completed` |
| `tenant_id` | `tenant-growth` |
| `source` | `assistant-corpus` |
| `artifact_uri` | `docs/assistant-corpus/finops/azure-finops-mvp.md` |
| `created_at` → `updated_at` | `2026-10-06 00:25:10.58` → `00:25:11.11` (0,53 s) |

La cola `processor:jobs` de RabbitMQ quedó con 0 mensajes listos y 0 sin confirmar: el mensaje se
consumió.

**5.3 Documento, fragmentos y vectores en pgvector: acreditado.**

| Comprobación | Resultado |
| --- | --- |
| `knowledge_documents` con `job_id` del trabajo | 1 fila: `id` igual al `job_id`, `tenant_id = tenant-growth`, mismo `source` y `artifact_uri`, `chunk_count = 19` |
| `document_chunks` de ese documento | 19 |
| `chunk_embeddings` de esos fragmentos | 19, dimensión mínima 8 y máxima 8, proveedor `mock` |
| Tipo de la columna de vectores | `vector(8)` |
| Fragmentos de este trabajo en `tenant-core` | 0 |
| Documentos de este trabajo fuera de `tenant-growth` | 0 |

Dos comprobaciones independientes del guion, hechas aparte con consultas de solo lectura:

- **Contenido guardado.** El hash MD5 del `text_content` guardado con los espacios normalizados
  (`b9d76bdc8cb1777c973024fff4efbdf6`, 8419 caracteres) coincide con el del documento local
  normalizado.
- **Fragmentos completos.** Recalculando los fragmentos con el algoritmo del processor (espacios
  normalizados, ventanas de 500 caracteres con solape de 50, `strip` de cada ventana) sobre el
  documento enviado salen 19, **idénticos uno a uno** a los 19 guardados. El documento llegó entero,
  sin truncar.

Residuo: en `tenant-growth` hay 5 documentos con este mismo origen y URI (uno por pasada); el de esta
pasada es el último. Ver «Residuo en el stack».

**5.4 Registro del processor: acreditado, con límite.** Desde el inicio de la ingesta
(`00:25:10.49Z`) el processor emitió 1 evento, `job_processing` (nivel `info`, `00:25:11.07Z`), y
ninguno de nivel `error`. El processor **no emite un evento de finalización**, así que el registro
solo acredita que recogió el trabajo; que terminó lo acreditan 5.2 y 5.3. El registro guardado no
contiene contenido del documento.

**No ejercitado en el navegador:** el escenario en que el trabajo no llega a completarse (por ejemplo,
con el processor parado). Lo cubre a nivel de API el smoke de JUP-050 («Processor stopped»); aquí no se
ha provocado.

### Asistente, historial y cierre de sesión (grupo 6), pasada 5

Todo el grupo se ejecutó con el proveedor de embeddings **`mock`** (dimensión 8, sin umbral de
distancia), como fija la decisión 1 del `design.md`. Pregunta: el caso `JUP-069-004` de
`docs/validation/JUP-069-questions.json`, «¿Uso coste actual o amortizado para repartir el coste de
una reserva?».

**6.1 Pregunta en Growth Ops: acreditado el camino de los datos, no la pertinencia.**

- `POST /assistant/conversations/{id}/messages` → 201. La respuesta es la plantilla del backend (639
  caracteres): «He encontrado contexto relacionado para tu consulta.», la pregunta y tres líneas
  `- assistant-corpus: <primeros 140 caracteres del fragmento>`. No hay texto generado.
- Cada uno de los 3 fragmentos mostrados **coincide exactamente** con los primeros 140 caracteres de un
  fragmento guardado en pgvector de un documento ingerido desde la interfaz, y es subcadena del
  documento original con los espacios normalizados.
- `retrieved_context` trae 4 fragmentos, los 4 a distancia `0.5694`. La interfaz no muestra
  `retrieved_context` aparte: pinta solo el rol y el texto de cada mensaje.
- **Los tres fragmentos mostrados son el mismo texto**, copia del fragmento 15 en tres de los cinco
  documentos duplicados (residuo): efecto de las copias idénticas, ver «Residuo en el stack».

**Lo que `mock` no acredita, medido aquí.** El documento tiene un único fragmento que contiene
«amortized» o «actual cost» (el 6 de 19, que es el que responde a la pregunta). **No se recuperó.** Se
recuperaron cuatro copias del fragmento 15, que empieza «er. 4. Confirmar si el cambio era esperado. 5.
Investigar causa tecnica o de negocio. 6. Estimar impacto…» y no trata de la pregunta. Otras
distancias del mismo recorrido: `0.1808` para una pregunta de comprobación sobre otro tema
(recuperó un fragmento de etiquetado) y `1.4164` para el único fragmento de Core Finance, que se
devolvió igualmente porque no hay umbral. Con `mock` las distancias no miden pertinencia.

Tampoco se evalúa la rúbrica de `JUP-069-004` (distinguir facturación de distribución del
compromiso, explicar el uso del amortizado para showback): el chat no genera una explicación, así que
esa rúbrica pertenece a un ensayo con modelo (JUP-065, JUP-070), no a esta validación.

**6.2 Evento `retrieval` del backend: acreditado.** Para el mensaje de la pregunta, buscado por su
identificador: `provider: mock`, `alias: mock`, `top_k: 4`, `max_distance: null`, 4 resultados,
distancias `[0.5694, 0.5694, 0.5694, 0.5694]`, `tenant-growth`. Los `document_ids` son cuatro de los
cinco documentos de `tenant-growth` con este origen, **entre ellos el de esta pasada**
(`82b49a42-548a-45d8-abce-ebf9a268af3d`). El evento no contiene texto de la pregunta ni de los
fragmentos.

**6.3 Recarga del historial (`RF-087-002`): no se reproduce el fallo.**

- Tras el `POST` de mensaje (201), el guion recarga la página, selecciona Growth Ops y abre `/assistant`:
  `GET /assistant/conversations/{id}` → **200** (la conversación abierta tenía 14 mensajes), y se
  muestran la pregunta y la respuesta. Las 12 lecturas de historial de la pasada (6 de la conversación abierta) dieron 200 y no
  hubo ninguna respuesta 5xx.
- Es el escenario que describe el hallazgo (enviar un mensaje y recargar el historial) contra
  **CockroachDB real**. En la base, los 12 mensajes del asistente llevan `metadata` no nula (ejemplo:
  `{"citations": ["…:chunk:0", …]}`), un objeto JSON, que es el tipo de valor que antes rompía la
  lectura al decodificarlo dos veces.
- La lectura actual de `Database.fetch_messages` solo decodifica `metadata` si llega como texto; ese
  cambio lo introdujo JUP-086 (PR #47, commit `d244278`). Ningún test del repositorio la cubre contra
  una base real; esta ejecución sí.
- **Propuesta para el backlog (tarea 10.2):** `RF-087-002` pasa a `Fixed`, citando JUP-086 y esta
  evidencia, con la nota de que sigue sin haber un test automatizado contra la base real.

**6.3b Segunda conversación en el mismo ámbito: FALLO del producto (hallazgo `RF-104-001`).** Paso
añadido durante el apply (no estaba en `tasks.md`) para reproducir de forma determinista lo que
descubrieron las pasadas 2 y 3. Con 5 conversaciones previas «Ops review» en Growth Ops, el guion
escribe el título «Segunda conversacion», pulsa «New» y envía un mensaje:

| Dato | Valor |
| --- | --- |
| Conversación creada por «New» (`POST /assistant/conversations` → 201) | `dde97015-aad1-4485-b07b-40d071244246` |
| Conversación a la que se envió el mensaje (`POST …/{id}/messages` → 201) | `fc77bad7-bcc1-4eee-ad5b-ec6369313d7a`, la **antigua** |
| Estado de la nueva en la base de datos | 0 mensajes |

La captura del paso (fuera del repositorio) lo confirma: el chat abierto es el de la conversación
antigua, resaltada en primer lugar de la lista con todo su historial acumulado, y «Segunda
conversacion» figura debajo, sin seleccionar y vacía. Lo mismo ocurre en Core Finance con
`461a1c7d`, que acumula 8 mensajes mientras sus conversaciones nuevas están vacías.

- **Reproducción manual:** acceder, elegir un ámbito que ya tenga una conversación, abrir
  `/assistant`, pulsar «New», escribir un mensaje y pulsar «Send».
- **Esperado:** la conversación nueva queda seleccionada y vacía, y el mensaje va a ella.
- **Observado:** la conversación seleccionada es la que era la primera de la lista antes de crear la
  nueva (la de actualización más reciente) y el mensaje va a ella; la nueva queda vacía. Efecto
  acumulado tras las cinco pasadas: 10 de las 12 conversaciones están vacías, y solo `fc77bad7` y
  `461a1c7d` tienen mensajes. La pasada manual (grupo 7) lo reproduce a mano en un navegador normal.
- **Sin efecto con el ámbito vacío:** la primera conversación de un ámbito sí se selecciona bien (por
  eso la pasada 1 no lo mostró y `6.1` solo lo revela con conversaciones previas).
- **Causa probable, por lectura del código; no depurada en ejecución.** En
  `apps/frontend/src/pages/ConversationsPage.tsx`, `onSuccess` de la creación (líneas 71 a 73)
  invalida la lista y selecciona la conversación nueva; pero el efecto de las líneas 51 a 62 comprueba
  que la seleccionada esté en la lista **que todavía es la antigua**, no la encuentra y selecciona
  `items[0]`. Cuando llega la lista refrescada, la seleccionada (la antigua) ya es válida y no vuelve a
  cambiar. Los PR #55 (JUP-025) y #69 (JUP-036), abiertos, conservan ese mismo efecto en sus ramas.
- **Gravedad propuesta:** media. Los mensajes terminan en una conversación distinta de la que el
  operador cree haber abierto, mezclando contextos; solo afecta a ámbitos con alguna conversación.
- **No se corrige aquí** (alcance fuera de la tarjeta, decisión 8 del `design.md`).

**6.4 La misma pregunta en Core Finance: acreditado el aislamiento.**

- Respuesta (196 caracteres): la plantilla con **una sola** línea, `- local-smoke: Smoke del entorno
  local.`, que es el único fragmento de `tenant-core`.
- Ningún fragmento mostrado es del documento ingerido en Growth Ops, y el `chunk_id` recuperado
  (`a67fcd64…`, el del smoke) no pertenece a ninguno de los cinco documentos de Growth Ops.
- Evento `retrieval`: `tenant-core`, 1 resultado, distancia `1.4164`. Que se devuelva un fragmento a
  esa distancia sin relación con la pregunta es otra muestra de que, con `mock` y sin umbral, la
  recuperación no filtra por pertinencia.
- Acredita el filtro por ámbito en la recuperación; no sustituye a las pruebas de aislamiento de
  JUP-086.

**6.5 Cierre de sesión y ruta protegida: acreditado.** Al pulsar «Cerrar sesion» se presenta la
pantalla de acceso (`/login`); abrir `/assistant` directamente termina en `/login`, y no queda
`finops.session` en el almacenamiento.

**6.6 Resultado completo del guion y tabla de pasos (pasada 5).** `results.json` (pasos,
observaciones, errores de página y versión del navegador) y las 17 capturas se guardaron fuera del
repositorio. Chromium `153.0.8010.12`, Playwright `1.63.0`, 0 errores de página.

| Paso | Qué comprueba | Estado |
| --- | --- | --- |
| `0.1` | Navegador sin opciones que relajen la seguridad | acreditado |
| `4.1` | Acceso por el formulario | acreditado |
| `4.2` | Costes de Core Finance | acreditado |
| `4.3` | Cambio de ámbito | acreditado |
| `4.4` | Origen de los datos por pantalla | acreditado |
| `5.1` | Envío desde `/ingest` | acreditado |
| `5.2` | Trabajo completado en CockroachDB | acreditado |
| `5.3` | Documento, fragmentos y vectores en pgvector | acreditado |
| `5.4` | Registro del processor | acreditado, con límite |
| `6.1` | Pregunta en Growth Ops | acreditado el camino, no la pertinencia |
| `6.2` | Evento `retrieval` | acreditado |
| `6.3` | Recarga del historial | acreditado; `RF-087-002` no se reproduce |
| `6.3b` | Segunda conversación | **fallido** (`RF-104-001`) |
| `6.4` | Aislamiento por ámbito | acreditado |
| `6.5` | Cierre de sesión y ruta protegida | acreditado |

14 acreditados y 1 fallido; ninguno sin ejecutar.

**Qué no acredita este grupo.** La pertinencia semántica de la recuperación y cualquier respuesta
generada por un modelo (el chat no genera texto); el modo `litellm`; las citas visibles: el backend
guarda `metadata.citations` con identificadores de fragmento, pero la interfaz no las muestra (JUP-025,
PR #55); las preguntas de gasto en el chat (JUP-036, PR #69); y la pasada manual en un navegador
habitual (tarea 7.1).

## Pasada manual (grupo 7)

**Ejecutada por Victor** sobre el mismo stack (`jup104-e2e`) y en la misma máquina que el guion, el
2026-10-05 por la noche, hora local (aproximadamente de las 01:15 a las 01:40 UTC del 2026-10-06). Siguió la lista de
pasos M1 a M9, que se reproduce abajo, mientras la herramienta de implementación comprobaba en la base
de datos lo que la interfaz no muestra.

| Dato | Valor |
| --- | --- |
| Navegador | Google Chrome `154.0.8037.98` (Official Build, 64 bits) |
| Sistema operativo | Windows 11 |
| Modo | Ventana de Incógnito, con las herramientas de desarrollo abiertas (Consola y Red) |
| Extensiones | **No comprobadas**: Incógnito las desactiva salvo permiso expreso y no se verificó si había alguna permitida |
| Frente al guion | Chrome `154` real, con perfil de persona, frente al Chromium `153` en modo headless con opciones de automatización |

| Paso | Qué se hizo | Resultado |
| --- | --- | --- |
| M1 (`4.1`) | Acceso con la contraseña de `DEMO_PASSWORD` (no consta) | **Bien.** Entra; identidad `operator@example.com`; ámbitos `Core Finance` y `Growth Ops`. Consola con **un único mensaje en rojo**: `Failed to load resource: 404` de `favicon.ico`. No es CORS ni una petición al backend: ver «Observaciones sin hallazgo». La pestaña de avisos mostraba 4, no revisados |
| M2 (`4.2`) | Core Finance, periodo del 01/06/2024 al 24/06/2024 | **Bien.** Por Servicio: `0.06 USD`, 1 fila «Sin dimensión» (38 registros) y aviso «Datos parciales: 38 registros sin dimensión; 0 registros sin fecha excluidos». Por Grupo de recursos: `0.06 USD` y 8 filas que suman 38 registros (CLASSICLAB `0.00`/1, ClancyTest `0.00`/2, DevTestLab `0.03`/8, JJExportTest `0.00`/1, fo-0824-x4 `0.00`/1, ftk-integration-tests `0.00`/21, pulkit-test-rg `0.00`/1, zfinops `0.04`/3). «Ahorro potencial: no disponible.» |
| M3 (`4.3`) | Growth Ops y vuelta a Core Finance | **Bien.** Growth Ops sin datos; Core Finance recupera `0.06 USD` |
| M4 (`5.1`) | Ingesta del documento en Growth Ops | **Bien.** «Job accepted», estado `queued`. Job ID `f6de05d1-f49f-4285-8d0d-503566878543` |
| M4b (`5.2`) | Estado del trabajo | **Bien**, comprobado por la herramienta de implementación: `completed`, `tenant-growth`, mismo origen y URI, 0,45 s de `created_at` a `updated_at`; 19 fragmentos y 19 vectores (`mock`, dimensión 8); el hash del texto guardado normalizado (`b9d76bdc8cb1777c973024fff4efbdf6`, 8419 caracteres) coincide con el del documento local; 0 errores del processor |
| M5 (`6.1`) | «New» y pregunta `JUP-069-004` en Growth Ops | Tras pulsar «New», **antes de escribir**: la conversación nueva (`9:19:10 PM`) aparece la primera de la lista y **sin resaltar**; resaltada, la antigua (`8:25:23 PM`), con su historial. Respuesta con la plantilla («He encontrado contexto relacionado…») y fragmentos de `assistant-corpus`. En la base: el mensaje fue a `fc77bad7` (la antigua, de 16 a 18 mensajes) y la nueva (`30fc4e51`) quedó vacía; el evento `retrieval` trae 4 resultados a distancia `0.5694`, de cuatro de los seis documentos duplicados, **ninguno el ingerido a mano** |
| M6 (`6.3`) | F5 y reabrir el historial | **Bien.** `GET /assistant/conversations/{id}` → **200**; se ven la pregunta y la respuesta. La conversación resaltada tras recargar es la misma `fc77bad7`, que sube al primer puesto porque la lista se ordena por hora de actualización (`9:23:19 PM`); no es otra conversación |
| M7 (`6.3b`) | Título «Segunda conversacion», «New», mirar, «Comprobacion» y «Send» | **Reproduce `RF-104-001`.** Tras «New» queda resaltada la antigua (`9:23:19 PM`) con su historial y «Segunda conversacion» (`9:31:59 PM`) aparece la primera, sin resaltar. Dos minutos después se envió «Comprobacion»: fue a `fc77bad7`; `46e19e5d`, la nueva, quedó con 0 mensajes. Antes, pulsar la conversación `9:19:10 PM` (la creada en M5) mostró un panel vacío |
| M8 (`6.4`) | Core Finance, «New» y la misma pregunta | **Bien.** Una sola línea, `- local-smoke: Smoke del entorno local.`, y ningún fragmento de `assistant-corpus`. En la base: `retrieval` de `tenant-core`, 1 resultado, distancia `1.4164`, documento `a67fcd64` (el del smoke); el mensaje fue a `461a1c7d` (la antigua, a 10 mensajes) y la nueva (`7291a6e1`) quedó vacía |
| M9 (`6.5`) | «Cerrar sesion» y abrir `/assistant` a mano | **Bien.** Ambas veces se presenta la pantalla de acceso |

Ningún registro de nivel `error`, `critical` o `warning` (salvo el ruido de `pika`) en el backend y el
processor durante la pasada manual, y las peticiones que mostraron las capturas de la pestaña Red
respondieron 200 o 201.

**Diferencias respecto al guion (tarea 7.2).**

- **Ninguna en el resultado de los pasos.** Los nueve pasos dieron lo mismo que el guion, incluido el
  fallo de `RF-104-001`, que por tanto **no es un artefacto del Chromium de pruebas ni de sus
  opciones de automatización**.
- **Lo que solo se ve en el navegador real:** el `GET /favicon.ico` con 404 (el Chromium headless del
  guion no lo pide) y el aviso de tipo de fecha del navegador.
- **Datos de entrada distintos, sin efecto:** el navegador mostraba las fechas como `mm/dd/aaaa` y el
  fin del periodo fue el 24 en lugar del 21; los registros de la muestra van del 2024-06-02 al
  2024-06-19, así que el resultado es idéntico.
- **El residuo condiciona el contexto recuperado:** al haber seis copias idénticas del documento en
  Growth Ops, el desempate por identificador devolvió fragmentos de cuatro copias anteriores y no de la
  que se ingirió a mano; el texto es el mismo.
- **Más datos que el guion no aportó:** el reproducido a ritmo humano (dos minutos entre «New» y
  «Send») y la secuencia de peticiones de la pestaña Red, ver `RF-104-001`.

**Efecto en el stack tras la pasada manual:** 6 trabajos en `tenant-growth` y 1 en `tenant-core`;
`tenant-growth` con 6 documentos `assistant-corpus` y 114 fragmentos; 15 conversaciones (10 en Growth
Ops y 5 en Core Finance), **13 de ellas vacías**; solo `fc77bad7` (20 mensajes) y `461a1c7d` (10) tienen
mensajes.

## Hallazgos y límites (grupo 8)

### Hallazgos nuevos (tarea 8.1)

Cuatro hallazgos, redactados con los campos de `openspec/findings/backlog.md` para pasarlos allí en la
tarea 10.2. Origen común: `jup-104-e2e-validation`, fecha `2026-10-06`, owner Equipo Economicon, estado
`Open`. Ninguno se corrige en esta tarjeta.

**RF-104-001 — La conversación recién creada no recibe el mensaje.** Severidad: **Media**. Tipo:
selección de conversación en `ConversationsPage`. Scope: fuera de alcance (frontend; la tarjeta no
corrige).

- *Reproducción:* con un ámbito que ya tiene una conversación, abrir `/assistant`, pulsar «New»,
  escribir un mensaje y pulsar «Send».
- *Esperado:* la conversación nueva queda seleccionada y vacía, y el mensaje va a ella.
- *Observado:* queda seleccionada la conversación que **era la primera de la lista antes de crear la
  nueva** (la de actualización más reciente) y el mensaje va a ella; la nueva queda vacía, y al
  refrescarse la lista aparece primera pero sin resaltar. Reproducido por el guion (paso `6.3b`) en las
  pasadas 3, 4 y 5 y por el paso `6.1`, **y a mano por una persona en Chrome 154** (pasos M5, M7 y M8,
  en Growth Ops y en Core Finance). Con el ámbito sin conversaciones previas no ocurre. Tras la pasada
  manual, 13 de las 15 conversaciones del stack están vacías y solo dos tienen mensajes.
- *No depende del ritmo:* en M7 pasaron dos minutos entre pulsar «New» y enviar el mensaje, y la
  seleccionada seguía siendo la antigua. No es una carrera que solo un guion rápido provoque.
- *Causa probable (por lectura del código, sin depurar en ejecución):* el efecto de
  `ConversationsPage.tsx` líneas 51 a 62 sustituye la selección por `items[0]` porque la lista cacheada
  aún no contiene la conversación recién creada (selección en las líneas 71 a 73).
- *Indicio observado en la pasada manual:* la pestaña Red muestra, tras el `POST` de creación (201) y
  la lectura de la lista, una petición del historial de la conversación **nueva** y **a continuación**
  otra de la **antigua**, es decir, la aplicación seleccionó la nueva y otro código la cambió por la
  antigua. Se deduce del orden de las filas (por inicio de petición); sigue sin depurarse en ejecución.
- *Acción propuesta:* no sustituir la selección mientras la conversación recién creada no esté en la
  lista, o insertarla en la caché antes de seleccionarla; añadir un test que cree una segunda
  conversación con otra existente. Coordinar con JUP-025 (PR #55) y JUP-036 (PR #69), que conservan el
  mismo efecto en el mismo archivo.
- *Evidencia:* esta evidencia, sección «Asistente, historial y cierre de sesión», paso `6.3b`.

**RF-104-002 — Cada llamada a `/health` abre una conexión nueva a RabbitMQ y deja 12 eventos de `pika`,
uno de nivel `error`.** Severidad: **Baja**. Tipo: ruido de registro. Scope: fuera de alcance (backend).

- *Observado:* una llamada a `GET /health` suma 12 eventos `rabbitmq_dependency_event` (una llamada,
  +12; dos llamadas, +24), uno de ellos de nivel `error` (`pika.adapters.base_connection`). Con el
  stack en reposo salen **48 eventos por minuto de forma constante**, que equivale a 4 llamadas por
  minuto: coincide con el intervalo de 15 s del healthcheck de Compose del backend (no se ha
  comprobado que sea la única fuente).
- *Por qué importa:* `rabbitmq_dependency_event` sustituye el mensaje original
  (`apps/backend/app/services/rabbitmq_queue.py`, línea 50), así que las líneas de nivel `error` no
  dicen qué ocurrió y no se puede distinguir un fallo real de un cierre de conexión normal. Durante todo
  el recorrido no hubo ningún síntoma: `/health` respondió 200 y los trabajos se publicaron y se
  completaron.
- *Acción propuesta:* decidir si el sondeo debe reutilizar la conexión y a qué nivel deben registrarse
  los eventos de `pika`; comprobar que ninguna alerta dependa del nivel `error`.

**RF-104-003 — La interfaz no puede saber si un trabajo de ingesta terminó o falló.** Severidad:
**Media**. Tipo: contrato ausente. Scope: fuera de alcance (backend y frontend).

- *Observado:* `apps/backend/app/api/routes/jobs.py` solo expone `POST /ingest`; el backend no tiene
  ninguna lectura del estado de un trabajo. `IngestPage.tsx` solo muestra el estado `queued` de la
  respuesta de creación y no vuelve a consultar. Un documento cuyo procesado falle es invisible para el
  operador: la única comprobación posible es la base de datos (como hizo esta validación).
- *Acción propuesta:* decidir si se añade una lectura del estado del trabajo, con aislamiento por
  ámbito, y si la pantalla de ingesta la consulta hasta un estado final. Relacionarlo con las
  capacidades ausentes de `RF-091-003`.

**RF-104-004 — Tres pantallas de demostración no lo indican en la interfaz.** Severidad: **Baja**. Tipo:
presentación de datos de demostración. Scope: fuera de alcance (frontend; relacionado con `RF-095-002`).

- *Observado:* `/operational`, `/cuts` y `/recommendations` no hacen ninguna petición al backend y no
  muestran ningún rótulo de demostración; `/anomalies` sí lo muestra (JUP-057) y `/` rotula su sección de
  demostración. Un operador no distingue esos datos de los reales.
- *Acción propuesta:* rotularlas como `/anomalies`, o decidir y documentar que no hace falta; tenerlo en
  cuenta en la decisión sobre `RF-091-003`.

### `RF-087-002` (tarea 8.2)

**No se reproduce.** Resultado y propuesta (`Fixed`, citando JUP-086, PR #47, y esta evidencia) en el
paso `6.3` de la sección anterior. Queda sin test automatizado contra una base de datos real.

### Observaciones sin hallazgo

- El agrupado por Servicio deja los 38 registros de la muestra simulada «sin dimensión» y la pantalla
  avisa de datos parciales: es una propiedad del conjunto de datos simulado.
- Una petición `GET /billing/summary` aparece como `net::ERR_ABORTED`: la capa API cancela la consulta
  en curso al cambiar la selección.
- El backend arrancó antes de que existiera la tabla de vectores (`embedding_dimension_check_skipped`):
  es la ventana ya registrada como `RF-096-002`.
- Con `mock` la recuperación no mide pertinencia (paso `6.1`): es el límite de la decisión 1 del
  `design.md`, no un fallo nuevo.
- La primera construcción desde cero del stack tardó 5 min 33 s.
- **`GET /favicon.ico` → 404** en la Consola del navegador real: `index.html` no declara ningún icono y
  el frontend no tiene carpeta `public/`. Cosmético; el Chromium headless del guion no lo pide, por eso
  solo salió en la pasada manual. No es CORS ni una petición al backend.
- **La suma de los grupos mostrados puede diferir un céntimo del total** (en el recorrido, `0.03` +
  `0.04` = `0.07` frente a `0.06`): son sumas redondeadas por separado. Valores exactos en la base:
  `0.0251` (DevTestLab), `0.0350` (zfinops) y total `0.0601`. Lo advierte el preflight de JUP-065
  (PR #63, sin fusionar).
- **El navegador muestra las fechas con su formato regional** (`mm/dd/aaaa` en la pasada manual); no
  afecta al valor enviado a la API.

### Qué no acredita esta validación (tarea 8.3)

- **La pertinencia semántica de la recuperación.** Con `mock` el fragmento que responde a la pregunta
  no se recuperó y las distancias no miden pertinencia.
- **Ninguna respuesta generada por un modelo**: el chat compone una plantilla con fragmentos. La rúbrica
  de `JUP-069-004` no se ha evaluado.
- **El modo `litellm`**: sin claves ni gateway en esta máquina; dimensión 1536 y umbral 0.6 sin ejecutar.
- **Las citas visibles** (JUP-025, PR #55): el backend guarda `metadata.citations` pero la interfaz no
  las muestra.
- **Las preguntas de gasto en el chat** (JUP-036, PR #69) y el panel de etiquetado (JUP-017, PR #66):
  no están en `develop`.
- **El fallo de la ingesta en el navegador** (trabajo que no se completa): no se provocó; lo cubre el
  smoke de JUP-050 a nivel de API.
- **Autorización cruzada entre ámbitos**: se comprueba separación de datos, no intentos de acceso a un
  ámbito ajeno (JUP-086).
- **Un recorrido sin residuo:** las cinco pasadas dejaron copias del mismo documento en Growth Ops.
- **Un navegador sin ninguna extensión:** la pasada manual se hizo en Chrome 154 en Incógnito y no se
  verificó si había extensiones permitidas. Tampoco se probó en Firefox ni Safari.
- **La expiración de sesión y las credenciales incorrectas**: ya acreditadas en JUP-085 y JUP-098, no
  repetidas.
- **Rendimiento, accesibilidad y despliegue fuera de local**: fuera de alcance.
- **Que otra persona repita la receta:** al escribir esta sección no la había ejecutado nadie más. Lo hizo
  después Alejandro en su «Validacion JUP-104»: ver «Pull request, reviews e integración con `develop`».

### Trazabilidad con los criterios de la tarjeta (tarea 8.4)

| Criterio de la tarjeta | Estado | Dónde |
| --- | --- | --- |
| 1. Recorrido en navegador real sin desactivar protecciones | Acreditado en el Chromium del guion y en Chrome 154 (pasada manual) | `0.1`, `4.1`; grupo 7 |
| 2. Cada paso registrado con lo hecho y lo observado | Acreditado | Grupos 4 a 6 |
| 3. Ingesta acreditada extremo a extremo | Acreditado | `5.1` a `5.4` |
| 4. Asistente con contexto recuperado, o parte dependiente de JUP-022/JUP-025 registrada | Acotado: camino de los datos y aislamiento acreditados; pertinencia y citas no | `6.1`, `6.2`, `6.4`; «Qué no acredita» |
| 5. Pantallas con datos de demostración identificadas | Acreditado | `4.4`, `RF-104-004` |
| 6. Todo fallo como hallazgo con reproducción | Redactados `RF-104-001` a `004`; pasan al backlog en 10.2 | Grupo 8 |
| 7. Decisión sobre automatizar en `design.md` | Hecha: receta versionada, sin CI | `design.md`, decisión 7 |

### Trazabilidad con los escenarios de la spec `operator-journey-validation`

| Requisito y escenario | Estado | Dónde |
| --- | --- | --- |
| Navegador real: acceso por la interfaz con las protecciones intactas | Acreditado | `0.1`, `4.1` |
| Navegador real: el entorno validado queda identificado | Acreditado | Entorno, «Stack local aislado», «Ejecuciones del guion» |
| Camino completo: resumen de costes del ámbito con datos | Acreditado | `4.2` |
| Camino completo: el cambio de ámbito cambia los datos | Acreditado | `4.3` |
| Camino completo: el historial sobrevive a la recarga | Acreditado | `6.3` |
| Camino completo: el cierre de sesión devuelve al acceso | Acreditado | `6.5` |
| Ingesta: documento enviado desde la interfaz | Acreditado | `5.1` a `5.3` |
| Ingesta: el trabajo no llega a completarse | **No ejercitado** | «Qué no acredita» |
| Contexto: pregunta en el ámbito del documento | Acreditado, con residuo | `6.1`, `6.2` |
| Contexto: la misma pregunta en otro ámbito | Acreditado | `6.4` |
| Contexto: límites del modo utilizado | Acreditado | `6.1`, «Qué no acredita» |
| Demostración: pantalla con datos reales y de demostración | Acreditado | `4.4` (`/`) |
| Demostración: pantalla solo de demostración | Acreditado | `4.4` |
| Fallos: fallo nuevo durante el recorrido | Acreditado | `RF-104-001` a `004` |
| Fallos: hallazgo conocido que el recorrido alcanza | Acreditado | `RF-087-002`, `6.3` |
| Fallos: paso no ejecutado | Acreditado | «Qué no acredita» |
| Repetible: otra persona repite la validación | Acreditado **por la «Validacion JUP-104» de Alejandro** (stack y versiones propios), no por quien escribe | [Receta](JUP-104-browser-recipe.md); sección del PR |
| Repetible: credenciales en el registro | Acreditado | Revisión de secretos (8.5) |

### Revisión de secretos (tarea 8.5)

Se comprobó que **ningún valor** de las variables secretas de `.env` (contraseñas, claves, cookie,
cadenas de conexión) aparece en esta evidencia ni en la receta, y tampoco en las salidas del guion
guardadas fuera del repositorio (`results.json`, registro del processor y registros de ejecución: 23
archivos revisados, sin coincidencias). La contraseña de demostración figura solo por el nombre de la
variable. Las capturas, también fuera del repositorio, no se han revisado una a una y no se adjuntan.

### Parada del stack (tarea 8.6)

Hecha tras la pasada manual y **antes** de la batería, porque la batería compite por CPU con el stack
y las pruebas con plazos de tiempo son sensibles a la carga (`RF-098-004`). `docker compose stop`
con `COMPOSE_PROJECT_NAME=jup104-e2e`, **sin borrar volúmenes**:

- Los 9 contenedores del proyecto quedan `exited`.
- Se conservan los 5 volúmenes `jup104-e2e_*` (`cockroach-data`, `pgvector-data`, `rabbitmq-data`,
  `prometheus-data` y `grafana-data`), con los datos descritos en «Residuo en el stack», y las imágenes
  `jup104-e2e-*`.
- Ningún proceso escucha en los puertos del stack.
- El proyecto por defecto `tfm-economicon` no se tocó en ningún momento. Borrar el proyecto
  `jup104-e2e` (`docker compose down -v`) queda a decisión de quien usa la máquina.

## Batería del carril (grupo 9)

Ejecutada el 2026-10-06 desde la raíz, con la rama en `0b68434`, el árbol de trabajo limpio y el stack
de Compose **parado**. `corepack pnpm exec pnpm --version` da `9.0.0`.

**Entorno de Python.** El entorno virtual de JUP-103 (`C:\Users\victo\Pontia\.venv-tfm`) ya no existía:
se recreó **fuera del repositorio** con Python `3.13.7` (en esta máquina no hay un 3.12, que es el de
CI y de las imágenes) y se instaló `requirements-dev.txt` de `backend`, `processor` y `azure-cost-api`
sin errores. Versiones relevantes: `fastapi 0.142.2`, `pytest 9.1.1`, `pika 1.4.4`, `psycopg 3.3.6`,
`langgraph 1.2.12`, `SQLAlchemy 2.0.54`, `structlog 26.1.0`. Se antepone su carpeta `Scripts` al `PATH`
de la consola que lanza `pnpm`, porque turbo usa el `python` que encuentra en el `PATH`.

| Tarea | Comando | Resultado |
| --- | --- | --- |
| 9.1 | `corepack pnpm install --frozen-lockfile` | Salida 0 en 18,7 s; `git status` sin cambios: no modifica el lockfile ni ningún archivo versionado |
| 9.2 | `corepack pnpm lint --force` | 4 de 4 tareas, 0 desde caché, 44,1 s |
| 9.2 | `corepack pnpm typecheck --force` | 1 de 1 (solo el frontend declara `typecheck`), 0 desde caché, 63,9 s |
| 9.2 | `corepack pnpm build --force` | 4 de 4 tareas, 0 desde caché, 46,2 s |
| 9.3 | Mitad Python: `corepack pnpm run test "--filter=!@finops/frontend"` con `TURBO_FORCE=true` | 3 de 3 tareas, 1 min 59,9 s: `azure-cost-api` 59 correctas; `processor` 448 correctas y 57 omitidas; `backend` 578 correctas y 28 omitidas. Total **1085 correctas, 85 omitidas, 0 fallidas** |
| 9.3 | Mitad frontend: `corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1` con `TURBO_FORCE=true` | 1 de 1 tarea, 147,6 s: **48 archivos y 443 pruebas correctas**, 0 fallidas |
| 9.4 | `corepack pnpm openspec:validate` | 46 de 46 |
| 9.4 | `corepack pnpm jup:check -- --change jup-104-e2e-validation` | Correcto: enlazado con Trello y completo |
| 9.4 | `corepack pnpm jup:cleanup:check` | Correcto: 826 archivos sin agentes personales, binarios ni tareas paralelas |
| 9.4 | `corepack pnpm repository:governance:test` | 13 de 13 |
| 9.4 | `corepack pnpm ci:check:test` (adicional) | 12 de 12 |

Más datos de la batería:

- `local:test` se ejecutó en el grupo 1, antes de levantar el stack, con **74 de 74** correctas.
- `--force` en cada tarea de turbo: su caché no depende del gestor de paquetes y una ejecución con
  `cache hit` no demuestra nada. Todas figuran con `0 cached`.
- Las tareas `build` de las tres aplicaciones de Python son `python -m compileall app` y no producen
  archivos: turbo avisa `no output files found` para ellas. Es el comportamiento esperado, no un fallo.
- `vite build` avisa de que el bundle principal supera los 500 kB (`751123` bytes). Es un aviso, no un
  error.
- **Se ejecutó por mitades y no con el comando único** `corepack pnpm test`: con los cuatro paquetes a la
  vez, las pruebas con plazos de tiempo son sensibles a la carga (`RF-098-004`; `RF-103-005`, registrado
  en el PR #75). El comando único no se ha ejecutado aquí, así que no se afirma nada sobre su resultado.
- **No se ha inspeccionado el motivo de las 85 pruebas omitidas.** Los tests opt-in con servicios reales
  se omiten en CI y no se activaron aquí (`RF-096-004`).
- La batería ejecuta Python `3.13.7`, no el `3.12` de CI.
- Esta batería no incluye los cambios del grupo 10: se repite la parte de OpenSpec y gobierno en la tarea
  10.4.

## Archivos compartidos (grupo 10)

**10.1 `develop` traído a la rama.** Al llegar a este grupo, el PR #75 de JUP-103 **no estaba fusionado**
y, además, había dejado de ser fusionable: JUP-067 (PR #74) entró en `develop` y añadió filas al
principio de la tabla del backlog, el mismo punto donde JUP-103 añade las suyas (`mergeable_state:
dirty`, conflicto solo en `openspec/findings/backlog.md`). La decisión 10 del `design.md` obligaba a
parar y decidir; **la decisión fue editar el spike y el backlog ya y resolver los conflictos al
integrar**, en lugar de esperar al #75.

- `develop` en `f0cacdd` se fusionó en la rama (`4c97c41`) sin conflictos. Lo nuevo es JUP-067: 19
  archivos, **ninguno bajo `apps/`**, así que no cambia el chat, la pantalla principal ni la ingesta y
  no hubo que repetir ningún paso del recorrido.
- Con el árbol fusionado: `openspec:validate` 47 de 47 (una spec más, la de JUP-067), `jup:check`,
  `jup:cleanup:check`, `ci:check:test` 12 de 12 (`develop` tocó `ci.yml`) y
  `repository:governance:test` 13 de 13.
- La prueba de fusión en seco antes de editar dio: JUP-103 contra `develop`, conflicto en
  `backlog.md`; esta rama contra `develop`, limpia.

**10.2 `openspec/findings/backlog.md`.**

- Añadidas las filas `RF-104-001` a `RF-104-004` al principio de la tabla, donde marca la convención
  (las más recientes primero), con los mismos 11 separadores que el resto de filas.
- `RF-087-002`: `Open` pasa a `Fixed`, con la actualización del 2026-10-06 (no se reproduce, con la
  evidencia) y la referencia a JUP-086 (PR #47). La decisión definitiva es del gate post-review.

**10.3 `docs/spikes/frontend-migration.md`.**

- «Hechos del destino»: el acceso local `operator@example.com` / `secret` pasa a
  `operator@example.com` con la contraseña de `DEMO_PASSWORD`, con la causa: desde JUP-085 el backend
  solo crea la cuenta con `DEMO_SEED_ENABLED=true` y una contraseña externa, y fuera del entorno `test`
  se niega a arrancar (`DemoRotationRequired`) si la cuenta guardada aún tiene `secret`. Comprobado en
  `apps/backend/app/db/database.py`.
- F5: la tarjeta `jup-0xx-validacion-e2e` pasa a `jup-104-e2e-validation`, con sus tres puntos marcados
  y el resultado. La segunda mención de `secret` desaparece del punto del E2E.
- «Próximos pasos»: punto 12 con el resultado de la tarjeta. Es el 12 y no el 11 porque el 11 es el de
  JUP-103, que está en su PR #75.
- Enlaces: los dos a la evidencia y la receta resuelven; el de la carpeta del change apunta a
  `archive/2026-10-06-jup-104-e2e-validation/` y **resuelve** desde que el change está archivado.

**Conflictos esperados al integrar con el PR #75** (aditivos; se resuelven conservando ambas partes):

| Archivo | Zona | Resolución |
| --- | --- | --- |
| `openspec/findings/backlog.md` | Principio de la tabla: filas `RF-103-001` a `005` frente a `RF-104-001` a `004` | Conservar las dos series |
| `docs/spikes/frontend-migration.md` | Final de «Próximos pasos»: punto 11 (JUP-103) frente al 12 (JUP-104) | Conservar los dos, en ese orden |

**10.4 Comprobaciones tras los cambios.** `openspec:validate` 47 de 47, `jup:check`, `jup:cleanup:check`
(839 archivos), `repository:governance:test` 13 de 13 y `ci:check:test` 12 de 12. Ningún valor secreto
en los archivos tocados. Enlaces relativos de backlog, spike, evidencia, receta, `proposal.md` y
`design.md`: todos resuelven salvo el de la carpeta archivada, esperado hasta el archivado.

**Corregido al archivar (2026-10-06):** los enlaces relativos de `proposal.md`, `design.md`, `review.md`
y de la receta, que bajan un nivel, y los de la evidencia a la carpeta del change. Un script que resuelve
cada enlace relativo de los `.md` tocados (el change archivado, la spec promovida, la evidencia, la receta,
el spike y el backlog) da **0 enlaces rotos**.

## No validado

Ver «Qué no acredita esta validación» en el grupo 8. Lo que no consta como ejecutado en este
documento no está validado.

## Pull request, reviews e integración con `develop`

Sección añadida el 2026-10-07, al atender las reviews del [PR #79](https://github.com/EconomiconFinOps/tfm-economicon/pull/79). Todo lo anterior de este
documento es lo que se revisó y validó sobre `339a157`; aquí consta lo ocurrido después.

| Dato | Estado |
| --- | --- |
| Pull request | [#79](https://github.com/EconomiconFinOps/tfm-economicon/pull/79), contra `develop`, abierto el 2026-10-06 |
| CI técnica sobre `339a157` | [7 de 7 jobs correctos](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37548790297): `JUP policy`, `OpenSpec`, `Frontend build`, `Frontend type check` y los tres de Python |
| «Validacion JUP-104» | [Alejandro, 2026-10-07, Comment](https://github.com/EconomiconFinOps/tfm-economicon/pull/79#pullrequestreview-5436024207): favorable dentro del alcance aprobado, con el fallo del producto y los límites expresos; Comment porque era la primera de las dos |
| «Revision JUP-104» | [Lucía, 2026-10-07, Approve](https://github.com/EconomiconFinOps/tfm-economicon/pull/79#pullrequestreview-5437848910): sin cambios bloqueantes, con dos puntos para el líder |
| Comentarios de conversación y en línea | Ninguno |
| Check `JUP reviews` | En rojo en sus dos ejecuciones sobre `339a157`, ambas anteriores a la review de Lucía; no se ha vuelto a consultar después |

**Repetición independiente de la receta (Alejandro).** Según su review, que es la fuente de todo este
párrafo y que quien escribe esta evidencia **no ha verificado por su cuenta**: ejecutó la receta sobre
`339a157` en un stack propio con volúmenes nuevos y credenciales propias, con Playwright `1.61.0` y
Chromium `149.0.7827.55` (versiones distintas de las de este documento), y obtuvo **14 pasos
acreditados y 1 fallido por `RF-104-001`**, smoke 5 de 5, 19 fragmentos y 19 vectores `mock` que
coinciden uno a uno con el algoritmo del processor, y `RF-087-002` sin reproducir. El único cambio que
declara en el guion es transportar los comandos de Docker por SSH. No hizo pasada manual ni repitió
la batería. Con ello queda cubierto el escenario «Otra persona repite la validación», el único de la
spec que figuraba como pendiente; el del trabajo de ingesta que no se completa sigue sin ejercitar.

**Respuesta a la pregunta abierta de `design.md`** (Alejandro, como líder de JUP-065): este registro
cuenta como **evidencia parcial** del preflight y del recorrido técnico de JUP-065 (acceso y ámbito,
muestra de costes, ingesta, procesado y base vectorial, separación de ámbitos, historial y cierre de
sesión). **No sustituye ni cierra el ensayo de la demo**: no acredita modelo, generación ni
pertinencia reales, citas integradas, los cinco casos con sus rúbricas, la duración ni los controles
previos. Dos diferencias que él señala: esta receta usa otro ámbito y documento, y fija el fin del
periodo en `2024-06-21` mientras el guion de JUP-065 fija `2024-06-20`. `RF-104-001` afecta a las
conversaciones nuevas de ese ensayo.

**Lo atendido de las reviews en esta integración:**

| Qué | Quién lo pidió | Qué se hizo |
| --- | --- | --- |
| Conflicto con `develop` tras fusionarse JUP-103 (PR #75, `b3716f7`) | Lucía y Alejandro | `develop` fusionado en la rama. Backlog: se conservan `RF-104-001` a `004` y `RF-103-001` a `005`. Spike: puntos 11 (JUP-103) y 12 (JUP-104), en ese orden |
| Comprobar que no se pierde ninguna fila `RF-` | Lucía | Comparadas las filas del resultado con las de `develop` y las de `339a157`: 70 filas, ninguna perdida ni duplicada; las únicas que no están en `develop` son las cuatro `RF-104`, y la única cuyo texto difiere del de `develop` es `RF-087-002` |
| Línea en blanco al final de `openspec/specs/operator-journey-validation/spec.md` (`git diff --check`) | Lucía y Alejandro | Retirada |
| La cita «líneas 51 a 61» del efecto de `ConversationsPage.tsx` estaba desplazada | Lucía | Corregida a 51 a 62 en el backlog y en esta evidencia: el `useEffect` empieza en la línea 51 y se cierra en la 62 |

Sin atender, porque no es de esta herramienta: la **nota de pairing** de Paris y Victor, que las dos
reviews recuerdan que sigue sin atribuir en Trello.

**Comprobaciones sobre el árbol fusionado** (2026-10-07, antes del commit de fusión). `develop` solo
aporta lo de JUP-103, que es documentación (`README.md`, su evidencia, su change archivado y la spec
`workspace-task-pipeline`): **nada bajo `apps/`**, así que no cambia nada de lo que el recorrido ejercitó
y no se repite ningún paso.

| Comprobación | Resultado |
| --- | --- |
| `corepack pnpm openspec:validate` | 48 de 48 (una spec más, la de JUP-103) |
| `corepack pnpm jup:check:all` | 9 changes activos correctos |
| `corepack pnpm jup:cleanup:check` | Correcto, 853 archivos |
| `repository:governance:test`, `ci:check:test`, `pr:check:test`, `jup:check:test` | 13 de 13, 12 de 12, 57 de 57 y 7 de 7 |
| `git diff --check origin/develop` | Sin avisos (antes avisaba de la línea en blanco final de la spec) |
| Enlaces relativos de los `.md` de la tarjeta, el spike y el backlog | 0 rotos |
| Marcadores de conflicto en el backlog y el spike | Ninguno |

No se ha repetido la batería de `lint`, `build`, `typecheck` y pruebas: esta integración no toca código.

**La CI de este nuevo estado y la
relectura de las reviews quedan pendientes**: el push de la fusión las deja sin efecto, y Lucía
anticipó que la relectura se limita al backlog y al spike.

## Pendiente

- CI del estado fusionado y relectura de «Revision JUP-104» y «Validacion JUP-104» tras el push.
- Nota real de pairing de Paris y Victor en Trello.
- Decidir qué hacer con el proyecto `jup104-e2e` (parado, con 5 volúmenes y las imágenes
  `jup104-e2e-*`): se conserva o se borra con `docker compose down -v` en ese proyecto.
- Abrir una tarjeta por cada hallazgo (`RF-104-001` a `RF-104-004`), empezando por `RF-104-001`.
- Los PR #55 (JUP-025) y #63 (JUP-065) también tocan el backlog y el spike: quien integre después
  tendrá el mismo conflicto aditivo, según la revisión de Lucía.
