# Ingesta documental local

La entrada de archivos acepta MD, TXT UTF-8, PDF, DOCX y DOC. Se selecciona o
arrastra **un archivo por envío**, de 1 a 20.000.000bytes (20 MB decimales).
La reserva de transferencia es por usuario, también entre pestañas, sesiones y
clientes; usuarios distintos pueden subir al mismo cliente simultáneamente.
Tras confirmar la transferencia puede enviarse otro archivo mientras el primero
se procesa en segundo plano. `queued` significa encolado, no completado.

Esta etapa experimental añade extracción/almacenamiento a la cadena existente.
Conserva el formulario de texto, `POST /jobs/ingest`, chunking, embeddings,
modelos, búsqueda y citas. No implementa la fragmentación estructural futura ni
recuperación híbrida. JUP y PR oficiales se formalizan según el proceso del
proyecto; este documento no asigna identificadores ni acredita aceptación humana.

## Arranque y configuración

MinIO forma parte del **Compose general**; no hace falta otro stack documental.
Completar `.env` desde `.env.example`, mantener los opt-ins/secretos existentes y
ejecutar el arranque del README. Además se requieren credenciales distintas para
administración de MinIO y acceso de la aplicación. `minio-init` crea un bucket
privado dedicado, un usuario con acceso sólo a ese bucket y una política fija
de expiración para `staging/`. Repetir el arranque no duplica la regla.

| Variable | Valor inicial / límites | Función |
| --- | --- | --- |
| `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` | secretos propios | Sólo servicio e inicializador; nunca navegador/backend/processor. |
| `DOCUMENT_S3_ACCESS_KEY`, `DOCUMENT_S3_SECRET_KEY` | secretos distintos de root | Identidad de servicio limitada al bucket dedicado. |
| `DOCUMENT_S3_BUCKET` | `document-ingestion` | Bucket exclusivo de esta función; el inicializador administra su política. |
| `DOCUMENT_S3_ENDPOINT` | `http://minio:9000` | Endpoint interno de backend/processor. |
| `DOCUMENT_S3_PUBLIC_ENDPOINT` | `http://localhost:9000` | Endpoint alcanzable por el navegador; host/puerto forman parte de la firma. |
| `DOCUMENT_S3_REGION` | `us-east-1` | Región de firma SigV4. |
| `MINIO_HOST_PORT` | `9000`, loopback | Publicación local del puerto S3. |
| `DOCUMENT_CORS_ORIGINS` | orígenes exactos del frontend, separados por coma | CORS de MinIO; alinear también `CORS_ALLOWED_ORIGINS` del backend. |
| `DOCUMENT_MAX_FILE_BYTES` | `20000000`, configurable1..20000000 | Puede reducir, nunca ampliar el máximo del producto. |
| `DOCUMENT_UPLOAD_URL_SECONDS` | `180`,30..900 | Validez breve del PUT y de la reserva. |
| `DOCUMENT_FAILED_RETENTION_DAYS` | `7`,1..90 | Retención de originales de trabajos fallidos **terminales**, no de reintentos pendientes. |
| `DOCUMENT_MAX_PAGES` | `100`,1..1000 | Límite explícito de páginas PDF. |
| `DOCUMENT_EXTRACTION_SECONDS` | `180`,10..600 | CPU del extractor y plazo de pared exterior, con 5 s para finalizar. |
| `DOCUMENT_OCR_PAGE_SECONDS` | `30`,1..120 | Plazo de Tesseract por página. |
| `DOCUMENT_EXTRACTION_MEMORY_MB` | `1536`,256..4096 | Espacio de direcciones del subproceso. El contenedor processor limita además los procesos a256. |
| `DOCUMENT_OCR_MAX_PIXELS` | `16000000`,1000000..32000000 | Máximo de píxeles renderizados por página. |
| `DOCUMENT_EXECUTION_LEASE_SECONDS` | `300`,15..900 | Reserva de ejecución con renovación cada tercio del plazo. |

El Compose habilita `DOCUMENT_UPLOADS_ENABLED=true` en backend y processor.
Fuera de Compose se habilita expresamente junto con la configuración S3; su
valor por defecto es falso para conservar el arranque anterior. En producción
los endpoints S3 requieren HTTPS. Este Compose local no aprovisiona TLS ni AWS.
No reutilizar claves, volúmenes ni puertos de otra instancia de pruebas.

El [agente CD](../deployment/dockerserver-cd.md) genera también las credenciales
documentales al inicializar o actualizar una raíz anterior, sin rotar valores
existentes. Deriva el puerto S3, su endpoint público y CORS por ranura para que
la release actual y el candidato puedan coexistir durante el relevo. En arranque
manual, `DOCUMENT_S3_PUBLIC_ENDPOINT` debe usar el `MINIO_HOST_PORT` elegido.

El agente CD limita cada build de Compose a 1200 s (`tools/cd/deploy.py`). La primera compilación de MinIO y mc desde fuente tarda entre 8 y 26 minutos según el equipo, así que el primer despliegue de esta versión puede fallar por ese plazo. Antes del primer despliegue, construir `minio` y `minio-init` a mano en el mismo host Docker, desde un clon de esa versión (`docker compose build minio minio-init`), para que el build del agente reutilice las capas en caché.

## Contrato HTTP y autorización

Todas las rutas requieren Bearer y un único `X-Tenant-Id` que corresponda a una
membresía vigente. Usuario y tenant proceden de la autenticación. Las claves de
objeto las elige el servidor; el cliente no puede suministrar una URI descargable.

| Ruta | Contrato |
| --- | --- |
| `POST /jobs/uploads` | JSON `filename`, `file_size`, SHA256 hexadecimal `content_hash`; devuelve201 con `upload_id`, PUT breve, cabeceras firmadas, vencimiento y máximo.409 si existe otra transferencia del mismo usuario;422 para admisión inválida. |
| `POST /jobs/uploads/{id}/confirm` | Verifica objeto real/tamaño/hash/formato y membresía de nuevo; devuelve202 con estado y trabajo. Repetirla devuelve el mismo trabajo. |
| `GET /jobs/uploads/{id}` | Estado de la subida y del trabajo, duplicado y limpieza; sólo su usuario y tenant.404 no revela una subida ajena. |
| `DELETE /jobs/uploads/{id}` | Cancela una reserva todavía sin confirmar y libera sólo su slot. No cancela un trabajo ya aceptado. |
| `GET /jobs/documents/{job_id}` | Contrato normalizado recuperable por el mismo tenant, sin reextraer ni necesitar el original.404 si aún no existe o pertenece a otro tenant. |

El PUT va directamente a S3 con sus cabeceras firmadas: **sin Bearer, cookies ni
cabecera de tenant de la aplicación**. El navegador calcula SHA256 como ayuda;
el servidor verifica los bytes reales. Cambiar un nombre o Content-Type no
convierte contenido inválido en un formato admitido. Nunca se registra el texto
del documento, la firma o las credenciales como evidencia técnica.

El panel calcula ese SHA256 con `crypto.subtle`, que el navegador sólo ofrece en contexto seguro (HTTPS o `localhost`/`127.0.0.1`). Abrir el frontend por `http://<ip>` hace fallar la subida con el mensaje genérico de conexión; usar `localhost`, el túnel a `127.0.0.1` que documenta el CD o HTTPS.

El backend comprueba extensión y contenido. TXT admite UTF-8 estricto, BOM
opcional y normaliza CRLF; no sustituye errores de codificación. DOCX exige ZIP
íntegro, XML Word y MIME coherentes, sin macros/cifrado/rutas de escape. Su
expansión se limita a 80 MB,2000entradas y20 MB por entrada. Sólo se admiten
miembros ZIP sin compresión o DEFLATE, los métodos de OPC; BZip2 y LZMA se
rechazan antes de descomprimir. Se verifican los bytes realmente leídos por
bloques acotados, incluidos tamaños y CRC falseados, sin confiar sólo en las
cabeceras. Los miembros no usados no se acumulan en memoria. El parser XML
rechaza DTD independientemente de la codificación, también UTF-16.
Un 422 de formato muestra el motivo controlado en el panel y exige seleccionar
otro archivo, en vez de ofrecer un reintento de conexión. DOC exige contenedor
OLE Word, sin VBA ni paquete cifrado. PDF exige cabecera y final válidos en la
admisión y un parseo completo posterior. El extractor puede rechazar documentos
corruptos, cifrados, vacíos o que excedan los límites derivados, aunque su tamaño
original sea admisible; no declara éxito truncando contenido silenciosamente.

## Finalización, cola y recuperación

1. La reserva durable usa `user_id` como clave única; no hay mutex global ni
   por tenant. Confirmación/cancelación/expiración liberan únicamente esa reserva.
2. El backend lee `staging/{tenant}/{user}/{upload}`, valida los bytes y los
   escribe en `confirmed/{tenant}/{user}/{upload}` con creación condicional.
   La URL del navegador sólo firma staging. Reutilizarla o sobrescribir staging
   después de confirmar no cambia el objeto final que consume el worker.
3. Confirmación, trabajo y outbox se enlazan en una transacción CockroachDB.
   RabbitMQ recibe IDs/referencias y metadatos autorizados, nunca el archivo ni
   el texto. Una publicación incierta queda pendiente; mantenimiento/reintento
   puede reenviarla. Esto no promete exactamente una entrega del broker.
4. El worker verifica mensaje contra trabajo persistido, autoría y membresía;
   comprueba de nuevo clave/tamaño/hash. Una reserva SQL excluye otra ejecución
   del mismo archivo. El propietario se comprueba antes de persistir checkpoint
   y antes/después del pipeline; una reserva perdida no puede publicar un nuevo
   checkpoint ni marcar completed, running o failed. El descarte terminal
   también requiere una reserva vigente; si la ejecución ya la liberó, el worker
   debe adquirir otra antes de modificar el estado. La persistencia vectorial existente es
   idempotente por trabajo. Un proceso muerto se recupera al vencer su reserva.
5. Se conserva la clasificación de errores/reintentos de la ingesta anterior:
   entradas permanentes se descartan, fallos no clasificados tienen una
   reentrega, fallos al leer/escribir estado se reencolan para no perder trabajo.
   Una interrupción tras checkpoint reutiliza la extracción persistida.

Si un mensaje de archivo coincide íntegramente con el trabajo confirmado pero
se revocó la membresía, el worker revalida la revocación dentro de la transacción
y lo marca failed/terminal bajo su reserva. Libera la referencia de deduplicación
y aplica la retención normal; no procesa el contenido ni deja una cola huérfana.
Un mensaje manipulado o ajeno no autoriza ninguna transición. Restaurar la
membresía no reactiva una entrega terminal; una nueva subida crea otro trabajo.

La deduplicación usa tenant+SHA256; otro tenant no comparte trabajo ni objeto.
Un duplicado devuelve el trabajo existente y un aviso visible, sin reemplazarlo.
El contrato técnico conserva `force_reprocess=true` para una petición deliberada
de reprocesamiento: crea otro trabajo y sustituye la referencia de dedup futura.
La interfaz no presenta casilla de reprocesamiento ni fuerza los envíos normales. Un fallo definitivo ofrece un reintento deliberado; un fallo todavía recuperable se muestra como pendiente de reintento y sigue consultándose.
No hay deduplicación por nombre, ni se confunde hash con ETag multipart.
La visibilidad del normalizado y la deduplicación son compartidas dentro del
tenant: un miembro autorizado puede recuperar un documento de otro miembro y
ver el ID del trabajo duplicado. Las sesiones de subida siguen siendo privadas
del usuario; otro tenant no puede consultar ninguno de esos recursos. Es el
modelo de conocimiento compartido actual, no una autorización entre tenants.
Las referencias heredadas a un fallo terminal no impiden una nueva ingesta del
mismo contenido: la confirmación las sustituye transaccionalmente.

## Documento normalizado y persistencia

La respuesta documental tiene `schema_version:1`, `document_id`, `tenant_id`,
`original_format`, `origin`, `text`, `blocks`, `file_metadata`, `warnings`,
`extraction_method` y `result:extracted`. `origin` conserva fuente/URI, usuario,
tenant y, para archivos, nombre original, tamaño, hash, tipo y fecha de subida.
Los metadatos de extracción permanecen separados de los de origen.

Los bloques son ordenados y tipados: encabezado/párrafo/lista/elemento/tabla/
código/enlace/texto cuando el formato permite reconocerlos. Pueden llevar
`source_lines` (líneas de origen,1-based, extremos incluidos), `page` (1-based),
`bbox` y `coordinate_system` (`pdf_points` o `render_pixels`), nivel, filas/celdas,
lenguaje o destino. Las tablas DOCX contienen bloques por celda y conservan su
posición entre párrafos. No todos los bloques tienen texto o la misma geometría;
la futura fragmentación debe usar el tipo y el formato, no inventar páginas o
jerarquía. Los contenedores Markdown/tablas PDF pueden solaparse con otros
bloques: el texto canónico no se reconstruye concatenándolos sin criterio.
Texto manual produce el mismo contrato con formato `manual-text` y `blocks:[]`.

La migración aditiva006 añade sesiones, slots por usuario, dedup, checkpoint,
partes y reservas de ejecución; no cambia ni destruye tablas/vectores existentes.
`extracted_documents` conserva JSON pequeños y, para documentos grandes, un
manifiesto `sql-parts-v1` con generación, cantidad, tamaño y SHA256. Las partes
de 64000caracteres (máximo 256KB UTF-8) se guardan en transacciones acotadas. El
manifiesto se publica sólo tras todas las partes y bajo la reserva vigente.
Lectura reconstruye y verifica cantidad/orden/tamaño/hash; un intento incompleto
no sustituye un checkpoint anterior. El API devuelve siempre el contrato común,
sin exponer este detalle de almacenamiento. El resultado del trabajo de archivo conserva referencia/versión y metadatos, sin duplicar el texto o los chunks ya persistidos; el resultado de la entrada manual mantiene su contrato anterior. Se evita así exceder el límite de
mensaje SQL de CockroachDB con archivos admitidos de20 MB; no se amplían ajustes
globales de la base. El límite serializado del checkpoint es160 MB/2500 partes.

## Extracción y límites reales

| Formato | Motor | Procedencia y límites |
| --- | --- | --- |
| MD | markdown-it-py | Texto Markdown conservado, tokens/bloques con líneas; no renderiza/ejecuta HTML o enlaces. |
| TXT | decodificación UTF-8 estricta | Texto normalizado y bloque con líneas; sin estructura semántica inventada. |
| DOCX | python-docx/lxml | Orden de párrafos/tablas, títulos/listas reconocibles y propiedades presentes; no reproduce el layout visual ni todos los objetos Word. |
| DOC | LibreOffice Writer local → DOCX | Perfil nuevo por extracción, macros y contenido activo deshabilitados, máximo 60s de conversión dentro del plazo total; una repetición limitada del reinicio normal 81 de LibreOffice. |
| PDF | pdfplumber/pdfminer.six | Texto nativo, líneas/cajas, tablas reconocidas y páginas; el orden del extractor no garantiza orden semántico multicolumna. |
| PDF sin texto o con imagen significativa | PDFium/Pillow + Tesseract `spa+eng` | OCR local por página; imágenes que cubran más del 15 % de la página activan OCR de página completa para páginas híbridas. Registra páginas OCR, cajas en píxeles y advertencias. No infiere títulos ni tablas semánticas desde OCR. |

El worker lanza un subproceso sin secretos heredados, con ficheros temporales
propios y límites de memoria/CPU/descriptores/salida. La salida de extracción se
limita a 80 MB, el texto a 20 millones de caracteres y los bloques a 50000. Un plazo
excedido termina el grupo de procesos, incluidos OCR/conversión, y retira el
directorio temporal. El sandbox necesita Linux amd64/arm64 con Landlock y
libseccomp: restringe lectura/escritura al temporal y a recursos de ejecución de
sólo lectura; deniega sockets de Internet y operaciones de privilegio. Si no
está disponible falla cerrado como problema de entorno; no cae a ejecución libre.

**Capacidad efectiva con OCR.** `DOCUMENT_EXTRACTION_SECONDS` es el plazo total de la extracción de un documento (y el tope de CPU del subproceso), no un plazo por página. El OCR de una página escaneada llena de texto (unas 45 líneas a 200 DPI) cuesta unos 6 s en un equipo de 8 CPU; un PDF digital de 100 páginas se extrae en unos 35 s. Con los valores por defecto (`DOCUMENT_MAX_PAGES=100`, `DOCUMENT_EXTRACTION_SECONDS=180`) caben unas **28 páginas escaneadas densas**: 5 páginas tardan unos 33 s, 20 unos 124 s y 40 terminan en `document_extraction_limit` a los 185 s. Ese fallo es terminal: el panel muestra «Fallido» y un reintento vuelve a agotar el plazo. El límite de 100 páginas sólo se cumple, por tanto, para PDF digitales o con pocas páginas OCR.

Para dimensionarlo, fijar `DOCUMENT_EXTRACTION_SECONDS` en al menos 6 s × páginas OCR esperadas por documento más un margen de 30 s, medido en el equipo de despliegue con un escaneado representativo. El máximo admitido (600 s) da para unas 95 páginas densas; si se esperan escaneados mayores, reducir `DOCUMENT_MAX_PAGES` para que el extractor rechace el PDF al abrirlo, antes de gastar el plazo en OCR. `DOCUMENT_OCR_PAGE_SECONDS` sólo limita cada página y no amplía el plazo total.

La biblioteca estándar y los paquetes de Python se habilitan en sólo lectura
mediante sus rutas de instalación `sysconfig` (`stdlib`, `platstdlib`, `purelib`
y `platlib`). Esto permite el runtime de CI bajo `/opt` y entornos virtuales sin
abrir el prefijo completo, `/opt`, el directorio del proyecto o el `sys.path`
heredado. El extractor sigue sin recibir secretos del servicio.

LibreOffice recibe un directorio IPC propio. Se deniega la prueba heredada de
`access(...,W_OK)` para que use ese directorio: Landlock no media `access(2)` y
LibreOffice, de otro modo, escogería `/tmp` global. Los permisos efectivos siguen
limitados por Landlock. Las pruebas comprueban denegación real de red y de
archivos ajenos, no sólo intención de comportamiento del conversor.

## Retirada de originales

El original final se conserva durante queued/running/reintento. Sólo después de
guardar checkpoint, vectores y estado SQL completed se borran final y staging.
El fallo de borrado no revierte completed: el mantenimiento del backend reintenta
cada 15 s, de forma idempotente y por elemento, sin rehacer el pipeline. Un archivo
fallido no se retira mientras su fallo sea recuperable; sólo un descarte terminal
abre la retención de 7 días. Cancelados, expirados y duplicados se retiran cuando
vence su URL. La limpieza no borra artefactos de otro upload o tenant.

Hasta que vence el PUT, su titular podría recrear staging: el barrido continúa y
`cleanup_done` sólo se fija tras el vencimiento y un borrado satisfactorio. La
regla S3 de 1día afecta **sólo staging**, nunca confirmed ni un original activo.
Las partes derivadas no referenciadas se retiran tras completed o fallo terminal
con retención cumplida; la generación publicada permanece disponible. El
documento normalizado y los datos vectoriales se conservan para RAG y la etapa
siguiente aunque ya no exista el archivo original.

## Reproducción

Las pruebas de Python usan los requisitos de desarrollo de cada aplicación.
Processor necesita las herramientas del Dockerfile o los paquetes equivalentes
de Linux que también instala CI. Los fixtures PDF/DOC se generan localmente;
no se versionan binarios ni documentos privados. Antes de la batería general se
prepara el tokenizer offline fijado mediante `apps/processor/build_tokenizer.py`,
como en CI; si se montan fuentes sobre una imagen, no ocultar ese asset generado.

```text
cd apps/backend
python -m pytest tests/test_document_uploads.py tests/test_document_container_limits.py -q
cd ../processor
python -m pytest tests/test_document_extraction.py tests/test_document_checkpoint.py -q
```

Con el stack desechable y mock en marcha, definir `DOCUMENT_SMOKE_EMAIL` y
`DOCUMENT_SMOKE_PASSWORD` en el entorno local y ejecutar desde la raíz:

```text
python scripts/smoke_file_upload.py --tenant tenant-core --file /ruta/fixture.pdf
```

El smoke de archivo hace autenticación, PUT real, confirmación repetida, consulta hasta
completed y lectura/hash del documento persistido. Emite metadatos técnicos,
sin texto ni URLs firmadas. `cleanup_done:false` inmediato puede corresponder
a la URL todavía vigente; inspección S3 o espera posterior demuestra retirada.
No usa proveedores externos. El smoke existente `scripts/smoke_document_ingestion.py` conserva la entrada de texto y las comprobaciones SQL/vectoriales originales, con sus opciones `--document`, `--tenant` y `--base-url`. La aceptación completa añade servicios reales,
frontera de20 MB, diferentes usuarios/tenants, expiración, reinicios/redelivery,
fallos de persistencia/borrado y recuperación/citas tras retirar originales.
Los vectores mock acreditan el recorrido y el aislamiento; no acreditan mejora
de relevancia o calidad semántica.

Un TXT de 20.000.000 bytes puede producir 44.445 fragmentos con el chunker
actual. Este arreglo no impone un límite de fragmentos ni altera embeddings;
hay que considerar ese coste antes de una ingesta real masiva. La fragmentación
estructural y su presupuesto se coordinan con la etapa siguiente. El formulario
manual conserva por compatibilidad su texto y la URI como referencia: no es
una descarga arbitraria desde esa URI.

## Dependencias y distribución

Las dependencias Python nuevas se declaran por aplicación y quedan resueltas con
hashes en `requirements-documents.lock`, junto a los locks existentes. El build
instala con hashes, ejecuta `pip check` y comprueba declaraciones sin descargar
otra resolución. No se añade SDK de OCR remoto ni librería de interfaz.

| Componente | Licencia principal / distribución |
| --- | --- |
| boto3, botocore y s3transfer | Apache-2.0; SDK S3, sin credenciales de AWS reales. |
| python-docx y markdown-it-py | MIT. |
| pdfplumber y pdfminer.six | MIT. |
| olefile | BSD-2-Clause. |
| lxml | BSD-3-Clause; componentes libxml2/libxslt con sus avisos. |
| Pillow | HPND/MIT-CMU y avisos de bibliotecas incluidas. |
| pypdfium2/PDFium | Apache-2.0/BSD-3-Clause y licencias de terceros del paquete. |
| Tesseract / modelos de idioma | Apache-2.0. |
| LibreOffice | MPL-2.0, componentes y avisos adicionales del paquete de distribución. |
| libseccomp | LGPL-2.1-or-later. |
| MinIO y mc | AGPL-3.0; servicios/binarios separados con LICENSE y fuentes oficiales identificadas en el Dockerfile. |

MinIO se construye desde fuentes oficiales porque la distribución pública
vigente de la versión de seguridad requiere build desde fuente. El Dockerfile
fija releases/archivos por SHA256 y bases por digest; no incorpora ejecutables
del host ni imágenes de terceros no oficiales. MinIO:
`RELEASE.2025-10-15T17-29-55Z`; mc:
`RELEASE.2025-08-13T08-35-41Z`. El build no modifica esas fuentes. Quien
redistribuya la imagen conserva avisos/licencias y facilita las fuentes
correspondientes y las instrucciones de build según sus licencias; no se
presenta MinIO como dependencia permisiva del producto. Las versiones de
paquetes del sistema siguen la distribución de la base fijada y deben revisarse
al mantener la imagen.

Referencias técnicas: [S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html),
[creación condicional](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html),
[MinIO security release](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z),
[pdfplumber](https://github.com/jsvine/pdfplumber),
[python-docx](https://python-docx.readthedocs.io/en/latest/api/document.html),
[Tesseract](https://tesseract-ocr.github.io/tessdoc/),
[Landlock](https://man7.org/linux/man-pages/man7/landlock.7.html),
[LibreOffice IPC](https://github.com/LibreOffice/core/blob/master/sal/osl/unx/pipe.cxx).
