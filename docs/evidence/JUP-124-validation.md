# JUP-124 — Evidencia de ingesta documental avanzada

JUP: JUP-124 · [Trello](https://trello.com/c/SEkdYIYs) · Registro: 16/10/2026.
Formalización **retrospectiva**, no una campaña de producto ejecutada hoy.
Implementación de referencia: commit local
`688dd7202bc9536f5bd6d4febafa3ee392764df5`, sobre `53b43bb1` de develop.
[OpenSpec](../../openspec/changes/archive/2026-10-16-jup-124-advanced-document-ingestion/proposal.md)
y [ADR-0022 Proposed](../adr/ADR-0022-document-ingestion-artifact-lifecycle.md).

## Matriz de los diez criterios

Los resultados siguientes se reutilizan de las campañas del 15–16/10 sobre los
bytes verificados de la entrega y sus correcciones. No se repiten producto,
OCR, proveedor o suites generales durante la formalización documental.

| Criterio oficial | Evidencia histórica y alcance | Referencia reproducible del repositorio |
| --- | --- | --- |
| 1. MD/TXT/DOCX/DOC y PDF digital/escaneado/mixto | Extracción local real, PDF/OCR, DOC convertido y DOCX estructurado. 25 casos iniciales; límites/sandbox negativos y documento digital, escaneado e híbrido. No promete reconstrucción perfecta de layout. | [test_document_extraction.py](../../apps/processor/tests/test_document_extraction.py), [límites y motores](../runbooks/document-ingestion.md#extracción-y-límites-reales). |
| 2. Un archivo, 20.000.000 bytes y reserva por usuario | Integración real: límite exacto y exceso, exclusión entre sesiones/tenants del usuario y concurrencia de usuarios del mismo tenant. UI final rechaza selección múltiple. | [test_document_uploads.py](../../apps/backend/tests/test_document_uploads.py), [panel](../../apps/frontend/src/components/DocumentUploadPanel.test.tsx). |
| 3. Autorización, tenant y contenido reales | Rechazos sin job por objeto ausente, tamaño/hash/formato reales y membresía; worker reautoriza. Corrección posterior: DOCX DEFLATE corrupto original ahora 422/cero jobs, control inválido 422 y admisible 202 idempotente. | [admisión](../../apps/backend/tests/test_document_uploads.py), [checkpoint/worker](../../apps/processor/tests/test_document_checkpoint.py). |
| 4. MinIO separado en Compose, privado y con CORS | MinIO/bucket/init reales, PUT firmado sin credenciales de aplicación, persistencia. Validación adicional de dos MinIO: ambos HTTP200 simultáneos, origen propio permitido y ajeno sin Allow-Origin. No demuestra despliegue remoto. | [Compose](../../docker-compose.yml), [topología](../../tools/docker-topology.test.mjs), [configuración](../runbooks/document-ingestion.md#arranque-y-configuración). |
| 5. Asíncrono, estados, identidad y recuperación | Integración real: confirmación repetida, dedup por tenant/hash, original confirmado inmutable, publicación incierta y reentrega. Checkpoint reutilizado sin extracción, reserva vigente al publicar. Aviso UI y smoke corregidos para retry_pending. | [servicio](../../apps/backend/tests/test_document_uploads.py), [reservas](../../apps/processor/tests/test_document_checkpoint.py), [smoke](../../scripts/smoke_file_upload.py). |
| 6. Limpieza tras éxito durable | Fallo de borrado recuperado; originales conservados en cola/retry. Reinicio y extracción normalizada disponible después de limpiar. Caso 20 MB persistido en 626 partes acotadas, sin duplicar texto en jobs.result. | [ciclo durable](../../apps/backend/tests/test_document_uploads.py), [retirada](../runbooks/document-ingestion.md#retirada-de-originales). |
| 7. Texto manual y RAG existente | Smoke manual original, dos tenants, persistencia SQL/vectorial, recuperación/citas tras retirar original y reiniciar. Inferencia/embeddings mock acreditan recorrido/aislamiento, no relevancia semántica. | [smoke manual](../../scripts/smoke_document_ingestion.py), [contrato anterior](../../openspec/specs/document-ingestion-handoff/spec.md). |
| 8. Estilo, temas y responsive sin forzar reprocesado | Capturas finales light/dark/mobile y recorrido de archivo completado en navegador, selección única aprobada; pruebas de panel/transporte. El retry deliberado tras fallo terminal no es una casilla de reprocesado automático. | [panel](../../apps/frontend/src/components/DocumentUploadPanel.test.tsx), [transporte](../../apps/frontend/src/services/document-api.test.ts). |
| 9. Migración/config/docs y CD | Migración 006 aditiva. Raíces CD nueva/anterior renderizadas en ambas ranuras, secretos/HMAC preservados y puertos sin solapamiento; coexistencia y persistencia MinIO real. No smoke DockerServer. | [test_deploy.py](../../tools/cd/test_deploy.py), [operación CD](../deployment/dockerserver-cd.md). |
| 10. local:doctor y fixtures coherentes | RED 45 PASS/12 FAIL de 57 por fixtures antiguas; corrección conserva 57 escenarios y añade dos. 59 doctor y 117 afectados PASS; diagnóstico productivo intacto. Validador: 116 PASS iniciales y un EPERM de entorno, sólo ese caso reejecutado PASS; cero skips. | [doctor](../../tools/local-doctor.test.mjs), [smoke](../../tools/local-smoke.test.mjs), [topología](../../tools/docker-topology.test.mjs). |

## Identificación de campañas y límites

- Entrega inicial 15/10: `integration-full.json`, 50 comprobaciones/11 documentos,
  SHA256 `0e78f9fd8f03cfe29b164acf362e88897ea067cf41cce727f8c20d251c5cfdf3`.
  SQL/S3/RabbitMQ/processor/pgvector reales, inferencia mock. Recuperación,
  reinicio y limpieza conservan recibos separados; no se suman como nuevas
  operaciones al mismo denominador. Validador inicial: 14/14 criterios internos,
  distintos del agrupamiento oficial actual en diez criterios.
- Ajustes de UI/smoke del 15/10: adenda funcional original con matriz de vigencia,
  SHA256 `a0310a83020f75f6d36efcffac5df8f610a952d6dbff4ed3063a5af9affdf970`.
  11 pruebas UI/transporte y dos casos CLI propios. Capturas anteriores
  reutilizadas por identidad de estilos; no se presenta otra captura.
- Correcciones F1/F2/F3, 16/10: revisión y validación locales independientes
  favorables. Recibo HTTP del DOCX corrupto y controles, SHA256
  `b3f6e2b6e1bb410d78ca1669f5e195a6ce4eae3565ca5ebab8fa0d78f1dc816b`.
  Validador contrasta ambos contratos y reutiliza explícitamente ese HTTP;
  sus servicios MinIO A/B prueban coexistencia, CORS y persistencia propios.
- Corrección doctor, 16/10: `affected-green.log`, 117 PASS, SHA256
  `1efb227387fc3ecdea041b4428ba6997b184de92121e5d6718c560bd3e47e377`.
  Revisión 97 casos propios y validación 117 casos distintos; sus adendas
  cubren consumidores directos. No se suman resultados solapados como casos únicos.

Los originales se conservan bajo custodia del liderazgo fuera de Git; aquí se
versiona el resumen trazable y sus huellas, no datos privados, secretos o rutas
de otra máquina. Las instrucciones siguientes permiten repetir alcances desde
el repositorio, no prometen reproducir toda la campaña histórica con un comando.

## Reproducción disponible

Usar un entorno propio desechable siguiendo el [runbook](../runbooks/document-ingestion.md),
sus dependencias declaradas, tokenizer preparado y configuración sintética.

```text
cd apps/backend
python -m pytest tests/test_document_uploads.py -q
cd ../processor
python -m pytest tests/test_document_extraction.py tests/test_document_checkpoint.py -q
```

Desde raíz, `corepack pnpm local:test` y `corepack pnpm docker:validate`
ejecutan herramientas/fixtures, no un stack real. Para renderizado CD con Docker:
`CD_COMPOSE_INTEGRATION=true python -m unittest discover -s tools/cd -p test_deploy.py -v`
(PowerShell: fijar `$env:CD_COMPOSE_INTEGRATION='true'` antes del comando Python).
El [smoke de archivo](../../scripts/smoke_file_upload.py) usa `--tenant`, `--file`
y `--base-url`; credenciales sólo por variables documentadas. El smoke manual
original sigue disponible. Ninguna receta autoriza gasto o recursos compartidos.

## Formalización y participación

Este encargo sólo añade OpenSpec/ADR/evidencia y actualiza continuidad. Sus
controles documentales del 16/10 son: change estricto válido, 74/74 validaciones
OpenSpec globales, trazabilidad de JUP-124 y todos los changes activos, higiene de
1620 archivos, 48 enlaces locales verificados y 733 archivos fuera de docs/OpenSpec
sin cambios de bytes. Diff-check de archivos versionados correcto. El verificador
de enlaces es una comprobación de rutas/anchors locales, no de sitios remotos.
Se informan por separado de las campañas reutilizadas; no son nuevas pruebas
funcionales ni una CI de la PR todavía inexistente.

Roles comunicados el 16/10/2026: liderazgo Paris Arcos; pairing Lucía Mateo;
revisión Víctor Méndez; validación/pruebas/documentación Alejandro Aguado.
Asignación no equivale a aportaciones acreditadas ni a reviews realizadas.
Las evaluaciones independientes locales anteriores no son `Revision JUP-124`
o `Validacion JUP-124` humanas. Ratificación ADR, aprobación final, archivo,
CI publicada, pairing y revisiones humanas siguen pendientes. Sin DockerServer,
producción, campaña LLM real ni fases 2/3 en esta evidencia.

## Archivo autorizado — 16/10/2026

Paris aprobó el cierre documental y autorizó archivar OpenSpec y publicar hacia develop. El CLI OpenSpec 1.8.0 promovió los diez requisitos a advanced-document-ingestion y archivó el change como 2026-10-16-jup-124-advanced-document-ingestion, sin omitir actualización de specs ni validación. Se ajustan las referencias relativas y el propósito de la capacidad promovida; producto y pruebas permanecen intactos. El ADR continúa Proposed: esta autorización no se presenta como ratificación colectiva ni como pairing o reviews realizados. La publicación y CI se verifican en GitHub por separado.

## Correcciones del pairing de PR #133

Incremento local del 16/10/2026 sobre `eb4453f96b7bab819bf4ba692e6bdcf7e521f2ef`,
base develop `53b43bb1`. Responde al feedback de Lucía, no sustituye su pairing
ni las reviews humanas. Los resultados siguientes son de esta corrección;
revisión y validación independientes del candidato final están pendientes.

- DOCX: lectura efectiva acotada, métodos OPC antes de descomprimir y rechazo
  DTD independiente de codificación. Las dos copias de admisión son idénticas.
  Un contenedor BZip2 falseado de 440 bytes y 32 MiB expandibles devuelve 422
  por HTTP/S3 reales, sin job y con cancelación de su reserva. En procesos Linux
  nuevos, ambos validadores lo rechazan con incremento de pico RSS de 0 KiB;
  la prueba exige menos de 16 MiB. Esta medida no promete memoria constante
  para cualquier documento válido ni reproduce el archivo privado de 300 MB.
- Ciclo de vida: revocar membresía antes del consumo termina failed/terminal,
  sin checkpoint, sin ejecutar el pipeline y sin claims residuales. Otro usuario
  del mismo tenant sube los mismos bytes y completa un trabajo nuevo. El barrido
  retira los originales fallidos tras su retención sin borrar el checkpoint sano.
  El ensayo adelanta sólo las fechas de esa fixture, no el reloj ni los plazos.
- Propietario: running/failed y descarte terminal comprueban reserva vigente;
  una ejecución antigua no pisa a la nueva. Un mensaje alterado no autoriza
  cambios de estado. Dedup también recupera referencias terminales heredadas.
- Interfaz: los 422 de formato muestran un motivo cerrado y requieren otro
  archivo; los fallos transitorios mantienen el reintento existente.

Pruebas: 41 casos de backend/admisión, 10 de checkpoint/propietario, 12 de panel
y transporte. Las regresiones de extracción/worker suman 183 casos únicos
favorables en ejecuciones separadas: 171 iniciales, seis SQLite y seis Cockroach
repetidas tras preparar correctamente su entorno. Las 18 extracciones incluyen
DOC antiguo, PDF mixto, OCR y sandbox real. No se suman reejecuciones al total.
Los fallos originales de preparación se conservan: PyJWT ausente en la imagen
de desarrollo, topología/marca de Cockroach exigidas por la fixture, y correo
sintético inválido en el primer recorrido. No se alteraron pruebas ni aserciones
para resolverlos. La primera tanda incompleta no se presenta como favorable.

Controles favorables: trazabilidad, política de PR/CI, gobierno, OpenSpec global,
higiene, typecheck/lint/build del frontend y diff-check. No se repitieron suites
generales ajenas ni la batería LLM. Backend y processor construidos con los
locks existentes; modelos y embeddings mock, gasto cero. MinIO conserva fuentes
y versiones fijadas; su build reutilizó caché en 2,25 s sin cambiar la política
de imagen. Los recibos, hashes de imágenes y originales quedan bajo custodia
del liderazgo, fuera de Git y sin secretos en esta evidencia.

Observaciones conservadas: conocimiento/dedup compartidos dentro del tenant,
coste potencial de 44.445 fragmentos de un TXT de 20 MB (sin nuevo límite aquí),
y texto/URI del formulario manual fuera del arreglo. No se acreditan calidad
RAG con proveedores reales, DockerServer, ni las fases posteriores. La
[reproducción](../runbooks/document-ingestion.md#reproducción) incluye las suites
de admisión nuevas y los smokes existentes. Commit, CI remota, publicación y
reviews humanas se gestionan por separado.

## Reconciliación local con develop — 17/10/2026

Candidato sin commit nuevo: rama `feat/JUP-124-advanced-document-ingestion`,
HEAD de partida `fd732f76de9a507935559d847d50b9467d19084b` y MERGE_HEAD
`ffdd8ee9895d95e085ef31f18064fd55d56fe4e5`. Preparación autorizada con
`merge --no-commit --no-ff`; staging final y commit corresponden al liderazgo.
No se atribuyen estos bytes al HEAD inicial ni se declara CI remota nueva.

Se conservan las filas de ambos índices y ambas entradas ADR-0022 por su ruta
completa; la numeración original no se modifica. Doctor conserva sus controles
de documentos/MinIO y añade la contraseña Grafana de develop. Compose, `.env`
y CI combinan ambos padres, incluidos MinIO general y los motores de extracción
en CI. Backend de documentos, processor y frontend mantienen identidad con
fd732f76, incluidos los arreglos de pairing y el límite de 20.000.000 bytes.

| Comprobación propia de la reconciliación | Resultado y límites |
| --- | --- |
| Doctor, smoke, topología y workflow, Node 24.22.0/yaml 2.9.0, candidato RO | Primera ejecución: 127/128 correctos; una expectativa resuelta omitía las dos claves S3. Corregida la unión, el único caso afectado pasa en ejecución focal. No se presenta como un nuevo 128/128 de una sola ejecución. |
| Preparación CD real, raíz nueva y heredada | Fallo original en ambas por ausencia de GRAFANA_EVALUATION_DB_PASSWORD; diagnóstico saneado y recibos conservados. |
| Compatibilidad CD corregida | Dos tests focales correctos: ambas raíces y dos ranuras, preservación del valor configurado y repetición idempotente. Usa el generador existente, añade sólo valores ausentes y no rota secretos. No se crean usuarios/grants ni se despliega. |
| Consumidor backend del cambio de series de fallos de assistant | 29/29 correctos en entorno Python 3.10.11 propio con dependencias declaradas. Sin red de proveedores ni servicios compartidos. |
| OpenSpec estricto global | 76/76 correctos; incluye la spec de fase 1 sin modificar sus requisitos. |
| Trazabilidad e higiene | Ocho changes activos trazables y 1.746 archivos correctos. |

El ajuste del generador CD es compatibilidad necesaria con la configuración
entrante de JUP-121, delimitada expresamente por el liderazgo. La variable se
genera únicamente si falta; las raíces existentes conservan sus valores y las
releases ya preparadas siguen inmutables. No equivale a actualización del agente
operativo ni a ejecución sobre DockerServer.

Se reutilizan por identidad las evidencias históricas de ingesta/formatos/OCR,
20 MB, aislamiento, multiusuario, limpieza y UI; no se reportan como ensayos
nuevos. No se ejecutan campañas LLM, llamadas pagadas o fases posteriores.
Autorrevisión y pruebas propias no sustituyen los nuevos dictámenes independientes
ni las reviews humanas. Fuentes, recibos originales, manifiesto de bytes y
recursos temporales quedan identificados fuera del producto bajo custodia del
liderazgo. Commit, evaluación independiente, CI remota y publicación pendientes.
