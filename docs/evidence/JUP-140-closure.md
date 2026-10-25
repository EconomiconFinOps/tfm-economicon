# JUP-140 — cierre autorizado de OpenSpec

24/10/2026 · [Tarjeta](https://trello.com/c/rXLyK4g4) · [R4 aprobado y límites](JUP-140-R4.md) · [Operación](../landing-runtime.md) · [Change](../../openspec/changes/archive/2026-10-24-jup-140-landing-video-app-runtime/)

Paris aprobó R4 y autorizó archivo/reconciliación/evaluación independiente afectada, con cierre antes de publicar. La base actual es develop 93624f77b2481d64ba40e95f211a9e53451f9e0e, rama feat/JUP-140-landing-runtime-links más cambios sin commit. No hay commit/push, PR, merge o despliegue autorizados por este hito.

## DoD activo y transición

Se conserva fuera del producto el DoD antes de mover el change, con tareas 8.6/8.7 completadas por los resultados R4 y aprobación humana reales. El archivo usa la fecha local 24/10/2026, sin omitir promoción o validación. Las comprobaciones posteriores se refieren al estado archivado; no se declara DoD activo nuevo sobre un directorio retirado.

## Delta y evidencia reutilizada

Develop incorpora métricas/datos/documentación y sus pruebas, sin cambiar el código de landing, Compose, CD, dependencias o gobernanza. La única intersección local fue el índice de continuidad: conserva la fila landing y las dos filas entrantes. Quince archivos locales cambiaron sólo CRLF→LF, contrastados contra los bytes originales preservados antes de la reconciliación; no se presentan hashes RAW como idénticos. El mapa externo enumera rutas, hashes y prueba exacta de normalización.

La imagen R4 a0f78529 y su manifiesto de build d9892d9f, scripts, configuración y medio aprobado conservan identidad. La normalización de algunas fuentes no reconstruye esa imagen ni convierte un hash RAW nuevo en el de la imagen. Las evaluaciones afectadas ratificarán expresamente qué evidencia R4 sigue aplicable. Globales R2 sólo para no afectados, con fecha/519 SKIP/fallos; reduce interactivo NOT_TESTED y limitaciones visuales/externas conservados. No nueva campaña, modelos, gasto o batería general.

## Estado de comprobación

Archivo nativo ejecutado con éxito como 2026-10-24-jup-140-landing-video-app-runtime, con validación habilitada y sin skip-specs. El directorio activo está ausente y los siete archivos movidos coincidieron exactamente antes de reparar enlaces. Las dos specs canónicas coinciden con sus promociones nativas preparadas: containerized-runtime +1; public-landing +5 y 2 modificaciones; ninguna retirada o renombrada. Se aplicaron sólo las seis reparaciones documentales preparadas y comprobadas por hash. Las comprobaciones estrictas posteriores se registran separadamente del DoD activo preservado. Evaluaciones independientes del estado fijo reconciliado/archivado pendientes en este corte. Se preservan los originales y controles de R4, sin sustituirlos por los nuevos.

## Etapas pendientes

Cierre técnico independiente afectado y presentación a Paris antes de publicar. Pairing humano de Alejandro aún no acreditado; Lucía revisión y Víctor validación mantienen sus roles, Paris lidera. Commit/push, CI del SHA definitivo y publicación requieren sus permisos. Reviews humanas separadas y merge siguen el proceso 18/10; excepción PR135 no aplicable. No se declara la JUP integrada ni desplegada.


## Comprobaciones observadas del cierre

Antes del movimiento: OpenSpec estricto 93 PASS, trazabilidad de 13 changes activos e higiene de 2568 fuentes. Se preservaron el DoD activo, su manifiesto de entradas y los siete archivos. Después: OpenSpec estricto 92 PASS, trazabilidad de los 12 changes que permanecen activos e higiene de 2568 fuentes; el total baja por el cambio archivado, no por una prueba omitida. El CLI general no recorre archives: el Validator nativo estricto validó además proposal y deltas en la ruta archivada real, sin recrear un change activo. Promociones canónicas idénticas a la preparación nativa y ninguna retirada.

La trazabilidad específica del archivo se conserva mediante sus metadatos JUP-140, URL directa de tarjeta, proposal/design/tasks, dos deltas y mapa exacto de siete movimientos. Los enlaces locales afectados y las dos filas ajenas del índice se contrastan al congelar el candidato. Esta actualización sólo consigna resultados ya observados; las evaluaciones independientes del cierre permanecen pendientes al congelar. No se anuncia un test/build global nuevo ni una imagen reconstruida a partir de los bytes normalizados.
