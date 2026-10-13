## ADDED Requirements

### Requirement: Enlace a la explicación en el asistente

El detalle de una anomalía DEBE (SHALL) ofrecer el enlace «Explicar en el asistente», que abre el
asistente con esa anomalía ya elegida para pedir su explicación. El enlace solo navega: el panel
NO DEBE (SHALL NOT) crear conversaciones ni enviar mensajes. Se ofrece en cualquier estado de la
anomalía, también cuando ya está cerrada o ya no se observa, siempre que su identificador tenga el formato
real (`anomaly-` seguido de 64 caracteres hexadecimales en minúscula): con otro formato el asistente lo
rechazaría, así que el enlace se omite en lugar de llevar a un aviso.

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

#### Scenario: Identificador sin el formato real
- **WHEN** el identificador de la anomalía no tiene el formato `anomaly-` más 64 caracteres hexadecimales en minúscula
- **THEN** el detalle no ofrece el enlace «Explicar en el asistente»
- **AND** el resto del detalle y sus acciones no cambian
