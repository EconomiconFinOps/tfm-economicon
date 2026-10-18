# PR134 / JUP-125 — Evidencia histórica C10 y C14

Paquete preparado el 18/10/2026 por T-800 para Paris y la posterior comprobación humana de Alejandro. Recupera archivos existentes. No constituye aceptación de C10/C14, revisión del producto actual, aprobación humana, CI ni permiso de publicación.

Contexto PM observado el 17/10/2026 a las 23:08:14 UTC: PR134 en ddd3356c8689b45acb3d419a214ed68194029e2b, base 466b083a6dae97f418cfb1d9156325749c6d7304. Los artefactos son históricos y no se atribuyen a ese SHA. C13 fue corregido por Lucía según el contexto PM; su revalidación humana es independiente.

## Comprobación offline

Descomprimir en una carpeta nueva. Con Python 3.10 o posterior, sin instalar dependencias:

    python -B verify_package.py
    python -B replay_cached_cosine.py

Ambos programas sólo leen archivos y escriben el resultado en pantalla. No usan red, proveedor, servicios ni tokenizador; no modifican el paquete. El primero comprueba el conjunto de rutas, tamaños, SHA256 y relaciones descritas abajo. El segundo realiza un cálculo NUEVO de coseno float64 sobre los vectores preservados. No reproduce SQL, filtros tenant/proveedor, backend, citas ni latencias; no ejecuta el candidato actual.

INDEX.json localiza originales, etapas y ausencias. C14/input-vector-index.json relaciona cada input literal con su SHA256 y archivo vectorial. MANIFEST.json incluye todos los archivos salvo el propio manifiesto; sus hashes y los del ZIP se entregan por separado al PM. La huella comprueba identidad frente a una referencia custodiada, no veracidad del recibo ni autenticidad criptográfica del proveedor.

## C10: originales, extracción y fixtures

C10/originals contiene los nueve archivos sintéticos originales, sin recreación. C10/normalized conserva la extracción real congelada de fase1; C10/historical-fixtures conserva copias de las nueve fixtures históricas, idénticas byte a byte. El inventario registra método, ID, hashes, caracteres y bloques.

Cadena comprobable: original → hash de inventario y origin.content_hash → normalizado → hash de fixture histórica → nombres y resultados del recorrido SQL/citas registrado. El normalizador original llama a extract_local; no se repitió OCR/extracción/conversión. Se entregan procedimientos históricos para inspección, no para ejecutarlos directamente sobre estas evidencias.

Los PDFs digital, tabla, escaneado, mixto e híbrido y los documentos TXT/MD/DOC/DOCX conservan sus métodos, páginas/coordenadas/rangos disponibles y advertencias. Las ausencias no se rellenan. Los recibos seleccionados de preparación/extracción e identidades están en C10/receipts.

El procedimiento SQL histórico contrasta contenido/metadata persistidos y reconstruye sólo desde filas chunks antes de comparar con el texto esperado. Un proceso backend separado contrasta recuperación, texto, rangos y citas. El recibo registra los nueve formatos. Usa mock8D y quality_claim:false: prueba un contrato de integración registrado, no calidad semántica. Las copias principal e independiente del resultado son idénticas; no se presentan como campañas nuevas.

**Ausencia material:** no se recuperaron filas SQL/chunks ni objetos completos de citas de esos nueve documentos. El JSON conservado resume comprobaciones con booleanos y no permite reconstruirlos offline desde filas persistidas. El verificador comprueba entradas y correspondencia de recibos; no convierte esos booleanos en nueva validación funcional.

## C14: corpus, inputs, vectores y etapas

Corpus canónico: C14/corpus/evaluation-corpus-frozen-v2.json, SHA256 **1db07751e61e841cfb00d6cd5d5b5aac1b5d989b9e2de7fe92840effeddd030b**. Seis documentos normalizados sintéticos, 10.475 caracteres y doce preguntas con evidencia, documento, rango Unicode fin exclusivo y página esperada. No sustituye extracción real C10. El freeze v2 explica la corrección de forma de celdas Word de la versión preliminar, antes de comparar; no se incluye aquella versión inválida como corpus operativo.

Cada inputs.json conserva documentos, preguntas, chunks antiguos/nuevos, metadata, manifiestos y tiempos offline. El índice vectorial enlaza 25 chunks antiguos + 9 nuevos + 12 preguntas = 46 inputs únicos con 46 vectores reales 1536D. Cada clave es SHA256 del UTF-8 de alias economicon-embedding, byte NUL e input exacto. Cada caché declara upstream openrouter/openai/text-embedding-3-small y alias economicon-embedding.

El recibo del 15/10/2026 23:24:33–35 UTC conserva una llamada HTTP200, 5.839 tokens y 0,00011678 USD conciliados. La recuperación no añade llamadas/gasto. No se recuperó la respuesta HTTP cruda; los vectores efectivos están en los 46 cachés y su inventario histórico de hashes/tamaños.

| Carpeta C14/stages | Versión nueva | Naturaleza |
|---|---|---|
| initial-1.0.0 | 1.0.0 | Inputs y resultado SQL iniciales |
| initial-enriched-1.0.0 | 1.0.0 | Procedencia enriquecida; resultado SQL propio conservado |
| r1-1.0.0 | 1.0.0 | Recalculado offline equivalente al inicial enriquecido; sin SQL propio |
| final-1.0.1 | 1.0.1 | Inputs y resultado SQL final propios; identidad/metadata nuevas |
| r2-1.0.1 | 1.0.1 | Regeneración offline idéntica a final en resultado nuevo completo; sin nuevo SQL |

**Anomalía preservada:** r1-1.0.0/EMPTY-corpus-original.json tiene cero bytes. No se reemplazó. Sus inputs conservan documentos y preguntas completos; el corpus canónico íntegro se entrega aparte. La coincidencia de inputs no transforma ese archivo vacío en corpus físico verificado de R1.

Baseline: TextChunker(500,50), normaliza blancos y usa ventanas de 500 caracteres/paso450. Estructural final: structural_recursive/1.0.1, target600/max800/overlap0,1, tiktoken0.14.0/cl100k_base. Resultado: 25→9 chunks, Recall@1/3/5/10=12/12 en ambos sobre esta muestra exploratoria; no demuestra mejora general. Acierto: mismo documento y evidencia completa en un chunk tras normalizar blancos. SQL histórico: coseno, top20, tenant/proveedor litellm.

Los resultados conservan doce registros por método, citas, top5 documentos y latencias de cada ejecución SQL, no un benchmark general. Las cuatro preguntas PDF conservan citation.page=null y page_provenance_matches=false en ambos métodos; no se presentan páginas como validadas. R2 conserva tiempos offline propios y reutiliza SQL final, sin otra medición SQL.

El verificador reconstruye los seis documentos final/R2 sólo desde chunks, spans primarios y blancos omitidos registrados y después compara con el corpus. No ejecuta la implementación del producto. La metadata inicial/R1 se conserva sin añadir descriptores nuevos.

## Versiones y límites de reproducción

versions conserva locks históricos: pdfplumber0.11.10, python-docx1.2.0, markdown-it-py4.2.0, pypdfium2 5.14.0; tiktoken0.14.0/regex2026.9.29; SQLAlchemy2.0.54, psycopg3.3.6, pydantic2.14.0/pydantic-settings2.15.0. Los locks no acreditan versiones instaladas durante la extracción. No se recuperaron recibos de las versiones ejecutadas Tesseract/LibreOffice, imagen histórica ejecutable ni fijación completa de OS/apt/extensión pgvector.

El recurso físico cl100k_base.tiktoken (SHA256 223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7) no se recuperó en la ruta local documentada. No hubo búsqueda indiscriminada. Tokens son conteos registrados, no retokenizados aquí. Replay de vectores no necesita ese recurso.

C14/historical-procedures/final-compare-real-pgvector.py es el procedimiento SQL original: /evidence para inputs, /vector-cache para vectores, processor importable, backend en /backend, SQL aislado loopback49563, contraseña local por variable de entorno y dos bases nuevas. Crea bases y salida exclusiva. **Es material de inspección, no un comando autocontenido para ejecutar en host o sobre el paquete.** No se incluyen todas las fuentes/dependencias históricas ni infraestructura SQL. Un recorrido sobre candidato actual exigiría identificarlo/preparar recursos propios y sería evidencia nueva. No se repiten SQL/OCR/inferencias para reconstruir pasado.

No se incluyen .env, credenciales, claves, URLs firmadas, logs generales ni corpus privado. Se seleccionan sólo datos sintéticos, recibos y procedimientos necesarios. La ruta local no da acceso a terceros: PM debe facilitar el ZIP por un canal autorizado antes de solicitar comprobación.

Roles actuales comunicados por PM: Paris liderazgo, Lucía pairing, Víctor revisión, Alejandro validación. Siguen pendientes la comprobación humana C10/C14 y revalidación correspondiente de C13.
