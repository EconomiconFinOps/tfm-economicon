# JUP-025 — Citas documentales

- Tarjeta: https://trello.com/c/qzRy4RQc
- Base contrastada: `origin/develop`, `2efef1a`, 30/09/2026.
- Rama: `feat/JUP-025-source-citations`.
- PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/55
- Contrato y escenarios: [OpenSpec](https://github.com/EconomiconFinOps/tfm-economicon/tree/17c8514d8ef4d4da583f878b6fc19b968ef2ca82/openspec/changes/jup-025-answer-citations/).

## Resultado

El chat conserva los IDs existentes y agrega una instantanea de cada fuente
utilizada. Los tres extractos citados enlazan al documento, fuente, referencia
estable, seccion disponible y evidencia expandible. El cuarto resultado de
retrieval ya no se presenta como evidencia utilizada. Reabrir una conversacion
conserva las citas. Los IDs inexistentes, repetidos o ajenos al tenant impiden
guardar una respuesta del asistente; la respuesta de error no contiene esos IDs.

Las referencias no son URLs de descarga. No se exponen URIs de artefactos ni
parametros de acceso. El enlace abre el extracto historico guardado en el mensaje.
La autorizacion de lectura sigue siendo la de la conversacion y su propietario.

## Validacion ejecutada

Entorno local: Windows, Python 3.14, dependencias del lockfile sin cambios.

| Comprobacion | Resultado |
| --- | --- |
| Backend completo | 336 pruebas aprobadas; 10 opt-in omitidas en esa ejecucion |
| Pgvector real aislado | 3 aprobadas: tenant A, tenant B y tenant sin documentos |
| Regresion JUP-024, `test_agent_runtime.py` | 16 aprobadas, sin modificar el contrato |
| Frontend completo con `--maxWorkers=1` | 267 aprobadas, 47 archivos |
| Ajuste final de enlace exacto a evidencia | 7 pruebas focalizadas aprobadas, incluida pregunta con marcador falso |
| Typecheck, build y lint de componentes nuevos | Correctos |
| OpenSpec estricto | 35/35 |
| Trazabilidad JUP y diff check | Correctos |

La primera ejecucion paralela del frontend tuvo ocho fallos de espera bajo carga;
la misma suite paso con un unico worker sin modificar los timeouts ni las pruebas
existentes. Posteriormente se agrego la prueba del marcador falso y se ejecuto la
suite focalizada. No se presenta 267 como el recuento final de todos los tests.
Persisten avisos de deprecacion de dependencias Python y tamano del bundle Vite.

Pgvector se ejecuto en un contenedor efimero separado en DockerServer, con puerto
loopback 55425, almacenamiento tmpfs y credenciales sinteticas. Se reutilizo la
fixture que verifica una base vacia, crea bases de prueba y las elimina. No se
utilizo ni modifico la base desplegada por JUP-021 o la PR #53.

## Comprobacion visual

Playwright abrio la aplicacion Vite en Chromium con respuestas API sinteticas:
click en `[1]`, evidencia visible, recarga de conversacion y vistas de escritorio
(1360 px) y movil (390 px). No hay enlaces externos en el panel de fuentes.
La persistencia real del mensaje se comprueba por separado en las pruebas API,
no mediante las respuestas sinteticas de navegador.

Capturas locales: `materiales/07-evidencias/JUP-025-citas-2026-09-30/`, fuera del
repositorio. Las citas se adaptan al ancho movil; la cabecera y navegacion global
ya desbordan ese ancho y no forman parte de este cambio.

## Limites y participacion

- La ingesta actual no conserva paginas PDF. `page` queda null; no se inventa.
- Se recupera seccion de Markdown original solo con coincidencia unica del chunk.
- Los mensajes historicos con solo IDs indican que la evidencia no esta disponible.
- FinOpsResponse 1.0 pertenece al processor; este chat sigue usando extractos
  deterministas. No se acredita conexion a LLM, calculo de metricas ni ejecucion
  de recomendaciones. Sus guardrails y evidence_ids permanecen intactos.
- Liderazgo: Alejandro Aguado. Pairing: Paris Arcos Martin. Revision: Lucia Mateo.
  Validacion: Victor Mendez. Son asignaciones de Trello, no aprobaciones humanas.
- Estado histórico de esta medición: revisión y validación pendientes; véase la actualización del 02/10/2026 al final.


## Correcciones de la revision — 01/10/2026

[Revision de Lucia](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5369995407)
sobre `1f28d42`: los tres problemas se reprodujeron antes de corregirlos.

- Encabezados vacios con espacios o CRLF ya no generan texto en blanco: se usa
  source como titulo y seccion null. Dos regresiones API confirman 201 y cita valida.
- Un indice de ubicaciones por documento normaliza texto en una pasada e ignora
  bloques cercados con backticks/tildes, codigo indentado y front matter YAML inicial.
  Las cercas sin cerrar se tratan conservadoramente como codigo. C# se conserva;
  solo se retiran hashes de cierre precedidos de espacio.
- La consulta de vecinos no trae texto completo. Una segunda consulta autorizada
  obtiene cada documento una sola vez; ambas usan la misma transaccion REPEATABLE
  READ. Las pruebas reales verifican cuatro chunks/un indice y una reingesta entre
  las dos consultas sin mezclar versiones.
- El source se recorta igual en el pasaje y en la cita, restaurando su enlace.
- La tarea tecnica 2.5 registra el traspaso del pendiente humano a Trello. No se
  acredita aprobacion, validacion funcional del equipo ni cierre de tarjeta.
- Se registra [RF-025-001](../../openspec/findings/backlog.md): un fallo 502 deja
  persistido el mensaje de usuario y un reintento lo duplica. Sigue abierto, como
  solicito la review; no se ha cambiado el contrato de reintentos ni persistencia.

Medicion local reproducible: documento de 400.780 caracteres, 1.000 encabezados y
cuatro fragmentos finales. Antes: 7,34 s. Despues: 0,0113 s para indexacion y cuatro
busquedas. Es una medicion del procesamiento local, no una promesa de latencia
HTTP. La prueba automatizada exige menos de 1,5 s con margen para CI.

Validacion de esta correccion:

- Backend completo: 353 PASS, 14 SKIP de servicios opt-in.
- Pgvector real efimero separado: 5 PASS, incluidas lectura unica y reingesta.
- Frontend focalizado de citas/conversaciones: 14 PASS. Sin cambios de frontend.
- OpenSpec estricto 35/35, trazabilidad y diff check correctos.

Comandos: `python -m pytest apps/backend/tests -q`; `python -m pytest
apps/backend/tests/test_tenant_isolation_vector.py -q` con la variable de conexion
sintetica `JUP086_VECTOR_TEST_URL`; `corepack pnpm --filter @finops/frontend test --
src/components/AnswerEvidence.test.tsx src/pages/ConversationsPage.test.tsx
tests/conversations.test.tsx --maxWorkers=1`. Python usa `PYTHONPATH=apps/backend`.


## Correcciones de la validación — 02/10/2026

[Víctor](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5385253656)
validó funcionalmente el HEAD `17c8514` tras la
[aprobación de Lucía](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5381249566).
Esta corrección conserva ese trabajo y atiende sus observaciones:

- Al activar una cita se cancela la navegación al fragmento antes de abrir el panel
  y enfocar su resumen; se evita que la navegación quite el foco o añada historial.
  La prueba exige cancelación del evento, panel abierto y foco en su resumen.
- Un chunk superior a 140 caracteres comprueba el recorte exacto de la evidencia y
  su igualdad con el pasaje generado, condición necesaria para crear el enlace.
- Las referencias al contrato usan el commit verificado `17c8514`, una URL estable
  que seguirá disponible al mover el change a `archive/`. No se archiva antes de
  completar la revisión.

Validación focalizada: backend `test_citations.py` 27 PASS; interfaz de citas y
conversaciones 14 PASS; lint y typecheck correctos; OpenSpec estricto 36/36 y
trazabilidad JUP-025 correctos. Se usan los comandos documentados arriba con
`PYTHONPATH=apps/backend`. No se repite la prueba de pgvector: esta corrección no
modifica recuperación ni persistencia. La validación funcional de Víctor queda
acreditada en su revisión, y la aceptación de estas correcciones queda pendiente.


La observación documental se separa en [JUP-101](https://trello.com/c/ReMOdXEK) y
[PR #64](https://github.com/EconomiconFinOps/tfm-economicon/pull/64), borrador para
acordar una convención común. PR #55 retira del diff el índice, el resumen y la
referencia añadida a AGENTS.md; se conservan en la propuesta documental y en el
workspace. Los conflictos futuros de #60/#61/#62 se resuelven al integrar esa
convención, conservando todos los temas; no se dan por resueltos aquí.

Comprobación por mutación: el test nuevo falla si el extracto se amplía a 200 o
el pasaje se reduce a 120. El test de interfaz falla al retirar preventDefault.
Restaurado el código, controles backend 27/27 e interfaz de evidencia 7/7 verdes.


Actualización de base del 02/10: se integra develop `5a54ce2`, que incorpora
JUP-099 y JUP-096. Se resuelve el conflicto de ConversationsPage conservando
AnswerEvidence y los tokens del tema, y el del backlog conservando ambos grupos
de incidencias. AnswerEvidence adopta los tokens existentes del tema.
Validación tras integración: 188 pruebas de citas/conversaciones y guardas de
paleta aprobadas; typecheck correcto; OpenSpec 37/37. No cambia el contrato backend.


## Reconciliación con JUP-022 integrada — 04/10/2026

PR #67 se integra en develop como `c3aa9d68690ae718aecf1bee2f08cd25eb5f704f`
a las 15:12:45 UTC. Se prepara localmente el merge desde HEAD remoto de #55
`e24e194747809553d0624d037989ce7170db41b9`. Se resuelven los conflictos de
`assistant.py`, `vector_store.py` y `openspec/findings/backlog.md`.

- La ruta conserva la selección del proveedor, la verificación del vector,
  top_k/umbral/proveedor configurados, los 503 saneados y los eventos/métricas
  de JUP-022. Valida el tenant antes de emitir identificadores en el evento,
  resuelve solo las referencias utilizadas y guarda `source_citations`.
- La consulta conserva filtro tenant/proveedor, umbral inclusivo antes de LIMIT
  y orden distancia/ID. Obtiene tenant e índice del chunk, carga cada documento
  una vez y calcula título/sección sobre el mismo snapshot REPEATABLE READ.
- El backlog conserva todas las filas originales de las dos ramas. Los dobles
  de JUP-022 incorporan la metadata documental y la segunda consulta de JUP-025;
  las aserciones de filtros, orden, logs y errores siguen vigentes.
- La regresión nueva en `test_retrieval_contract_pgvector.py` une consulta real y
  ruta: excluye un vector de proveedor obsoleto y otro tenant, limita a un chunk
  y comprueba su cita, título, sección, referencia, extracto y contexto público.

Comprobaciones propias sobre el candidato, sin sustituir review/validación humana:

| Comprobación | Resultado |
| --- | --- |
| Backend completo, Python 3.12.13 y pgvector desechable | 628 PASS / 16 SKIP, 96,74 s |
| Backend focalizado local, Python 3.14 | 119 PASS / 2 SKIP |
| AnswerEvidence y conversaciones, maxWorkers=1 | 13 PASS |
| Frontend tsc --noEmit | Correcto |
| OpenSpec estricto | 45/45 |
| Trazabilidad global e higiene | Correctas, 826 archivos |
| Tests de política PR / CI / gobernanza | 57 / 10 / 13 PASS |
| git diff --check y conservación de filas backlog | Correctos |

El backend se ejecuta copiando `apps/backend` y `apps/processor` al contenedor de
pruebas Python 3.12, con requirements-dev del candidato, en la red de un pgvector
propio sin puertos publicados, sin volumen persistente y solo loopback interno
55432. Comando desde apps/backend: `python -m pytest tests -q --tb=short`, con
`JUP086_VECTOR_TEST_URL` del recurso desechable. No se guardan claves en la evidencia.

No se repiten navegador, Compose completo, CockroachDB/RabbitMQ reales, modelos
externos ni calibración de relevancia. Los 16 SKIP no cuentan como validación.
La primera ejecución focalizada detectó dobles JUP-022 incompatibles con la metadata
adicional y el snapshot; se adaptaron los fixtures sin retirar sus verificaciones.
El primer intento del contenedor carecía de httpx; se instalaron requirements-dev
antes de la ejecución completa correcta. No se atribuye pairing a Paris.

Reconciliación publicada en `d09f16a0f373dc5ca9df016453d1cd6be00ad49f`.
CI 37214915405 correcta: siete checks técnicos.
[Víctor validó favorablemente este SHA](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5407281630)
el 04/10/2026, como COMMENTED porque en ese momento faltaba la revisión incremental de Lucía.
Su Compose/navegador/mutantes son evidencia del validador, no ejecuciones propias
del líder. El cierre de archivo y la nota posterior de Paris se describen en el
apartado vigente del 06/10; las aprobaciones antiguas no se atribuyen al HEAD final.


## Mejoras para el archivo — 04/10/2026

Atendidas las notas no bloqueantes de la validación de Víctor sobre d09f16a:
se comprueba la referencia completa de chunks con índice distinto de cero en
la prueba de recuperación documental; RF-025-001 registra también el mensaje
sin respuesta y la duplicación al reintentar un 503 de recuperación; la evidencia
identifica la reconciliación publicada y distingue resultados propios y del validador.
La representación cruda del error 503 es un límite heredado de RF-098-003 y no se
cambia aquí. La implementación de citas/recuperación permanece igual a d09f16a.

El archivo se preparó localmente el 04/10, con especificación canónica
`openspec/specs/answer-citations/spec.md`. Su cierre y la aportación documental
posterior de Paris se describen en el apartado vigente del 06/10. #69 (JUP-036) sigue abierta y comparte
ruta, esquema de mensajes e interfaz: quien integre segundo debe reconciliar y
revalidar los contratos, sin incorporar preventivamente su borrador en esta rama.


Verificación propia del candidato de archivo: citas y las dos suites de pgvector
real **44 PASS** con Python 3.12.13 y base desechable; el mutante que fija
`chunk_index` a cero falla en la nueva aserción `document:own/chunk:1`. Restaurado
el fichero, el control pasa. Script de mutación conservado solo en continuidad
local, sin modificar el producto ni incluir utilidades personales en la PR.
OpenSpec estricto **45/45**, trazabilidad global e higiene correctas. No se repite
la suite completa, ya acreditada en d09f16a; este candidato solo cambia test y
documentación/especificación, sin cambios en `apps/backend/app`.

Archivo preparado en
[2026-10-04-jup-025-answer-citations](../../openspec/changes/archive/2026-10-04-jup-025-answer-citations/proposal.md)
y [contrato canónico](../../openspec/specs/answer-citations/spec.md).
Los enlaces anteriores fijados a 17c8514 conservan el contrato histórico revisado.
La revisión de Lucía y la aceptación del HEAD que publique el archivo siguen
pendientes; el COMMENTED favorable de Víctor acredita d09f16a, no este candidato.


### Revisión incremental de Lucía y finding fuera de alcance

[Lucía aprobó d09f16a](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5407419137)
el 04/10/2026 a las 17:54:50 UTC (19:54:50 Europe/Paris), después de la
validación favorable COMMENTED de Víctor sobre ese mismo SHA. Su dictamen
incluye recuperación/snapshot/tenant, mutantes, backend con pgvector real,
interfaz y smoke real. Son ejecuciones de la revisora, no propias del líder.
No hay cambios bloqueantes pedidos ni solicitudes de review pendientes en d09f16a.

Registrado **RF-025-002**, fuera de alcance, por petición explícita de Lucía:
el 502 de validate_context no emite diagnóstico propio ni contador de fallo
retrieval; acordar categoría limitada y log saneado en una tarjeta futura.
No se cambia el runtime ni se debilita la protección de tenant; la falta de
telemetría se distingue del rechazo de evidencia, que sí funciona.

Los dos dictámenes favorables acreditan la reconciliación publicada d09f16a.
No se atribuyen al candidato de archivo: su publicación requiere CI y dictámenes
incrementales del delta. La nota de Paris del 06/10 acredita la aportación
documental indicada abajo; no se modifica autoría histórica. Este archivo no
autoriza merge ni cierre de Trello.


## Cierre para revisión final — 06/10/2026

La rama reúne el archivo preparado, las mejoras de test/findings y el HEAD de
PR #55 `2271b7042949a5b3b0cd6ebde416585ea8d0c05a`, más develop
`0488372` (#70, archivo documental JUP-023). Las incorporaciones de #58/#71
son de CI y documentación. Se conservan íntegramente los cambios de develop y
no hay delta en código de producción backend/processor/frontend respecto a
la reconciliación `d09f16a`; no se incorporan cambios del borrador #69.

El change de citas queda archivado en `2026-10-04-jup-025-answer-citations`,
fecha de su preparación, con los cinco requisitos promovidos a
`openspec/specs/answer-citations/spec.md`. Los enlaces nuevos son relativos al
archivo/contrato canónico; los enlaces históricos a 17c8514 siguen siendo inmutables.

### Participación acreditada

- Liderazgo: Alejandro Aguado, implementación, resolución y cierre de evidencia.
- Pairing/coautoría: Paris Arcos Martin, aportación documental descrita en su nota.
- Revisión: Lucía Mateo, dictamen técnico sobre d09f16a y delta final pendiente.
- Validación: Víctor Mendez, dictamen funcional sobre d09f16a y delta final pendiente.

La nota **«Aportación de pairing»** de Paris en
[JUP-025](https://trello.com/c/qzRy4RQc), comentario `6ac4d3d31570eab97990d1a2`,
fue publicada el 06/10 a las 10:56:19 UTC (12:56:19 Europe/Paris). Leyó título,
fuente, sección, extracto y referencia de las citas, el enlace al detalle de evidencia
y la localización del pasaje en el corpus, y dio conformidad sin ajustes. Esta
aportación se acredita mediante la nota aceptada por el acuerdo operativo del
usuario. No se le atribuyen commits, pruebas ni una sesión conjunta. La regresión
processor->pgvector->backend propuesta anteriormente no se declara ejecutada
ni se exige como requisito adicional para esta acreditación.

Los resultados propios **44 PASS y mutante detectado** corresponden al candidato
probado el 04/10; sus tres ficheros de tests y el runtime permanecen iguales tras
las actualizaciones documentales. No se repiten baterías sin un cambio funcional.
Los controles nuevos del 06/10 se registran a continuación; la CI del último SHA
se verifica en GitHub. Las revisiones humanas de d09f16a no se presentan como
aceptación de este delta: se solicita revisión incremental de archivo, índice
no nulo, findings, enlaces y evidencia, y validación de lo afectado sobre el SHA final.
No se autoriza merge ni movimiento a Hecho desde esta evidencia.


Controles de cierre ejecutados el 06/10: OpenSpec estricto **46/46**,
trazabilidad global e higiene (**830 archivos**) correctas; tests de política PR
**57/57**, CI **12/12** y gobernanza **13/13**. Comparación exacta: runtime
backend/processor/frontend sin delta desde d09f16a, tres ficheros focalizados de
citas/pgvector sin delta desde el candidato probado; cinco requisitos archivados
promovidos sin pérdida (normalizando líneas vacías del archivador) y tres enlaces
locales nuevos válidos. Se conservan todas las filas del backlog de develop.
`git diff --check` del delta propio correcto. La línea vacía final de la spec
canónica de citas generada por el archivador se retira; repository-governance,
procedente de #58/base, permanece sin cambios propios.


## Reconciliación del backlog tras #74 — 06/10/2026

[Lucía publicó revisión incremental favorable de f0a5d38](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5431451872),
como COMMENTED y sin cambios bloqueantes; falta la validación final de Víctor.
Sus ejecuciones propias de 44 tests pgvector, 628/16 backend y 451 frontend
pertenecen a ese dictamen, no a una nueva ejecución del líder.

Se incorpora develop `f0cacdd` (#74, métricas técnicas) y se resuelve su único
conflicto en `openspec/findings/backlog.md`, conservando literalmente todas las
filas de ambas ramas: RF-025-001/002 y RF-067-001..004 aparecen una vez cada una.
Los ficheros de #74 quedan íntegros; no se modifica runtime ni los tests de producto.
El cierre de archivo y la nota real de Paris en Trello permanecen como estaban.

La relectura de Lucía se solicita solo sobre la unión del backlog y la validación
de Víctor sobre el HEAD resultante, con aceptación incremental del cierre de
archivo/evidencia ya entregado. Se ejecutan controles documentales/política/CI
incluyendo las herramientas de métricas nuevas; no se repiten suites de producto
ni se transfieren los dictámenes anteriores al SHA que publica esta reconciliación.


Controles proporcionales de esta reconciliación: OpenSpec **47/47**, trazabilidad
e higiene correctas; comandos de tests de política PR, CI y gobernanza correctos;
calculador documental de métricas de #74 **103 tests correctos** en Python3.14.
No se ejecutan nuevas suites de producto. Se comprueba conservación literal de
filas de los dos padres y unicidad de las seis incidencias RF-025/RF-067.
Las solicitudes finales se refieren al SHA de esta unión documental, no al anterior.


## Reconciliación documental tras #75 — 07/10/2026

Se incorpora develop `b3716f7` (JUP-103/#75) para que Víctor pueda validar #55.
Único conflicto: `openspec/findings/backlog.md`. La unión conserva todos los IDs,
sin duplicados, con RF-025-001/002, RF-067-001..004 y las cinco RF-103 nuevas.
Se respetan además las actualizaciones intencionales de filas existentes hechas
por develop; no se restauran versiones antiguas ni se duplica un ID para conservar
su historia. Los demás documentos y specs de #75 se incorporan sin cambios propios.
No hay delta de apps/, workflow, herramientas ni package.json desde 102768a.
La revisión favorable de Lucía sobre ese SHA permanece como evidencia previa;
se pide relectura solo de la reconciliación documental y validación de Víctor
sobre el último HEAD, sin nuevas suites de producto.

El mensaje Discord «PR #63 (JUP-025): Validada» mezcla identificadores: #63 es
JUP-065 (Preparar demo funcional reproducible). No se usa como validación de #55;
en GitHub no hay un dictamen final nuevo de Víctor para #55 en este corte.
Archivo de citas y aportación documental real de Paris siguen entregados.

Filas finales: 68. Actualizaciones de develop preservadas: RF-093-001, RF-098-004.

Controles del 07/10: OpenSpec48/48, trazabilidad global correcta, higiene851archivos;
políticaPR57/57, CI12/12 y gobernanza13/13, todos con exit0. Delta propio
contra develop limpio. La línea vacía final de workspace-task-pipeline/spec.md
es heredada de #75 y no se modifica en JUP-025. Sin nuevas suites de producto.
