# Títulos desestimados en JUP reviews

JUP: JUP-126
Trello: https://trello.com/c/SplMvNMA

## Why
PR63 combina una validación desestimada con una revisión complementaria de la
misma persona. La regla histórica de JUP-100 exige una excepción inexistente.
Modificar dictámenes o fabricar acuerdos no es una solución válida.

## What Changes
- Seleccionar el último título de cada tipo por persona y tarjeta; si está
  desestimado no aporta rol ni solapamiento ni revive títulos anteriores.
- Conservar íntegra la resolución de solicitudes de cambios y los controles de
  autor, borradores, títulos, excepciones visibles y errores de API.
- Alinear CONTRIBUTING, AGENTS, especificación y pruebas; proceso2026-10-16.
- Registrar reproducción mínima de PR63 sin reutilizarla como aceptación humana.

## Capabilities
### Modified Capabilities
- `pr-review-validation`: cálculo de títulos que cuentan para el check.

## Impact
Herramienta pura de política, tests y documentación. Sin cambios de workflow,
rulesets, permisos, aplicación o dictámenes en GitHub. La política propuesta
requiere revisión/validación de esta PR antes de integración autorizada.
