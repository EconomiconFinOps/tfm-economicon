# Notas historicas de JUP-035

Trasladadas del indice de continuidad el 12/10/2026. Son un registro de
intentos y checkpoints anteriores, no el estado vigente ni pruebas nuevas.
Las rutas locales que aparecen no son instrucciones reproducibles.

+# Continuidad del proyecto

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


## Correccion local retrieval conninfo (12/10/2026)

Reproducido en backend existente: peer disponible, dimension1536, consulta
ordinaria devuelve dos chunks; ruta acotada falla antes de SQL porque context
AdaptersMap del driver no es opcion libpq. Se excluye solo de make_conninfo,
conservando el mismo objeto y opciones TLS/hostaddr en la conexion efectiva.
En proceso desechable con fuente corregido, ambas rutas devuelven dos chunks
del tenant correcto, con vector sintetico y transacciones solo lectura.
Diagnostico por etapa/codigo cerrado y UUID autenticados, sin datos sensibles.
66 pruebas afectadas PASS, 5 omitidas por falta de JUP086_VECTOR_TEST_URL;
nueve focales y cuatro mutaciones detectadas (no sumar repeticiones).
No build/restart/modelos/admin/Git. Causa de los 429 no establecida. Pendientes
revision y aceptacion real; presupuesto .29 restante .020865394 no cabe .025.
Ver [evidencia conninfo](../evidence/jup-035-required-tool-retrieval-20261012.md).

## Correccion local envelope nativo (12/10/2026)

La aceptacion real anterior fallo antes del tool/RAG: envelope/ValueError,
operacion 9fbcc540-7194-4128-beab-13bae203cec9. El recibo no conserva el campo;
nulls y repeticion de metadatos son defectos reproducidos offline, no causa real
confirmada. Se normalizan fragmentos null, id/type repetidos identicos y se
rechazan contradicciones/tipos/limites con codigos cerrados sin contenido.
59 pruebas afectadas PASS, cuatro mutaciones detectadas y fases separadas.
El FAIL intermedio de compatibilidad del diagnostico se conserva: corregido
sin cambiar expectativas antiguas. Pendientes revision y aceptacion real.
No inferencias, builds, administracion ni Git en esta correccion.
Ver [evidencia del parser](../evidence/jup-035-required-tool-envelope-20261012.md).

## Correccion local SQL deadline (12/10/2026)

REVIEW_FAIL P2 anterior conservado: la espera terminaba y el worker SQL seguia.
El chat ahora usa conexion propia acotada, sin pool compartido ni DNS nuevo;
captura hostaddr solo de conexiones ordinarias ya autenticadas, mantiene
hostname/TLS y falla cerrado sin direccion confiable. Deadline/cancelacion cubren
conexion, consulta y lectura. Los llamadores sin deadline siguen intactos.
54 pruebas afectadas PASS; seis casos focales y tres mutaciones detectadas en
sus checkpoints separados. No PostgreSQL real ni inferencia en esta fase.
Pendientes revision independiente afectada y aceptacion real del caso focal.
Ver [correccion acotada](../evidence/jup-035-required-tool-dbdeadline-20261012.md).
El checkpoint anterior se conserva como historial, no como revision vigente.

## Checkpoint local required-documentation-v1 (12/10/2026)

Paris autoriza integrar una busqueda nativa obligatoria en el mismo intento:
required -> recuperacion backend con tenant autenticado -> resultado HMAC ->
none y respuesta final estricta. No hay prefetch ni otro dispatch. El contexto
inicial queda congelado; la extension se valida y contabiliza por separado.
Solo billing conserva autoridad financiera, nunca el corpus.
Offline: 74 pruebas processor y 37 backend, mas 5 pruebas focales processor
y 3 backend sobre consumo/recuperacion, sin sumar estas repeticiones como
pruebas unicas. Cinco mutaciones detectadas en copias desechables. Guards de
fases conformes; no sustituyen el control independiente de parent.
Pendientes revision independiente y una operacion real con corpus/citas/par
persistido/reapertura. No se declara aceptacion real ni full28 actual ni JUP-070.
Desarrollador no realiza inferencias/admin/Git. Presupuesto comunicado por
parent: TOTAL .29USD, baseline .338851568, gasto .260606508; reserva .012 por
llamada conservada. El caso real requiere .024 para dos LLM mas margen de
embedding verificado, sin ampliar topes.
Ver [entrega offline required](../evidence/jup-035-required-tool-offline-20261012.md).
Los cortes siguientes son historicos.

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

Corte real focal semantic3200i12/10:013 completada en un intento, runnerexit0,
revision tecnica PASS y validacion independiente PASS comunicadas por parent.
Estado insufficient_data, evidence/metrics/recommendations vacias, calculo
hipotetico200EUR/20%, sin citas inventadas y un par persistido sin duplicados.
Esto acredita solo la rama no accionable en este ensayo, no full28i ni la rama
accionable real o cumplimiento anyOf futuro. RondaTOTAL0.20USD: gastado0.154364728,
restante0.045635272, baseline0.338851568 intacto. No nuevas llamadas hasta resolver
presupuesto y autorizacion de expiry para otra tanda completa.
Ver [anexo focal i](../evidence/jup-035-battery-semantic3200i-focused013.md).

Corte offline historico semantic3200i12/10: la tanda h de rondaTOTAL0.20USD completo001-012
y paro en013 por actionable_requires_evidence, con finish_reason stop, no length.
El esquema privado incorpora dos ramas completas anyOf: ok/partial exigen una
evidencia y los otros cinco estados permiten lista vacia. Publico/validadores
intactos; 25 pruebas backend y49 processor PASS, dos mutaciones detectadas y
conteo efectivo identico. Compatibilidad del endpoint real y aceptacion pendientes,
sin cierre full28. Ver [evidencia offline i](../evidence/jup-035-battery-semantic3200i-offline.md).
Los cortes siguientes son historicos; no sustituyen este estado ni el presupuesto
TOTAL0.20USD autorizado, sin incremento ni nuevas llamadas por el desarrollador.

Ultimo corte semantic3200h: revision tecnica PASS y validacion independiente
focal015/021/023 3/3PASS; tres operaciones completadas en un intento, runnerexit0.
Investigacion condicional, contraste de ahorro y referencia temporal aceptados.
Evidencia local: [bateria focal h](../evidence/jup-035-battery-semantic3200h-focused.md).
Gasto acumulado de ronda0.123576800USD, restante0.026423200 del TOTAL0.15USD;
baseline0.338851568 intacto. No hay full28h ni cierre global: falta repetir la
bateria completa en esta revision y permiso presupuestario suficiente para ello.

Corte historico focalg: 015/023 PASS, 021 FAIL por omitir contraste cuantitativo entre
ahorro implementado estimado y verificado pese a citas pertinentes. semantic3200h
refuerza conservar cada importe relevante con categoria/unidad; no cambia
autoridad financiera ni reglas de g. Revision y ensayo focal pendientes, sin
declarar cierre ni full28 aceptada. Saldo comunicado0.032521687USD de rondaTOTAL0.15.

Corte historico financialschema de bateria chat12/10: 28 operaciones completadas, 26 PASS/2 FAIL
de contenido y temporal023 pendiente. semantic3200g refuerza investigacion
condicional de alertas, sustento de cada fragmento citado y limites temporales de
captured_at, sin reloj nuevo ni cambios del contrato. Pruebas locales no acreditan
reparacion real; revision/aceptacion pendientes. Presupuesto TOTAL0.15USD intacto;
restante comunicado0.039264117USD no permite otra tanda completa comparable segura.
Detalle y cortes historicos: [chat conversacional](../continuidad/chat-conversacional.md).

Correccion local de bateria JUP-035: ver [chat conversacional](../continuidad/chat-conversacional.md).
El corte de diagnostico identifica tres metricas no verificadas; la aceptacion
real de las 28 consultas del bundle v3 sigue pendiente.
El ajuste autorizado de recuperacion contigua y completitud de reglas conserva
los filtros y limites; 13 operaciones completas no acreditan contenido correcto.
Tras REVIEW_FAIL, reparacion local de scope con espacios y comparaciones solo
solicitadas; nueva revision y comprobacion real afectadas siguen pendientes.
La tanda completa final3200 se ejecuto: 19 aceptadas/9 fallidas semanticamente.
Correccion general de instrucciones autorizada; repetir y evaluar sigue pendiente.
El checkpoint semantic3200c pide periodo con datos elegibles cuando falta el
denominador; la espera contable del ensayo es acotada y no elimina la parada
por incertidumbre. La comprobacion real de esta correccion sigue pendiente.
Focused9 tuvo 6 PASS/3 FAIL y una cita extra no pertinente. semantic3200d refuerza
instrucciones generales; la aceptacion real afectada y full28 siguen pendientes.
semantic3200e aclara ambas unidades de cobertura de tagging aun si se pregunta
solo por coste; nueva comprobacion real pendiente, sin declarar causa confirmada.
Aceptacion mixta: 8 PASS/1 FAIL. semantic3200f explicita checklist completo de
rightsizing en next_actions; repeticion real y full28 no se declaran superadas.
Full28f paro tras cinco completadas/006 fallida. financialschema3200 restringe
metrics en esquema privado sin autoridad financiera servidor, conserva costes
cero validos y guard publico; nueva revision y aceptacion real siguen pendientes.
