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

> Estado de este documento: **en curso.** Están registrados los grupos 1 a 6 de `tasks.md`. Las demás
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
- **Observado:** la conversación seleccionada es la primera de la lista (la de actualización más
  reciente) y el mensaje va a ella; la nueva queda vacía. Efecto acumulado tras las pasadas: 10 de
  las 12 conversaciones están vacías, y solo `fc77bad7` y `461a1c7d` tienen mensajes.
- **Sin efecto con el ámbito vacío:** la primera conversación de un ámbito sí se selecciona bien (por
  eso la pasada 1 no lo mostró y `6.1` solo lo revela con conversaciones previas).
- **Causa probable, por lectura del código; no depurada en ejecución.** En
  `apps/frontend/src/pages/ConversationsPage.tsx`, `onSuccess` de la creación (líneas 71 a 73)
  invalida la lista y selecciona la conversación nueva; pero el efecto de las líneas 51 a 61 comprueba
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

## Batería del carril (grupo 9)

No ejecutada.

## Archivos compartidos (grupo 10)

No modificados.

## No validado

Todo lo que no consta arriba como ejecutado. La lista final se redacta en la tarea 8.3.
