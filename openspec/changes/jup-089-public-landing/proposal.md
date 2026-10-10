JUP: JUP-089
Trello: https://trello.com/c/fD7nJKRl

## Why

Economicon necesita explicar su propuesta FinOps públicamente sin publicar la
aplicación privada ni confundir conceptos de marketing con capacidades probadas.
La tarjeta permite construir la landing antes de resolver dominio, M4 y M5 RC1.

## What Changes

- Añadir `apps/landing`, sitio estático autónomo, sin credenciales, API ni sesión.
- Reutilizar la marca y el concepto visual del dossier, y evidencia histórica
  identificada como prueba con API simulada. Separar integrado, simulado y futuro.
- Proporcionar build reproducible, 404 real, metadatos, navegación accesible,
  privacidad sin analítica y contrato de publicación con HTTPS.
- Medir localmente y documentar la evidencia por criterio y sus límites.

No cambia `apps/frontend`, sus tokens ni rutas; la adaptación global corresponde
a JUP-112. No elige ni compra dominio, publica infraestructura, abre DockerServer,
acepta M4/M5, promete ahorro ni acredita roles humanos por inferencia.

## Capabilities

### New Capabilities
- `public-promotional-landing`: escaparate público estático, límites de contenido y publicación.

### Modified Capabilities
None.

## Impact

Nuevo paquete de workspace sin dependencias de runtime; CI específica, documentación,
assets públicos seleccionados y un ADR propuesto para la frontera entre landing y
aplicación. Roles propuestos de Trello conservados: Paris liderazgo, Victor pairing,
Alejandro revisión y Lucia validación. Esta preparación técnica asistida no acredita
pairing ni una revisión independiente.
