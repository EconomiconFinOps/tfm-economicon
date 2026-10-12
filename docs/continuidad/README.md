# Continuidad del proyecto

## Parche auto de PR120 — 12/10/2026

Último corte: [backend corregido](chat-conversacional.md), suite completa Linux
1671PASS/47SKIP, cero fallos/errores, exit0 sobre8294c48. Ocho fallos y tres errores
resueltos; revisión/validación asistidas autorizadas y atribuidas a Codex.
Evidencia reproducible y límites en el informe. Proveedor/navegador/full28 pendientes.
Los resultados que siguen son antecedentes, no el estado actual del backend.

[Chat conversacional](chat-conversacional.md): aporte local en rama propia sobre
f63c150, contrato auto-documentation-v2 entregado en codigo 5dd1597. Focales
processor130/backend62 pasan (15SKIP); build/OpenSpec/frontend/API pasan.
Ampliación Linux autorizada sobre 9829d82: processor1002PASS/71SKIP y backend
focal77PASS con CockroachDB. Backend amplio no verde; contraste y límites en el
informe. Proveedor real/full28 y dictámenes pendientes. Los cortes siguientes
pertenecen a la entrega original.

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
Detalle y cortes historicos: [chat conversacional](chat-conversacional.md).

Correccion local de bateria JUP-035: ver [chat conversacional](chat-conversacional.md).
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

Resúmenes técnicos para retomar el trabajo. Trello conserva alcance, responsables
y estado operativo; GitHub conserva código y revisiones; OpenSpec conserva
requisitos y diseño. Este índice enlaza evidencia, no sustituye esas fuentes.
Leer la [convención](convencion-compartida.md) y sólo los temas pertinentes.
Las fechas indican la última actualización documental, no una nueva ejecución de pruebas.

| Tema | Resumen y estado documental | Actualizado |
| --- | --- | --- |
| [Chat conversacional](chat-conversacional.md) | JUP-035: RAG/batería importados en rama de entrega; real010 con citas/par/reapertura acreditado. Editorial, checks del checkpoint final y reviews humanas pendientes; límites históricos conservados. | 2026-10-12 |
| [Demo con datos sintéticos de coste](demo-datos-sinteticos-coste.md) | JUP-107: demo de tres minutos con los datos de JUP-106 y conjunto sintético de anomalías con herramienta, esperados y guía (30 pruebas de la parte nueva, 6 con CockroachDB real). Dos changes aprobados y archivados; panel `/anomalies` aún con datos fijos; sin ensayo humano. | 2026-10-11 |
| [Identidad de marca del frontend](identidad-marca-frontend.md) | JUP-112: marca de Economicon en tema claro y oscuro con estados y gráficas validados; implementación local sobre `develop`, 787 tests del frontend, capturas en 1280 y 390 px. PR #112 abierto y con cambios pedidos por la revisión, ya atendidos; falta confirmar en Trello la ampliación al tema oscuro. | 2026-10-11 |
| [Hitos de entrega y cierre del MVP](hitos-entrega.md) | JUP-080: fechas23/10 y29/10 confirmadas por usuario;11 vencimientos activados y verificados. Archivo OpenSpec y cierre por PR en curso. | 2026-10-11 |
| [Memoria: integración DevOps](memoria-devops.md) | JUP-111 / PR87: f incorporado y preservación verificada; PDF13p, Markdown y hashes fuera de Git; revisión delegada por excepción de plazo, integración en curso. | 2026-10-11 |
| [Arquitectura técnica](arquitectura-tecnica.md) | JUP-060 / PR92: arquitectura reconciliada con a0e9a56, memoria histórica verificada y dictámenes por subagentes autorizados; OpenSpec archivado. Estado de integración en PR/Trello. | 2026-10-11 |
| [Arquitectura documental AWS](cloud-aws.md) | Referencia Fargate y Terraform sin ejecución; antecedente EC2 operativo superado. 6 pruebas mock/8 rutas correctos, sin despliegue. | 2026-10-10 |
| [Proveedor y modelos](proveedor-modelos.md) | JUP-078 / PR113: gateway dedicado, claves9+1 USD/30d y26 controles Docker verificados; OpenSpec archivado, revision asistida aprobada, sin gasto real. | 2026-10-10 |
| [Métricas funcionales de negocio](metricas-funcionales-negocio.md) | JUP-068 / PR68: cierre técnico por excepción MVP con subagente;113 pruebas y59 OpenSpec pasan. Piloto/beneficio real sin medir. | 2026-10-10 |
| [Cobertura de etiquetado](cobertura-etiquetado.md) | JUP-017 / PR66: excepción MVP autorizada; conflicto y refresco corregidos, revisión asistida y pruebas en curso. Evidencia versionada en docs/evidence/JUP-017-validation.md. | 2026-10-10 |
| [Consulta de ownership](consulta-ownership.md) | JUP-037 / PR100: cierre preparado bajo excepción de plazo MVP; atribución real documentada, 209 backend/35 frontend y navegador HTTP/SQL pasan. Corrección de nuevo hilo; CI final/integración por verificar al publicar. | 2026-10-10 |
| [Pruebas unitarias e integradas](pruebas-unitarias-integradas.md) | JUP-054: PR93 integrada por excepción de plazo del MVP (7 tests nuevos, CI Linux 2041 pass/91 skips). Segunda pasada en rama, con flujo ordinario: cobertura del candidato `e1c2a8f` y 291 pruebas nuevas, sin cambios de producto; 5 defectos registrados sin corregir (`RF-054-001` a `005`); PR #114 abierta con CI en verde, revisión y validación pendientes. | 2026-10-10 |
| [Dimension vectorial desde Settings](dimension-vectorial-settings.md) | JUP-102 / PR #108: pruebas y CI tecnica verificadas; excepcion de entrega fuera de plazo autorizada, atribucion real bajo Alejandro y cierre por PR. Reviews humanas dispensadas, no simuladas. | 2026-10-10 |
| [Pipeline Turbo y pnpm](pipeline-turbo-pnpm.md) | JUP-105 / PR #86: residual publicado en 12841e6 desde copia propia; comentario y evidencia reconciliados. CI por SHA enlazada en PR; dictámenes Lucía/Paris y merge pendientes. | 2026-10-10 |
| [Entorno pnpm de Alejandro](pnpm-entorno-rf093001.md) | Diagnóstico Codex ff2ea6b entregado; consola normal y corrección permanente pendientes. RF-093-001 sigue Open. | 2026-10-10 |
| [Deteccion de anomalias de coste](deteccion-anomalias-coste.md) | JUP-030 / PR #117: evaluador `POST /billing/anomalies/evaluate` y contrato para JUP-038; 181 pruebas con CockroachDB real (cero omitidas), validacion por HTTP con Docker, OpenSpec 62/62. Archivado con aprobacion de Lucia por la excepcion temporal; sin revision ni validacion humanas de otras personas. Panel `/anomalies` aun con datos de demostracion. | 2026-10-11 |
| [Presupuestos y umbrales](presupuestos-umbrales.md) | JUP-029 / PR #61: correccion documental del P2 de Paris; convencion global separada en JUP-101, nueva revision y validacion pendientes. | 2026-10-02 |
| [Convención compartida](convencion-compartida.md) | JUP-101 / PR #64: adopción para el MVP por excepción de plazo autorizada por el usuario; ejecución asistida atribuida y requisitos humanos dispensados para este cierre, sin consenso ni reviews inventados. | 2026-10-10 |
| [Citas del asistente — JUP-025](citas-asistente.md) | Evidencia histórica de implementación conservada; consultar PR #55 para el estado posterior y el cambio OpenSpec archivado. | 2026-10-10 |

La fila y el resumen de presupuestos conservan su corte histórico de 2026-10-02.
La reconciliación de JUP-101 no revalida ese trabajo; el contraste posterior de
las PR de origen está en la evidencia enlazada desde la convención.
