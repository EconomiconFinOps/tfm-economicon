# Chat conversacional - JUP-035

Actualizado: 13/10/2026. Este tema describe la entrega local, no un merge
ni una validacion humana. Los responsables y el estado oficial siguen en Trello.

## Recorrido vigente

Ultima bateria real de 28 preguntas: 25 aprobadas con el criterio MVP-TFM
acordado, 005 contradictoria (amarillo/rojo) y 014/017 rechazadas por evidencia
documental seleccionada sin uso, incluso tras la correccion. 003/011 pasan
en esta repeticion. Las 26 respuestas entregadas coinciden con su historial
y evento final, sin duplicados. No hubo cambios de producto durante la tanda.
Este checkpoint conserva los fallos, no declara cierre ni publicacion. Ver
[bateria y pendientes](../evidence/jup-035-mvp-full28-20261013.md).

La ampliacion local de fuentes permite respaldo documental en abstenciones y
rechazos, valida referencias de segmentos y autoriza una sola correccion con
contexto reutilizado y deadline original. No muestra borradores antes de validar
y persistir. Pasan 57 pruebas backend, 161 processor y 37 frontend. En la ronda
focal anterior 025/026 respondian correctamente, pero 003 conservaba una cita
incompleta y 011 un supuesto con cifra equivocada. Se preserva ese resultado
historico, sin sustituirlo por el posterior. Ver
[resultados y limites actuales](../evidence/jup-035-bounded-correction-20261013.md).

Se ha corregido la fixture SQL del resumen: prepara datos sinteticos propios y
espera la tarea de limpieza, en lugar de inferir su fin de la respuesta HTTP.
La carrera se reprodujo con cierre retrasado; seis controles SQL reales y dos
casos relacionados pasan sin omisiones. No cambio el producto. Ver
[diagnostico y reproduccion](../evidence/jup-035-summary-sql-settlement-20261013.md).
La revision independiente y los 12 controles/28 preguntas siguen separados.

La ultima ronda real de 005/006/007/012 cumple el criterio MVP: respuestas
coherentes con la documentacion, calculos correctos y sin datos inventados.
Cada caso completa en un intento y persiste una pareja, con streaming igual
al resultado e historial. 005/006 conservan fuentes pequenas al reabrir.
Se retiro el rechazo lexical de colores correctos y se simplifico el prompt;
la comprobacion funcional conserva la responsabilidad de detectar contradicciones.
6400 tokens de salida corrigen la truncacion acreditada de 006 con 3200.
019/021/022 conservan sus resultados focales anteriores, no se repitieron aqui.
El margen de reloj de 1 s sigue limitado al entorno SQL aislado y no repara
su reloj. Gasto adicional asentado 0,083706085 USD de 0,12.
Sin publicacion ni bateria completa repetida. Ver
[informe y limites](../evidence/jup-035-expressions-adaptation-20261013.md).

Reconciliacion local del 13/10/2026 sobre `8d98ae57`: el migrador distingue
`002_anomaly_episodes` y `002_chat_operations` y reaplica sus pasos idempotentes
si una base conserva solo el marcador historico `002`. La vista de propiedad
envia siempre `ownership_query`. El panel de anomalias prepara sus filas y
filtros para el chat sin convertirlas en evidencia financiera autorizada.
Las suites de sesion y aislamiento conservan sus aserciones con los rotulos
en espanol de develop. La comprobacion de arranque real requiere Docker.
Resultados y limites: [evidencia de reconciliacion](../evidence/jup-035-checkpoint-reconciliation-20261013.md).

La interfaz assistant-ui usa operaciones `/assistant/.../generations`.
Backend autentica al propietario, valida el contexto y consulta los costes.
El protocolo local adaptado es `server-documentation-v4`: backend recupera una
vez con la pregunta canonica filtrada por tenant y processor ejecuta una unica
generacion estricta por intento. La correccion autorizada consume otro intento
de los cuatro existentes, reutiliza la recuperacion y no renueva el deadline.
Las expresiones tipadas y los pasajes autenticados se
proyectan al formato publico existente. La respuesta validada, las
citas y la evidencia se guardan atomicamente en el historial JSONB.

El modo mock no llama a modelos. El modo IA utiliza LiteLLM/OpenRouter con
claves distintas de chat y embeddings; no cambia automaticamente a mock.
El resumen conserva los mensajes originales y bloquea el envio mientras comprime.
Las conversaciones antiguas siguen visibles, pero sus respuestas de plantilla
no entran en el contexto del modelo ni en nuevos resumenes.

## Lectura para revision y validacion

1. [Contrato publico](../../apps/backend/app/schemas/chat.py): autoridad financiera y procedencia.
2. [Operaciones](../../apps/backend/app/services/chat_operations.py): admision, espera, cancelacion y recuperacion.
3. [Repositorio](../../apps/backend/app/db/chat_repository.py): transacciones, fencing y persistencia.
4. [Contexto](../../apps/backend/app/services/chat_context.py): costes, RAG y limite de 20 conjuntos antes de consultar.
5. [Panel](../../apps/frontend/src/components/chat/ChatPanel.tsx): estados, historial y envio.
6. [Evaluador](../../tools/assistant-eval.py): usa el chat nuevo, espera estado terminal y conserva recuperacion real.

## Arranque y demo

Preparar `.env` siguiendo el README y ejecutar `corepack pnpm local:prepare`
antes de `docker compose up --build`; o `corepack pnpm local:up`.
La preparacion crea una clave HMAC solo si no hay una configurada. No reemplaza
una clave existente ni regenera una ruta explicita desaparecida.
CD hace lo mismo en su directorio privado, fuera de las releases.

Prompts y tokenizer estan incluidos en las imagenes. El tokenizer se descarga
al construir desde una revision oficial fija y se verifica por SHA256.
Para pruebas fuera de Docker: `corepack pnpm tokenizer:prepare`.
La ejecucion posterior no descarga el tokenizer.

La demo utiliza el panel nuevo; `/assistant` redirige a ese panel. El endpoint
antiguo de mensajes rechaza la generacion de plantilla con 410; la consulta
estructurada de ownership conserva su contrato especifico y su formulario en
`/ownership`, por aprobacion de Paris. No ofrece generacion ficticia.
`CHAT_ENABLED=true` y `SUMMARY_ENABLED=true` son los valores de ejemplo vigentes:
chat y compresion activos, proveedores mock por defecto; el modo IA es explicito.
La evaluacion funcional usa `tools/assistant-eval.py collect`, no ese endpoint.
Se conservan los limites de espera y el presupuesto configurado; no se promete
HA, ejecucion multiproceso ni exactitud financiera sin evidencia autorizada.

## Evidencias y decisiones

- [Correcciones actuales](../evidence/jup-035-review-improvements-20261012.md).
- [Reproduccion desde el repositorio](../validation/JUP-035-chat-reproduction.md).
- [ADR del runtime](../adr/ADR-0019-conversational-runtime.md).
- [OpenSpec archivado](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/proposal.md).
- [Notas historicas](../evidence/jup-035-historical-notes.md) y
  [temas historicos](../evidence/jup-035-historical-topics.md).

Los ensayos anteriores, incluidos sus fallos, no se sobrescriben. Las referencias
a discos personales son antecedentes no portables; la guia actual permite
repetir la evaluacion desde el banco versionado sin copiarlos.

## Incorporacion de PR #121

Paris aprueba conservar el RAG automatico el 12/10/2026. Se incorpora la rama
`fix/JUP-035-auto-documentation` de Alejandro, conservando sus commits y sus
correcciones de cierre del streaming y pruebas SQL portables. Se mantienen las
correcciones locales de resiliencia, timeout, despliegue, historial y UI.

Sus resultados previos no acreditan esta combinacion. Las comprobaciones locales
afectadas pasan: 210 casos focalizados, incluidos tres probes SQL reales.
La pregunta documental recupera, cita y persiste correctamente con OpenRouter.
El saludo inicial falla por evidence_membership y se corrige restringiendo el
esquema sin fuentes; la repeticion pasa sin RAG ni citas y persiste el par.
Gasto adicional observado: 0.006293990 USD de 0.03 autorizados. No se repite la
bateria completa ni se declara validacion humana, publicacion o merge en develop.

- [Evidencia original del compañero](../evidence/jup-035-auto-documentation-20261012.md).
- [Incorporacion y ensayos focales](../evidence/jup-035-pr121-integration-20261012.md).

## Correcciones posteriores comprobadas

El [informe de correcciones](../evidence/jup-035-review-improvements-20261012.md)
relaciona cada peticion con su implementacion y pruebas. Backend completo:
1649 passed/82 skipped; tras la ruta de propiedad, 73 passed/1 skipped focales.
Frontend completo final: 888 passed, sin fallos ni omisiones. Operaciones:
tres ejecuciones de 20 casos sin fallos. Los tres controles de provenance detectan
el mutante. Processor completo: 999 passed/71 skipped y seis fallos por PyJWT
ausente de la imagen local; repetidos en imagen de pruebas corregida, los seis
pasan. No se afirma una unica ejecucion completa verde del processor.

Repeticion posterior completa en la imagen de pruebas corregida: 1005 passed,
71 skipped y cero fallos en 300.56 s, sin red y con codigo montado en lectura.
Se conserva el resultado anterior; las omisiones y la CI remota siguen separadas.

Navegador autenticado /ownership sobre imagen final y backend desechable:
acceso, consulta vacia con evidencia, recarga, rechazo de moneda/periodo
incompleto y cambio de tenant comprobados. SQL confirma cuatro mensajes
sin inserciones por entradas rechazadas. Sin gasto ni datos de otros stacks;
no acredita importes con datos cargados ni otra validacion de chat real.

El formulario real de JUP-037 queda disponible en `/ownership`, siempre con
consulta estructurada; `/assistant` abre solo el panel nuevo. Se conservan las
pruebas de sesion y aislamiento al adaptar sus rutas, no se eliminan por fallar.
Los modulos Python de producto estan formateados; imagenes y recursos offline,
preparacion local/CD, evaluador y controles documentales comprobados. Se preservan
advertencias de lint/build y ensayos fallidos. Sin nuevos gastos ni bateria real
completa repetida. Commit, CI por el SHA final y dictamenes independientes siguen
pendientes; el change automatico no se archiva ni se declara cerrado.

Ensayo de historial en stack mock aislado: envio, reapertura tras recarga,
renombrado desde panel/historial y borrado confirmados por navegador y SQL;
23 pruebas focales pasan. Recuperacion desde pgvector con embeddings mock
filtra el tenant y resuelve una cita sintetica; una fixture visual muestra
su fuente debajo a 13 px, con icono y sin extracto. No acredita decision RAG
ni generacion real del modelo. Detalles y limites en el informe de correcciones.

Ensayo real posterior: ingesta sintetica con embedding LiteLLM de 1536 dimensiones,
pregunta desde el panel, RAG automatico, cita sustentada y reapertura persistida
comprobados; coste adicional 0.005040712 USD. El entorno externo carece del archivo
de clave separada para resumen: memoria descriptor_mismatch y siguiente envio
bloqueado. No se declara memoria validada ni bateria completa repetida.

Configuracion del ensayo completada despues con la clave separada de resumen:
reintento deja cola idle y no bloqueada, sin gasto. Tras recargar/reabrir,
desaparece el aviso y Enviar se habilita al escribir. Dos mensajes y fuente
conservados; no se acredita compresion nueva ni refresco automatico sin recarga.

Ensayo posterior de compresion real con fixture de cinco pares y reintento
controlado: una llamada, resumen valido persistido, un par procesado y cuatro
recientes reservados; diez mensajes conservados, citas literales respaldadas.
Estados del servidor blocked=true durante la ejecucion e idle/no bloqueado al
final; envio habilitado al reabrir. Coste resumen 0.0008586 USD; total del ensayo
0.005899312 USD. No acredita umbral automatico ni una respuesta posterior con
ese resumen; pruebas grandes y bateria completa permanecen separadas.

Comprobacion posterior: una pregunta real recibe ese resumen en el manifiesto,
recuerda NEXO-LIMA y Equipo Delta, termina completed en un intento y conserva
doce mensajes sin duplicados al recargar/reabrir. Sin RAG ni citas externas en
esta consulta de historial. Advertencia tecnica sobre resumen con perdida de
detalle conservada; no acredita umbral automatico grande. Coste de la respuesta
0.0071139 USD; total asentado en OpenRouter 0.013013212 USD de 0.12 autorizados.
La matriz y la bateria completa siguen pendientes, sin nueva ejecucion.

Bateria real posterior ejecutada: 28 operaciones, 23 completed y 5 failed,
secuenciales y con un intento; 23 pares persistidos sin duplicados. Rechazos
native_tool_index en 005/022 y evidence_membership en 006/007/009. Ademas quedan
negativa de calculo 001, fuente omitida 003 y contradicciones 018/019/026.
No es un resultado favorable ni una validacion humana. Corpus: 52 fragmentos
reales de 1536 dimensiones; total registrado del ensayo 0.085089836 USD de 0.12.
Detalle: [bateria RAG automatico](../evidence/jup-035-auto-rag-battery-20261012.md).
Sin correcciones de producto ni repeticion de casos durante la tanda.

## Reconciliacion del checkpoint: 2026-10-13

Rama local codex/JUP-035-checkpoint-handoff, base 8d98ae5.
Corregidas colision de migraciones, envio de ownership_query, captura del
panel de anomalias y fixtures afectadas por la reconciliacion con develop.
Frontend completo 977/977; comprobacion final de migraciones 22/22 con
CockroachDB real. Compose mock y persistencia, renombrado y borrado comprobados.
La revision local asistida no conserva hallazgos abiertos de reconciliacion;
no declara aceptados los casos reales 005/006 ni sustituye CI o reviews humanas.
Resultados completos, fallos iniciales y repeticiones focalizadas:
[evidencia de reconciliacion](../evidence/jup-035-checkpoint-reconciliation-20261013.md).
Correcciones sin commit ni publicacion.

Correccion focal posterior: rechazo de resumenes sin temas/hechos y recuperacion
de consultas de estado con reintentos acotados. Ensayo real conserva AZ-6082 y
Equipo Abeto, desbloquea automaticamente y usa resumen mas cuatro pares en una
respuesta posterior; doce mensajes persistidos. No se repite bateria ni se cierra
JUP-035. Ver [evidencia de memoria](../evidence/jup-035-summary-empty-recovery-20261013.md).
