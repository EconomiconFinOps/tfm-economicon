# Ingesta documental

Actualización documental: 2026-10-16. La etapa experimental se formaliza como
[JUP-124](https://trello.com/c/SEkdYIYs), rama
`feat/JUP-124-advanced-document-ingestion`, con código de referencia
`688dd7202bc9536f5bd6d4febafa3ee392764df5` y base develop `53b43bb1` ya incluida.
El [change archivado](../../openspec/changes/archive/2026-10-16-jup-124-advanced-document-ingestion/proposal.md)
registra retrospectivamente implementación del 15/10 y correcciones del 16/10;
no inventa un diseño previo ni altera producto. La [matriz de diez criterios](../evidence/JUP-124-validation.md)
y [ADR-0022 Proposed](../adr/ADR-0022-document-ingestion-artifact-lifecycle.md)
separan evidencia histórica, ratificación y reviews humanas pendientes.
Paris aprobó el archivo el 16/10/2026: requisitos promovidos y change archivado en la misma rama. La PR tendrá destino develop; publicación, CI y reviews humanas se registran por separado, sin atribuir merge.

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

## Compatibilidad del sandbox con CI

La CI del 16/10/2026 sobre `51010c4` registró diez fallos en extracción. Se
reprodujeron con Python 3.12.15 bajo `/opt`: Landlock denegaba las importaciones
tardías de sus bibliotecas fuera de `/usr`, y el subproceso de la prueba de
aislamiento perdía la ruta de `app` al cambiar al temporal de pytest. Se habilitan
únicamente las cuatro rutas de bibliotecas declaradas por `sysconfig` en sólo
lectura y la fixture fija su propia ruta de importación. No se cambia el entorno
del extractor: se descartó que quitar `LD_LIBRARY_PATH` impidiera arrancar el
binario oficial de CI. Se conservan los fallos originales y los límites de
recursos, red, escritura y archivos ajenos; no se admiten `/opt` ni el prefijo
completo. Las 18 pruebas de extracción y las siete de checkpoint pasan en un
contenedor aislado sin red con el runtime oficial de CI y usuario no privilegiado.
Este resultado local no sustituye la CI remota ni acredita un despliegue.
