# Índices de embeddings

Actualización documental: 2026-10-18. Entrega técnica local completada sobre
la base de chunking documental. JUP-127 formaliza la tercera entrega incremental
con [tarjeta oficial](https://trello.com/c/AG5fAbl3), [change](../../openspec/changes/archive/2026-10-17-jup-127-contextual-hybrid-retrieval/proposal.md)
y [evidencia](../evidence/JUP-127-validation.md). Cierre local aprobado por Paris;
no acredita activación estable, CI remota, participación humana ni publicación.

La [guía técnica](../embedding-indexes.md) describe identidad del espacio, preparación
contextual limitada, lotes, caché PostgreSQL por tenant/espacio/texto, snapshots
inmutables, publicación online/CAS, rollback, retención y recuperación FTS/RRF.
La migración 004 es aditiva y conserva las tablas/vectoriales anteriores. Las tres
opciones de consulta verificada/contextual/híbrida permanecen OFF por defecto.

Pruebas propias de desarrollo han ejercitado SQL real con PostgreSQL/pgvector,
incluidas activación, catálogo obsoleto, concurrencia, reanudación, retención,
aislamiento, permisos del operador y snapshot fijo del lector. Se han comprobado
consumidores de pipeline/reprocesado y backend, transporte/cancelación y el colector
nativo con control de presupuesto offline. Los logs adversos y sus correcciones
se conservan fuera de Git; los números de cada pasada no se suman como pruebas
únicas. Una primera revisión independiente detectó tres casos fuera de las
aserciones funcionales iniciales: unidad porcentual, avisos de recorte y nueva
admisión tras coste desconocido. Se corrigen conservando `%` en ambos carriles,
avisos por revisión en el manifiesto consultable y bloqueo de reservas hasta
conciliar coste y fin de operación. Su reevaluación local fue favorable. La integración con el gateway requiere
además vincular su cabecera nativa de despliegue al mapping acreditado, porque
el cuerpo puede conservar el alias lógico. Una evaluación focal detectó que la exigencia se había extendido al lote legacy
y que faltaba propagar el nuevo setting por Compose/doctor. Se corrige separando
modelo esperado explícito del recorrido sin identidad y completando su entrada
operativa. La reevaluación independiente de esta corrección, la comparación
experimental completa y la retirada final se registran por separado; no hay
aceptación global por los resultados locales.

Las comprobaciones de unidad son gratuitas; la comparación real está iniciada
y permanece incompleta. El colector
conserva el banco original y exige capturas sintéticas válidas y evidencia real
del tool result; los ejercicios hipotéticos no se convierten en autoridad financiera
del servidor. No considera `/evidence` como captura completa.
Los resultados locales no acreditan una mejora de recuperación o de respuestas.


La revisión adversarial posterior detectó tres defectos adicionales: un constructor
obsoleto podía invalidar una generación reanudada y activada; dos hits de caché
podían perder recuperación por el mantenimiento concurrente; y una comparación
no soportada conservaba rescate por otro identificador. Se corrigen con cercado
de ejecución, mantenimiento auxiliar no bloqueante/reintento exclusivamente SQL
y cierre conservador de comparaciones incompletas. Pasan 35 pruebas de
generaciones con PostgreSQL y 27 de política; los consumidores directos añaden
82 comprobaciones del lector/contexto y 13 del operador de reprocesado.
Son pruebas propias, pendientes de evaluación independiente de estos bytes.

La campaña anterior conserva sus 272 casos terminales y evidencia externa.
Un ensayo posterior compara recuperación plain densa e híbrida con vectores y
consultas efectivos guardados, sin nuevas llamadas. Sus resultados y límites se
entregan aparte; no reescriben la campaña, su ranking histórico ni el dictamen
adverso original. No implica aceptación, cambio de opciones por defecto ni
activación estable.


La revisión incremental detectó además retroceso del análisis ante puntuación
final tras EUR o %. Se conserva su dictamen adverso y se corrige consumiendo la
unidad antes de validar el sufijo numérico; se añaden dos positivos/negativos
unitarios y dos regresiones FTS reales. La reevaluación corresponde a los mismos
evaluadores sobre referencias independientes nuevas.


La reevaluación v2 corrigió los casos de puntuación, pero mostró aceptación
parcial de números con separadores repetidos. Su dictamen adverso se conserva;
v3 cierra la continuación numérica repetida, mixta o espaciada y añade dos
regresiones FTS y cinco variantes de política. No cambia el lector, F1/F2 ni la
estrategia experimental. Las evidencias previas no afectadas se reutilizan por
identidad, sin presentarlas como ejecuciones nuevas de cada versión.


Paris selecciona D para el cierre de fase 3 el 2026-10-17: chunking estructural
600/800/60, contexto determinista e híbrido FTS/GIN/RRF k60. Se incorpora una
[guía de activación y retorno](../rag-d-activation.md), ejemplos de entorno y
descriptor; conserva OFF general hasta verificar los índices de todos los tenants.
Base reconciliada con develop `1de41b90` mediante `3dc2268a`; F1/F2/F3 conservadas.
El delta de calculadora/proyección privada exclusivo de E se conserva fuera del
producto y queda excluido de RAG. E permanece cancelada. Las cifras de D histórica
no acreditan este candidato nuevo. Revisión/validación independientes y mensaje
PR se preparan para Paris antes de publicación; identificador oficial JUP-127
y rama normativa confirmados por PM. No hay activación compartida ni nueva campaña por estos cambios.


JUP-127 queda formalizada con doce criterios, ADR-0024 Proposed y evidencia
versionada. La preparación CD real detectó la contraseña Grafana ausente; se
porta el fix mínimo ya autorizado con preservación/idempotencia y aserciones RAG
intactas. Las tres omisiones iniciales quedan cubiertas:61 pruebas CD en Windows
con Compose real y2 POSIX en Linux. Las30 del datasource pasan tras retirar su
conteo global rígido, conservando las comprobaciones semánticas. No se despliega,
no se modifican secretos compartidos y no hay nuevas llamadas o gasto.


Cierre local JUP-127: D-v2 recibió REVIEW_PASS y VALIDATION_PASS de evaluadores
distintos, originales y límites íntegros en la evidencia. Ambos roles y BM-0
verificaron 1820 huellas sin diferencias y las MISMAS referencias originales PM;
PM confirmó retorno independiente a las 13:58:53/57 UTC y prearchivo a las
14:06:33/38 UTC, sin violaciones. Recursos propios retirados, cero nuevas
llamadas/gasto y E cancelada. Las cifras históricas no miden calidad nueva.

Paris aprobó el cierre y ordenó archivo, commit y PR (PM, 17/10/2026 15:06:24
Atlantic/Canary). Este ajuste sólo actualiza tareas/estado/evidencia después de
los controles originales; no cambia motor, perfil ni pruebas. El PM ejecutará
archivo/Git/CI/PR y comprobará las rutas resultantes; los mismos evaluadores
resolverán vigencia por adenda documental. No se declaran todavía realizados
archivo, publicación, CI remota, pairing o revisiones humanas.


Archivo ejecutado por PM mediante OpenSpec 1.8 el 17/10/2026, comunicado a las
15:10:10 Atlantic/Canary: change trasladado a la ruta archivada enlazada arriba
y doce requisitos promovidos a `openspec/specs/verified-contextual-retrieval/spec.md`.
Se corrigen sólo enlaces afectados y este estado documental. No equivale a commit,
CI remota, publicación, integración de dependencias o participación humana.

Tras publicar `6ba7d299`, CI39040100565 falla en9 casos backend y2 processor.
La reproducción local conserva ese resultado adverso. La corrección afecta sólo
a tres archivos de pruebas: constructores simulados donde startup los consume,
aserciones de lote/vector/reentrega y compatibilidad individual. Motor D y base
intactos. Pasan129 backend afectados (17 omisiones CockroachDB),179 regresiones
backend, 651 passed, 151 skipped, 6021 warnings in 49.06s en los demás consumidores directos de la fixture,
55 ingesta/reentrega y126 contratos processor. Evidencia y límites en
[JUP-127](../evidence/JUP-127-validation.md). Candidato corregido pendiente de
nuevas guardas y reevaluación independiente; CI posterior, PR, dependencias y
roles humanos conservan su fase. Cero llamadas/coste, sin reanudar E.

## Compatibilidad de citas con fase 2

Corrección local del 18/10 sobre `bc9f6df7`, sin reconciliar otras ramas: adapta
los títulos Markdown y la lectura manual de PR #134 también al índice verificado,
el fallback legacy sólo ante SQL42703 y el diagnóstico de tokenizer en arranque.
Se incorpora después el delta corregido de `3591ac7a`: limpieza ATX sin retroceso
cuadrático y fallback sólo cuando la posición del error señala `metadata` de 003,
con bordes ATX y límites SQL fijados por pruebas. No se copia el lector de fase 2.
Conserva cancelación, aislamiento, caché concurrente y snapshots. El título limpio
puede cambiar input/hash contextual de nuevas ingestas o reprocesos explícitos;
plain no usa ese título y los datos persistidos no se corrigen retroactivamente.
No se reindexa ni activa nada. Pruebas y límites en la
[evidencia existente](../evidence/JUP-127-validation.md#compatibilidad-local-con-pr-134).
Los dictámenes internos de este delta se entregan por separado; no acreditan
las revisiones humanas ni resuelven los conflictos actuales con develop.

## Integración de la base final de fase 2 — 18/10/2026

El PM preparó una copia independiente desde el checkpoint local `27a69cb0`
(los trece archivos ya evaluados sobre `bc9f6df7`) e inició la composición con
`f8dd03bc`, que incorpora develop `0e686f91`. La copia anterior, sus informes
originales y sus guardas permanecen intactos; esos PASS no se trasladan aquí.

Se combinan el lector por generación y la expansión posicional/políticas de B.
Cada expansión consulta únicamente miembros y revisiones de la generación
capturada y vectores de su espacio. Conserva los límites de ambigüedad, bytes,
fragmentos, literalidad, coordenadas canónicas/legacy y 64 tramos. La operación
de prueba se adapta a `server-documentation-v4`; no fuerza el protocolo nativo
antiguo. No se cambia la receta, el proveedor ni las opciones por defecto.

Las pruebas focales SQL/mock, caché y tokenizer están conformes. La corrección
de huellas de fase 2 `fdcccf8e` se incorpora tras contrastar el módulo efectivo;
el manifiesto y pin backend coinciden con ese commit. Pasan la operación,
contexto, citas e historial (49 casos), recursos processor (18) y bundle/diagnóstico
backend (6). El candidato compuesto requiere dos referencias PM nuevas y
evaluaciones independientes propias, cuyos informes se entregan por separado.
Ver la [evidencia de integración](../evidence/JUP-127-validation.md#integracion-local-de-la-base-final--18102026).
Sin nuevas inferencias, gasto, campañas, reindexación ni activación compartida.
