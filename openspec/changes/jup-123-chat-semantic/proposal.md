JUP: JUP-123

## Why

La entrega A aporta la ingeniería del chat; no acredita la calidad de sus
respuestas. JUP-123 separa la evaluación semántica de esa entrega y conserva
los fallos históricos sin reinterpretar una campaña N=1 como mejora causal.
Trello: https://trello.com/c/TqtcumIN
Dependencia: JUP-122, PR https://github.com/EconomiconFinOps/tfm-economicon/pull/130

## What Changes

- Reconciliar el flujo server-documentation-v4 con la base de ingeniería A.
- Recoger campañas reproducibles y completas del banco original JUP-069.
- Comparar por requisito y repetición, agrupando defectos por respuesta.
- Aplicar correcciones deterministas a cálculos, reglas y evidencia según la
  línea base; separar prompts por modo sólo si las mediciones lo justifican.
- Mantener el chat desactivado por defecto hasta su aceptación.

## Capabilities

### New Capabilities
- `chat-semantic-evaluation`: evidencia repetida, trazabilidad y límites de gasto.

## Impact

Backend, processor y herramientas de evaluación. B sigue local, sin publicar.
El usuario autorizó un entorno aislado y aumentó el máximo acumulado a20USD,
conservando todas las reservas. Claves existentes hasta16/10a18:00París, sin
renovación automática. N3 de5119 completa:327 requisitos originales conformes;
012r1 fallo de calidad y023r3 duda pendientes. N5 detenida por presupuesto112/140,
111conformes/1técnica, sin repetir ese fallo ni liberar máximos. Propuesta21USD no
autorizada ni activada. Integración local2339 con develop53b43 comprobada en código,
SQL e imágenes; su corpus nuevo no hereda la medición de5119. Criterios y adjudicación
independiente pendientes; no aceptación ni reviews simuladas. Detalle y evidencia:
`docs/validation/JUP-123-local-review.md`.
