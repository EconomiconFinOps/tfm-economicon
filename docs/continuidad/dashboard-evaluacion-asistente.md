# Dashboard de resultados de evaluación del asistente — JUP-121

Última actualización documental: 2026-10-15. Esta nota no repite el alcance de la tarjeta, que vive en [Trello](https://trello.com/c/aIdxwsXR).

## Estado

- Rama `feat/JUP-121-assistant-evaluation-dashboard`, creada desde `develop`; `origin/develop` integrado dos veces (JUP-120 y JUP-122). Sin push ni PR todavía.
- OpenSpec: `openspec/changes/jup-121-assistant-evaluation-dashboard/` (propuesta, diseño, spec, tareas y `review.md` con la evidencia por tarea). ADR: [ADR-0022](../adr/ADR-0022-assistant-evaluation-results-in-grafana.md), en estado Proposed.
- Guía y contrato de datos: [evaluation-dashboard.md](../validation/evaluation-dashboard.md). Manifiesto versionado: [evaluation-runs.json](../validation/evaluation-runs.json). Evidencia: [JUP-121-validation.md](../evidence/JUP-121-validation.md) y capturas en `docs/evidence/JUP-121/`.
- Producto: `tools/evaluation-dashboard.py` (adaptadores, SQL, carga, rol), `apps/monitoring/grafana/dashboards/assistant-evaluation.json` (21 paneles, secciones A, B y C), datasource `evaluation-postgres.yml`, variable `GRAFANA_EVALUATION_DB_PASSWORD` en `docker-compose.yml` y `.env.example`, scripts `evaluation-dashboard:*` y un paso de CI. Cambio mínimo en el backend: `assistant.py` crea a 0 las series de `backend_retrieval_failures_total`.

## Decisiones que no se deducen del código

- **PostgreSQL nativo como fuente** (esquema `evaluation` en el `postgres-pgvector` existente, rol `grafana_evaluation_reader` de solo lectura) y no Pushgateway, JSON directo ni un endpoint propio: Prometheus fecha lo que ingiere con la hora de ingesta, no la de la ejecución, y el datasource JSON necesita un plugin que no está instalado. Los informes siguen siendo la fuente de verdad; la base es una proyección que se tira y se recarga.
- **Contrato `rows-v1`:** JUP-071 (robustez) no existe aún; entra emitiendo ese formato o con su propio adaptador. Mientras tanto la sección de robustez muestra «Sin datos».
- **Lo no medido nunca es 0 %.** Las ejecuciones de plantilla, dobles o sintéticas se rotulan «no real» y sus series van discontinuas. Una serie con menos de dos puntos medidos no se dibuja.
- **Latencia y disponibilidad de campaña (tipo A) y de tráfico real (tipo C) no se mezclan** en un panel.
- **El `load` necesita la pila de Compose levantada y el `.env` completo**; la contraseña de Grafana y la de `load` son la misma variable.

## Qué tocar si cambia algo

- Un informe nuevo: añadir su adaptador a `tools/evaluation-dashboard.py` o emitir `rows-v1`, y una entrada en el manifiesto; el dashboard no cambia. Comprobar con `corepack pnpm evaluation-dashboard:rows`.
- Un panel: editar `assistant-evaluation.json` (las pruebas estructurales exigen tipo A/B/C, «Mide:» y «No demuestra:», un solo datasource por panel y los textos de «Sin datos»).
- Una categoría nueva de fallo de recuperación: se añade a `FAILURE_CATEGORIES` y la serie a 0 sale sola.
- Regenerar los datos: `corepack pnpm evaluation-dashboard:load`; pruebas: `corepack pnpm evaluation-dashboard:test` (las que usan PostgreSQL real necesitan Docker).

## Pendiente

- Revisión y validación independientes; PR a `develop`.
- Añadir `GRAFANA_EVALUATION_DB_PASSWORD` al `.env` local y al de DockerServer antes de levantar la pila: `docker compose` se niega a arrancar sin ella.
- Hallazgos diferidos con su detalle en `openspec/findings/backlog.md` (cargas simultáneas, contraseña en claro en el `ALTER ROLE` si el servidor registra sentencias, y otros de severidad baja).
- La robustez espera a JUP-071; la validación en DockerServer y la primera ejecución de la CI en GitHub no se han hecho.
