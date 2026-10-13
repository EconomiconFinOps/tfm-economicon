JUP: JUP-113
Trello: https://trello.com/c/JaHmg0fs

## Why

El worker del processor reencola sin límite cualquier excepción que no sea `InvalidJobMessage` o
`ProviderError` (`apps/processor/app/workers/runner.py`, líneas 89 a 91). Dos entradas conocidas
llegan a esa rama con un fallo que nunca se va a resolver, y el mensaje vuelve a la cabeza de una
cola que comparten todos los tenants:

- **`RF-086-004` (High, abierto desde el 2026-09-28).** `POST /jobs/ingest` acepta cualquier `source`
  no vacío, pero el processor exige `^[a-z0-9][a-z0-9._-]{0,63}$` tras quitar espacios y pasar a
  minúsculas. Un valor como `Azure Cost Management`, que se puede escribir en el campo de texto libre
  de la pantalla de ingesta, recibe 202 y después falla siempre en el guardrail de entrada. Cada
  vuelta, unos 2 s, hace dos `UPDATE` en `jobs` y suma un fallo a
  `processor_ingest_jobs_failed_total`, que alimenta la alerta de ingesta de JUP-045.
- **`RF-054-001` (Low, del 2026-10-10).** Al reentregarse un trabajo `completed`, un `result`
  guardado corrupto lanza un `JSONDecodeError` crudo, que entra en el mismo bucle, y un `result` que
  no es un objeto se devuelve tal cual aunque la firma promete `dict`.

Las dos cosas están leídas en el código; ninguna se ha ejecutado todavía contra un broker. La tarjeta
pide cerrarlas antes de la entrega del MVP porque un solo trabajo mal formado deja sin ingesta a
todos los ámbitos.

## What Changes

- **BREAKING** (API): `POST /jobs/ingest` responde 422, con el cuerpo saneado que ya usa la
  validación, a un `source` que el processor no admitiría. Antes respondía 202. No crea trabajo, no
  reserva y no publica. Un `source` admitido se sigue guardando y publicando literal (decisión de
  JUP-086).
- Backend y processor comprueban la misma tabla de casos del `source`, para que la regla no vuelva a
  divergir entre los dos servicios.
- El processor trata el rechazo del guardrail de entrada como fallo permanente: el trabajo queda
  `failed` y el mensaje se descarta sin reencolar en esa misma entrega. Cubre los trabajos ya
  guardados antes de este cambio.
- El processor reintenta un fallo no clasificado como máximo una vez. Usa la marca de reentrega del
  broker: si la entrega ya es una reentrega y vuelve a fallar, el trabajo queda `failed` y el mensaje
  se descarta. Sin DLQ, sin migración, sin cambiar el tipo de cola y sin configuración nueva.
- Un mensaje solo se descarta si el trabajo tiene registrado un estado terminal o si el mensaje es
  inválido. Cuando el worker no puede leer o escribir el estado del trabajo (base caída), sigue
  reencolando sin tope, igual que hoy.
- La reentrega de un trabajo `completed` valida que el resultado guardado es un objeto; si está
  corrupto o tiene otra forma, el mensaje se rechaza como inválido, sin reencolar y sin cambiar la
  fila.
- `InvalidJobMessage` y `ProviderError` conservan su tratamiento actual.
- ADR nuevo con la política de reintentos y su coste, que complementa ADR-0008 (este decía que no se
  definía ningún límite).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `document-ingestion-handoff`: se añaden la regla de admisión del `source`, el fallo permanente de
  entrada, el tope de un reintento para fallos no clasificados, la condición para descartar un
  mensaje y la validación del resultado en la reentrega de un trabajo completado. El requisito
  vigente «Preserve failure handling and request correlation» no se modifica: sigue siendo cierto
  para el reintento que se permite.
- `llm-provider-routing`: el requisito «Fallos reales terminales sin alterar otros errores» deja de
  decir que los demás errores conservan su comportamiento y remite a la política nueva.

## Impact

- **Producto, backend:** `apps/backend/app/schemas/jobs.py` (validación del `source`).
- **Producto, processor:** `apps/processor/app/agents/guardrails.py` (error de entrada tipado),
  `apps/processor/app/tasks/ingest.py` (clasificación del fallo y resultado de un trabajo
  completado), `apps/processor/app/clients/rabbitmq_queue.py` (marca de reentrega en el mensaje) y
  `apps/processor/app/workers/runner.py` (política de descarte y reintento).
- **Nuevo:** `docs/api/ingest-source-contract-cases.json` (tabla de casos compartida),
  `docs/adr/ADR-0019-ingestion-retry-policy.md`, `docs/evidence/JUP-113-validation.md`,
  `docs/continuidad/reintentos-ingesta.md` y pruebas nuevas en `apps/backend/tests` y
  `apps/processor/tests`.
- **Modificado, documentación:** `docs/adr/README.md`, `docs/architecture.md`,
  `apps/backend/README.md`, `apps/processor/README.md`, `docs/testing/critical-flows.md`,
  `docs/continuidad/README.md` y `openspec/findings/backlog.md` (`RF-086-004` y `RF-054-001`); al
  archivar, `openspec/specs/document-ingestion-handoff/spec.md` y
  `openspec/specs/llm-provider-routing/spec.md`.
- **Pruebas existentes:** cuatro aserciones fijan hoy `requeue=True` (`test_ingest_task.py:225`,
  `test_secret_boundaries.py:428` y `test_tenant_isolation_jobs.py:176` y `:293`). Las cuatro son
  primeras entregas con un error no clasificado, que con este diseño se sigue reencolando, así que
  se espera que pasen sin tocarlas; si alguna falla, se para y se revisa (ver `design.md`,
  decisión 9).
- **API:** los productores conocidos envían valores que la regla admite (`aws-cur` por defecto en la
  pantalla, `local-smoke`, `cd-smoke`, `assistant-corpus` y `test` en las pruebas). Un cliente que
  enviara otro formato pasa de 202 a 422.
- **Sin cambios:** esquema de la base, tipo y argumentos de la cola, dependencias, CI, frontend y
  variables de entorno.
- **Fuera de alcance:** `RF-086-005` (NaN y surrogates en `metadata` dan 500), `RF-104-003` (lectura
  del estado de un trabajo), DLQ, backoff, tope configurable, mensajes que matan el proceso antes de
  que el worker pueda tratarlos y cambios en la pantalla de ingesta.
- **Coordinación:** la capacidad `tenant-isolation` vive en el change `jup-086-tenant-isolation-contract`,
  que sigue sin archivar, y su escenario «Transient failure remains retryable» dice que ese contrato
  no introduce límite de reintentos. No se edita ese change; la discrepancia se anota en la
  evidencia para quien lo archive.
- **ADR:** aplica. `ADR-0019` era el siguiente número libre en `develop` y en todas las ramas de
  `origin` el 2026-10-11; se vuelve a comprobar antes de abrir la PR.

## Human Approval

- Change: jup-113-bounded-ingestion-retries
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-10-11
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Pairing: Victor indica que Lucia (pairing) ha visto el diseño y está de acuerdo con la política de
  reintentos. Consta por lo que dice Victor; no es una revisión de GitHub ni sustituye a
  `Revision JUP-113` y `Validacion JUP-113`, que siguen pendientes.
- Scope adjustment approved: el criterio 5 de la tarjeta («un error no clasificado se reintenta
  como máximo las veces fijadas y después el trabajo queda `failed`») se cumple siempre que el
  estado del trabajo se pueda registrar. Si el worker no puede leerlo o escribirlo, el mensaje se
  reencola sin tope, como hoy. Victor lo aprueba y matiza el criterio en Trello.
- Decisions approved: se aprueban las once decisiones del `design.md`. (1) **La admisión aplica la
  misma regla que el processor y no normaliza**: 422 saneado sin efectos; el valor admitido se guarda
  literal. (2) **Una tabla de casos compartida** en `docs/api/` vigila la deriva entre los dos
  servicios. (3) **`IngestTask` dice si registró el fallo y si es permanente**, sin exponer la causa.
  (4) **El tope es la marca de reentrega del broker**: una reentrega como máximo, que puede ser
  ninguna si la entrega anterior se interrumpió. (5) **Solo se descarta con estado terminal
  registrado o por mensaje inválido**; sin estado legible o registrable se reencola sin tope. (6) **El
  resultado de un trabajo completado se valida al decodificar**; nulo o ausente devuelve `{}`.
  (7) **Eventos con nombre fijo y sin métricas nuevas.** (8) **Sin configuración nueva.**
  (9) **Reproducir antes de implementar**; las cuatro aserciones existentes de `requeue=True` no se
  editan. (10) **Requisitos nuevos en `document-ingestion-handoff`** y una frase modificada en
  `llm-provider-routing`. (11) **ADR-0019**, que complementa ADR-0008.
- Cost accepted: una caída de pgvector o de los embeddings de más de unos 2 s marca `failed` los
  trabajos en cola, que hoy esperarían, y hay que volver a enviarlos. Queda registrado en la base,
  en los registros y en la alerta de JUP-045; la interfaz no lo muestra (`RF-104-003`).
- Constraints: el producto cambiado se limita a los cinco archivos del apartado Impact. Sin cambios
  en el esquema de la base, el tipo o los argumentos de la cola, dependencias, CI, frontend ni
  variables de entorno. `InvalidJobMessage` y `ProviderError` conservan su tratamiento. No se
  registra el `source`, el contenido ni la causa en eventos o excepciones. No se edita el change
  `jup-086-tenant-isolation-contract`. No se adapta ninguna prueba existente para que pase. No se
  da por validado nada que no se haya ejecutado, y las pruebas opt-in no se presentan como
  cubiertas por CI.
- Main risks: (a) el diseño depende de que RabbitMQ marque la reentrega con `basic_get`; se
  comprueba en la tarea 1.3 y, si no se cumple, se para. (b) El análisis de `RF-086-004` es
  estático; la tarea 1.2 lo reproduce y, si no se reproduce, se para. (c) Un mensaje que mata el
  proceso se seguiría reentregando; fuera de alcance. (d) Las pruebas con broker real no corren en
  CI (`RF-096-004`). (e) El 422 nuevo afecta a un cliente que enviara otro formato de `source`.
- Required changes before execution: ninguno en los artefactos. En Trello, matizar el criterio 5
  como indica «Scope adjustment approved».
- Notes: nada de lo descrito en `design.md` se ha ejecutado todavía; se leyó en el repositorio
  sobre `develop` en `8511fb1f`, que no ha cambiado al registrar esta aprobación. Son 41 tareas en
  8 grupos. Comprobaciones del gate el 2026-10-11: `corepack pnpm openspec:validate` (64 de 64),
  `corepack pnpm jup:check -- --change jup-113-bounded-ingestion-retries` y
  `corepack pnpm jup:cleanup:check`, las tres correctas.

### Adenda a la aprobación pre-código: excepción a «no se adapta ninguna prueba existente»

- Fecha: 2026-10-11. Decide: Victor, a pregunta expresa del orquestador durante la tarea 3.2.
- Motivo: `IngestionFailed` (subclase de `RuntimeError`, necesaria para llevar el indicador
  `permanent` al worker) hace que el registro `worker_loop_failed` anote `exception_type` con el
  valor `IngestionFailed` en lugar de `RuntimeError`. La prueba existente
  `apps/processor/tests/test_secret_boundaries.py::test_rf053_003_task_to_worker_preserves_sanitized_root_diagnostics`
  exigía el nombre antiguo (línea 439).
- Decisión: cambiar solo esa aserción a `IngestionFailed`. Lo que la prueba protege (tipo de la
  excepción visible, sin el texto del proveedor ni secretos en el diagnóstico) se mantiene y las
  demás aserciones no cambian. No se encontró ningún panel, alerta ni documento que dependa del
  nombre antiguo.
- Alcance: solo esa línea. Las cuatro aserciones de `requeue=True` siguen sin tocarse.
- Alternativas descartadas: registrar un nombre de tipo distinto del real solo para contentar a la
  prueba, y rediseñar sin subclase (obligaba a rehacer los 32 casos del Red ya commiteado).

### Adenda: corrección de la cifra del coste aceptado

- Fecha: 2026-10-11 (hora local; 00:19 UTC del día siguiente en los registros de Docker). Origen: medición con pgvector parado en el stack real (tarea 6.4).
- El texto aprobado decía «una caída de pgvector o de los embeddings de más de unos 2 s». Es inexacto: el
  trabajo se descarta tras dos intentos, y con pgvector parado cada intento tarda unos 4 s en fallar y el
  worker espera 2 s entre ambos, es decir, unos 10 s hasta el descarte. La caída que provoca el coste es la
  que cubre los dos intentos, y su duración depende de cómo falle la dependencia.
- La decisión no cambia: el coste aceptado es el mismo (trabajos en cola descartados como `failed` que hay
  que reenviar). Se corrigen la cifra en `design.md` y en `ADR-0019`, y el texto anterior de esta aprobación
  se conserva como registro histórico.
