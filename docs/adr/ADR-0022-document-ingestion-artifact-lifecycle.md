# ADR-0022: Artefactos temporales y normalizado durable de documentos

- Status: Proposed
- Date: 2026-10-16
- Related JUP/OpenSpec: JUP-124, [jup-124-advanced-document-ingestion](../../openspec/changes/archive/2026-10-16-jup-124-advanced-document-ingestion/design.md)
- Trello: https://trello.com/c/SEkdYIYs
- Supersedes: none
- Superseded by: none

## Context

La ingesta admite archivos privados y formatos que requieren conversión/OCR.
Los binarios no deben viajar completos en RabbitMQ ni vivir indefinidamente
para que el RAG siga funcionando. La extracción debe poder recuperarse tras
reentregas y conservar límites y autorización por tenant.

Registro retrospectivo: implementación experimental autorizada del 15/10/2026
y correcciones del 16/10, recogidas en el commit local `688dd720`. El liderazgo
aceptó esa implementación y autorizó formalizar JUP-124; eso no equivale a
ratificación documental de este ADR. Su estado permanece Proposed.

## Decision

Separar tres responsabilidades existentes:

1. Originales privados y temporales en un bucket MinIO dedicado, dentro del
   Compose general. El backend emite staging PUT breve, verifica los bytes y
   fija el original confirmado en una clave inmutable. Sólo el servidor decide
   claves, tenant y autorización; la identidad de aplicación está separada de root.
2. Extracción local acotada en el processor, sin credenciales heredadas y bajo
   aislamiento Linux. LibreOffice/Tesseract y los parsers producen texto/bloques,
   posiciones disponibles y advertencias, no una interpretación LLM del archivo.
3. Normalizado durable en CockroachDB antes de continuar el pipeline existente.
   Para documentos grandes se usan partes acotadas y manifiesto íntegro, evitando
   un único valor SQL y la duplicación del texto completo en el resultado del job.

Las reservas de ejecución protegen la publicación; los reintentos reutilizan el
checkpoint. El original se conserva mientras pueda necesitarse para recuperación.
Tras éxito durable se retira mediante limpieza recuperable, sin borrar normalizado
o vectores ni convertir un fallo de borrado en fallo del trabajo ya completado.
La caducidad S3 sólo afecta staging; cancelados/expirados/terminales conservan su
política documentada. No se cambian la política del worker ni los modelos RAG.

## Consequences

- Recuperación y citas no dependen de conservar el binario original. El normalizado
  queda disponible para tareas posteriores sin volver a ejecutar los extractores.
- Se añaden operación MinIO, sus credenciales y CORS, bibliotecas de parsing y
  herramientas locales. La migración es aditiva y el backend mantiene la propiedad
  del esquema. CD debe configurar MinIO y su puerto por ranura, no sólo credenciales.
- OCR/conversión pueden fallar o advertir limitaciones de lectura. Sandbox no
  disponible falla cerrado; no se promete compatibilidad de ejecución nativa en
  cualquier host ni preparación productiva mediante este Compose local.
- MinIO/mc son AGPL-3.0; el [runbook](../runbooks/document-ingestion.md) conserva
  fuentes/releases verificadas, avisos, límites y responsabilidades de distribución.
- Se reutilizan ADR-0006/0008/0011/0015/0018/0019, sin sustituirlos ni cambiar sus
  estados: secretos, autorización, propiedad SQL, Compose, CD y reintentos.

## Alternatives Considered

- Binarios en la cola o en un único JSON SQL: acoplarían transporte/tamaño y
  recuperación; el ensayo de 20 MB acreditó la necesidad de partes y resultado
  compacto. No se amplía el tamaño global de mensajes SQL.
- Conservar archivos sólo en disco efímero del worker: no proporciona recuperación
  durable tras reinicio ni acceso seguro desde otros servicios.
- Almacenar originales permanentemente: no es necesario para el contrato actual y
  amplía retención de datos; el resultado normalizado durable es el recurso del RAG.
- OCR gestionado/remoto: no seleccionado; implica enviar documentos a otro
  proveedor, costes/accesos y una decisión fuera de esta implementación local.

Estas alternativas explican retrospectivamente la decisión implementada; no
representan nuevos benchmarks comparativos o una nueva aprobación de diseño.

## Evidence And Follow-up

[Matriz JUP-124](../evidence/JUP-124-validation.md),
[diseño](../../openspec/changes/archive/2026-10-16-jup-124-advanced-document-ingestion/design.md) y
[operación](../runbooks/document-ingestion.md) conservan trazabilidad y límites.
Hay SQL/S3/cola/OCR reales con inferencia mock, más correcciones evaluadas;
no DockerServer real ni campaña de calidad LLM.

Pendientes: ratificación explícita de este registro, pairing y reviews humanas
JUP-124, aprobación final/archivo/publicación según proceso. No se incorporan
chunking estructural, recuperación híbrida o hosting productivo por este ADR.
