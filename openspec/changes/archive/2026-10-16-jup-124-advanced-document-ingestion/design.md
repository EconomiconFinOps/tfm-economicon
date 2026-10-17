# Diseño documentado retrospectivamente — JUP-124

JUP: JUP-124
Trello: https://trello.com/c/SEkdYIYs
Registro: 2026-10-16. Implementación experimental del 15/10 y correcciones del
16/10; no se atribuye aprobación de este documento antes del código.

## Contexto y candidato

El commit local `688dd7202bc9536f5bd6d4febafa3ee392764df5` contiene la etapa 1
y las correcciones evaluadas. Parte de `53b43bb1e79b08967cc1b9efdf66669f11e8197c`,
base de develop confirmada por el liderazgo el 16/10/2026, sin commits pendientes
de incorporar al iniciar la formalización. Rama oficial:
`feat/JUP-124-advanced-document-ingestion`; destino PR: `develop`.

## Decisiones y ADR

- [ADR-0022](../../../../docs/adr/ADR-0022-document-ingestion-artifact-lifecycle.md)
  registra originales temporales S3, extracción local aislada y normalizado SQL
  durable. Es Proposed para ratificación documental; no introduce otro subsistema.
- Se reutilizan [ADR-0006](../../../../docs/adr/ADR-0006-runtime-secret-boundaries.md)
  para secretos, [ADR-0008](../../../../docs/adr/ADR-0008-tenant-isolation-boundaries.md)
  para autorización y [ADR-0011](../../../../docs/adr/ADR-0011-single-owner-per-table.md)
  para propiedad de tablas/migraciones.
- [ADR-0015](../../../../docs/adr/ADR-0015-local-compose-deployment-boundary.md),
  [ADR-0018](../../../../docs/adr/ADR-0018-private-dockerserver-cd.md) y
  [ADR-0019](../../../../docs/adr/ADR-0019-ingestion-retry-policy.md) conservan sus
  límites de Compose/CD/reintentos y sus estados originales; no se ratifican aquí.

## Recorrido implementado

1. `DocumentUploadPanel` conserva el pegado de texto y añade selección/arrastre
   de un archivo. Muestra progreso y estado del trabajo, sin casilla de
   reprocesado forzoso ni cambios de tema del template.
2. `POST /jobs/uploads` autentica usuario/tenant y reserva un slot por usuario,
   incluso entre sesiones/tenants. Distintos usuarios pueden subir al mismo
   tenant. Devuelve PUT staging breve a una clave elegida por el servidor.
3. El PUT va directamente a MinIO, sin Bearer, cookies ni selector de tenant de
   la aplicación. Confirmación verifica objeto real, tamaño, SHA256 y formato
   y vuelve a comprobar membresía antes de crear el trabajo.
4. Los bytes verificados se fijan en una clave final inmutable. Confirmación
   repetida devuelve el mismo trabajo; dedup por tenant/hash evita trabajo
   duplicado sin depender del nombre. El retry deliberado existente no se
   convierte en reprocesado automático de cada envío.
5. Outbox durable y RabbitMQ transportan referencias, no el archivo completo.
   El worker reautoriza y verifica original/integridad. Reserva renovable y
   comprobación de propietario protegen la publicación del resultado.
6. Extracción local normaliza texto/bloques; el pipeline existente recibe el
   texto. El checkpoint se reutiliza sin reextraer y se consulta mediante
   `GET /jobs/documents/{job_id}` bajo el tenant autorizado.
7. Tras persistir checkpoint, vectores y completed se intenta retirar originales
   e intermedios; un fallo de limpieza se reintenta sin revocar completed.

Endpoints, estados y configuración completos permanecen en el
[runbook](../../../../docs/runbooks/document-ingestion.md). `queued` no significa
`completed`; `failed` con `retry_pending` conserva recuperación. El aviso de
sondeo desaparece al recuperarse la consulta y el smoke espera ese retry.

## Extracción y límites

MD/TXT usan UTF-8; DOCX conserva párrafos/tablas y propiedades disponibles; DOC
se convierte con LibreOffice local. PDF usa extracción nativa y OCR local
PDFium/Tesseract spa+eng en páginas escaneadas o híbridas elegibles. No se ejecuta
contenido activo ni se promete reconstrucción semántica perfecta del layout.

El máximo real es 20.000.000 bytes; la prevalidación UI no sustituye al servidor.
ZIP/XML rechazan corrupción, macros y expansión indebida; errores esperados de
descompresión producen 422. El subproceso no hereda secretos, deniega red y
acceso a archivos ajenos y limita tiempo/memoria/páginas/salida. El sandbox
requiere Linux/Landlock/libseccomp y falla cerrado si no está disponible.

## Persistencia y retirada

La migración aditiva 006 conserva tablas/datos anteriores. Normalizado v1 guarda
texto, bloques, posiciones disponibles, origen, metadatos, método y advertencias.
Documentos grandes usan partes SQL acotadas y manifiesto íntegro; jobs de archivo
no duplican todo el texto. Un checkpoint incompleto no sustituye al publicado.

Originales sobreviven a cola, ejecución y retries pendientes. Fallos terminales
usan la retención configurada; cancelación/expiración conservan su ciclo vigente.
El PUT podría recrear staging hasta vencer: el barrido continúa y `cleanup_done`
se fija tras vencimiento y borrado confirmado. Expiración S3 sólo afecta staging,
no originales confirmados activos. Normalizado y vectores permanecen tras limpiar.

## Operación y compatibilidad

MinIO/inicializador están en Compose general, con bucket privado, usuario de
servicio y CORS exacto; root no llega a las aplicaciones. CD completa sólo
secretos ausentes y asigna MinIO a base + 11 por ranura, con endpoint público y
orígenes coherentes. No cambia promoción ni comparte volúmenes entre releases.
`local:doctor` lee los requisitos de Compose; sus fixtures incluyen variables y
puerto documentales sin relajar el runtime. Véase la
[guía CD](../../../../docs/deployment/dockerserver-cd.md).

No cambian texto manual, chunker, modelo/dimensión de embedding, retrieval,
citas o aislamiento previos. Fase 2 podrá consumir el normalizado, pero sus
cambios no se incluyen ni se evalúan dentro de JUP-124.

## Evidencia y límites

La [matriz de diez criterios](../../../../docs/evidence/JUP-124-validation.md)
separa campañas históricas, correcciones y comprobaciones documentales actuales.
Almacenamiento/SQL/cola/OCR reales usaron inferencia mock: no prueban calidad LLM.
Coexistencia MinIO local no equivale a desplegar DockerServer. Los informes
locales no sustituyen pairing o reviews humanas JUP-124. Archivo/publicación
quedan fuera de este encargo.
