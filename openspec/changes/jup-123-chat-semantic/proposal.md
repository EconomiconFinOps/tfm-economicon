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

Backend, processor y herramientas de evaluación. No se publica ni despliega B
por esta fase local. N3/N5 no ejecutados y criterios de aceptación del equipo
pendientes: no se inventa un porcentaje aprobado ni se reemplazan reviews.
