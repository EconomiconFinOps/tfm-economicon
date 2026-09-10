# Review: jup-042-structured-logging

## Result

Pending team review (primera HU hands-on de Lucia; sin aprobación humana registrada aún)

## Scope Reviewed

- `apps/backend/app/core/logging.py`, `apps/backend/app/core/request_context.py`, `apps/backend/app/main.py`
- `apps/processor/app/core/logging.py`, `apps/processor/app/core/request_context.py`, `apps/processor/app/main.py`
- `apps/processor/app/clients/azure_cost.py`, `apps/processor/app/tasks/azure_cost_ingest.py`, `apps/processor/app/workers/runner.py`
- `apps/backend/app/run.py` (nuevo), `apps/backend/Dockerfile`, `apps/backend/package.json`, `apps/processor/app/run_all.py`, `apps/processor/app/run_api.py` (desactivación del access log y del log_config por defecto de uvicorn)
- `docs/manuals/python-service-conventions.md`, `apps/backend/README.md`, `apps/processor/README.md`
- Tests nuevos/modificados en `apps/backend/tests/` y `apps/processor/tests/`
- `openspec/changes/jup-042-structured-logging/{proposal,design,specs,tasks}.md`

## Checklist

- [x] Implementation matches acceptance criteria (JSON estructurado + correlación por `request_id` en backend y processor, verificado con tests y con `docker compose` real).
- [x] Tasks are marked accurately in `tasks.md` (18/18).
- [x] Tests/checks were executed successfully (backend 17/17, processor 134/134).
- [x] `proposal.md`, `design.md`, `specs`, and `tasks.md` match the final state.
- [x] Architecture decisions are recorded in ADRs or explicitly marked not applicable.
- [x] All project decisions remain available in Git-tracked OpenSpec and project documentation.
- [x] No old harness structure was reintroduced.

ADR no aplicable. Justificado en `design.md`: elegir `structlog` es una decisión de tooling sustituible
sin coste ni vendor lock-in, no una decisión de arquitectura duradera (a diferencia de `ADR-0002`).

## Validation

```txt
apps/backend: python -m pytest tests -> PASS: 17/17 (venv aislado)
apps/processor: python -m pytest tests -> PASS: 134/134 (venv aislado)
docker compose down -v && docker compose up -d --build backend processor -> ambos "healthy"
Petición real GET /health en backend y processor -> logs JSON con el mismo request_id
  compartido entre todas las líneas de una misma petición, confirmado en ambos servicios.
El access log nativo de uvicorn (texto plano) ya no aparece; sustituido por un evento
  "http_request" propio en JSON (method, path, status_code, duration_ms, request_id).
Las líneas de ciclo de vida de uvicorn (Started server process, Waiting for application
  shutdown, Application startup complete, etc.) también salen en JSON tras desactivar el
  log_config por defecto de uvicorn (logger "uvicorn.error"), confirmado con reinicio real
  de ambos contenedores.
GitHub Actions (PR #23): 6/6 checks en verde.
```

## Review Findings

| ID | Tipo | Severidad | Scope | Descripcion | Accion | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-042-001 | Harness documentation | Low | Out of scope | La skill `openspec-apply-change` referencia `pnpm hu:check:pre-code`, un script que no existe en este repo (residuo de plantilla genérica). El gate real disponible es `pnpm jup:check -- --change <name>`. | Corregir la skill local para referenciar el script real | Open (skill personal, no versionada) |
| RF-042-002 | Missing test dependency | Low | Fixed in this HU | `apps/backend/requirements-dev.txt` no declaraba `httpx`, usado directamente en los tests nuevos de middleware. Pasaba en local por contaminación del entorno global (instalado ya vía `processor`), pero fallaba en CI (entornos aislados). Detectado por el check `Python tests (backend)` del PR #23. | Añadido `httpx>=0.27.0` a `requirements-dev.txt`; verificado en venv aislado | Fixed |

## Risks / Follow-Ups

- La migración de `logging.getLogger` a `structlog.get_logger` en `processor` se completó en los tres
  módulos identificados en `design.md`. No quedan usos de `logging.getLogger` fuera de la propia
  configuración en ninguno de los dos servicios.
- Verificación manual (tarea 6.1) requirió ajustes de entorno local (config y Docker) sin relación con
  el código de esta HU; no aportan al contenido revisable del PR.

## Human Approval

- Change: jup-042-structured-logging
- Approval type: pending
- Decision: pending
- Approver: pendiente (primera HU hands-on de Lucia; falta revisión de PR según el rol rotatorio de la
  tarjeta JUP-042)
- Notes: Implementación y verificación técnica completas (18/18 tareas). Pendiente de que el equipo
  revise el PR y registre su aprobación antes de mergear, siguiendo el mismo criterio ya aplicado en
  JUP-048/JUP-090 (no se atribuye aprobación no realizada).
