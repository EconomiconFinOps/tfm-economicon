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

Backend, processor y evaluación. B sigue local, chat desactivado por defecto.
La corrección012a7f9502d tiene213Windows/213Linux, replay167 y2builds estándar;
54fragmentos cargados con permisos específicos. N3DeepSeek/CoreWeave completa:
84respuestas conformes localmente/495comprobaciones/84costes observados; no
adjudicación independiente, aceptación o superioridad general. UI003/012/027,
fuentes/fechas/historial/recarga y1280/390px conformes, sin POSTgenerativos.
Se continuaron sólo025–028r3 tras el permiso humano24h para las mismas claves,
hasta17/10a18:00París; límites4.5/0.1/contadores/reservas íntegros, cap30USD.
B anterior restaurado sano y temporales parados. Corpus/modelo nuevos no heredan
la N5de5119 ni la parcialGLM; N5actual no ejecutada. Criterios y adjudicación
siguen pendientes; no reviews simuladas ni publicación. Auditoría/paquete203,
costes y límites en `docs/validation/JUP-123-local-review.md` y continuidad.
