# JUP-071 — Evidencia de robustez

[Tarjeta](https://trello.com/c/H0woDubz). Última actualización: 16/10/2026. Esta evidencia describe el instrumento, la batería y las líneas base. No contiene ninguna medición de un modelo real ni ningún dictamen humano.

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
| `corepack pnpm assistant-robustness:test` | 128 pruebas OK (123 hasta el PR #136 y 5 de la capa de informe después) |
| Pruebas de JUP-070 y de métricas de JUP-067 | 110 y 103 OK |
| `node --test tools/ci-workflow.test.mjs` | 14 OK (con las dependencias del repositorio principal enlazadas temporalmente) |
| `corepack pnpm openspec:validate`, `jup:check` del change y `jup:cleanup:check` | 74/74, OK, OK |

### 16/10/2026: distancia no medida y contrato del dashboard (tareas 4.4 y 4.5)

La herramienta acepta fragmentos con `distance: null` y `public_evidence`, y expone `ACCEPTS_UNMEASURED_DISTANCE`. El comando `rows` emite el informe como `rows-v1`: se generaron `JUP-071-template-fixed-rows.json` y `JUP-071-template-empty-rows.json` y el validador de las cabezas `e4b403d4` y `b6695100` del PR #132 de JUP-121 los acepta (código de salida 0). Una pasada adversarial automatizada (1 HIGH, 4 MEDIUM, 6 LOW) llevó a validar el informe antes de emitir, a marcar las dos tasas como no medidas sin casos evaluados, a copiar proveedor y alias, a dejar nulo el modelo no verificado y a endurecer `public_evidence`. Después, la guía del dashboard (cabeza `b6695100`) fijó que la cobertura reducida va como juicio humano y pidió el desglose por tipo de perturbación, y ambos se aplicaron. Quedan 123 pruebas en verde. Los nombres de grupo y métrica y el lugar donde se muestran siguen pendientes de confirmar con quien mantiene el dashboard (la clasificación `human`/`automatic` ya la fija su guía).

### 16/10/2026: procedencia del servidor (tarea 4.6)

Con la cabeza `e0a0c41e` del PR #131, el colector copia a `execution.collection.server_reported` la procedencia que reporta el servidor. El informe y `rows` llevan el `prompt_sha256` único como dato no atestiguado, y `mixed` o `absent` si no hay uno. Se comprobó con una fila construida con la forma exacta del colector (no se repitió con un backend real). 123 pruebas en verde (el conjunto actual).

## Trazabilidad por criterio de Trello

| Criterio original | Entrega / evidencia | Pendiente |
| --- | --- | --- |
| Resultado funcional verificable | Runner ejecutable, 29 casos emparejados, informes de plantilla y [protocolo](../validation/JUP-071-robustness.md) | Medición con un modelo real |
| Pruebas necesarias añadidas y en verde | `scripts/tests/test_assistant_robustness.py`, validación de la batería y las comprobaciones de arriba | CI al publicar y validación independiente |
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

Siguiente paso: revisión y validación humanas; acordar con quien lidera JUP-123 cómo se puntúan las respuestas con citas del chat real; con el chat activado con un modelo, un presupuesto acordado y juicios humanos, tres campañas iguales con el colector de JUP-123. El cierre requiere además un PR revisado e integrado y la evidencia enlazada por quien lidera.
