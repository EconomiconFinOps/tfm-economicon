## MODIFIED Requirements

### Requirement: Consulta estructurada de propiedad preservada

La retirada del chat ficticio SHALL conservar la consulta de propiedad JUP-037
en una vista especifica, sin cambiar su contrato SQL ni simular generacion LLM.

#### Scenario: Consulta de propiedad sin chat ficticio

- **WHEN** un usuario autenticado abre `/ownership` y envia una pregunta con seleccion de propiedad
- **THEN** el formulario SHALL enviar `ownership_query` obligatorio al endpoint existente, conservar filtros, evidencia y aislamiento por tenant/conversacion; SHALL no permitir envio documental de plantilla
- **AND** `/assistant` SHALL abrir el panel nuevo y el evaluador SHALL usar generaciones; el panel abierto desde `/ownership` SHALL usar captura `no-adapter`, sin datos financieros inferidos

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

#### Scenario: Recuperacion unica determinada por servidor

- **WHEN** comienza un intento autorizado del chat
- **THEN** SHALL utilizar server-documentation-v4, recuperar una vez con los primeros 2048 caracteres de la pregunta canonica y realizar una unica generacion final estructurada, sin decisiones ni llamadas nativas del modelo
- **AND** SHALL conservar claim congelado, HMAC, correlacion, aislamiento, cancelacion y deadline comun; SHALL rechazar resultados ajenos o repetidos y contar contexto y esquema efectivo antes de generar
- **AND** SHALL recuperar tambien ante saludos sin citar resultados irrelevantes; SHALL mantener reasoning high con exclude true, 6400 tokens totales y no registrar razonamiento privado

#### Scenario: Expresiones y segmentos privados verificados

- **WHEN** el modelo expresa un calculo en una respuesta
- **THEN** SHALL usar segmentos privados con expresiones de raiz operacion sobre cantidades autorizadas de valor, unidad y origen; SHALL admitir suma, diferencia, cociente, porcentaje, variacion relativa y comparacion terminal
- **AND** SHALL limitar profundidad a 4, operaciones a 12, cantidades a 128, precision Decimal a 40, entrada a 10^12, resultado a 10^18 y representacion a seis decimales; el denominador calculado SHALL reutilizar el subarbol completo
- **AND** SHALL rechazar operandos ajenos, estructuras y unidades incompatibles sin reparacion por inferencia; cero SHALL ser indefinido y divisas incompatibles no agregables
- **AND** SHALL usar el mismo renderer para streaming y final, conservar FinOpsResponse 1.0 y una pareja persistida; el calculo hipotetico SHALL no convertirse en evidencia financiera

#### Scenario: Seleccion autenticada de citas

- **WHEN** una respuesta cita corpus recuperado
- **THEN** el esquema privado SHALL restringir IDs a registros autorizados y exigir support_quote literal; SHALL validar el pasaje antes de proyectar al formato publico
- **AND** backend SHALL rechazar IDs ajenos o duplicados, procedencia alterada y citas distintas de las conservadas; SHALL conservar fuentes debajo de respuesta e historial
- **AND** la aceptacion real SHALL comprobar pertinencia entre afirmacion y pasaje, no solo literalidad o pertenencia al corpus

#### Scenario: Consulta documental SQL acotada realmente

- **WHEN** la recuperacion documental alcanza SQL
- **THEN** SHALL aplicar los controles de deadline y cancelacion descritos a continuacion

#### Scenario: Decision documental automatica dentro del mismo intento

- **WHEN** comienza el intento IA
- **THEN** la decision documental SHALL corresponder al servidor bajo server-documentation-v4, usando la pregunta canonica truncada a 2048 caracteres; SHALL no solicitar una decision ni herramienta nativa al modelo

#### Scenario: Decision sin herramienta y finalizacion estricta

- **WHEN** el intento responde a un saludo o aclaracion sin necesidad documental semantica
- **THEN** SHALL realizar igualmente la unica recuperacion del servidor y una generacion estricta, sin citar resultados irrelevantes; este escenario historico SHALL no implicar una fase de decision del modelo

#### Scenario: Resultado privado y continuacion final

- **WHEN** backend obtiene la recuperacion del intento
- **THEN** SHALL devolverla por HMAC correlacionada con el control canonico, contabilizar esquema y mensajes efectivos y autorizar una unica generacion; SHALL conservar el claim original y usar contexto recuperado como datos no confiables, no mensajes nativos de herramientas

#### Scenario: Cancelacion, resultado ajeno o segunda herramienta

- **WHEN** vence el plazo, se cancela el intento o llega un resultado ajeno, repetido o una segunda recuperacion
- **THEN** SHALL rechazar la continuacion sin otra generacion ni persistencia, conservando el deadline absoluto y la politica de reintentos del backend

#### Scenario: Plazo SQL de recuperacion

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
- **THEN** el sistema SHALL distinguir truncacion, rechazo contractual y fallo HTTP en sus diagnosticos internos sin registrar prompts, valores rechazados, respuestas, secretos ni excepciones arbitrarias; el chat SHALL reservar la salida configurada, con 6400 tokens por defecto y como maximo aprobado, sin cambiar modelo, deadline ni politica de reintentos

#### Scenario: Semaforo documental verificado

- **WHEN** se clasifica un porcentaje de coste no asignado con un pasaje completo efectivo y autorizado de la regla versionada
- **THEN** SHALL usar classification con rule_id y expresion porcentaje, aplicar <=5 verde, >5 y <=10 amarillo, >10 rojo antes de redondear y renderizar conclusion e intervalo desde el servidor
- **AND** SHALL publicar sus propias citas con pasajes completos autorizados de formula y bandas, incluso si el modelo no las enumera; SHALL rechazar citas entregadas con metadatos/pasajes incorrectos, fuentes ajenas y reglas alteradas; SHALL no emitir color si el denominador es cero o falta regla autorizada
- **AND** SHALL admitir explicaciones y reiteraciones correctas sin exigir una redaccion concreta; la aceptacion funcional SHALL comprobar coherencia documental y ausencia de datos inventados
- **AND** SHALL conservar aritmetica hipotetica sin promoverla a evidencia financiera, renderer comun y formato publico existente

#### Scenario: Afirmaciones sobre politica de tagging

- **WHEN** la respuesta enumera requisitos de tagging
- **THEN** SHALL citar el fragmento que contiene esos requisitos; si no fue recuperado SHALL omitir esa afirmacion y conservar solo la distincion sustentada entre asignacion y cumplimiento

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
- **AND** las instrucciones aceptadas de unidades y condiciones contractuales SHALL permanecer intactas, sin relajar validadores ni cambiar modelo, routing, plazos o salida de 3200 tokens

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

#### Scenario: Finalizacion sin fuentes disponibles

- **WHEN** la finalizacion no dispone de evidencia autorizada inicial ni de fuentes en el resultado validado de la recuperacion
- **THEN** el esquema estricto SHALL exigir evidence vacia y conservar solo la rama de estados no accionables, sin borrar referencias despues de recibirlas ni relajar los validadores
- **AND** con evidencia financiera o documental autorizada SHALL conservar ambas ramas del esquema anterior; la unica generacion SHALL usar el esquema final sin herramientas nativas

#### Scenario: Fuentes ajenas

- **WHEN** una salida refiere evidencia desconocida o de otro tenant
- **THEN** el backend rechaza esas referencias antes de guardar o mostrar la respuesta; los borradores no SHALL emitirse a la interfaz

#### Scenario: Fuente documental vinculada en cualquier estado

- **WHEN** un segmento utiliza documentacion recuperada
- **THEN** SHALL declarar base documental y referencias a evidencia autorizada con pasaje literal, incluso en no_data o refused
- **AND** SHALL rechazarse respaldo ausente o evidencia corpus sin uso; la pertinencia semantica SHALL comprobarse en aceptacion, no mediante filtros de palabras

#### Scenario: Correccion unica bajo autoridad del backend

- **WHEN** una respuesta incumple coherencia de estado, respaldo obligatorio o uso de evidencia y queda margen
- **THEN** backend SHALL autorizar como maximo una correccion dentro de cuatro intentos totales, reutilizando recuperacion autenticada y deadline del intento fallido
- **AND** SHALL conservar contexto canonico, aislamiento, cancelacion, consumo de intentos rechazados y una pareja persistida; la correccion fallida SHALL finalizar sin encadenar reintentos

#### Scenario: Presentacion posterior a validacion

- **WHEN** se genera o corrige una respuesta
- **THEN** SHALL mostrarse progreso sin borrador, y el texto SHALL emitirse solo despues de validar y persistir
- **AND** estados no accionables SHALL exigir metrics y recommendations vacios en esquema del proveedor y validacion final
