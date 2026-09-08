JUP: JUP-042
Trello: https://trello.com/c/vKCJl5NY

## Why

`backend` y `processor` solo tienen `logging.basicConfig` con texto plano y sin ningún tipo de correlación entre las líneas de log generadas por una misma petición HTTP. Cuando varias peticiones se procesan en paralelo, sus logs se entremezclan y no hay forma de reconstruir, a partir de un fallo, qué ocurrió durante esa petición concreta. Esto dificulta depurar errores en producción y no cumple el requisito de observabilidad del guion del proyecto.

## What Changes

- Sustituir la configuración de logging de `backend` y `processor` por logs en formato JSON estructurado (clave-valor), usando `structlog` como nueva dependencia en ambos servicios.
- Añadir un middleware FastAPI en cada servicio que genere un `request_id` (UUID) por petición HTTP entrante y lo propague vía `contextvars`.
- Inyectar automáticamente el `request_id` (y demás contexto relevante) en cada línea de log generada durante el ciclo de vida de esa petición, sin necesidad de pasarlo a mano en cada llamada a logger.
- El frontend queda explícitamente fuera de alcance: es una SPA sin logging de servidor; su instrumentación (error tracking de cliente) es un problema distinto y no forma parte de esta HU.

## Capabilities

### New Capabilities
- `structured-logging`: logging JSON estructurado con correlación por request (`request_id`) en los servicios `backend` y `processor`.

### Modified Capabilities

<!-- Ninguna. No existe ninguna capability de logging previa en openspec/specs/. -->

## Impact

- `apps/backend/app/core/logging.py`, `apps/processor/app/core/logging.py`: reescritos para configurar `structlog` con salida JSON.
- `apps/backend/app/main.py`, `apps/processor/app/main.py`: registro del nuevo middleware de correlación por request.
- `apps/backend/requirements.txt`, `apps/processor/requirements.txt`: nueva dependencia `structlog`.
- Todos los puntos donde ya se usa `logging.getLogger(__name__)` en ambos servicios pasan a usar el logger de `structlog` de forma progresiva (alcance detallado en `tasks.md`).
- Nuevo `docs/manuals/python-service-conventions.md`: convención de logging documentada como fuente única, enlazada desde `apps/backend/README.md` y `apps/processor/README.md` (evita duplicar la regla en ambos README).
- Sin impacto en el frontend ni en contratos de API existentes.
