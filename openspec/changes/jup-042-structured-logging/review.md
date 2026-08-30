# Review: jup-042-structured-logging

## Result

Pending team review (primera HU hands-on de Lucia; sin aprobación humana registrada aún)

## Scope Reviewed

- `apps/backend/app/core/logging.py`, `apps/backend/app/core/request_context.py`, `apps/backend/app/main.py`
- `apps/processor/app/core/logging.py`, `apps/processor/app/core/request_context.py`, `apps/processor/app/main.py`
- `apps/processor/app/clients/azure_cost.py`, `apps/processor/app/tasks/azure_cost_ingest.py`, `apps/processor/app/workers/runner.py`
- Tests nuevos/modificados en `apps/backend/tests/` y `apps/processor/tests/`
- `openspec/changes/jup-042-structured-logging/{proposal,design,specs,tasks}.md`

## Checklist

- [x] Implementation matches acceptance criteria (JSON estructurado + correlación por `request_id` en backend y processor, verificado con tests y con `docker compose` real).
- [x] Tasks are marked accurately in `tasks.md` (18/18).
- [x] Tests/checks were executed successfully (backend 14/14, processor 131/131).
- [x] `proposal.md`, `design.md`, `specs`, and `tasks.md` match the final state.
- [x] Architecture decisions are recorded in ADRs or explicitly marked not applicable.
- [x] All project decisions remain available in Git-tracked OpenSpec and project documentation.
- [x] No old harness structure was reintroduced.

ADR no aplicable. Justificado en `design.md`: elegir `structlog` es una decisión de tooling sustituible
sin coste ni vendor lock-in, no una decisión de arquitectura duradera (a diferencia de `ADR-0002`).

## Validation

```txt
apps/backend: python -m pytest tests -> PASS: 14/14
apps/processor: python -m pytest tests -> PASS: 131/131
docker compose up -d backend processor -> ambos "healthy"
Petición real GET /health en backend y processor -> logs JSON con el mismo request_id
  compartido entre todas las líneas de una misma petición, confirmado en ambos servicios.
```

## Review Findings

| ID | Tipo | Severidad | Scope | Descripcion | Accion | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-042-001 | Harness documentation | Low | Out of scope | La skill `openspec-apply-change` referencia `pnpm hu:check:pre-code`, un script que no existe en este repo (residuo de plantilla genérica). El gate real disponible es `pnpm jup:check -- --change <name>`. | Corregir la skill local para referenciar el script real | Open (skill personal, no versionada) |

## Risks / Follow-Ups

- La migración de `logging.getLogger` a `structlog.get_logger` en `processor` se completó en los tres
  módulos identificados en `design.md`. No quedan usos de `logging.getLogger` fuera de la propia
  configuración en ninguno de los dos servicios.
- El `.env` local de Lucia tenía `DATABASE_URL` con el esquema `postgresql+psycopg://` en vez de
  `cockroachdb+psycopg://` (desincronizado de `.env.example`, que ya tiene el valor correcto) — corregido
  localmente durante la verificación manual; no es un defecto del repo.
- Verificación manual (tarea 5.1) bloqueada inicialmente por: disco C: casi lleno (resuelto liberando
  espacio y moviendo el disco virtual de Docker a D:), y una capa de imagen Docker corrupta tras la
  migración de datos (resuelto con `docker system prune -af` + rebuild `--no-cache --pull`). Ninguno de
  los dos es un problema del código de esta HU.

## Human Approval

- Change: jup-042-structured-logging
- Approval type: pending
- Decision: pending
- Approver: pendiente (primera HU hands-on de Lucia; falta revisión de PR según el rol rotatorio de la
  tarjeta JUP-042)
- Notes: Implementación y verificación técnica completas (18/18 tareas). Pendiente de que el equipo
  revise el PR y registre su aprobación antes de mergear, siguiendo el mismo criterio ya aplicado en
  JUP-048/JUP-090 (no se atribuye aprobación no realizada).
