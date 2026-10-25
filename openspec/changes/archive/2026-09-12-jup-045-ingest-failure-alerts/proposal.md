JUP: JUP-045
Trello: https://trello.com/c/gDiwvnHh

## Why

Cuando falla la ingesta de una fuente de costes, hoy la única señal visible es el estado `failed` del job en base de datos y, si alguien lo mira, el dashboard de Grafana (JUP-043). No hay ningún mecanismo que empuje la alerta hacia el equipo: hay que entrar activamente a Grafana o consultar la base de datos para enterarse. El equipo consultó la posibilidad de notificar por Discord (webhook o canal dedicado) y decidió, por ahora, no abrir un canal externo: JUP-081 dejó la integración de Discord estrictamente de solo lectura de forma deliberada, y el equipo prefiere no reabrir esa decisión todavía. Esta HU se resuelve, por tanto, con alertas nativas de Grafana (Unified Alerting) sobre la métrica ya expuesta en JUP-043, visibles en el propio dashboard sin salir del stack observability.

## What Changes

- Nuevo contador Prometheus en `processor` para jobs de ingesta fallidos (`processor_ingest_jobs_failed_total`, o nombre equivalente), incrementado cuando un job de ingesta termina en estado `failed`.
- Regla de alerta de Grafana Unified Alerting provisionada como código (no configuración manual), que se dispara cuando el contador de fallos de ingesta crece por encima de un umbral en una ventana de tiempo.
- El estado de la alerta (`Normal`/`Pending`/`Firing`) es visible en el dashboard de Grafana ya existente (JUP-043), sin necesidad de un receptor externo (email/Discord/Slack) en esta iteración.
- Actualización de la documentación de convenciones (`docs/manuals/python-service-conventions.md`) explicando el nuevo contador y cómo se define una alerta.

## Capabilities

### New Capabilities
- `ingest-failure-alerting`: contador de fallos de ingesta en `processor` y regla de alerta de Grafana provisionada como código, visible en el dashboard sin receptor externo.

### Modified Capabilities
(ninguna: `technical-metrics` no cambia sus requisitos, solo se añade un contador nuevo dentro de la capability existente de alertado, que es nueva)

## Impact

- `apps/processor/app/core/metrics.py`: nuevo contador.
- `apps/processor/app/tasks/ingest.py` o `apps/processor/app/repositories/jobs.py` (donde se marca `failed`): incrementar el contador.
- Provisioning de Grafana (`infra/grafana/` o equivalente ya usado en JUP-043): nueva regla de alerta como código.
- Sin cambios en `apps/backend`, `apps/frontend` ni en la integración de Discord (JUP-081 no se toca).
