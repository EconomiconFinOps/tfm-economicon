# Evidencia de validación JUP-045

## Estado (2026-09-12)

Alertado de fallos de ingesta implementado sobre Grafana Unified Alerting, sin receptor externo (decisión explícita del equipo tras consultar en Discord sobre la política de solo-lectura de JUP-081).

## Suite de tests

```
apps/processor: 259 passed, 34 skipped
```

Nuevos: `apps/processor/tests/test_ingest_failure_metrics.py` (2 casos, TDD RED→GREEN): `mark_failed` incrementa `processor_ingest_jobs_failed_total`; `mark_completed` no lo incrementa.

## Verificación en vivo (Docker, stack completo)

1. **Provisioning de Grafana**: `docker compose up` carga `apps/monitoring/grafana/provisioning/alerting/ingest-failures.yml` sin pasos manuales. Se detectaron y corrigieron dos errores reales del YAML durante esta verificación:
   - Un `contactPoint` de tipo `grafana` con `settings: {}` es rechazado por Grafana (`no settings are set`); se eliminó por innecesario (sin receptor externo no hace falta contact point propio).
   - La expresión de umbral (`refId: C`, tipo `threshold`) necesitaba el campo `expression: A` explícito; sin él, Grafana no podía resolver sobre qué serie evaluar (`no variable specified to reference for refId C`).
2. **Scrape de Prometheus**: confirmado via `GET /api/v1/query` que `processor_ingest_jobs_failed_total` llega a Prometheus con el valor real expuesto por el `processor`.
3. **Transición de estado real** (`Normal → Pending → Firing`): login con usuario demo (`POST /auth/login`), 4 llamadas reales a `POST /jobs/ingest`, procesadas por el worker real del `processor` (mismo proceso que sirve `/metrics`). Los jobs fallaron por un bug preexistente no relacionado (`RF-045-001`, ver `openspec/findings/backlog.md`), lo que sirvió igualmente para demostrar el alertado sobre fallos reales:
   - `processor_ingest_jobs_failed_total` subió (RabbitMQ reintenta el mensaje fallido automáticamente).
   - La regla pasó a `Pending` en cuanto `increase(...[5m]) > 2`.
   - Tras el `for: 2m`, la regla pasó a `state: "firing"`, confirmado vía `GET /api/prometheus/grafana/api/v1/rules`.
4. Limpieza tras la verificación: purga de la cola `processor:jobs` para detener el bucle de reintentos del bug preexistente; `postgres-pgvector` restaurado.

## Hallazgo colateral

`RF-045-001` (Open, High): la ingesta de texto real está rota en `develop` independientemente de JUP-045 — el `processor` nunca deserializa `job["payload"]` antes de invocar el pipeline, que espera `text_content` a nivel superior. No bloquea esta HU (el alertado funciona correctamente incluso sobre este fallo real), pero requiere una tarjeta propia.
