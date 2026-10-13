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
