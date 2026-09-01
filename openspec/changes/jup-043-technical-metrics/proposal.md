JUP: JUP-043
Trello: https://trello.com/c/TI46x9Sr

## Why

El operador no tiene forma de conocer el estado de la plataforma más allá de leer logs uno a uno. JUP-042 dejó logging estructurado JSON con correlación por `request_id` (duración y código de estado por request), pero eso son eventos individuales, no métricas agregadas y consultables en el tiempo. Sin latencia, tasa de errores y volumen de consultas/ingestas expuestos como métricas, no se puede detectar degradación ni dimensionar carga sin grep manual de logs.

## What Changes

- Instrumentar `apps/backend` y `apps/processor` con `prometheus_client`, exponiendo un endpoint `GET /metrics` en formato Prometheus en cada servicio.
- Métricas mínimas por servicio: contador de requests HTTP por método/ruta/status (volumen y tasa de error), histograma de latencia (`duration_ms` ya calculado en el middleware existente), y contadores específicos de dominio: ingestas (`POST /jobs/ingest`) y consultas al asistente (`apps/backend/app/api/routes/assistant.py`).
- Añadir un servicio `prometheus` a `docker-compose.yml`, configurado para scrapear `backend:8000/metrics` y `processor:8001/metrics`.
- Añadir un servicio `grafana` a `docker-compose.yml` con un dashboard mínimo provisionado como código (provisioning por archivo, no configurado a mano), apuntando al `prometheus` del stack.
- Documentar la convención de métricas en `docs/manuals/python-service-conventions.md`, igual que se hizo con logging en JUP-042.

## Capabilities

### New Capabilities

- `technical-metrics`: expone métricas técnicas (latencia, errores, volumen de consultas e ingestas) vía `/metrics` en formato Prometheus en cada servicio, scrapeadas por un Prometheus local del stack de desarrollo.

### Modified Capabilities

(ninguna — no cambia el comportamiento de negocio existente, solo añade observabilidad)

## Impact

- **Nuevo código:** middleware/instrumentación de métricas en `apps/backend` y `apps/processor`; endpoint `/metrics` en ambos.
- **Dependencias nuevas:** `prometheus-client` en `apps/backend/requirements.txt` y `apps/processor/requirements.txt`.
- **Infraestructura:** nuevos servicios `prometheus` y `grafana` en `docker-compose.yml`, con configuración de scrape y provisioning de dashboard versionadas en el repo.
- **Documentación:** `docs/manuals/python-service-conventions.md`, `docs/architecture.md` (si se añade Prometheus/Grafana al diagrama de servicios).
- **Sin impacto en:** contratos de API existentes, frontend, esquema de base de datos.
