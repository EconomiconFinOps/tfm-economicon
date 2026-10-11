JUP: JUP-113
Trello: https://trello.com/c/JaHmg0fs

# Revisión JUP-113

Registro de evidencia por grupo de tareas, en orden de ejecución. Se completa con la revisión final
(tarea 8.4). Nada de lo que figura aquí se da por ejecutado si no consta su comando y su resultado.

Las pruebas de Python se ejecutan en este equipo con el entorno virtual local (Python 3.13.7), solo
sobre los archivos de cada tarea; la batería completa se ejecuta en un contenedor equivalente a CI
en la tarea 8.1, porque en Windows fallan pruebas ajenas del backend (`RF-105-004`).

## Grupo 1 — Reproducción y decisión

Mutación N/A — grupo sin código de producto (documentación, reproducción y ADR). Tester, coder y QA
no intervienen. Resultados en `docs/evidence/JUP-113-validation.md` y `docs/adr/ADR-0019-ingestion-retry-policy.md`.

## Grupo 2 — Regla de admisión del origen en el backend

### Red (tareas 2.2 y 2.4), 2026-10-11

Cifras históricas del commit Red (la tabla vigente tiene 16 aceptados y 20 rechazados, es decir 37 casos por
prueba, tras el caso de la sección «Mutación»). Tabla compartida `docs/api/ingest-source-contract-cases.json`:
16 aceptados y 19 rechazados, sin
desacuerdos con la regla del processor (comprobada con `strip().lower()` y `fullmatch`).

- `apps/backend/tests/test_ingest_source_admission.py` (nuevo, 36 casos):
  `cd apps/backend && python -m pytest tests/test_ingest_source_admission.py -q`.
  **Resultado Red: 17 fallan y 19 pasan.** Los 17 fallan por el motivo esperado,
  `assert 202 == 422`: la API admite el valor y crea el trabajo. Los fallos son `spaces-inside`,
  `two-words-lowercase`, `newline-inside`, `too-long-65`, `too-long-padded`, `leading-hyphen`,
  `leading-dot`, `leading-underscore`, `slash`, `colon`, `at-sign`, `comma`, `accented-letter`,
  `cyrillic-lookalike`, `zero-width-space`, `nul-character` y `dotted-capital-i`. Pasan `empty` y
  `whitespace-only` (ya se rechazaban), los 16 aceptados (hoy ya se admiten y se guardan literales) y
  el guardián de la tabla.
- `apps/processor/tests/test_ingest_source_contract.py` (nuevo, 36 casos):
  `cd apps/processor && python -m pytest tests/test_ingest_source_contract.py -q`. **36 pasan desde
  el principio**; describe comportamiento existente y por eso es una prueba de contrato y no un Red.
- Contraste: `tests/test_tenant_isolation_api.py` del backend, 16 pasan y 2 se omiten (variantes
  opt-in de CockroachDB), sin cambios.
- Los 36 casos se repitieron por separado por el orquestador con el mismo resultado. No hay cambios
  en `apps/*/app/**`.

Limitación declarada: en Red, las comprobaciones de que no hay efectos, de que la tabla `jobs` no
cambia y de que el valor no aparece en la respuesta ni en los registros solo se ejercitan de verdad
en los dos casos vacíos; en los otros 17 la aserción de estado falla antes. Quedarán probadas en
Green.

Hallazgos del tester a tener en cuenta en Green: la validación debe aplicar exactamente
`strip().lower()` de Python sobre `str` Unicode y `fullmatch` (no `$`, que acepta un salto de línea
final, ni `re.ASCII` ni `re.IGNORECASE`), porque `no-break-space-padding`,
`kelvin-sign-lowers-to-ascii` y `newline-inside` dependen de ello. Un NUL en una columna de texto de
PostgreSQL o CockroachDB podría dar un error de base de datos; con SQLite no, así que esa parte no
queda demostrada por esta prueba.

### Green (tarea 2.3), 2026-10-11

Producto modificado: solo `apps/backend/app/schemas/jobs.py`. `IngestJobRequest.validate_source`
aplica `SAFE_SOURCE.fullmatch(value.strip().lower())` y devuelve el valor original sin normalizar;
un único camino sustituye la comprobación de vacío. El patrón es una copia deliberada del de
`apps/processor/app/agents/guardrails.py`; la tabla compartida vigila que no diverjan.

- `test_ingest_source_admission.py`: **36 pasan, 0 fallan** (antes 17 fallaban con `assert 202 == 422`).
  Con el 422 ya existente se ejercitan de verdad las comprobaciones de no-efectos, de `jobs` sin
  cambios y de que el valor no aparece en la respuesta ni en los registros.
- Contraste, ejecutado por el coder y repetido por el orquestador: `test_tenant_isolation_api.py`,
  `test_job_publication.py`, `test_job_reservation_rejection.py`, `test_jobs_schema.py` y
  `test_ingest_tracing.py`, junto con la prueba nueva: 78 pasan y 4 se omiten (variantes opt-in).
  `test_ingest_padded_source_is_preserved` y `test_ingest_blank_source_is_rejected_without_effects`
  siguen pasando sin cambios.
- Processor, `test_ingest_source_contract.py`: 36 pasan (sin cambios de producto en el processor).
- Suite completa del backend en Windows, ejecutada por el coder: 1023 pasan, 64 se omiten y **145
  fallan**, todas en los cuatro archivos `*_jup047.py` de salud (`RF-105-004`, error
  `ProactorEventLoop ... _ssock`). El coder comprobó con el cambio retirado que dos de esos archivos
  fallan igual en la línea base (36 fallos); los otros dos no se ejecutaron en línea base. No se da
  por demostrado que los 145 sean preexistentes hasta la batería de la tarea 8.1 en contenedor Linux.
- Productores de `source` de `POST /jobs/ingest` revisados (`aws-cur`, `local-smoke`, `cd-smoke`,
  `assistant-corpus`, `test`, `azure-cost` y el caso con relleno ` azure `): ninguno es rechazado
  por la regla. La pantalla de ingesta envía el texto libre del usuario, así que un valor con
  espacios interiores pasa a recibir 422; lo que muestra la pantalla se comprueba en la tarea 6.4.
- Un comentario del coder decía que el processor «descartaría» ese trabajo; hoy lo reencola (es el
  defecto), así que el orquestador reformuló esa frase. Sin cambio de comportamiento.

### Mutación (tarea 2.5), 2026-10-11

Contenedor desechable `python:3.12` sobre una copia del árbol (el repositorio montado en solo
lectura), con `mutmut<3` (no corre en Windows y no se añade a ninguna dependencia del repo) acotado
a `app/schemas/jobs.py`, más 13 mutantes manuales dirigidos aplicados con una sustitución de texto y
la prueba `test_ingest_source_admission.py` como ejecutor. Línea base: 37 pasan.

Mutantes manuales: **12 muertos y 1 superviviente equivalente**.

| Mutante | Resultado |
| --- | --- |
| Sin `strip()`; sin `lower()` | muertos |
| Límite `{0,62}`; límite `{0,64}` | muertos |
| `match`; `search` en vez de `fullmatch` | muertos |
| Devolver el valor normalizado en vez del original | muerto |
| Primer carácter sin restringir; sin guion bajo; sin punto | muertos |
| Validación desactivada (`if False`) | muerto |
| `.casefold()` en vez de `.lower()` | **superviviente real en la primera pasada; muerto tras el caso `eszett-casefold-differs`** |
| El mensaje del `ValueError` incluye el valor | superviviente equivalente (ver abajo) |

Remediación (tester): se añadió a la tabla compartida el caso rechazado `eszett-casefold-differs`
(`straße`): `lower()` conserva la `ß`, que no es ASCII, y el patrón la rechaza; `casefold()` la
convertiría en `ss` y la aceptaría. Verificado por el tester contra el mutante (1 falla con
`assert 202 == 422`, 36 pasan) y contra el código real (37 pasan en backend y en processor), y
repetido por el orquestador en el contenedor (1 falla, 19 pasan por el corte del primer fallo).
Cambios de fichero: solo `docs/api/ingest-source-contract-cases.json`.

`mutmut` sobre el archivo: **6 supervivientes**, ninguno en código que cambia este grupo salvo los
dos equivalentes:

- Mutantes 1 y 2 (`strip_whitespace` y `min_length` de `NonEmptyText`) y 7 y 8 (valores por defecto
  de `artifact_uri` y `metadata`): líneas que este change no toca (`text_content`, `artifact_uri`,
  `metadata`). Fuera del alcance de la tarea; no se añaden pruebas para código ajeno.
- Mutante 11 (quitar `@classmethod` de `validate_source`): equivalente, `field_validator` de
  pydantic envuelve el método como método de clase por su cuenta.
- Mutante 13 y el mutante manual «mensaje con el valor»: equivalentes. `validation_error_handler`
  (`apps/backend/app/core/request_context.py`) descarta el `msg` de cada error y devuelve siempre
  `"Invalid request value"`, de modo que el texto del `ValueError` no es observable por la API. La
  garantía de no filtrar el valor la da ese manejador y la comprueba el test de no-eco ya existente.

Hallazgo de proceso: el fichero de casos, tal como se commiteó en el commit Red, contenía caracteres
no ASCII literales (incluido un espacio de ancho cero invisible) en lugar de escapes. Se convirtieron
a escapes `\uXXXX`; el contenido parseado es idéntico (comprobado por comparación) y no queda ningún
byte no ASCII. El cambio solo toca datos de prueba compartidos.

### Verificación del backend (tarea 2.6)

Suite completa del backend en contenedor `python:3.12` (equivalente a CI): **1169 pasan, 64 se
omiten, 0 fallan**, `compileall` correcto. Los 145 fallos de Windows son, por tanto, del entorno
(`RF-105-004`) y no del cambio: esos cuatro archivos pasan en Linux. Las 64 omitidas son las pruebas
opt-in con servicios reales; no se comparó el recuento con el de la base. `test_ingest_padded_source_is_preserved`
y `test_ingest_blank_source_is_rejected_without_effects` pasan sin cambios.

### DoD y QA del grupo 2

**DoD** (`node .claude/harness/check-dod.mjs`, Windows, 2026-10-11): lint, type-check y escaneo de
secretos **PASS**. La regresión completa queda **FAIL solo por el entorno**: el backend da 145
fallos, 1024 pasan y 64 se omiten, y los 145 están en los cuatro archivos `*_jup047.py` de
`RF-105-004` (72 + 37 + 33 + 3), cuyo recuento exacto ya consta en el backlog; turbo dio 3 de 4
paquetes correctos (azure-cost-api, frontend y processor). La misma suite del backend en contenedor
`python:3.12` pasa entera (1169 pasan, 64 se omiten, 0 fallan), así que el rojo no lo causa este
cambio. No se presenta el DoD como verde en Windows.

**QA (agente independiente): `accept-with-notes`.** Verificó con comandos propios: los tests no
cambian entre el commit Red y HEAD, el producto es solo `apps/backend/app/schemas/jobs.py`, los
cuatro escenarios de la spec tienen prueba (también la ausencia del valor en la respuesta y en los
registros), la tabla compartida coincide con la del commit Red salvo la entrada nueva y no tiene
bytes no ASCII, y los tres supervivientes justificados lo están (comprobó el manejador de
validación y el comportamiento de pydantic sin `@classmethod`). Sin hallazgos para tester o coder.
Limitación declarada por QA: no repitió la ejecución de `mutmut` en contenedor; se apoya en el
informe y en los datos que sí verificó. Notas: (1) cifras históricas de la sección Red, aclaradas
arriba; (2) los cambios sin commitear de la tabla, `review.md` y `tasks.md` entran en el commit de
cierre del grupo, porque las pruebas dependen de la tabla corregida.

## Grupo 3 — Fallo permanente de entrada en el processor

### Red (tarea 3.1), 2026-10-11

Ajuste de tareas: la variante `redelivered=True` de la 3.1 pasa a la 4.2, porque el campo
`QueueMessage.redelivered` no existe hasta la 4.4 y no se puede escribir antes. Mismo alcance, otra
posición.

`apps/processor/tests/test_ingest_permanent_input_failure.py` (nuevo, 32 casos), con `AgentRuntime`,
`PipelineRunner` (LangGraph), `JobRepository` y `ProcessorWorker` reales sobre SQLite y solo el
proveedor y el almacén vectorial doblados:
`cd apps/processor && python -m pytest tests/test_ingest_permanent_input_failure.py -q`.

**Resultado Red: 32 fallan, 0 pasan**, repetido por el orquestador. Motivos:

- **3 por comportamiento del worker**, sin depender de nombres nuevos: la entrega del trabajo con
  `Azure Cost Management` lanza `RuntimeError: ingestion_failed` (hoy `nack(requeue=True)` y relanza;
  2 casos) y el trabajo envenenado deja un `worker_loop_failed` en el bucle antes del válido siguiente
  (1 caso).
- **29 por el contrato aún inexistente**: `ImportError` de `AgentInputError` (20) o de `IngestionFailed`
  (9), importados dentro de cada test para que la colección funcione y cada caso falle por separado.

Cubren: descarte en una entrega (un `nack(requeue=False)`, sin `ack`, sin relanzar, fila `failed`,
proveedor y almacén vectorial sin llamadas, contador +1); diagnóstico con el evento fijo
`job_input_rejected` y el `request_id` y sin el `source`, el contenido ni el texto de la excepción;
trabajo válido de otro tenant procesado detrás; clasificación (`permanent` verdadero solo para
`AgentInputError`; falso para `RuntimeError`, `ValueError`, `AgentGuardrailError` base y
`AgentResponseError`); los fallos de `mark_failed` y `mark_running` se propagan sin convertirse en
`IngestionFailed`; y que las comprobaciones de entrada de los guardrails lanzan `AgentInputError`
mientras `parse_and_validate_response` no.

Contraste (`test_ingest_task.py`, `test_tenant_isolation_jobs.py`, `test_secret_boundaries.py`,
`test_guardrail_validation.py`, `test_ingest_failure_metrics.py`): 152 pasan y 6 se omiten, igual con
y sin el archivo nuevo. Sin cambios en `apps/*/app/**`.

Hallazgos del tester para Green: LangGraph **no** envuelve la excepción del guardrail
(`AgentGuardrailError` llega tal cual a `IngestTask`, sin `__cause__`), así que basta
`isinstance(..., AgentInputError)`; el `request_id` llega al registro en JSON; y el caso del
diagnóstico exige además que el evento sea `warning` y que sus claves estén dentro de
`{event, level, logger, request_id, timestamp, service}`, parte que hoy no se ejercita porque el
test cae antes.

### Green (tarea 3.2), 2026-10-11: producto hecho, una prueba existente pendiente de ajuste

Producto modificado (solo processor): `agents/guardrails.py` (`AgentInputError`, subclase de
`AgentGuardrailError`, que lanzan `normalize_source` y las cuatro comprobaciones de entrada de
`prepare_agent_input`, sin cambiar ningún mensaje), `tasks/ingest.py` (`IngestionFailed`, subclase de
`RuntimeError` con el booleano `permanent`, que se lanza tras `mark_failed` con `from None`) y
`workers/runner.py` (rama `IngestionFailed`: si `permanent`, evento fijo `job_input_rejected`, un
`nack(requeue=False)` y retorno sin relanzar; si no, `nack(requeue=True)` y relanza como hoy).

- `test_ingest_permanent_input_failure.py`: **32 pasan** (antes 32 fallaban).
- Contraste de nueve suites del processor y suite completa (coder): 712 pasan, 65 se omiten y **1
  falla**, que es `test_secret_boundaries.py::test_rf053_003_task_to_worker_preserves_sanitized_root_diagnostics`.
  Las demás aserciones de esa prueba pasan (`nack(42, requeue=True)`, sin secretos, sin el texto del
  proveedor); falla solo la de la línea 439, que exige `"RuntimeError"` en el diagnóstico, y ahora el
  worker registra `IngestionFailed`.
- El coder paró y no tocó la prueba, como debe. Decisión de Victor: cambiar solo esa aserción (ver la
  adenda de `proposal.md`). El hook del harness bloquea editar un test ya commiteado, así que el
  cambio de la línea 439 queda pendiente de hacerse a mano. Hasta entonces el Green está completo en
  producto pero no cerrado: la tarea 3.2 no se marca.

### Mutación (tareas 3.3 y 3.4), 2026-10-11

**3.3.** `tests/test_guardrail_validation.py` y las demás pruebas que esperan `AgentGuardrailError`
pasan sin cambios: `AgentInputError` es subclase y ningún mensaje cambió.

**3.4.** Contenedor desechable `python:3.12` sobre una copia del árbol (repositorio montado en solo
lectura), con 23 mutantes dirigidos sobre las líneas que cambia el grupo, aplicados por sustitución
de texto, y nueve suites del processor como ejecutor. En la copia, y solo en la copia, la línea 439 de
`test_secret_boundaries.py` lleva la aserción pendiente (`IngestionFailed`), para medir el estado
final real sin tocar el repositorio. Línea base de la copia: **240 pasan, 6 se omiten, 0 fallan**, lo
que confirma que ese cambio de una línea basta para dejar la suite en verde.

**22 muertos y 1 superviviente equivalente.**

| Zona | Mutantes muertos |
| --- | --- |
| `IngestionFailed` (`ingest.py`) | `permanent` siempre verdadero, siempre falso, calculado con la base `AgentGuardrailError`; conservar la causa (`from exc`); mensaje distinto; dejar de ser `RuntimeError` |
| Worker (`runner.py`) | condición invertida; `requeue=True` al descartar; descartar sin `nack`; sin `return` tras descartar; `requeue=False` y sin `raise` en la rama no permanente; evento con otro nombre, a nivel `error` o con un campo extra |
| Guardrails (`guardrails.py`) | cada uno de los seis `raise` degradado a `AgentGuardrailError`; `AgentResponseError` pasa a ser de entrada; `AgentInputError` pierde su base |

- **Superviviente equivalente:** importar `AgentGuardrailError` sin usarlo en `ingest.py`. Es un
  control que se añadió a propósito; no cambia ningún comportamiento observable.
- Un mutante («sin `return`») no se aplicó la primera vez por un patrón mal escrito en el guion; se
  repitió con el patrón correcto y murió.
- Sin pruebas nuevas: ningún superviviente real, así que no hace falta remediación del tester.

Límite: son mutantes escritos a mano sobre las líneas del grupo, no una herramienta automática sobre
el archivo entero (`mutmut` genera mucho ruido en `guardrails.py`, que tiene 400 líneas ajenas a este
cambio).

### Green cerrado (tarea 3.2), 2026-10-11

El cambio de la línea 439 de `test_secret_boundaries.py` (de `"RuntimeError"` a `"IngestionFailed"`, con
dos líneas de comentario) lo hizo Victor a mano: el hook del harness bloquea editar tests commiteados
y el clasificador de permisos de Claude Code denegó levantarlo por tratarse de autoconfiguración del
harness, así que no se rodeó. `git diff` del test: solo esa aserción y el comentario.

Resultado, ejecutado por el orquestador con el cambio ya aplicado (entorno virtual local, Windows):

- `test_ingest_permanent_input_failure.py`: **32 pasan** (antes 32 fallaban).
- `test_secret_boundaries.py`: 31 pasan.
- Suite completa del processor: **713 pasan, 65 se omiten, 0 fallan**, igual que el recuento predicho
  y que el de la copia usada para la mutación (240 pasan, 6 se omiten en las nueve suites).
- Las 65 omitidas son pruebas opt-in con servicios reales; no se comparó el recuento con el de la base
  del change (681 pasan y 65 se omiten antes del grupo 3, con los 32 casos fallando).

### Mutantes adicionales contra el repo real y QA del grupo 3

Los 23 mutantes de arriba se midieron sobre una copia con la aserción pendiente aplicada. Ya con la
línea 439 cambiada en el repositorio, se repitieron en contenedor, sin ninguna sustitución, los tres
que la QA razonó pero no había ejecutado más uno equivalente: **4 muertos de 4**. Línea base sobre el
repo real: 240 pasan, 6 se omiten, 0 fallan.

| Mutante | Resultado |
| --- | --- |
| Quitar `mark_failed` del `except Exception` | muerto |
| Envolver `ProviderError` en `IngestionFailed` | muerto |
| Quitar `mark_failed` del `except ProviderError` | muerto |
| `mark_failed` después del `raise` (inalcanzable) | muerto |

**DoD:** no se repitió `check-dod.mjs` completo para este grupo; la regresión completa del backend en
Windows falla por `RF-105-004` (ver el grupo 2) y el processor completo pasa: 713 pasan, 65 se omiten,
0 fallan. Lint y type-check del repositorio se ejecutan en la tarea 8.3.

**QA (agente independiente): `accept-with-notes`, sin hallazgos para tester ni coder.** Comprobó con
comandos propios: el test del tester no cambia desde el commit Red; el único cambio de tests es la
aserción de la línea 439, legítima según la adenda (ninguna otra aserción, panel, alerta ni documento
depende de `RuntimeError` en `exception_type`); el producto es el mínimo y no adelanta nada de los
grupos 4 y 5; los tres escenarios del requisito tienen prueba; y 181 pasan y 6 se omiten en las cinco
suites relacionadas. Notas: (1) producto, línea 439 y documentos entran en un único commit Green;
(2) los mutantes extra, ya ejecutados arriba; (3) `__context__` conserva la causa original (`from None`
solo suprime `__cause__`), preexistente y sin fuga: la rama permanente no relanza ni imprime la
excepción.

Pendiente de este requisito, por pertenecer a otros grupos: la variante con `redelivered=True` (4.2),
el tope de reintentos (grupo 4), el resultado corrupto de un `completed` (grupo 5) y la comprobación
con broker real (grupo 6).

## Grupo 4 — Tope de un reintento

### Red (tareas 4.1, 4.2 y 4.3), 2026-10-11

Dos archivos nuevos, con `IngestTask`, `JobRepository` y `ProcessorWorker` reales sobre SQLite
(`cd apps/processor && python -m pytest tests/test_queue_message_redelivered.py tests/test_ingest_bounded_retry.py -q`):

- `tests/test_queue_message_redelivered.py` (13 casos, tarea 4.1): `blocking_pop` copia `redelivered`
  del frame (verdadero y falso), un frame sin el atributo cuenta como primera entrega, los valores no
  booleanos se convierten con `bool`, `QueueMessage` vale `False` por defecto y admite la palabra clave,
  y un mensaje ilegible se descarta sin afectar a la marca del siguiente.
- `tests/test_ingest_bounded_retry.py` (28 casos, tareas 4.2 y 4.3): primera entrega con fallo no
  clasificado (reencola y relanza); reentrega con el mismo fallo (un `nack(requeue=False)`, no relanza,
  fila `failed`, contador +1, evento `job_retry_exhausted` solo con `request_id`, sin `source`,
  contenido ni texto de la causa); reintento que se completa (`ack`); secuencia completa con el
  pipeline invocado exactamente 2 veces; trabajo válido de otro tenant detrás; permanente de entrada,
  `InvalidJobMessage` y `ProviderError` sin cambios con `redelivered` verdadero; y, para la lectura del
  trabajo, `mark_running` y `mark_failed` que fallan, el reencolado sin tope también en una reentrega.

**Resultado Red, repetido por el orquestador: 19 fallan y 22 pasan** (41 casos).

- **13 fallan por el campo inexistente**: `AttributeError: 'QueueMessage' object has no attribute
  'redelivered'` (11) y `TypeError ... unexpected keyword argument 'redelivered'` (2).
- **6 fallan por comportamiento del worker**: `IngestionFailed` escapa y se hace `nack(requeue=True)` con
  `redelivered` verdadero (reentrega sin descarte: `RuntimeError`, `ValueError` y `KeyError`; evento
  `job_retry_exhausted` ausente; la 2ª entrega de la secuencia relanza), y el bucle deja un
  `worker_loop_failed` antes del trabajo válido siguiente.
- **22 pasan hoy a propósito**: primera entrega, reintento que se completa, permanente de entrada,
  `InvalidJobMessage`, `ProviderError` y los 12 casos de estado no disponible. Son guardas contra una
  implementación que aplique el tope de más; los de estado no disponible con reentrega verdadera son los
  más importantes, porque matan un worker que descarte toda reentrega.

Contraste (`test_ingest_task`, `test_tenant_isolation_jobs`, `test_tenant_isolation_malformed_queue`,
`test_secret_boundaries`, `test_worker_tracing`, `test_ingest_permanent_input_failure`): 91 pasan y 6 se
omiten, igual con y sin los archivos nuevos. Sin cambios en `apps/*/app/**`.

Notas del tester para Green: el helper de `test_ingest_bounded_retry.py` marca la reentrega asignando
`message.redelivered = True` sobre un `QueueMessage(job, tag)`, así que el dataclass **no debe** ser
`frozen` ni usar `__slots__`; y los dobles `SimpleNamespace(delivery_tag=..)` de
`test_tenant_isolation_malformed_queue.py` no tienen `redelivered`, por eso el valor por defecto de un
frame sin el atributo es `False`.

### Green (tareas 4.4 y 4.5), 2026-10-11

Producto modificado (solo processor, dos archivos): `clients/rabbitmq_queue.py` (`QueueMessage.redelivered:
bool = False`, mutable; `blocking_pop` lo rellena con `bool(getattr(method_frame, "redelivered", False))`, con
el valor por defecto a propósito para los dobles `SimpleNamespace` existentes y porque ante la duda se
reencola) y `workers/runner.py` (en la rama `IngestionFailed` no permanente: reentrega → evento fijo
`job_retry_exhausted`, un `nack(requeue=False)` y retorno sin relanzar; primera entrega → `nack(requeue=True)`
y relanza como hoy; el `except Exception` genérico, que cubre el estado no legible o no registrable, no
cambia y reencola sin tope, con un comentario que explica por qué). `ingest.py` y `guardrails.py` no se
tocan. Ningún test cambia desde el commit Red.

Resultado, ejecutado por el orquestador:

- `test_queue_message_redelivered.py` y `test_ingest_bounded_retry.py`: **41 pasan** (antes 19 fallaban).
- **Tarea 4.5**: las cuatro aserciones de `requeue=True` pasan sin editar (`test_ingest_task.py:225`,
  `test_secret_boundaries.py:428` y `test_tenant_isolation_jobs.py:176` y `:293`); con sus suites
  completas, 54 pasan y 6 se omiten (las variantes de CockroachDB sin URL).
- Suite completa del processor: **754 pasan, 65 se omiten, 0 fallan** (713 anteriores más los 41).

### Mutación (tarea 4.6), 2026-10-11

Contenedor desechable `python:3.12` sobre una copia del árbol (repositorio en solo lectura), 22 mutantes
escritos a mano sobre las líneas que cambian y ocho suites del processor como ejecutor (línea base: 132
pasan, 6 se omiten). **22 muertos, 0 supervivientes.**

| Zona | Mutantes muertos |
| --- | --- |
| Lectura de `redelivered` | siempre falso; siempre verdadero; valor por defecto verdadero del frame sin atributo; sin `bool()`; valor invertido; valor por defecto verdadero del dataclass |
| Rama de reentrega | condición invertida; descartar siempre; reencolar siempre; descartar con `requeue=True`; sin `return`; relanzar tras descartar; sin `nack`; evento con otro nombre, a nivel `error` o con un campo extra; permanente tratado como reintento agotado |
| Primera entrega | `requeue=False`; sin `raise` |
| Estado no disponible | `requeue=False`; tope por reentrega (`requeue=not message.redelivered`); sin `raise` |

El mutante «tope por reentrega» en el estado no disponible es el que corresponde a la implementación
ingenua que descartaría toda reentrega aunque el trabajo siga en `queued` o `running`: muere gracias a los
12 casos de estado no disponible con reentrega verdadera.

Límite: mutantes manuales sobre las líneas del grupo, no una herramienta automática sobre el archivo
entero. Las pruebas usan un broker doblado: demuestran lo que el worker hace con la marca, no que la marca
llegue; esa comprobación con RabbitMQ real se hizo en la tarea 1.3 y se repite de extremo a extremo en el
grupo 6.

### QA del grupo 4

**Veredicto del agente QA independiente: `accept-with-notes`**, sin hallazgos que exijan tocar producto ni
tests. Comprobó con comandos propios: los tests no cambian desde el commit Red; el producto es solo
`rabbitmq_queue.py` y `runner.py` y es mínimo; `ingest.py` y `guardrails.py` no cambian respecto del
commit del grupo 3 y no hay nada del grupo 5; el descarte está solo en la rama `IngestionFailed` no
permanente con `redelivered` verdadero, y las ramas `InvalidJobMessage`, `ProviderError`, permanente de
entrada y el `except Exception` genérico quedan intactas, con la permanente evaluada antes que la de
reentrega; 78 pasan en las cinco suites relacionadas; las cuatro aserciones de `requeue=True` siguen sin
editar; y los gates de OpenSpec pasan. Los 22 mutantes le parecen suficientes: `ack` en lugar de `nack`,
el orden de las ramas `except` y quitar la limpieza del contexto los mataría el código actual sin
ejecutarlos.

Notas y cómo se atienden:

1. **Escenario «Reentrega sin fallo anterior registrado»** (primera entrega interrumpida). No tiene una
   prueba que lo nombre. Lo representa `test_redelivered_unclassified_failure_is_discarded_without_reraising`
   (`tests/test_ingest_bounded_retry.py`): siembra el trabajo en `queued` y lo entrega con `redelivered`
   verdadero sin una primera entrega previa, que es lo que ocurre tras una interrupción. Demuestra lo que
   hace el worker ante la marca. Que RabbitMQ marque como reentrega un mensaje interrumpido sin respuesta
   lo demostró la sonda de la tarea 1.3, con el caso «tras cerrar sin ack»
   (`docs/evidence/JUP-113-validation.md`, apartado «Marca de reentrega del broker»), y se repite de
   extremo a extremo en el grupo 6. No se añade código.
2. **«El reintento conserva el sobre original y el identificador de correlación»** solo se ejerce de forma
   débil (se reentrega el mismo diccionario y se comprueba el `request_id` del evento). La conservación
   del cuerpo al reencolar es del broker, que no interviene en estas pruebas; queda para el grupo 6.
3. **Enlace de la evidencia del broker real:** ver la nota 1; la medición con RabbitMQ 3.13.7 y pika 1.4.4
   consta en el apartado citado de la evidencia.

Riesgo de diseño: el coste de que una caída de pgvector o de los embeddings de más de unos 2 s marque
`failed` los trabajos en cola está registrado en la aprobación (`proposal.md`, «Cost accepted»), en
`design.md` (Riesgos) y en el ADR-0019 (Consecuencias), y el ADR coincide con lo implementado: una
reentrega como máximo y reencolado sin tope si no se puede leer o registrar el estado.

**DoD:** no se ejecutó `check-dod.mjs` completo en este grupo; el processor completo pasa (754 pasan, 65
se omiten, 0 fallan) y lint, type-check y la batería final se ejecutan en las tareas 8.1 y 8.3.
