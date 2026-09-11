JUP-045

## Context

JUP-043 ya expone métricas técnicas de `backend` y `processor` en Prometheus y las visualiza en un
dashboard de Grafana provisionado como código (`apps/monitoring/grafana/`), según ADR-0005. Los
jobs de ingesta fallidos se registran hoy solo en base de datos: `JobsRepository.mark_failed()`
(`apps/processor/app/repositories/jobs.py`) marca el job como `failed`, pero nada emite una métrica
ni una notificación. La HU pide que el operador "reciba alertas... para corregirlo de inmediato".

El equipo evaluó notificar por Discord (webhook a un canal nuevo o al existente) pero decidió no
abrir un canal externo por ahora, para no reabrir la decisión de solo-lectura tomada en JUP-081.
Esta iteración se apoya, por tanto, únicamente en Grafana Unified Alerting (motor de alertado nativo
de Grafana 11.3, sin Alertmanager separado), con el estado de la alerta visible en el dashboard ya
existente.

## Goals / Non-Goals

**Goals:**
- Contar los fallos de ingesta como métrica Prometheus, igual que el resto de contadores de JUP-043.
- Definir una regla de alerta de Grafana como código (archivo versionado, sin pasos manuales) que
  pase a `Firing` cuando los fallos de ingesta superen un umbral en una ventana de tiempo.
- Que el estado de la alerta sea visible en el dashboard de Grafana sin acción manual al levantar el stack.

**Non-Goals:**
- No se implementa ningún receptor externo (Discord, email, Slack, webhook) en esta iteración: decisión
  explícita del equipo, revisable más adelante en una tarjeta propia si se abre un canal de alertas.
- No se toca la integración de Discord de JUP-081 (sigue estrictamente de solo lectura).
- No se rediseña el pipeline de ingesta ni sus reintentos; solo se instrumenta el fallo ya existente.

## Decisions

- **Contador dedicado `processor_ingest_jobs_failed_total`** (sin labels adicionales de momento,
  consistente con `backend_ingest_jobs_total` de JUP-043) en `apps/processor/app/core/metrics.py`,
  incrementado dentro de `JobsRepository.mark_failed()`. Alternativa descartada: derivar la alerta
  del contador genérico `processor_http_requests_total` con status `5xx` — no cubre fallos de ingesta
  que no pasan por HTTP (el worker consume de RabbitMQ), así que no es fiable como señal de negocio.
- **Grafana Unified Alerting como motor de alertado**, no un servicio nuevo (Alertmanager standalone,
  cron de polling, etc.): ya viene integrado en la imagen de Grafana que usa el proyecto (ADR-0005),
  se provisiona como código igual que el dashboard, y no añade infraestructura nueva. Se documenta como
  extensión de ADR-0005 en vez de un ADR nuevo, porque la decisión de fondo (Grafana como pieza central
  de observabilidad) ya está tomada; JUP-045 solo añade su capacidad de alertado nativa.
- **Regla de alerta provisionada en `apps/monitoring/grafana/provisioning/alerting/`** (carpeta nueva,
  hermana de `dashboards/` y `datasources/`), como archivo YAML de alert rules + un contact point
  "no-op" o de tipo `grafana` visible solo en la UI (sin integración externa), reflejando que no hay
  receptor externo en esta iteración.
- **Sin receptor externo**: la alerta cambia de estado (`Normal` → `Pending` → `Firing`) y es visible en
  el panel de Grafana, pero no empuja notificación fuera del stack. Esto es una limitación conocida y
  aceptada explícitamente por el equipo, no un descuido.
- **La regla evalúa `increase()` sobre una ventana móvil, no el valor absoluto del contador**: un
  `Counter` de Prometheus es monótono creciente (solo sube; solo se resetea si el proceso se reinicia),
  así que alertar sobre su valor absoluto dejaría la alerta en `Firing` para siempre en cuanto hubiera
  un solo fallo histórico. La condición de la regla usa `increase(processor_ingest_jobs_failed_total[5m])`
  (o ventana equivalente) para medir "fallos nuevos en los últimos N minutos"; cuando esa cifra vuelve a
  estar por debajo del umbral, la alerta vuelve a `Normal` sola, aunque el contador acumulado siga alto.

## Risks / Trade-offs

- [Riesgo] Sin receptor externo, un operador que no esté mirando Grafana activamente no se entera del
  fallo "de inmediato", que es literalmente lo que pide la HU → Mitigación: se documenta como limitación
  conocida en el proposal y en el review; si el equipo decide más adelante abrir un canal de alertas
  (Discord u otro), se resuelve en una tarjeta de seguimiento aparte sin rehacer esta base.
- [Riesgo] Un contador sin labels no permite distinguir qué fuente de ingesta falla → Mitigación: fuera
  de alcance de esta HU (la HU pide alertar, no diagnosticar); los logs ya correlacionados por JUP-044
  (`request_id`) permiten investigar el detalle una vez se sabe que algo falló.
- [Riesgo] Umbral de la regla de alerta mal calibrado (demasiado sensible → ruido; poco sensible → alertas
  tardías) → Mitigación: se documenta el umbral elegido y el motivo en tasks.md/review.md, ajustable sin
  cambios de código al vivir en el YAML de provisioning.

**Valores de partida** (sin datos reales de volumen de ingestas todavía, deliberadamente conservadores y
ajustables sin tocar código, solo el YAML de provisioning):
- Condición: `increase(processor_ingest_jobs_failed_total[5m]) > 2`
- Ventana de la query: `5m` (fallos nuevos en los últimos 5 minutos)
- `for`: `2m` (la condición debe mantenerse 2 minutos antes de pasar a `Firing`, para no disparar por un pico aislado)

## Migration Plan

- Nuevo contador y su incremento: cambio aditivo, sin migración de datos.
- Nueva carpeta de provisioning de alerting: Grafana la carga al arrancar (mismo mecanismo que dashboards);
  levantar el stack con `docker compose up` la aplica sin pasos manuales. Rollback: eliminar la carpeta o
  el `docker-compose.yml` revierte a estado JUP-043 sin efectos secundarios.

## Open Questions

- Si el equipo decide en el futuro abrir un canal de alertas externo, quién lo prioriza (tarjeta nueva,
  fuera de esta HU).
