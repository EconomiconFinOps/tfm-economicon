# Revision de jup-050-reproducible-local-runtime

JUP: JUP-050
Trello: https://trello.com/c/4VYnTkuD

## Resumen

- RabbitMQ arranca a la primera desde cero: su healthcheck corre como `rabbitmq` y ya no crea un cookie de root (RF-096-001). Su estado vive en `rabbitmq-data` con `hostname` fijo.
- El processor tiene 300 s de `start_period` para sus migraciones iniciales (RF-050-001).
- `local:doctor` diagnostica `.env`, puertos y volumenes antes de arrancar, con las reglas de Compose y las de arranque del backend, sin mostrar valores.
- `local:smoke` recorre el camino minimo: salud, login demo, ingesta de costes, resumen con datos y un job por RabbitMQ hasta el processor.
- README con el recorrido desde clon limpio y que conserva o borra cada forma de parar; RF-090-001 cerrado con control positivo.

## Decisiones

- Decisiones de Lucia (2026-10-01): alcance completo de la tarjeta; `.env` sigue siendo manual, sin generar secretos (frontera de JUP-053), con un diagnostico; volumen con nombre para RabbitMQ; smoke con salud, login, ingesta de costes y job.
- La spec se amplio durante la implementacion: el diagnostico lee de `docker-compose.yml` las variables obligatorias y los puertos (incluye `PROMETHEUS_PORT` y `GRAFANA_PORT`, que faltaban en la lista inicial), detecta puertos duplicados y sigue informando si Docker no responde.
- ADV-4: Lucia eligio portar al diagnostico las reglas de arranque del backend, con un test que falla si cambian las listas de `runtime_secrets.py`.
- ADR: no aplica. Son ajustes de la topologia local dentro de JUP-049 y ADR-0011; el servicio `migrate`, que si lo necesitaria, se descarto en el diseño.

## Validacion

Comandos y resultados en la [evidencia](../../../docs/evidence/JUP-050-validation.md): tests en rojo y en verde de cada grupo, mutantes, reproduccion de RF-096-001 antes (3/3 `eacces`) y despues (0/3), arranque en frio de 489 s en un solo `up --wait`, smoke repetido, control negativo con el processor parado, job en cola que sobrevive a `down`/`up`, `down -v` y control positivo del lockfile.

## Adversarial Review (pass 1)

Base `1e897dc`, head `71f0f2f`. Veredicto: `changes-requested`.

| ID | Sev. | Estado | Descripcion | Reproduccion | Incumple |
|---|---|---|---|---|---|
| ADV-1 | HIGH | CONFIRMED | El doctor lee `.env` sin la interpolacion `$VAR`/`${VAR}` que aplica Compose: falsos desacuerdos con valores validos, desacuerdos reales no detectados y `$UNSET` contado como presente. | `.env` con `RABBITMQ_URL=amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@...`, `POSTGRES_PASSWORD='ab$cd'` y `VECTOR_DATABASE_URL=...:ab$cd@...`: `docker compose config` resuelve la primera valida y la segunda con password `ab`; el doctor da dos falsos desacuerdos y no ve el real. | Decision 5 del diseño; escenarios de credenciales y de variables obligatorias. |
| ADV-2 | HIGH | CONFIRMED | Una `@` sin codificar en la password de `VECTOR_DATABASE_URL` se da por buena: WHATWG `URL` corta en la ultima `@` y SQLAlchemy `make_url` en la primera. | `POSTGRES_PASSWORD=p@ss` y `...postgres:p@ss@postgres-pgvector...`: doctor 0; `make_url` da `password='p'`, `host='ss@postgres-pgvector'`. | Escenario "Credentials that do not agree"; README. |
| ADV-3 | HIGH | CONFIRMED | En Windows, un proceso en `::` con dual stack no se detecta; Compose falla despues con "ports are not available". | Servidor Node en `::`:47123: `isPortFree` da `true` en `0.0.0.0` y `127.0.0.1`; `docker run -p 47123:...` falla. Afecta a los cuatro puertos de aplicacion. | Escenario "Busy host port". |
| ADV-4 | MEDIUM | CONFIRMED | El doctor no aplica las reglas de arranque del backend (`runtime_secrets.py`, `config.py`): da `[OK]` y el backend no arranca. | guest/guest, `postgres`, `changeme`, `AUTH_SECRET_KEY` de 40 espacios o 16 emojis, salto de linea, `DATABASE_URL` `postgresql://` o remota con `sslmode=disable`, `VECTOR_DATABASE_URL` `mysql://`, `RABBITMQ_URL` `http://`. | Goal del diseño. |
| ADV-5 | LOW | CONFIRMED | El smoke exige `DEMO_SEED_ENABLED` exactamente `true`; el backend acepta `True`, `1`, `yes`. | `runSmoke` con esos valores falla con el seed activo. | Escenario "Demo seed disabled" (falso negativo). |
| ADV-6 | LOW | PLAUSIBLE | La consulta de `jobs` usa `defaultdb`; con otra base en `DATABASE_URL` agota 120 s y atribuye mal la causa. | Por lectura de codigo. | Robustez del mensaje. |
| ADV-7 | LOW | CONFIRMED | El backlog enlaza `docs/evidence/JUP-050-validation.md`, que no existia. | `git ls-tree` del head. | Trazabilidad. |

Ataques que resistieron (resumen del revisor): healthcheck con `gosu` frente a seis pings inmediatos en volumen nuevo, con control positivo sin `gosu` (sale con 1 y cookie `root:root`); cambio de cookie con volumen existente; mensaje durable tras recrear el contenedor; `.env.example` copiado y Docker caido; BOM, CRLF, comillas y comentarios; `+`, `#` y `/` en passwords; opt-in en mayusculas; puertos de loopback frente a holders en `0.0.0.0` y `::`; UUID antes del SQL; errores sin mensaje crudo; esperas acotadas; tablas de versiones de migraciones separadas.

Barrido del revisor: `parseDotenv` tambien lo usa el smoke (mismo defecto con `DEMO_PASSWORD` con `$`); el parser de URL frente a `make_url`/`urlsplit` de backend y processor; `isPortFree` es la unica comprobacion de puertos de `tools/`; las reglas de secretos estan en `runtime_secrets.py` de backend y processor (identicos) y en `config.py` del backend.

### Correcciones de la pasada 1

Cada una con test en rojo antes del cambio y mutantes detectados:

- ADV-1: `parseDotenv` interpola `${VAR}`, `$VAR`, `${VAR:-x}`, `${VAR-x}`, `$$` y `\$` como `docker compose config` (casos contrastados con Compose real), mirando antes el entorno del proceso. El smoke usa la misma funcion.
- ADV-2: cualquier `@` sin codificar en usuario o password de una DSN se rechaza, en las tres URL.
- ADV-3: los puertos publicados en todas las interfaces se prueban tambien en `::` con dual stack; sin IPv6 en el host, esa sonda no cuenta.
- ADV-4: reglas de `runtime_secrets.py` y `config.py` portadas, con 19 casos y un test que compara las listas de backend y processor.
- ADV-5: el smoke acepta los valores verdaderos del backend, compartidos con el doctor.
- ADV-6: el smoke consulta `jobs` en la base de `DATABASE_URL` y falla en el acto si no puede leerla.
- ADV-7: evidencia creada.

## Adversarial Review (pass 2)

Base `1e897dc`, head `0848975`. Revisor sin acceso al razonamiento de la implementacion ni a la pasada 1. Veredicto: `changes-requested`.

| ID | Sev. | Estado | Descripcion | Reproduccion | Incumple |
|---|---|---|---|---|---|
| P2-1 | HIGH | CONFIRMED | El doctor no rechaza passwords de ejemplo en `DATABASE_URL`; el backend aplica esa regla a las tres DSN fuera de `test`. | `DATABASE_URL=cockroachdb://root:changeme@cockroachdb:26257/defaultdb?sslmode=disable` en `development`: doctor `[OK]`; `Settings(...)` lanza `database_url contains a known credential placeholder`. | Escenario "Values the backend would reject". |
| P2-2 | MEDIUM | CONFIRMED | El doctor pasa a minusculas el esquema y acepta `COCKROACHDB://`; SQLAlchemy `make_url` conserva las mayusculas y el backend lo rechaza. En `RABBITMQ_URL` `urlsplit` si lo pasa a minusculas. | `DATABASE_URL=COCKROACHDB://root@...`: doctor 0, backend `must be a valid service DSN`. Contrastado tambien con `POSTGRESQL+PSYCOPG` en `VECTOR_DATABASE_URL`. | Mismo escenario. |
| P2-3 | LOW | CONFIRMED | Un `%` sin codificar en la password (`p%zz`) hace que el doctor diga que no es una URL valida; el backend lo tolera. Falso rechazo, coherente con el consejo de codificar. | `RABBITMQ_URL=amqp://u:p%zz@r:5672/`: doctor 1. | Ninguno estricto. |
| P2-4 | LOW | PLAUSIBLE | Un proceso solo en `::1` en el puerto elegido no se detecta en Windows; en Linux el comportamiento depende de la plataforma. | Servidor en `::1:18081`: `isPortFree` da `true` para `0.0.0.0`, `127.0.0.1` y `::`. Sin confirmar en Linux ni con Docker. | Escenario "Busy host port". |
| P2-5 | LOW | CONFIRMED | El README solo da el paso de copiar `.env.example` en PowerShell. | `grep` en README. | Escenario "Documented path". |

Ataques que resistieron (resumen del revisor): BOM, CRLF, `export`, comentarios en linea, comillas y valores multilinea; interpolacion `${VAR}`, `$$` y `$` suelto; precedencia del entorno, incluida la variable vacia; puertos duplicados y valores `0x1F40`, `1e3`, `-1`, `08000`; password codificada, host IPv6 y vhost `%2F`; 16 emoji como `AUTH_SECRET_KEY`; `DEMO_SEED_ENABLED=True` sin password; `DATABASE_URL` sin password a un host remoto; ningun secreto en la salida; endpoints, modulo y argumentos del smoke frente al backend y el processor; UUID antes del SQL; esperas acotadas; coherencia de `hostname`, `rabbitmq-data` y `start_period` con la spec.

Barrido del revisor: el patron de P2-1 solo aparece en `checkConfiguration`; el de P2-2 y P2-3 solo en `parseDsn`; ningun otro `tools/*.mjs` parsea `.env` (el smoke reutiliza `parseDotenv`).

### Correcciones de la pasada 2

- P2-1: la regla de password de ejemplo se aplica a las tres DSN, como el backend, y se relaja en `test`. Tests: `changeme` y `Password` en `DATABASE_URL`, en rojo antes del cambio.
- P2-2: el esquema de `DATABASE_URL` y `VECTOR_DATABASE_URL` se compara tal como esta escrito; el de `RABBITMQ_URL` sigue en minusculas. Tests en rojo antes del cambio, mas un control de que `AMQP://` se acepta.
- P2-5: el README indica `cp -n .env.example .env` para Linux y macOS.
- P2-3 y P2-4 quedan sin corregir: P2-3 es un falso rechazo que empuja a codificar la password (lo que la guia ya pide) y P2-4 no se ha confirmado fuera de Windows. Pendientes de que Lucia los acepte o pida corregirlos.

## Riesgos

- El diagnostico duplica reglas del backend: un test compara sus listas con `runtime_secrets.py` de backend y processor, pero una regla nueva con otra forma requiere actualizar el diagnostico a mano.
- Medidas de tiempo de un solo host (Windows, Docker Desktop).

## Findings

- RF-090-001: cerrado con control positivo.
- RF-050-001: registrado y cerrado (ventana de salud del processor).
- RF-096-001: corregido y evidenciado aqui; su fila llega con el PR #51 y se cerrara al traer `develop`.
