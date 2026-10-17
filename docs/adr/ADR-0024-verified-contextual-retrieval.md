# ADR-0024 — Espacios verificados y recuperación contextual/híbrida

- Estado: Proposed; ratificación humana pendiente.
- Fecha:2026-10-17.
- JUP:[JUP-127](https://trello.com/c/AG5fAbl3).
- Diseño:[change JUP-127](../../openspec/changes/archive/2026-10-17-jup-127-contextual-hybrid-retrieval/design.md).

## Contexto

Legacy no acredita su modelo por tener1536dimensiones. Las entregas JUP-124/125
aportan documentos y chunking determinista. Se necesita evolución verificable
sin mezclar vectores ni perder fuentes, permisos o consulta anterior. Paris
selecciona D para el cierre; la calidad histórica no acredita el candidato actual.

## Decisión

Usar descriptor canónico del espacio y binding operativo al gateway, caché por
tenant/espacio/texto, contexto determinista separado de content y migración004
aditiva. Generaciones completas e inmutables, CAS con catálogo/permisos y lectura
fija aseguran coherencia. F1 cerca ejecuciones obsoletas y F2 hace mantenimiento
de caché no bloqueante con reintento sólo SQL.

Recuperación D: structural_recursive1.0.1 600/800/60, small1536/coseno, contexto128,
entrada1024/16384, dense0.6 y FTS simple/GIN,20por carril, RRF60/pool20, cuatro
semillas y vecinos autorizados. F3 exige literales completos y rechaza rescate
de comparaciones no soportadas; no interpreta fórmulas. El perfil se habilita
explícitamente tras verificar cabezas de todos los tenants. Legacy permanece
recuperable; no se cambia indiscriminadamente la dimensión ni los flags generales.

## Consecuencias

Más almacenamiento y preparación operativa explícita; el gateway sigue siendo
dependencia de confianza. La política conservadora puede reducir recall; no hay
garantía de mejora universal. Fallos/CAS adversos se conservan, no se fuerzan.
Rollback sobre catálogo cambiado requiere reconstrucción autorizada y quizá
presupuesto. No se añaden servicios, ANN, reranking, Redis o funciones del chat.

## Evidencia y estado

[Evidencia técnica](../evidence/JUP-127-validation.md) y
[guía D](../rag-d-activation.md). Evaluación independiente, aprobación final,
archivo/publicación y reviews humanas permanecen explícitos en cada hito; este
ADR no los declara completados ni sustituye las decisiones del equipo.
