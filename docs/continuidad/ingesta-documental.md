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

La admisión DOCX conserva el rechazo 422 sin publicar un trabajo: ahora sólo
acepta ZIP sin compresión/DEFLATE, verifica los bytes efectivos por bloques y
rechaza BZip2/LZMA antes de descomprimir, además de DTD también en UTF-16.
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

## Corrección del feedback de pairing de PR #133

Sobre `eb4453f9`, se corrigen el pico de memoria del contenedor DOCX falseado y
el trabajo huérfano tras revocar membresía. Las transiciones running/failed y
terminal requieren propietario vigente; una entrega manipulada no muta estado.
El fallo terminal libera dedup y recupera la limpieza con la retención existente.
El panel distingue un formato inválido de un fallo transitorio y no lo reintenta.
El ensayo propio con CockroachDB, RabbitMQ y MinIO reales confirma DOCX válido,
revocación, nueva subida por otro usuario y limpieza sin borrar su checkpoint;
los proveedores son mock y no hay gasto. Se conservan los fallos de preparación.
La [evidencia incremental](../evidence/JUP-124-validation.md#correcciones-del-pairing-de-pr-133)
separa pruebas, límites y evaluaciones independientes todavía pendientes.

## Reconciliación local con develop — 17/10/2026

Se prepara la combinación de `fd732f76de9a507935559d847d50b9467d19084b` con
`ffdd8ee9895d95e085ef31f18064fd55d56fe4e5`, comprobado por el liderazgo.
La rama conserva ingesta, formatos/OCR, texto manual, límites y concurrencia,
limpieza durable y los arreglos del pairing. No incorpora las fases 2/3.
Los conflictos de los índices ADR/continuidad conservan ambas aportaciones,
incluidas las dos rutas ADR-0022 ya identificadas en los padres; no se renumeran
ni se ratifican. La fixture de doctor conserva variables documentales y suma
la contraseña de evaluación requerida por Compose.

La nueva obligación `GRAFANA_EVALUATION_DB_PASSWORD` exponía una incompatibilidad
del generador CD: la preparación real fallaba tanto en raíz nueva como heredada.
Por delimitación del liderazgo se añade sólo la clave ausente mediante el
generador seguro existente. No se cambian valores configurados, permisos,
roles de base de datos ni accesos operativos. Las pruebas generan exclusivamente
secretos sintéticos temporales. Preparación de ambas raíces/ranuras y repetición
idempotente correctas; se comprueba también la conservación de un valor existente.

[Evidencia incremental](../evidence/JUP-124-validation.md#reconciliación-local-con-develop--17102026):
127 casos de herramientas correctos y un fallo inicial propio de resolución de
la expectativa S3, corregido y repetido focalmente; 29 casos del consumidor
assistant y 76 OpenSpec correctos. Los errores CD originales se conservan,
separados del resultado corregido. No se repiten OCR, multiusuario o campañas
RAG cuyos archivos mantienen identidad, ni se usan proveedores reales.

Se entrega el árbol de trabajo para staging/commit del liderazgo, sin commit
ni push propios. Evaluaciones independientes y CI del futuro commit pendientes;
no se presenta la CI histórica de fd732f76 como comprobación de esta combinación.


## Contrato de Grafana en CI sin recuento global — 17/10/2026

La CI sobre la base reconciliada detectó un test desactualizado de
`test_evaluation_grafana_datasource.py`: exigía 103 líneas ajenas a la variable
de evaluación, frente a las 127 legítimas de esta rama (129 en fase2).
La corrección elimina ese tamaño global fijo y conserva las cinco declaraciones
previas relevantes, además de los casos existentes de declaración exacta/vacía,
unicidad y posición tras `GRAFANA_ADMIN_PASSWORD`. Nombre y comentarios del test
reflejan ese contrato, que admite ampliaciones independientes.

El archivo completo pasa sus 30 casos en Python3.10/Windows y Python3.12/Linux.
Controles mediante el override existente de configuración: tres entradas válidas
(base actual, ampliación independiente y configuración de fase2 como dato) aceptadas;
catorce incumplimientos de declaración/posición o ausencia/duplicación de las cinco
variables previas rechazados por aserciones. El fallo original se conserva.
No cambia configuración de runtime; el paquete/CI descubre el mismo archivo.
[Evidencia de esta corrección](../evidence/JUP-124-validation.md#corrección-del-test-del-contrato-de-grafana--17102026).
Evaluación independiente del candidato, aceptación y posterior incorporación por
el liderazgo a fase2 siguen pendientes; fase2 no se edita anticipadamente.
