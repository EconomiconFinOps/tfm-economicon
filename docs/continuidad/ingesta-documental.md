# Ingesta documental

Actualización técnica: 2026-10-16. Etapa experimental de la iniciativa RAG,
en `feat/rag-ingestion`, desde `53b43bb1e79b08967cc1b9efdf66669f11e8197c`.
El estado oficial, la formalización JUP y la integración se conservan en las
fuentes de proyecto; este resumen no acredita aceptación final ni merge.

La nueva entrada acepta un archivo MD/TXT UTF-8/PDF/DOCX/DOC por envío, máximo
20.000.000 bytes. El backend autentica usuario/tenant, reserva una transferencia
por usuario entre sesiones y confirma tamaño, SHA256 y formato reales. Usuarios
distintos del mismo tenant no se bloquean. MinIO privado forma parte del Compose
general; una URL staging breve nunca permite reescribir el objeto confirmado.

El processor reautoriza el trabajo, descarga/verifica el original y extrae texto
y bloques con herramientas locales y sandbox Linux. La representación versionada
persiste antes del pipeline actual y es recuperable mediante
`GET /jobs/documents/{job_id}` sin necesitar el original. Los checkpoints grandes
usan partes SQL acotadas y un manifiesto íntegro; el resultado del trabajo de
archivo no duplica el texto. Se preservan chunker, embeddings, recuperación/citas
y contrato de texto manual. La fragmentación estructural pertenece a la etapa
siguiente y no debe volver a ejecutar los extractores.

Tras completed persistido se retiran originales/intermedios; mantenimiento
reintenta fallos de borrado. Pendientes/reintentos conservan sus originales y
el checkpoint permite recuperar la ejecución. La expiración S3 sólo afecta
staging. El documento normalizado y pgvector permanecen disponibles para RAG.

El [runbook](../runbooks/document-ingestion.md) describe configuración, migración,
contratos de bloques y posiciones, límites de OCR/conversión, licencias y smoke
reproducible. Las pruebas nuevas están en `test_document_uploads.py`,
`test_document_extraction.py`, `test_document_checkpoint.py` y
`DocumentUploadPanel.test.tsx`; usan fixtures reales generadas localmente. La
prueba con modelos mock demuestra recorrido/persistencia/aislamiento, no calidad
semántica de recuperación. No se versionan corpus privados ni entornos generados.

## Correcciones de despliegue y admisión

El agente CD genera credenciales documentales ausentes tanto en raíces nuevas
como anteriores, sin rotar valores existentes. Cada ranura usa su puerto MinIO
(base + 11), endpoint público y orígenes exactos del frontend. El
[procedimiento CD](../deployment/dockerserver-cd.md) incluye actualización del
agente y túnel S3; las releases ya preparadas permanecen inmutables.

La admisión DOCX convierte errores de descompresión DEFLATE/BZip2/LZMA en rechazo
de formato 422, sin publicar un trabajo ni cambiar las reservas o sus plazos.
Las dos copias del contrato de formatos permanecen idénticas. Las regresiones
están en `tools/cd/test_deploy.py` y `test_document_uploads.py`: preparación real
con Compose de ambas ranuras y raíz anterior, preservación de secretos y
documentos comprimidos corruptos. La preparación renderizada no equivale a un
despliegue real; no se ha actuado sobre DockerServer.

Las fixtures de `tools/local-doctor.test.mjs` incluyen las cinco variables
documentales obligatorias y el puerto MinIO del Compose vigente. El ejemplo
puede contener orígenes CORS válidos aunque sus secretos sigan vacíos: la prueba
distingue ambos casos. Se conservan los escenarios anteriores y se comprueban
ausencias, valores vacíos y precedencia de entorno para cada variable documental,
puertos MinIO inválidos/duplicados/ocupados y ausencia de secretos en el diagnóstico.
No se ha relajado ni modificado `tools/local-doctor.mjs`. Las 12 pruebas que
fallaban por preparación desactualizada quedan cubiertas por la suite corregida,
sin omitir casos ni repetir la extracción o la batería general de aplicaciones.
