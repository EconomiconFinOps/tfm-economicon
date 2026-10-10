JUP: JUP-038
Trello: https://trello.com/c/QzkjVY7P

## Why

Una marca de anomalía necesita explicar qué regla se cumplió y con qué datos.
El contrato candidato JUP-030 contiene evidencia numérica, pero no demuestra
causas del gasto. Esta contribución permite explicar sus alertas sin inventarlas.

## What Changes

- Explicación determinista en español con evidencia v1, periodos UTC, moneda,
  reglas, calidad, límites y comprobaciones pendientes.
- Entrada autenticada de conversación mediante identificadores y definición;
  el servidor obtiene los importes. Rechazo de fotografías desactualizadas.
- Adaptador explícito al evaluador JUP-030; ausencia del módulo produce 503.
- Pruebas de contrato, errores, aislamiento y persistencia de evidencia.

No incluye detección nueva, forecast, causalidad, ahorro, LLM, interfaz visual
ni modificación del enrutado de texto libre JUP-035/036. El contrato consumido
se verificará sobre la versión de JUP-030 que se integre antes de liberar la PR.

## Capabilities

### New Capabilities

- `anomaly-explanations`: explicación trazable de reglas de anomalía observadas.

### Modified Capabilities

Ninguna.

## Impact

Backend: tres módulos propios, registro de ruta, pruebas y documentación.
Dependencia de JUP-030 para responder con costes reales; en la base develop
`c2995a1` no está integrado. Los dobles de prueba se declaran explícitamente.
Roles Trello conservados: Lucía liderazgo, Paris pairing, Víctor revisión,
Alejandro validación. La contribución no acredita esos trabajos humanos.
