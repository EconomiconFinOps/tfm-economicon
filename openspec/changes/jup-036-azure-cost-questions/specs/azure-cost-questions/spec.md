## ADDED Requirements
### Requirement: Selección explícita y autorizada
El chat SHALL aceptar selección estricta de suscripción, cuenta o servicio y periodo UTC [inicio, fin), con tenant y usuario obtenidos de la sesión.
#### Scenario: Periodo omitido
- **WHEN** la selección omite las dos fechas
- **THEN** se consulta el mes UTC actual y se muestra el periodo resuelto
#### Scenario: Selección inválida o conversación ajena
- **WHEN** las fechas son inválidas, hay campos extra o la conversación no pertenece al usuario/tenant
- **THEN** se rechaza antes de consultar gasto o escribir mensajes
### Requirement: Respuesta financiera determinista
El sistema SHALL calcular en el repositorio, separar monedas y conservar créditos y cero.
#### Scenario: Sin filas
- **WHEN** la selección no encuentra filas completadas
- **THEN** responde no_data sin inventar gasto cero
#### Scenario: Solapamiento de fuentes
- **WHEN** dos ingestas completadas cubren una misma suscripción/día
- **THEN** devuelve conflicto sin responder con importes, aunque el filtro de servicio seleccione solo una fuente
### Requirement: Procedencia persistida
La respuesta SHALL conservar selección, snapshot del resultado, ID de evidencia, ingestas y días observados, declarando límites de cobertura.
#### Scenario: Consulta completada
- **WHEN** el usuario consulta un servicio con registros
- **THEN** el chat muestra importes por moneda y conserva evidencia al recargar la conversación sin usar retrieval documental
