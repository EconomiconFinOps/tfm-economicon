# Fragmentación documental estructural

Actualización técnica: 2026-10-16. Etapa experimental en `feat/rag-chunking`,
sobre `7daa2d7962675804a3d5e712d95b9d0e08fcd9f5`, que incorpora la ingesta corregida
documental de la etapa anterior. Sin JUP oficial, PR ni integración en `develop`.

Las nuevas ingestas entregan al grafo el documento normalizado v1 persistido:
texto canónico, bloques, formato, origen y extracción. El chunker no descarga ni
reextrae originales. La entrada manual usa el mismo contrato con estructura
desconocida. El resultado de un trabajo de archivo conserva su resumen, sin
duplicar el normalizado ni el contenido de los chunks en `jobs.result`.

`structural_recursive/1.0.1` identifica límites por formato y agrupa unidades de
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

El paquete de entrega conserva evaluaciones y hallazgos originales; la
corrección de parentesco TXT permanece y se corrigieron las coordenadas Markdown
tras separadores Unicode y la división de subsecciones H3–H6 que caben dentro
de un padre extenso. El extractor Markdown utiliza el mismo dominio de líneas.
Los checkpoints con un bloque desalineado se advierten sin atribuir una referencia falsa.

Los chunks nuevos permiten reconstrucción exacta del normalizado desde contenido
y metadatos, retirando overlap/contexto y conservando blancos omitidos de vectores
en el primer chunk. Longitud/hash/número total permiten rechazar conjuntos
incompletos o incoherentes sin rellenar desde el documento. Ver función e interfaz
en el runbook. Los históricos siguen consultables sin reproceso obligatorio.

Las nueve normalizaciones de extracción real se contrastan con sus fuentes
congeladas: MD/TXT/DOCX/DOC, PDF digital, OCR, mixto/híbrido y tabla. Se verifica
reconstrucción y procedencia real por rangos y referencias; el recorrido de grafo,
pgvector y citas contrasta los nueve formatos. Una comprobación SQL adicional
conserva contenido/IDs/vectores legacy anteriores a la migración junto con chunks
nuevos, consultas/citas actuales y aislamiento entre tenants.

La base incorpora los arreglos de ingesta y las fixtures local:doctor alineadas
con MinIO; los 59 escenarios se han contrastado, incluido el consumidor de reglas.
La recuperación con los 46 vectores cacheados se repitió con IDs/metadata nuevos:
mantiene 12/12 en ambos métodos y no atribuye mejora general. No hubo nuevas
inferencias. El límite de 20 MB se verificó también con reconstrucción exacta.

La revisión y validación independientes finales confirmaron las correcciones
anteriores y los 59 casos de local:doctor, pero detectaron otro borde: espacios
interiores largos conservaban un recuento de fragmentos que incluía piezas
blancas omitidas. Se corrige numerando sólo fragmentos persistidos, manteniendo
los blancos exactos en metadata y los errores de conjuntos incompletos. Los
informes adversos originales se conservan; la reevaluación afectada y la
aprobación humana están pendientes. No acredita cierre ni integración.
