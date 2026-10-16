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
El usuario autorizó el entorno aislado, elegir modelo y un máximo acumulado de
30 USD, conservando todas las reservas. La vigencia actual de las claves acaba
el 16/10 a las 18:00 de París; la solicitud condicional de 19:00 sigue pendiente.
La N5 histórica de 5119 terminó con 140 recogidas: 139 completed, un fallo técnico
y un fallo de calidad en 012; no acredita el corpus o código integrado posteriores.
La corrección de 012 está en a7f9502d: 213 pruebas Windows y 213 Linux conformes,
replay de 167 contextos y dos builds estándar. El corpus nuevo de 54 fragmentos
se cargó tras permisos específicos; ambos máximos de embeddings se conservan.
GLM parcial4 se congela con dos respuestas y dos fallos técnicos 429. La N3
separada DeepSeek/CoreWeave se detuvo por caducidad en80/84:80respuestas localmente
conformes/473comprobaciones y80costes observados. Faltan sólo025–028r3. No es una
N3completa ni aceptación. La recuperación de024r3 fue por GET/SQL, sin nueva respuesta.
Navegador003/012/027, fuentes/fechas/historial/recarga y1280/390px conformes, sin
POSTgenerativos. B anterior restaurado sano y temporales parados.
Criterios y adjudicación independiente siguen pendientes; no reviews simuladas.
Evidencia y límites: `docs/validation/JUP-123-local-review.md`.
