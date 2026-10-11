# Review — jup-054-final-candidate-coverage

JUP: JUP-054. Registro de evidencia por tarea durante el apply. El resultado global, la
checklist y el cierre se completan en la tarea 7.5.

## Excepción del ciclo Red/Green/mutación (grupos 1 a 4 y 5)

- **Grupos 1 a 4:** sin código de producto ni de pruebas (medición, auditoría y decisiones). Se
  omiten tester, coder y mutación, como en las tareas doc-only.
- **Grupo 5:** las pruebas se escriben sobre código de producto que ya existe, por lo que pasan a
  la primera y no hay Red en sentido estricto. El Red se sustituye por la rotura manual del
  comportamiento cubierto (decisión 7 del `design.md`), hecha **sólo en una copia desechable dentro
  de un contenedor**, nunca en el árbol de trabajo. El `coder` no interviene: no hay cambio de
  producto. Si una prueba fallara contra el candidato sin modificar, se registra un hallazgo (5.10).
- **Mutación automática (Stryker/mutmut):** no se ejecuta; la sustituyen las roturas manuales
  (decisión 7). Los mutantes supervivientes de cada tarea se listan con su justificación.
- **Entorno de ejecución:** contenedores Linux con Python 3.12 y las dependencias de
  `requirements-dev.txt`, equivalentes a CI. El backend en Windows tiene fallos conocidos de
  `socketpair` (evidencia de la primera pasada), así que no se usa para esta verificación.

## Tarea 5.1 — H-02, `GET /tenants` (backend)

- **Archivo nuevo:** `apps/backend/tests/test_tenants_route.py`, 10 pruebas, SQLite real y
  autenticación real; sin skips ni xfail.
- **Comando:** `python -m pytest tests/test_tenants_route.py -q -p no:cacheprovider` desde
  `apps/backend` (Python 3.12).
- **Resultado limpio:** 10 passed. Junto a `test_tenant_isolation_api.py`, `test_cors.py` y
  `test_auth_api.py`: 162 passed y 2 omitidas (opt-in CockroachDB preexistentes), sin interferencias.
- **Roturas del tester** (en copia desechable): `fetch_tenants` sin filtro por usuario (4 fallan),
  ruta sin `get_current_user` (9 fallan), rol admin recibe todos los tenants (1 falla) y usuario
  inexistente aceptado (1 falla). Cada una falla por el motivo esperado.
- **Roturas independientes de QA:** orden invertido, filas duplicadas, JOIN que multiplica filas,
  filtro de usuario debilitado con `OR ut.role='member'`, resultado truncado, `plan` nulo, tenant
  leído de `X-Tenant-Id` y usuario inexistente aceptado. Las ocho se detectan.
- **Mutante superviviente (justificado):** eliminar por completo la cláusula `ORDER BY t.name` de
  `fetch_tenants` no hace fallar ninguna prueba. SQLite devuelve las filas en su orden natural, que
  coincide con el alfabético, y el fixture compartido tiene `id == name`, de modo que el orden por
  `id` o por `name` es indistinguible. La prueba detecta un orden alterado o invertido, no la
  ausencia de orden. Distinguirlo exige datos distintos en un fixture compartido, fuera del alcance
  de este hueco; el orden no está garantizado por el contrato fuera de SQLite.
- **Veredicto QA:** accept. Sin hallazgos bloqueantes. No hay caso de membresía revocada porque
  con el esquema actual equivale a no tener fila en `user_tenants`, ya cubierto por `admin-alone` y
  por la ausencia de tenants ajenos.
- **Producto:** sin cambios (`git diff --stat -- apps` vacío; sólo el archivo nuevo).

## Tarea 5.2 — H-03, `POST /assistant/conversations` con éxito (backend)

- **Archivo nuevo:** `apps/backend/tests/test_conversation_creation.py`, 26 casos con SQLite real,
  autenticación real y validación de pertenencia real; sin skips ni xfail. No repite los casos de
  `test_tenant_isolation_api.py` (422 por `user_id` en el cuerpo y 404 indistinguible de ids ajenos).
- **Comando:** `python -m pytest tests/test_conversation_creation.py -q -p no:cacheprovider -W ignore`
  desde `apps/backend` (Python 3.12).
- **Resultado limpio:** 26 passed. Con `test_tenants_route.py`, `test_tenant_isolation_api.py` y
  `test_assistant_service.py`: 54 passed y 2 omitidas (opt-in CockroachDB preexistentes). QA repitió el
  archivo tres veces seguidas, en orden inverso y duplicado en la misma invocación: 26 passed siempre.
- **Qué cubre:** respuesta 201 con la forma exacta del registro, id uuid4 por patrón, tenant y usuario
  tomados del contexto autenticado (cuatro identidades y un usuario multi-tenant en ambos tenants),
  título recortado, `created_at == updated_at`, fila persistida idéntica a lo devuelto, una sola fila
  nueva sin tocar las existentes ni `messages`, ids distintos en creaciones consecutivas, lectura por su
  dueño, invisibilidad para otro tenant, otro usuario y el mismo usuario en otro tenant, presencia sólo
  en el listado de su dueño y tenant, y rechazos sin escritura (401 sin token y con token inválido, 400
  sin `X-Tenant-Id`, 403 sin pertenencia incluido un admin sin membresías, 422 con título vacío o ausente).
- **Roturas del tester** (copia desechable): título fijo o sin recortar (también vía esquema), `user_id` y
  `tenant_id` fijos en la inserción, ruta sin autenticación, `get_active_tenant` sin pertenencia,
  `fetch_conversation(es)` sin filtro de usuario o de tenant, `updated_at` distinto, INSERT omitido con
  registro devuelto e `id` fijo. Todas detectadas. Una (listado sin filtro de tenant) sobrevivió a la primera
  versión del archivo y se mató añadiendo el caso del usuario multi-tenant.
- **Roturas independientes de QA** (siete): fechas fijas en el año 2000, 200 en lugar de 201, una fila extra
  en `messages`, título persistido distinto del devuelto, campo extra en el registro, detalle sin filtro de
  usuario con 404 de cuerpo distinto, y `uuid1` en lugar de `uuid4`. Las siete se detectan.
- **Matiz de la rotura «ruta sin autenticación»:** quitar `get_current_user` sólo de la ruta no se observa
  como 401 porque `get_active_tenant` depende de él; por eso se rompió también `get_current_user`, y eso sí
  se detecta.
- **Riesgo de reloj, valorado por QA:** la ventana `antes <= created_at <= despues` usa el mismo reloj, en el
  mismo proceso, que el producto, sin red de por medio, así que la deriva entre host y contenedor de
  `RF-085-002` no le afecta. Sólo fallaría con un retroceso del reloj durante los milisegundos de la
  llamada. Se acepta sin tolerancia añadida.
- **Límite conocido:** `get_active_tenant` también responde 400 con cabecera `X-Tenant-Id` duplicada, con
  espacios o con comas; aquí sólo se prueba la cabecera ausente. Es una dependencia compartida por todas
  las rutas y queda fuera de este hueco.
- **Sin supervivientes.** Veredicto QA: accept. Producto sin cambios (`git diff --stat -- apps` vacío).

## Tarea 5.3 — H-07, reentrega idempotente y payload persistido corrupto (processor)

- **Archivo nuevo:** `apps/processor/tests/test_ingest_redelivery.py`, 50 casos que salen de siete
  funciones parametrizadas, con SQLite real, el `JobRepository` real y el `IngestTask` real. Sólo son
  dobles el proveedor del agente y el sumidero vectorial (como en la primera pasada). Sin skips ni xfail.
- **Comando:** `python -m pytest tests/test_ingest_redelivery.py -q -p no:cacheprovider -W ignore` desde
  `apps/processor` (Python 3.12).
- **Resultado limpio:** 50 passed, tres veces seguidas. Con `test_ingest_task.py`,
  `test_tenant_isolation_jobs.py` y `test_agent_ingestion_integration.py`: 76 passed y 6 omitidas
  (opt-in CockroachDB preexistentes).
- **Qué cubre:** la reentrega de un trabajo completado tras un primer procesamiento real devuelve el mismo
  resultado sin repetir efectos (mismas llamadas al proveedor, a los embeddings y al sumidero vectorial,
  sólo se consulta el repositorio y la fila no cambia, ni siquiera `updated_at`); las variantes del
  resultado almacenado (texto JSON, dict, vacío y `NULL`); doce intentos de usar un trabajo completado
  como atajo (contenido, metadatos, origen, `artifact_uri`, tenant o creador distintos) que dan
  `InvalidJobMessage` sin filtrar el resultado guardado; y el payload persistido corrupto o que no es un
  objeto, con trabajos en cola, completados y fallidos, que da `InvalidJobMessage` exacto (sin
  `JSONDecodeError`, sin causa encadenada), sin pipeline, sin cambios de estado y sin tocar la fila.
- **`RecordingRepository`:** subclase real de `JobRepository` que delega siempre con `super()` y sólo
  anota llamadas. Su única alteración (`decode_result`) emula que CockroachDB entrega JSONB ya como dict,
  que SQLite no puede ejercitar; está acotada y documentada, y el primer caso usa el flujo real sin ella.
- **Roturas del tester** (copia desechable, 15): eliminar la rama completada, devolver `{}`, validar
  después de devolver, quitar el `try/except` del `json.loads`, que el corrupto marque fallido o
  `running`, no deserializar el texto, `mark_running` en completados (con y sin guarda de la base),
  quitar la comprobación de objeto, `None` en lugar de `{}`, quitar `from None`, quitar
  `incoming != payload`, tratar igual en cola y completado y lanzar un `ValueError` genérico. Detectadas.
- **Roturas independientes de QA** (diez): `mark_completed` en la reentrega, devolver el resultado de otro
  trabajo, comparar contra `running`, ejecutar el pipeline y descartar su resultado, `mark_running` en la
  reentrega, añadir una clave al resultado, sustituir el payload corrupto por `{}`, filtrar el payload en
  el mensaje de error y devolver el resultado de un completado con payload corrupto. Nueve detectadas.
- **Superviviente de QA, cubierto por vecinos:** bloquear también los trabajos `failed` en la rama de
  completados no se detecta en este archivo, pero sí lo detectan `test_ingest_task.py` (dos fallos). La
  reentrega de `failed` o `running` con payload válido queda a cargo de esos suites.
- **Supervivientes equivalentes (2):** quitar `job.get("artifact_uri") != stored.get("artifact_uri")` o
  `"source"` del bucle de comparación no cambia ningún comportamiento observable: `_payload` obliga a que
  ambos coincidan con su propio payload e `incoming != payload` iguala los dos payloads, de modo que la
  igualdad ya está garantizada por transitividad (defensa en profundidad). QA lo comprobó con pruebas
  desechables.
- **Hallazgo de producto (no fijado con una prueba):** con un trabajo `completed` cuyo `result` almacenado es
  corrupto, `IngestTask.execute` lanza un `json.JSONDecodeError` crudo en `ingest.py:74` (`''` y
  `'not json'`), y si el resultado no es un objeto (`'[1]'`, `'"x"'`, `'123'`, `'true'`, `'null'`) lo
  devuelve tal cual aunque la firma promete `dict`. Reproducido por separado por el tester y por QA con
  pruebas desechables en el contenedor. En `workers/runner.py:83-91` sólo `InvalidJobMessage` y
  `ProviderError` van a `nack(requeue=False)`; cualquier otra excepción hace `nack(requeue=True)` y se
  relanza, así que un `result` corrupto dejaría el mensaje reentregándose sin salida automática (leído en
  el código, no ejecutado contra un broker). Atenuante según QA: `result` sólo lo escribe el propio
  repositorio con `json.dumps`, por lo que el estado exige corrupción externa o manual. Gravedad propuesta:
  baja-media. No se fija con una prueba porque afirmaría un defecto como comportamiento esperado. **Se
  registrará como `RF-054-001` en la tarea 7.1**, con la corrección sugerida (validar que el resultado
  decodificado es un objeto y, si no, lanzar `InvalidJobMessage`).
- **Veredicto QA:** accept. Producto sin cambios (`git diff --stat -- apps` vacío).


## Tarea 5.4 — H-08, alcance de `start_run` y atomicidad del repositorio de costes (processor)

- **Corrección de alcance:** la auditoría describía H-08 como «rechazo de run ajeno sólo con CockroachDB».
  Al leer los tests, `complete_run` y `fail_run` con un run ajeno ya estaban cubiertos en SQLite por
  `test_tenant_isolation_costs.py`. Lo que faltaba de verdad: `start_run` con un run ajeno (sólo existía la
  variante CockroachDB, omitida en CI) y las guardas de integridad por `rowcount` (líneas 74, 194, 221 y 248),
  que ninguna prueba ejercita: el helper `ReportZeroUpdatedRows` está definido y ningún test lo usa. La fila
  H-08 de la evidencia se corrigió en ese sentido.
- **Archivo nuevo:** `apps/processor/tests/test_azure_cost_scope_rejection.py`, 21 casos con SQLite real y el
  `SqlAzureCostRepository` real; sin skips ni xfail.
- **Comando:** `python -m pytest tests/test_azure_cost_scope_rejection.py -q -p no:cacheprovider -W ignore`
  desde `apps/processor` (Python 3.12).
- **Resultado limpio:** 21 passed. Con `test_tenant_isolation_costs.py` y `test_azure_cost_ingestion.py`: 85
  passed y 3 omitidas (variantes CockroachDB preexistentes), en ambos órdenes y en dos ejecuciones.
- **Qué cubre:** `start_run` con un run ajeno (otro tenant, otra suscripción, tenant o suscripción erróneos
  y ambos), con el run ajeno también en estado `failed`, que da `PermissionError` con el mensaje exacto y deja
  runs y registros idénticos; el reinicio del run propio, incluido el reintento tras un fallo (limpia
  `error_code` y `completed_at`, contadores a 0, sin borrar hijos); `complete_run` sobre un run ajeno con un
  registro colisionante y con uno inválido, que debe dar `PermissionError` y no un error de integridad que
  revelaría la existencia de registros ajenos; y, con triggers de SQLite, las guardas de `_delete_records`, del
  INSERT por registro y de los UPDATE finales de `complete_run` y `fail_run`, con rollback total y control
  positivo tras quitar el trigger.
- **Primera pasada de QA: `changes-requested`.** Cuatro roturas sobrevivían: el reinicio no limpiaba
  `error_code` (la aserción era vacua porque el run de partida ya tenía `error_code` nulo), un run ajeno
  `failed` era reiniciable, `fail_run` dejaba `row_count = 1` sin que nada lo notara y `_lock_run` sin guarda
  no se detectaba. Esta última contradecía la afirmación del tester de que era equivalente en SQLite: sin la
  guarda `complete_run` sobre un run ajeno lanza `IntegrityError` en lugar de `PermissionError`, y el `UNIQUE`
  haría de oráculo de existencia de registros de otro tenant. Reproducido de forma independiente por el
  orquestador con una prueba desechable. El tester añadió siete casos (de 14 a 21) y las cuatro roturas se
  detectan; la segunda pasada de QA lo confirma.
- **Roturas del tester** (copia desechable, ~30): condiciones del `WHERE` de `start_run` (tenant, suscripción,
  todo y `OR status = 'failed'`), cada guarda de `rowcount`, cambios de tipo y mensaje de excepción, `commit`
  parcial en cuatro puntos, `start_run` que rechaza el run propio o borra sus hijos, `row_count`, `page_count`
  y `retry_count` de `fail_run`, y `_lock_run` sin guarda. Todas detectadas.
- **Roturas independientes de QA** (22 entre las dos pasadas): detectadas, salvo los supervivientes que se
  documentan abajo.
- **Supervivientes conocidos (no bloqueantes):**
  - `complete_run` sobre un run ajeno en estado `failed`: una guarda de `_lock_run` con excepción «salvo si
    está failed» es indistinguible, porque el UPDATE final también rechaza con `PermissionError`. Impacto
    bajo: el run no se reescribe y los registros ajenos no se tocan. Mejora opcional y barata.
  - `complete_run` con `records=()` sobre un run propio con registros previos: ninguna prueba comprueba que
    se vacíen (una reingesta con 0 filas debe limpiar los datos viejos). Queda fuera del alcance de H-08
    y se anotará como candidato a diferido en la tarea 7.1.
  - Equivalentes: un `DO UPDATE` que además asigne `tenant_id` es un no-op porque el `WHERE` ya exige
    igualdad. Que `_delete_records` ignore `subscription_id` lo detecta el vecino
    `test_cleanup_preserves_inconsistent_cross_scope_children`.
- **Aserción vacua conocida:** `assert restarted["error_code"] is None` del control positivo del run
  `completed` no discrimina (el valor ya era nulo); es inocua y la cobertura real está en el caso del
  reintento tras fallo. No se retira para no debilitar nada.
- **Limitación de la técnica (redacción de QA):** estas pruebas demuestran, sobre SQLite, que cuando una
  sentencia del repositorio afecta 0 filas la guarda lanza la excepción esperada y la transacción se revierte
  entera. No demuestran la semántica de `rowcount` de CockroachDB con psycopg: CockroachDB podría devolver
  otro `rowcount` para UPDATE, DELETE o INSERT, o 0 para `INSERT ... ON CONFLICT DO UPDATE ... WHERE` en un
  caso que SQLite no reproduce. Un `RAISE(IGNORE)` en un trigger BEFORE se parece al fallo real, pero no es
  igual a una escritura rechazada por la base en un nodo remoto. Tampoco demuestran el bloqueo por
  `SET id = id` ni la serialización de `_lock_run`. La verificación en CockroachDB sigue pendiente en la
  variante `cockroach` (omitida en CI) y en `test_azure_cost_cockroach_integration.py`.
- **Observación de producto, sin hallazgo:** `start_run` no actualiza `request` al reiniciar un run propio
  (el `DO UPDATE` no lo incluye). QA lo confirmó con un script desechable y lo valora informativo: el id del
  run es un `uuid5` que incluye la definición canónica (`ingestion_run_id`), de modo que el mismo id implica
  la misma definición, y la única llamada de producto a `start_run` es `AzureCostIngestionService.ingest`.
  Sólo divergiría con un llamador futuro que reutilice un id con otra definición. No se registra `RF-054`.
- **Veredicto QA:** accept (segunda pasada). Producto sin cambios (`git diff --stat -- apps` vacío).


## Tarea 5.5 — H-01, contrato de error de las rutas de billing (backend)

- **Archivo nuevo:** `apps/backend/tests/test_billing_error_contract.py`, 37 casos (461 líneas) con la
  aplicación real, la autenticación y la pertenencia reales y la base sustituida por un doble; sin skips ni
  xfail. **El SQL real de `fetch_tag_coverage` y `fetch_billing_summary` no se prueba aquí** (usa `jsonb_typeof`,
  `->>` y `regexp_replace`, que SQLite no tiene): sigue cubierto sólo por las variantes CockroachDB, omitidas
  en CI. El docstring lo dice.
- **Comando:** `python -m pytest tests/test_billing_error_contract.py -q -p no:cacheprovider -W ignore` desde
  `apps/backend` (Python 3.12).
- **Resultado limpio:** 37 passed, tres veces seguidas y en orden inverso. Con `test_tag_coverage.py`,
  `test_billing_summary.py`, `test_budget_evaluation.py` y `test_tenant_isolation_api.py` en ambos órdenes:
  117 passed y 32 omitidas (CockroachDB preexistentes). La suite completa del backend en el contenedor da 1033
  passed y 62 omitidas, las mismas omitidas que en la referencia de CI.
- **Qué cubre:** en `GET /billing/tag-coverage`, el camino feliz con importes decimales conservados como
  cadena (incluido `9007199254740993.01`) y los `null`; el reenvío del tenant activo y del periodo como `date`
  (también para un usuario multi-tenant en ambos tenants); el periodo por defecto, con el reloj congelado en
  cinco instantes (mitad de mes, 31 de diciembre con cambio de año, año bisiesto, 1 de enero y último segundo
  de junio); que con fechas explícitas no se lee el reloj; que una clave extra del doble no llega a la
  respuesta; el 409 con cuerpo exacto `{"detail": {"code": "ambiguous_cost_source"}}` sin que el mensaje de la
  excepción aparezca en la respuesta, en stdout, en stderr ni en los registros; y que un error plano o un
  resultado malformado dé 500 y no 409 ni un 200 parcial. En `GET /billing/summary`, el mismo 409 para
  distintas agrupaciones (con `tag_key` canónico), el 500 para errores planos, una sola llamada al repositorio,
  y que el 409 no enmascara nunca un 401 ni un 403 ni afecta a otras rutas.
- **Roturas del tester** (copia desechable, 50): quitar o ensanchar el `except`, cambiar estado, código o
  `detail` del 409, tenant fijo, `start` y `end` intercambiados o ignorados, `group_by` y `tag_key` sin
  canonizar, sin `response_model` o con `model_construct`, importes como float, periodo por defecto en varias
  formas erróneas, 409 que imprime, registra o escribe, doble llamada y `except` demasiado ancho. 49 se
  detectan y una es equivalente.
- **Roturas independientes de QA** (~30, entre tag-coverage, summary y periodo por defecto): llamar a otro
  método del repositorio, `end` inclusivo, 409 convertido en 200, `required_tags` incompleto, caché o 409
  pegajoso por tenant, 409 condicionado a una fecha explícita o a la agrupación, tenant fijo en la firma y
  orden de monedas alterado, entre otras. Detectadas.
- **Supervivientes:** (1) una cabecera de respuesta `X-Debug` con datos añadida al 409 no la detecta ningún
  test porque ninguno mira las cabeceras de respuesta; es una rotura exótica y se deja como superviviente
  conocido (cerrarlo es una aserción sobre `response.headers`). (2) Quitar el `from None` del
  `raise HTTPException` no cambia la respuesta. (3) `return result` conservando el `response_model` es
  equivalente porque FastAPI valida y filtra igual.
- **Comportamiento fijado a propósito:** un error plano del repositorio o un resultado del doble que viola el
  esquema responden 500 sin filtrar detalles (fallar cerrado), y `ValueError` plano no se convierte en 409
  aunque `AmbiguousCostSource` herede de `ValueError`. QA lo valora contrato deseable: el 500 lo produce
  `RequestIdMiddleware` (`request_context.py:19-23`), que registra sólo el tipo de la excepción. Detalle
  incidental menor: `assert tz is timezone.utc` fija la identidad del objeto, de modo que un refactor a
  `ZoneInfo("UTC")` lo rompería sin cambiar el comportamiento; el patrón ya existe en
  `test_ownership_questions.py`.
- **Reloj:** se congela con un `monkeypatch` local sobre `app.api.routes.billing.datetime`, restaurado por
  test, sin contaminar otros módulos. QA lo probó con zonas horarias extremas (`Pacific/Kiritimati`,
  `America/Los_Angeles`) y barrió cada día de 2024-01-01 a 2026-12-31 a las 23:59:59 UTC sin ninguna forma
  inválida. No hay dependencia del reloj real ni del orden.
- **Proporcionalidad (ruido conocido, no bloqueante):** 37 casos para ~6 líneas de producto. QA midió con las
  roturas hechas que se podrían retirar 15 casos y ~25 líneas de aserción (casos `multi-*` de reenvío,
  variantes redundantes de error plano y de agrupación, instantes del reloj subsumidos, el test del
  reloj que falla si se lee y la aserción de `contract_version` por defecto) sin perder la detección de
  ninguna rotura, dejando ~390 líneas y 22 casos. La diferencia es de un 15 % y se decidió no abrir otra
  ronda; la mayoría son filas de parametrización baratas (4,5 s en total). Si un revisor lo prefiere, es un
  recorte mecánico.
- **Veredicto QA:** accept. Producto sin cambios (`git diff --stat -- apps` vacío).


## Tarea 5.6 — H-04, reserva rechazada y resultado de publicación fuera de contrato (backend)

- **Archivo nuevo:** `apps/backend/tests/test_job_reservation_rejection.py`, 137 líneas y 14 casos de tres
  funciones, con la aplicación, la autenticación y la pertenencia reales, SQLite real y sólo la cola doblada;
  sin skips ni xfail. Reutiliza los dobles de `test_job_publication.py` importando sólo nombres que no son
  tests, y no repite lo que ese archivo ya cubre (los resultados `not_sent`, `rejected` y `unknown` que llegan
  por `publish` y el fallo SQL de finalización).
- **Comando:** `python -m pytest tests/test_job_reservation_rejection.py -q -p no:cacheprovider -W ignore`
  desde `apps/backend` (Python 3.12).
- **Resultado limpio:** 14 passed. Con `test_job_publication.py`, `test_tenant_isolation_api.py` y
  `test_cors.py`: 114 passed y 4 omitidas (variantes CockroachDB preexistentes), en dos ejecuciones; QA lo
  repitió en ambos órdenes y sin nombres de test duplicados.
- **Qué cubre:** una reserva con `outcome == "not_sent"` da 503 con cuerpo exacto
  `{"detail": ..., "code": "publish_not_sent", "job_id": null, "retryable": false}` antes de crear el trabajo,
  sin `Retry-After`, sin el contenido enviado por el cliente, sin filas nuevas en `jobs`, sin llamar a
  `create_job`, `finalize_job_publication` ni `publish`, y sin tocar la métrica de trabajos aceptados
  (también para un usuario multi-tenant sobre tenant-b). Como control positivo, sólo la cadena exacta
  `not_sent` corta la ruta: una reserva sin `outcome`, con `reserved`, `rejected`, `unknown` o `NOT_SENT` sigue
  el flujo normal con 202, se publica con esa reserva, se cancela una vez y suma una a la métrica. Un
  `outcome` de publicación fuera de contrato (`bogus`, vacío, `None`, `CONFIRMED`, `Confirmed`, un entero y un
  marcador distintivo) da un 500 genérico sin filtrar el valor, no finaliza la publicación, cancela la reserva
  una vez, no cuenta como aceptado y no deja el trabajo en `queued` ni persiste el valor.
- **Roturas del tester** (copia desechable, 31 en la primera ronda y 9 tras cada mejora): quitar o alterar el
  retorno temprano, el código o el cuerpo del 503, `retryable`, la métrica, comparar con `!=` o con la
  veracidad de la reserva, crear el trabajo antes de reservar, quitar o ensanchar la guarda del outcome,
  normalizar mayúsculas, que el valor inválido llegue a `finalize_job_publication`, mover, duplicar o anular
  `cancel`, reflejar el valor en la respuesta, imprimirlo, registrarlo o persistirlo. Todas detectadas salvo los
  supervivientes de abajo.
- **Roturas independientes de QA** (14) y mías: una segunda reserva antes de comprobar el tenant, `Retry-After`
  o retorno temprano sólo para un tenant, la métrica antes de finalizar, el outcome inválido que devuelve 503,
  que finalice como `unknown`, que deje el trabajo `queued` o que se persista, y un `print(outcome)` en el
  camino inválido. Detectadas.
- **No hay fuga de reserva en la salida temprana (hallazgo descartado):** `RabbitMQQueue.reserve()`
  (`rabbitmq_queue.py:305-319`) devuelve `PublishResult("not_sent", ...)` en sus tres fallos (`stopping`,
  `owner_unavailable`, `capacity`) sin registrar ningún ticket, y `cancel()` sólo actúa si la reserva está en
  `_tickets`. Por eso la ruta no llama a `cancel` ahí y no se asierta; la versión inicial lo fijaba y se retiró
  por estar acoplada a la implementación.
- **Fragilidad corregida:** una primera mejora sustituyó la búsqueda de la palabra `outcome` en los logs por
  la igualdad exacta del conjunto de cabeceras, de los loggers y de los eventos, lo que habría fallado ante
  cualquier cabecera o evento legítimo nuevo (por ejemplo un `X-Request-Id`). Se recortó a lo que no tiene ese
  riesgo: subcadenas distintivas en respuesta, cabeceras y logs; todas las líneas de stdout y stderr son JSON y
  objetos; ninguna clave de registro contiene `outcome` ni `publication`; y `exception_type` es exactamente
  `RuntimeError`.
- **Supervivientes conocidos y aceptados:** un valor no distintivo (vacío, `None`, `7`) en una cabecera de
  depuración, en un registro JSON sin esas claves o en un `logging.warning` no es observable sin fijar el
  conjunto exacto de cabeceras o eventos, y se prefiere no fijarlo; persistir el valor vacío en `jobs.result`
  tampoco (es subcadena de cualquier texto). Es inobservable offline que el mensaje del `RuntimeError` incluya
  el valor, porque el middleware sólo registra el tipo de la excepción. Quitar el `from None` o condicionar
  `cancel` al contenido del cuerpo son equivalentes o artificiales.
- **Fuera de alcance, detectado por un vecino:** reservar antes de validar `payload.tenant_id` sin cancelar en
  el 400 lo detecta `test_tenant_isolation_api.py::test_ingest_error_precedence_without_effects`.
- **Estado real del trabajo con outcome inválido:** queda en `publish_pending` con
  `{"publication": {"outcome": "pending", "code": "awaiting_publisher"}}` (se crea antes de publicar). El test
  sólo fija que no es `queued` y que no se persiste el valor, no el estado concreto, que es incidental.
- **Veredicto QA:** accept en la primera ronda. Las mejoras posteriores (quitar la aserción de `cancel`,
  comprobación estructural, supervivientes `b10` y `b12`) y su recorte los verifiqué yo (ejecución, lectura y
  una rotura independiente) sin una nueva ronda de QA, por ser cambios que QA propuso y de alcance pequeño.
  Producto sin cambios (`git diff --stat -- apps` vacío).


## Tarea 5.7 — H-06, guardrails de entrada y salida del agente (processor)

- **Archivo nuevo:** `apps/processor/tests/test_guardrail_validation.py`, 389 líneas, 25 funciones y 95 casos
  sobre las funciones reales de `app.agents.guardrails` (puras, sin dobles salvo un proveedor que cuenta
  llamadas en un caso); sin skips ni xfail y con marcadores sintéticos (`SECRETO-SINTETICO-*`). No repite lo
  que ya cubre `test_agent_runtime.py` (tenant vacío, origen `<script>`, metadatos públicos con `inf` y texto
  no JSON). El objetivo inicial de menos de 250 líneas no era alcanzable sin perder detección (QA lo midió con
  una batería de 86 mutantes) y se da por no aplicable: los límites 50, 100, 500, 4000 y la profundidad 4 son
  límites de seguridad y de tamaño del prompt, y los casos parametrizados caben en una o dos líneas.
- **Comando:** `python -m pytest tests/test_guardrail_validation.py -q -p no:cacheprovider -W ignore` desde
  `apps/processor` (Python 3.12).
- **Resultado limpio:** 95 passed. Junto a `test_agent_runtime.py` y `test_agent_ingestion_integration.py`: 135
  passed, en dos ejecuciones; QA lo repitió en orden inverso y no hay nombres de test duplicados.
- **Qué cubre:** entrada (payload que no es objeto; tenant ausente, `None`, no cadena o en blanco; estado
  inseguro y su límite de 64 caracteres; origen ausente, vacío, no cadena e inseguro, y su normalización con
  `strip` y minúsculas; metadatos que no son un objeto, con un caso que demuestra que se rechazan antes de
  llamar al proveedor), saneado de metadatos (redacción de claves sensibles en cualquier nivel y en cualquier
  capitalización sin que el valor secreto aparezca en la salida, profundidad y su frontera exacta, recorte a 50
  elementos de listas y diccionarios, cadenas anidadas y de primer nivel a 500, claves a 100, no finitos, tipos
  desconocidos, tuplas, claves no cadena y el aviso de truncado con una vista previa de 3900 caracteres y la
  frontera exacta de 4000) y salida (respuesta vacía o que no es texto, cinco entradas hostiles que no filtran
  su contenido ni por el mensaje, ni por `__cause__`, ni por `__context__`, ni por el traceback, y la guarda
  `NUMERIC_CLAIM` contra cifras sin evidencia estructurada, con ocho formas de unidad rechazadas y cinco
  entradas con cifras sin unidad o unidades sin cifra aceptadas).
- **Roturas del tester** (copia desechable, ~70 entre las tres rondas) y **de QA** (15 manuales y una batería de
  86 mutantes): cada guarda, los patrones de origen y estado, `strip` y minúsculas, la redacción y su
  sensibilidad a mayúsculas y nivel, `credential` y `token` en la lista de palabras, profundidad, límites,
  vista previa, tuplas, `ensure_ascii`, separadores, no finitos, respuesta vacía, el payload en el error,
  `raise ... from exc`, `isinstance`, la lista de fuentes soportadas y `NUMERIC_CLAIM` (`%`, `USD`, `euros?`,
  `IGNORECASE`, `€`, el límite de palabra y aceptar sin evidencias). Detectadas.
- **Primera pasada de QA: `changes-requested`.** Pidió cubrir `NUMERIC_CLAIM` (sobrevivían `%`, `USD`, `euros`
  e `IGNORECASE`, ni en este archivo ni en los vecinos), el recorte de cadenas anidadas (sólo se probaba en el
  primer nivel) y retirar dos tests que fijaban detalles incidentales (el orden «tenant primero» y el formato
  compacto exacto, ya protegido por otros tests). Aplicado; se redujeron además a cinco las entradas hostiles.
- **Corrección de la afirmación de QA:** QA daba por matables dos mutantes de `NUMERIC_CLAIM` (quitar `-?` y
  quitar la coma o la parte decimal). Son **equivalentes**: el `(?<!\w)` permite al motor emparejar `5 EUR`
  dentro de `12,5 EUR` y `4 euros` dentro de `-4 euros`, así que el resultado booleano de `search` no cambia.
  El tester lo comprobó por fuerza bruta (21.435.887 cadenas, 0 diferencias) y el orquestador lo reprodujo de
  forma independiente (111.110 cadenas sobre un alfabeto menor, 0 diferencias). Los casos `12,5 EUR` y
  `-4 euros` se mantienen como documentación del contrato, no como detección.
- **Supervivientes conocidos y aceptados:** recorte de cadenas sólo hasta profundidad 2 (un caso a
  profundidad 3 lo mataría; no se añade por proporción); añadir `key` o `bearer` a `SENSITIVE_KEY` (sobre-redacción
  que ningún caso de clave pública distingue); `AgentResponseError` que deje de heredar de `AgentGuardrailError`
  (nadie captura la base); `sort_keys=False` (equivalente, `_sanitize_value` ya ordena antes de insertar) y
  quitar `bool` de los escalares (equivalente, `bool` es subclase de `int`).
- **Defecto de producto confirmado, no fijado con una prueba (a registrar como `RF-054-002`):**
  `_sanitize_value` (`guardrails.py:115-119`) recorta la clave con `str(key)[:100]` y *después* busca la palabra
  sensible, de modo que una clave con la palabra más allá del carácter 100, o cortada por el recorte, no se
  redacta y su valor llega íntegro al prompt del proveedor (`service.py:34-38`). Reproducido por el tester,
  por QA (con `"a"*95+"password"` y `"a"*100+"password"` filtrando; con `"a"*90+"password"` y
  `"a"*92+"password"`, que llegan justo a 100, redactando) y por el orquestador, tanto con `sanitize_metadata`
  como con `prepare_agent_input`. Los metadatos los aporta quien envía el trabajo (`IngestJobRequest.metadata`
  es un `dict` libre sin validar claves). Gravedad propuesta por QA: **baja**, defensa en profundidad, porque
  no hay fuga entre tenants y el remitente sólo expone sus propios datos a un proveedor externo; sube a
  **media** si algún flujo compone `metadata` con claves de terceros (por ejemplo etiquetas de Azure).
  Corrección mínima: `SENSITIVE_KEY.search(str(key))`, que pasa todas las pruebas actuales. No se escribe un
  test que consagre la fuga ni uno que exija la corrección, porque fallaría sin `xfail`; tras corregir el
  producto habrá que añadir una prueba de regresión.
- **Código inalcanzable, informativo (a registrar como `RF-054-003`):** las líneas 146-147 (`except ValueError`,
  mensaje «provider response is not valid JSON») no se pueden alcanzar: `ValidationError` de pydantic v2 es
  subclase de `ValueError` y se captura antes, y ninguna entrada hostil (NUL, `{`, `NaN`, anidación de 100.000
  niveles, un número de 5.000 dígitos, BOM, un objeto de 5 MB) produce ese mensaje: todas dan «does not match
  the FinOps response schema». Corrección sugerida: borrar el `except ValueError` o invertir el orden. Queda
  documentado en un comentario del test y no se fuerza por mock.
- **Detalle de diseño, sin hallazgo:** el aviso `metadata_truncated` puede acabar en torno al doble de 4000
  caracteres, porque la vista previa de 3900 se vuelve a serializar y cada `"` o `\` se escapa (medido: 7.824
  y 7.828 caracteres con diez valores de 500 comillas). Sigue siendo JSON válido y está acotado.
- **Veredicto QA:** changes-requested en la primera pasada; las correcciones las verifiqué yo (ejecución dos
  veces, git y la equivalencia de los mutantes de `NUMERIC_CLAIM`) sin una segunda ronda de QA, por ser
  exactamente lo que QA pidió. Producto sin cambios (`git diff --stat -- apps` vacío).


## Tarea 5.8 — H-09, fallos de transporte y páginas malformadas del cliente Azure (processor)

- **Archivo nuevo:** `apps/processor/tests/test_azure_client_failures.py`, 226 líneas, 6 funciones y 16 casos
  (el informe del tester decía 18: era un error de cuenta; `--co` da 16), sin skips ni xfail y con un token
  sintético. Reutiliza sólo nombres no test de `test_azure_cost_client.py`. No repite lo que ya cubren esa
  suite (errores HTTP, JSON y celdas inválidos, columnas duplicadas o ausentes, páginas vacías, ciclos,
  `nextLink` cruzado y la redirección real) ni `test_azure_api_contract_integration.py` (401, 403 y 404 con
  servidor real).
- **Comando:** `python -m pytest tests/test_azure_client_failures.py -q -p no:cacheprovider -W ignore` desde
  `apps/processor` (Python 3.12).
- **Resultado limpio:** 16 passed, diez veces seguidas y bajo carga de CPU (16 bucles sobre 8 núcleos, de 2,4 a
  3,3 s); con `python -X dev -W error::ResourceWarning` también; junto a `test_azure_cost_client.py`,
  `test_azure_cost_ingestion.py` y `test_azure_api_contract_integration.py`: 136 passed, en tres ejecuciones y
  en orden inverso. Al terminar queda un solo hilo y ningún socket abierto.
- **Qué cubre:** (A) transporte real con un `ThreadingHTTPServer` en loopback: una conexión rechazada da
  exactamente `AzureCostClientError` («connection failed») y un servidor que no responde o se detiene a mitad de
  cuerpo da exactamente `AzureCostTimeoutError`, sin token ni puerto en el mensaje y con una sola petición (sin
  reintentos de red); un caso con el `_opener` sustituido para `URLError` con motivo de timeout, que no se puede
  reproducir de forma determinista con sockets. (B) A través de `AzureCostIngestionService` con SQLite: el run
  queda `failed` con `error_code` igual al nombre de la excepción, contadores a 0, sin registros nuevos y sin
  tocar un run completado de otro tenant. (C) Nueve páginas malformadas (columnas vacías o no lista, columna que no
  es objeto, nombre vacío o no cadena, tipo fuera de contrato, `rows` que no es lista y `nextLink` numérico o
  vacío) con una sola petición, y una página malformada en la segunda posición que no devuelve el resultado
  parcial.
- **Roturas del tester** (copia desechable, 36) y **de QA** (20, distintas): cada `except` del transporte, los
  tipos de excepción cruzados, token o URL en el mensaje, no pasar `timeout` a `opener.open`, reintentar errores
  de red, cada una de las cinco comprobaciones de página y sus variantes, devolver el resultado parcial, y en el
  servicio no marcar `failed`, `error_code` constante, `completed` vacío, contadores, registro parcial, borrar
  registros de todos los tenants, no guardar `error_code` y `fail_run` con el tenant equivocado. Detectadas, sin
  supervivientes reales: cuatro roturas de QA las detectan sólo los vecinos (`HTTPError` que lanza `Timeout`,
  `nextLink` de otro origen, página intermedia vacía y columnas sin `Currency`), que es funcionalidad de otra
  suite; `except TimeoutError` sin `socket.timeout` es equivalente (en Python 3.10+ son el mismo tipo).
- **Defecto de producto confirmado, no fijado con una prueba (a registrar como `RF-054-004`):**
  `UrllibTransport.post` (`azure_cost.py:92-97`) sólo captura `TimeoutError` y `URLError`, y
  `OpenerDirector.open` sólo envuelve en `URLError` los fallos de `request()`; los de `getresponse()` y los de
  `response.read()` salen **crudos**. Con un servidor que cierra sin responder sale `http.client.RemoteDisconnected`,
  con una línea de estado basura `BadStatusLine`, con un `Content-Length` mayor que el cuerpo `IncompleteRead`, y
  con un RST `ConnectionResetError`; ninguno es `AzureCostClientError`. Reproducido por el tester, por QA (que
  además ejecutó el `main()` real con `startup_boundary` contra un servidor hostil) y por el orquestador con un
  socket crudo. El servicio (`azure_cost_ingest.py:73`, `except Exception`) marca el run `failed` con el nombre
  crudo como `error_code` y relanza, así que la base queda coherente. El CLI (`run_azure_cost_ingestion.py:91-97`)
  sólo captura las tres excepciones seguras, de modo que no emite su JSON de fallo
  `{"error_code": ..., "status": "failed"}`: `startup_boundary` (`runtime_secrets.py:39-40`) lo reescribe como
  `StartupError("Runtime startup failed; check configuration and dependency availability.")` sin causa visible,
  un mensaje que apunta a configuración cuando el fallo es de red; el código de salida 1 se deduce del código,
  no se midió. Plausible en operación: `RemoteDisconnected` y `ConnectionResetError` son lo que ve un cliente
  cuando la API de Azure o un balanceador reinicia a mitad de petición. Sin pérdida de datos ni fuga en el CLI
  (los logs y la base sólo guardan el nombre de la excepción), aunque `BadStatusLine` lleva en su `str` la línea
  recibida del servidor, que vería quien use el cliente sin `startup_boundary`. Gravedad propuesta por QA:
  **media-baja**. Corrección mínima: en `post`, tras `except URLError`, capturar
  `(http.client.HTTPException, OSError)` y lanzar `AzureCostClientError("Azure Cost API connection failed") from exc`
  (después de `HTTPError` y de los timeouts, porque `TimeoutError` es subclase de `OSError`); eso haría perder la
  distinción actual del `error_code`, que se puede conservar con una subclase. Una vez corregido, un test que lo
  exija pasa de rojo a verde sin `xfail`; no se escribió ninguno que lo exija ni que consagre la fuga.
- **Observaciones de QA aplicadas o aceptadas:** (O1) en Windows nativo una conexión a un puerto cerrado con
  `timeout=0.3` da `TimeoutError` tras ~0,32 s (medido con Python 3.13 local), por lo que el caso de conexión
  rechazada usa un plazo generoso, ya que no espera nada; CI sólo usa `ubuntu-latest`. (O2) `closed_port()` reserva
  y cierra el puerto antes de conectar, con una ventana teórica mínima de que otro proceso lo tome; ninguna
  ejecución la mostró. El stub de `_opener` es aceptable: es la única costura de red de `UrllibTransport` y
  sólo la detecta él (rotura m11).
- **Corrección del ejecutor de pruebas:** el contenedor sólo copiaba `apps/` y fallaban 4 pruebas de la primera
  pasada que leen archivos de la raíz del repositorio; ahora copia el árbol versionado completo. Los errores no
  eran del archivo nuevo ni del producto (la prueba de contrato también fallaba sola).
- **Veredicto QA:** accept. Producto sin cambios (`git diff --stat -- apps` vacío).


## Tarea 5.9 — H-11, filtros con dimensión o etiqueta no soportada (azure-cost-api)

- **Archivo nuevo:** `apps/azure-cost-api/tests/test_unsupported_filters.py`, 86 líneas y 22 casos (16 + 5 + 1,
  contados con `--co -q`), con el `TestClient` real sobre la aplicación y el CSV público; sin skips ni xfail.
  Reutiliza `CASES_BY_ID` y `post_query` de `test_query_api.py` y no repite sus casos: el caso contractual
  `unsupported-dimension` es una agrupación (línea 39 del motor), no un filtro.
- **Comando:** `python -m pytest tests/test_unsupported_filters.py -q -p no:cacheprovider -W ignore` desde
  `apps/azure-cost-api` (Python 3.12).
- **Resultado limpio:** 22 passed. Junto a `test_query_api.py`, `test_repository.py` y `test_resilience.py`: 81
  passed, tres veces seguidas y en orden inverso; sin nombres de test duplicados.
- **Qué cubre:** un nombre de dimensión o de etiqueta no soportado en un filtro se rechaza con un 400 de cuerpo
  exacto `{"error": {"code": "BadRequest", "message": "Unsupported dimension|tag: <nombre>"}}`, sin filas ni
  `properties`, tanto en la raíz como anidado en cualquier posición (primero, medio y último hijo de `and` y de `or`,
  `and` dentro de `or` y `or` dentro de `and`); la agrupación por una etiqueta no soportada; que dimensiones y
  etiquetas son conjuntos distintos (un nombre válido como etiqueta no vale como dimensión, ni al revés, en
  agrupación y en filtro); y un control positivo con filtros válidos de dimensión, de etiqueta y de ambos.
- **Roturas del tester** (copia desechable, 34): quitar cada comprobación (líneas 55 y 57), quitar la recursión
  o limitarla a `and`, a `or`, al primer hijo o al último, intercambiar los conjuntos, 422 o 500 en lugar de 400,
  cambiar el código o el mensaje, validar después de leer registros, datos en el error, condiciones invertidas y
  `return` en cada rama. 31 detectadas; una equivalente (`is not None` frente a la veracidad de un modelo
  pydantic, siempre verdadera) y M13 (ver abajo). **Roturas independientes de QA** (13): tres relevantes para
  este hueco (no validar el filtro sin agrupación, nombre de etiqueta en minúsculas en el mensaje y `return` en
  lugar de `raise` en la rama de etiqueta) se detectan sólo con el archivo nuevo y ningún test vecino las
  detecta, lo que acredita su valor.
- **Supervivientes conocidos y aceptados (fuera del hueco o equivalentes):** validar sólo `grouping[:1]` (una
  segunda agrupación inválida no se prueba en ninguna parte; el producto la rechaza hoy), el orden entre el 400 y
  el 404 de suscripción desconocida, las cabeceras del 400, `strip` del nombre (hoy `"ServiceName "` da 400) y el
  orden en que se informa de dos hijos inválidos (no es contractual). `and` de un solo hijo y `dimensions` más
  `tags` a la vez no son construibles: el modelo (`QueryFilter`, `models.py:64-84`) exige exactamente una rama y
  al menos dos operandos.
- **Ambigüedad de contrato, gravedad baja (a registrar como `RF-054-005`, documental):** la validación de
  **nombres** de campo es exacta (`not in frozenset`: `servicename`, `SERVICENAME`, `ENV`, `Env`, `"env "` y
  `"ServiceName "` dan 400), mientras que los **valores** se comparan sin distinguir mayúsculas (`STORAGE` y `PROD`
  dan 200 con filas). El contrato dice «los filtros de dimensiones y tags ignoran mayúsculas»
  (`docs/api/azure-cost-query-contract.md:78`; `azure-cost-query-mapping.json:49`:
  `dimensionAndTagFilters: case-insensitive`; `openspec/specs/simulated-azure-cost-api/spec.md:70`:
  «case-insensitive `In` comparisons») sin aclarar si se refiere a nombres o a valores. El comportamiento actual
  es coherente con la lectura natural (las comparaciones `In` comparan valores) y conservador (400 en lugar de
  aceptar). Único indicio contrario: `repository.tag_value` hace `casefold()` del nombre de la etiqueta, hoy
  inalcanzable por la validación exacta; y relajar sólo la validación de dimensiones daría `KeyError` y un 500
  (deducido leyendo `dimension_value`, no ejecutado). Es una pregunta al responsable del contrato, no al tester ni
  al coder. **No se fija con un test**: congelaría una decisión no tomada; si el contrato se aclara a «nombres
  exactos», bastarían un caso con `servicename` y otro con `ENV`.
- **Observaciones menores, no bloqueantes:** el texto del mensaje (`Unsupported dimension: X`) está literal en 21
  casos y no figura en el contrato (sólo fija el estado 400 y el código `BadRequest`), de modo que una
  reformulación razonable los rompería todos a la vez; es el único canal que distingue qué comprobación se
  disparó y con qué nombre, y se mantiene. La matriz de 16 posiciones es sobredimensionada: tres casos
  (`and-medio` de dimensión, `or-dentro-de-and` de dimensión y la raíz de etiqueta) detectan las mismas roturas
  (se podrían retirar 6 de etiqueta sin pérdida), pero cuesta ~0,1 s y es una tabla legible; no se recorta.
- **Veredicto QA:** accept. Producto sin cambios (`git diff --stat -- apps` vacío).

## Tarea 5.10 — pruebas nuevas que fallan contra el candidato sin modificar

Ninguna prueba nueva falló contra el candidato `e1c2a8f` sin modificar, de modo que no hubo que entregar ningún
fallo esperado estricto ni dejar ninguna prueba fuera. Los defectos de producto aparecieron por sondeos y por la
lectura del código, no por un fallo de prueba, y **no se fijaron con ninguna aserción** (consagrarían el defecto o
exigirían la corrección sin `xfail`): `RF-054-001` (resultado persistido corrupto en un trabajo completado,
`ingest.py:74`), `RF-054-002` (la clave se recorta a 100 caracteres antes de buscar palabras sensibles,
`guardrails.py:115-119`), `RF-054-003` (rama inalcanzable `except ValueError`, informativo), `RF-054-004`
(`UrllibTransport.post` deja escapar excepciones crudas, `azure_cost.py:92-97`) y `RF-054-005` (ambigüedad de
contrato sobre mayúsculas en los nombres de campo). Se registran en `openspec/findings/backlog.md` en la tarea 7.1.

## Tarea 5.11 — el diff sólo añade pruebas

Contra la base auditada `e1c2a8f`, `git diff --name-status` bajo `apps/`, `.github/`, `package.json`,
`pnpm-lock.yaml`, `turbo.json`, `docker-compose.yml`, `packages/` y `tools/` muestra únicamente nueve archivos
añadidos (`A`), todos `test_*.py` nuevos bajo `apps/*/tests/`: cuatro en backend, cuatro en processor y uno en
azure-cost-api. No hay ningún archivo modificado ni borrado, ninguno que no sea una prueba nueva, y nada en
`apps/frontend`, `apps/*/app`, `apps/*/requirements*.txt`, CI ni dependencias.

