# Índices de embeddings

Actualización documental: 2026-10-16. Implementación experimental en curso sobre
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
