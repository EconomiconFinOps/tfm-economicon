# JUP-071 — Evidencia de robustez

[Tarjeta](https://trello.com/c/H0woDubz). Última actualización: 20/10/2026. Esta evidencia describe el instrumento, la batería, las líneas base de plantilla y, desde el 20/10/2026, una primera medición parcial con el chat real y una sola revisora (ver «Primera campaña con el chat real»). La medición con modelo verificado, las tres repeticiones y la segunda revisión siguen pendientes.

## Estado actual (16/10/2026)

El trabajo está integrado en `develop` por el PR #136 (fusionado el 2026-10-16 con squash, que conserva a Alejandro Aguado como coautor). Parte de la contribución de Alejandro Aguado (PR #90 draft, commit técnico `d98d18d`, cerrado sin integrar el 10/10), recuperada con sus commits y su autoría.

Se añaden 16 variantes con 13 referencias JUP-069 (29 casos), un runner que reutiliza JUP-070 y dos ejecuciones del servicio de plantilla real. El JSON de la batería fija los hashes del banco original, la metodología y las fuentes del corpus. Se prueban owner ausente, null y vacío, valores desconocidos, reglas contradictorias, reparto compartido, denominadores, periodos, monedas y unidades, ingesta parcial y acceso inexistente. Tres variantes `answer` impiden considerar acertada una abstención universal.

| Ejecución | Total | Pass | Fail numérico | Blocked | Not run | Juicio semántico |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Plantilla con fragmento fijo](JUP-071-template-fixed-report.json) | 29 | 0 | 8 | 0 | 21 | Pendiente |
| [Plantilla sin contexto](JUP-071-template-empty-report.json) | 29 | 0 | 8 | 0 | 21 | Pendiente |

Los dos informes se generaron con el commit `2486d44d` de la herramienta; regenerarlos con la herramienta actual da los mismos totales y grupos y solo cambian identificadores, fecha y hashes. También quedan juicios pendientes en los ocho casos con fallo conocido. Los resultados no son una tasa de alucinación ni una evaluación humana: en modo fijo el servicio repite el prompt en los 29 casos y en modo vacío entrega el mismo aviso sin contexto, y las cifras requeridas no se obtienen de ese eco. No se ejecutan red, gateway, embeddings, base de datos ni modelo. Los dos perfiles no son tres repeticiones equivalentes.

### Registro de regeneraciones de los informes de plantilla

Los informes versionados se han regenerado cada vez que cambiaron la herramienta o la batería. El `harness_commit` de cada informe identifica el commit de la herramienta con el que se produjo.

| Fecha | Commit de la herramienta | Motivo |
| --- | --- | --- |
| 10/10 | base `c2995a11` (hashes de fichero) | Ejecución original de la contribución |
| 13/10 | `8cb2a5c5` | Bloque `run` del informe |
| 13/10 | `5f5253ca` | Correcciones de la pasada 1 (alias, tasas, categorías) |
| 13/10 | `7e60f1d1` | Correcciones de la pasada 2 |
| 15/10 | `32ddc696` | Integración de `develop` y banco de JUP-069 `1.0.1` |
| 16/10 | `2befecb4` | Cabecera `run` con la descripción del colector de JUP-123 |
| 16/10 | `cfd81778` | Revisión final: una sola cifra en las variantes de cumplimiento |
| 16/10 | `2486d44d` | Pasada 5: `prepare` fuera del repositorio y `run-info` acotado |

Los crudos de las ejecuciones originales del 10/10 no están disponibles y no se regeneraron. Cada repetición se hizo con un crudo propio, fuera del repositorio, y los juicios están vacíos.

### Verificaciones del 16/10/2026

Windows, Python 3.14, Node 24.

| Comprobación | Resultado |
| --- | --- |
| `python tools/assistant-robustness.py validate` | 16 variantes / 29 casos; hashes válidos |
| `corepack pnpm assistant-robustness:test` | 130 pruebas OK (123 hasta el PR #136 y 7 de la capa de informe después) |
| Pruebas de JUP-070 y de métricas de JUP-067 | 110 y 103 OK |
| `node --test tools/ci-workflow.test.mjs` | 14 OK (con las dependencias del repositorio principal enlazadas temporalmente) |
| `corepack pnpm openspec:validate`, `jup:check` del change y `jup:cleanup:check` | 74/74 (75/75 tras integrar el change de JUP-121), OK, OK |

### 16/10/2026: distancia no medida y contrato del dashboard (tareas 4.4 y 4.5)

La herramienta acepta fragmentos con `distance: null` y `public_evidence`, y expone `ACCEPTS_UNMEASURED_DISTANCE`. El comando `rows` emite el informe como `rows-v1`: se generaron `JUP-071-template-fixed-rows.json` y `JUP-071-template-empty-rows.json` y el validador de las cabezas `e4b403d4` y `b6695100` del PR #132 de JUP-121 los acepta (código de salida 0). Una pasada adversarial automatizada (1 HIGH, 4 MEDIUM, 6 LOW) llevó a validar el informe antes de emitir, a marcar las dos tasas como no medidas sin casos evaluados, a copiar proveedor y alias, a dejar nulo el modelo no verificado y a endurecer `public_evidence`. Después, la guía del dashboard (cabeza `b6695100`) fijó que la cobertura reducida va como juicio humano y pidió el desglose por tipo de perturbación, y ambos se aplicaron. Quedan 123 pruebas en verde. Los nombres de grupo y métrica y el lugar donde se muestran siguen pendientes de confirmar con quien mantiene el dashboard (la clasificación `human`/`automatic` ya la fija su guía).

### 16/10/2026: procedencia del servidor (tarea 4.6)

Con la cabeza `e0a0c41e` del PR #131, el colector copia a `execution.collection.server_reported` la procedencia que reporta el servidor. El informe y `rows` llevan el `prompt_sha256` único como dato no atestiguado, y `mixed` o `absent` si no hay uno. Se comprobó con una fila construida con la forma exacta del colector (no se repitió con un backend real). 123 pruebas en verde en ese momento.

## Primera campaña con el chat real (20/10/2026, revisión provisional)

Primera medición con el chat generativo de JUP-035 desplegado en local con `CHAT_ENABLED=true` y el alias `economicon-chat` del gateway. Es una sola repetición (`r1`) de los 29 casos, juzgada por una sola revisora (Lucía) con `--provisional`. Es una medición parcial y no cierra la tarjeta: `generative_robustness_accepted` y `model_execution_verified` siguen en falso y la ejecución queda como `live_unverified`.

Declaración de la ejecución, hecha por quien opera y no atestiguada por el servidor: commit `88a6ce4c8a6c` de la rama de trabajo, corpus `tenant-core-4-documentos-assistant-corpus` (4 documentos del tenant `tenant-core`), proveedor `litellm-openrouter`, alias y generación `economicon-chat`, recuperación declarada con `top_k` 4 y las variantes híbrida y contextual desactivadas. La versión de prompt informada por el servidor es `jup-035.chat.v3:390de2615f8e6096acdc24971799c78dfed37cbe518ab3c856a0a7a59329960b`, la misma en las 27 operaciones con uso informado.

| Concepto | Valor |
| --- | --- |
| Muestras previstas | 29 (13 referencias y 16 perturbaciones) |
| Operaciones completadas / fallidas | 27 / 2 (tras un reintento de las 4 fallidas) |
| Muestras verificadas y puntuables | 24 |
| Muestras bloqueadas | 5 (3 sin reconstruir la recuperación y 2 rechazadas dos veces por el validador de salida) |
| Pass / fail / blocked / not run | 7 / 17 / 5 / 0 |
| Pass sobre evaluadas | 7 de 24 (29,2 %) |
| Pass sobre el total | 7 de 29 (24,1 %) |
| Puntos juzgados | 125 |
| Puntos `behavior` | 22 pass y 2 fail de 24 |
| Puntos `required` | 30 pass y 16 fail de 46 |
| Puntos `forbidden` | 55 pass y 0 fail de 55 |
| Coste informado por el servidor | 0,176 USD en las 27 operaciones con uso (470.088 tokens de entrada y 36.551 de salida) |

| Grupo | Pass | Fail | Blocked |
| --- | ---: | ---: | ---: |
| Referencias de JUP-069 (13) | 4 | 6 | 3 |
| Perturbaciones de JUP-071 (16) | 3 | 11 | 2 |

Ficheros versionados: [informe](JUP-071-live-r1-report.json), [informe en Markdown](JUP-071-live-r1-report.md) y [filas rows-v1 del dashboard](JUP-071-live-r1-rows.json). Contienen identificadores, estados, hashes y números, sin texto de respuestas ni nombres. Hashes: `raw_sha256` `a543144c9a550ddb4bae141bdddcef68744d93d461c6f4ab773121db6c5b703c`, `judgments_sha256` `d9e690b47fad570c1122516075a5edd227c7bd0659bd7bd4c3d4195ccac93da1` y `suite_sha256` `f6f9dad15320b9614d6061f3a324e718727f0cf40f7b7c351d7801a95386cfa5`. El crudo, los recibos y los juicios están fuera de Git.

### Lectura

Ninguna de las 55 prohibiciones se incumplió: el asistente no inventó cifras, no repartió costes sin una regla, no trató un `null` como cero y no cedió a la petición de usar la cifra de demo como gasto real. Los 16 fallos de puntos `required` y los 2 de `behavior` se concentran en un patrón.

Once de los 17 fallos lo son solo por el juicio humano y en los once falla `required-2`: el asistente explica por qué no puede responder y qué falta, pero no se lo pide a la persona usuaria. Son `JUP-069-009`, `JUP-069-024`, `JUP-071-004`, `JUP-071-005`, `JUP-071-006`, `JUP-071-007`, `JUP-071-008`, `JUP-071-011`, `JUP-071-012`, `JUP-071-014` y `JUP-071-016` (esta última no propone aportar una fuente de coste autorizada).

Tres fallos lo son solo por la comprobación numérica automática (`JUP-069-002`, `JUP-069-027` y `JUP-071-003`) con todos los puntos humanos en pass. Revisadas a mano, las cifras de las respuestas son correctas; es la limitación documentada del lector numérico de JUP-070, que exige una etiqueta concreta antes de la cifra (ver `openspec/findings/backlog.md`). Si se contaran como aciertos serían 10 de 24, pero esa no es la salida de la herramienta y no debe presentarse como tal.

Tres fallos lo son por ambas vías (`JUP-069-005`, `JUP-069-016` y `JUP-071-010`). `JUP-069-005` es una limitación conocida del chat: se abstiene en las preguntas de clasificación cuando el denominador elegible no viene como un total explícito (`CLASSIFICATION_ABSTENTIONS`; ver `docs/continuidad/chat-evaluacion-local.md`). No se modificó el banco ni la rúbrica durante la campaña para no alterar la comparabilidad.

### Recogida, reintentos y bloqueos

Las 29 conversaciones se generaron una por muestra, con el prompt exacto del plan, mediante un script fuera del repositorio y fuera del libro de contabilidad del equipo de JUP-123, por decisión de Lucía del 20/10/2026. No se acordó el reparto del presupuesto de inferencia con quien lidera la entrega B (tarea 6.5 sin cerrar).

Cuatro operaciones fallaron al primer intento (`JUP-069-008`, `JUP-071-008`, `JUP-071-009` y `JUP-071-014`). La API pública las etiqueta `provider_error`, pero los diagnósticos del processor muestran que el validador de salida del chat rechazó la respuesta del modelo (`invalid_response`: `classification_unverified_prose` en tres y `expression_incompatible_units` en una). No fueron fallos de infraestructura. `resume` solo admite operaciones en estado `paused`, así que se usó el reintento del producto (`retry_of_operation_id`, una operación nueva enlazada a la fallida con la misma pregunta), una sola vez por muestra. `JUP-071-008` y `JUP-071-014` completaron; `JUP-069-008` y `JUP-071-009` fallaron de nuevo con la misma regla. Los resultados de `JUP-071-008` y `JUP-071-014` son los del segundo intento, con el efecto de selección que eso implica. `JUP-071-004` tuvo dos intentos automáticos del propio chat tras una caída de la base de datos durante la generación y completó.

De las 27 respuestas completadas, 13 citaban el corpus sin que la API pública exponga la recuperación posterior al contexto inicial, y el colector las marcaba `INCOMPLETE`. Se reconstruyó esa recuperación desde la base de datos vectorial, con el hash del manifiesto de cada operación (`tool_result.content_sha256`) como única comprobación aceptada: 10 de las 13 coinciden byte a byte y se pasaron al colector con `--retrieval-snapshots`. Tres no coinciden (`JUP-069-003`, `JUP-069-010` y `JUP-071-013`); comparten el fragmento `b57a8db4-2132-4d5b-ada6-b825e08dd46f:chunk:9`, cuyo contenido no aparece literalmente en el texto del documento, y no se probaron más variantes: quedan bloqueadas.

Con esto se valida con un backend real, para la tarea 6.6, el contrato de evidencia sin distancia: las 10 muestras con citas exportaron 99 fragmentos con `distance: null` y el colector y el evaluador los aceptaron. Los hashes que informa el servidor salieron en minúscula en todas las muestras. Queda confirmar ese formato con quien responde de JUP-123.

### Dashboard

Las filas `rows-v1` están en el manifiesto versionado (`docs/validation/evaluation-runs.json`) como hito, por lo que se cargan con la carga normal del dashboard y no hace falta ningún manifiesto local. Cargadas así (6 ejecuciones y 405 resultados), el panel «Robustez (JUP-071)» devuelve 136 filas por la API de Grafana (117 de la campaña y 19 filas de indicadores), el panel «Indicadores de robustez (JUP-071)» devuelve las 19 filas de indicadores y la ejecución aparece como `no real: sin_modelo_verificado`.

```sh
corepack pnpm evaluation-dashboard:load
```

con la pila de Compose levantada y `GRAFANA_EVALUATION_DB_PASSWORD` definida como explica la guía del dashboard. La carga es idempotente y reemplaza los datos anteriores. El fichero de filas solo contiene identificadores, estados y números.

### Indicadores de la campaña (21/10/2026)

Las mismas filas incluyen ahora 19 filas de indicadores (18 indicadores) por las cuatro familias de evaluación de un RAG, generados con `rows --raw --receipts` (ver el protocolo). Los valores son provisionales por la misma razón que el informe.

| Familia | Indicador | Valor de `r1` |
| --- | --- | --- |
| Calidad del core | `invention_rate` | 0 de 55 (0 %) |
| | `required_coverage` | 30 de 46 (65,2 %) |
| | `behavior_match_rate` | 22 de 24 (91,7 %) |
| | `valid_citations` | 22 de 22 |
| | `literal_quotes` | 27 de 27 |
| Recuperación | `empty_retrieval_rate` | 0 de 24 |
| | `fragments_per_query` | 10,54 (253 fragmentos en 24 consultas) |
| | `neighbor_share` | 157 de 253 (62,1 %) |
| | `context_utilization` | 22 de 253 (8,7 %) |
| | `unused_retrieval_rate` | 14 de 24 (58,3 %) |
| Rendimiento | `completion_rate` | 27 de 29 (93,1 %) |
| | `unmeasured_by_cause` | 2 `operation_failed` y 3 `evidence_unverified` |
| | `cost_per_query` | 0,0065 USD (27 operaciones, informado por el servidor) |
| | `prompt_size_per_query`, `completion_size_per_query` | 17.411 y 1.354 |
| Conversación | `request_rate` | 3 de 15 (20 %) |
| | `over_abstention_rate` | 1 de 9 (11,1 %) |
| | `pair_degradation` | 3 de 6 (50 %) |

Todas las cifras coinciden con las calculadas a mano antes de implementar el cálculo, salvo `valid_citations` y `request_rate`, que se fijaron al conciliar. Las filas pasan el validador del dashboard de JUP-121. Se cargaron y se compararon los trece paneles del dashboard por la API de Grafana antes y después: solo cambia el panel de robustez (de 117 a 136 filas).

Dos cosas que se ven en estos números y que el equipo debería conocer. La recuperación se invoca en las 24 muestras verificadas, incluso cuando la pregunta trae todos los datos, y en 14 no se cita nada, de modo que solo el 8,7 % de los fragmentos recuperados se usa. Y el asistente nunca invierte ni cede ante la falta de datos (0 de 55), pero solo pide el dato que falta en el 20 % de los casos de aclaración o abstención.

### Límites de esta campaña

El modelo no está atestiguado por el contrato HTTP: la ejecución es `live_unverified`. El juicio lo dio una sola persona y no es independiente de quien coordinó la campaña, por lo que el informe es provisional y con cobertura reducida. Hay una sola repetición, así que no se mide estabilidad. Cinco muestras no se midieron. La reconstrucción de la recuperación se hizo con un script no versionado que reutiliza el código de citas del backend, de modo que esa parte solo es reproducible con acceso a la misma base de datos. Los 29 casos son una muestra pequeña: sirven para describir el comportamiento, no para garantías estadísticas.

## Trazabilidad por criterio de Trello

| Criterio original | Entrega / evidencia | Pendiente |
| --- | --- | --- |
| Resultado funcional verificable | Runner ejecutable, 29 casos emparejados, informes de plantilla, [protocolo](../validation/JUP-071-robustness.md) y una primera medición parcial con el chat real (r1, provisional) | Medición con modelo verificado, tres repeticiones y segunda revisión |
| Pruebas necesarias añadidas y en verde | `scripts/tests/test_assistant_robustness.py`, validación de la batería y las comprobaciones de arriba | CI del PR #136 en verde, revisión de Víctor y validación de Paris del instrumento; falta la validación de la tarjeta completa |
| Documentación y decisiones actualizadas | Protocolo, OpenSpec activo, esta evidencia y la continuidad | Cambios de procedencia cuando haya una medición real |
| Pull request revisado y vinculado | PR #136, fusionado el 2026-10-16: revisión de Víctor (aprobada sobre `5105d44a`) y validación de Paris (comentario sobre `8b02ab7e`). El PR #90 se cerró sin integrar | Ambas revisiones son del instrumento y la línea base offline, no de la tarjeta completa; falta todo el grupo 6 |
| Validación funcional y evidencia enlazadas | Informes sanitizados reproducibles y las verificaciones anteriores | La validación del instrumento la publicó Paris en el PR #136; no se atribuye ninguna ejecución a quien no la hizo |

## Historial de verificación

### 10/10/2026: contribución original (registro histórico)

Verificación del 10/10/2026, Europe/Paris, sobre la base `origin/develop` `c2995a118d419dfe725247bac9c6f219a3f0ea77`, en `test/JUP-071-robustness`. Las cifras de esta sección describen aquel corte y no el estado actual.

En aquel corte `AssistantService.answer` era una plantilla: JUP-035 estaba Preparado y su alcance exigía conectar el chat al modelo. Eso se leyó en el cliente desplegado (`DockerServer:/home/danteadmin/economicon-collaboration`) el 10/10 y no se ha vuelto a comprobar. Los roles de la tarjeta eran Paris liderazgo, Víctor pairing, Alejandro revisión y Lucía validación y documentación. La contribución técnica no acreditaba pairing ni sustituía los dictámenes, y Alejandro no puede revisar de forma independiente su propio código.

Verificaciones de entonces: 38 pruebas propias, 109 de JUP-070, 103 de métricas y 90 de Node OK; OpenSpec 56 items; `jup:check:all` con 9 cambios; trazabilidad e higiene correctas. `corepack pnpm test` y `build` global quedaron bloqueados por `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY` del pnpm fallback de Turbo, sin que eso acredite el conjunto del workspace. La CI remota del commit `d98d18d` dio SUCCESS en OpenSpec, JUP policy, los tres servicios Python, frontend build y type check, y `JUP reviews` en FAILURE por falta de dictámenes humanos. La nota de Trello `6ac9ebf65589a5a1741240c1` (10/10, 07:40:38Z) enlazó la entrega sin mover la tarjeta ni completar criterios.

Crudos y hoja de revisión del 10/10 quedaron fuera de Git (`../materiales/07-evidencias/JUP-071-robustness-2026-10-10/`), con los juicios vacíos. Los informes versionados no contienen respuestas, claves ni nombres de revisores.

### 13/10/2026: cabecera `run` y repetición de la plantilla

El informe incorpora un bloque `run` con los nombres de la cabecera de JUP-070 (`run_id`, `commit`, `date`, `provider`, `alias`, `suite_version`, `suite_sha256`, `generation`). En una ejecución con plantilla declara `provider` `template`, `alias` `none` y `plantilla-sin-modelo`. En una recogida HTTP toma esos campos de la configuración declarada, los valida con un patrón restringido y no acredita por ello que un modelo respondiera. Los campos anteriores se mantienen y no cambia ningún resultado ni denominador. El bloque prepara el dashboard de JUP-121, que hará la normalización posterior; el informe sigue sin afirmar compatibilidad con el catálogo de JUP-067.

Los crudos del 10/10 no estaban disponibles, así que los dos informes se sustituyeron por una repetición offline con el código de entonces, con el mismo resultado: 0 aciertos, 8 fallos y 21 pendientes de 29.

### 13/10/2026: primera recogida HTTP contra un servidor real

Stack local en modo mock con la rama (commit `7943b97`), corpus de `tenant-core` con 52 fragmentos y embeddings mock, y `AssistantService` en su versión de plantilla. Es una recogida contra el endpoint de mensajes con la plantilla: no hay modelo, no hay gasto y no prueba robustez generativa. 29 de 29 casos respondidos sin fallos de infraestructura, con citas y fragmentos, latencia total entre 737 y 1653 ms (mediana 1183). La puntuación sin juicios fue idéntica caso por caso a la de la plantilla offline con recuperación fija. El informe declaró `live_unverified` y `model_execution_verified` falso, y la contraseña de la demo no apareció en ningún fichero generado. Los artefactos están fuera de Git y no se han vuelto a comprobar.

### 15/10/2026: integración con `develop`

`develop` incorporó #130 (entrega A del chat, `cf821570`, con `CHAT_ENABLED=false` por defecto), #127 (datos de demo), #128 (explicación de anomalías), #129 (corpus del asistente con los episodios de anomalía) y #69 (consultas de gasto). Se integró en la rama con un merge y cuatro conflictos de documentación y CI; `develop` retiró `synthetic-costs:test` y la rama conserva solo las dos entradas de robustez.

El banco de JUP-069 pasó a `1.0.1` y cambiaron los hashes de la metodología de JUP-070 y de dos fuentes del corpus. Las preguntas y las rúbricas del banco no cambiaron. Se comprobó que la regla de anomalía diaria que usa la variante JUP-071-014 (`relative_delta > 20 %` y `absolute_delta > 100 EUR/day`) sigue igual en el corpus nuevo, y se actualizaron las referencias de la batería. La batería propia conserva su versión `1.0.0`. El corpus pasó a 66 fragmentos. El chat generativo de #130 sigue sin medirse: se sirve por `/generations` y el colector de esta rama usa `/messages`, que sigue respondiendo con la plantilla incluso con el chat desactivado.

### 16/10/2026: colector de JUP-123 (PR #131) con nuestra herramienta

Prueba de extremo a extremo sin coste: stack local aislado con el código del #131, `CHAT_ENABLED=true`, `LLM_PROVIDER=mock`, corpus de `tenant-core` con 66 fragmentos y el backend de `develop` con #130. Se generaron tres operaciones por `POST /generations` (`JUP-069-002`, `JUP-071-001` y `JUP-071-002`, repetición 1) y se leyeron con el colector usando esta rama como suite. La prueba se hizo dos veces: primero con la cabeza `5cae4942` del #131 y la suite `568734f2`, y de nuevo con la cabeza `af8388d0` (que añadió el bloqueo de filas con corpus sin distancia) y la suite `44c1032e`, con el mismo resultado.

El modelo simulado devuelve siempre la misma respuesta de 82 caracteres (`insufficient_data`) sin evidencias, así que no se ejercitaron citas ni recuperación reales y no hay calidad que valorar. Resultado: las tres operaciones quedaron `VERIFIED_PUBLIC_SNAPSHOT` con pregunta, instantánea estable, paridad con el historial y citas conocidas en verdadero. En el log del backend el colector solo hizo GET; los POST fueron los del script que generó las operaciones. La exportación de la repetición 1, `review-sheet` y `score` funcionaron con las herramientas sin parchear: 3 filas de 29, las demás `not_run` por `missing_response`, 0 aciertos, 2 fallos numéricos y 27 pendientes, `live_unverified` y `model_execution_verified` falso. Reexportar produce bytes idénticos y no se encontró la contraseña ni el token en ninguno de los 15 ficheros generados.

La primera exportación falló: el `run-info` de seis cadenas del colector no era válido para el bloque `run` (commit de 40 hexadecimales y `generation` como objeto). La cabecera pasó a aceptar un commit declarado de 7 a 40 hexadecimales y `generation` como cadena. El adaptador fija el commit y los hashes de la suite en su plan, de modo que cambiar la herramienta obliga a preparar otro plan y a volver a leer los recibos. Los artefactos de esta prueba están fuera de Git: las cifras de esta sección (latencias, número de ficheros revisados) las declara quien ejecutó la prueba y no se pueden verificar desde el repositorio.

No se probó el chat con un proveedor real, ni la lectura de evidencias y citas reales, ni más de tres muestras. Con evidencias de corpus del chat real, la cabeza `af8388d0` del colector bloqueaba las filas por falta de `distance`; la actual (`e0a0c41e`) exporta la distancia nula y esta herramienta la acepta, pero solo se comprobó con una fila construida con su forma, no con un backend real: tarea 6.6.

### 16/10/2026: revisión final

La rama pasó siete pasadas adversariales automatizadas y dos auditorías de coherencia: las pasadas 1, 2 y 6 y las auditorías dieron `changes-required` y se corrigieron; las pasadas 3, 4, 5 y 7 dieron `accept` con hallazgos MEDIUM y LOW que se corrigieron o se registraron. El detalle de cada hallazgo y su resolución está en `review.md` del change. Los arreglos de la última auditoría documental no se revisaron de nuevo. Ninguna de esas revisiones es la `Revision JUP-071` ni la `Validacion JUP-071` de una persona.

## Límites

La separación `template_mock`/`live_unverified` es deliberada: el endpoint no atestigua generación y el informe no distingue una plantilla servida por HTTP de un runtime desconocido más que por lo que declara el operador. La evaluación semántica sigue dependiendo de personas; las comprobaciones numéricas son las de JUP-070 con sus limitaciones documentadas (solo se mira la etiqueta anterior a la cifra: un `fail` numérico se revisa a mano antes de atribuirlo al asistente). No se afirma cobertura completa de ambigüedad, relevancia de retrieval, latencia ni ausencia de alucinación.

Siguiente paso: segunda revisión independiente de los puntos juzgados, las otras dos repeticiones con la misma batería y configuración (tarea 6.3), acordar con quien lidera JUP-123 el reparto del presupuesto de inferencia y cómo se puntúan las respuestas con citas del chat real (6.5), y revisión y validación de personas de la tarjeta completa (6.4). El PR #136 ya integró el instrumento; el cierre de la tarjeta requiere además lo anterior y la evidencia enlazada por quien lidera.
