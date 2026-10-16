# Chunking estructural y reprocesamiento

El worker usa `StructuredChunker` sobre el contrato normalizado v1. No es una
nueva extracción ni añade información al contenido enviado al modelo de embeddings.
El chunker por caracteres 500/50 se conserva como baseline explícito en
`app.embeddings.chunker.TextChunker` y en la calibración histórica JUP-022.

## Preparación y configuración

En el entorno Python 3.12 del processor instalar sus requisitos declarados. La
imagen instala los locks con hashes, prepara GLM y cl100k_base y verifica ambos.
Para desarrollar sin cambiar el recurso GLM:

```sh
python apps/processor/build_tokenizer.py --embedding-only
```

El destino por defecto es `~/.cache/economicon/tokenizers/cl100k_base.tiktoken`,
fuera del checkout. `EMBEDDING_TOKENIZER_FILE` permite otro archivo externo; la
imagen usa `/opt/economicon/tokenizers/cl100k_base.tiktoken`. No descargar recursos
dentro del repositorio, aunque estén ignorados. El preparador rechaza ese destino.
Tamaño 1.681.126 bytes, SHA256
`223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7`,
recurso oficial `https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken`.
En ejecución no se descarga nada: archivo ausente, enlace o hash incorrecto
provocan error. La identidad incluye biblioteca 0.14.0, encoding y hash.

| Variable | Default | Validación |
|---|---:|---|
| `EMBEDDING_CHUNK_TARGET_TOKENS` |600| Entero≥8 y≤máximo |
| `EMBEDDING_CHUNK_MAX_TOKENS` |800| Entero≥objetivo y≤800 |
| `EMBEDDING_CHUNK_OVERLAP_RATIO` |0.1| Finito,≥0 y<1 |

El overlap objetivo es `floor(target_tokens * overlap_ratio)`. Incluye contexto
real repetido en el conteo máximo; entre secciones independientes puede ser 0.
Las antiguas variables de caracteres ya no controlan el worker estructural.
Cambiar parámetros sólo afecta ingestas nuevas o reprocesamientos explícitos.

## Contrato, integridad y compatibilidad

`chunk_document(document)` devuelve `chunks` y `manifest`. Un chunk contiene
`chunk_id`, `document_id`, `chunk_index`, `content` y `metadata`:

```json
{
  "content_type":"table",
  "token_count":64,
  "chunk_hash":"sha256 del contenido efectivo",
  "chunking_strategy":"structural_recursive",
  "chunking_version":"1.0.0",
  "chunking_fingerprint":"generación reproducible",
  "configuration_fingerprint":"configuración reproducible",
  "tokenizer_id":"biblioteca:encoding:sha256",
  "source_spans":[],
  "primary_spans":[],
  "repetitions":[],
  "fragments":[],
  "effective_overlap_tokens":0,
  "section_path":null,
  "heading_level":null,
  "warnings":[]
}
```

Este ejemplo describe la forma, no una medición. `source_spans` conserva cada
`normalized_range`, referencia JSON a un bloque real, `original`, ruta de sección
y nivel/depth disponibles. `original` puede contener página, líneas, bbox con
sistema de coordenadas, método OCR y fila/columna. `{}` y referencia `null`
declaran desconocimiento; no inventan metadatos. Un chunk con varias subsecciones
conserva sus rutas por tramo y sólo un prefijo común cuando lo hay.

En TXT y texto manual, los marcadores de lista con indentación explícita
conservan profundidad y `parent_normalized_range`. Un tabulador avanza hasta
la siguiente columna múltiplo de ocho. Los límites de lista priorizan cada
elemento raíz con sus hijos; si ese conjunto excede el presupuesto, el fallback
puede dividirlo conservando la relación en cada tramo. Esos rangos pertenecen
al texto normalizado; no crean ubicaciones del original ni encabezados.

`primary_spans` cubre una sola vez el texto canónico y enlaza posiciones en el
chunk. `repetitions` marca el rango añadido y su razón/tokens. `fragments` conserva
grupo, índice 1-based, total, motivo de división y unidad original. Sólo separadores
puramente blancos pueden omitirse de los embeddings; sus rangos exactos quedan
en `ignored_whitespace_ranges` del manifiesto y el texto padre no se altera.

Los IDs incluyen identidad documental, hash de entrada/configuración/algoritmo/
tokenizador y orden. Dos jobs distintos conservan IDs documentales distintos.
Los timestamps y `publication_id` son operativos y no forman parte de la generación.
Los spans normalizados cuentan caracteres Unicode, base 0 y fin exclusivo, no bytes
ni tokens. `position_contract` define también líneas/páginas y coordenadas.

La migración 003 debe ejecutarse con `PgVectorStore.initialize()` en la preparación
del processor antes de servir consultas con el nuevo backend. Añade JSONB sin
reindexar ni cambiar vectores. `{}` identifica chunks antiguos; la recuperación
mantiene su fallback. Las citas nuevas añaden `source_spans` y `position_contract`
y conservan los campos públicos existentes. No se inventa una página única para
un chunk que contiene varias páginas o texto con ubicación desconocida.

## Reprocesamiento solicitado por operador

En el processor configurado con sus conexiones y proveedor habituales:

```sh
python -m app.reprocess_document --document-id ID --tenant-id TENANT --created-by PROPIETARIO
```

El propietario y pertenencia al tenant se comprueban contra el trabajo existente;
el comando no crea acceso, job, transferencia, endpoint ni nueva extracción.
Sólo admite completed y documento vectorial previo. Carga y verifica el checkpoint,
calcula todos los embeddings y publica padre/chunks/vectores en una transacción.
Una publicación posterior a la lectura inicial causa `StalePublication`: no se
sobrescribe. Un fallo del proveedor o SQL conserva la versión anterior. El estado
completed del job original permanece intacto. No ejecutar en masa sin planificación
y autorización de los datos/coste correspondientes.

## Comprobaciones reproducibles

Con el recurso preparado, desde `apps/processor`:

```sh
python -B -m pytest -q tests/test_chunk_contracts.py tests/test_embedding_tokenization.py tests/test_document_structure.py tests/test_structural_chunker.py tests/test_reprocess_document.py
```

Las nueve fixtures JSON de `tests/fixtures/normalized_documents/` provienen de la
extracción real de archivos sintéticos MD/TXT/PDF digital/OCR/híbrido/DOCX/DOC.
Las pruebas de chunking no vuelven a invocar OCR ni los conversores. Se verifica
la regla real y su aclaración de límites estrictos desde el corpus de negocio,
además de una regla genérica distinta para evitar un algoritmo basado en frases.

`test_chunk_publication_pgvector.py`, `test_tenant_isolation_vector.py` y
`test_vector_settings_pgvector.py` requieren PostgreSQL+pgvector desechable,
autenticado, vacío, en loopback y puerto no habitual. Usar sus opt-ins existentes
`JUP086_VECTOR_TEST_URL` y `JUP102_VECTOR_TEST_URL`; nunca una base de aplicación.
Cada fixture crea/retira su propia base. Cubren sustitución, fallo SQL tras borrar,
dos publicaciones simultáneas, tenant, persistencia JSONB y dimensiones.
El backend conserva sus pruebas reales de ranking, filtros, snapshot y citas.

El smoke `scripts/smoke_document_ingestion.py` verifica ahora chunks enriquecidos,
manifiesto, IDs y tokens mediante HTTP, RabbitMQ y las dos bases. Ejecutarlo con
los requisitos y recurso offline del processor, conservando `--document`,
`--tenant` y `--base-url`; sus opciones de tamaño son ahora
`--expected-target-tokens`, `--expected-max-tokens` y `--expected-overlap-ratio`.

El cierre encontró además 12 fallos de fixtures MinIO en `local-doctor.test.mjs`,
reproducidos sin cambios también sobre el Compose de la base. Ese check no está
verde y su resolución sigue pendiente fuera de esta implementación. No equivale
a un fallo de conexión del entorno de pruebas ni a una aceptación del despliegue.

La comparación congelada y los recibos técnicos se conservan como artefactos de
evaluación externos; el corpus sintético se identifica por SHA256
`1db07751e61e841cfb00d6cd5d5b5aac1b5d989b9e2de7fe92840effeddd030b`.
Repetir recuperación usa sus 46 vectores cacheados y no requiere nuevas llamadas.
Ver metodología, resultados y limitaciones en la
[continuidad](../continuidad/chunking-documental.md). Cualquier nueva inferencia
requiere datos y presupuesto autorizados; no confundir mocks con medición real.

## Límites

Las fuentes que no proporcionan jerarquía, página o coordenadas no pueden
recuperarlas con certeza. Los bloques PDF ambiguos se marcan como no alineados y
se conserva íntegro el texto canónico. Word no identifica siempre cabeceras de
tabla ni profundidad de listas. La primera fila repetida se declara como contexto.
Las citas históricas guardadas son una instantánea de la evidencia usada en su
respuesta; una nueva generación cambia su ID y no reescribe esa conversación.
La muestra de recuperación es exploratoria y demasiado pequeña para atribuir
mejora general. No hay semantic chunking, reranking ni modificación del modelo.
