# JUP-035: correcciones de revision

Corte local: 12/10/2026. No es una review humana, una CI remota ni un merge.
Paris autoriza ejecutar el plan de correcciones e incorporar el trabajo de
PR #121, conservando su RAG automatico. Aprueba ademas conservar JUP-037 en
una vista especifica de propiedad, sin chat ficticio.

## Revision y alcance

- Rama: `feat/JUP-035-chat-delivery`.
- HEAD previo a este delta: `4d5edf70e037f8e9757f8433dfedce672cadcbbc`.
- Checkpoint propio conservado: `a8f4dddc05d85b17ed2023388c8857d1ce538882`.
- Trabajo del compañero conservado: `75f4f41dc970f32447fde5ce0e10adf24bcea61d`.
- Este informe cubre un arbol con cambios sin commit; no atribuye sus resultados
  a un SHA inmutable posterior ni acredita CI del ultimo candidato.
- No se modifica la rama original del compañero, Trello ni GitHub.

## Peticiones y respuesta tecnica

| Peticion | Implementacion y comprobacion |
| --- | --- |
| Tokenizer fuera de Git | Descarga oficial fijada por revision y SHA256 al construir; cache verificada para pytest; dos imagenes cargan recursos sin red ni montaje. |
| Planificador sobrevive a fallos SQL | Diagnostico cerrado y saneado por etapa, continuidad del bucle y reinicio de tarea terminada; OperationalError en recuperacion de operaciones/resumenes no impide completar la espera. |
| HMAC en local y CD | Preparacion persistente antes de Compose; no sobrescribe una clave existente ni recrea silenciosamente una ruta explicita perdida. init -> prepare -> docker compose config comprobado en directorio temporal. |
| Alcance y demo | Guia de lectura en continuidad: canal privado, historial, reintentos, resumen, tokenizer y panel; mock por defecto y activacion IA explicita. No se afirma HA. |
| Python denso | 32 modulos de producto formateados con Black 24.10.0, comprobacion segura de equivalencia AST y comprobacion final sin cambios necesarios; sin nueva dependencia de produccion. |
| Indice y dos temas | Una fila y un tema actual de chat; bitacoras conservadas como evidencia historica, fuera del indice. |
| ADR y arquitectura | ADR-0019 describe HMAC, JSONB, assistant-ui y tokenizer; arquitectura describe backend -> processor -> gateway, no el chat ficticio. |
| Dos chats y evaluador | /assistant abre el panel nuevo; messages sin ownership_query devuelve 410; collect usa generaciones, espera estado final y guarda recuperacion real. /ownership conserva solo la consulta estructurada JUP-037. |
| Carrera y tests inestables | Se conservan las correcciones de fencing/orden SQL-SSE del compañero. Suite de operaciones repetida tres veces: 20/20 cada vez, sin operation_changed inesperado. No demuestra ausencia de cualquier carrera en produccion. |
| Estados y evidencia en UI | AnswerEvidence muestra no_data/insufficient_data y cost_query separado del corpus; controles frontend existentes y pruebas de propiedad conservados. |
| Mutante provenance | Tres controles de evidencia falsificada pasan; en una copia temporal con evidence_provenance sustituido por pass fallan los tres como se esperaba. No se modifica el producto para ejecutar el mutante. |
| SQL deadline portable | Se conserva fixture del compañero: base propia por ensayo, sin exigir el nombre de una maquina; tres probes Cockroach y un control CPU previamente ejecutados sobre la combinacion. |
| Evidencias locales y bateria | Siete informes identifican expresamente los recibos locales como antecedentes no portables. Banco de 28 entradas y guia versionados; no se inventan ni sobrescriben resultados historicos. |
| Robustez | Limite de 20 datasets antes de billing; fechas numericas rechazadas; timeout de contexto 503; liberacion de buffers; streaming sin decodificar historial por fragmento; historial corrupto aislado; suscripciones canonicas verificadas. Suites de admision, contexto, historial y resiliencia. |
| Enlaces heredados | Indice enlaza los informes existentes de metricas y etiquetado; referencias del tema historico apuntan al tema actual. |

La retirada de la vista antigua descubrio una regresion de acceso a JUP-037.
No se eliminaron sus pruebas para obtener verde: con aprobacion de Paris, se
reutilizan el formulario, las queries y el endpoint de costes en /ownership.
Siempre se envia ownership_query; se conservan filtros, evidencia, errores,
aislamiento y descarte de respuestas tardias. Desde esa vista el panel usa
captura no-adapter sin promover datos del formulario a evidencia financiera.

La recuperacion nueva conserva tambien los contadores y diagnosticos saneados
de JUP-022; la nueva generacion contabiliza assistant_queries_total una vez por
operacion creada, no otra vez por repeticion idempotente.

## Resultados locales

| Comprobacion | Resultado y limite |
| --- | --- |
| Backend completo antes de añadir /ownership a capturas | 1649 passed, 82 skipped, cero fallos; 304.81 s. |
| Backend despues de la ruta de propiedad | 73 passed, 1 skipped en screen/ownership; el omitido requiere Cockroach opt-in. No se suman con la suite completa. |
| Backend focal, historial/admision/resiliencia/recuperacion | 63 passed; solapa la suite completa. |
| Processor completo | 999 passed, 71 skipped, 6 failed por entorno local sin PyJWT. |
| Processor: seis fallos anteriores en imagen corregida | 6 passed, 6 skipped en test_ingest_task; los seis omitidos ya pertenecian a los 71. No es una nueva suite completa verde. |
| Processor completo, repeticion final con imagen corregida | 1005 passed, 71 skipped, cero fallos; 300.56 s, exit 0. Contenedor desechable sin red, 2 GiB y repositorio montado en lectura; Python 3.12. |
| pgvector real, busqueda y aislamiento | 17 passed, sin omisiones; servicio propio eliminado al terminar. |
| Evaluador, CD y downloader | 127 passed, 139 subtests; Python 3.12 sin inferencia. |
| Workflow, gobernanza, topologia y tooling local | 137 passed, cero fallos; repeticion con permisos para el test de symlink de Windows. |
| Frontend completo final | 888 passed, cero fallos y cero omitidos; se conservan los ensayos fallidos. |
| Frontend typecheck | Tres configuraciones sin errores. |
| Frontend lint | Cero errores; una advertencia heredada exhaustive-deps en ChatPresentation.tsx, no corregida en este alcance. |
| Frontend build | Correcto; conserva advertencia de bundle >500 kB y advertencia de importacion estatica/dinamica. |
| Navegador autenticado /ownership | Acceso real, consulta vacia con evidencia, recarga con persistencia, moneda invalida y fechas incompletas rechazadas, historial oculto al cambiar de tenant y restaurado al volver. SQL confirma cuatro mensajes, sin inserciones por los dos rechazos. |
| Formato Python | Black 24.10.0, 32 modulos de producto, cero cambios necesarios en comprobacion final. |
| OpenSpec/trazabilidad/higiene | 67 items OpenSpec, siete changes con trazabilidad y 1407 archivos de higiene sin incidencias; no implican aceptacion funcional humana. |

La dependencia PyJWT ya estaba declarada en requirements-dev del processor.
La imagen local anterior no la incluia: se creo una imagen desechable de pruebas
con PyJWT 2.15.1, sin cambiar requisitos del producto ni aserciones para ocultarlo.
La cobertura combinada identifica los seis casos repetidos; no se presenta como
si una sola ejecucion completa hubiera dado 1005 passed.

Posteriormente, por indicacion de Paris de continuar las comprobaciones, se
repite la suite completa con la imagen de pruebas corregida y se obtiene
1005 passed/71 skipped en una unica ejecucion. Esta nueva ejecucion no
sobrescribe los seis fallos anteriores ni convierte las omisiones en PASS.
Log conservado fuera del producto: `processor-review-complete-corrected-20261012.log`
en el directorio de evidencias `pr121-integration` del worktree. El HEAD sigue
siendo 4d5edf70 con el delta local sin commit; no es un resultado de CI remota.

## Reproduccion

Desde cada servicio con sus dependencias de desarrollo y recursos preparados:

```text
python -m pytest -q -p no:cacheprovider tests
python -m pytest -q -p no:cacheprovider tests/test_chat_resilience_jup035.py tests/test_chat_admission_hardening_jup035.py tests/test_chat_operations_jup035.py
python -m pytest -q -p no:cacheprovider tests/test_chat_screen_jup035.py tests/test_ownership_questions.py
```

Desde frontend:

```text
node node_modules/vitest/vitest.mjs run --maxWorkers=2
node node_modules/typescript/bin/tsc --noEmit
node node_modules/typescript/bin/tsc -p tsconfig.node.json --noEmit
node node_modules/typescript/bin/tsc -p tsconfig.test.json --noEmit
node node_modules/eslint/bin/eslint.js src tests
node node_modules/vite/bin/vite.js build
```

Para repetir preguntas reales, seguir la
[guia versionada](../validation/JUP-035-chat-reproduction.md). Las entradas
sinteticas en texto no equivalen a costes SQL verificados: cargar la muestra y
su captura cuando el criterio lo exija. No requiere recibos privados de otra
maquina. Los tests nativos requieren servicios/base propios y las variables
documentadas en sus fixtures; las omisiones no cuentan como pruebas pasadas.

## Imagenes y recursos

- Backend final: manifest list
  `sha256:de2a08447200093e9de6a259043c2db4fee3c004e05670b00dd5fbcc1a66824d`.
- Processor: manifest list
  `sha256:a2a1b87baab3eadb303534ba8c061a6ba54ab86c800264e2ef0296d3165d8ce8`.
- Prompts/tokenizer cargados con usuario no root y --network none, sin montaje.
- No se levanta otro stack completo en este corte ni se consume OpenRouter.
  Los dos ensayos reales aceptados y el saludo fallido permanecen en la
  [evidencia de incorporacion](jup-035-pr121-integration-20261012.md).

## Fallos conservados y pendientes

Se conservan los logs anteriores: backend 12 fallos iniciales, processor seis
por dependencia ausente, frontend 37 fallos por vista retirada, adaptacion inicial
11 fallos por espera de carga, y una comprobacion del recuento de navegacion
desactualizada. Ninguno se transforma retrospectivamente en una ejecucion verde.
Tambien se conserva el intento de carga offline con nombres de funcion
incorrectos: fallo de la invocacion, repetido con load_resources y superado.

El test de navegacion comprueba nueve destinos, padding compacto y scroll
horizontal disponible, no anchuras de pixels que jsdom no mide.

## Comprobacion posterior en navegador autenticado

Paris autoriza consultar y usar solo la clave demo y levantar un backend temporal.
Se usa la imagen final de backend con el frontend local compilado contra
http://127.0.0.1:48535; vista http://127.0.0.1:48237/ownership.
Proyecto propio: autonomo-jup035-ownership-20261012. Cockroach, RabbitMQ y
pgvector tienen datos propios y ningun puerto publicado; solo backend se
publica en loopback. CORS admite unicamente el origen de esta vista.

Migraciones de backend y processor ejecutadas solo en esta base desechable.
La consulta de aplicacion sin costes devuelve ausencia de registros, no gasto
cero, y muestra evidencia de costes. Recarga y cambio de tenant conservan el
historial correcto. Una moneda en minusculas y una fecha sin pareja producen
alertas sin persistir mensajes. SQL confirma tenant-core y cuatro mensajes
de dos consultas vacias. La primera automatizacion de fecha no actualizaba el
estado del control; se repite con tecla nativa y se observa el rechazo correcto.
No se atribuye ese intento inicial a una validacion de fechas favorable.

Se conservan los fallos de preparacion: script de entrada de Cockroach,
alias no admitido por el opt-in local y puerto no publicado al usar solo red
interna. Se corrige exclusivamente la configuracion del ensayo, no el producto
ni sus validadores. La lectura SQL inicial uso una columna inexistente; se
repite sobre dialogue_history con resultado correcto.

Captura externa: ownership-authenticated-20261012.jpg en pr121-integration.
No se comprueban importes con datos cargados, responsive movil ni chat en este
stack: CHAT_ENABLED=false y SUMMARY_ENABLED=false, sin processor de inferencia
ni credenciales de modelos. No hay gasto nuevo. El entorno queda disponible
temporalmente para Paris; no se alteran stacks anteriores.

Pendientes de entrega: commit del arbol final, CI remota por ese SHA, revision y
validacion independientes y autorizaciones de publicacion/archivo que correspondan.
El change auto-documentation conserva 2.2 y 2.3 pendientes: los probes focales no
acreditan toda su matriz ni otra bateria completa. No se archiva adicionalmente
ni se repiten las 28 contra el proveedor por iniciativa propia.

## Controles documentales finales

Tras la comprobacion del navegador se repiten OpenSpec estricto (67/67),
trazabilidad (siete changes), higiene (1407 archivos) y git diff --check, todos
sin incidencias. Se verifica la existencia de ocho documentos principales
referenciados y las 28 entradas con identificadores unicos del banco versionado;
no es una validacion de todos los enlaces externos ni de las respuestas reales.
La invocacion via Corepack falla al resolver registry.npmjs.org antes de ejecutar
OpenSpec; se usa la misma CLI local instalada, version 1.8.0, sin descargas,
actualizaciones ni debilitamiento de la validacion. Su ejecucion directa pasa.
No se cambia el checklist de la matriz real ni de la bateria completa para
convertir la evidencia focal en cumplimiento de esas tareas.

## Historial y fuentes en navegador - ensayo aislado

12/10/2026, autorizado por Paris. Imagenes finales de backend y processor,
proyecto Docker desechable `autonomo-jup035-chat-ui-20261012`, modo mock,
CockroachDB y pgvector propios. Backend en loopback 48536 y preview 48238;
no se usan claves de modelos ni se consumen inferencias. Codigo sin cambios.

- Envio por el panel: operacion completed, un mensaje y una respuesta;
  ambos reaparecen tras recargar y abrir la conversacion desde el historial.
- Nombre automatico y renombrado desde panel e historial comprobados. SQL
  confirma el ultimo nombre y dos mensajes JSONB. Un borrador vacio no se
  guarda hasta enviar: su nombre provisional no sobrevive a la recarga.
- Confirmacion de borrado: No conserva la conversacion; Si la elimina y deja
  una nueva vacia. SQL confirma cero conversaciones y cero operaciones en
  ese corte. El resumen es una columna del padre, no una tabla independiente.
- Fuente sintetica NEXO-LIMA: se guarda un documento de cada uno de dos tenants
  en pgvector y se ejecuta `ChatContext.retrieve` con embeddings mock de ocho
  dimensiones. Recupera solo el documento de tenant-core; un tenant sin corpus
  devuelve vacio. El extracto contiene Equipo Delta y respalda la afirmacion.
- Presentacion: una fixture de historial identificada como prueba visual usa
  esa cita recuperada. El navegador muestra titulo y fuente debajo de la
  respuesta, icono de documento y texto de 13 px, sin extracto completo.
  Esta fixture no pasa por una generacion del modelo ni acredita su decision
  automatica de buscar o citar. La recuperacion y la presentacion se comprueban
  por separado, no como un nuevo ensayo completo de IA real.
- Pruebas existentes focales: AnswerEvidence (12), chat-deletion (5),
  chat-titles (6): 23 passed, cero fallos, 7.40 s. Incluyen bloqueo de borrado
  por solicitudes activas, 409 conservando datos, cancelacion y lectores tardios.

Recetas, recibo de recuperacion y capturas `chat-ui-reopened-20261012.png` y
`chat-ui-source-20261012.png` se conservan en el paquete externo
`pr121-integration`. No son dependencias de ejecucion del producto. Se conservan
los fallos iniciales de preparacion: generador incompatible con PowerShell 5,
subred ocupada, preview inicial no accesible y consultas SQL con formato/nombre
incorrectos; corregidos solo en el ensayo. La matriz real y las 28 preguntas
siguen pendientes; no se marcan como completadas por estas comprobaciones.

## Ensayo real de embedding, pregunta y fuente

12/10/2026, 19:09-19:19 UTC. Paris autoriza documento/pregunta sinteticos,
prompt de sistema, herramienta y esquema enviados a OpenRouter, con maximo
0.12 USD para este ensayo. Solo se renueva la caducidad de las claves existentes;
no se cambian modelos, permisos, concurrencia ni presupuestos de las claves.
Proyecto aislado `autonomo-jup035-chat-real-20261012`; backend 48538 y preview
48239, imagenes finales locales de esta entrega. No se modifica producto.

- Documento NEXO-LIMA: Equipo Delta, comprobacion del identificador de lote,
  aprobacion antes de publicar y referencia NL-7429; sin plazos ni importes.
- Ingesta publica `/jobs/ingest`, trabajo
  `3bb57a64-ee22-42b7-89bf-98072a30f2a8`: completed. SQL confirma un chunk,
  provider litellm, dimension declarada y real 1536, tenant-core. La fuente
  `nexo-lima-validation` no es una fuente de analisis financiero admitida:
  ese paso devuelve unsupported sin inferencia; el embedding si es real.
- Pregunta enviada desde el navegador sin pedir citas. Operacion
  `f6e779d2-fc9b-48cf-9cb9-4762a43f721c`: completed, un intento. El modelo
  solicita la herramienta; el backend recupera el chunk de ese documento
  con distancia 0.26190584685747087 (umbral 0.6). La respuesta contiene los
  tres datos correctos, sin inventar cifras ni plazos; metrics y subscriptions
  vacios. La cita apunta a ese chunk y su contenido sustenta las afirmaciones.
- Conversacion `c9413f77-2a77-4b6d-865b-04a5d64a72e2`: API confirma exactamente
  dos mensajes, respuesta y cita persistidas. Recarga y reapertura desde historial
  conservan ambos. Fuente debajo de la respuesta a 13 px con icono, sin extracto.
- Consumo upstream: 0.620367234 -> 0.625407946 USD; diferencia
  0.005040712 USD, por debajo de 0.12. Generacion registra 10277 tokens de entrada,
  271 de salida y coste 0.0050388525 USD. Embedding del documento: 82 tokens,
  0.00000164 USD; la pregunta consume embedding adicional. No es un precio fijo.

Limite detectado: SUMMARY_ENABLED=true sin SUMMARY_API_KEY_FILE en el Compose
externo del ensayo. El descriptor informa summary_ready=false y la memoria queda
failed/descriptor_mismatch, bloqueando un siguiente envio. No se acredita memoria
funcional ni se declara todo el entorno verde. Debe completarse la configuracion
de su clave separada; no se reutiliza la clave principal ni se relaja el control.

Se conserva la primera ingesta fallida por usar una ruta con barras en source;
el identificador seguro la corrige. Su mensaje se retira solo de la cola desechable
tras conservar el recibo. No hubo embedding ni respuesta en ese intento. Recibos
externos: real-flow-budget-before.json, real-flow-ingest.receipt.json,
real-flow-ingest-valid-source.receipt.json y real-flow-chat.receipt.json;
captura real-flow-source-20261012.png. No se repiten ni se acreditan las 28 preguntas.

### Configuracion de resumen completada en el ensayo

Paris autoriza completar el entorno y comprobar el desbloqueo. Se monta en lectura
la clave virtual separada de resumen existente mediante SUMMARY_API_KEY_FILE.
Su caducidad se prolonga hasta 12/10/2026 21:21:41 UTC; se conservan alias
economicon-chat, concurrencia 1 y presupuesto 0.07 USD. Solo se recrea el processor
de este stack; no se modifica producto ni los otros stacks. No hay claves en Git.

Reintentar compresion desde el panel deja la cola idle/cold, blocked=false,
retryable=false; se mantienen exactamente dos mensajes y la operacion completed.
Un unico intercambio sigue reservado como contexto reciente: available=false y
processed_pairs=0 son correctos; no se ha ejecutado una compresion del modelo.
La vista abierta conservo temporalmente la actividad anterior. Tras recargar y
reabrir desde el historial, desaparecen el aviso y el boton de reintento; Enviar
queda habilitado al escribir un borrador, que se retira sin enviarlo. Respuesta
y fuente permanecen. No se acredita refresco automatico sin recarga.

Gasto adicional de este paso: cero; upstream permanece 0.625407946 USD y la clave
de resumen en 0.029277255 USD. Total del ensayo real: 0.005040712 USD. Recibos
externos summary-key-preflight.receipt.json, summary-key-renewal.receipt.json,
real-flow-summary-retry.receipt.json y captura real-flow-unblocked-20261012.png.

### Compresion real focalizada

Paris autoriza probar la compresion. Conversacion desechable
590e4806-6fd3-44fa-889c-e995764cf653: cinco pares sinteticos, insertados mediante
los metodos de historial y marcados test_fixture/model_generation=false. Su
metadata de generacion es una fixture del contrato, no acredita cinco inferencias.
Se prepara un control fallido solo en esa conversacion para activar el reintento
publico; no se modifica el producto ni se simula haber alcanzado el umbral grande.

12/10/2026, aproximadamente 19:31 UTC: `/summary/retry` recorre backend, processor,
LiteLLM y OpenRouter. Se observa pending/running con blocked=true y, al terminar,
idle con blocked=false. Una llamada, artefacto
5971ba25-dae8-4b80-a4ec-9fb907678a61, disponible y valido en SQL y API. Comprime
un par y reserva los cuatro recientes; los diez mensajes originales se conservan.
El resumen mantiene Equipo Delta y NL-7429 como citas literales con source_ref
del par procesado. Se comprueba que cada cita existe en su mensaje autorizado.
Reapertura en navegador: Enviar habilitado al escribir, sin reintento ni memoria
visible. No se observo el boton de envio durante la llamada; el bloqueo durante
ese intervalo se acredita por los estados del servidor, no por una captura UI.

Recibo del proveedor: 672 tokens de entrada, 267 de salida, 939 totales;
coste 0.0008586 USD. La lectura inmediata de saldo aun no reflejaba el cargo;
se conserva y se contrasta despues: clave de resumen 0.029277255 -> 0.030135855,
upstream 0.625407946 -> 0.626266546 USD. Total acumulado de este ensayo real:
0.005899312 USD de 0.12 autorizados. Sin cambios de presupuesto o modelos.

Los dos primeros intentos de preparacion no llamaron al modelo: primero faltaba
metadata elegible en la fixture; despues el reintento sobre cola idle no actuaba.
Recibos originales conservados (real-summary-run.receipt.json y
real-summary-run-v2.receipt.json). El ensayo efectivo esta en
real-summary-run-v3.receipt.json, real-flow-summary-persisted.receipt.json,
real-summary-fixture-v2.receipt.json y real-summary-armed.receipt.json.
Captura: real-summary-completed-20261012.png. Esta prueba no acredita disparo
automatico al umbral de contexto ni uso del resumen en una nueva respuesta;
no sustituye la matriz ni la bateria completa pendientes.

### Respuesta real posterior al resumen

12/10/2026, 19:43 UTC: pregunta sobre el primer intercambio en la misma
conversacion. Operacion b5385177-3705-40b9-8adc-d909b4035883 completed, un intento.
El manifiesto declara summary.used=true y el artefacto 5971ba25-dae8-4b80-a4ec-9fb907678a61.
Recuerda la pregunta sobre NEXO-LIMA, Equipo Delta y NL-7429. No usa RAG ni
anade citas documentales: consulta el historial, no nueva evidencia externa.
Estado no_data, sin metricas ni recomendaciones; conserva una advertencia
demasiado tecnica sobre summary_is_lossy. No se corrige el texto en este ensayo.

SQL/API conservan doce mensajes, sin duplicados; el resumen permanece disponible
y la cola idle/no bloqueada. Tras recargar y seleccionar el historial, pregunta
y respuesta siguen visibles. Esto acredita incorporacion del resumen y recuerdo
coherente, no fidelidad literal ni dependencia exclusiva del resumen: cuatro
pares recientes tambien siguen presentes. No acredita el umbral automatico grande.

Recibo: 11400 tokens de entrada, 715 de salida, 12115 totales, 0.0071139 USD.
Lectura upstream asentada a las 19:47 UTC: 0.633380446 USD; respecto a la base
0.620367234, gasto total de este ensayo 0.013013212 USD, inferior a 0.12.
Presupuestos, modelos y caducidades sin cambios. Se conservan las lecturas
inmediatas donde el cargo aun no aparecia, sin interpretarlas como gasto cero.
Recibos externos post-summary-response.receipt.json,
real-flow-post-summary-final.receipt.json y real-flow-post-summary-settled.receipt.json.
Captura post-summary-reopened-20261012.png. No se repite la bateria completa.
