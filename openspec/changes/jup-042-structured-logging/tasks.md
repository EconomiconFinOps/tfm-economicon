## 1. Backend: configuración base de structlog

- [x] 1.1 Añadir `structlog` a `apps/backend/requirements.txt`
- [x] 1.2 Reescribir `apps/backend/app/core/logging.py` para configurar `structlog` con salida JSON (campos mínimos: `timestamp`, `level`, `service`, `logger`, `event`)
- [x] 1.3 Test: arrancar el logging configurado y verificar que una línea de log emitida es JSON válido con esos campos

## 2. Backend: correlación por request

- [x] 2.1 Añadir middleware FastAPI en `apps/backend/app/main.py` que genere un `request_id` (UUID) por petición y lo vincule vía `structlog.contextvars.bind_contextvars`
- [x] 2.2 Test: dos peticiones concurrentes simuladas generan logs con `request_id` distinto cada una, sin mezclarse
- [x] 2.3 Test: varias líneas de log dentro de una misma petición comparten el mismo `request_id`
- [x] 2.4 Migrar `logging.getLogger(__name__)` existentes en `backend` a `structlog.get_logger(__name__)` (no aplica: `backend` no tenía ningún uso fuera de `core/logging.py`)

## 3. Processor: configuración base de structlog

- [x] 3.1 Añadir `structlog` a `apps/processor/requirements.txt`
- [x] 3.2 Reescribir `apps/processor/app/core/logging.py` para configurar `structlog` con salida JSON (mismos campos mínimos que backend)
- [x] 3.3 Test: arrancar el logging configurado y verificar que una línea de log emitida es JSON válido

## 4. Processor: correlación por request

- [x] 4.1 Añadir middleware FastAPI en `apps/processor/app/main.py` equivalente al de `backend`
- [x] 4.2 Test: dos peticiones concurrentes simuladas generan logs con `request_id` distinto cada una
- [x] 4.3 Test: varias líneas de log dentro de una misma petición comparten el mismo `request_id`
- [x] 4.4 Migrar `logging.getLogger(__name__)` existentes en `processor` (`clients/azure_cost.py`, `tasks/azure_cost_ingest.py`, `workers/runner.py`, y equivalentes) a `structlog.get_logger(__name__)`

## 5. Access log propio (sustituye al de uvicorn)

- [x] 5.1 Backend: log JSON `http_request` (method, path, status_code, duration_ms, request_id) en `RequestIdMiddleware`, con test
- [x] 5.2 Backend: desactivar el access log nativo de uvicorn (`--no-access-log` en `Dockerfile` y `package.json`)
- [x] 5.3 Processor: mismo log JSON `http_request` en `RequestIdMiddleware`, con test
- [x] 5.4 Processor: desactivar el access log nativo de uvicorn (`access_log=False` en `run_all.py`/`run_api.py`)
- [x] 5.5 Verificación manual en Docker: confirmar que ya no aparece ninguna línea de texto plano de uvicorn

## 6. Verificación y cierre

- [x] 6.1 Verificación manual local (`docker compose up`): una petición HTTP real produce logs JSON con el mismo `request_id` en `backend` y en `processor`
- [x] 6.2 Ejecutar la batería de tests completa de ambos servicios y confirmar que no hay regresiones
- [x] 6.3 Actualizar `review.md` documentando que no aplica ADR (decisión no arquitectónica/duradera, justificado en `design.md`) y cualquier alcance no cubierto (p. ej. módulos no migrados)
- [x] 6.4 Crear `docs/manuals/python-service-conventions.md` con la convención de logging (usar `structlog.get_logger`, no `logging.getLogger`, en código nuevo de `backend`/`processor`) y añadir un enlace a ese archivo desde `## Notas` en `apps/backend/README.md` y `apps/processor/README.md`, sin duplicar el contenido
