## 1. Backend: configuración base de structlog

- [x] 1.1 Añadir `structlog` a `apps/backend/requirements.txt`
- [x] 1.2 Reescribir `apps/backend/app/core/logging.py` para configurar `structlog` con salida JSON (campos mínimos: `timestamp`, `level`, `service`, `logger`, `event`)
- [x] 1.3 Test: arrancar el logging configurado y verificar que una línea de log emitida es JSON válido con esos campos

## 2. Backend: correlación por request

- [ ] 2.1 Añadir middleware FastAPI en `apps/backend/app/main.py` que genere un `request_id` (UUID) por petición y lo vincule vía `structlog.contextvars.bind_contextvars`
- [ ] 2.2 Test: dos peticiones concurrentes simuladas generan logs con `request_id` distinto cada una, sin mezclarse
- [ ] 2.3 Test: varias líneas de log dentro de una misma petición comparten el mismo `request_id`
- [ ] 2.4 Migrar `logging.getLogger(__name__)` existentes en `backend` a `structlog.get_logger(__name__)`

## 3. Processor: configuración base de structlog

- [ ] 3.1 Añadir `structlog` a `apps/processor/requirements.txt`
- [ ] 3.2 Reescribir `apps/processor/app/core/logging.py` para configurar `structlog` con salida JSON (mismos campos mínimos que backend)
- [ ] 3.3 Test: arrancar el logging configurado y verificar que una línea de log emitida es JSON válido

## 4. Processor: correlación por request

- [ ] 4.1 Añadir middleware FastAPI en `apps/processor/app/main.py` equivalente al de `backend`
- [ ] 4.2 Test: dos peticiones concurrentes simuladas generan logs con `request_id` distinto cada una
- [ ] 4.3 Test: varias líneas de log dentro de una misma petición comparten el mismo `request_id`
- [ ] 4.4 Migrar `logging.getLogger(__name__)` existentes en `processor` (`clients/azure_cost.py`, `tasks/azure_cost_ingest.py`, `workers/runner.py`, y equivalentes) a `structlog.get_logger(__name__)`

## 5. Verificación y cierre

- [ ] 5.1 Verificación manual local (`docker compose up`): una petición HTTP real produce logs JSON con el mismo `request_id` en `backend` y en `processor`
- [ ] 5.2 Ejecutar la batería de tests completa de ambos servicios y confirmar que no hay regresiones
- [ ] 5.3 Actualizar `review.md` documentando que no aplica ADR (decisión no arquitectónica/duradera, justificado en `design.md`) y cualquier alcance no cubierto (p. ej. módulos no migrados)
- [ ] 5.4 Crear `docs/manuals/python-service-conventions.md` con la convención de logging (usar `structlog.get_logger`, no `logging.getLogger`, en código nuevo de `backend`/`processor`) y añadir un enlace a ese archivo desde `## Notas` en `apps/backend/README.md` y `apps/processor/README.md`, sin duplicar el contenido
