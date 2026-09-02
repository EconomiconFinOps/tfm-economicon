JUP: JUP-043

Ver [ADR-0003](../../../docs/adr/ADR-0003-prometheus-grafana-metrics.md) para la decisión de arquitectura duradera (Prometheus + Grafana como stack de métricas).

## Context

`apps/backend` y `apps/processor` son servicios FastAPI que ya comparten patrón de middleware (`RequestIdMiddleware` en `app/core/request_context.py`) y de logging (`app/core/logging.py`, `structlog`, JSON). No existe hoy ninguna librería de métricas ni servicio de monitorización en `docker-compose.yml` (solo `cockroachdb`, `rabbitmq`, `postgres-pgvector`, `azure-cost-api`, `backend`, `processor`, `frontend`).

Endpoints de dominio relevantes para volumen: `POST /jobs/ingest` (`apps/backend/app/api/routes/jobs.py`) para ingestas, y las rutas de `apps/backend/app/api/routes/assistant.py` para consultas.

## Goals / Non-Goals

**Goals:**

- Exponer `GET /metrics` (formato Prometheus) en `backend` y `processor`.
- Medir, por servicio: volumen de requests HTTP por método/ruta/status, latencia (histograma), y contadores de dominio para ingestas y consultas al asistente.
- Levantar `prometheus` y `grafana` en `docker-compose.yml`, con configuración y dashboard versionados como código.
- Documentar la convención en `docs/manuals/python-service-conventions.md`.

**Non-Goals:**

- Alertas (Alertmanager, reglas de alerta): eso es JUP-045/JUP-046.
- Métricas de negocio de costes Azure (más allá del volumen de requests a esos endpoints).
- Persistencia de métricas a largo plazo o retención más allá de lo que Prometheus guarda localmente por defecto.
- Autenticación del endpoint `/metrics` o de Grafana más allá de lo mínimo del entorno local de desarrollo.

## Decisions

- **`prometheus_client` con métricas globales por proceso.** Se define un módulo `app/core/metrics.py` en cada servicio (mismo patrón que `app/core/logging.py`) con los objetos `Counter`/`Histogram` de `prometheus_client` creados una sola vez a nivel de módulo. Alternativa descartada: crear un `CollectorRegistry` por request, innecesario para un servicio single-process.

- **Instrumentación HTTP vía middleware dedicado, junto a `RequestIdMiddleware`.** Se añade un `MetricsMiddleware` independiente (no se mezcla con `RequestIdMiddleware`) que mide su propia duración y la observa en el histograma. Se mantiene separado del middleware de logging para no acoplar la responsabilidad de métricas a la de correlación/logging — cada uno puede evolucionar o desactivarse sin tocar el otro.

- **Métricas de dominio en el punto de negocio, no en el middleware.** El contador de ingestas se incrementa dentro de `create_ingest_job` (`jobs.py`), y el de consultas al asistente dentro de su handler — el middleware HTTP no distingue intención de negocio, solo ruta/método/status.

- **Nombres de métrica con prefijo por servicio** (`backend_http_requests_total`, `processor_http_requests_total`, etc.), para que ambos `/metrics` puedan coexistir sin colisión de series al verlos juntos en Grafana.

- **`/metrics` sin autenticación, solo accesible dentro de la red del compose.** No se expone puerto público adicional; Prometheus scrapea por nombre de servicio Docker (`backend:8000`, `processor:8001`), igual que ya hacen los healthchecks.

- **Provisioning de Grafana como código.** Datasource (Prometheus) y un dashboard mínimo (latencia p50/p95, tasa de error, volumen de ingestas y consultas) se versionan en `apps/monitoring/grafana/` (o ubicación equivalente), cargados vía provisioning de Grafana al arrancar — no configuración manual.

## Risks / Trade-offs

- **Más contenedores en el compose local** → tiempo de arranque más largo y más RAM en la máquina de desarrollo. Mitigación: healthchecks con `start_period` generoso, igual que el resto del stack, y documentar que son opcionales para quien solo trabaje en backend/processor sin observabilidad.
- **Doble instrumentación de latencia (log + métrica) puede desincronizarse** si se edita una sin la otra. Mitigación: ambas usan `perf_counter`; el log conserva milisegundos para lectura humana y la métrica usa segundos para respetar los buckets y la convención de Prometheus.
- **Cardinalidad de labels.** Etiquetar por `path` con valores dinámicos (p. ej. IDs en la URL) puede disparar el número de series. Mitigación: usar el patrón de ruta de FastAPI (`request.scope["route"].path`) y agrupar las rutas no emparejadas bajo `__unmatched__`, nunca usar la URL resuelta.

## Migration Plan

1. Añadir `prometheus-client` a `requirements.txt` de `backend` y `processor`.
2. Crear `app/core/metrics.py` en ambos servicios y extender/añadir el middleware de métricas.
3. Instrumentar `POST /jobs/ingest` y las rutas de `assistant.py`.
4. Añadir servicios `prometheus` y `grafana` a `docker-compose.yml` con su configuración versionada.
5. Documentar en `docs/manuals/python-service-conventions.md` y, si aplica, actualizar el diagrama de servicios en `docs/architecture.md`.
6. **Rollback:** revertir el middleware y los servicios de compose; no hay migración de datos ni cambio de contrato de API existente.

## Open Questions

- Retención y volumen de datos de Prometheus en local: se deja la configuración por defecto salvo que el equipo detecte problemas de espacio en disco durante el desarrollo.
