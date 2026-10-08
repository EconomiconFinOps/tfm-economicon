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
- `EMBEDDING_PROVIDER` (`mock` solo con `RUNTIME_ENVIRONMENT=development|test`, o `litellm`)
- `EMBEDDING_DIMENSION` (1536 con `litellm`)
- `EMBEDDING_MODEL`
- `LITELLM_BASE_URL`
- `LITELLM_API_KEY` (clave virtual propia del backend; en Compose se lee de `BACKEND_LITELLM_API_KEY`)
- `EMBEDDING_TIMEOUT_SECONDS` (por intento, 10 s por defecto) y `EMBEDDING_MAX_RETRIES` (1 por defecto): una pregunta espera como mucho (reintentos + 1) x plazo, 20 s en el peor caso con los valores por defecto, mas las esperas entre reintentos (0,25 s la primera, hasta 1 s las siguientes); el par no puede superar 60 s de intentos
- `RETRIEVAL_TOP_K` (1 a 20, por defecto 4) y `RETRIEVAL_MAX_DISTANCE` (mayor que 0 y como maximo 2; en blanco usa 0.6 con `litellm` y ningun umbral con `mock`; `none` u `off` lo desactiva)
- `AUTH_SECRET_KEY`
- `AUTH_TOKEN_TTL_MINUTES`
- `RUNTIME_ENVIRONMENT`
- `CORS_ALLOWED_ORIGINS`

## Recuperacion Semantica Y Reindexado

El chat embebe la pregunta con `EMBEDDING_PROVIDER` y recupera los fragmentos del tenant activo con `RETRIEVAL_TOP_K` y `RETRIEVAL_MAX_DISTANCE` (distancia coseno, inclusiva; 0.6 por defecto con `litellm`, calibrado en `docs/spikes/JUP-022-retrieval-calibration.md`). Si ningun fragmento cumple, la lista es vacia y el asistente responde sin contexto. Decision y alternativas: [ADR-0017](../../docs/adr/ADR-0017-backend-query-embedding-own-key.md).

Con `litellm` el backend usa su propia clave virtual (`BACKEND_LITELLM_API_KEY` en Compose) y exige `EMBEDDING_DIMENSION=1536`; el arranque la rechaza si falta, y `mock` solo se admite con `RUNTIME_ENVIRONMENT=development|test`.

`EMBEDDING_PROVIDER` es una unica variable de Compose compartida con el processor a proposito: la ingesta y la consulta deben usar el mismo proveedor. El processor ya soporta `litellm` (JUP-023, PR #65); la recuperacion solo considera los vectores del proveedor configurado, asi que tras activarlo hay que reindexar el corpus con ese proveedor o devolvera vacio.

Una base pgvector creada con `vector(8)` (proveedor `mock`) no sirve con el modelo real: los vectores de la ingesta y de la pregunta deben tener la misma dimension y el mismo modelo. Para pasar a `vector(1536)` hay que reindexar el corpus en una coleccion nueva, nunca en caliente: en un entorno desechable, parar el stack, borrar el volumen `pgvector-data`, poner `EMBEDDING_PROVIDER=litellm` y `EMBEDDING_DIMENSION=1536` en processor y backend con sus claves y volver a ingerir los documentos. El procedimiento se ejecuto en la revision del PR #67 contra un gateway simulado (al borrar el volumen, el processor crea `vector(1536)` y guarda `provider=litellm`) y no se ha repetido de extremo a extremo con el modelo real. Un cambio de modelo con la misma dimension no se detecta: finding RF-022-001.

Las rutas sincronas del backend comparten el pool de hilos (40 por defecto): con un gateway que acepta la conexion y no responde, muchas preguntas en espera pueden retrasar `/health` mientras dure el plazo de cada una; el tope por pregunta acota ese efecto y queda registrado como finding RF-022-005.

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

`GET /billing/summary` devuelve el contrato v2 de JUP-026 sobre los costes Azure
ingeridos, separados por moneda y periodo. Los importes son strings decimales;
`savings_identified` permanece null. Las fuentes ambiguas devuelven 409.

`POST /billing/budget/evaluate` evalua un presupuesto del tenant activo sin
guardarlo. Requiere el mismo bearer y `X-Tenant-Id`. Ver
[contrato y ejemplos JUP-029](../../docs/manuals/budget-evaluation.md).

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

## Dashboard de salud — JUP-047

La API conserva el healthcheck público y añade `GET /health/status` y `POST /health/provider-check`, autenticados por bearer y tenant. El GET diagnostica conectores y actividad con lecturas acotadas; el POST aplica admisión y reserva antes de una comprobación generativa. Las opciones de diagnóstico son adicionales y la inferencia está deshabilitada por defecto. Contratos, configuración, límites, estado contable y pruebas reproducibles están en el [runbook de salud](../../docs/runbooks/system-health.md). Las pruebas focales usan upstream sintético; no prueban gasto real ni despliegue M5.

La respuesta funcional válida determina la disponibilidad del proveedor. Modelo y coste del gateway se informan aparte, sin confirmar identidad ni facturación upstream. La admisión ordinaria conserva la reserva histórica dentro del margen, sin exigir conciliación inexistente ni reiniciar envíos acumulados. La autorización humana del 08/10 mantiene el techo de **0,20 EUR acumulados, incluidos los intentos previos**; sustituye el antiguo cupo humano de13 y los0,40 USD. El cierre local registra **6 intentos reales**, sin éxitos retrospectivos: la sexta comprobación desde el panel recibió HTTP200, JSON válido, una elección, stop y OK exacto; la quinta mantiene su error429. La cohorte terminó6/6, sin envíos restantes. El coste informado de la sexta fue0,00001935 USD, concordante con el delta de la clave diagnóstica; identidad y facturación upstream siguen sin confirmar. La reserva incierta histórica se conserva íntegra.

La observación real se conserva hasta el siguiente resultado real, sin caducidad por antigüedad. Un timeout posterior muestra unknown/timeout y conserva verified_at y check_id del último éxito como historia; checked_at y last_attempt_at pertenecen al último intento real. Los rechazos de admisión no sustituyen esa observación. expires_at se emite null y se admite como campo nullable por compatibilidad. GET/polling no renueva fechas ni genera inferencias. El panel autenticado visible comparte una apertura por entrada lógica y una comprobación cada diez minutos desde el último POST, con reinicio por acción manual y sin solapamientos. Al ocultarse pausa los temporizadores; al volver realiza como máximo una comprobación vencida, sin recuperar envíos acumulados. Las fechas UTC válidas admiten hasta un segundo futuro frente a la recepción, sin límite de antigüedad; Azure indica SIMULADO y no acredita Azure real. La revisión técnica interna y la validación local anteriores al cambio de retención acreditaron214 pruebas propias cada una; la validación completó cuatro procesos (102+33+29+50), y su ejecución conjunta sin resultado no cuenta como PASS. E12 conserva15 mutantes detectados y controles37/37. Quedan pendientes DockerServer M5 con Alejandro, CI remota, aprobación humana final, archivo específicamente autorizado en la misma rama, PR vinculada y reviews humanas. Los originales y la historia contable se conservan en la evidencia externa E13, sin datos privados en el repositorio.

El mensaje sintético fijo es "Return exactly the two uppercase letters OK. Do not include punctuation, quotes, whitespace, or any other text.". Se conserva content.strip().upper()==OK: puntuación y texto adicional siguen siendo respuesta inválida. LiteLLM usa un probe exclusivo HTTP200/string JSON "I'm alive!" en /health/liveliness; processor/Azure conservan el contrato genérico status. Ambos mantienen límites, cierre, aislamiento de DNS y ausencia de generación por GET. Las cinco suites del comando focal del runbook cubren wire/negativas, selección del adaptador y regresiones de admisión.
