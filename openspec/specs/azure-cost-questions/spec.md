# azure-cost-questions Specification

## Purpose
Permitir consultas explícitas de gasto Azure ingerido por suscripción, cuenta de facturación o servicio, con importes deterministas y evidencia persistida del cliente autorizado.
## Requirements
### Requirement: Selección explícita y autorizada
El chat SHALL aceptar selección estricta de suscripción, cuenta o servicio y periodo UTC [inicio, fin), con tenant y usuario obtenidos de la sesión.
#### Scenario: Periodo omitido
- **WHEN** la selección omite las dos fechas
- **THEN** se consulta el mes UTC de la fecha de referencia compartida (el día real UTC si no hay fecha simulada) y se muestra el periodo resuelto
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

#### Scenario: Dos selecciones incompatibles
- **WHEN** una petición incluye cost_query y ownership_query
- **THEN** se rechaza con 422 sin leer costes ni escribir mensajes
#### Scenario: Evidencia Azure en el visor compartido
- **WHEN** se abre la evidencia persistida de una consulta de cuenta
- **THEN** se muestran el desglose exacto y la procedencia de esa selección, conservando el soporte de evidencia de propiedad

#### Scenario: Fecha de referencia anterior al fin solicitado
- **WHEN** el periodo de una selección Azure se extiende más allá de la fecha de referencia
- **THEN** solo se cuentan las filas hasta ese día inclusive, se conservan los filtros y se registra la fecha de referencia en la evidencia

#### Scenario: Identificador de suscripción con mayúsculas
- **WHEN** se consulta una suscripción con mayúsculas o mezcla de mayúsculas y minúsculas
- **THEN** se normaliza como en la ingesta y devuelve el mismo gasto y alcance de conflictos que la selección equivalente en minúsculas
#### Scenario: Fechas con hora o timestamp
- **WHEN** las fechas no siguen el patrón YYYY-MM-DD
- **THEN** se rechazan antes de leer costes o escribir mensajes
#### Scenario: Etiquetas con separadores de línea
- **WHEN** una etiqueta ingerida o seleccionada contiene un salto de línea o U+2028
- **THEN** la respuesta la muestra entre comillas y escapada sin introducir líneas que suplanten importes o evidencia del sistema
