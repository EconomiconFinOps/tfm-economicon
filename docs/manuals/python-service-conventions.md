# Convenciones de código para servicios Python

Convenciones obligatorias para código nuevo en `apps/backend` y `apps/processor`, más allá de lo que ya cubre `CONTRIBUTING.md` (proceso git/PR). Se añaden entradas aquí a medida que surgen, para no duplicarlas en cada README de servicio.

## Logging

Ambos servicios usan `structlog` configurado con salida JSON y correlación por `request_id` (ver `app/core/logging.py` y `app/core/request_context.py` de cada uno). No uses `logging.getLogger(__name__)` en código nuevo — usa `structlog.get_logger(__name__)`.

El `request_id` se inyecta automáticamente en cada log de una petición vía middleware + `contextvars`; no hace falta pasarlo a mano.

Introducido en JUP-042.
