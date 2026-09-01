## 1. Backend: instrumentación HTTP

- [x] 1.1 Añadir `prometheus-client` a `apps/backend/requirements.txt`.
- [x] 1.2 Crear `apps/backend/app/core/metrics.py` con el `Counter` de requests HTTP (`backend_http_requests_total`, etiquetas método/ruta/status) y el `Histogram` de latencia (`backend_http_request_duration_ms`).
- [x] 1.3 Añadir `MetricsMiddleware` dedicado en `apps/backend/app/core/metrics.py` que incrementa el contador y observa la latencia, usando el patrón de ruta (`request.scope["route"].path`) como etiqueta, no la URL resuelta.
- [x] 1.4 Añadir el router de `GET /metrics` (usando `prometheus_client.generate_latest`) y registrarlo en `apps/backend/app/main.py`.

## 2. Backend: métricas de dominio

- [ ] 2.1 Añadir contador `backend_ingest_jobs_total` en `metrics.py` e incrementarlo en `create_ingest_job` (`apps/backend/app/api/routes/jobs.py`) tras una creación exitosa.
- [ ] 2.2 Añadir contador `backend_assistant_queries_total` e incrementarlo en el/los handler(s) de `apps/backend/app/api/routes/assistant.py` tras una respuesta exitosa.

## 3. Processor: instrumentación HTTP

- [ ] 3.1 Añadir `prometheus-client` a `apps/processor/requirements.txt`.
- [ ] 3.2 Crear `apps/processor/app/core/metrics.py` con el `Counter` de requests HTTP (`processor_http_requests_total`) y el `Histogram` de latencia (`processor_http_request_duration_ms`), replicando el patrón del backend.
- [ ] 3.3 Extender el middleware equivalente en `apps/processor/app/core/request_context.py`.
- [ ] 3.4 Añadir el router de `GET /metrics` y registrarlo en `apps/processor/app/main.py`.

## 4. Infraestructura: Prometheus y Grafana

- [ ] 4.1 Crear `apps/monitoring/prometheus/prometheus.yml` con jobs de scrape para `backend:8000/metrics` y `processor:8001/metrics`.
- [ ] 4.2 Añadir el servicio `prometheus` a `docker-compose.yml`, montando el archivo de configuración anterior, con healthcheck y puerto expuesto solo en local (`127.0.0.1`).
- [ ] 4.3 Crear el provisioning de Grafana (`apps/monitoring/grafana/provisioning/datasources/`, `.../dashboards/`) con el datasource de Prometheus y un dashboard mínimo (latencia p50/p95, tasa de error, volumen de ingestas y consultas).
- [ ] 4.4 Añadir el servicio `grafana` a `docker-compose.yml`, montando el provisioning anterior, con puerto expuesto solo en local.

## 5. Pruebas

- [ ] 5.1 Test de backend: `GET /metrics` responde 200 con contenido en formato Prometheus.
- [ ] 5.2 Test de backend: tras una request a un endpoint existente, el contador HTTP correspondiente aumenta.
- [ ] 5.3 Test de backend: tras `POST /jobs/ingest` exitoso, `backend_ingest_jobs_total` aumenta.
- [ ] 5.4 Test de backend: tras una consulta exitosa al asistente, `backend_assistant_queries_total` aumenta.
- [ ] 5.5 Test de processor: `GET /metrics` responde 200 con contenido en formato Prometheus.
- [ ] 5.6 Test de processor: tras una request existente, el contador HTTP correspondiente aumenta.

## 6. Documentación y cierre

- [ ] 6.1 Documentar la convención de métricas en `docs/manuals/python-service-conventions.md` (misma sección que logging, o una nueva "Métricas").
- [ ] 6.2 Actualizar `docs/architecture.md` si se añade Prometheus/Grafana al diagrama o descripción de servicios.
- [ ] 6.3 Ejecutar la batería de checks del carril (`openspec:validate`, `jup:check`, tests de backend/processor) y registrar el resultado en `review.md`.
- [ ] 6.4 Verificar manualmente que `docker compose up` levanta Prometheus y Grafana, que Prometheus scrapea ambos `/metrics`, y que el dashboard de Grafana muestra datos tras generar tráfico de prueba.
