# Chat conversacional - JUP-035

Actualizado: 12/10/2026. Este tema describe la entrega local, no un merge
ni una validacion humana. Los responsables y el estado oficial siguen en Trello.

## Recorrido vigente

La interfaz assistant-ui usa operaciones `/assistant/.../generations`.
Backend autentica al propietario, valida el contexto y consulta los costes.
Processor decide con `auto-documentation-v2` si necesita la herramienta RAG;
backend ejecuta la busqueda solicitada filtrada por tenant. Una segunda llamada
produce la respuesta estricta, tambien cuando no se solicita busqueda. La respuesta validada, las
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
