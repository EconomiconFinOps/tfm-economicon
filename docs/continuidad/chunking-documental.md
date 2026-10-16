# Fragmentación documental estructural

Actualización técnica: 2026-10-16. Etapa experimental en `feat/rag-chunking`,
sobre `c201386556a87a727efb301272876eb4bd79c47b`, que incorpora la ingesta
documental de la etapa anterior. Sin JUP oficial, PR ni integración en `develop`.

Las nuevas ingestas entregan al grafo el documento normalizado v1 persistido:
texto canónico, bloques, formato, origen y extracción. El chunker no descarga ni
reextrae originales. La entrada manual usa el mismo contrato con estructura
desconocida. El resultado de un trabajo de archivo conserva su resumen, sin
duplicar el normalizado ni el contenido de los chunks en `jobs.result`.

`structural_recursive/1.0.0` identifica límites por formato y agrupa unidades de
la misma sección. Usa objetivo 600, máximo 800 tokens y overlap 0,1 del objetivo,
medidos con `tiktoken 0.14.0/cl100k_base`. El máximo incluye contexto y repetición.
Una sección completa que cabe se conserva; secciones independientes no comparten
overlap. Si hay que dividir, prioriza filas, elementos de lista, líneas de código,
párrafos, frases y palabras; el último recurso corta por caracteres Unicode
válidos contando sus tokens reales. El overlap efectivo puede ser menor que el
objetivo y se conserva como rangos y número de tokens.

Markdown conserva encabezados, jerarquía, listas, tablas y código del texto
normalizado. Word usa el orden de bloques, filas y celdas y los niveles de título
disponibles; no inventa páginas ni profundidad de listas. PDF digital y OCR usan
anotaciones alineadas con el texto, página y coordenadas declaradas por el
extractor; no convierten píxeles a puntos ni infieren títulos por apariencia.
TXT usa párrafos y marcadores visibles de listas sin inventar encabezados.
Los spans conservan también el lenguaje de código y la referencia al elemento
padre de una sublista cuando el Markdown permite determinarla.

Las tablas se dividen por filas y repiten cabecera Markdown o primera fila como
contexto cuando el extractor no la identificó como cabecera. Una fila/celda/línea
excesiva conserva todos sus caracteres en fragmentos identificados. Un contexto
demasiado largo se repite parcialmente y lo declara; su aparición primaria se
conserva completa. Las posiciones originales desconocidas son explícitas.

Cada chunk conserva ID, orden, contenido, tipo, tokens, hash, jerarquía por tramo,
referencias a bloques y posiciones, fragmentos y repetición. El padre conserva
formato, título, hash, origen, extracción y manifiesto. Las posiciones normalizadas
son puntos de código Unicode, base 0 y fin exclusivo; líneas y páginas originales
base 1, líneas con fin inclusivo. Filas/columnas de tablas son base 0 y fin exclusivo.
No se confunden posiciones canónicas con coordenadas originales.

La migración vectorial 003 añade dos campos JSONB con `{}` por defecto. Los
documentos antiguos mantienen texto, IDs y vectores; sólo los nuevos y los
reprocesamientos explícitos usan IDs derivados de su generación. La sustitución
de padre/chunks/vectores es transaccional, con un identificador operativo separado
para rechazar operaciones obsoletas. No se mezclan generaciones activas. Los
lectores mantienen una instantánea `REPEATABLE READ` entre recuperación y citas.

La recuperación usa metadatos persistidos y conserva procedencia por tramo. Sólo
publica una página o sección única cuando representa al chunk. El fallback de
búsqueda textual queda para chunks antiguos sin metadatos. No cambian modelo,
1536 dimensiones del proveedor real, coseno, ranking, filtros, BM25 ni prompts.
La vectorización recibe únicamente el contenido efectivo del chunk.

Reprocesar exige una petición explícita del operador, un trabajo completed,
propietario/tenant autorizados y checkpoint disponible. No añade endpoints ni
actúa al arrancar o reproducir mensajes completed. Si falta el checkpoint, se
rechaza con explicación y permanece la búsqueda antigua. Ver configuración,
preparación offline y comandos en el [runbook](../runbooks/document-chunking.md).

La comparación exploratoria congelada usa 6 documentos sintéticos normalizados y
12 preguntas con evidencia por documento y tramo/página. Con el mismo modelo real
`openai/text-embedding-3-small` y pgvector:25 chunks antiguos y 9 nuevos; nuevos
16–657 tokens. Recall@1/3/5/10 es 12/12 en ambos. No demuestra mejora de Recall ni
representatividad de producción. El lote deduplicado de 46 entradas/5.839 tokens
costó 0,00011678 USD, conciliado con uso, cabecera y contador del gateway. Los mocks
se usan sólo para contratos, integridad y aislamiento. No acreditan calidad.

El paquete de entrega conserva por separado las evaluaciones locales y sus
evidencias. Esta continuidad no acredita cierre humano ni integración autorizada.
El check obligatorio de herramientas mantiene 12 fallos de fixtures de
`local-doctor.test.mjs` por las variables MinIO; se reproducen también en la base
original y no son una regresión del chunker. Su resolución y el cierre que exija
ese check verde siguen pendientes; no se consideran pruebas superadas.

La corrección local del 16/10 conserva relaciones padre/hijo en listas TXT con
indentación explícita, incluso cuando un hijo se recupera en otro fragmento.
Cinco regresiones nuevas fallan antes de corregir y pasan después junto al núcleo
afectado (99 casos); la reevaluación independiente de esta corrección está pendiente.
