# Fragmentación documental estructural

Actualización documental: 2026-10-16. [JUP-125](https://trello.com/c/H0RUnArf),
rama `feat/JUP-125-deterministic-document-chunking`. Formalización retrospectiva
de la implementación experimental y sus correcciones; no OpenSpec pre-code.
Dependencia JUP-124/PR #133 integrada en develop (`466b083a`, 17/10/2026) e incorporada a esta rama en `4888625e`.
[Matriz de quince criterios](../evidence/JUP-125-validation.md),
[OpenSpec archivado](../../openspec/changes/archive/2026-10-16-jup-125-deterministic-document-chunking/proposal.md)
y [ADR-0023 Proposed](../adr/ADR-0023-deterministic-document-chunking.md).

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
informes adversos originales se conservan. Revisión y validación locales R2
favorables: 175 y 126 pruebas propias afectadas, respectivamente, más recorrido
SQL propio del Validador con nueve formatos y equivalencia completa del lote.
Ambos resolvieron el mismo input de 200.013 caracteres y mantuvieron los negativos
de fragmento ausente/duplicado. PM verificó las mismas referencias sin violaciones.
No equivale a reviews humanas, CI o integración.


## Formalización y base incorporada — 16/10/2026

El checkpoint R2 `5dc63747` preserva el resultado evaluado. PM incorporó JUP-124
`e126b217` mediante `23896393`: seis rutas modificadas y ocho documentos añadidos,
con 1.640 fuentes anteriores byte-idénticas y ningún borrado. Chunker, regresiones,
fixtures y comparación permanecen iguales; sandbox de extracción y su test son
el único delta de producto, evaluado separadamente en fase 1. Se conserva el
sandbox y sólo sus rutas de bibliotecas Python declaradas son de lectura.

OpenSpec, diseño y ADR registran decisiones ya implementadas; la matriz separa
pruebas históricas de controles documentales/consumidores actuales. La nueva base
y documentación requieren evaluación independiente afectada y controles PM nuevos;
no se extienden los PASS R2 automáticamente. No se vuelve a pagar el lote ni se
repite OCR o una batería completa por rutina.

Roles humanos recibidos del liderazgo: Paris lidera; Víctor pairing, Lucía revisión,
Alejandro validación. Asignación no acredita aportaciones. Revisión/validación locales
de esta formalización, ratificación documental del ADR, aprobación final, archivo
específico y publicación quedan separados; no se archiva ni abre PR desde este hito.
La fase 3 espera el cierre coordinado de la fase 2. El estado CI oficial y cualquier
ajuste posterior de base se contrastan por separado en la evidencia JUP-125.


PM incorporó después la corrección evaluada de una única prueba health,
`eb4453f9`, mediante `2bf31fe356aeccc45991c9f91d65dfbba29b003d`, conservando
los trece documentos en preparación y las otras 1.660 fuentes. Los tokens de
prueba se crean al actuar, sin cambios auth/TTL/leeway/runtime. Las ocho variantes
afectadas pasan localmente, separadas de las tres TXT/MD/sandbox y de la evidencia
R2 reutilizada. CI remota del HEAD final y reviews humanas no se presumen.


## Cierre local y archivo autorizado — 16/10/2026

Revisión y validación finales favorables, quince criterios y cuatro comprobaciones
vigentes, con control PM de las mismas referencias sin violaciones. Paris aprobó
el cierre y el archivo; requisitos promovidos y enlaces actualizados en esta rama.
Producto/tests/corpus conservados. Commit/push/CI propia se comprueban después;
publicación de la PR espera que Paris vea el mensaje. Pairing y reviews humanas
no se dan por realizados; ADR-0023 continúa Proposed.


## Reconciliación de base preparada — 17/10/2026

Se prepara sobre `0d34c06b` el merge de JUP-124 `d4c545e7`, que contiene
develop `ffdd8ee9` y los arreglos posteriores de ingesta/pairing/CD. Conflictos
sólo en índices ADR/continuidad, resueltos conservando ambas aportaciones.
Chunker, metadata, rangos, reconstrucción, atomicidad y citas permanecen iguales;
el pipeline automático conserva el documento normalizado y añade los controles
de propiedad/revocación de fase1. El archivo OpenSpec existente no se repite.

Controles propios:128/128 herramientas,2/2CD con Compose real,29/29assistant,
77/77OpenSpec. Processor:332PASS/6fallos de importación del subproceso/6SKIP SQL;
visibilidad de dependencias corregida sólo en entorno y seis casos afectados PASS.
Se preservan ambos recibos; no se afirma otra ejecución completa limpia. Los tests
reutilizan nueve normalizados de extracción real para chunking/reconstrucción/traza;
legacy/tenant/citas SQL y el lote de46vectores se reutilizan por identidad, sin OCR
ni inferencias nuevos. Detalle en la [evidencia](../evidence/JUP-125-validation.md).

Staging/commit y nuevas referencias de integridad corresponden al PM antes de
evaluación independiente de este candidato. Dictámenes previos, CI del padre,
aprobación humana, pairing/reviews y publicación permanecen diferenciados.


## Incorporación del fix del contrato Grafana — 17/10/2026

Sobre `025a5a48`, el liderazgo inicia la incorporación de fase1 `4cf7782d`,
que conserva el fix focal del test de CI después de revisión/validación
independientes y retorno PM. La lógica del test se integra sin conflicto y
permanece idéntica a la evaluada en fase1. El único conflicto, en el índice de
continuidad, se resuelve conservando la información de ingesta y chunking.
No se añade otra reconciliación con develop ni cambia el runtime de fase2.

El archivo afectado se ejecuta **desde este checkout de fase2 con su
`.env.example` real, sin override externo**:30/30casos correctos y14/14de
consumidores de package/CI/documentación,44/44en la misma ejecución
Python3.12/Linux RO/sin red. Los controles negativos previos de fase1 se
reutilizan con atribución por identidad del test, sin repetirlos por rutina.
No se presenta como nueva batería1842ni como CI remota favorable.

Candidato local aún pendiente de staging/commit PM y evaluación independiente
afectada contra referencias PM propias de esta incorporación. El archivo
OpenSpec previo, chunker/metadata/reconstrucción, modelos/citas y evidencias
funcionales anteriores permanecen conservados; participación humana y
publicación se gestionan por separado. Sin servicios o inferencias nuevos.

## Corrección de C13 tras la Validacion JUP-125 — 18/10/2026

La `Validacion JUP-125` de Alejandro sobre `4888625e` (no favorable) reprodujo que `StructuredChunker.validate()` aceptaba procedencia bien formada pero incoherente: una referencia de bloque existente cambiada de `blocks/0` a `blocks/1` con página 999 se publicaba y se citaba, igual que una sección inventada o un `parent_normalized_range=[0,999]`. El validador ahora recalcula desde la estructura del documento las anotaciones de cada tramo y la ruta de sección del chunk, compartiendo con el chunker las funciones `source_spans` y `common_section_path`, y rechaza cualquier diferencia. `tests/test_chunk_provenance_integrity.py` cubre el caso de Alejandro, los nueve formatos tras un viaje JSON (control positivo) y la manipulación de sección, padre, nivel y tipo: 10 fallos sin la corrección y 19 correctos con ella.

C10 (cadena original → normalizado) y C14 (paquete congelado de la comparación de recuperación) siguen pendientes de las evidencias que custodia el liderazgo. Pendiente: revalidación del delta y revisión de Víctor.
