JUP: JUP-037
Trello: https://trello.com/c/n4Aplko2

## Why

El chat necesita responder consultas de gasto por proyecto, aplicación, equipo,
centro de coste o etiqueta con cifras verificables y ownership no inferido.

## What Changes

- Añadir `ownership_query` estructurado en el chat y respuesta determinista.
- Reutilizar billing v2, taxonomía existente y contrato de evidencia JUP-036.
- Distinguir selección, contexto, dimensión ausente, cero y falta de datos.
- Guardar evidencia financiera/procedencia autorizada al recargar la conversación.
- Añadir formulario y pruebas de API, SQL y frontend.

El encargo del 10/10 autoriza implementar la tarjeta, incluido su título
equipo/etiqueta, y supera la restricción histórica del refinamiento del 03/10.
No se atribuye pairing o aceptación humana. Sin catálogo nuevo JUP-015, NL libre,
ingesta nueva, conversión de monedas, reparto contable o despliegue.

## Capabilities

### New Capabilities

- `ownership-cost-query`: selección explícita, respuesta y evidencia financiera.

### Modified Capabilities

Ninguna modificación semántica al contrato público de billing v2; la procedencia
se obtiene de forma interna y opcional.

## Impact

Schema/ruta/servicio assistant, lectura de procedencia SQL y formulario del chat.
Sin migraciones. Contrato y límites: `docs/api/ownership-questions.md`.
