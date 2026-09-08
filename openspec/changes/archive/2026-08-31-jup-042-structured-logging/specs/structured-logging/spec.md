## ADDED Requirements

### Requirement: Logs en JSON estructurado
Los servicios `backend` y `processor` SHALL emitir cada línea de log como un objeto JSON con, como mínimo, los campos `timestamp`, `level`, `service`, `logger` y `event` (el mensaje).

#### Scenario: Log de arranque del servicio
- **WHEN** el servicio `backend` o `processor` arranca
- **THEN** la línea de log emitida es un JSON válido parseable, con los campos `timestamp`, `level`, `service` y `event` presentes

#### Scenario: Log de error con excepción
- **WHEN** se registra un log de nivel `ERROR` con una excepción capturada
- **THEN** el JSON emitido incluye la información de la excepción (tipo, mensaje, traceback) como parte de la estructura, no como texto libre concatenado al `event`

### Requirement: Correlación por request mediante request_id
Cada petición HTTP entrante a `backend` o `processor` SHALL recibir un `request_id` único (UUID), generado por un middleware, y ese `request_id` SHALL aparecer en cada línea de log emitida durante el procesamiento de esa petición, sin que el código de la ruta o de las capas internas lo reciba como parámetro explícito.

#### Scenario: Todas las líneas de una request comparten request_id
- **WHEN** llega una petición HTTP y, durante su procesamiento, se generan varias líneas de log en distintas capas (ruta, servicio, acceso a datos)
- **THEN** todas esas líneas de log incluyen el mismo campo `request_id`

#### Scenario: Peticiones concurrentes no mezclan su request_id
- **WHEN** dos peticiones HTTP se procesan de forma concurrente
- **THEN** los logs de cada una llevan un `request_id` distinto y no se contamina el `request_id` de una petición con logs generados por la otra

#### Scenario: Request sin contexto previo recibe un request_id nuevo
- **WHEN** llega una petición HTTP que no trae ningún identificador de correlación en sus cabeceras
- **THEN** el middleware genera un `request_id` nuevo (UUID) para esa petición

### Requirement: Alcance limitado a servicios de servidor
Esta capability SHALL aplicar únicamente a los servicios `backend` y `processor`. El frontend queda explícitamente fuera de alcance.

#### Scenario: Frontend no se ve afectado
- **WHEN** se implementa esta capability
- **THEN** no se introduce ningún cambio de logging en `apps/frontend`
