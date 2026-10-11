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

Grupo 1 (reproducción y decisión) en curso: tareas 1.1 a 1.3 ejecutadas, ADR pendiente (1.4). Todo
lo que figura abajo está ejecutado; lo que no consta como ejecutado no se da por hecho. Los
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
