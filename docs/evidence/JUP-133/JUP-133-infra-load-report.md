# JUP-133 — Informe de carga y dashboard

**Carga verificada por contenido exacto y consultas de Grafana.**

Destino: DockerDevelop, `embeddings.evaluation`. Reemplazo completo preparado: 17 ejecuciones / 765 resultados → 23 ejecuciones / 1284 resultados.

Se conservan exactamente los valores y metadatos de las 17 ejecuciones anteriores, incluidas cinco incorporaciones locales que no estaban en el manifiesto de Git. La transacción bloquea las tablas y aborta si cambió la instantánea previa. No se modifica DockerServer, el acceso, las credenciales ni las cuotas.

Las seis ejecuciones nuevas son provisionales. El modelo aparece como declarado y no verificado; no hay juicios humanos, aceptación ni métricas humanas medidas. La tabla comparativa muestra fecha, campaña, repetición, operaciones completadas, intentos, coste, mediana y p95.

Antes de la carga: 25 consultas del dashboard y la nueva consulta de comparación comprobadas por API; éxito: True.

Después: contenido normalizado exacto, 23 ejecuciones / 1284 resultados; histórico anterior preservado: 17 / 765. Cero filas de juicio humano medidas en las campañas nuevas.

Grafana después de cargar: 26 consultas del dashboard, éxito True; comparación con 6 filas, HTTP 200.

Revisión visual: documentada en el JSON adjunto.

SQL, instantáneas, autorización de carga y captura visual permanecen fuera de Git en el directorio privado del workspace. El manifiesto versionado contiene 18 ejecuciones (12 anteriores + 6 nuevas); la base preserva además las cinco ejecuciones locales.

[Detalle y huellas](JUP-133-infra-load-report.json) · [Comparación de las seis repeticiones](JUP-133-infra-comparison-report.md).

Pruebas offline del registro: 12 pruebas offline: 9 pasan y 3 fallan por expectativas fijas del manifiesto anterior (12 ejecuciones frente a las 18 actuales). El contrato rows-v1 y la conciliación independiente pasan; no se declara la integración en verde.
