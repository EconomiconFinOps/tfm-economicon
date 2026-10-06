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

> Estado de este documento: **en curso.** Están registrados los grupos 1 a 4 de `tasks.md`. Las demás
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

### Ingesta (grupo 5) y asistente (grupo 6)

Ejecutados por la misma pasada; su registro se añade en los commits de esos grupos.

## Batería del carril (grupo 9)

No ejecutada.

## Archivos compartidos (grupo 10)

No modificados.

## No validado

Todo lo que no consta arriba como ejecutado. La lista final se redacta en la tarea 8.3.
