# Review: jup-044-e2e-tracing

## Result

Pending team review (implementación técnica completa; falta revisión de PR según el rol rotatorio de la tarjeta JUP-044 — Lucia Mateo)

## Scope Reviewed

- `apps/backend/app/api/routes/jobs.py` (propagación del `request_id` al job publicado)
- `apps/processor/app/workers/runner.py` (`ProcessorWorker._process_message`: bind/clear de `structlog.contextvars`)
- `docs/manuals/python-service-conventions.md` (nueva sección "Trazabilidad extremo a extremo")
- Tests nuevos: `apps/backend/tests/test_ingest_tracing.py`, `apps/processor/tests/test_worker_tracing.py`
- `openspec/changes/jup-044-e2e-tracing/{proposal,design,specs,tasks}.md`
- Housekeeping de proceso incluido en esta misma rama: archivado de `jup-042-structured-logging` y `jup-043-technical-metrics` (ambos ya mergeados sin ese paso), con promoción de sus capabilities a `openspec/specs/`.

## Checklist

- [x] Implementation matches acceptance criteria (`request_id` propagado del HTTP de ingesta al mensaje de cola, y de ahí a los logs del pipeline del processor).
- [x] Tasks are marked accurately in `tasks.md` (11/11).
- [x] Tests/checks were executed successfully (backend 26/26, processor 155/155 + 34 skipped de integración).
- [x] `proposal.md`, `design.md`, `specs`, and `tasks.md` match the final state.
- [x] Architecture decisions: ADR no aplicable (extiende la convención ya registrada en JUP-042, sin dependencia nueva).
- [x] All project decisions remain available in Git-tracked OpenSpec and project documentation.
- [x] No old harness structure was reintroduced.

## Validation

```txt
apps/backend: python -m pytest -> PASS: 26/26
apps/processor: python -m pytest -> PASS: 155/155 (34 skipped, integración CockroachDB real)
corepack pnpm openspec:validate -> PASS: 25/25 (incluye specs structured-logging y technical-metrics
  recién promocionados al archivar JUP-042/043)
corepack pnpm jup:check -- --change jup-044-e2e-tracing -> PASS
corepack pnpm jup:cleanup:check -> PASS: 441 archivos

Verificación manual en vivo (docker compose up, volumen de CockroachDB recreado desde cero):
- POST /jobs/ingest -> 202, log del backend con
  request_id=4fdf3085-e64d-4a74-981a-4d420259459b
- Mensaje inspeccionado directamente en RabbitMQ (management API,
  GET /api/queues/%2F/processor:jobs/get) -> payload incluye
  request_id=4fdf3085-e64d-4a74-981a-4d420259459b, idéntico al del backend
- Logs del processor ("Processing job ...") -> mismo request_id en cada línea,
  incluidos varios reintentos consecutivos del mismo job (nack/requeue) —
  confirma que el request_id sobrevive a reintentos, tal como documenta design.md
```

## Review Findings

| ID | Tipo | Severidad | Scope | Descripcion | Accion | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-044-001 | Concurrency bug / reliability | High | Out of scope | `run_all.py` lanza el hilo del worker y uvicorn en paralelo; ambos llaman a `Database.initialize()` sin coordinación. El perdedor de la carrera revienta con `UniqueViolation` en un hilo demonio — el processor queda "healthy" pero el worker está muerto en silencio, sin consumir jobs. Reproducido de forma determinista durante la verificación manual de esta HU (resultado distinto en arranques consecutivos). | Serializar la inicialización (un único punto de `database.initialize()`) | Open |

Descubierto de forma incidental durante la tarea 4.3 (verificación manual), no introducido por esta HU. Bloqueó parcialmente la primera ronda de verificación en vivo del lado del processor; superado reintentando el arranque hasta que el worker ganó la carrera, y confirmando entonces la correlación end-to-end con éxito.

## Risks / Follow-Ups

- `RF-044-001` (arriba) debería priorizarse pronto: afecta a la fiabilidad general del pipeline de ingesta, no solo a esta HU — el worker puede estar caído sin que ningún healthcheck lo detecte, ya que `/health` solo reporta el estado de la API.
- El contrato de `POST /jobs/ingest` y de `IngestJobResponse` no cambia; el `request_id` viaja solo dentro del mensaje interno de cola, coherente con lo decidido en `design.md`.
- Quedan fuera de esta HU (documentado como Non-Goals): tracing distribuido con spans, y el pipeline batch de ingesta de costes Azure (`azure_cost.py`), que no forma parte del flujo ingesta-de-documentos → respuesta del agente.

## Human Approval

- Change: jup-044-e2e-tracing
- Approval type: pending
- Decision: pending
- Approver: pendiente (falta revisión de PR según el rol rotatorio de la tarjeta JUP-044 — Lucia Mateo)
- Notes: Implementación y verificación técnica completas (11/11 tareas), incluida verificación manual en vivo end-to-end (backend → RabbitMQ → processor, con y sin reintentos). Se descubrió y registró `RF-044-001` (bug de concurrencia preexistente en `run_all.py`), no introducido ni resuelto por esta HU. Pendiente de que el equipo revise el PR y registre su decisión antes de mergear.
