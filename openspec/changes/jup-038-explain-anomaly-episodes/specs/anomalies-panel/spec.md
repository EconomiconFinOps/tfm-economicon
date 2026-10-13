## ADDED Requirements

### Requirement: Enlace a la explicación en el asistente

El detalle de una anomalía DEBE (SHALL) ofrecer el enlace «Explicar en el asistente», que abre el
asistente con esa anomalía ya elegida para pedir su explicación. El enlace solo navega: el panel
NO DEBE (SHALL NOT) crear conversaciones ni enviar mensajes. Se ofrece en cualquier estado de la
anomalía, también cuando ya está cerrada o ya no se observa.

#### Scenario: Desde una anomalía abierta
- **WHEN** el usuario abre el detalle de una anomalía y pulsa «Explicar en el asistente»
- **THEN** se abre el asistente con esa anomalía indicada en la dirección
- **AND** el panel no ha enviado ninguna petición nueva al backend

#### Scenario: Desde una anomalía cerrada
- **WHEN** el usuario abre el detalle de una anomalía resuelta o marcada como falso positivo
- **THEN** el enlace se ofrece igual, aunque no haya acciones de estado

#### Scenario: Nombre accesible
- **WHEN** una persona usa un lector de pantalla en el detalle
- **THEN** el enlace se anuncia como enlace con el texto «Explicar en el asistente»
