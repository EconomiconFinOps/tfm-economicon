## ADDED Requirements

### Requirement: Compatibilidad con activación y aislamiento de A
La entrega semántica MUST conservar los controles de disponibilidad de A:
capacidad autenticada por tenant con booleano efectivo y Cache-Control no-store,
panel oculto salvo confirmación válida y nueva comprobación antes de crear una
conversación. La preparación de CD conserva subred e IP distintas por slot,
HMAC estable y puertos privados. Esto no autoriza activar o desplegar el chat.

#### Scenario: Backend desactivado o disponibilidad no confirmada
- **WHEN** el estado es falso, inválido, está pendiente o falla la consulta
- **THEN** no se monta el acceso del chat ni se crea una conversación por el envío
- **AND** la consulta de capacidades no inicia planificador ni inferencias

#### Scenario: Dos slots preparados con la base de B
- **WHEN** se renderizan ambos slots desde el código reconciliado de B
- **THEN** reciben subred e IP diferentes, HMAC reutilizado y puertos loopback
- **AND** no se declara desplegable un pool que solape una red existente del host

### Requirement: Cobertura de listas documentales completas
El servidor MUST conservar todas las unidades de una sección de reglas en las
rutas conceptuales admitidas de tagging y operación de presupuestos. La compilación
exige rangos originales contiguos y ambos límites de sección, sin rellenar texto
ausente, mezclar políticas o conceder autoridad financiera.

#### Scenario: Una lista completa tiene tabla y reglas adicionales
- **WHEN** una pregunta conceptual admitida tiene una única sección completa y autorizada con lista y tabla citables
- **THEN** el esquema admite sólo el terminal ligado a esa pregunta y sección y el servidor muestra todas sus unidades literales
- **AND** streaming y final conservan paridad y el proveedor no puede añadir auxiliares que contradigan la política

#### Scenario: Falta un extremo o hay contradicción entre fragmentos
- **WHEN** la sección carece de comienzo o cierre original, presenta un hueco o un solapamiento incompatible, o hay dos documentos candidatos
- **THEN** no se compila un terminal completo ni se inventan reglas para rellenarlo
- **AND** permanece la ruta general sin atribuirle las garantías de ese terminal

#### Scenario: La pantalla tiene datos financieros además de la política
- **WHEN** la pregunta es conceptual y el contexto contiene costes contrastados
- **THEN** la respuesta de política conserva sólo sus fuentes documentales y no genera métricas financieras

### Requirement: Recuperación de política en un solo snapshot
La recuperación MUST enlazar encabezado, texto y chunks de una política en la
misma transacción por tenant y proveedor, conservando plazos y límites. No solicita
otro embedding ni convierte una política parcial en completa por truncamiento.

#### Scenario: El ranking no incluye la sección solicitada
- **WHEN** una pregunta conceptual admitida corresponde a una única sección completa del corpus autorizado
- **THEN** la búsqueda exacta por sección puede recuperar sus chunks aunque estén fuera del umbral de similitud
- **AND** conserva la distancia real y el máximo total de20 fragmentos

#### Scenario: El documento cambia durante la recuperación
- **WHEN** otro escritor confirma cambios de texto y chunks entre las lecturas
- **THEN** la búsqueda y las citas conservan la misma versión transaccional de la política

#### Scenario: La política excede los límites o es ambigua
- **WHEN** hay dos documentos candidatos, el documento excede65536 bytes o la expansión requiere más de6 chunks
- **THEN** no se da prioridad a una selección parcial ni se elige arbitrariamente un documento
- **AND** todas las consultas adicionales quedan sujetas al plazo y cancelación existentes

### Requirement: Negativa de ejecución ligada a capacidad del asistente
Ante órdenes directas de cambio de recursos reconocidas por su gramática acotada,
el servidor MUST conservar la ausencia de capacidad de ejecución del asistente.
La respuesta tipada no deriva prerrequisitos para cualquier cambio a partir de
una política documental de rightsizing ni concede autoridad financiera.

#### Scenario: Orden directa de apagado o modificación
- **WHEN** la petición actual ordena una acción reconocida sobre máquinas, VMs u otros recursos
- **THEN** el esquema privado sólo admite la negativa ligada a esa entrada y el servidor ofrece análisis o propuesta revisable, sin ejecutar cambios
- **AND** status es refused, sin métricas, ahorro, citas o recomendaciones inventados, con paridad stream/final

#### Scenario: Pregunta conceptual, negación o instrucción citada
- **WHEN** la entrada pregunta por budgets, explica una operación, niega la orden o sólo la describe en el contexto o una cita
- **THEN** no se activa esa negativa determinista y se conserva la ruta general
- **AND** ni texto recuperado ni un ID de otra entrada pueden imponer o modificar la respuesta de capacidad

### Requirement: Campaña repetida identificable
El evaluador MUST conservar cada caso y repetición del banco original con una
identidad única y hacer visibles las muestras ausentes y los fallos técnicos.

#### Scenario: Falta una repetición aunque están los 28 casos
- **WHEN** el recibo N3 omite la tercera ejecución de un caso
- **THEN** el informe declara la muestra ausente y las 84 muestras esperadas
- **AND** no convierte la cobertura de identificadores en campaña completa

#### Scenario: Repetición ambigua o duplicada
- **WHEN** una fila repetida omite su número o duplica caso y repetición
- **THEN** el evaluador rechaza el recibo sin escoger una respuesta favorable

### Requirement: Evidencia de calidad y comparación
El evaluador MUST comparar requisitos emparejados y mantener pendientes los
juicios inciertos, sin aceptar semántica a partir de heurísticas o estado completed.

#### Scenario: Regresión en una sola repetición
- **WHEN** un requisito pasa a fallar sólo en la segunda repetición
- **THEN** la comparación identifica ese caso y repetición
- **AND** agrupa requisitos del mismo defecto en un fallo por respuesta

### Requirement: Ejecución trazable y limitada
El colector MUST verificar candidato, banco, corpus y contabilidad antes de
iniciar gasto, preservar todos los intentos y respetar el máximo acumulado autorizado.

#### Scenario: Contabilidad o procedencia no verificada
- **WHEN** sólo hay un gasto histórico o no se puede vincular runtime y candidato
- **THEN** la campaña no se inicia y conserva el motivo pendiente

#### Scenario: Reserva insuficiente
- **WHEN** el máximo de coste del siguiente intento supera el saldo autorizado
- **THEN** no se envía la inferencia y se conserva la campaña parcial

#### Scenario: Fallo terminal con coste upstream todavía indeterminado
- **WHEN** la entrada durable y el recibo de un fallo técnico están verificados pero falta prueba completa del coste
- **THEN** el evaluador mantiene el fallo y conserva íntegra su reserva máxima sin considerarlo gratuito o coste conciliado
- **AND** sólo avanza si la contabilidad viva y todas las reservas completas admiten la siguiente operación
- **AND** no repite la operación fallida ni permite este tratamiento para una operación activa

### Requirement: Contrato privado compatible con autoridad y soporte
El esquema de generación MUST exigir soporte documental visible propio para
cada recomendación y no ofrecer selecciones documentales en campos de modos
que no pueden consumir esa autoridad. Los validadores de servidor siguen siendo
obligatorios; la selección literal no acredita por sí sola pertinencia semántica.

#### Scenario: Recomendación sin fuente propia
- **WHEN** se ofrece una recomendación en el contrato privado
- **THEN** su justificación exige seleccionar un pasaje literal autorizado y visible
- **AND** una cita independiente en la respuesta no sustituye ese soporte

#### Scenario: Escenario hipotético sin autoridad documental
- **WHEN** se usa el modo user_scenario o greeting
- **THEN** sus campos auxiliares no ofrecen selecciones documentales que contradigan el modo
- **AND** no se concede autoridad financiera ni se relajan las comprobaciones de servidor

### Requirement: Cobertura aritmética de comparaciones explícitas
El servidor MUST conservar la diferencia absoluta y la desviación relativa sobre
el presupuesto al explicar un escenario hipotético con campos adyacentes y
explícitos de forecast y presupuesto en la misma moneda. No genera el forecast
ni acredita que los valores correspondan a costes reales.

#### Scenario: El modelo omite el porcentaje de exceso
- **WHEN** el modo hipotético recibe forecast1200EUR y presupuesto1000EUR como campos explícitos compatibles
- **THEN** el servidor muestra diferencia200EUR y desviación relativa20% aunque el texto del modelo sólo muestre el ratio120%
- **AND** streaming y respuesta final contienen la misma comparación sin conceder autoridad financiera

#### Scenario: Operandos ambiguos o incompatibles
- **WHEN** hay roles duplicados, moneda distinta, base no positiva o calificadores interpuestos de ámbito o periodo
- **THEN** esa comparación determinista no se aplica y se conserva la ruta general

### Requirement: Citas repetidas sin desbordamiento artificial
El renderer MUST conservar una sola instancia visible de una selección literal
idéntica de la misma fuente dentro de answer, validando cada selección antes de
deduplicar. Conserva los pasajes distintos, el soporte de campos auxiliares y el
límite público de4000caracteres; no trunca silenciosamente contenido único.

#### Scenario: Una cita literal se repite durante la generación
- **WHEN** el modelo repite una selección source_id/passage ya usada en answer
- **THEN** la repetición no añade otra copia al texto público ni a su cómputo de longitud
- **AND** streaming y final mantienen paridad y una cita inventada sigue siendo rechazada

### Requirement: Cobertura completa por coste y número de recursos
El servidor MUST calcular y mostrar ambos porcentajes cuando una petición de
cumplimiento por coste contiene un escenario completo de dos grupos disjuntos,
con número total y conforme, costes de ambos grupos en la misma moneda y
declaración explícita de que todo el coste es etiquetable. Los resultados son
hipotéticos; no verifican las etiquetas ni conceden autoridad financiera.

#### Scenario: El texto del modelo omitiría el resultado ponderado
- **WHEN** nueve de diez recursos cumplen, cuestan100EUR y el restante cuesta900EUR
- **THEN** el terminal de servidor entrega10% por coste y90% por número de recursos
- **AND** no permite reemplazar esos resultados con prosa ni auxiliares contradictorios
- **AND** streaming y final muestran los mismos resultados

#### Scenario: Coste total cero
- **WHEN** el escenario completo declara coste total cero
- **THEN** el cumplimiento por coste queda indefinido y se conserva el porcentaje por recursos
- **AND** no se inventa cumplimiento del0% o100%

#### Scenario: No se puede cerrar la partición o el ámbito
- **WHEN** las cantidades de recursos no suman el total, hay monedas distintas o información adicional no interpretada
- **THEN** no se activa ese terminal y se conserva la ruta general

### Requirement: Localización estructural de fallos del streaming
El diagnóstico MUST identificar el índice de segmento o el intervalo de textos
adyacentes que provoca un rechazo del renderer durante answer, cuando esa
localización es conocida. No registra el texto, la ecuación ni sus hashes y no
relaja el validador ni modifica el error público.

#### Scenario: Ecuación libre fragmentada entre segmentos
- **WHEN** una ecuación prohibida se forma al unir dos segmentos de texto
- **THEN** el rechazo conserva la regla original y registra el intervalo de índices y tipo
- **AND** la localización es estable aunque la trama llegue byte a byte
- **AND** las claves y valores arbitrarios del proveedor nunca forman parte del evento

### Requirement: Atributos y cálculos de un desglose completo de servicios
El servidor MUST conservar período, suscripción, moneda y vista de coste aportados
cuando agrega una lista explícita y completa de importes por servicio. Los nombres
y cantidades son datos variables del escenario; no se convierten en costes verificados.

#### Scenario: Se declara coste actual y se pide total y servicio principal
- **WHEN** se aporta un desglose completo de600/250/150EUR con vista actual
- **THEN** el resultado conserva esa vista, suma1000EUR y muestra el servicio de600EUR con60%
- **AND** no permite añadir una limitación que niegue el atributo declarado

#### Scenario: Hay créditos, empate o total no positivo
- **WHEN** las líneas contienen ajustes negativos o comparten el mayor importe
- **THEN** se conserva la suma con signo y se muestran todos los servicios empatados
- **AND** no se interpreta participación del gasto si el total neto no es positivo
- **AND** un porcentaje redondeado se marca aproximado

#### Scenario: El desglose no es completo o el período no coincide
- **WHEN** hay servicios duplicados, unidades incompatibles, alcance adicional o diferencia de período entre petición y declaración
- **THEN** esa ruta no agrega datos ni borra la ambigüedad y conserva el flujo general

### Requirement: Coste shared sin regla aprobada
El servidor MUST mantener el coste compartido identificado cuando el escenario
declara expresamente que no existe regla aprobada ni consumo por equipo. No infiere
porcentajes ni selecciona citas generales como sustituto de esa regla.

#### Scenario: Se solicita cuánto cargar por equipo sin base de reparto
- **WHEN** la petición y declaración coinciden en importe, moneda y activo compartido
- **THEN** se conserva el coste shared y se pide la regla, su base y los datos que requiera
- **AND** no se reparten importes iguales ni se presentan como aprobados
- **AND** no se añaden citas documentales ajenas para justificar los hechos del usuario

#### Scenario: Los operandos difieren o sí se aporta una regla
- **WHEN** la petición contradice importe, moneda o activo, o la declaración incluye una regla o datos adicionales
- **THEN** no se fuerza la decisión de regla ausente y se conserva el flujo general

### Requirement: Etapas de ahorro y realization ligadas a la entrada
El servidor MUST distinguir ahorro identificado, implementado estimado y verificado
cuando el escenario declara las tres cantidades en una unidad común y define
realization como verificado dividido entre identificado por100. La cantidad realizada
del ejercicio es la verificada; no se suman etapas ni se acreditan ahorros reales.

#### Scenario: Hay tres etapas y una fórmula explícita
- **WHEN** se declaran identificado200EUR/mes, estimado150EUR/mes y verificado80EUR/mes
- **THEN** el terminal conserva las tres etiquetas y muestra80EUR/mes realizado en el ejercicio y40% realization
- **AND** el modelo no puede sustituir esas cantidades o emitir la ecuación como prosa libre
- **AND** streaming, resultado del gateway y respuesta final mantienen paridad

#### Scenario: Denominador cero o resultado redondeado
- **WHEN** el ahorro identificado es cero o el porcentaje no admite representación exacta en seis decimales
- **THEN** la división por cero queda indefinida o el porcentaje redondeado se marca aproximado
- **AND** no se convierte la estimación en ahorro verificado ni se fuerza un máximo de100%

#### Scenario: La declaración de etapas no es coherente o completa
- **WHEN** faltan roles, se duplican, difieren moneda o unidad temporal, o cambia la fórmula o ámbito
- **THEN** esa ruta no infiere los datos faltantes ni convierte unidades y conserva el flujo general
- **AND** una observación financiera del servidor no se sustituye por el escenario del usuario

### Requirement: Definiciones completas sin reforzar sus calificadores
El servidor MUST conservar íntegramente las definiciones documentales pertinentes
al comparar coste actual y amortizado, incluidas sus frases limitantes. Sólo compila
una sección completa, única, autorizada y con pasajes citables en fragmentos reales.

#### Scenario: La fuente usa una conclusión matizada
- **WHEN** la definición dice que actual cost se aproxima a facturación y amortized cost suele ser más útil para showback
- **THEN** se muestran ambas definiciones sin convertirlas en una prohibición o asignación equitativa garantizada
- **AND** una limitación posterior dentro de la definición no se descarta al primer punto

#### Scenario: Sección incompleta o ambigua
- **WHEN** faltan sus límites, hay huecos/solapamientos contradictorios o dos documentos candidatos
- **THEN** no se ofrece el terminal documental ni se inventa una definición de respaldo

### Requirement: Recomendaciones matizadas y premisas desconocidas
El servidor MUST mantener el carácter de consejo de una política que usa conviene,
se recomienda o se aconseja. Al aplicarla a un escenario explícito, conserva por
separado el estado de rightsizing y la demanda estable/inestable/desconocida.

#### Scenario: Rightsizing pendiente y demanda desconocida
- **WHEN** se consulta una compra inmediata con migración prevista, sin precios ni términos
- **THEN** se recomienda resolver los pendientes y evaluar el compromiso sin afirmar que la demanda desconocida es inestable o inexistente
- **AND** se explica el riesgo de infrautilización como condicional, sin inventar plazos, descuentos ni ahorros
- **AND** la falsedad de una conjunción no cambia a falso un operando desconocido

#### Scenario: La política contiene una excepción no interpretada
- **WHEN** la sección añade una excepción o cambia el consejo a otra modalidad o acciones
- **THEN** no se compilan únicamente las frases favorables y se conserva el flujo general

### Requirement: Comparación de coste unitario con etiquetas vinculadas
El servidor MUST vincular cada variación a su métrica al comparar dos períodos
hipotéticos completos y comparables con gasto, volumen y definición explícita de
coste unitario. No infiere comparabilidad, equivalencia de monedas o unidades.

#### Scenario: Sube el gasto y baja el coste por unidad
- **WHEN** el gasto cambia de1000a1200EUR y el volumen de100a200pedidos
- **THEN** el coste unitario cambia de10a6EUR/pedido, con variación absoluta−4 y relativa−40%
- **AND** la variación del gasto200EUR/20% se presenta por separado
- **AND** el proveedor no puede sustituir las etiquetas ni añadir prosa o métricas ajenas al terminal
- **AND** streaming y resultado final coinciden, sin acreditar ahorro real ni calidad del servicio

#### Scenario: Volumen o coste inicial nulos
- **WHEN** hay volumen cero o coste unitario inicial cero
- **THEN** la división correspondiente se declara indefinida y no se inventa un porcentaje
- **AND** los resultados redondeados se marcan aproximados y los operandos conservan su precisión

### Requirement: Riesgo explícito y condicional de rightsizing sin validar
El servidor MUST separar la política literal de su interpretación al aconsejar
sobre una reducción de VM con CPU media y datos de carga incompletos. Solo compila
una sección autorizada, completa y reconocida; no ejecuta cambios.

#### Scenario: CPU media aislada sin recomendación ni ahorro medido
- **WHEN** faltan memoria, I/O, picos y SLA y la política exige validarlos
- **THEN** el consejo pide esos datos, crecimiento y restricciones, y validación humana antes de actuar
- **AND** explica el posible impacto en rendimiento, servicio o SLA como riesgo condicional
- **AND** no afirma una degradación observada, un ahorro garantizado ni que rightsizing siempre signifique reducir
- **AND** las etiquetas históricas inciertas permanecen pendientes de adjudicación independiente
