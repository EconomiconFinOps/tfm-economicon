# conversational-web-interface Specification

## Purpose
Definir el chat conversacional de Economicon: interfaz integrada, streaming autenticado, aislamiento por tenant y usuario, historial persistente, contexto de pantalla, citas y compresión de preguntas/respuestas mediante LLM.
## Requirements
### Requirement: Panel conversacional integrado

La interfaz SHALL ofrecer un panel derecho fijo v1 con control abierto–cerrado,
estilo del shell, acceso por teclado y adaptación responsive, preservando sesión,
tenant y conversación. El preview de escritorio SHALL reservar aproximadamente la mitad derecha (~50%
del ancho de ventana) al chat y mantener la app visible en la otra mitad, con
estilo existente y datos sintéticos, conforme a Paris vía PM15:25:33/TL15:25:57
del 09/10/2026. Atajo, animación y móvil requieren diseño aprobado.

#### Scenario: Panel

- **WHEN** un usuario autenticado abre o cierra el panel
- **THEN** el control comunica su estado, gestiona foco y conserva el scope autorizado sin cambiar la ruta funcional

### Requirement: Lectura y seguimiento del historial

El panel SHALL preservar la lectura cuando el usuario se desplaza hacia mensajes
anteriores y ofrecer volver al final para reanudar seguimiento. La política de
envío propio/carga y adaptación de altura se concretará en el spike aprobado;
streaming real es obligatorio por Paris vía PM15:47:28/TL15:48:23 del
09/10/2026; comportamiento UI concreto queda en spike posterior.

#### Scenario: Lectura y seguimiento

- **WHEN** llegan mensajes o cambia la altura de citas mientras el usuario lee arriba
- **THEN** el panel no lo arrastra al final y permite volver abajo de forma explícita, conservando scope al cambiar conversación

### Requirement: Respuesta natural real y evidenciada

El sistema SHALL responder preguntas con la vertical 020–026, gateway023,
guardrails024 y retrieval022, conservando citas025 y contrato de respuesta
aprobado; SHALL entregar texto generado incrementalmente desde gateway a UI
mediante processor y backend, antes de terminar la generación; SHALL reconocer
evidencia insuficiente sin inventar cifras.

#### Scenario: Respuesta real

- **WHEN** una pregunta autorizada dispone de evidencia relevante
- **THEN** un modelo real mediante gateway responde dentro del contrato validado y la plantilla o mock no cuentan como aceptación

#### Scenario: Sin evidencia

- **WHEN** no existe evidencia suficiente
- **THEN** se declara no_data o insufficient_data sin hechos financieros inventados

#### Scenario: Decision documental automatica dentro del mismo intento

- **WHEN** el chat IA inicia un intento autorizado
- **THEN** SHALL usar el contrato auto-documentation-v2 y realizar una primera peticion con search_documentation estricta y tool_choice auto sin response_format final, admitir cero o una llamada nativa con query acotada sin parametros de tenant y ejecutar la recuperacion existente en backend con el scope autenticado; SHALL mantener una operacion, un intento, un dispatch privado y el contexto/hash canonicos iniciales congelados, sin precargar corpus para simular la herramienta

#### Scenario: Decision sin herramienta y finalizacion estricta

- **WHEN** la primera peticion termina con stop sin llamada nativa
- **THEN** SHALL descartar su texto sin mostrarlo, persistirlo ni reutilizarlo como contexto; SHALL realizar una segunda y ultima generacion con el contexto autorizado original, tool_choice none y FinOpsResponse estricto; SHALL permitir respuestas con evidencia existente, saludos o aclaraciones no accionables, y exigir abstencion si falta sustento documental, sin recuperacion oculta; SHALL conservar el deadline comun y sumar el uso real de ambas generaciones, sin autoridad financiera derivada de usuario o corpus

#### Scenario: Resultado privado y continuacion final

- **WHEN** el backend obtiene fuentes para la llamada nativa vigente
- **THEN** SHALL devolver una extension autorizada mediante el HMAC existente a un endpoint privado del processor, vinculada al intento y tool_call_id, y continuar con el mensaje assistant original mas role tool correlacionado, las mismas tools y FinOpsResponse estricto con tool_choice none; SHALL conservar la autoridad financiera exclusivamente de billing, validar citas contra las fuentes realmente recuperadas, contar herramientas y continuacion en ambos servicios y sumar el consumo de las dos peticiones sin alterar FinOpsResponse 1.0

#### Scenario: Cancelacion, resultado ajeno o segunda herramienta

- **WHEN** vence el plazo comun, se cancela el intento o llega un resultado ajeno, repetido, desconocido o una segunda llamada
- **THEN** SHALL rechazar la continuacion sin segunda inferencia ni persistencia; la recuperacion y espera SHALL compartir el deadline del intento, sin reiniciarlo; una recuperacion vacia SHALL permitir una abstencion validada y nunca inventar fuentes; el modo mock SHALL seguir disponible sin llamadas pagadas

#### Scenario: Consulta documental SQL acotada realmente

- **WHEN** la recuperacion documental del chat esta conectando, ejecutando SQL o leyendo resultados y vence el deadline comun o se cancela el intento
- **THEN** SHALL interrumpir la conexion/consulta propia y no dejar un worker esperando SQL tras terminar la espera asincrona; SHALL aplicar el plazo restante tambien a las lecturas de documentos y conservar tenant/proveedor/filtros; los llamadores ordinarios sin deadline SHALL conservar el camino existente, sin cambiar el pool compartido

#### Scenario: Conexion acotada sin resolucion DNS nueva

- **WHEN** el chat necesita abrir su conexion documental acotada
- **THEN** SHALL usar una copia de la direccion IP obtenida desde una conexion ordinaria ya autenticada, conservando hostname, TLS y todos los parametros originales; sin direccion confiable SHALL fallar cerrado inmediatamente, sin DNS nuevo ni fallback tras direccion obsoleta; la captura SHALL aprovechar conexiones existentes, sin abrir otra para capturar ni cambiar los llamadores ordinarios

#### Scenario: Persistencia unica tras recuperacion documental

- **WHEN** la respuesta final supera los validadores existentes
- **THEN** SHALL persistir una sola pareja pregunta/respuesta y las citas resueltas por el backend, recuperables al reabrir la conversacion; los errores de SQL SHALL conservar el mecanismo existente sin comprar otra llamada al modelo

#### Scenario: Calculo hipotetico solicitado

- **WHEN** el usuario solicita un calculo con cifras que aporta sin registros financieros contrastados
- **THEN** el asistente puede resolverlo solo en answer, identificado como hipotetico, con assumptions y limitations, sin convertirlo en metrics ni evidence inventada; sin evidencia autorizada SHALL conservar un estado no accionable y metrics y recommendations vacias

#### Scenario: Scope canonico de la respuesta

- **WHEN** el proveedor entrega una respuesta de chat
- **THEN** el servidor SHALL incorporar period y subscription_ids desde el contexto canonico, sin permitir que el modelo los genere; los IDs admitidos SHALL normalizarse con strip y deduplicarse despues sin reescribir la captura, conservando el limite de entrada de 1 a 256 caracteres y rechazando blancos con 422 antes del proveedor; sin suscripciones seleccionadas la lista SHALL estar vacia, nunca contener el tenant; mas de 20 suscripciones normalizadas distintas SHALL rechazarse con 422 antes de reclamar un intento, sin truncar la seleccion ni alterar FinOpsResponse 1.0

#### Scenario: Salida truncada y diagnostico seguro

- **WHEN** una salida termina por length o es rechazada por una regla del contrato
- **THEN** el sistema SHALL distinguir truncacion, rechazo contractual y fallo HTTP en sus diagnosticos internos sin registrar prompts, valores rechazados, respuestas, secretos ni excepciones arbitrarias; el chat SHALL reservar la salida configurada, con 3200 tokens por defecto y como maximo aprobado, sin cambiar modelo, deadline ni politica de reintentos

#### Scenario: Continuacion documental acotada

- **WHEN** la recuperacion de chat obtiene fragmentos documentales relevantes
- **THEN** SHALL conservar los primeros retrieval_top_k como resultados principales y puede incorporar vecinos inmediatos por document_id y chunk_index dentro de un maximo de 20 candidatos con los mismos filtros de tenant, proveedor y distancia; SHALL conservar IDs, contenido y citas reales, deduplicar, descontar las evidencias financieras del limite y mantener el presupuesto de contexto; SHALL indicar que la recuperacion contigua esta acotada y las omisiones por capacidad, sin garantizar vecinos ausentes ni recurrir a filtros menos seguros

#### Scenario: Reglas documentales incompletas y comparaciones

- **WHEN** el asistente explica reglas de clasificacion, tagging o comparaciones de importes
- **THEN** SHALL abstenerse de asignar categorias o umbrales que no constan en una regla completa autorizada, explicar owner como equipo y excluir PII al describir la politica de tagging, y expresar diferencias absolutas y relativas solo para comparaciones solicitadas de importes respecto de una base distinta de cero sin inventar porcentajes cuando sea cero ni comparaciones adicionales con umbrales; al comparar porcentajes por solicitud SHALL distinguir variacion relativa y puntos porcentuales; SHALL conservar las reglas existentes de evidencia y estado, sin transformar ejercicios hipoteticos en costes verificados

#### Scenario: Completitud semantica del analisis

- **WHEN** el usuario pide analizar ratios, cobertura, alertas, ahorro, cambios de recursos o conversiones monetarias
- **THEN** SHALL declarar indefinido un ratio con denominador cero y solicitar un periodo con datos elegibles y su consulta autorizada cuando falte denominador o coste para calcular, distinguir ponderacion por coste de conteo, ahorro identificado de implementado y estimado de verificado; SHALL proponer investigar causas y si los cambios eran esperados sin apagar automaticamente, explicitar riesgos de rendimiento y SLA al considerar rightsizing, solicitar fuente autorizada del tenant sin secretos ni accesos nuevos cuando faltan datos y moneda de destino, tipo de cambio y fecha cuando procede convertir; SHALL distinguir dato ausente de cero verificado y citar solo fragmentos que sustenten la afirmacion concreta, sin considerar suficiente la validez de sus IDs
- **AND** con recuentos y costes elegibles de tagging SHALL devolver ambas tasas y sus denominadores, explicando por que pueden diferir; ante anomalias candidatas SHALL pedir investigar y confirmar causa y esperabilidad; en rightsizing SHALL explicar consecuencias concretas de degradacion de rendimiento/servicio o incumplimiento del SLA incluso con CPU media baja; SHALL retirar cada referencia extra que no sustente una afirmacion concreta hecha aunque otras citas sean pertinentes
- **AND** con ambos tipos de datos disponibles SHALL calcular primero tasa por recursos y despues ponderada por coste, aunque la pregunta mencione solo coste, como complemento definicional de cobertura y no como comparaciones adicionales de importes
- **AND** ante rightsizing, next_actions SHALL pedir explicitamente validar utilizacion CPU/memoria/IO/picos, rendimiento, SLA, crecimiento y restricciones de negocio antes de cualquier ajuste, agrupando el checklist completo aunque los requisitos ya aparezcan en evidencia; su presencia solo en extractos no sustituye la peticion

#### Scenario: Alertas conceptuales, citas individuales y referencia temporal

- **WHEN** el asistente explica presupuestos o alertas, selecciona citas documentales o responde a una referencia relativa como hoy
- **THEN** al explicar umbrales SHALL incluir en next_actions investigar causa y esperabilidad si se superan, sin afirmar que ya se superaron ni automatizar recursos
- **AND** cada cita SHALL sustentar una afirmacion concreta con su fragmento exacto; compartir documento, titulo o vecindad con una cita pertinente no basta; la seleccion SHALL producirse al generar la respuesta, sin filtros semanticos posteriores que borren citas recibidas
- **AND** captured_at SHALL tratarse como instante declarado de captura, no autoridad de hoy ni periodo financiero; sin referencia temporal explicita e inequivoca SHALL conservar la expresion relativa sin inventar fecha y solicitar periodo y zona cuando sean necesarios, sin introducir reloj ni campos privados nuevos
- **AND** SHALL conservar FinOpsResponse 1.0, periodo financiero canonico del servidor, autoridad financiera, modelo, salida de 3200 tokens y plazos existentes

#### Scenario: Comparacion cuantitativa de categorias de ahorro

- **WHEN** el usuario aporta importes relevantes de categorias de ahorro para compararlas
- **THEN** la respuesta SHALL conservar cada importe relevante y su unidad junto a su categoria, distinguiendo ahorro identificado, implementado estimado y verificado; SHALL contrastarlos cuantitativamente, sin sustituirlos por una enumeracion generica de categorias aunque el ratio final sea correcto
- **AND** si los importes son hipoteticos SHALL permanecer en answer con supuestos en assumptions y limitaciones, sin producir metricas financieras ni convertir estimaciones implementadas en ahorro verificado; la autoridad financiera del servidor y FinOpsResponse 1.0 SHALL permanecer intactos

#### Scenario: Unidades, condiciones contractuales y sustento de citas

- **WHEN** el asistente explica resultados con unidades, compromisos contractuales o fuentes documentales
- **THEN** SHALL conservar en answer la unidad completa del input junto al resultado, incluido su denominador temporal, sin convertir una tasa en un total
- **AND** SHALL no completar duraciones, precios ni condiciones contractuales con conocimiento general si no constan en el input o corpus autorizado; SHALL explicar el concepto sin esos detalles y pedir las condiciones pertinentes cuando sean necesarias
- **AND** SHALL citar solo fragmentos que sustenten afirmaciones expresadas, no instrucciones del sistema ni aritmetica del usuario; SHALL no anadir afirmaciones irrelevantes para justificar una cita
- **AND** estas instrucciones SHALL aplicarse en el productor, sin borrado posterior de citas ni cambios en esquema publico o privado, validadores, retrieval, modelo, routing, reintentos o salida de 3200 tokens

#### Scenario: Formula monetaria con destino y direccion explicitos

- **WHEN** una respuesta considera convertir importes en monedas diferentes
- **THEN** sin destino, fecha y direccion del tipo de cambio autorizados SHALL mantener importes separados y pedir esos datos, sin formular una suma que presuponga un importe ya expresado en el destino desconocido
- **AND** un ejemplo hipotetico de formula SHALL declarar moneda de origen, destino y unidades del tipo de cambio, convirtiendo cada importe necesario al mismo destino sin inventar cotizaciones ni inferir moneda por tenant o configuracion regional
- **AND** las instrucciones aceptadas de unidades y condiciones contractuales SHALL permanecer intactas, sin cambios de schema, validadores, retrieval, modelo, routing, plazos ni salida de 3200 tokens

#### Scenario: Sustento antes de seleccionar estado

- **WHEN** el productor selecciona estado y evidencias de una respuesta
- **THEN** SHALL determinar primero que fragmentos autorizados sustentan realmente sus afirmaciones, sin elegir ok o partial para despues rellenar citas que permitan ese estado
- **AND** si un ejercicio hipotetico no tiene evidencia financiera ni corpus que sustente la respuesta SHALL conservar respuesta util con estado no accionable compatible y evidence vacia, sin confundir recuperacion con sustento
- **AND** SHALL conservar las instrucciones aceptadas de unidades y condiciones contractuales, sin borrado posterior de citas, reparacion de estados ni relajacion de schema o validadores

#### Scenario: Esquema de proveedor sin metricas financieras autorizadas

- **WHEN** el contexto no contiene metricas de una consulta financiera efectuada y validada por el servidor
- **THEN** el esquema privado entregado al proveedor SHALL limitar metrics a una lista vacia con maxItems 0; las cifras hipoteticas SHALL permanecer solo en answer con sus supuestos y limitaciones
- **AND** la autoridad SHALL proceder de la validacion de costes del servidor, no de kind o flags enviados por el usuario; una consulta cost_query valida con metricas SHALL conservar la posibilidad de devolverlas
- **AND** FinOpsResponse 1.0 y la validacion final de evidencia SHALL permanecer sin relajacion; no se SHALL borrar metricas de una respuesta recibida para hacerla admisible
- **AND** financial_metrics_allowed SHALL ser un booleano obligatorio del contexto privado canonico generado por el servidor tras validar billing, nunca un control del request publico; costes cero validados SHALL habilitar metricas y una consulta vacia o fallida SHALL mantener la restriccion
- **AND** el gateway de chat SHALL seleccionar la variante efectiva del esquema segun ese control autenticado y contabilizarla dentro del presupuesto existente; la politica SHALL quedar identificada en el manifiesto de integridad sin cambiar el schema publico ni la autoridad de validacion final

#### Scenario: Estado accionable con evidencia en el esquema privado

- **WHEN** el gateway prepara el esquema privado para una respuesta de chat
- **THEN** SHALL conservar el objeto base y sus restricciones en dos ramas anyOf con referencias a los mismos $defs: ok o partial SHALL exigir evidence con minItems 1, y los otros cinco estados SHALL permitir evidence vacia
- **AND** backend y processor SHALL derivar y contabilizar el mismo esquema efectivo, conservar la restriccion financiera autenticada y verificar el hash privado actualizado del manifiesto; el esquema publico FinOpsResponse 1.0 y los validadores SHALL permanecer intactos
- **AND** la cardinalidad SHALL no acreditar pertinencia o autorizacion de citas; la compatibilidad anyOf del endpoint real SHALL requerir un ensayo separado, sin fallback ni reparacion posterior si el proveedor rechaza o incumple el esquema

#### Scenario: Evidencia

- **WHEN** una respuesta afirma hechos basados en fuentes
- **THEN** las citas conservan origen y contenido persistido del tenant autorizado

#### Scenario: Fuentes ajenas

- **WHEN** una salida refiere evidencia desconocida o de otro tenant
- **THEN** el backend rechaza esas referencias al validar el final, antes de guardar la respuesta como confirmada o presentar sus citas como verificadas; la evidencia de entrada se autoriza antes de generar y los fragmentos de texto visibles siguen siendo provisionales

### Requirement: Streaming real y cierre verificable

Por instrucción humana de Paris vía PM09/10/2026 15:47:28, el sistema SHALL
transmitir incrementos de generación reales gateway→generador processor→backend→UI
con autorización tenant Y usuario. SHALL distinguir texto provisional, resultado
final validado/persistido, cancelación y fallo/interrupción. No se atribuye esta
instrucción a una mención de Trello no verificada.

#### Scenario: Streaming real

- **WHEN** el gateway está generando una respuesta autorizada
- **THEN** la UI recibe al menos un incremento de texto generado antes del fin del productor, sin esperar el cuerpo completo ni temporizar una respuesta ya terminada

#### Scenario: Cancelación streaming

- **WHEN** el propietario pulsa Detener durante una generación
- **THEN** el servidor intenta el cierre terminal único, confirma solo tras commit y propaga cierre upstream best effort sin garantizar cese de facturación

#### Scenario: Ocultación y cambio de identidad

- **WHEN** se oculta el panel, se pierde el lector o cambia sesión/tenant/usuario
- **THEN** ocultar o desconectar no envía Stop ni cancela implícitamente el productor; el cambio de identidad limpia estado/listeners y descarta callbacks antiguos sin mostrar datos del scope anterior

#### Scenario: Error tras headers

- **WHEN** un stream HTTP 200 emite error o termina sin evento final válido
- **THEN** se presenta error/interrupción saneado y el borrador no se considera respuesta final aceptada

#### Scenario: Final inválido

- **WHEN** al terminar la generación el objeto o sus referencias/citas no pasan validación completa y pertenencia
- **THEN** se reconcilia el borrador con error visible y no se persiste como respuesta confirmada; mostrar provisional antes del final no equivale a validarlo por token

### Requirement: Operación durable y pareja completa final

Por instrucciones Paris PM21:33:08 y aprobación PM21:46:22, el sistema SHALL separar reserva/idempotencia operacional del historial completo. SHALL conservar pregunta recuperable y contador/fences por operación; pregunta y respuesta completa SHALL persistirse juntas atómicamente al finalizar antes de confirmar completed. Reintentos SHALL reutilizar pregunta lógica y nunca concatenar fragmentos. El registro operacional separado permanece válido. La elección posterior PM10/10/2026 03:01:32 establece un documento JSONB por conversación como historial canónico; esquema003/backfill concretos están propuestos y pendientes de ejecución autorizada. RabbitMQ SHALL permanecer solo ingesta.

#### Scenario: Rollback de pareja

- **WHEN** falla la inserción de respuesta o el cierre de operación en la transacción final
- **THEN** no se publica pareja incompleta; la solicitud recuperable permanece y el error SQL no dispara otra inferencia

#### Scenario: Recuperación operacional

- **WHEN** cae el proceso con un intento reservado o con commit final ambiguo
- **THEN** se resuelve estado/contador mediante lectura y fencing, sin redispatch del mismo intento ni regeneración de completed; parcial RAM puede perderse, pregunta operacional se conserva

#### Scenario: Retry de solicitud antigua

- **WHEN** se reintenta una operación fallida cuya pregunta ya fue guardada por otra operación
- **THEN** la transacción final verifica pertenencia y contenido, reutiliza la pregunta y guarda otra respuesta completa sin duplicar user

#### Scenario: Stop frente al final

- **WHEN** Stop autorizado compite con commit final o programación de siguiente intento
- **THEN** un CAS/commit válido gana; Stop confirmado impide siguiente intento y final tardío, completed previo permanece

#### Scenario: Idempotencia y exclusión

- **WHEN** se repite clave/payload o se envía otra intención en una conversación abierta
- **THEN** la repetida observa misma operación sin productor adicional, distinto payload409conflict y otra intención409busy, sin segunda pregunta

### Requirement: Tres reintentos funcionales adicionales

Por Paris PM21:33:08/21:46:22, el backend SHALL permitir inicial más tres retries automáticos, máximo cuatro intentos por operación,120s por intento y480s activos. Transporte/gateway SHALL mantener retries0 para no multiplicarlos. Interrupciones transitorias SHALL programar otro intento si queda; errores permanentes, Stop voluntario y desconexión de lector SHALL quedar diferenciados. Por decisión humana PM23:05:12, cada solicitud SHALL disponer de dos presupuestos independientes acumulados:120s de espera automática local y120s de espera automática del proveedor. Retry/resume/recuperación de la misma operación SHALL conservar sus consumidos y contador, sin reinicio. El máximo240s de esperas automáticas SHALL distinguirse del tiempo total hasta respuesta y del presupuesto120s de ejecución por intento. Retry-After SHALL respetarse: si excede saldo proveedor restante, pausa visible conservando solicitud/contador/retry_at y reanudación explícita solo desde fecha mínima, sin renovar presupuestos ni anticipar envío.

#### Scenario: Cuatro interrupciones

- **WHEN** cuatro intentos de una operación fallan transitoriamente
- **THEN** no se ejecuta un quinto, cada intento usa ID/buffer propios, pregunta única y error final saneado

#### Scenario: Espera y cancelación

- **WHEN** el proveedor indica Retry-After o el usuario pulsa Stop durante espera
- **THEN** la espera automática solo se programa si cabe en el saldo proveedor acumulado restante; en otro caso hay pausa visible y resume explícito solo≥retry_at, sin reset de saldos/contador; Stop confirmado cancela programación y nunca se envía antes de fecha permitida

### Requirement: Estados de operación comprensibles

La interfaz SHALL distinguir vacío, carga, error, datos insuficientes y fallo
de proveedor y ofrecer información accesible sin revelar detalles sensibles.

#### Scenario: Estados

- **WHEN** cambia el estado de una conversación
- **THEN** se representa y anuncia de forma accesible sin atribuir datos reales a fixtures

#### Scenario: Error proveedor

- **WHEN** hay error permanente o se agotan los cuatro intentos por fallo transitorio
- **THEN** se muestra error final saneado y acción comprensible sin respuesta inventada; desconexión del lector no agota intentos

### Requirement: Historial persistente y privado

El sistema SHALL preservar mensajes y metadata JSONB tras recarga y restringir
lectura/escritura a tenant y usuario propietarios, conservando controles de sesión.

#### Scenario: Historial

- **WHEN** el propietario crea una conversación, envía un mensaje y recarga con Cockroach real
- **THEN** contenido y metadata/citas se recuperan sin doble decodificación JSONB

#### Scenario: Historial ajeno

- **WHEN** otro tenant o un usuario distinto del mismo tenant solicita una conversación ajena
- **THEN** la operación devuelve 404 sin revelar sus mensajes o metadata

#### Scenario: Identidad

- **WHEN** cambia tenant, identidad o sesión mientras una respuesta está en curso
- **THEN** ningún mensaje ni estado tardío del contexto anterior se muestra en el nuevo

### Requirement: Contexto de pantalla limitado y validado

Conforme Paris vía PM09/10/2026 19:42:02, UI Context Awareness SHALL capturar
una instantánea JSON YA preparada al recibir/cambiar datos de pantalla activa, filtros,
periodo, moneda, totales/desglose, fechas/completitud; SHALL excluir credenciales
y datos internos innecesarios. El servidor SHALL verificar identidad/tenant/ownership
y schema, tratar la captura como datos no confiables, conservarla por intento
y separar citas de pantalla declarada de evidencia financiera verificada.
SHALL permanecer separado del compresor QA mínimo de JUP-035 y de memoria avanzada JUP-041; el modelo no autoriza ámbitos.

#### Scenario: Contexto UI

- **WHEN** el cliente envía pantalla y filtros manipulados, caducados o de ámbito ajeno
- **THEN** el servidor valida su schema y permisos y rechaza o solicita aclaración conforme al contrato sin consultar datos ajenos

#### Scenario: Captura y discrepancia

- **WHEN** un envío copia la versión preparada de pantalla y su contraste servidor difiere o no está disponible
- **THEN** la captura completa se conserva bajo su propietario y la respuesta distingue declaración de pantalla, demo y evidencia propia verificada sin inventar cifras o certeza temporal

#### Scenario: Captura e idempotencia

- **WHEN** se repite la misma clave con captura idéntica o cambiada
- **THEN** idéntica recupera el intento sin regenerar; cambiada produce conflict; retry humano usa captura y clave nuevas sobre la pregunta existente

### Requirement: Prompts versionados exclusivamente en servidor

Por aprobación Paris vía PM19:42:02, el sistema SHALL cargar instrucciones estables
desde recursos versionados Git en servidor, reutilizar reglas JUP-024 y registrar
la versión por respuesta. Historial/evidencias/captura SHALL permanecer como datos
no confiables separados de instrucciones. La caché SHALL ser opcional y no sustituir
el contexto necesario de cada petición ni la base de datos.

#### Scenario: Versión y datos hostiles

- **WHEN** datos variables intentan cambiar instrucciones o el recurso requerido no coincide con la versión validada
- **THEN** datos cliente no seleccionan roles/prompts ni se convierten en autoridad; el runtime no infiere con recursos inválidos y no confirma salida que incumpla los guards

#### Scenario: Caché no disponible

- **WHEN** no hay hit o no se dispone de usage.cached_tokens
- **THEN** la corrección conserva el contexto completo necesario y no genera reintentos para calentar caché; campo ausente no se presenta como cero

### Requirement: Capacidad de costes explícita

La respuesta SHALL consultar costes084/036/037 únicamente mediante contratos
disponibles y autorizados, conservando periodo UTC, ámbito, moneda y procedencia.

#### Scenario: Costes disponibles

- **WHEN** una pregunta solicita una dimensión de coste que aún no está integrada
- **THEN** se declara la limitación sin fingir disponibilidad ni calcular con datos sintéticos como reales

### Requirement: Compresión mínima del diálogo con originales preservados

Por ampliación Paris vía PM09/10/2026 21:07:33, la propuesta JUP-035 SHALL preparar diálogo QA resumido y turnos recientes dentro del presupuesto compatible. El compresor SHALL generar resumen mediante llamada LLM por actualización necesaria solo de preguntas/respuestas completas, preservar originales/referencias, persistir fuentes/revisión y congelar contexto por intento. Controles locales no sustituyen la llamada LLM. Pantalla, metadata, evidencia y anexos SHALL permanecer fuera de su entrada. Defaults y nueva columna son propuestas pendientes de aprobación pre-code, no ejecución autorizada.

#### Scenario: Preparación y omisiones

- **WHEN** el diálogo supera el umbral propuesto o el espacio residual de la petición
- **THEN** se prepara un resumen best effort mediante LLM, fuentes trazables y recientes completos que caben y cobertura/omisiones explícitas, conservando todos los originales y el snapshot fuera del compresor

#### Scenario: Resumen fallido o anticuado

- **WHEN** falla la preparación, compiten dos candidatos o un retry completed cambia una fuente cubierta
- **THEN** CAS y hashes impiden instalar/usar un resumen obsoleto; el chat usa el previo válido o recientes que caben con limitación explícita, sin bloquear respuesta principal ni sustituirlo por resumen local; nuevas llamadas solo por actualización necesaria

### Requirement: Conversaciones privadas concurrentes

Por corrección Paris PM21:12:15, listado, lectura, envío, retry, estado, Stop, stream, reenganche, evidencias, contexto y resumen SHALL exigir tenant + propietario + conversación. Exclusión de generación SHALL ser por conversación. Capacidad global configurable SHALL permitir el objetivo de cinco chats privados concurrentes; límite8 es propuesta operativa, no capacidad upstream comprobada.

#### Scenario: Cinco usuarios del mismo tenant

- **WHEN** cinco usuarios envían simultáneamente en sus cinco conversaciones privadas
- **THEN** cinco productores pueden estar activos antes de finalizar ninguno; Stop/reenganche de uno no afecta los otros; un segundo envío del mismo chat continúa sujeto a exclusión

#### Scenario: Cruce de identidad en recursos

- **WHEN** un usuario solicita cualquier recurso o stream de otro usuario del mismo tenant o de otro tenant
- **THEN** no accede a mensajes, estados, buffers, snapshots, evidencia ni resúmenes ajenos y ninguna invocación amplía su ámbito

### Requirement: Snapshot por pestaña y presupuesto explícito

Por aprobación Paris PM21:15:55, el sistema SHALL mantener JSON específico con datos cargados de la pestaña, actualizado ante cambio de filtros/periodo/datos y Send SHALL copiar/congelar versión preparada sin construir/refetch ni diagnóstico. SHALL conservar captura íntegra hasta1MiB, aplicar el techo8192 tokens variables con conteo/capacidad compatibles, separar proyección y original y declarar excesos/omisiones sin truncado silencioso. El reparto es propuesta revisable; caché no sustituye transmisión de contexto.

#### Scenario: Cambio de pantalla y exceso

- **WHEN** cambian datos/filtros antes de enviar o la captura/presupuesto excede el límite
- **THEN** el intento toma la versión actual; captura sobre1MiB se rechaza explícitamente antes de reserva, proyección limitada declara omisiones y no descarta silenciosamente información indispensable

### Requirement: Canal privado autenticado en un DockerServer

Por elección Paris PM21:17:13, backend→processor SHALL usar red privada dedicada y autenticación/integridad/replay con secret exclusivo, processor sin host port y listener chat solo en interfaz privada. HTTP interno queda permitido únicamente en un DockerServer con esa topología; HTTPS externo permanece y entre hosts requiere reevaluación. Red privada y HMAC no proporcionan confidencialidad.

#### Scenario: Acceso por interfaz equivocada

- **WHEN** se intenta acceder al chat por host, otra red/interfaz o sin autenticación válida
- **THEN** el endpoint no queda expuesto en dichas interfaces y la llamada no autorizada no ejecuta generación, conservando conectividad legítima de ingesta, DB y gateway

### Requirement: Prefijo estable de resumen como datos

Por Paris PM21:33:08, resumen vigente SHALL permanecer como user no confiable después de system estable y antes de pantalla/pregunta/variables; SHA/revisión/versiones fijan bytes usados. Contexto necesario SHALL reenviarse en cada intento, sin promesa de hit/memoria remota ni promoción de resumen a instrucciones.

#### Scenario: Cambio de resumen y cache miss

- **WHEN** cambia revisión del resumen o no hay hit de caché
- **THEN** nuevo prefijo refleja versión autorizada para nueva operación; intentos ya congelados no cambian, contexto requerido se transmite y no se llama para calentar caché

### Requirement: Conteo offline fijado

Por aprobación Paris PM21:54:52, diseño SHALL usar tokenizers0.22.1 y artefacto ZAI de revisión/hash fijados en contrato de prompts, sin pesos/código remoto/fallback tokenizador ajeno como equivalente. Conteo contractual del límite8192 SHALL distinguirse de uso/facturación reportados; instalación/build/carga y prueba focal futuros tras pre-code.

#### Scenario: Artefacto o recuento inválido

- **WHEN** falta/cambia hash del tokenizer o el contexto contractual supera presupuesto
- **THEN** se cierra admisión o declara insuficiencia antes de upstream, sin equivalencia inventada bytes/tokens ni truncado silencioso de información esencial

### Requirement: Admisión visible con presupuestos acumulados

Por decisión humana PM23:05:12, una solicitud válida sin capacidad local inmediata SHALL conservarse waiting, con espera visible/cancelable, y SHALL arrancar automáticamente cuando haya plaza dentro de su saldo local acumulado120s. Esperar capacidad SHALL no consumir intento del proveedor ni crear active sin claim. Al agotar saldo local SHALL pasar a paused visible, conservar pregunta/operación y no reencolarse automáticamente. Resume explícito SHALL no renovar ningún presupuesto o contador; con saldo local agotado SHALL requerir plaza inmediata, permaneciendo paused si falta. No se promete plazo total de cuatro minutos ni capacidad medida8.

#### Scenario: Primera admisión sin plaza

- **WHEN** no hay capacidad inmediata para una solicitud válida
- **THEN** se reserva waiting sin intento consumido, visible/cancelable, y al obtener plaza dentro del saldo local se registra el claim y empieza automáticamente

#### Scenario: Agotamiento local acumulado

- **WHEN** la misma operación acumula120s de espera local entre admisión y reintentos
- **THEN** queda paused con pregunta conservada, sin bucle automático; resume explícito conserva saldos/contador y solo arranca si hay plaza inmediata

#### Scenario: Retry-After supera saldo proveedor

- **WHEN** quedan30s de espera proveedor automática y Retry-After exige60s
- **THEN** no hay envío anticipado ni nueva bolsa120s: pausa visible con retry_at, reanudación explícita solo desde esa fecha y saldo/counter intactos

#### Scenario: Reanudación o caída entre esperas

- **WHEN** una operación con consumidos locales90s y proveedor80s se recupera o reanuda
- **THEN** conserva saldos locales30s y proveedor40s, sin reset por nuevo intento, sin contar dos veces tiempo solapado y sin usar pausas humanas como renovación de espera automática

### Requirement: Documento canónico JSONB único por conversación

Por decisión Paris PM10/10/2026 03:01:32 el sistema SHALL mantener un documento JSONB por conversación como única fuente activa de historial completo, identificado por tenant/usuario/conversación, versionado y con revisión/ordinal explícitos. SHALL conservar el contrato público de mensajes, IDs, textos, metadata y citas. SHALL validar identidad y estructura bajo autorización de propietario; un documento inválido o no migrado SHALL fallar cerrado sin fallback por filas. Operaciones durables SHALL permanecer separadas del historial.

#### Scenario: Envío y deltas no modifican historial

- **WHEN** se envía una pregunta, espera o recibe contenido incremental sin final completo validado
- **THEN** el documento canónico permanece idéntico y la solicitud recuperable reside sólo en el registro operacional

#### Scenario: Turno final atómico exactamente una vez

- **WHEN** una operación vigente finaliza con respuesta completa validada
- **THEN** una sola transacción agrega pregunta y respuesta completas con ordinals consecutivos y confirma completed; rollback o Stop ganador no deja contenido parcial, y observar completed otra vez no agrega mensajes ni incrementa revisión

#### Scenario: Respuesta alternativa de una pregunta lógica

- **WHEN** se completa A, se completa B y después un retry humano de A
- **THEN** existen dos preguntas y tres respuestas completas con orden explícito, la pregunta A no se duplica y su latest answer se elige por ordinal; lectura, recuperación y contexto usan sólo el documento

#### Scenario: Migración legacy sin pérdida ni doble autoridad

- **WHEN** se ejecuta la transición aislada sin escritores y se reinicia tras un corte de backfill
- **THEN** IDs, textos, metadata, citas, autores nullable y timestamps/precisión legítimos se preservan y contrastan sin duplicación; datos inconsistentes bloquean sin destrucción; la versión sólo se registra tras completitud y los datos originales retenidos no tienen ruta productiva paralela

#### Scenario: Resumen derivado desde el documento

- **WHEN** lectura, retry, recuperación o compresión resuelven el historial y las QA completas
- **THEN** consultan el documento único; un retry invalida el derivado afectado en el mismo commit y reconstruye desde originales, conservando legacy no vinculado visible y excluido de QA/resumen sin adivinar parejas

### Requirement: Verificación independiente de retirada activa

Por instrucción Paris PM10/10/2026 03:03:01 la revisión y validación SHALL aportar evidencia específica de retirada del mecanismo activo sustituido: persistencia, lectores/escritores alternativos, helpers/config/contratos/tests/docs obsoletos y ausencia de doble fuente. SHALL distinguir soporte de migración/compatibilidad estrictamente necesario y evidencia histórica, sin borrar datos para cumplir limpieza. Revisor/Validador SHALL permanecer independientes y sin escrituras bajo guard PM.

#### Scenario: Inspección y ejecución de fuente única

- **WHEN** Revisor inspecciona las rutas activas y Validador ejecuta flujos documentados y contrasta DB
- **THEN** sus informes muestran fuente JSONB, ausencia de modificación al enviar/deltas, cierre atómico una vez, lectura/retry/recuperación/compresión y transición legacy sin escritura paralela; cada resto necesario tiene motivo y carece de ruta alternativa activa

### Requirement: Proyección compatible del esquema de resumen con autoridad local íntegra

Corrección propuesta el 11/10/2026, pendiente de decisión humana previa al código. El sistema SHALL enviar al proveedor una copia de `SummaryResponse` que omita exclusivamente `uniqueItems` en las listas `question_refs` y `answer_refs` de `SummaryTopic`, conservando todos los demás campos y restricciones, json_schema y strict true. SHALL mantener el esquema canónico v2 completo y rechazar referencias duplicadas tanto mediante Pydantic en el processor como mediante la validación local del backend. SHALL distinguir el hash del esquema local del hash de la proyección; no alterar payload, manifest, autorización o artefactos persistidos por esta adaptación.

#### Scenario: Petición proyectada sin alterar el contrato local

- **WHEN** se construye la petición de un lote de resumen autorizado
- **THEN** el esquema enviado carece exactamente de los dos flags uniqueItems y conserva strict true y el resto íntegro; el esquema local mantiene ambos flags y su hash `72404e66533f03268bf53727e7ed01cad00a71c31ad483f823ee4c3c8e06783e`, distinto del hash de proyección `ec92ca50508a0fe0b94ef08ef81c3b1f330973d5b9266d22a53c9b1ca4b8e5ac`

#### Scenario: Referencias repetidas devueltas por el proveedor

- **WHEN** un candidato contiene una referencia repetida en question_refs o answer_refs
- **THEN** processor y backend lo rechazan localmente sin deduplicarlo ni instalarlo, conservan las QA originales y el anterior válido y no hacen otra inferencia automática

#### Scenario: Cambio de transporte sin renovación de memoria ni presupuesto

- **WHEN** cambia únicamente la proyección enviada al proveedor y se prueba la corrección en un entorno aislado reiniciado
- **THEN** los artefactos compatibles continúan sujetos al esquema completo y a las mismas fuentes y epoch; el startup no despacha, un nuevo evento autorizado precede la evaluación y se preservan contadores, reservas, límites y rechazos previos sin afirmar cachehit ni aceptación semántica a partir de simulación

### Requirement: Periodo de respuesta gestionado por el servidor

El sistema SHALL excluir scope.period del esquema solicitado al modelo y conservarlo en FinOpsResponse 1.0. El backend SHALL fijar el periodo desde los registros de costes contrastados por el servidor: un unico intervalo UTC valido, o null si no existe un intervalo inequivoco. El processor SHALL ensamblarlo desde el contexto autenticado antes de validar el contrato completo; el backend SHALL comprobar la correspondencia antes de persistir.

#### Scenario: Pregunta sin periodo financiero verificado

- **WHEN** el contexto no contiene un periodo contrastado o contiene varios periodos distintos
- **THEN** la respuesta final contiene scope.period null y el modelo no puede generar ese campo

#### Scenario: Intervalo verificado unico

- **WHEN** los registros contrastados contienen un unico intervalo UTC con inicio anterior al fin
- **THEN** el servidor conserva exactamente ese intervalo en el contexto congelado y en la respuesta final

#### Scenario: Intento de sustituir el periodo del servidor

- **WHEN** el proveedor devuelve scope.period o el resultado recibido por el backend difiere del periodo congelado
- **THEN** se rechaza la respuesta sin corregir fechas ni persistir el resultado; las fechas del navegador no sustituyen la verificacion del servidor

### Requirement: Instruccion explicita para respuestas no accionables

El prompt de chat SHALL indicar que los estados no_data, insufficient_data, unsupported, refused y error requieren metrics y recommendations vacios. Las sugerencias no financieras para conseguir informacion SHALL expresarse en next_actions. Los validadores existentes SHALL permanecer activos sin reparacion silenciosa del candidato.

#### Scenario: Pantalla sin costes disponibles

- **WHEN** el proveedor responde no_data ante una pantalla vacia
- **THEN** devuelve metrics y recommendations como listas vacias y puede explicar como obtener informacion en next_actions; una respuesta que incumpla esta regla sigue siendo rechazada sin persistir una respuesta parcial

### Requirement: Contexto ampliado con limites conjuntos

El sistema SHALL usar presupuestos configurables de entrada, hasta el contexto
1048576 del modelo, con reservas de instrucciones, esquema, margen y salida800.
Backend y processor SHALL verificar el mismo descriptor de presupuesto. SHALL
conservar limites privados de 2097152 bytes para chat y 1048576 para resumen,
medidos sobre el sobre completo, sin convertir bytes a tokens por aproximacion.
El chat SHALL conservar el mayor sufijo de pares completos que cabe, sin limite
fijo de cuatro y sin duplicar los pares cubiertos por memoria valida.

#### Scenario: Historial mayor que los techos anteriores

- **WHEN** chat supera8192 tokens o un lote de resumen supera4096 y cabe en ambos presupuestos completos
- **THEN** se admite sin truncar mensajes ni evidencia esencial; los originales y validadores de citas, negaciones y periodos permanecen intactos

#### Scenario: Un limite conjunto no permite el siguiente par

- **WHEN** agregar un par completo supera tokens o bytes del sobre con las reservas
- **THEN** se conserva el mayor conjunto que cabe o se devuelve limite explicito si no cabe un par; no se afirma que un millon de tokens quepa en1MiB

### Requirement: Nombres de conversaciones editables y aislados

El ChatPanel SHALL crear el nombre desde la primera pregunta, normalizando espacios
y limitando a 60 puntos de codigo Unicode, sin llamadas adicionales al modelo.
SHALL preservar nombres manuales, incluidos borradores, y no recalcular nombres
de conversaciones existentes al enviar, reintentar o completar respuestas.
La cabecera y cada entrada de historial SHALL ofrecer edicion accesible con lapiz,
guardar/cancelar, Enter/Escape, estado pendiente y error sin perder el texto.
PATCH /assistant/conversations/{conversation_id} SHALL aceptar solo title, normalizar
espacios y rechazar vacio o mas de 60 puntos de codigo con 422. SHALL actualizar
solo title y updated_at con filtro SQL id, tenant_id y user_id autenticados.

#### Scenario: Primer envio y nombre manual

- **WHEN** el primer envio crea una conversacion desde un borrador
- **THEN** el nombre es su nombre manual explicito o los primeros 60 puntos de codigo de la pregunta normalizada; la pregunta se conserva completa

#### Scenario: Edicion y respuestas tardias

- **WHEN** se guarda un nombre desde cabecera o historial y llega una respuesta tardia
- **THEN** se actualizan solo la celda y entrada correspondientes, sin cambiar seleccion; una lectura de historial iniciada antes no revierte el nombre confirmado

#### Scenario: Cancelacion y error

- **WHEN** el usuario cancela con Escape o guardar falla
- **THEN** Escape cancela solo el editor sin escritura ni cierre del panel/dialogo; el fallo conserva nombre previo, texto editable y mensaje de error; no se duplica el envio pendiente

#### Scenario: Propiedad y contenido intacto

- **WHEN** se intenta renombrar un id inexistente, de otro usuario o de otro tenant
- **THEN** se devuelve el mismo 404 sin modificar datos; un renombrado autorizado conserva historial, resumen y operaciones

### Requirement: Eliminacion individual segura de conversaciones

El historial SHALL ofrecer una papelera junto al lapiz en cada conversacion, con
confirmacion modal "¿Estás seguro? No podrás recuperar esta conversación" y botones
"Sí" y "No". No/Escape SHALL cancelar sin escritura; el foco inicial SHALL ser No.
La eliminacion SHALL ser definitiva, individual, autenticada y atomica, sin migracion.
DELETE /assistant/conversations/{id} SHALL devolver204 sin cuerpo o el mismo404
para inexistente/ajena. CORS SHALL permitir DELETE sin ampliar origenes/headers.

#### Scenario: Eliminacion propia y conservacion de terceros

- **WHEN** se confirma una conversacion propia sin trabajo pendiente
- **THEN** una transaccion serializable con bloqueo del padre elimina sus operaciones terminales, mensajes legacy y conversacion con su historial/resumen; no modifica otras conversaciones ni corpus

#### Scenario: Trabajo pendiente o incoherencia

- **WHEN** hay operacion active/waiting/paused o compresion pending/running/reconciling o failed con job/owner residual
- **THEN** se rechaza con409 y explicacion sin borrar; una incoherencia de propietarios o fallo de almacenamiento aborta toda la transaccion

#### Scenario: Confirmacion pendiente y respuestas tardias

- **WHEN** se confirma el borrado y despues responden lectores antiguos
- **THEN** no se duplica DELETE ni se resucitan celda, historial o solicitudes; se cancelan lectores/timers propios, se crea borrador solo si sigue seleccionada la eliminada y se conserva otra seleccion posterior

#### Scenario: Error de eliminacion

- **WHEN** el servidor rechaza o no se confirma el borrado
- **THEN** el modal conserva error visible y los datos locales, sin afirmar exito ni ejecutar inferencia para recuperar

### Requirement: Compresion durable excluyente y recuperable

El sistema SHALL persistir dialogue_compaction JSONB nullable mediante migracion
aditiva nueva. Final y pending SHALL confirmarse atomicamente. La admision SHALL
rechazar nuevos envios ocupados por tenant, usuario y conversacion con409
conversation_compacting, antes de trabajo caro y dentro de reserve, contrastando
revision de historial y hash de resumen del contexto. SHALL mantener disponibles
repeticiones idempotentes y lecturas. Un CAS de control SHALL excluir propietarios
obsoletos; la instalacion valida y la transicion del control SHALL ser atomicas.

#### Scenario: Carrera de envios e instalacion

- **WHEN** dos clientes envian durante compresion o usan contexto anterior a una instalacion
- **THEN** no se crea otra operacion ni se gasta inferencia con memoria obsoleta, y otra conversacion sigue disponible

#### Scenario: Reinicio con ejecucion remota incierta

- **WHEN** se recupera un trabajo running o reconciling tras reinicio o lease vencido
- **THEN** se consulta o cancela el mismo job, sin duplicar dispatch ni liberar por timeout; se muestra recuperacion pendiente hasta confirmar settlement

#### Scenario: Error y recuperacion explicita

- **WHEN** falla la compresion de forma confirmada
- **THEN** se conserva historial y ultimo resumen valido, se expone causa saneada y reintento explicito; un propietario antiguo no puede instalar ni liberar otro control

#### Scenario: Borrador durante compresion

- **WHEN** se abre, recarga o finaliza un chat con memoria ocupada
- **THEN** el frontend recupera el estado del servidor, conserva borrador editable y bloquea Enter y boton hasta instalar la memoria; error y recuperacion son visibles

### Requirement: Reproducible private Compose chat

The project Compose SHALL package pinned offline chat and summary resources and
hash-locked dependencies. The existing exclusive backend migrator SHALL complete
before verify-only API startup. Processor SHALL retain its schema ownership.
The chat listener SHALL bind only a private concrete address, with no host port,
and authenticate with an operator-owned shared HMAC file. Context budgets SHALL
agree between services, with chat output 800 and summary output 10000.

The summary lot SHALL have a configurable independent absolute deadline
SUMMARY_TIMEOUT_SECONDS (30..300 seconds, default 180) mirrored across services.
Its ownership lease SHALL outlast that configured window by 15 seconds. Generation
SHALL reserve five seconds inside the lot deadline for validating/installing the
result. Timeout SHALL preserve originals and existing uncertainty/reconciliation
rules, without changing main-chat deadlines or creating another model dispatch.

#### Scenario: Summary completes after the former 30-second ceiling

- **WHEN** an authenticated summary lot remains within its configured deadline
- **THEN** both private boundaries admit it, the generation timeout uses remaining time minus five seconds, and only a validated result may be installed

#### Scenario: Summary deadline or invalid configuration

- **WHEN** the lot expires or configuration falls outside integer 30..300 seconds
- **THEN** expired work cannot install a result, invalid settings fail startup, and the chat deadline remains unchanged

#### Scenario: Isolated mock startup

- **WHEN** an operator configures a disposable development/test stack with mock providers
- **THEN** chat and compression use explicit deterministic adapters without network inference, disclose simulated output and omissions, preserve originals and validate source references

#### Scenario: Real provider failure

- **WHEN** the AI profile uses the existing JUP-108 gateway and a request fails
- **THEN** no mock fallback runs, and summary uses its separate virtual key without exposing upstream credentials to applications

#### Scenario: Offline image and migration readiness

- **WHEN** built project images start with a read-only root and no model-asset network access
- **THEN** pinned resources are locally available, and backend cannot start before successful migration or silently create schema in verify mode
### Requirement: Evidencia generada limitada al contexto efectivo

La respuesta final SHALL generarse con un esquema derivado de la evidencia del
intento autenticado, incluyendo los resultados documentales aceptados por la
continuacion HMAC. El esquema SHALL permitir solo registros exactos de id, kind,
title y source y excluir duplicados. El backend SHALL conservar su validacion
independiente y SHALL rechazar candidatos invalidos sin reparar, filtrar ni
persistir texto parcial.

#### Scenario: Finalizacion sin fuentes
- **WHEN** auto decide no buscar y no existe evidencia financiera autorizada
- **THEN** el esquema SHALL admitir evidence vacia y estados no accionables; SHALL impedir inventar una cita para emitir ok o partial

#### Scenario: Evidencia recuperada o ajena
- **WHEN** una unica busqueda autenticada devuelve fuentes del alcance actual
- **THEN** la finalizacion SHALL incluir esas fuentes exactas entre las opciones del esquema, sin admitir fuentes de otro usuario/tenant ni metadatos alterados; el presupuesto SHALL contar el esquema efectivo

#### Scenario: Proveedor emite varias herramientas
- **WHEN** el proveedor emite mas de una llamada nativa en una generacion
- **THEN** el intento SHALL fallar antes de ejecutar cualquiera, sin ignorar llamadas extra ni iniciar una tercera generacion; el diagnostico SHALL distinguir cardinalidad multiple de un indice malformado sin registrar argumentos

# Native tool stream normalization

## Requirement: Opciones de driver y diagnostico de recuperacion
La recuperacion acotada MUST conservar las opciones Python del driver para la
conexion real y excluirlas exclusivamente de la comprobacion conninfo libpq.

#### Scenario: Contexto de adaptadores SQLAlchemy
- **WHEN** el driver entrega un AdaptersMap context junto con opciones de conexion
- **THEN** verifica hostname y puerto usando solo opciones libpq y conserva el mismo context en la conexion asincrona
- **AND** conserva peer confiable, TLS, deadline, cancelacion y filtros autenticados

#### Scenario: Recuperacion fallida identificable sin contenido
- **WHEN** embedding, consulta vectorial o validacion de candidatos falla
- **THEN** conserva la omision publica y emite un codigo cerrado de etapa y causa
- **AND** correlaciona solo UUID autenticados de operacion e intento, sin valores, claves, prompts ni mensajes arbitrarios de excepcion

## Requirement: Fragmentos nativos acotados
El processor MUST interpretar campos nativos null como ausencia de fragmento,
sin inventar argumentos ni omitir la validacion final de la herramienta.

#### Scenario: Metadatos repetidos y fragmentos ausentes
- **WHEN** una llamada nativa incluye campos null o repite id y type identicos
- **THEN** conserva un unico id y type y concatena solo fragmentos de nombre y argumentos no null
- **AND** rechaza metadatos contradictorios, tipos invalidos, limites excedidos y nombres finales no autorizados

#### Scenario: Diagnostico nativo sin contenido
- **WHEN** el parser rechaza un fragmento nativo
- **THEN** registra un codigo cerrado de regla sin valores, argumentos ni texto arbitrario de excepcion
