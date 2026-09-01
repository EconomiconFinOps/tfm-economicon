# Review: jup-043-technical-metrics

## Result

Pending team review (implementación técnica completa; falta revisión de PR según el rol rotatorio de la tarjeta JUP-043)

## Scope Reviewed

- `apps/backend/app/core/metrics.py` (nuevo), `apps/backend/app/main.py`, `apps/backend/app/api/routes/jobs.py`, `apps/backend/app/api/routes/assistant.py`
- `apps/processor/app/core/metrics.py` (nuevo), `apps/processor/app/main.py`
- `apps/backend/requirements.txt`, `apps/processor/requirements.txt` (añadido `prometheus-client`)
- `docker-compose.yml` (nuevos servicios `prometheus`, `grafana`)
- `apps/monitoring/prometheus/prometheus.yml`, `apps/monitoring/grafana/provisioning/**`, `apps/monitoring/grafana/dashboards/technical-metrics.json`
- `docs/manuals/python-service-conventions.md`, `docs/architecture.md`
- `docs/adr/ADR-0003-prometheus-grafana-metrics.md`
- Tests nuevos en `apps/backend/tests/test_metrics.py`, `apps/backend/tests/test_domain_metrics.py`, `apps/processor/tests/test_metrics.py`
- `openspec/changes/jup-043-technical-metrics/{proposal,design,specs,tasks}.md`

## Checklist

- [x] Implementation matches acceptance criteria (`/metrics` en ambos servicios, contadores de dominio, Prometheus scrapeando, Grafana provisionado como código).
- [x] Tasks are marked accurately in `tasks.md` (28/28).
- [x] Tests/checks were executed successfully (backend 21/21, processor 136/136).
- [x] `proposal.md`, `design.md`, `specs`, and `tasks.md` match the final state.
- [x] Architecture decisions are recorded in ADRs — ADR-0003 registra la decisión de Prometheus + Grafana.
- [x] All project decisions remain available in Git-tracked OpenSpec and project documentation.
- [x] No old harness structure was reintroduced.

## Validation

```txt
apps/backend: python -m pytest -> PASS: 21/21
apps/processor: python -m pytest -> PASS: 136/136
corepack pnpm openspec:validate -> PASS: 18 items
corepack pnpm jup:check:all -> PASS (todos los changes activos, incluido jup-043)
corepack pnpm jup:cleanup:check -> PASS: 349 archivos
docker compose config -q -> sin errores de sintaxis
docker compose up -d backend processor prometheus grafana (+ dependencias) -> backend, processor,
  prometheus, cockroachdb, rabbitmq, postgres-pgvector, azure-cost-api healthy
GET http://localhost:8000/metrics -> 200, contiene backend_http_requests_total y
  backend_http_request_duration_ms_bucket con datos reales tras tráfico de prueba
GET http://localhost:8001/metrics -> 200, contiene processor_http_requests_total y
  processor_http_request_duration_ms_bucket con datos reales
GET http://localhost:9090/api/v1/query?query=up -> up{job="backend"}=1, up{job="processor"}=1
  (Prometheus scrapea ambos servicios correctamente)
Grafana: la primera migración SQLite fue extremadamente lenta en este equipo (causa raíz
  investigada y confirmada: el disco de datos de Docker Desktop está en D:, un HDD mecánico —
  CustomWslDistroDir en settings-store.json —, y cada transacción SQLite hace fsync, ~250-400ms
  por escritura en HDD). Tras dejarla completar, Grafana respondió en GET /api/health ("database":
  "ok"), el datasource de Prometheus quedó provisionado (GET /api/datasources) y el dashboard
  "Economicon — Métricas técnicas" apareció en GET /api/search. Confirmado visualmente por el
  usuario en http://localhost:3000: los 4 paneles (latencia p95, tasa de error, volumen de
  ingestas, volumen de consultas al asistente) se ven correctamente por servicio.
```

## Review Findings

Ninguno. La verificación incompleta del dashboard de Grafana (ver Validation) se investigó hasta
su causa raíz y resultó ser una particularidad de la máquina de desarrollo usada en esta sesión
(disco de datos de Docker Desktop en un HDD), no un defecto del código o la configuración
entregados — no califica como finding de proyecto.

## Risks / Follow-Ups

- El contador `backend_ingest_jobs_total`/`backend_assistant_queries_total` se probó a nivel de función (llamando a los handlers directamente con fakes), no con un cliente HTTP end-to-end contra la app completa — coherente con el resto de tests unitarios del repo, que tampoco usan `TestClient` sobre la app real.
- Quedan fuera de esta HU (documentado en `design.md` como Non-Goals): alertas (JUP-045/046), duración del pipeline de ingesta, latencia del LLM y de `azure-cost-api` — candidatas naturales para HUs futuras de observabilidad.
- El fallo de build de `apps/frontend` (`pnpm install`, `ERR_UNKNOWN_BUILTIN_MODULE`) encontrado durante `docker compose up --build` es preexistente y no relacionado con esta HU; no se tocó el frontend en JUP-043.

## Human Approval

- Change: jup-043-technical-metrics
- Approval type: pending
- Decision: pending
- Approver: pendiente (falta revisión de PR según el rol rotatorio de la tarjeta JUP-043 — Lucia Mateo)
- Notes: Implementación y verificación técnica completas (28/28 tareas). Pendiente de que el equipo revise el PR y registre su aprobación antes de mergear.
