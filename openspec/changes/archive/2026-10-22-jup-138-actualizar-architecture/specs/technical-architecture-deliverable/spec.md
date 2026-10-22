## ADDED Requirements

### Requirement: La vista de arquitectura coincide con el stack integrado en su corte

La arquitectura técnica SHALL declarar la SHA de develop contra la que se verificó y, en esa SHA, SHALL
describir cada servicio, red, secreto y volumen de la topología local, así como cada capacidad integrada, sin
afirmaciones que el código contradiga. Las capacidades integradas pero desactivadas por defecto SHALL
describirse como tales, sin presentarlas como activas ni como pendientes. Las que el código prepara para un
entorno sin desplegar SHALL distinguirse de un despliegue realizado.

#### Scenario: Un servicio de Compose aparece en la topología

- **WHEN** un revisor lista los servicios, redes y volúmenes de Compose en la SHA del corte, con los perfiles y
  el overlay de IA
- **THEN** cada uno aparece en la vista de despliegue o tiene una justificación explícita de su ausencia
- **AND** los recuentos de servicios y volúmenes del documento coinciden con esa lista

#### Scenario: Una capacidad integrada está desactivada por defecto

- **WHEN** el documento describe una capacidad cuyo código está integrado pero cuya activación depende de
  configuración, como el chat generativo o la recuperación contextual e híbrida
- **THEN** indica qué la activa y su valor por defecto
- **AND** mantiene rotulado como objetivo lo que no está integrado, como las tools deterministas conectadas al
  agente

#### Scenario: El código admite un entorno cloud que no está desplegado

- **WHEN** el documento menciona modos de aplicación o pipelines para un proveedor cloud
- **THEN** separa lo que el código admite de lo que se ha desplegado a fecha del corte
- **AND** remite el estado operativo a la documentación de ese despliegue en lugar de copiarlo

#### Scenario: El corte declara la SHA verificada

- **WHEN** un lector abre la cabecera del documento
- **THEN** encuentra la fecha y la SHA de develop contra la que se contrastó el contenido
- **AND** el documento no presenta como estado actual un hecho posterior a ese corte
