# Dashboard de resultados de evaluación del asistente — JUP-121

Última actualización documental: 2026-10-16. Esta nota no repite el alcance de la tarjeta, que vive en [Trello](https://trello.com/c/aIdxwsXR).

## Estado

- Rama `feat/JUP-121-assistant-evaluation-dashboard`, creada desde `develop`; `origin/develop` integrado dos veces (JUP-120 y JUP-122). PR [#132](https://github.com/EconomiconFinOps/tfm-economicon/pull/132) abierta. Paris pidió cambios (`local:doctor` con la variable nueva) y Lucia dejó un comentario de pairing con mejoras de lectura; ambos se atienden en el change `jup-121-lectura-dashboard` ([archivado](../../openspec/changes/archive/2026-10-16-jup-121-lectura-dashboard/)), pendiente de revalidación. Las segundas revisiones (anotaciones de la latencia, estado de casos solo de JUP-070, contrato de clasificación para JUP-071, orden de la sección A, títulos de C y fecha de la matriz) se resuelven en el change `jup-121-anotaciones-y-fuente`.
- OpenSpec: `openspec/changes/archive/2026-10-15-jup-121-assistant-evaluation-dashboard/` (propuesta, diseño, spec, tareas y `review.md` con la evidencia por tarea). ADR: [ADR-0022](../adr/ADR-0022-assistant-evaluation-results-in-grafana.md), en estado Proposed.
- Guía y contrato de datos: [evaluation-dashboard.md](../validation/evaluation-dashboard.md). Manifiesto versionado: [evaluation-runs.json](../validation/evaluation-runs.json). Evidencia: [JUP-121-validation.md](../evidence/JUP-121-validation.md) y capturas en `docs/evidence/JUP-121/`.
- Producto: `tools/evaluation-dashboard.py` (adaptadores, SQL, carga, rol), `apps/monitoring/grafana/dashboards/assistant-evaluation.json` (24 paneles, secciones A, B y C, con resumen de la última campaña, matriz por métrica y ejecución y evolución de la latencia), datasource `evaluation-postgres.yml`, variable `GRAFANA_EVALUATION_DB_PASSWORD` en `docker-compose.yml` y `.env.example`, scripts `evaluation-dashboard:*` y un paso de CI. Cambio mínimo en el backend: `assistant.py` crea a 0 las series de `backend_retrieval_failures_total`.

## Decisiones que no se deducen del código

- **PostgreSQL nativo como fuente** (esquema `evaluation` en el `postgres-pgvector` existente, rol `grafana_evaluation_reader` de solo lectura) y no Pushgateway, JSON directo ni un endpoint propio: Prometheus fecha lo que ingiere con la hora de ingesta, no la de la ejecución, y el datasource JSON necesita un plugin que no está instalado. Los informes siguen siendo la fuente de verdad; la base es una proyección que se tira y se recarga.
- **Contrato `rows-v1`:** JUP-071 (robustez) no existe aún; entra emitiendo ese formato o con su propio adaptador. Mientras tanto la sección de robustez muestra «Sin datos».
- **Lo no medido nunca es 0 %.** Las ejecuciones de plantilla, dobles o sintéticas se rotulan «no real» y sus series van discontinuas. Una serie con menos de dos puntos medidos no se dibuja.
- **Latencia y disponibilidad de campaña (tipo A) y de tráfico real (tipo C) no se mezclan** en un panel.
- **El `load` necesita la pila de Compose levantada y el `.env` completo**; la contraseña de Grafana y la de `load` son la misma variable.

- **La matriz «Resultados por métrica y ejecución» pivota con `groupingToMatrix`** (una columna por ejecución, funciona con texto en Grafana 11.3.0), pero la transformación no ordena las filas: la consulta cruza las ejecuciones con el catálogo de métricas y ordena en SQL. Los nombres legibles salen de un `CASE` con las 17 métricas de JUP-067 (una prueba exige que cubra el catálogo entero). Las tablas por fila se conservan como «detalle» porque la conciliación con los informes originales las usa. Todo el dashboard va en UTC.

## Qué tocar si cambia algo

- Un informe nuevo: añadir su adaptador a `tools/evaluation-dashboard.py` o emitir `rows-v1`, y una entrada en el manifiesto; el dashboard no cambia. Comprobar con `corepack pnpm evaluation-dashboard:rows`.
- Un panel: editar `assistant-evaluation.json` (las pruebas estructurales exigen tipo A/B/C, «Mide:» y «No demuestra:», un solo datasource por panel y los textos de «Sin datos»).
- Una categoría nueva de fallo de recuperación: se añade a `FAILURE_CATEGORIES` y la serie a 0 sale sola.
- Regenerar los datos: `corepack pnpm evaluation-dashboard:load`; pruebas: `corepack pnpm evaluation-dashboard:test` (las que usan PostgreSQL real necesitan Docker).

## Pendiente

- Revalidación de Paris y revisión técnica de Alejandro sobre el candidato corregido; respuesta a los comentarios de la PR #132.
- Añadir `GRAFANA_EVALUATION_DB_PASSWORD` al `.env` local y al de DockerServer antes de levantar la pila: `docker compose` se niega a arrancar sin ella.
- Tarjeta de pulido del dashboard (por crear en Trello, la crea el líder): columnas repetidas, referencias JUP en el texto visible, descripciones de los ⓘ, calibración y benchmark en español, sección C sin duplicar el dashboard técnico y gráficas para la sección B y la calibración (propuestas de Lucia). Las tablas «(detalle)» se movieron al final de la sección A pero no se pliegan, porque una fila plegada anida sus paneles y la conciliación recorre los de primer nivel.
- Hallazgos diferidos con su detalle en `openspec/findings/backlog.md` (cargas simultáneas, contraseña en claro en el `ALTER ROLE` si el servidor registra sentencias, y otros de severidad baja).
- La robustez espera a JUP-071; la validación en DockerServer y la primera ejecución de la CI en GitHub no se han hecho.
