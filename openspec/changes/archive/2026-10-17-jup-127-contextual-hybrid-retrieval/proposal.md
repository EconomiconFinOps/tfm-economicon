# Optimizar embeddings e implementar recuperación híbrida del RAG

JUP: JUP-127
Trello: https://trello.com/c/AG5fAbl3

## Why

La tercera entrega incremental RAG formaliza índices con identidad verificable,
contexto determinista y búsqueda híbrida sobre JUP-124/JUP-125. Paris selecciona D
el17/10/2026 para el cierre, conservando las correcciones posteriores F1/F2/F3.
La coincidencia de dimensiones o un resultado histórico no acredita el espacio
actual ni una mejora universal de las respuestas.

## What Changes

- Espacios de embeddings con modelo/receta/huella explícitos; lotes completos y
  caché PostgreSQL por tenant/espacio/texto exacto.
- Contexto determinista separado del contenido, con límites y avisos de recorte.
- Generaciones inmutables, construcción/reanudación, activación CAS, publicación
  online, lectura fija, rollback y retención que conservan datos compatibles.
- Dense exacto y FTS/GIN/RRF con elegibilidad lexical conservadora, límites,
  cancelación y aislamiento; cercado del constructor y caché concurrente segura.
- Perfil y guía D: chunking600/800/60, contextual, hybrid/RRF60, small1536/coseno;
  activación sólo tras verificar todos los tenants, con legacy recuperable.
- Evidencia histórica A–D/E cancelada/J5 diferenciada de las comprobaciones nuevas.

## Capabilities

### New Capabilities
- `verified-contextual-retrieval`: identidad, preparación, generaciones y consulta híbrida.

## Impact

Processor/backend, migración aditiva004, configuración Compose/doctor, herramientas
de operación y recogida de evidencia, pruebas y documentación. No se cambia el
generador, prompts, validadores financieros, modelos ni dimensión aprobados. Se
excluye el delta de calculadora/proyección privada del ensayo E, custodiado fuera
del producto. Sin ANN/reranking/Redis, servicios nuevos, despliegue compartido ni
campaña adicional. No archiva ni publica por sí mismo.
