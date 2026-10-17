# Índices de embeddings

Actualización documental: 2026-10-17. Implementación experimental en curso sobre
la base de chunking documental, pendiente de identificador oficial de la entrega
y formalización. No implica aceptación, activación estable ni publicación.

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
