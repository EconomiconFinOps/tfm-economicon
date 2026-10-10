# JUP-022 — Evidencia de validacion

Cambio: [jup-022-semantic-retrieval](../../openspec/changes/archive/2026-10-03-jup-022-semantic-retrieval/design.md). Tarjeta: https://trello.com/c/DPZpQ09b. Rama local `feat/JUP-022-semantic-retrieval` sobre `develop` `d6fc408` (JUP-021 integrada). Fecha: 2026-10-03.

## Estado de las dependencias (tarea 1.1)

| Dependencia | Estado el 2026-10-03 | Efecto en este cambio |
| --- | --- | --- |
| JUP-021 (#53, vigilancia de dimension y persistencia de pgvector) | integrada en `develop` el 02/10 | La rama se rebaso sobre ella sin conflictos; el arranque del backend compara la dimension de la columna con la del proveedor. |
| JUP-023 (#65, cliente LiteLLM del processor) | integrada en `develop` el 03/10 | La rama se rebaso sobre ella sin conflictos y la prueba de paridad de categorias dejo de saltarse: 6 de 6 pasan contra el cliente real (ADV-2 resuelto). |
| JUP-025 (#55, citas y evidencia) | con cambios pedidos | Reescribe la misma ruta del asistente: habra que resolver conflictos al integrarse el segundo en llegar. |

## Comandos y resultados

| Que | Comando | Resultado |
| --- | --- | --- |
| Backend con pgvector real | `JUP086_VECTOR_TEST_URL=<pgvector desechable en loopback> python -m pytest -q` en `apps/backend` | 552 passed, 17 skipped |
| Backend como la CI (sin servicios reales) | `python -m pytest -q` en `apps/backend` | 540 passed, 29 skipped |
| Processor | `python -B -m pytest tests -q` en `apps/processor` | 414 passed, 55 skipped (sin cambios en el processor) |
| Calibracion y utilidades Python | `python -m unittest discover -s scripts/tests` | 59 tests OK (1 skipped: paridad con pgvector, opt-in) |
| Herramientas | `node --test tools/*.test.mjs` | 242 de 243; el fallo es `local-doctor.test.mjs` ("puertos publicados no ocupados"), de JUP-050, porque la maquina de validacion tenia su propio stack en los puertos 3000 y 9090 |
| Etiquetas | `corepack pnpm retrieval-labels:validate` | 28 etiquetas (23 directas, 3 parciales, 2 sin cobertura) |
| OpenSpec y trazabilidad | `openspec:validate`, `jup:check:all`, `jup:cleanup:check`, `git diff --check` | 40/40; OK; 773 archivos; sin avisos |

Tras rebasar sobre `develop` `6410950` (con #65): backend 552 passed y 16 skipped con pgvector real y un fallo temporal de `test_rabbitmq_publisher.py::test_actual_pika_blocked_unblocked_resumes_once_and_close_is_terminal` ("Publisher did not reach the expected state within its observation budget") en una maquina con el stack de Docker levantado; es un test de JUP-086 que no toca este cambio y pasa 3 de 3 veces ejecutado solo (22 passed). Processor 448 passed y 57 skipped, herramientas 243 de 244 (mismo fallo del doctor por puertos ocupados), utilidades Python OK, OpenSpec 42/42.

El pgvector real fue `pgvector/pgvector:pg17` (la imagen del Compose) en un contenedor desechable en `127.0.0.1:55432`, eliminado al terminar.

## Mutantes

Cada mutante se aplico a una copia del codigo, se ejecutaron las pruebas del cambio y se restauro el original.

| Area | Mutantes | Detectados |
| --- | --- | --- |
| Almacen (`vector_store.py`): quitar el desempate, `<=` por `<`, orden descendente, quitar el filtro de tenant, `LIMIT` fijo | 6 | 6 |
| Proveedor del backend: seguir redirecciones, reintentar 401, quitar el plazo total de lectura, aceptar no finitos, longitud o numero de vectores, reintentos solo en transitorios, no reintentar 5xx | 8 | 8 (dos revelaron huecos que se cubrieron: 302 en POST y `1e999`) |
| Almacen y ruta: quitar el filtro de proveedor, invertir la comparacion de dimension, quitar la comprobacion de longitud, no pasar el proveedor, no capturar fallos del almacen o del proveedor | 6 | 6 |
| Trazabilidad: invertir o quitar el contador de vacios, quitar el contador de fallos, id de mensaje equivocado, distancias o documentos vacios, resultados a 0, parametros a 0, pregunta en el evento de exito o de fallo, quitar el id de documento | 11 | 11 |
| Trazabilidad: quitar la normalizacion de categorias | 1 | 1 (tras anadir un test directo) |

## Calibracion real

Gateway LiteLLM `v1.103.2` fijado por huella (ADR-0016 del PR #65), local y solo en loopback, con una clave virtual restringida al alias `economicon-embedding` y tope de 0,50. 80 llamadas por ejecucion, todas con respuesta 200. Informe: [JUP-022-retrieval-calibration.md](../spikes/JUP-022-retrieval-calibration.md); anexo de troceado: [JUP-022-retrieval-calibration-chunking.md](../spikes/JUP-022-retrieval-calibration-chunking.md).

- `top_k` 4 (3 a 6 dan el mismo acierto) y distancia maxima 0.6 con `litellm`, por la regla escrita: la menor distancia del barrido que conserva al menos el 90 % del acierto por seccion sin umbral.
- Con 0.6 el acierto por seccion de los casos `answer` pasa de 75 % a 70 % y el 5 % queda vacio; los casos `clarify` y `abstain` siguen recuperando fragmentos, por lo que negarse o aclarar corresponde a las guardas de respuesta.
- Con el proveedor simulado el acierto por seccion fue de 15 a 50 %.

## Revision adversarial

Agente independiente `adversarial-reviewer`, recibiendo solo las specs, el diseno y el diff. Veredicto: **accept**, sin BLOCKING ni HIGH. Detalle y disposicion de cada hallazgo en [review.md](../../openspec/changes/archive/2026-10-03-jup-022-semantic-retrieval/review.md).

## No validado

- Arranque completo del backend (`lifespan`) contra los servicios reales de Compose con `litellm`: queda por reindexar el corpus en `vector(1536)` con el processor ya integrado.
- Reindexado del corpus en una base `vector(1536)` de extremo a extremo.
- Trazabilidad en un entorno con dos instancias o con carga: los contadores son del proceso.
- Claves expiradas o revocadas y presupuesto agotado contra el gateway real.

## Nota de release

| Fecha | JUP | Nota de release | Review | ADRs |
| --- | --- | --- | --- | --- |
| 2026-10-03 | JUP-022 | El chat recupera fragmentos con el proveedor de embeddings configurado, con `top_k` y distancia maxima explicitos (0.6 por defecto con `litellm`) y trazabilidad acotada; el backend usa su propia clave virtual. | [review.md](../../openspec/changes/archive/2026-10-03-jup-022-semantic-retrieval/review.md) | [ADR-0017](../adr/ADR-0017-backend-query-embedding-own-key.md) |

## Correccion tras la validacion del PR #67 (2026-10-03)

La validacion de Alejandro sobre `5f8bd90` pidio cambios (P1): el plazo del proveedor del backend no limitaba las cabeceras lentas. Reproduccion propia antes de corregir: servidor loopback que envia una cabecera a un byte cada 30 ms; timeout 0,05 s sin reintentos tardo 2,7 s, 0,5 s tardo 2,2 s y 0,1 s con dos reintentos tardo 6,9 s (tres intentos). Despues de la correccion, el mismo escenario acaba en `timeout` dentro del plazo (limites en las pruebas: 0,45 s, 1,0 s y 1,6 s respectivamente, con 1, 1 y 3 intentos). Detalle y mutantes en [review.md](../../openspec/changes/archive/2026-10-03-jup-022-semantic-retrieval/review.md). Backend: 563 passed y 16 skipped con pgvector real tras el cambio.

## Revision del PR #67 (2026-10-04)

Atendida la `Revision JUP-022` de Victor sobre `7f69269`: defaults de 10 s y un reintento con un tope de 60 s de intentos por pregunta, errores de arranque que nombran el ajuste, test del `lifespan` y registro cuando la comprobacion de dimension se omite. Detalle en [review.md](../../openspec/changes/archive/2026-10-03-jup-022-semantic-retrieval/review.md). Findings nuevos: RF-022-005 y RF-022-006.
