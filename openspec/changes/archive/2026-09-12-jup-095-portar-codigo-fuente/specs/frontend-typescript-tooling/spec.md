## ADDED Requirements

### Requirement: La verificación automática incluye ejecución de pruebas

La cadena de verificación de `apps/frontend` SHALL ejecutar pruebas automáticas reales mediante el
comando de pruebas estándar del paquete, informando de cuántas se han ejecutado. Un marcador que no
ejecuta nada NO SHALL considerarse verificación de pruebas. El comando SHALL terminar con estado de
error cuando alguna prueba falle, de modo que la verificación no pueda pasar en falso.

#### Scenario: El comando de pruebas ejecuta pruebas reales

- **WHEN** se invoca el comando de pruebas del paquete del frontend
- **THEN** se ejecutan las pruebas declaradas en el paquete
- **AND** el resultado informa de cuántas se han ejecutado

#### Scenario: Una prueba fallida detiene la verificación

- **WHEN** una de las pruebas del frontend falla
- **THEN** el comando de pruebas termina con estado de error

#### Scenario: Las pruebas se ejecutan en integración continua

- **WHEN** se propone un cambio que toca el frontend
- **THEN** la integración continua ejecuta las pruebas del frontend sobre ese cambio
- **AND** su resultado es visible junto al resto de comprobaciones de la propuesta
