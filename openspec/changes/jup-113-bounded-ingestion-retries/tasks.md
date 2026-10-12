Cada grupo con código sigue el ciclo Red (prueba que falla por el motivo esperado), Green (mínimo de
producto) y mutación, y termina con un punto de parada para el commit. Las pruebas de Python se
ejecutan en un contenedor equivalente a CI (`python:3.12`), porque en Windows fallan pruebas ajenas
del backend (`RF-105-004`).

## 1. Reproducción y decisión (antes de tocar producto)

- [x] 1.1 Comprobar `origin/develop`, fijar el SHA base y abrir `docs/evidence/JUP-113-validation.md`
  con fecha, rama, SHA base y enlace a Trello.
- [x] 1.2 Reproducir `RF-086-004` con Compose en un proyecto aislado: enviar `POST /jobs/ingest` con
  `source` igual a `Azure Cost Management`, comprobar el 202 y anotar las reentregas (eventos
  `worker_loop_failed`, cambios de la fila en `jobs` y valor de
  `processor_ingest_jobs_failed_total`). Publicar después un trabajo válido de otro tenant y anotar
  si se completa. Guardar comandos y salida en la evidencia. Si no se reproduce, parar y revisar el
  `design.md`.
- [x] 1.3 Comprobar con RabbitMQ real que `basic_get` devuelve `redelivered=False` en la primera
  entrega y `True` tras `nack(requeue=True)` y tras cerrar la conexión sin responder. Es la hipótesis
  de la decisión 4; si no se cumple, parar y revisar el `design.md`.
- [x] 1.4 Redactar `docs/adr/ADR-0019-ingestion-retry-policy.md` desde `docs/templates/adr.md`, en
  estado `Proposed`, con las decisiones 4 y 5 del `design.md`, su coste y las alternativas, enlazado
  a JUP-113 y a este change. Añadir su fila en `docs/adr/README.md`. Comprobar antes que el número
  0019 sigue libre en `develop` y en las ramas de `origin`.

## 2. Regla de admisión del origen en el backend

- [x] 2.1 Crear `docs/api/ingest-source-contract-cases.json` con los casos aceptados y rechazados de
  la decisión 2 del `design.md`.
- [x] 2.2 Red, backend: para cada caso rechazado de la tabla, `POST /jobs/ingest` responde 422 con el
  cuerpo saneado, no crea trabajo, no reserva y no publica, y ni la respuesta ni los registros
  contienen el valor; para cada caso aceptado responde 202 y guarda y publica el valor literal.
- [x] 2.3 Green, backend: validar el `source` en `IngestJobRequest` con la regla de la decisión 1.
- [x] 2.4 Processor: prueba que recorre la misma tabla con `normalize_source`. Describe el
  comportamiento actual, así que se espera en verde desde el principio; se anota como prueba de
  contrato y no como Red.
- [x] 2.5 Mutación sobre la validación del backend (quitar `strip`, quitar `lower`, coincidencia
  parcial en vez de completa, límite de 63 o 65) y cubrir los mutantes que sobrevivan.
- [x] 2.6 Ejecutar la suite completa del backend y comprobar que
  `test_ingest_padded_source_is_preserved` y `test_ingest_blank_source_is_rejected_without_effects`
  pasan sin cambios.

## 3. Fallo permanente de entrada en el processor

- [x] 3.1 Red, processor: con repositorio SQLite y cola doblada, la entrega de un trabajo guardado
  con `source` no admitido deja el trabajo `failed` con `ingestion_failed`, llama a
  `nack(requeue=False)` una vez, no relanza, no invoca al proveedor ni al almacén vectorial, suma
  uno al contador de fallos y registra el evento fijo sin el `source` ni la causa. Un trabajo válido
  de otro tenant publicado detrás se procesa. (La variante con `redelivered=True` pasa a la 4.2,
  porque el campo no existe hasta la 4.4.)
- [x] 3.2 Green, processor: error de entrada tipado en `guardrails.py`, error de fallo registrado con
  indicador de permanente en `ingest.py` y rama nueva en `runner.py` (decisiones 3 y 5).
- [x] 3.3 Comprobar que las pruebas de `test_guardrail_validation.py` que esperan
  `AgentGuardrailError` pasan sin cambios.
- [x] 3.4 Mutación sobre la clasificación en `IngestTask` y la rama del worker; cubrir los mutantes
  que sobrevivan.

## 4. Tope de un reintento

- [x] 4.1 Red, processor: `blocking_pop` entrega `QueueMessage.redelivered` con el valor de la
  respuesta de `basic_get`, verdadero y falso, con un canal doblado; un `QueueMessage` creado sin ese
  campo vale `False`.
- [x] 4.2 Red, processor: un fallo no clasificado con `redelivered=True` deja el trabajo `failed`,
  llama a `nack(requeue=False)`, no relanza y registra el evento fijo de reintento agotado sin datos
  del trabajo; con `redelivered=False` reencola y relanza como hoy; una reentrega que termina bien
  queda `completed` con `ack`. Un fallo permanente de entrada con `redelivered=True` se descarta
  igual que con `False` (variante diferida de la 3.1).
- [x] 4.3 Red, processor: si falla la lectura del trabajo, `mark_running` o `mark_failed`, el worker
  llama a `nack(requeue=True)` también con `redelivered=True`.
- [x] 4.4 Green, processor: campo `redelivered` en `QueueMessage` y `blocking_pop`, y política de la
  tabla de la decisión 5 en `runner.py`.
- [x] 4.5 Comprobar que `test_ingest_task.py:225`, `test_secret_boundaries.py:428` y
  `test_tenant_isolation_jobs.py:176` y `:293` pasan sin editarlas. Si alguna falla, parar: no se
  adapta la prueba.
- [x] 4.6 Mutación sobre la lectura de `redelivered` y las ramas del worker (invertir la condición,
  reencolar siempre, descartar siempre, relanzar tras el descarte); cubrir los mutantes que
  sobrevivan.

## 5. Resultado de un trabajo completado (`RF-054-001`)

- [x] 5.1 Red, processor, en un archivo nuevo `tests/test_completed_result_shape.py` (el
  `test_ingest_redelivery.py` existente está commiteado y bloqueado, y se reutilizan sus ayudantes):
  un trabajo `completed` con resultado `''` o `not json` lanza `InvalidJobMessage`, no cambia la
  fila, no ejecuta el pipeline y la excepción no contiene el resultado; lo mismo con `[1]`, `"x"`,
  `123` y `true`, como texto y ya decodificados, y con los falsy ya decodificados `[]`, `0`, `False`
  y `""`, que hoy se convierten en `{}` por la precedencia de `... if ... else result or {}`;
  `null` como texto o ausente devuelve `{}`.
- [x] 5.2 Red, processor: a través del worker, esos casos terminan en `nack(requeue=False)`.
- [x] 5.3 Green, processor: validación del resultado en `IngestTask` (decisión 6).
- [x] 5.4 Comprobar que `test_completed_redelivery_returns_stored_result_in_any_representation` pasa
  sin cambios.
- [x] 5.5 Mutación sobre la validación del resultado; cubrir los mutantes que sobrevivan.

## 6. Comprobación con servicios reales (opt-in, fuera de CI)

- [x] 6.1 Prueba opt-in en un archivo nuevo, `apps/processor/tests/test_ingestion_retry_integration.py`
  (`test_tenant_isolation_integration.py` está commiteado y bloqueado, y se reutilizan sus fixtures),
  con el broker y las bases reales de sus fixtures: un trabajo guardado con `source` no admitido seguido de uno
  válido de otro tenant; el primero queda `failed`, el segundo `completed` y la cola vacía.
- [x] 6.2 Prueba opt-in: un fallo no clasificado se reencola una vez, la reentrega llega con
  `redelivered=True`, vuelve a fallar y la cola queda vacía con el trabajo en `failed`.
- [x] 6.3 Ejecutar las dos con servicios aislados y anotar en la evidencia los comandos, los resultados y
  que CI las omite (`RF-096-004`). Se ejecutaron con el entorno virtual local (Windows) contra contenedores
  desechables, no dentro de un contenedor Linux.
- [x] 6.4 Repetir la reproducción de 1.2 con Compose sobre la rama: la API responde 422; un trabajo
  envenenado insertado como preexistente se descarta en una entrega; un trabajo válido de otro tenant
  publicado después se completa. Anotar qué muestra la pantalla de ingesta ante el 422, sin cambiar
  su código; si no es comprensible, registrar un finding.

## 7. Documentación

- [x] 7.1 `apps/processor/README.md` y `docs/architecture.md`: tabla de tratamiento de fallos, tope de
  un reintento, caso sin tope y coste ante una caída de pgvector o de los embeddings.
- [x] 7.2 `apps/backend/README.md`: regla del `source` en `POST /jobs/ingest` y su 422.
- [x] 7.3 `docs/testing/critical-flows.md`: suites nuevas en las filas de tenant y de agente, con lo
  que queda opt-in.
- [x] 7.4 Completar ADR-0019 con la evidencia de 1.2, 1.3 y 6.
- [x] 7.5 `openspec/findings/backlog.md`: `RF-086-004` y `RF-054-001` a `Fixed` con enlace a la
  evidencia; registrar como `RF-113-NNN` lo que quede fuera (al menos la frase desactualizada del
  change `jup-086` y, si se observan, el mensaje que mata el proceso y el aviso de la pantalla).
- [x] 7.6 Crear `docs/continuidad/reintentos-ingesta.md` y añadir su fila en
  `docs/continuidad/README.md`.

## 8. Verificación y cierre

- [x] 8.1 Ejecutar las suites completas de backend y processor en el contenedor equivalente a CI y
  anotar aprobadas, fallidas y omitidas frente a la base de 1.1.
- [x] 8.2 Comprobar con `git diff --stat` contra la base que el producto cambiado se limita a los
  cinco archivos del `proposal.md` y que no cambian dependencias, CI, frontend ni migraciones.
- [x] 8.3 Ejecutar `corepack pnpm lint`, `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-113-bounded-ingestion-retries` y
  `corepack pnpm jup:cleanup:check`.
- [x] 8.4 Escribir `review.md` con la evidencia Red, Green y de mutación de cada grupo, y cerrar
  `docs/evidence/JUP-113-validation.md` con un apartado por criterio de la tarjeta y lo no validado.
- [x] 8.5 Comprobar `origin/develop` otra vez; si hay commits que tocan los archivos de producto de
  este cambio, integrarlos y repetir 8.1.
- [ ] 8.6 Registrar la aprobación posterior a la revisión, archivar el change en la rama y abrir la
  PR contra `develop` desde `fix/JUP-113-bounded-ingestion-retries`.
