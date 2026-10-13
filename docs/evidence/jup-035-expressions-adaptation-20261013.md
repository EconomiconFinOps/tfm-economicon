# JUP-035: adaptacion local de expresiones y citas

Fecha: 2026-10-13. Estado: implementacion local preparada; los cuatro focales
corregidos cumplen el criterio MVP aprobado. No es validacion humana, CI remota
ni autorizacion de publicacion.

## Cierre focal posterior: criterio MVP

Paris aclaro que el MVP requiere respuestas coherentes con la documentacion y
sin datos inventados, no una redaccion exacta. Se retiro el filtro lexical que
rechazaba incluso colores correctos y se simplifico el prompt. Una contradiccion
real sigue invalidando la aceptacion funcional; no se afirma un verificador
semantico general. Se conservan aritmetica, aislamiento, fuentes autorizadas,
pasajes literales y controles de evidencia financiera.

La ronda final uso una recuperacion y una generacion por caso, 6400 tokens de
salida y las mismas condiciones del proveedor. El intento historico truncado
de 006 consumio exactamente 3200 tokens de salida y termino con length; este
dato justifica el aumento solo del chat, no de ingesta ni resumen.

| Caso | Resultado revisado de la ronda final |
| --- | --- |
| 005 | 700 + 200 + 100 = 1000 EUR elegibles; excluded fuera; 10 %, amarillo; formula y bandas citadas. |
| 006 | 50 / 1000 = 5 %, verde; formula y limite inclusivo citados; sin truncacion ni rechazo. |
| 007 | 101 / 1000 = 10,1 %, rojo; clasificacion antes de redondear y fuentes pertinentes. |
| 012 | Falta de owner no implica unallocated si costcenter identifica al equipo; distingue tagging y asignacion y cita definiciones y politica. |

Los cuatro completaron en un intento, sin duplicados y con dos mensajes cada
uno. El texto capturado del SSE real coincide exactamente con el resultado;
contenido y metadatos coinciden con el historial. 005/006 se reabrieron en
navegador y conservan fuentes pequenas debajo, sin mostrar chunk_id.
012 conserva un detalle menor de puntuacion entre segmentos (allocated.En);
no altera el significado y no bloquea el criterio MVP. No se repitieron las 28.

Red nuevo: cinco fallos esperados contra el filtro anterior. Green: 88 pruebas
focales de processor y 19 de backend. Se conservan las mutaciones y regresiones
anteriores, los fallos reales y los recibos negativos; no se suman suites
solapadas como pruebas unicas. Se mantienen las omisiones historicas descritas.

Imagenes probadas:
- Backend: sha256:a4152a2f353ae4d90602142d46c6a69ede792cfff2e96565bb0d936bb08290e7.
- Processor: sha256:3a4544761f6ade603795b200a2da258a298645a5c90f5b833adfc557504c9ef6.
- Prompt: jup-035.chat.v3:da6956edb67aa5fec7eadba0a8540ff13f161fb7e440bbfacda93e18b31e8383.
- System SHA256: 6e318cd584d0071b0437271c461f05eae6bb21c205eeffb34e0b2cf6edbad9ac.
- Assembler SHA256: f8a6d36420ebacc4d2c356730c5b4dd8762652f0c05ce44c718af7fe9910d703.

Gasto adicional asentado de la ronda: **0,083706085 USD de 0,12 USD**,
incluidos intentos previos fallidos y embeddings. No se ampliaron topes ni
caducidades en este cierre. Recibos: focal/classification-mvp-final-actual/,
classification-mvp-settled-budget, classification-mvp-red,
classification-mvp-green-valid, classification-mvp-backend-valid,
classification-mvp-image-build y capturas classification-mvp-005/006.png,
en el directorio externo de evidencias previamente documentado.
HEAD sigue a55bb304b8f2a199049134f902146b3f981727be, con cambios locales sin
commit/push. La rama y PR de Alejandro no se modificaron.

Los cortes inferiores son historicos, no el estado actual de estos cuatro casos.

## Actualizacion focal: 13/10, 16:42 Atlantic/Canary

Este corte sustituye el estado operativo de las tablas historicas inferiores,
que se conservan para no borrar los fallos previos. No hay aceptacion completa.

Paris autorizo excepcionalmente `--max-offset=1s` solo en la base aislada,
conservando su volumen. No se cambio el Compose del producto, Windows, WSL ni
otros stacks. Hubo 37 consultas SQL sin error y cinco pruebas nativas favorables
(concurrencia, rollback, SQLSTATE y confirmacion perdida). Persistieron 11 avisos
de salto atras, pero cero rechazos por reloj adelantado o fallos de latido en esa
ventana: mitigacion del entorno, no reparacion de su reloj. Dos errores de
preparacion del ejecutor se conservaron y corrigieron antes del resultado verde.

Se renovaron dos horas solo las caducidades de chat y embeddings. Topes, modelos,
permisos y concurrencia permanecieron iguales. Gasto adicional asentado total:
**0,042052156 USD de 0,12 USD**, incluidos intentos fallidos y embeddings.

Correcciones propias posteriores al primer corte:
- Diagnostico dimensional cerrado en ambos `chat_expressions.py` y en
  `processor/app/clients/chat_gateway.py`; 005 comparaba porcentaje con moneda.
- Admision en `backend/app/api/routes/chat.py`: errores SQL anteriores a la
  reserva devuelven 503 `storage_unavailable`, sin filtrar excepciones.
- Pruebas Red/Green: 24 casos de operaciones y 99 focales de diagnostico;
  44 casos finales de prompt, recursos, cantidades y adaptacion. Los negativos
  originales se conservan. No se suman estas suites solapadas como casos unicos.
- Prompt: unidades compatibles en comparaciones y conclusion explicita del
  semaforo solicitado. Manifiesto actualizado. Esas instrucciones no garantizan
  por si solas una conclusion correcta, como muestran 005 y 007.

Imagenes finales de este corte:
- Backend: `sha256:bd822ee7d80fd1be8d3621abdadf481d237b2b96aa09985388fd63b881f4a4b8`.
- Processor: `sha256:95c5b055709376f652686db33cf03c27676e52a946b888440f9aeec258f11e46`.
- Prompt: `jup-035.chat.v3:7b5040b49862ec15f61b3c0b04c9e2be136ff8f60c7db2c0bbf092083d670317`.

| Caso | Resultado funcional de las imagenes finales |
| --- | --- |
| 005 | No aceptado. Total elegible 1000 EUR y 10 % correctos, pero afirma rojo en vez de amarillo y omite evidencia. El ensayo intermedio calculaba bien pero omitia el color. Ambos se conservan. |
| 006 | Respuesta final correcta: 5 %, verde, formula y limite inclusivo citados. Primer intento truncado (`length`, JSON incompleto); el reintento automatico existente completa. No es una ejecucion limpia ni se oculta el primer fallo. |
| 007 | No aceptado. Calcula 10,1 % y concluye rojo, pero compara el porcentaje consigo mismo (`10,1 > 10,1`, falso) en lugar del umbral documental; prosa y comparacion se contradicen. |
| 012 | Admision corregida y distincion allocated/tagging correcta. Pendiente de cita completa: afirma cinco tags obligatorios, incluido owner, pero los dos fragmentos seleccionados no contienen esa politica. |
| 019 | Criterio focal favorable: 150 EUR/dia, variacion relativa indefinida por base cero, pide baseline y no afirma la doble condicion. Cita la definicion de anomalia; no una prueba de costes reales. |
| 021 | Criterio focal favorable: diferencia 200 identificado, 150 estimado y 80 EUR/mes verificado del ejercicio; calcula 40 % y cita las definiciones pertinentes. |
| 022 | Criterio focal favorable: rightsizing, uso estable y riesgo de infrautilizacion; sin inventar precio, descuento, plazo contratado ni ahorro. El proximo mes procede de la pregunta, no de una duracion contractual inventada. |

Las siete operaciones quedaron completed y persistieron exactamente una pareja.
Contenido y metadatos del resultado final coinciden con historial; no hay IDs de
mensajes/citas duplicados ni citas ajenas a lo recuperado. Eso NO prueba pertinencia:
la matriz anterior incluye lectura de afirmaciones y fragmentos. Se reabrieron
005 y 006 en navegador: 006 conserva fuentes pequenas bajo la respuesta; 005
conserva tambien su conclusion erronea, sin fuentes. No se modifica el historial
para ocultar el fallo. Los deltas SSE reales no se capturaron; equivalencia de
streaming sigue acreditada solo con productores controlados.

Recibos nuevos: `clock-margin-*`, `focal/diagnostic-clock-1s/`,
`focal/compare-prompt/`, `focal/classification-prompt/`,
`focal/classification-other/`, `focused-results-audit.json`, congelacion
`classification-prompt-final-code-freeze.json` y capturas finales 005/006.
Pendiente: resolver conclusion/comparador/citas de 005/007/012 y decidir el
tratamiento del intento truncado de 006 manteniendo los limites aprobados.
No hay mas llamadas tras esta comprobacion ni se ha repetido la bateria de 28.

## Base, propiedad y atribucion

Destino exclusivo `feat/JUP-035-chat-delivery`, asociado a PR #120. HEAD local
permanece `a55bb304b8f2a199049134f902146b3f981727be`; no hay commits nuevos.
La consolidacion no mueve HEAD: aplica contenido propio de `8d98ae57` y cambios
locales del checkpoint, preservando migraciones, interfaz y resumen. El
experimento de calculadora anterior queda respaldado con SHA256 fuera del repo.

Referencia de Alejandro: `193b785a786ab68b3b2839e5154e814571fa1319`.
HEAD de referencia examinado: `f1848e5744391d7bd472ec9c944ba08f8ad764aa`.
Se leyeron los siete commits posteriores sin integrar toda la rama. Origen de
la evolucion: `0d91d337`, `1b7eb148`, `41e23706`, `85994b86`, `192b6872`, `193b785a`.
Su rama y PR #121 no se modificaron. No se hicieron push, comentarios ni merge.

## Matriz historica del primer corte

| Parte | Situacion |
| --- | --- |
| Aislamiento, HMAC, persistencia atomica, autoridad financiera, periodo y suscripciones | Ya presentes; conservados |
| Recuperacion de resumen, migraciones y UI propia | Consolidados desde checkpoint propio |
| `server-documentation-v4`, una recuperacion y una generacion | Adaptados en ambos servicios |
| Catalogo cerrado, expresiones Decimal, segmentos privados | Adaptados; sin calculadora nativa ni IDs de resultados |
| Pasajes literales y seleccion de citas autenticadas | Adaptados; controles del backend conservados |
| Prompt separado del de ingesta, reasoning high/exclude, 3200 tokens | Adaptado; manifiestos e imagenes coincidentes |
| Aceptacion real 005 | Pendiente: `expression_incompatible_units` |
| Aceptacion real 006/007 | Contenido, fuentes y persistencia favorables en este corte |
| Aceptacion real 012/019 | Pendiente: HTTP 500 antes de admitir generacion |
| Aceptacion real 021/022 | No ejecutadas por inestabilidad persistente del reloj SQL |
| Publicacion y CI por commit | Fuera de este encargo; sin commit nuevo |

## Archivos de la adaptacion

- Ambos servicios: `app/core/chat_expressions.py`, `chat_segments.py`,
  `chat_calculations.py` y `chat_resources.py`. Los tres modulos compartidos
  son byte-identicos; `chat_calculations.py` solo conserva el guard de prosa,
  no el plan de calculos anterior.
- Backend: `app/schemas/chat.py`, `app/services/chat_context.py` y
  `chat_operations.py` (este ultimo solo cambia el protocolo del recorrido).
- Processor: `app/agents/schemas.py`, `prompts.py`, `app/clients/chat_gateway.py`,
  `chat_stream_parser.py` y `app/chat.py`.
- Prompt: `prompt_resources/jup035/chat/v3/system.md` y `manifest.json`.
- Pruebas de expresiones, cantidades documentales, evidencia, gateway, protocolo,
  contexto, streaming y fixtures de resumen ajustadas al esquema efectivo.
- ADR-0019, change `jup-035-auto-documentation` y unico tema de continuidad.

El diff completo tambien contiene la consolidacion del checkpoint; no atribuir
esos cambios anteriores a esta adaptacion. El manifiesto externo distingue
ambos grupos por hashes de la base consolidada.

## Pruebas locales

| Comprobacion | Resultado |
| --- | --- |
| Red backend | 16 fallos y 1 exito, antes de implementar |
| Red processor | 2 errores de coleccion por modulos nuevos inexistentes |
| Backend, regresion chat/contexto/resumen final | 513 superadas, 18 omitidas |
| Processor, regresion chat/contexto/resumen final | 387 superadas, 6 omitidas |
| Cockroach real, suite backend | 15 superadas |
| Deadline de resumen backend, suite dedicada | 4 superadas (3 SQL reales y 1 SQLite) |
| Mutaciones suma, denominador, umbral inclusivo, procedencia | 4/4 detectadas |
| OpenSpec estricto | 69/69 |
| Trazabilidad e higiene | Favorables |
| Pruebas Node de gobernanza y banco | 34 superadas |

Las 18 omisiones del backend corresponden a las suites SQL ejecutadas aparte.
Las seis del processor son probes nativos de resumen no ejecutados en esta
ronda: su suite todavia exige el nombre historico fijo de base
`economicon_jup035_mock_smoke_479b1dcb8293`. No se declaran superadas ni se crea
una base con ese nombre para ocultar la restriccion.

Se conservaron los primeros fallos de regresion y los recibos posteriores.
Los fixtures anteriores de dos generaciones/schema sin fuentes se adaptaron
al nuevo contrato; no se relajaron validadores para lograr resultados verdes.
No se ha repetido toda la suite del monorepo ni las 28 preguntas.

Reproduccion sin llamadas a modelos: desde cada servicio, ejecutar `pytest`
sobre `tests/test_chat_*`, `tests/test_context_compaction*` y `tests/test_summary_*`
con las dependencias fijadas de su imagen. Para las pruebas SQL usar una base
desechable propia y las variables documentadas por cada suite, no credenciales
de produccion. Validar despues OpenSpec y `jup:check -- --change
jup-035-auto-documentation`. Los archivos de prueba nuevos contienen los
ejemplos de expresiones, unidades, limites, citas y errores de procedencia.

## Imagenes y prompt probados

- Backend: `sha256:011e150c23c1fed87a48d524ca6dd5c2e610a4f498bc8f451a0a01cb63289d40`.
- Processor: `sha256:ecef167e53e00438bb0e2c62022d8b5b15b1e6d4a1ccfb7f2803a2cdf8c7c747`.
- Prompt: `jup-035.chat.v3:37bdf7986e7e6772fb17c3e6ed2d742e5c7908ba0cd8b323effdc037672699a9`.
- Tokenizer: `19e773648cb4e65de8660ea6365e10acca112d42a854923df93db4a6f333a82d`.

Prompts/tokenizer incluidos en imagen, sin montaje Windows. La congelacion
inicial de presupuesto precede al rebuild; `runtime-at-run-*` y
`final-code-freeze.json` identifican las imagenes realmente ejecutadas.

## Ensayo real y limites

Se autorizo expresamente enviar preguntas sinteticas, prompt, esquema y corpus
de pruebas a OpenRouter, con maximo adicional de 0,12 USD. Gasto asentado observado
al detener: **0,008926029 USD**, incluidos fallos y embeddings. No se ampliaron
topes, modelos, permisos ni caducidad. Conversaciones nuevas, una activa cada vez.

| Caso | Observacion de esta ejecucion |
| --- | --- |
| 005 | Un intento; rechazo `expression_incompatible_units` en `provisional_answer`; cero mensajes persistidos. El catalogo local si reconoce 700, 200 y 100 EUR. No se conserva la expresion rechazada: combinacion concreta aun desconocida. |
| 006 | 50/1000 x100 = 5 %, verde inclusivo; chunks 3 y 4 de reglas de negocio sustentan formula y umbral. Dos mensajes, sin duplicados. Reabierta en navegador con fuentes pequenas bajo respuesta. |
| 007 | 101/1000 x100 = 10,1 %, rojo; mismos fragmentos pertinentes; dos mensajes sin duplicados. |
| 012 | HTTP 500 en admision; sin respuesta evaluable. |
| 019 | HTTP 500 en admision; sin respuesta evaluable. |
| 021/022 | No ejecutadas tras confirmar problema persistente del reloj. |

En 006/007 el contenido final y los metadatos publicos se contrastan con el
historial. El historial anade `role` y `created_at`; no se exige igualdad del
envoltorio HTTP completo. La equivalencia del streaming se cubre con productores
controlados; este ejecutor real consulta resultado final, no captura los deltas.
Las fuentes son dos fragmentos del mismo documento, mostrados como dos lineas.
Se verifico su pertinencia leyendo el contenido, no solo los IDs.

El reloj SQL puntual estaba dentro del intervalo de la peticion. Sin embargo,
el archivo de log interno de Cockroach muestra `backward time jump detected`
y `remote wall time is too far ahead` repetidos, con saltos de unos 0,7-0,85 s.
El incidente de las 14:50:34 UTC coincide con el HTTP 500 de 012. Es evidencia
de entorno inestable, no prueba de fallo del modelo. Leer solo stdout del
contenedor no detecta estos avisos. No se ampliaron tolerancias ni reinicio
Docker Desktop/WSL, que afectaria a otros proyectos.

## Pendientes y recibos

1. Estabilizar el reloj del entorno Docker y repetir probes sin gasto antes de
   reintentar admision. No presentar SQL inestable como error semantico.
2. Acotar la expresion incompatible de 005 con diagnostico estructural saneado;
   no reparar operandos por inferencia ni relajar unidades.
3. Completar 005/012/019/021/022 y reapertura favorable de 005. No repetir 28.
4. Resolver la portabilidad de los seis probes processor o documentar su
   ejecucion independiente cuando exista un entorno autorizado compatible.

Recibos locales conservados en `jup035-adaptation-20261013`: backups con hashes,
`consolidated-baseline.json`, `final-code-freeze.json`, `delivery.diff`, XML y logs
Red/Green, `mutations.json`, `real-clock-diagnostic.log`,
`real-processor-diagnostic.log`, `real-acceptance-partial.json` y `focal/`.
La ubicacion absoluta se entrega en el informe del chat; no es prerrequisito de
las pruebas versionadas. Los recibos no contienen claves. Las evidencias de
campanas anteriores permanecen intactas y no acreditan esta aceptacion.
