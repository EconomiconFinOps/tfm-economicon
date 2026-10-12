# JUP-113 — Acotar los reintentos de la cola de ingesta

Trello: https://trello.com/c/JaHmg0fs
Fecha de apertura: 2026-10-11. Rama: `fix/JUP-113-bounded-ingestion-retries`.
Base: `develop` en `8511fb1fc4141781bc76cde33b4c14855697330b` (el commit de rama
`b09e1776942bedfc238d321cfb1ac4397b5aabfb` solo añade el change de OpenSpec). Change:
`openspec/changes/jup-113-bounded-ingestion-retries/`.

Evidencia técnica de implementación; no sustituye a las reviews humanas `Revision JUP-113` y
`Validacion JUP-113`, que siguen pendientes. PR y CI: se rellenan al abrir la PR.

Entorno de medición: Docker 29.8.1 (Docker Compose 5.5.1) en Windows 11, proyecto Compose
aislado `jup113-repro`, con volúmenes nuevos y puertos de host distintos de los del proyecto
principal. No se usan los volúmenes de `tfm-economicon` ni de `jup104-e2e`.

## Estado

Grupos 1 a 8 ejecutados (reproducción y decisión, admisión del origen, fallo permanente de entrada, tope de un
reintento, forma del resultado guardado, servicios reales, documentación y verificación final); gate posterior a la revisión, archivo y PR pendientes. Todo lo que
figura abajo está ejecutado; lo que no consta como ejecutado no se da por hecho. Los
proveedores de LLM y de embeddings del stack son `mock`, y el worker es un único hilo
(`apps/processor/app/run_all.py`).

## Reproducción de `RF-086-004` antes de la corrección (tarea 1.2)

Stack: `docker compose -p jup113-repro` con CockroachDB, RabbitMQ 3.13.7, pgvector, Azure Cost API,
backend y processor construidos desde la base. Usuario demo `operator@example.com`, que pertenece a
`tenant-core` y `tenant-growth`.

1. `POST /jobs/ingest` en `tenant-core` con `source` igual a `Azure Cost Management`:
   **202** y trabajo `queued`. Es el valor que `RF-086-004` cita como ejemplo.
2. El mensaje se procesa una y otra vez. Marcas de tiempo de tres vueltas consecutivas en el
   registro del processor: `22:02:31.9`, `22:02:33.9`, `22:02:35.9` (unos 2,03 s entre vueltas, que
   es la espera de `run_forever` tras la excepción). Cada vuelta emite `job_processing` y
   `worker_loop_failed` con `exception_type: RuntimeError`, que es el `ingestion_failed` aplanado.
3. La fila del trabajo queda en `failed` con `{"error": "ingestion_failed"}` y su `updated_at`
   cambia en cada vuelta (`2026-10-11 22:02:33.95` en la lectura tomada).
4. Con un solo trabajo, 26 eventos `worker_loop_failed` y `processor_ingest_jobs_failed_total` en
   25 en unos 52 s. El contador sube con cada vuelta (0 antes; 30 cuando se publicó el segundo
   trabajo; 66 al terminar la observación). Es la métrica que alimenta la alerta de ingesta de
   JUP-045.
5. **Retención de la cola.** Con el bucle activo se publicó un trabajo válido de `tenant-growth`
   (`source` igual a `local-smoke`, 202). Se leyó su estado cada 10 s durante 60 s: `queued` en las
   seis lecturas, mientras el envenenado seguía en `failed` y la cola mostraba 2 mensajes. El
   trabajo válido no avanzó.
6. Se paró el worker (`docker compose stop processor`) para cortar el bucle; la cola conserva los
   dos mensajes (`processor:jobs`, 2 listos, 0 sin confirmar). Se dejan así a propósito para la
   tarea 6.4, que comprueba que un trabajo envenenado ya presente se descarta con la corrección.

Qué acredita: el finding se reproduce tal como está descrito, con el desenlace que afecta a otros
tenants. Qué no acredita: no se midió cuánto tarda en notarse con carga real ni se probó con un
LLM real; el fallo ocurre antes de llamar al proveedor, así que el proveedor no interviene.
Tampoco se reproduce `RF-054-001`, que exige un resultado guardado corrupto y se cubre con
pruebas unitarias en el grupo 5.

## Marca de reentrega del broker (tarea 1.3)

Hipótesis de la decisión 4 del `design.md`. Sonda con pika 1.4.4 (la versión del processor) contra
RabbitMQ 3.13.7 real, en una cola de prueba duradera propia `jup113:redelivery-probe`, declarada
igual que `RabbitMQQueue` y borrada al terminar; no toca `processor:jobs`. Se ejecutó dentro de la
imagen del processor con `docker compose run --rm --no-deps -T processor python -I -`:

```text
pika 1.4.4
1. primera entrega            redelivered = False
2. tras nack(requeue=True)    redelivered = True
3. segundo nack(requeue=True) redelivered = True
4. tras cerrar sin ack        redelivered = True
5. tras nack(requeue=False)   mensaje presente = False
6. mensaje nuevo              redelivered = False
```

La hipótesis se cumple: `redelivered` vale `False` solo en la primera entrega y `True` en toda
reentrega, tanto tras un `nack` con reencolado como tras cerrar la conexión sin responder. El caso 4
confirma lo que dice el `design.md`: un mensaje cuya primera entrega se interrumpió llega como
reentrega, de modo que ese primer fallo ya se descartaría. El tope es una reentrega como máximo y
no garantiza ninguna.

Límite: la sonda usa `basic_get`, como el worker, y una sola conexión a la vez; no prueba otro
modo de consumo ni un broker en clúster.

## Pruebas con servicios reales (tareas 6.1 a 6.3)

Archivo nuevo `apps/processor/tests/test_ingestion_retry_integration.py` (15 casos), opt-in: se omite sin las
variables y **CI no lo ejecuta** (no levanta CockroachDB, RabbitMQ ni pgvector, `RF-096-004`). Reutiliza las
fixtures de `test_tenant_isolation_integration.py`, que rechazan cualquier destino no desechable.

Servicios, creados para esta comprobación con `docker run` (sin volúmenes, solo loopback, borrados al terminar):
CockroachDB `v24.1.11` marcado con `cluster.organization = 'processor-integration-tests'` (puerto 46454),
pgvector `pg17` vacío (45454) y RabbitMQ `3.13.7` (45654). Las pruebas se ejecutan con el entorno virtual
local (Python 3.13.7, Windows) contra esos contenedores; **no** se ejecutaron dentro de un contenedor Linux.

```text
export PROCESSOR_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:46454/defaultdb?sslmode=disable'
export JUP086_VECTOR_TEST_URL='postgresql+psycopg://postgres@127.0.0.1:45454/postgres'
export JUP086_RABBITMQ_TEST_URL='amqp://jup113:jup113test@127.0.0.1:45654/%2F'
cd apps/processor && python -m pytest tests/test_ingestion_retry_integration.py -q -ra -p no:cacheprovider
```

| Ejecución | Resultado |
| --- | --- |
| Esta rama, con servicios reales | **15 pasan** (41 s) |
| Esta rama, sin las variables | 15 omitidas, sin errores |
| **Base** (`develop` en `8511fb1f`, extraída con `git archive`) con las mismas pruebas | **11 fallan y 4 pasan** (31 s) |

La ejecución sobre la base usa una copia aparte donde, solo en la copia, el `import` del nombre nuevo
`IngestionFailed` se sustituye por una clase vacía para que las pruebas lleguen a sus aserciones; el
repositorio no cambia. Los 4 que pasan son los resultados `{"ok": 1}`, `{}`, JSONB `null` y SQL NULL, que ya
funcionaban. De los 11 que fallan, **9 lo hacen por comportamiento** y **2 por API inexistente**:

- **Un envenenado retiene la cola** (`RF-086-004`, 1 caso, comportamiento): `At index 1 diff: 'jup113-poison' !=
  'jup113-valid'`; las 10 entregas procesadas son del envenenado y el trabajo válido de `tenant-b` no llega a
  procesarse.
- **Reintento sin tope** (1 caso, comportamiento, el de la marca real): `assert 10 == 2` sobre las ejecuciones del
  pipeline, que son 10 (el límite del bombeo de la prueba) en lugar de 2.
- **Resultado guardado inválido** (`RF-054-001`, 7 casos, comportamiento): 6 valores que no son objeto (`[1]`,
  `[]`, `123`, `0`, `true`, `false`) se aceptan con `ack` como si fueran un resultado válido (no aparece
  `job_message_rejected`; una sola entrega), y el séptimo, el JSON texto `"x"`, lanza `JSONDecodeError` y se
  reencola 10 veces (`assert 10 == 1` sobre las entregas de ese caso).
- **`QueueMessage` sin `redelivered`** (2 casos, API inexistente, no comportamiento): `AttributeError` en el
  reintento que se completa y en la primera entrega interrumpida, que leen la marca desde el mensaje.

Con servicios reales en esta rama:

1. **Un envenenado no retiene a un válido de otro tenant (6.1).** El envenenado (`tenant-a`, `Azure Cost
   Management`) queda `failed` con `{"error": "ingestion_failed"}`; el válido (`tenant-b`, `local-smoke`) queda
   `completed` y es el único documento en pgvector; se procesan exactamente 2 entregas, ninguna reentrega; el
   proveedor no se llama; aparece `job_input_rejected` y no `worker_loop_failed`; la cola queda vacía.
2. **Un fallo no clasificado se reintenta una vez con la marca real del broker (6.2).** El pipeline se ejecuta 2
   veces y `redelivered` vale `[False, True]` con la marca REAL de RabbitMQ; solo la primera relanza; el trabajo
   queda `failed`, sin documentos en pgvector; aparece `job_retry_exhausted`; el texto de la causa no sale en la
   salida ni en la traza.
3. **El reintento se completa**: falla la primera vez y acierta la segunda; `completed`, un documento, 2
   entregas (`redelivered` `[False, True]`), cola vacía.
4. **Primera entrega interrumpida**: `blocking_pop` sin ack ni nack y cierre de la conexión; la nueva conexión
   recibe el mismo mensaje con `redelivered=True`, y con un pipeline que falla se descarta tras una sola
   ejecución. Confirma con el broker real el límite del diseño: el tope es «una reentrega como máximo», no «dos
   intentos siempre».
5. **JSONB con CockroachDB real (`RF-054-001`)**: `{"ok": 1}`, `{}`, JSONB `null` y SQL NULL terminan en `ack`;
   `[1]`, `[]`, `"x"`, `123`, `0`, `true` y `false` en `nack(requeue=False)` tras una sola entrega, con la fila
   sin cambios, el pipeline sin ejecutar y sin `worker_loop_failed`. Tipos que entrega el controlador
   (`psycopg`): `dict`, `None` (JSONB `null` y SQL NULL son indistinguibles), `list`, `str` (el JSON texto
   `"x"` llega ya decodificado como `x`), `int` y `bool`. Con esto queda ejecutada contra CockroachDB real la
   rama del JSONB ya decodificado que el grupo 5 solo había emulado.

Cada caso comprueba el estado final de la cola con `basic_get` (debe ser `None`), y repite la comprobación
desde una conexión nueva para que un mensaje entregado sin ack ni nack, que el broker devolvería al cerrar, no
se confunda con una cola vacía. Las bases y colas generadas las borran las fixtures: al terminar, CockroachDB
lista solo `defaultdb`, `postgres` y `system`, y pgvector solo `postgres`.

Sensibilidad: un complemento temporal que fuerza `redelivered` a `False` hace fallar los casos 2, 3 y 4 por
aserción (`assert 10 == 2`), no por cuelgue, porque el bombeo corta en 10 entregas.

Límites: servicios de un solo nodo; el proveedor de IA es un doble (la ruta `local-smoke` no lo llama); no se
midió el rendimiento ni la carga; y todo esto se ejecutó a mano, no en CI.

## Recorrido con Compose sobre la rama (tarea 6.4)

Mismo proyecto aislado `jup113-repro` de la reproducción (volúmenes nuevos, puertos distintos), con backend y
processor reconstruidos desde la rama (`1cd18feb`); se conservaron la base y la cola de la reproducción.

**1. Envenenado ya presente en la cola.** Estado inicial, el de la reproducción: `processor:jobs` con 2 mensajes,
el envenenado (`tenant-core`, `Azure Cost Management`, ya `failed`) y un trabajo válido de `tenant-growth`
retenido en `queued`. Al arrancar el worker nuevo:

```text
00:18:43.414 job_processing        (envenenado)
00:18:43.459 job_input_rejected    (una sola vez)
00:18:43.464 job_processing        (el válido de tenant-growth)
```

El envenenado queda `failed` con `{"error": "ingestion_failed"}`; el válido pasa a `completed` y se guarda en
pgvector; la cola queda en 0; `processor_ingest_jobs_failed_total` vale 1 (proceso nuevo) y **no hay ningún
`worker_loop_failed`**. En la reproducción antes de la corrección, el mismo mensaje se repetía cada ~2 s y el
válido siguió `queued` durante los 60 s observados.

**2. La API.** `POST /jobs/ingest` con `source` igual a `Azure Cost Management` responde **422** con
`{"detail":[{"type":"validation_error","msg":"Invalid request value"}]}`; el recuento de la tabla `jobs` no cambia
(2 antes y 2 después). Con `aws-cur`, el valor por defecto de la pantalla, responde 202 y el trabajo termina
`completed`. Con ` Azure-Cost ` responde 202 y la fila guarda el valor literal `[ Azure-Cost ]` (entre
corchetes para ver el relleno) y termina `completed`. Cola en 0 y sin `worker_loop_failed`.

**3. El coste aceptado, con pgvector parado.** Con `docker compose stop postgres-pgvector` y el worker en marcha,
se envía un trabajo válido (`aws-cur`):

```text
00:19:31.207 job_processing           (primer intento)
00:19:35.234 worker_loop_failed       (relanza: la causa es el almacén vectorial, no se registra)
00:19:37.236 job_processing           (reentrega, con la marca de RabbitMQ)
00:19:41.267 job_retry_exhausted      (descartado sin relanzar)
```

El trabajo queda `failed` unos 10 s después del envío, la cola queda en 0 y el contador sube 2 (cada intento
registra `failed`). Al volver pgvector, el worker se recupera solo: un trabajo enviado después se completa. El
trabajo descartado durante la caída **sigue `failed` y no se reprocesa**: hay que reenviarlo. Es el coste que
recoge el ADR-0019. La cifra «unos 2 s» de la aprobación era inexacta (ver la adenda de `proposal.md`).

**4. Lo que muestra la pantalla de ingesta ante el 422** (leído en el código, **no ejecutado en navegador**):
`IngestPage.tsx` pinta `mutation.error.message` en rojo, y `ApiError` lleva el cuerpo crudo de la respuesta
(hasta 512 caracteres) como mensaje. El usuario vería `{"detail":[{"type":"validation_error","msg":"Invalid
request value"}]}`, sin que se nombre el campo Source ni el formato admitido. No se cambia la pantalla (fuera
de alcance); se registra como finding en la tarea 7.5. El campo Source es un texto libre con `aws-cur` por
defecto, así que el valor por defecto sigue siendo válido.

Limitaciones: no se probó un fallo de embeddings reales ni un LLM real (proveedores `mock`); no hay frontend ni
navegador en este recorrido; el comportamiento de la pantalla es lectura de código; y la comprobación se hizo
con un único worker y a mano.

### Comandos y su procedencia (tareas 6.1 a 6.4)

Qué consta con su comando y qué no, para que nadie dé por reproducible lo que no lo es.

- **Servicios desechables:** `docker run -d --name jup113-it-crdb -p 127.0.0.1:46454:26257
  cockroachdb/cockroach:v24.1.11 start-single-node --insecure --store=type=mem,size=1GiB`;
  `docker run -d --name jup113-it-pg -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:45454:5432
  pgvector/pgvector:pg17`; `docker run -d --name jup113-it-mq -e RABBITMQ_DEFAULT_USER=jup113 -e
  RABBITMQ_DEFAULT_PASS=jup113test -p 127.0.0.1:45654:5672 rabbitmq:3.13-management`; marca del nodo:
  `cockroach sql --insecure -e "SET CLUSTER SETTING cluster.organization = 'processor-integration-tests'"`. Se
  retiraron con `docker rm -f` al terminar.
- **Base:** `git archive 8511fb1f apps/processor apps/backend docs/api` extraído en una carpeta aparte, con el
  archivo de pruebas nuevo copiado dentro y, solo allí, el `import` de `IngestionFailed` sustituido por una
  clase vacía; mismo comando `pytest` y mismas variables de entorno.
- **Compose (6.4):** `docker compose -p jup113-repro --env-file <copia de .env con otros puertos> up -d --build
  --wait backend processor`; la API con `curl -X POST http://127.0.0.1:18000/jobs/ingest` con los cuerpos de la
  sección anterior, `Authorization: Bearer <token del usuario demo>` y `X-Tenant-Id`; los estados de los
  trabajos con `cockroach sql --insecure --format=csv -e "SELECT ... FROM jobs WHERE id = '...'"`; la cola con
  `rabbitmqctl list_queues name messages messages_unacknowledged`; el contador con
  `curl http://127.0.0.1:18001/metrics`; los eventos con `docker compose logs processor`; la caída con
  `docker compose stop postgres-pgvector` y `start postgres-pgvector`.
- **No consta el comando exacto:** el complemento temporal que fuerza `redelivered` a `False` (lo escribió el
  tester en memoria, fuera del repositorio, y no se conserva), y la comprobación de que no quedaban bases
  huérfanas tras la ejecución (declarada por el tester; el orquestador no la repitió antes de borrar los
  servicios). La sensibilidad de los casos de reintento queda además respaldada por la ejecución sobre la base,
  que sí consta.

## Verificación final (grupo 8)

Fecha: 2026-10-11 (hora local). Rama `fix/JUP-113-bounded-ingestion-retries`; `develop` sin cambios desde la base
(`8511fb1f`, comprobado con `git fetch` antes y después de la batería).

**Suites completas en contenedor `python:3.12` (equivalente a CI), sobre una copia del árbol, en serie:**

| Suite | Base `8511fb1f` | Rama | Diferencia |
| --- | --- | --- | --- |
| Backend (`python -m pytest tests -q`) | 1132 pasan, 64 omitidas, 0 fallan | **1169 pasan, 64 omitidas, 0 fallan** | +37: `test_ingest_source_admission.py` |
| Processor | 644 pasan, 65 omitidas, 0 fallan | **816 pasan, 80 omitidas, 0 fallan** | +172 = 37 + 32 + 41 + 56 + 6; +15 omitidas = `test_ingestion_retry_integration.py` sin servicios |

`compileall` correcto en ambos. Las 64 y 80 omitidas son las pruebas opt-in con servicios reales; no se
presentan como aprobadas. No se ejecutó `azure-cost-api` (este change no lo toca) ni el frontend en contenedor.
La primera ejecución del processor dio 3 errores idénticos en la rama y en la base: era un fallo de mi copia, que
no incluía la carpeta `fixtures/` de la raíz, y se corrigió; no eran del código.

Otras comprobaciones (Windows, Python 3.13.7): `corepack pnpm lint` y `corepack pnpm typecheck` correctos,
`openspec:validate` 64 de 64, `jup:check` del change, `jup:cleanup:check` (1209 archivos) y las pruebas de esas
dos herramientas (7 y 6) correctos. En esa máquina la batería del backend falla 145 pruebas `*_jup047.py` por
`RF-105-004`; no es de este change y pasan en Linux.

**Alcance del diff contra la base** (`git diff --stat 8511fb1f HEAD`): el producto cambiado son exactamente los
cinco archivos previstos, `apps/backend/app/schemas/jobs.py` y, en el processor, `agents/guardrails.py`,
`tasks/ingest.py`, `clients/rabbitmq_queue.py` y `workers/runner.py` (125 inserciones y 12 borrados); 8 archivos de
pruebas nuevos y **una sola aserción modificada en una prueba existente**
(`test_secret_boundaries.py`, línea 439, por decisión de Victor registrada en la aprobación); y nada de
dependencias, CI, frontend, Compose, migraciones, variables de entorno ni esquema.

## Criterios de la tarjeta

Texto de la tarjeta de Trello adaptado al alcance aprobado: el criterio 5 se cumple siempre que el estado del
job se pueda registrar (ver la adenda de `proposal.md`). «Cumplido» significa ejecutado y con el resultado
citado; no significa revisado ni validado por una persona.

| # | Criterio | Evidencia | Estado |
| --- | --- | --- | --- |
| 1 | `POST /jobs/ingest` con `Azure Cost Management` responde 422 saneado y no crea trabajo, no reserva y no publica | `test_ingest_source_admission.py` (20 rechazados: 422 con el cuerpo exacto, `no_effects` y tabla `jobs` sin cambios, valor ausente de la respuesta y los registros). En Compose: 422 y la tabla `jobs` pasa de 2 a 2 filas | Cumplido. «No reserva ni publica» consta con la cola doblada de las pruebas; en Compose solo se comprobó que no se crea trabajo |
| 2 | Un `source` admitido sigue dando 202 y se guarda como se envió | 16 aceptados en la misma prueba (fila, payload y mensaje publicado literales); en Compose `aws-cur` y ` Azure-Cost ` dan 202, completan y el segundo se guarda literal | Cumplido |
| 3 | Un trabajo ya guardado con `source` no admitido queda `failed` y se descarta sin reencolar en una entrega | `test_ingest_permanent_input_failure.py` (32); servicios reales (6.1): `failed`, 2 entregas, cola vacía; Compose: `job_input_rejected` una vez | Cumplido |
| 4 | Un `completed` con resultado corrupto o que no es un objeto se descarta sin reencolar y sin cambiar la fila | `test_completed_result_shape.py` (56) y `test_completed_result_exposure.py` (6); CockroachDB real: 7 valores JSONB que no son objeto → `nack(requeue=False)`, fila intacta | Cumplido. **El texto corrupto (`''`, `not json`) solo se prueba con SQLite**: una columna JSONB real no puede almacenarlo |
| 5 | Un error no clasificado se reintenta como máximo una vez; después `failed` y descarte | `test_ingest_bounded_retry.py` (28) y `test_queue_message_redelivered.py` (13); broker real: `redelivered` `[False, True]` y 2 ejecuciones; Compose con pgvector parado: descarte a los ~10 s | Cumplido para el caso en que el estado se puede registrar. **Reencolar sin tope cuando no se puede leer o registrar el estado** está probado con fallos doblados de la base, **no con una caída real de CockroachDB** |
| 6 | Un fallo transitorio que se resuelve dentro del tope se completa en el reintento | Caso del reintento que se completa, con servicios reales: `completed`, un documento, 2 entregas | Cumplido |
| 7 | Los mensajes inválidos y los fallos de proveedor se comportan igual | Casos con `redelivered` falso y verdadero en `test_ingest_bounded_retry.py`; la mutación los cubre | Cumplido con dobles. **No se ejecutaron con servicios reales** |
| 8 | Con RabbitMQ real, un envenenado seguido de un válido de otro ámbito: el válido se completa | Servicios reales (6.1) y Compose: el trabajo retenido de `tenant-growth` se completa a los 50 ms del descarte; sobre la base, las mismas pruebas fallan | Cumplido |
| 9 | La decisión sobre el tope y su coste queda en un ADR enlazado a esta tarjeta | `docs/adr/ADR-0019-ingestion-retry-policy.md`, con el coste medido (~10 s con pgvector parado) | Cumplido en el documento. **El ADR sigue `Proposed`: la ratificación es de la revisión de la PR** |
| 10 | `RF-086-004` y `RF-054-001` pasan a `Fixed` con enlace a la evidencia | `openspec/findings/backlog.md` | Cumplido como **Fixed técnico**; integración y validación humana pendientes |

## Lo que no se ha validado

- **Ninguna revisión ni validación humana.** No existen `Revision JUP-113` ni `Validacion JUP-113`; la PR aún no está abierta y el CI de GitHub no se ha ejecutado sobre esta rama.
- **Las pruebas con servicios reales no corren en CI** (`RF-096-004`) y se ejecutaron a mano, en Windows contra contenedores, no dentro de un contenedor Linux.
- Una **caída real de CockroachDB** (decisión 4), un proveedor de embeddings o un LLM reales, un clúster de varios nodos, la carga y el rendimiento.
- La **pantalla de ingesta en navegador**: lo que muestra ante el 422 se leyó en el código (`RF-113-001`).
- Un mensaje que mata el proceso antes de que el worker responda al broker: sigue sin tope y no se ha reproducido.
- El **frontend** no se ha tocado ni se ha ejecutado en este change.
- La integración con `develop`: no se ha hecho `Update branch` ni se ha simulado un merge.

## Entorno de pruebas

El proyecto Compose `jup113-repro` y sus volúmenes siguen en la máquina de Victor; se borran con
`docker compose -p jup113-repro down -v`. Los tres servicios desechables de las pruebas reales ya se retiraron.
Enlaces de PR y de CI: se rellenan al abrir la PR.
