# JUP-021: runtime vectorial

ADR: not applicable. Se conserva el almacenamiento pgvector y el ranking exacto
existentes; este cambio agrega controles operativos, un indice relacional y evidencia.

Se reutiliza PostgreSQL 17 con pgvector del Compose principal; el Compose aislado
permite validar esta dependencia sin arrancar CockroachDB, RabbitMQ o proveedores
de IA. El volumen conserva datos y el puerto se publica solo en loopback.

La migracion 002 agrega un B-tree de knowledge_documents.tenant_id. Los indices
UNIQUE existentes cubren document_chunks(document_id, chunk_index) y
chunk_embeddings(chunk_id). Se mantiene el ranking coseno exacto: un indice ANN
global puede reducir los resultados tras filtrar tenant. No se acredita escalado
ANN ni un SLA de latencia. Ver [runbook](../../../docs/runbooks/vector-database.md).

El inicializador consulta atttypmod de la columna vector tras migrar y rechaza
desajustes con la dimension configurada. Los lotes de escritura se validan antes
de la transaccion para conservar un documento anterior ante entradas incompatibles.
No se altera ni convierte automaticamente un volumen de otra dimension.

El smoke usa implementaciones actuales de embeddings del processor y backend,
verifica igualdad y recupera contenido real de PostgreSQL. Ambos usan mock SHA-256;
EMBEDDING_MODEL es un alias reservado que actualmente no selecciona otro algoritmo.
Cambiar de modelo exige una base nueva y reingesta; no se infiere compatibilidad
por compartir dimension. No se añade soporte externo de embeddings en esta tarjeta.

Migrar con un unico proceso antes de escalar workers. La exclusión de migraciones
existente es dentro del proceso, no distribuida. El indice 002 se crea en una
transaccion y requiere una ventana sin ingesta para una base existente grande.

La recuperacion restaura un dump custom en otro proyecto Compose con otro puerto
y volumen. Nunca ejecuta DROP ni restaura sobre el origen. La evidencia distingue
despliegue de validacion, revision humana y entorno de produccion.
