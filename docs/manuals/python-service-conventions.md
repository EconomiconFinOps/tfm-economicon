# Convenciones de código para servicios Python

Convenciones obligatorias para código nuevo en `apps/backend` y `apps/processor`, más allá de lo que ya cubre `CONTRIBUTING.md` (proceso git/PR). Se añaden entradas aquí a medida que surgen, para no duplicarlas en cada README de servicio.

## Logging

Ambos servicios usan `structlog` configurado con salida JSON y correlación por `request_id` (ver `app/core/logging.py` y `app/core/request_context.py` de cada uno). No uses `logging.getLogger(__name__)` en código nuevo — usa `structlog.get_logger(__name__)`.

El `request_id` se inyecta automáticamente en cada log de una petición vía middleware + `contextvars`; no hace falta pasarlo a mano.

Introducido en JUP-042.

## Métricas

Ambos servicios exponen `GET /metrics` en formato Prometheus vía `prometheus_client` (ver `app/core/metrics.py` de cada uno). El `MetricsMiddleware` registra volumen de requests HTTP (`<servicio>_http_requests_total`, etiquetado por método/ruta/status) y latencia en segundos (`<servicio>_http_request_duration_seconds`), usando el patrón de ruta de FastAPI. Las rutas no emparejadas se agrupan bajo `__unmatched__` para mantener acotada la cardinalidad, y las excepciones no controladas se registran con status `500` antes de propagarse.

Las métricas de dominio (p. ej. `backend_ingest_jobs_total`, `backend_assistant_queries_total`) se incrementan en el propio handler de negocio, no en el middleware — el middleware solo conoce método/ruta/status, no intención de negocio.

Prometheus scrapea ambos `/metrics` en el stack local (`docker-compose.yml`, `apps/monitoring/prometheus/prometheus.yml`), y Grafana visualiza un dashboard mínimo provisionado como código (`apps/monitoring/grafana/`).

Introducido en JUP-043.

## Alertado de fallos de ingesta

El `processor` expone un contador dedicado `processor_ingest_jobs_failed_total` (`app/core/metrics.py`), incrementado en `JobRepository.mark_failed()` cada vez que un job de ingesta termina en estado `failed` — independiente del contador genérico de requests HTTP, porque el worker consume de RabbitMQ y no siempre pasa por una request.

Sobre ese contador hay una regla de Grafana Unified Alerting provisionada como código en `apps/monitoring/grafana/provisioning/alerting/ingest-failures.yml`, sin pasos manuales de configuración. La condición usa `increase()` sobre una ventana móvil, no el valor absoluto del contador (que es monótono creciente y solo se resetea si el proceso se reinicia):

```
increase(processor_ingest_jobs_failed_total[5m]) > 2   # for: 2m
```

Valores de partida (ajustables sin tocar código, solo el YAML): ventana de 5 minutos, umbral de 2 fallos, confirmación de 2 minutos antes de pasar a `Firing`. Sin datos reales de volumen de ingestas todavía, son conservadores y revisables.

**Sin receptor externo**: el estado de la alerta (`Normal`/`Pending`/`Firing`) es visible en el dashboard de Grafana, pero no se envía a Discord ni a ningún otro canal — decisión explícita del equipo, para no reabrir la política de solo-lectura de Discord fijada en JUP-081. Revisable en el futuro en una tarjeta propia.

Introducido en JUP-045.

## Secretos y arranque

Backend y processor usan Pydantic Settings y SecretStr. No hay DSN ni JWT
implicitos: los clientes reciben el valor desenvuelto solo en su constructor
y JWT solo en las funciones de firma/verificacion. No serializar Settings,
ValidationError.errors(), bodies, cabeceras Authorization o cookies.
Python no lee dotenv por defecto; usar una ruta explicita en
`ECONOMICON_ENV_FILE`. El entorno prevalece y se ignoran claves ajenas del
fichero compartido. Las variables propias siempre se validan.

`RUNTIME_ENVIRONMENT=production` por defecto, independiente de IA.
Test requiere fixtures sinteticas explicitas, conserva formato/validacion
de proveedores y no se infiere de pytest. La unica excepcion de DB sin
autenticacion requiere development/test, `ALLOW_INSECURE_LOCAL_DATABASE=true`
y destino exacto localhost, 127.0.0.1, ::1 o cockroachdb. Esta URL no prueba
aislamiento: el operador confirma datos desechables, proyecto privado y puertos
loopback. Produccion rechaza el opt-in. No usar el Compose inseguro en un
entorno compartido. TLS, provisioning y secret manager necesitan otro alcance.

Los imports no crean clientes. Lifespan y entrypoints validan antes de abrir
recursos, y fallan con diagnosticos estables incluso antes de configurar
logging. El worker combinado inicializa antes de arrancar su thread y se
detiene y espera al salir el servidor. No interpretar un import correcto como
readiness o conexion verificada.

| Credencial | Fuente y propietario |
| --- | --- |
| AUTH_SECRET_KEY | Operador del backend; clave externa aleatoria de al menos 32 caracteres, sin placeholders |
| DATABASE_URL | Operador Cockroach; usuario/password del servidor, salvo excepcion local explicita |
| VECTOR_DATABASE_URL / POSTGRES_PASSWORD | Operador pgvector; passwords coincidentes, nunca el default postgres |
| RABBITMQ_URL / RABBITMQ_DEFAULT_USER / RABBITMQ_DEFAULT_PASS | Operador RabbitMQ; usuario/password coincidentes, nunca guest/guest |
| RABBITMQ_ERLANG_COOKIE | Operador RabbitMQ; cookie privado externo obligatorio, conservar el existente sin fallback publicado |
| DEMO_PASSWORD | Operador de la cuenta; requerida solo para crear con seed opt-in |
| GRAFANA_ADMIN_PASSWORD | Valor existente conservado en .env local ignorado; no generar ni rotar como parte del traslado |
| LITELLM_API_KEY | Clave virtual del processor; solo obligatoria para proveedor litellm |
| OPENROUTER_API_KEY / LITELLM_MASTER_KEY | Solo gateway; nunca aplicaciones o build |
| AZURE_COST_* tokens y skiptoken | Fixtures sinteticas del simulador publico local/test, nunca Azure real |

Generar secretos nuevos externamente en el entorno seguro del operador y
entregarlos por variables/ficheros locales restringidos, sin terminales
compartidos, capturas o argumentos de proceso. Esa indicacion NO se aplica al
traslado Grafana: conservar su valor existente. Al preparar DSN, URL-encodear
por separado usuario y password (por ejemplo con urllib.parse.quote,
safe=""), no la URL completa. Mantener el mismo valor sin codificar en el
servidor. Usar hosts Compose para contenedores y loopback/puertos publicados
para clientes nativos. No imprimir `docker compose config` expandido con
secretos reales; usar `docker compose config --quiet`.

Compose exige `RABBITMQ_ERLANG_COOKIE` no vacio. Para una instalacion
existente, el operador obtiene el cookie privado que ya usa RabbitMQ y lo
aporta mediante una fuente privada excluida de Git, contextos Docker y bundles,
sin imprimirlo ni incluirlo en evidencias. El entorno conserva precedencia.
Una instalacion nueva requiere un valor privado externo. Esta reconciliacion
no genera, sustituye ni rota cookies, no modifica el .env real y no altera
clustering, persistencia o volumenes. Si el cookie existente coincide con un
valor publicado, escalar antes de arrancar: cambiarlo o conservarlo mediante
una excepcion requiere autorizacion; no recuperar el fallback versionado.

Los DSN de CockroachDB y pgvector solo admiten `sslmode`,
`connect_timeout` y `application_name` en la query, sin valores repetidos.
Host, puerto, usuario, password y base deben venir de la autoridad/ruta del
DSN. Se rechazan overrides y selectores como `hostaddr`, `service`,
`passfile` y destinos multiples via query antes de construir clientes;
no se cargan perfiles ni passwords alternativas desde estos parametros.

Git excluye .env y variantes salvo ejemplos vacios. Los contextos Docker
excluyen tambien dotenv anidados antes de COPY. Nunca introducir secretos
en ARG, ENV de imagen o VITE_*, ni confiar en borrarlos de una capa posterior.
Al configurar Grafana no sobrescribir un .env existente, no resetear su
cuenta o volumen y no deshabilitar autenticacion. La precedencia del entorno
permanece; trasladar una password debil no mejora su fortaleza.

## Diagnosticos acotados

La redaccion final de structlog y logging estandar ocurre tras interpolacion
y formateo de excepciones y antes de JSONRenderer. Oculta campos sensibles
anidados y valores SecretStr activos, passwords parseadas de DSN y sus formas
URL-encoded; tambien omite URLs completas. Conserva nivel, logger, servicio,
timestamp, request_id, tipo y mensaje saneado de excepcion y traceback sin
locales. No se promete encontrar secretos arbitrarios desconocidos ni todas
sus codificaciones. Evitar registrar valores sensibles desde el origen.

Logs de acceso usan la ruta plantilla o __unmatched__. HTTP 422 devuelve
diagnosticos sin input/ctx ni claves de usuario; HTTP 500 devuelve un mensaje
estable y registra tipo de error sin body/cabeceras. Los jobs de ingesta
persisten ingestion_failed, nunca str(exc). El access_token legitimo de login
conserva su contrato y no debe redaccionarse en la respuesta al usuario.

Para verificar: suites Python con fixtures explicitas, logs stdout/stderr con
sentinelas, topologia `corepack pnpm docker:validate` y
`corepack pnpm llm-gateway:test`. El scan de fuentes, contextos, capas y
bundle necesita controles positivos sinteticos y resultados por ruta/categoria
sin valores. Tests unitarios no acreditan aislamiento real, capas construidas
ni rotacion desplegada.

## Rotacion de la cuenta demo

El seed esta apagado por defecto. Para una cuenta nueva activar
DEMO_SEED_ENABLED con DEMO_PASSWORD externa no heredada; el email es
operator@example.com y el formulario no precarga password. Reiniciar solo
crea datos/asociaciones ausentes, sin sobrescribir hash, identidad o rol.
Cambiar DEMO_PASSWORD no cambia la password persistida.

Fuera de test, la deteccion del hash de la password demo heredada bloquea el
arranque incluso con seed apagado. Un operador autorizado debe confirmar el
ID y rotarlo explicitamente usando las funciones existentes. Con los servicios
consumidores detenidos y configuracion externa preparada, ejecutar el siguiente
codigo desde apps/backend en una sesion Python privada. No poner la nueva
password en comandos, SQL literal o historial:

```python
from getpass import getpass
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.core.runtime_secrets import PLACEHOLDERS

settings = get_settings()
user_id = input("ID exacto de la cuenta autorizada: ").strip()
password = getpass("Nueva password: ")
if not password.strip() or password.lower() in PLACEHOLDERS:
    raise SystemExit("Password no valida")
if password != getpass("Repetir nueva password: "):
    raise SystemExit("No coincide")
engine = create_engine(settings.database_url.get_secret_value(), hide_parameters=True)
try:
    with engine.begin() as connection:
        user = connection.execute(
            text("SELECT id, email FROM users WHERE id = :id"),
            {"id": user_id},
        ).mappings().one()
        if input(f"Confirmar rotacion de {user['email']} escribiendo su ID: ") != user_id:
            raise SystemExit("Cancelado")
        connection.execute(
            text("UPDATE users SET password_hash = :hash WHERE id = :id"),
            {"hash": hash_password(password), "id": user_id},
        )
        stored = connection.execute(
            text("SELECT password_hash FROM users WHERE id = :id"),
            {"id": user_id},
        ).scalar_one()
        if not verify_password(password, stored):
            raise RuntimeError("Verificacion fallida; transaccion cancelada")
finally:
    engine.dispose()
    del password
```

Reiniciar backend y verificar login manual, identidad y roles sin registrar
el token. No borrar usuarios, migrar el esquema ni resetear volumenes.
Si la verificacion falla, corregir bajo control del operador con una password
valida no comprometida; no restaurar la password heredada.

## Rotacion de otras credenciales

JWT: sustituir la clave externa y reiniciar todos sus consumidores de forma
coordinada. Los tokens firmados con la clave anterior dejan de ser validos;
no cambia TTL ni claims. Verificar nuevo login y rechazo de tokens anteriores.

DB y RabbitMQ: actualizar primero la credencial con la herramienta administrativa
del servicio propietario, preparar DSN y variables de todos los consumidores,
reiniciar de forma coordinada y comprobar health y una operacion autorizada.
POSTGRES_PASSWORD es configuracion inicial: cambiar env no rota usuarios de
un volumen existente. Usar la operacion administrativa de cambio de password
del servidor sobre el usuario exacto. RabbitMQ tambien requiere actualizar
su usuario existente; no basta con cambiar variables de inicializacion.
No borrar volumenes. Si falla, el operador debe restaurar coordinadamente
una credencial valida no comprometida, nunca defaults inseguros.

Gateway: crear/rotar la clave en su propietario, actualizar consumidores,
verificar una peticion no sensible y retirar la clave antigua. Upstream,
master y virtual son credenciales independientes. No hay despliegue de
proveedor real en JUP-053.

Grafana: el traslado aprobado solo conserva la password existente en .env.
Cambiar esa variable no rota una cuenta persistida. Una rotacion futura
requiere una accion explicita del administrador en Grafana y autorizacion
separada; no forma parte de este traslado ni autoriza reset de volumen.

## Trazabilidad extremo a extremo (ingesta)

El `request_id` de la petición HTTP que crea un job (`POST /jobs/ingest`) viaja dentro del mensaje publicado a RabbitMQ (`job["request_id"]`). El `ProcessorWorker` (`apps/processor/app/workers/runner.py`), al consumir cada mensaje, hace `clear_contextvars()` seguido de `bind_contextvars(request_id=...)` con ese valor (o uno generado si el mensaje no lo trae) antes de procesar el job — todos los logs de `IngestTask`, `PipelineRunner` y sus dependencias heredan el `request_id` automáticamente, igual que ocurre con las peticiones HTTP.

No se persiste el `request_id` en la tabla `jobs`; vive solo en el mensaje de cola y en los logs.

Introducido en JUP-044.
