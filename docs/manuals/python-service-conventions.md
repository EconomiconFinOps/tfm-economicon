# Convenciones de código para servicios Python

Convenciones obligatorias para código nuevo en `apps/backend` y `apps/processor`, más allá de lo que ya cubre `CONTRIBUTING.md` (proceso git/PR). Se añaden entradas aquí a medida que surgen, para no duplicarlas en cada README de servicio.

## Logging

Ambos servicios usan `structlog` configurado con salida JSON y correlación por `request_id` (ver `app/core/logging.py` y `app/core/request_context.py` de cada uno). No uses `logging.getLogger(__name__)` en código nuevo — usa `structlog.get_logger(__name__)`.

El `request_id` se inyecta automáticamente en cada log de una petición vía middleware + `contextvars`; no hace falta pasarlo a mano.

Introducido en JUP-042.

## Métricas

Ambos servicios exponen `GET /metrics` en formato Prometheus vía `prometheus_client` (ver `app/core/metrics.py` de cada uno). El `MetricsMiddleware` registra volumen de requests HTTP (`<servicio>_http_requests_total`, etiquetado por método/ruta/status) y latencia en segundos (`<servicio>_http_request_duration_seconds`), usando el patrón de ruta de FastAPI. Las rutas no emparejadas se agrupan bajo `__unmatched__` para mantener acotada la cardinalidad, y las excepciones no controladas se registran con status `500` antes de propagarse.

Las métricas de dominio (p. ej. `backend_ingest_jobs_total`, `backend_assistant_queries_total`) se incrementan en el propio handler de negocio, no en el middleware — el middleware solo conoce método/ruta/status, no intención de negocio.

Prometheus scrapea ambos `/metrics` en el stack local (`docker-compose.yml`, `apps/monitoring/prometheus/prometheus.yml`), y Grafana visualiza un dashboard mínimo provisionado como código (`apps/monitoring/grafana/`).

Introducido en JUP-043.

## Trazabilidad extremo a extremo (ingesta)

El `request_id` de la petición HTTP que crea un job (`POST /jobs/ingest`) viaja dentro del mensaje publicado a RabbitMQ (`job["request_id"]`). El `ProcessorWorker` (`apps/processor/app/workers/runner.py`), al consumir cada mensaje, hace `clear_contextvars()` seguido de `bind_contextvars(request_id=...)` con ese valor (o uno generado si el mensaje no lo trae) antes de procesar el job — todos los logs de `IngestTask`, `PipelineRunner` y sus dependencias heredan el `request_id` automáticamente, igual que ocurre con las peticiones HTTP.

No se persiste el `request_id` en la tabla `jobs`; vive solo en el mensaje de cola y en los logs.

Introducido en JUP-044.
