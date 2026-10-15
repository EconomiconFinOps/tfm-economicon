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

Backend, processor y herramientas de evaluación. B se conserva sin publicar en
GitHub; el usuario autorizó un entorno aislado en DockerServer y amplió el máximo
acumulado a10USD el15/10, conservando todas las reservas pendientes. La baseline
y las campañas N3 de e23,c7,7be,72 y a545 están recogidas.003/013/015/025 pasan3/3
en producto30596942/cortea54582fb, pero quedan un fallo de coherencia027, dos
incertidumbres020 y un fallo técnico429: B no aceptada. Las mismas claves tienen
vigencia autorizada hasta15/10 a18:00París, sin renovación posterior. N5 y criterios
del equipo siguen pendientes: no se inventa un porcentaje aprobado ni se reemplazan reviews.
