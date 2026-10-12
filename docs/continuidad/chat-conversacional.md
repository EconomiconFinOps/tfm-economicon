## Backend corregido y suite verde — 12/10/2026

Mismo origen JUP-035/PR120 y chat `01a1302b-c7a5-7c71-ba85-4d2391f8ff33`.
El usuario pidió corregir 8 FAIL/3 ERROR y autorizó la validación por el agente.
Sobre `8294c4875b7cfdbefbf240a0dcbfab618ee96ed5`, suite backend completa Linux:
**1671 PASS/47 SKIP, cero fallos/errores, exit 0, 285.01 s**. OpenSpec67/67.
Se resuelven JWT generados en colección que caducaban, DTO pgvector obsoleto,
probes SQL ligados a datos smoke y carrera SQL/RAM real de cierre de streaming.
Seis regresiones deterministas cubren evento publicado antes/después de la lectura
y cierre sin duplicados para éxito/fallo. Summary SQL usa fixtures propios y pasa
las tres comprobaciones nativas; ya no está pendiente en el backend.

Revisión y validación asistidas atribuidas a Codex, autorizadas por el usuario;
no se inventan dictámenes de otras personas. Este corte sustituye el estado
backend no verde y la espera de revisión humana del corte anterior para este
parche offline. Las47 omisiones de otras integraciones se detallan en los logs;
proveedor, navegador y full28 siguen pendientes, sin autorización de gasto nueva.
Ver [informe](../evidence/jup-035-auto-documentation-20261012.md) y `backend-green/`
del paquete externo. Siguiente: integrar el parche y acordar aceptación real.
Sin push, mensajes, merge, despliegue ni cambios en la rama de Paris.

## Antecedente: parche incremental auto de PR120 — 12/10/2026

Origen: «Implementa # Orden de trabajo — JUP-035 / PR120», chat
`01a1302b-c7a5-7c71-ba85-4d2391f8ff33`. Orden externa del espacio:
`materiales/07-evidencias/JUP-035-PR120-orden-trabajo.md`.

Checkout propio `tfm-economicon-jup035-auto`, rama
`fix/JUP-035-auto-documentation`, derivado de PR120
`f63c15031b65c99f1da149e867675ff771d3c1dd`. HEAD/comentarios/reviews reconfirmados
el 12/10: mismo SHA, sin comentarios ni reviews. No modifica la rama de Paris.

Implementado `auto-documentation-v2`: decision privada sin response_format,
cero/una busqueda y final estricto none, maximo dos generaciones y un plazo
comun. Texto de decision descartado; contexto financiero y validadores intactos.
Hashes, descriptor, prompt y OpenSpec coordinados; contrato antiguo rechazado.
Reproduccion original: cuatro fallos funcionales y tres rechazos correctos con
SSE sintetico. Demuestra rechazo propio, no incompatibilidad del proveedor.

[Informe y pruebas](../evidence/jup-035-auto-documentation-20261012.md): commit de
codigo `5dd15972e53afa1668d80ba5d75c07c821d7a61b`; aporte local terminado.
Processor focal final 130 PASS, backend 62 PASS/15 SKIP, frontend 882 y API de
costes 81 PASS; build 4/4, OpenSpec 67/67 y controles de gobernanza pasan.
Campañas amplias no verdes: processor 13 FAIL/4 ERROR reproducidos en base;
backend 147 FAIL reproducidos en base y una carrera de fixture corregida.
Los conteos solapados no se suman y no equivalen a una bateria real de 28.
Sin presupuesto nuevo autorizado: matriz real, full28 y aceptacion en runtime
pendientes. El usuario autorizó posteriormente copia y pruebas aisladas Linux:
SHA probado 9829d82, processor completo 1002 PASS/71 SKIP, backend focal 77 PASS
incluidos 15 SQL CockroachDB. Backend amplio 1654 PASS/47 SKIP/8 FAIL/3 ERROR;
un FAIL pgvector reproducido en base, otros siete no repetidos en focal51PASS,
probes summary SQL pendientes por entorno específico. Ver informe para límites.
Logs/receta en linux/ del paquete. Contenedores e imagen temporales retirados;
archivos en /tmp/economicon-jup035-auto-01a1302b conservados como evidencia.

Siguiente: Paris revisa el parche separado; resolver entorno/presupuesto para
matriz real, probes summary SQL/navegador y full28 sobre un SHA final.
Revision Alejandro y validacion Lucia siguen separadas y pendientes. Sin mensajes,
reviews publicadas, push a Paris, merge, despliegue ni cierre de tarjeta.

## Cierre documental de entrega — 12/10/2026

RAG/batería incorporados por PM en feat/JUP-035-chat-delivery,
checkpoint42e9ff073bcc3380aeb9b8bda1315a092cbbc4b0 sobre2814403 y develop8035a3d.
La aceptación interna real010 posterior completó required -> recuperación tenant
-> continuación autenticada -> respuesta estricta en16,703s, un par persistido
y reapertura con citas. Dos LLM y un embedding reales; corpus sintético SQL1536.
No full28 actual ni reviews humanas ni CI del checkpoint final acreditadas aquí.
Original1130 SHA46fc8e44 preservado y PM comunicó PASS11:06:45UTC precommit;
nueva referencia PM y revisión/revalidación afectada pendientes tras editorial.
Siete casillas históricas conservan límites explícitos. JUP-036 continúa en espera.
Ver [evidencia final](../evidence/jup-035-required-tool-retrieval-20261012.md) y
[conciliación de entrega](../evidence/jup-035-delivery-reconciliation-20261012.md).
Los cortes siguientes se conservan como historial, no como estado actual.

## Correccion recuperacion acotada conninfo (12/10/2026)

ProgrammingError reproducido antes de SQL: context=AdaptersMap entregado por
SQLAlchemy se pasaba a make_conninfo, que solo admite opciones libpq. Se filtra
context exclusivamente en la copia usada para verificar host/puerto; conexion
real conserva context identico, hostname, TLS, hostaddr, deadline y cancelacion.
El backend existente recupera dos chunks del tenant correcto con la correccion
en un proceso desechable SQL solo lectura/vector sintetico, no un RAG completo.
ChatContext conserva retrieval_unavailable publico y registra etapa/causa cerrada
con operacion/intento autenticados propagados al worker, sin claves ni contenido.
66 PASS/5 SKIP en suites afectadas; SKIP requiere JUP086_VECTOR_TEST_URL.
Cuatro mutaciones detectadas y guards separados conformes. No modelo, build,
restart, admin ni Git. 429 previos siguen sin atribucion fiable; no limites nuevos.
La aceptacion anterior fallo en corpus/citas aunque persistio un par; no se
reclasifica ni se declara aceptacion actual. Restante .020865394 < reserva .025:
parent necesita resolver presupuesto antes de otra operacion real.
Ver [evidencia de la correccion](../evidence/jup-035-required-tool-retrieval-20261012.md).

## Correccion envelope nativo (12/10/2026)

SSE nativo: null representa ausencia de fragmento; id/type son metadatos
idempotentes si se repiten identicos. Nombre/argumentos siguen siendo fragmentos
concatenados y la llamada final exige nombre exacto, id valido y query acotada.
Contradicciones, tipos invalidos y limites siguen fallando cerrado, ahora con
rule_code estatico solo para errores nativos. Los diagnosticos previos no
reciben nuevos campos. No se registran valores ni mensajes de excepcion.
59 pruebas gateway/resources PASS y cuatro mutaciones detectadas offline.
No se atribuye el fallo real a nulls sin evidencia del campo; el recibo anterior
envelope/ValueError y su coste .002291962USD quedan conservados. Presupuesto
parent: .262898470 de .29, restante .027101530, sin consumo del desarrollador.
Requiere revision independiente y una aceptacion focal, no bateria completa.
Ver [evidencia y limites](../evidence/jup-035-required-tool-envelope-20261012.md).

## Correccion SQL deadline (12/10/2026)

El deadline nativo no termina solo wait_for: conexion propia psycopg/SQLAlchemy
asincrona, NullPool por peticion, timeout SQL restante y cancelacion/cierre del
driver acotan la consulta/lectura real. Hostaddr procede del driver ordinario ya
autenticado en verify_dimension/ping/consulta, nunca de DNS del chat; hostname y
TLS permanecen. Sin peer confiable se devuelve retrieval_unavailable saneado,
sin conexion extra para resolver ni fallback de direccion obsoleta.
54 pruebas afectadas PASS y mutaciones focales detectadas; son doubles, no
confirmacion de cancelacion PostgreSQL remota. Requiere revision independiente
afectada y una aceptacion real, sin ampliar presupuesto o repetir bateria.
Ver [evidencia y limites](../evidence/jup-035-required-tool-dbdeadline-20261012.md).

## Checkpoint previo required-documentation-v1 (12/10/2026)

Una operacion/intento y un dispatch privado: primera llamada required con
search_documentation estricto; backend recupera despues usando el tenant
autenticado y filtros existentes; envia extension correlacionada por HMAC al
processor pendiente; segunda llamada none conserva tools/esquema y termina
con FinOpsResponse 1.0. No nuevas dependencias, migraciones o rutas publicas.
Deadline comun para embedding/recuperacion/espera y modelo; cancelacion impide
continuacion y persistencia. Contexto inicial/hash congelados. Solo evidencia
billing validada habilita metrics; corpus no cambia financial_metrics_allowed.
El modo mock-direct-v1 explicito conserva el arranque sin gasto.

Green offline y cinco mutaciones focales detectadas; fixture-correction en fase
tests-only separada, sin relajar aserciones ni borrar los FAIL originales.
Backend y processor cargan el mismo bundle y cuentan la continuacion igual.
Falta revision independiente y caso real con recuperacion/citas/persistencia y
reapertura; no se afirma integracion real validada ni full28 ultima revision.
Ver [evidencia local y limites](../evidence/jup-035-required-tool-offline-20261012.md).

## Corte historico — archivo autorizado 11/10/2026

OpenSpec archivado por autorización expresa de Paris. Rama codex/JUP-035-e5-full-validation reconciliada con develop 3b8e952, HEAD previo al archivo 8886494. La compresión y el consumo por una respuesta posterior ya tienen evidencia histórica satisfactoria; no quedan pendientes globales por no repetirse en el último ensayo de Compose. Véase [entrega, evidencias y límites](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/archive-delivery.md). Los cortes anteriores se conservan como historia; CI remota, publicación y gates humanos no se declaran cumplidos.

# Chat conversacional

## Cierre funcional focal (12/10/2026)

Cierre funcional focal comunicado por parent (12/10): REVIEW_PASS de l con
control independiente1314; VALIDATION_PASS SOLO024l, completed en7.86s y
un intento. Conserva100EUR y100USD separados, pide moneda/tipo/fecha, sin
formula, statusno_data y evidence/citations/metrics vacias; un par persistido.
019 y022 aceptados en j sin repetirlos. Las tres correcciones quedan aceptadas
mediante ensayos focales, conforme a Paris: no nueva full28, no28PASS en ultima
revision ni evaluacion formal JUP-070. Sin publicacion.
Ultimo consumo.003271992USD; acumulado.225790862 del TOTAL.25,
restante.024209138; baseline.338851568 y upstreamusage.564642430.
024kFAIL por cita y guard historicoFAIL conservados, sin recalificarlos.
Ver [cierre focal final](../evidence/jup-035-battery-final-focal-acceptance.md).
Los estados pendientes siguientes son cortes historicos.

## Corte vigente semantic3200l-citationstatus

Corte vigente semantic3200l-citationstatus (12/10):019 y022 aceptados;
parent comunica024k completed pero FAIL por cita KPI no pertinente, con
formula/aritmetica PASS. El productor determina sustento antes de status y no
elige ok/partial para rellenar citas. Ejercicios sin evidencia financiera ni
corpus sustentante conservan answer util, estado no accionable y evidence vacia.
Instrucciones019/022 y conversion k intactas; no borrado posterior ni relajacion.
Offline22PASS y mutacion detectada. Revision independiente y SOLO024 real
pendientes; no full28 actual aceptada ni JUP-070 formal.
RondaTOTAL.25USD, gasto comunicado.222518870, restante.027481130,
baseline.338851568 intacto. No llamadas/admin por desarrollador.
Incidente historico de integridad k: snapshot parent anterior a ultima escritura
documental autorizada; guardFAIL conservado, no atribuido al revisor ni calificado
PASS. Nueva revision requerida sobre entrega con TODOS los archivos terminados.
Ver [evidencia l](../evidence/jup-035-battery-semantic3200l-citationstatus-offline.md).
Los cortes siguientes son historicos.

## Corte vigente semantic3200k-currencylimit

Corte vigente semantic3200k-currencylimit (12/10): parent comunica focal j
019 PASS,022 PASS,024 FAIL por formula de conversion con destino/direccion
ambiguos; las citas irrelevantes del caso anterior ya no aparecen. Paris acepta
019/022 y pide corregir y repetir SOLO024, sin otra full28 ni retest de los dos.
El productor pide destino, fecha y direccion del cambio antes de formular una
suma con destino desconocido; los ejemplos hipoteticos declaran origen/destino
y unidades del cambio, convirtiendo cada importe necesario sin inventar tasas.
Instrucciones019/022 intactas. Local22PASS, mutacion detectada, OpenSpec63/63 y
conteo efectivo identico; no acreditan cumplimiento semantico del modelo.
Revision independiente y real024 pendientes. Historico full28i25PASS/3FAIL
conservado, sin afirmar full28 aceptada en esta revision ni JUP-070 formal.
RondaTOTAL0.25USD, gasto comunicado0.220203420 y restante0.029796580,
baseline0.338851568 intacto; el desarrollador no realiza llamadas ni administra.
Ver [evidencia offline k](../evidence/jup-035-battery-semantic3200k-currencylimit-offline.md).
Los cortes siguientes se conservan como historial.

## Corte vigente semantic3200j-all3

Corte vigente semantic3200j-all3 (12/10): full28i completo 28 operaciones en un
intento, con aceptacion independiente 25 PASS/3 FAIL (019,022,024). Paris
sustituye la aceptacion provisional de limitaciones por corregir los tres:
unidad completa junto al resultado en answer, condiciones contractuales
solo desde input/corpus autorizado y citas de afirmaciones realmente expresadas,
no instrucciones internas ni aritmetica del usuario. Los FAIL historicos se
conservan; no son exenciones finales ni criterios debilitados.
Checkpoint local estable: 22 pruebas PASS, tres mutaciones detectadas y recursos
contabilizados identicamente. Revision independiente y ensayo real focal de los
tres pendientes; estas pruebas locales no acreditan cumplimiento semantico.
Paris no exige otra full28 para esta entrega si la aceptacion focal es correcta;
no se declara 28 PASS en la revision actual ni evaluacion formal JUP-070.
Presupuesto TOTAL0.25USD, baseline0.338851568, gastado0.212688338 y
restante0.037311662 segun el corte comunicado del ensayo i, sin nuevas consultas
por el desarrollador ni cambios de topes.
Ver [evidencia offline j-all3](../evidence/jup-035-battery-semantic3200j-all3-offline.md).
Los cortes siguientes son historicos, no el estado vigente.

## Correcciones de bateria local (11/10/2026)

### Corte real focal semantic3200i (12/10/2026)

Parent comunica revision tecnica PASS y validacion independiente PASS del nuevo
013 real: completed en un intento, runnerexit0, status insufficient_data con
evidence[], metrics[] y recommendations[]. Calcula exceso hipotetico200EUR/20%,
sin inventar citas ni confundir coste actual con prevision. Scope canonico coherente
y un par usuario/asistente persistido sin duplicados. Gateway acepto el esquema
en este ensayo por la ruta intacta; no se prueba la rama accionable real ni la
aplicacion futura de anyOf. Full28i y evaluacion humana JUP-070 siguen pendientes.

Control independiente parent:1310archivos sin diferencias, SHA256
B3605F05C07887C40EF74B190E205C9A52FDB23FE302D79032872419BFF53853.
Snapshot guardado2026-10-12T01:03:35.780975Z: usage0.493216296USD, baseline0.338851568,
gastado0.154364728 y restante0.045635272 deTOTAL0.20USD. Incluye intentos fallidos
anteriores; no reinicia presupuesto ni confunde saldo upstream con permiso de ronda.
Sin nuevas llamadas hasta presupuesto suficiente y autorizacion de expiry para
full28. Ver [anexo focal i](../evidence/jup-035-battery-semantic3200i-focused013.md).
El fallo013h y el corte offline que siguen se conservan como historia.

### Corte offline historico semantic3200i (12/10/2026)

Paris autorizo dos ramas anyOf del esquema privado tras diagnosticar013:
001-012 completadas entre las dos tandas h,013 fallida en un intento con
actionable_requires_evidence del processor y finish_reason stop. No atribuir
truncacion ni afirmar el estado exacto ok/partial no conservado en el diagnostico.
El ensayo se detuvo por terminal_cost_unverified, sin despachar otra consulta.

Cada rama conserva el objeto base completo y referencias a los mismos $defs.
ok/partial exigen evidence minItems1; los otros cinco estados admiten evidence[].
La restriccion financiera autenticada, scope del servidor y guard publico no
cambian. No hay citas artificiales, filtros de estados ni reparacion postrespuesta.
Los manifiestos v3 verifican el hash privado nuevo en ambos servicios; el publico
permanece baf067ac8fe35a693848012c5358cb1c6ab8883ebaa02a63166b00f7d8298018.

Offline:25 backend y49 processor PASS, dos mutaciones minItems retirado detectadas,
OpenSpec63/63. Las variantes financieras tienen1633 tokens de esquema y el
ejemplo sintetico suma8919 con margen1024 y salida3200, identicos entre servicios.
No son los tokens de una llamada real ni prueban soporte anyOf del endpoint.
OpenRouter documenta soporte por endpoint y strict dependiente del proveedor;
soporte response_format en LiteLLM no acredita este keyword en GLM-5.2/DeepInfra.
Si se rechaza o incumple el esquema, detener y decidir, sin cambiar routing/modelo
ni fallback. Revision independiente y ensayo parent013 pendientes, full28 no cerrada.
PresupuestoTOTAL0.20USD intacto; no inferencia/admin ni modificaciones Git locales.
Ver [expediente offline i](../evidence/jup-035-battery-semantic3200i-offline.md).
Los cortes anteriores se conservan sin sobrescribir como historia.

Ultimo corte semantic3200h comunicado y documentado por coordinacion12/10:
revision tecnica PASS; ensayo real015/021/023 runnerexit0, tres operaciones
completadas en un intento y validacion independiente3/3PASS. 015 investiga
condicionalmente al superar umbrales, sin inventar incidencia. 021 conserva
200identificados,150implementadosestimados y80verificadosEUR/mes y40% como
ejercicio hipotetico, sin citas inventadas. 023 no deriva hoy de captured_at,
solicita fuente autorizada, periodo y zona. Tres pares usuario/asistente persistidos
sin duplicados; cuatro citas con procedencia y sustento verificados. No se
alteraron marcadores originales del auditor para conseguir el resultado.
Ver [evidencia focal h](../evidence/jup-035-battery-semantic3200h-focused.md).

Snapshot administrativo2026-10-12T00:23:12.429612Z: usage0.462428368USD menos
baseline fijo0.338851568 = gastoTOTALronda0.123576800USD, margen0.026423200 de
allowance0.15USD. Incluye ensayos previos, no solo estos tres. No ampliacion.
No se ha ejecutado full28h: el corte anterior26PASS/2FAILfinancialschema y los
tres focales h NO equivalen a28/28de una revision final. Falta full28h y permiso
presupuestario suficiente; evaluacion humana JUP-070 y cierre global separados.

Corte focalg comunicado por coordinacion: 2/3 PASS (015 investigacion condicional
y 023 referencia temporal); 021 corrige citas pero omite el contraste entre
importe implementado estimado y verificado. No es un PASS de toda la bateria.
semantic3200h conserva las reglas de g y exige conservar cada importe relevante
con unidad/categoria y contrastar cuantitativamente ahorro implementado estimado
frente a verificado, sin sustituirlo por enumeracion generica aunque el ratio
final sea correcto. Importes hipoteticos siguen solo en answer, con assumptions
y limitations, sin metrics financieras nuevas. Pruebas de instrucciones/hash no
acreditan cumplimiento semantico real; revision y focal021 pendientes.
Saldo de ronda comunicado0.032521687USD, TOTAL0.15USD sin ampliacion; permite
un ensayo focal conservador, no una tanda completa comparable. No nuevas llamadas
realizadas por este ejecutor; cortes de fallo y manifiestos previos conservados
en evidencia externa, sin reescribir el archivo historico v2.

Corte real historico financialschema (12/10): 28 operaciones completadas en un intento, con un par
usuario/asistente por conversacion y sin duplicados en los recibos. Aceptacion
independiente: 26 PASS/2 FAIL (015 omite investigar umbrales, 021 cita fragmentos
sin sustento), mas interpretacion temporal de 023 pendiente. Dos tandas del mismo
producto terminaron exit1 por contabilidad atrasada fuera de la espera; no se
declaran ejecuciones con exit0. Evidencia externa financialschema-stale60-assessment.md
conservada por el coordinador; no sustituye evaluacion humana formal JUP-070.

semantic3200g refuerza solo instrucciones generales: next_actions condicional de
investigacion al explicar alertas, sin inventar incidencias; sustento individual
del fragmento exacto de cada cita, incluidos vecinos; captured_at no autoriza
resolver hoy ni fijar periodo financiero. Sin referencia temporal inequivoca,
conservar expresion relativa y pedir periodo/zona cuando sean necesarios. No hay
reloj nuevo, campos privados nuevos ni filtros semanticos posteriores que borren
citas. Modelo, salida3200, plazos, autoridad financiera y FinOpsResponse1.0 intactos.
Pruebas locales de instrucciones/manifiesto no acreditan reparar los casos reales;
nueva revision y aceptacion pendientes, sin marcar cierre ni ampliar presupuesto.
Ronda acumulada0.110735883USD del total0.15; restante0.039264117USD segun el corte
administrativo comunicado, no saldo actualizado por este ejecutor. No iniciar
otra tanda comparable completa con ese margen y la reserva actual.

El bundle de chat activo pasa a v3; v2 y el archivo OpenSpec historico permanecen
intactos. El servidor fija suscripciones desde la seleccion canonica (sin ella,
lista vacia), rechaza mas de 20 distintas con 422 antes del intento y conserva
FinOpsResponse 1.0. Los calculos hipoteticos del usuario solo van en answer con
supuestos y limitaciones, sin metrics financieras inventadas. El diagnostico
backend registra una regla cerrada sin contenido. Salida de chat: 3200 tokens por
defecto y como maximo, autorizados directamente por Paris el 11/10/2026;
sustituye el procedimiento inicial de 1600 y escalado tras truncacion.
Ingestion y compresion no cambian.

Ajuste minimo posterior autorizado: chat recupera hasta 20 candidatos con los
mismos filtros; conserva sus resultados principales y agrega vecinos inmediatos
del mismo documento solo si estan en ese conjunto. No hay SQL nuevo, reindexado
ni cambios del corpus. Las citas mantienen IDs reales y el contexto declara el
limite y los vecinos omitidos por capacidad, descontando evidencia financiera.
La continuacion no esta garantizada si queda fuera de los candidatos. El prompt
refuerza completitud de tagging (owner equipo y ausencia de PII), abstencion con
reglas fragmentadas y diferencias absolutas/relativas solo para comparaciones
solicitadas de importes, sin division por cero ni comparaciones adicionales con
umbrales. Distingue variacion relativa y puntos porcentuales cuando se solicitan.

Reparacion posterior a REVIEW_FAIL autorizada: el scope del servidor aplica strip
y dedup despues de normalizar, alineado con StringConstraints del processor.
Blancos se rechazan con 422 antes del proveedor; la captura original permanece
sin reescribir. Limites de entrada 1..256 caracteres y 20 IDs normalizados distintos
sin cambios. El fallo y la evidencia de revision anteriores se conservan; esta
reparacion local no convierte la revision independiente en aprobada.

Evaluacion externa final3200: 28 operaciones completas y persistidas, pero
19 aceptadas y 9 rechazadas semanticamente. Paris autorizo reparar las reglas
generales de ratios indefinidos, ponderaciones, investigacion, riesgo SLA,
tipos de ahorro, fuentes autorizadas, conversion y sustento de citas. No se
alteran corpus, retrieval, modelos, contrato ni evaluador. No hay autocitado
backend: se muestran solo evidencias que el modelo devuelve; que sus IDs sean
validos no prueba que el contenido sustente la respuesta. Nuevas pruebas de
prompt no acreditan por si solas corregir esos nueve casos reales. La evidencia
original de fallo se conserva y la repeticion/aceptacion sigue pendiente.

Checkpoint semantic3200c: tras la primera repeticion, el ratio indefinido ya se
explica correctamente, pero faltaba pedir un periodo con datos elegibles. El
prompt ahora solicita ese periodo y su consulta autorizada, no solo otra consulta.
Pruebas locales de instrucciones e integridad no acreditan aun la respuesta real.
El ejecutor externo espera confirmacion contable cada dos segundos hasta 60,
exigiendo incremento que cubra el coste informado con tolerancia USD 0.000001.
Si no se confirma, detiene la tanda; no interpreta el retraso como coste cero.

Aceptacion independiente de focused9: 6 PASS/3 FAIL (011, 016 y 020), mas cita
adicional no pertinente en 021 bajo el criterio global de sustento. El fragmento
business-rules:chunk5 si contiene SavingsRealization; la hipotesis previa de que
era solo tagging se descarta. semantic3200d refuerza reglas generales: ambas
tasas de tagging con sus denominadores cuando existen recuentos y costes,
investigar y confirmar causa/esperabilidad de anomalias candidatas, consecuencias
concretas del rightsizing sobre rendimiento/servicio/SLA, y retirar cada cita
extra sin sustento. Pruebas locales no acreditan corregir esos casos reales.
011 siguio fallando en una repeticion posterior; no se ha confirmado su causa.
semantic3200e elimina la condicion ambigua de medidas solicitadas: con costes y
recuentos elegibles, calcular primero cobertura por recursos y despues por coste,
explicando diferencia aunque la pregunta solo mencione costes. La comprobacion
real de esta aclaracion queda pendiente, sin mas tuning automatico si falla.
Aceptacion mixta posterior: 8 PASS/1 FAIL; 011e, 016d y 021d aceptadas, 020d
omite pedir restricciones de negocio. semantic3200f exige en next_actions el
checklist completo de utilizacion CPU/memoria/IO/picos, rendimiento, SLA,
crecimiento y restricciones de negocio antes de cualquier ajuste. No basta
que los requisitos aparezcan en extractos de evidencia. Repeticion real pendiente;
si vuelve a omitir un requisito, detener esa parte y pedir decision.

Full28f detenido tras cinco completadas y 006 fallida por financial_metric_unverified;
el ejecutor no despacho otro caso. Decision humana posterior: esquema privado de
proveedor limita metrics a [] cuando no hay autoridad financiera del servidor.
Checkpoint financialschema3200 deriva financial_metrics_allowed solo de metricas
creadas tras consulta billing por tenant, parseo y coherencia del servidor. Es un
booleano obligatorio del contexto privado canonico, no un campo publico. Coste
cero valido habilita metrics; consulta vacia/fallida, corpus o pantalla no las
habilitan. Streaming usa esa variante y ambos lados contabilizan el esquema
efectivo. Politica server-billing-authority-empty-metrics-v1 en manifiesto v3.
FinOpsResponse 1.0 y guard final quedan intactos; no se borran metrics recibidas.
Pruebas locales no acreditan repetir 006 ni completar/aceptar las 28 consultas.

Tanda externa affected-3200: 13/13 operaciones completas en un intento, pero
007 y 010 requieren correccion semantica por reglas fragmentadas/incompletas;
014 omite la diferencia relativa en answer. No se ha repetido esa tanda ni las
28 completas. 016, 019 y 024 requieren comprobar donde aparece cada requisito.
Los estados ok en ejercicios con corpus realmente usado conservan el contrato
actual, sin convertir esos calculos en costes verificados; la valoracion semantica
de 005, 011, 014 y 027 sigue pendiente, sin nueva politica de estado.

Reproduccion externa sobre diagnostic1: 005, 007 y 011 rechazados por
financial_metric_unverified; 021 completo esta vez, causa original no demostrada.
Estas observaciones no acreditan todavia las 28 consultas corregidas, ni reviews
humanas, CI remota o cierre global. El runner de ensayo es externo al producto,
secuencial y conserva las evidencias anteriores.

Verificacion documental: 2026-10-11. Identificador: JUP-035.
La continuidad no sustituye alcance y roles de Trello ni las reviews humanas.

## Referencias

- [Correcciones locales de CI](../evidence/jup-035-ci-corrections.md): tokenizer
  declarado, prueba portable, plugin de lint compatible, fixtures HMAC y
  recuperacion de operaciones desde conversaciones sin mostrar solicitudes;
  confirmacion remota pendiente.
- [Cambio OpenSpec](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/proposal.md).
- [Integracion con Compose](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/compose-chat-design.md).
- [Correccion del plazo de compresion](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/summary-timeout-correction.md).
- [Arranque y configuracion](../../README.md).
- Commit de entrega previo a reconciliar: `01bfb7ba1361467b71301aeb08d9a6942c5e76cd`.
- Base incorporada en la reconciliacion local: develop `3b8e952`.

## Entrega y comprobaciones anteriores a la reconciliacion

Los servicios empaquetan locks, prompts y tokenizer. El migrador backend termina
antes del arranque en modo verify; processor conserva sus propias migraciones.
El transporte privado usa red interna y HMAC. Los mocks son explicitos para
desarrollo; IA usa las claves restringidas del gateway, sin fallback a mock.

El chat muestra fuentes documentales compactas, historial de conversaciones,
renombrado y borrado individual. No muestra la memoria interna ni las solicitudes
guardadas; los datos operativos necesarios se conservan.

El plazo de compresion es configurable entre 30 y 300 segundos, 180 por defecto
en ambos servicios. Reserva cinco segundos para validar y guardar. La lease
dura el plazo mas 15 segundos. No se modifica el timeout del chat normal.

Antes de incorporar esta base se comprobaron Compose mock e IA en entornos
aislados: streaming, persistencia tras reiniciar y bloqueo de envio durante
compresion. Una recuperacion publica real produjo un resumen validado y
persistente tras reinicio; los 14 mensajes originales permanecieron identicos.
El fallo previo de compresion se conserva como antecedente: llamada de 146.203
segundos frente al antiguo plazo local de 30, sin perdida de mensajes.

## Limites y reconciliacion

La recuperacion real exitosa duro 10.135 segundos: no prueba por si sola un caso
real superior a 30 segundos ni que ampliar el plazo causara ese exito. No se
envio otra pregunta para comprobar consumo del resumen; tampoco se certifica
exactitud financiera o RAG de un corpus poblado con estos fixtures sinteticos.

La reconciliacion preserva los cambios de ownership, las evidencias financieras
y los controles de instalacion de dependencias incorporados por develop. Sus
pruebas locales no se presentan como una repeticion de las llamadas reales.
CI remota, publicacion, archivado y cierre global siguen su procedimiento y
autorizaciones especificas; no se han acreditado por este hito local.

## Correcciones CI de fixtures Python (2026-10-11)

Se adaptan las pruebas al checkout portable, al Compose principal y su overlay
IA, al escritor atomico append_pair y al plazo de resumen configurado. No cambia
el producto ni se reducen las aserciones funcionales. Processor: 127 PASS;
backend: 212 PASS / 3 SKIP de SQL nativo no configurado. Revision interna
incremental: REVIEW_PASS, con hashes tecnicos sin cambios tras su retorno.
La evidencia [de correcciones CI](../evidence/jup-035-ci-corrections.md) conserva
los fallos intermedios y las omisiones SQL nativas; la confirmacion remota sigue
a cargo del PM.
