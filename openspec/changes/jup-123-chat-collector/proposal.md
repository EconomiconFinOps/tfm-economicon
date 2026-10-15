# Colector independiente de evidencia del chat

JUP: JUP-123
Trello: https://trello.com/c/TqtcumIN

## Why

JUP-071 necesita recoger respuestas del contrato de operaciones de JUP-035/A.
El colector existe en B, cuya aceptación semántica no debe bloquear esa reutilización.
El usuario autoriza extraerlo y publicarlo como PR independiente sobre develop.

## What Changes

- Extraer colector GET, verificación de recuperación exacta y sus pruebas.
- Preparar los29casos de JUP-071 con sus propios prompts, hashes y repeticiones.
- Recoger operaciones existentes y exportar el formato del evaluador071 sin
  inventar respuestas, fragmentos, costes, latencia ni juicios.
- Documentar la copia externa de JUP-071 y ejecutar las pruebas en CI.

## Capabilities

### New Capabilities
- `chat-evidence-collector`: recogida verificable y adaptación para JUP-071.

## Impact

tools, documentación, script de pruebas y una invocación adicional en CI.
Sin cambios en aplicaciones, bancos, corpus, prompts, proveedor o contabilidad.
No se incluye el ejecutor de campañas ni el rediseño semántico de B.
