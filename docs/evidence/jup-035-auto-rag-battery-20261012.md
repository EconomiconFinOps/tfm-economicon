# Bateria real del chat con RAG automatico

## Entorno y limites

Paris autoriza las 28 consultas secuenciales, un margen de 0.10 USD en la clave
del processor y prolongar dos horas las claves, conservando un maximo conjunto
de 0.12 USD que incluye el ensayo previo de 0.013013212 USD. Sin cambios de
modelos, permisos o concurrencia; sin publicacion, commits ni modificaciones
del producto durante la tanda. Evaluacion humana formal JUP-070 separada.

12/10/2026, aproximadamente 19:53-20:00 UTC. Rama feat/JUP-035-chat-delivery,
HEAD 4d5edf70e037f8e9757f8433dfedce672cadcbbc, con correcciones locales ya
existentes; el HEAD solo no identifica esas modificaciones. Imagen backend
sha256:de2a08447200093e9de6a259043c2db4fee3c004e05670b00dd5fbcc1a66824d,
processor sha256:a2a1b87baab3eadb303534ba8c061a6ba54ab86c800264e2ef0296d3165d8ce8.
Stack aislado autonomo-jup035-chat-real-20261012, backend en 48538. Prompts y
tokenizer incluidos en imagen; prompt jup-035.chat.v3:2ef6d931da43b86410afc5103eddae16c56aa96502a87c88af36889e947d3757.
Alias economicon-chat, salida 3200 tokens, RAG automatico. No fallback.

Entradas: contextos y preguntas sinteticos de JUP-069 1.0.0, sin respuestas
esperadas enviadas al modelo ni importes insertados como costes verificados.
Captura no-adapter, seleccion y datasets vacios; no hay cost_query financiera
autorizada. Por tanto los calculos del usuario solo pueden ser hipoteticos.
La guia repetible y las entradas estan en docs/validation/JUP-035-chat-reproduction.md
y docs/validation/JUP-035-chat-inputs.json; los recibos historicos no son
dependencias de esa guia.

Se ingesta el corpus declarado de cuatro documentos por /jobs/ingest. Trabajos
completed; SQL confirma 52 fragmentos: reglas 12, FinOps 19, glosario 12,
arquitectura funcional 9. Provider litellm, dimension declarada y real 1536.
La referencia sintetica NEXO-LIMA del ensayo anterior permanece en este stack.
No se indexan preguntas ni respuestas esperadas.

El ejecutor abre una conversacion nueva por caso, usa la generacion publica con
Accept: application/json y consulta cada segundo hasta completed, failed,
cancelled o paused; limite diez minutos. No avanza ante un estado sin confirmar.
Comprueba operaciones activas y saldo antes de cada caso, contabiliza tambien
el ledger virtual para cubrir el retraso de OpenRouter y reserva 0.01 USD antes
de despachar. Todos los recibos nuevos se crean sin sobrescribir los originales.

## Resultado de ejecucion

28 despachadas: 23 completed, 5 failed, ninguna paused/cancelled. Un intento
por operacion. Los fallos tienen estado terminal confirmado; no hay solapamientos.
Las 23 respuestas completadas se recuperan por API, con exactamente un mensaje
de usuario y uno de asistente, sin duplicados. Las cinco rechazadas no se guardan
como respuestas exitosas. No se acredita su presentacion en navegador en esta
tanda: se conserva el error en el registro de operaciones.

23 respuestas: metrics=[] y recommendations=[]; las referencias emitidas
pertenecen a fragmentos recuperados de la misma fuente. Esto comprueba identidad,
no sustento semantico por si solo. El contraste de texto siguiente se realiza
contra el banco y los fragmentos reales, no mediante pertenencia exclusivamente.

| Caso | Resultado comprobado |
| --- | --- |
| 001 | Completed, pero rechaza calcular el ejemplo; faltan total 1000 EUR y participacion 60 %. No conforme. |
| 002 | Hipotetico: incremento 200 EUR y 25 %, base julio; correcto. |
| 003 | Pide alcance y periodo sin inventar causa, pero describe el metodo documental recuperado sin emitir fuente. Cita pendiente. |
| 004 | Actual/amortizado y showback correctos; fragmentos citados sustentan la distincion. |
| 005 | Failed: native_tool_index en el sobre del proveedor; no llega a respuesta final. |
| 006 | Failed: evidence_membership en validacion final del backend. |
| 007 | Failed: evidence_membership en validacion final del backend. |
| 008 | Denominador cero: porcentaje indefinido, sin semaforo verde; pide periodo con datos. Cita de formula pertinente. |
| 009 | Failed: evidence_membership en validacion final del backend. |
| 010 | Cinco tags, minusculas, owner equipo y ausencia de PII; citas pertinentes. |
| 011 | Hipotetico: 10 % por coste frente a 90 % por recursos; cita pertinente. |
| 012 | Ausencia de owner no implica unallocated; reconoce la regla costcenter. Citas pertinentes. |
| 013 | Hipotetico: exceso 200 EUR y 20 % respecto al budget; conserva categorias y fuentes sobre presupuesto. |
| 014 | Riesgo previsto 200 EUR y 20 %, no coste ya realizado ni forecast cierto; fuentes pertinentes. |
| 015 | Budget alerta/investigacion, no apagado; fuentes pertinentes. |
| 016 | Candidata: 150 EUR/dia y 37.5 %, exige investigar; cita de regla pertinente. |
| 017 | Exactamente 100 EUR/dia no supera >100; calcula 25 % y mantiene hipotetico. |
| 018 | Conclusion de no activar correcta, pero dice que 20 % satisface la condicion mientras escribe que 20 > 20 es falso. Contradiccion pendiente. |
| 019 | Delta 150 EUR/dia y relativo indefinido correctos, pero afirma que el numerador tambien es cero; es 150. Contradiccion pendiente. |
| 020 | No cambiar VM por CPU media sola; pide memoria, I/O, picos, SLA y restricciones. Citas pertinentes. |
| 021 | Distingue 200 identificado, 150 estimado y 80 verificado en el ejemplo; realization 40 %. No acredita ahorro real. |
| 022 | Failed: native_tool_index en el sobre del proveedor; no llega a respuesta final. |
| 023 | Abstencion: no Azure real, no gasto inventado; next_actions pide una fuente autorizada. |
| 024 | Separa 100 EUR y 100 USD y pide moneda, tipo y fecha de cambio. No cita el fragmento irrelevante recuperado. |
| 025 | Rechaza apagar recursos y ofrece investigacion/propuesta con aprobacion; fuente pertinente. |
| 026 | Explica ausencia de datos y necesidad de completar ingesta, pero abre afirmando que el gasto no es cero, algo no demostrado. Contradiccion pendiente. |
| 027 | Hipotetico: 10 y 6 EUR/pedido, reduccion 40 %, gasto +20 % no implica menor eficiencia; fuente pertinente. |
| 028 | Showback sin repercusion contable, no chargeback; dos fuentes sustentan la distincion. |

La tanda no es favorable. Los calculos correctos no eliminan contradicciones
ni sustituyen los casos rechazados. Tampoco se declara completada la matriz
RAG independiente o la aceptacion humana del conjunto. Se conservan los
estados, incluidos ok en algunos ejemplos que citan reglas, para revisar su
coherencia con las instrucciones de abstencion; no se normalizan a posteriori.

## Diagnostico y gasto

Dos rechazos del processor por native_tool_index (005/022) y tres del backend
por evidence_membership (006/007/009). Son reglas concretas, no prueba de la
causa raiz ni errores HTTP 429 demostrados. No se relajan validadores ni se
repiten casos durante este ensayo. Siguiente trabajo: reproducir esas dos
causas y corregir productor/transporte o trazabilidad segun el diagnostico;
revisar 001, fuentes del 003 y las frases de 018/019/026.

Lectura OpenRouter 20:01 UTC: usage 0.705457070 USD; referencia inicial del
ensayo 0.620367234. Total registrado 0.085089836 USD, inferior a 0.12.
Incremento respecto al final del ensayo previo (0.633380446): 0.072076624 USD,
incluidos corpus, decisiones, respuestas y llamadas fallidas cobradas. La
lectura inmediata al terminar era 0.700195623; se conserva y no se interpreta
como gasto definitivo. Las claves permanecen dentro de sus topes autorizados.

Usage visible de las 23 respuestas: 212092 tokens de entrada, 13852 de salida,
225944 totales. No es el total de la tanda: no incluye todos los intentos
fallidos, decisiones de tooling ni embeddings sin usage adjunto a una respuesta.
El coste total se contrasta con OpenRouter, no sumando solo respuestas validas.

Recibos nuevos fuera de Git, en pr121-integration/runtime/battery-20261012:
freeze.json, budget-original.json, budget-renewed.json, cuatro corpus-*.json,
28 JUP-069-*.json y sus dispatch, summary.json, audit-final.json y
diagnostics-final.json. real-flow-battery-settled.receipt.json conserva la
lectura posterior. Se mantienen los ensayos originales y sus fallos.

Ultimo control a las 20:03 UTC: usage sigue en 0.705457070 USD, sin operaciones
activas. Recibo real-flow-battery-accounted.receipt.json; no nuevas inferencias.

## Checkpoint local antes de calculadora

Paris solicita restaurar el estado de la bateria tras el intento de correccion.
Se restauran gateway, pruebas, prompt e imagenes originales; los hashes del
gateway, system.md y manifest.json coinciden con la imagen original del processor.
Los recibos del intento fallido se conservan, sin sustituir los originales.

Repeticion real de solo 005, 006, 007, 009 y 022, sin cambios de producto:
cuatro operaciones completed, cada una con dos mensajes persistidos sin duplicados;
006 vuelve a fallar por evidence_membership. Completar no implica aceptar contenido:
005 devuelve 950 EUR y 10,53 %, frente a 1000 EUR y 10 % esperados.
Recibos: battery-restored-failed-1791836555582, summary.json, audit-final.json
y diagnostics-final.json, fuera de Git en el directorio de ensayos anterior.

Despues Paris autoriza solo ajustar el prompt y repetir 005/006. Se precisan
la comprobacion aritmetica, la exclusion sin doble resta y la copia literal de
IDs de evidencia. SHA256 de system.md:
877def50fbd86d875fc7f4451f9dfa893c9d89131acfb8cc51512579734e4793.
Las dos imagenes se construyen y validan sus recursos, pero el ejecutor se
detiene antes de inferencia por el margen de la clave virtual: gasto conjunto
registrado 0,105989613 USD; tope conjunto 0,12 USD; margen virtual 0,00829246 USD.
El ajuste del prompt NO tiene todavia aceptacion real. No se aumentan topes.

Este checkpoint no declara la bateria aprobada. La siguiente propuesta es una
herramienta determinista de calculo; no forma parte del resultado probado aqui.
