## ADDED Requirements

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
