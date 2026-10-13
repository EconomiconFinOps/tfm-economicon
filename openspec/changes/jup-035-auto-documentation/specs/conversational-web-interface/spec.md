## MODIFIED Requirements

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
- **THEN** SHALL usar server-documentation-v4 y derivar la consulta de los primeros2048 caracteres de la pregunta canonica, sin peticion de decision al modelo; SHALL ejecutar como maximo una recuperacion existente con scope autenticado, una operacion y un intento; SHALL conservar contexto/hash inicial congelado y no recuperar antes de iniciar el deadline del intento

#### Scenario: Decision sin herramienta y finalizacion estricta

- **WHEN** termina la recuperacion unica, incluso sin fuentes pertinentes
- **THEN** SHALL realizar una sola generacion FinOpsResponse estricta y sin herramientas nativas; SHALL permitir saludos, aclaraciones, definiciones documentadas y ejercicios hipoteticos utiles sin confundir ausencia de costes reales con imposibilidad de responder; SHALL mantener estados/evidencia y autoridad financiera existentes, deadline comun y uso real de esa unica generacion

#### Scenario: Resultado privado y continuacion final

- **WHEN** el backend obtiene fuentes para el control de recuperacion vigente
- **THEN** SHALL devolver la extension mediante HMAC vinculada al intento, tenant y digest de consulta canonica; SHALL rechazar una consulta que difiera de la derivada del contexto, y continuar con user UNTRUSTED_RETRIEVAL_CONTEXT sin mensajes assistant/tool fabricados; SHALL contar el contexto y esquema final efectivo identicos en ambos servicios y conservar FinOpsResponse1.0 y autoridad exclusiva de billing

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
- **AND** estas instrucciones SHALL aplicarse en el productor, sin borrado posterior de citas ni cambios en esquema publico, retrieval, modelo, routing, reintentos o salida de3200 tokens; el esquema privado exige un extracto literal por cita documental, validado antes de proyectar FinOpsResponse publico

#### Scenario: Formula monetaria con destino y direccion explicitos

- **WHEN** una respuesta considera convertir importes en monedas diferentes
- **THEN** sin destino, fecha y direccion del tipo de cambio autorizados SHALL mantener importes separados y pedir esos datos, sin formular una suma que presuponga un importe ya expresado en el destino desconocido
- **AND** un ejemplo hipotetico de formula SHALL declarar moneda de origen, destino y unidades del tipo de cambio, convirtiendo cada importe necesario al mismo destino sin inventar cotizaciones ni inferir moneda por tenant o configuracion regional
- **AND** las instrucciones aceptadas de unidades y condiciones contractuales SHALL permanecer intactas, sin relajar schema publico ni validadores, retrieval, modelo, routing, plazos ni salida de3200 tokens

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
- **THEN** SHALL conservar el objeto base y sus restricciones en dos ramas completas anyOf con referencias a los mismos $defs, sin duplicar propiedades en la raiz: ok o partial SHALL exigir evidence con minItems 1, y los otros cinco estados SHALL permitir evidence vacia
- **AND** backend y processor SHALL derivar y contabilizar el mismo esquema efectivo, conservar la restriccion financiera autenticada y verificar el hash privado actualizado del manifiesto; el esquema publico FinOpsResponse 1.0 y los validadores SHALL permanecer intactos
- **AND** la cardinalidad SHALL no acreditar pertinencia o autorizacion de citas; la compatibilidad anyOf del endpoint real SHALL requerir un ensayo separado, sin fallback ni reparacion posterior si el proveedor rechaza o incumple el esquema

#### Scenario: Evidencia

- **WHEN** una respuesta afirma hechos basados en fuentes
- **THEN** las citas conservan origen y contenido persistido del tenant autorizado

#### Scenario: Fuentes ajenas

- **WHEN** una salida refiere evidencia desconocida o de otro tenant
- **THEN** el backend rechaza esas referencias al validar el final, antes de guardar la respuesta como confirmada o presentar sus citas como verificadas; la evidencia de entrada se autoriza antes de generar y los fragmentos de texto visibles siguen siendo provisionales


## ADDED Requirements

### Requirement: Evidencia generada limitada al contexto efectivo

La respuesta final SHALL generarse con un esquema derivado de la evidencia del
intento autenticado, incluyendo los resultados documentales aceptados por la
continuacion HMAC. El esquema SHALL permitir solo registros exactos de id, kind,
title y source. La proyeccion enviada SHALL omitir uniqueItems por compatibilidad
con el proveedor; processor y backend SHALL rechazar IDs duplicados
independientemente despues de la generacion. El backend SHALL conservar su validacion
independiente y SHALL rechazar candidatos invalidos sin reparar, filtrar ni
persistir texto parcial.

#### Scenario: Finalizacion sin fuentes
- **WHEN** no hay fuentes pertinentes ni evidencia financiera autorizada
- **THEN** el esquema SHALL admitir evidence vacia y estados no accionables; SHALL impedir inventar una cita para emitir ok o partial, conservando la respuesta util que pueda sustentarse

#### Scenario: Evidencia recuperada o ajena
- **WHEN** una unica busqueda autenticada devuelve fuentes del alcance actual
- **THEN** la finalizacion SHALL incluir esas fuentes exactas entre las opciones del esquema, sin admitir fuentes de otro usuario/tenant ni metadatos alterados; el presupuesto SHALL contar el esquema efectivo

#### Scenario: Control estructurado cerrado
- **WHEN** llega un control alterado, extra, duplicado o ajeno, o el proveedor genera llamadas nativas o JSON final invalido
- **THEN** SHALL rechazarlo sin reparacion ni inferencia adicional; una consulta alterada SHALL rechazarse antes de retrieval y una salida invalida antes de persistir; length SHALL conservar502 incomplete y la politica de reintentos existente

#### Scenario: Sustento literal y pertinencia
- **WHEN** el proveedor selecciona una cita de corpus en la respuesta final
- **THEN** SHALL seleccionar support_quote de ventanas literales no vacias de hasta2048 caracteres enumeradas para ese fragmento; el processor SHALL rechazar selecciones fuera de ese conjunto, y proyectar solo los campos publicos de evidencia tras validarlo
- **AND** el extracto SHALL sustentar una afirmacion pertinente a la pregunta; la coincidencia literal no sustituye la aceptacion semantica, ni autoriza citas accesorias o afirmaciones añadidas para justificarlas; backend y processor SHALL contar la misma variante efectiva del esquema

#### Scenario: Operadores y datos numericos ausentes
- **WHEN** un calculo hipotetico evalua un umbral o combina monedas
- **THEN** SHALL conservar el operador estricto o inclusivo de la fuente, evaluar cada condicion antes de combinar AND u OR y no redondear antes de comparar; SHALL no inventar cotizaciones numericas ni siquiera como ejemplo cuando falta tipo, fecha o destino autorizado

### Requirement: Aritmetica hipotetica calculada y proyectada

La finalizacion privada SHALL representar calculos mediante expresiones tipadas
autocontenidas sobre cantidades indivisibles valor/unidad de la pregunta actual
o de documentos efectivos autenticados. Las cantidades documentales MUST tener
unidad explícita, identificador y contenido de origen concordantes con el mensaje
recuperado y la evidencia autorizada. MUST NOT aportar autoridad de facturación
ni desplazar operandos del usuario cuando se alcance el límite global128.
SHALL evaluar con Decimal sin eval, profundidad maxima4 y doce operaciones en
total entre todos los campos. Ningun calculo SHALL conferir evidencia financiera.

#### Scenario: Cantidades vinculadas al origen
- **WHEN** se construye el esquema final efectivo
- **THEN** SHALL enumerar hasta128 cantidades con origen conservado, unidades adyacentes o contexto monetario/temporal/poblacional inequívoco y aliases no ambiguos; fechas, recuentos y umbrales SHALL no heredar moneda por su mera coexistencia; sin cantidades o al superar128 SHALL no ofrecer expresiones
- **AND** el catalogo SHALL aparecer una sola vez mediante $defs compartidos y niveles finitos; ambos servicios SHALL contar el esquema completo identico, sin intersecciones redundantes de literales

#### Scenario: Operandos, unidades y limites
- **WHEN** una expresion usa una hoja ajena, forma mixta, operacion no admitida, unidades incompatibles, mas de12 operaciones, profundidad excesiva o magnitud fuera de limite
- **THEN** SHALL rechazarla sin reparar operandos ni comprar otra inferencia; SHALL conservar suma/diferencia, cociente dimensional, porcentaje, variacion relativa con baseline explicita y comparacion terminal sin reutilizar booleanos como numeros
- **AND** denominador cero SHALL producir una limitacion explicita de resultado indefinido sin inventar numero; conversion no autorizada SHALL no producir numero y SHALL conservar monedas separadas y solicitud de datos necesarios
- **AND** SHALL comparar sin redondear operandos y marcar aproximacion cuando la salida se redondee a seis decimales; diferencias de porcentajes SHALL mostrarse como puntos porcentuales

#### Scenario: Proyeccion y streaming de expresiones
- **WHEN** la finalizacion incluye segmentos privados text o expression
- **THEN** SHALL renderizar cada expresion como un bloque completo con formula, unidades y resultado o limitacion explicita, sin IDs de resultados generados ni ecuaciones arbitrarias reparadas; SHALL rechazar segmentos mixtos y ecuaciones o marcadores libres incluso partidos entre segmentos text contiguos
- **AND** la raiz publicada SHALL ser una operacion; una cantidad aislada SHALL ser solo operando. Las expresiones SHALL aparecer solo en answer; cada elemento de assumptions, limitations y next_actions SHALL contener exactamente un segmento text de hasta500 caracteres, validado localmente sin truncar
- **AND** SHALL conservar Unicode y escapes fragmentados,128 segmentos,4000 caracteres de answer y500 por elemento de lista, normalizar solo extremos globales, emitir deltas de hasta8192 bytes antes del fin de generacion y hacer coincidir SSE, final validado y JSONB persistido
- **AND** la garantia SHALL limitarse a la operacion renderizada: seleccion semantica, prosa, completitud y pertinencia documental SHALL seguir requiriendo aceptacion real; no se SHALL afirmar entailment universal ni prohibir fechas o cifras originales en prosa

### Requirement: Clasificación documental de intervalos con alcance explícito

El servidor SHALL evaluar las etiquetas de intervalos documentales mediante una
expresión privada `classify`, conservando el esquema público y el máximo global
de12 operaciones. La gramática SHALL exigir fórmula porcentual explícita y una
partición completa de2 a8 intervalos sin huecos ni solapamientos.

#### Scenario: Límite incluido y KPI inequívoco
- **WHEN** una regla documental efectiva tiene un límite incluido y el numerador del escenario tiene una etiqueta léxica inequívoca del mismo KPI
- **THEN** el servidor SHALL calcular el porcentaje y seleccionar la etiqueta con comparaciones Decimal exactas, mostrando la sección y las condiciones en un bloque
- **AND** SHALL exigir las fuentes de la regla en evidence, sin otorgar autoridad financiera a los datos hipotéticos

#### Scenario: Fragmentos ambiguos o clasificación de otro KPI
- **WHEN** faltan rangos contiguos, el solapamiento difiere, hay una fila no interpretable, o el numerador pertenece a otro KPI
- **THEN** el servidor SHALL rechazar la clasificación y no reparar la regla ni trasladar sus umbrales
- **AND** SHALL distinguir secciones por posición original, aunque compartan título, y respetar los encabezados internos del fragmento

#### Scenario: Conclusión libre y límites de la garantía
- **WHEN** una conclusión libre usa vocabulario explícito de clasificación y etiquetas de las reglas disponibles
- **THEN** SHALL rechazarse salvo cita literal respaldada por su fuente, incluso si no existe segmento classify
- **AND** la aceptación semántica SHALL seguir comprobando denominador, pertinencia y prosa; este control acotado no constituye garantía universal de interpretación

### Requirement: Cierre observable y truncacion transitoria

El stream SHALL comunicar el estado confirmado aunque la lectura SQL y la
publicacion RAM se crucen, tanto al POST inicial como a observadores posteriores.
La respuesta final truncada SHALL conservar la politica existente de reintentos y no
persistir texto provisional como confirmado.

#### Scenario: Transicion confirmada antes de publicacion
- **WHEN** completed, failed, paused o waiting ya esta confirmado en SQL y su evento aun no esta publicado
- **THEN** el consumidor SHALL recibir el estado final o de espera correspondiente y cerrar sin perderlo ni duplicarlo

#### Scenario: Lectura anterior a un evento ya publicado
- **WHEN** un observador lee active pero final, terminal, paused o retry_scheduled ya esta publicado al suscribirse
- **THEN** el stream SHALL entregar ese cierre una sola vez en lugar de quedar abierto con heartbeats

#### Scenario: Final con finish_reason length
- **WHEN** la finalizacion termina por longitud
- **THEN** el processor SHALL devolver 502 incomplete, sin candidato confirmado, y el backend SHALL programar un reintento dentro de su politica existente

