## ADDED Requirements

### Requirement: Endpoint de métricas Prometheus por servicio

`apps/backend` y `apps/processor` SHALL exponer un endpoint `GET /metrics` que devuelve las métricas del proceso en formato de exposición de Prometheus.

#### Scenario: Consultar métricas de un servicio

- **WHEN** se hace `GET /metrics` contra `backend` o `processor`
- **THEN** la respuesta tiene `Content-Type` de texto Prometheus
- **AND** incluye al menos un contador de requests HTTP y un histograma de latencia

### Requirement: Volumen y latencia de requests HTTP

Cada servicio SHALL registrar, por cada request HTTP atendida, un incremento en un contador etiquetado por método, patrón de ruta y código de estado, y una observación de su duración en un histograma.

#### Scenario: Request exitosa incrementa el contador y observa latencia

- **WHEN** se completa una request HTTP con status `2xx`
- **THEN** el contador de requests del servicio se incrementa en 1 con las etiquetas de método, ruta y status correctos
- **AND** el histograma de latencia registra la duración de esa request

#### Scenario: Request con error queda contabilizada como error

- **WHEN** se completa una request HTTP con status `4xx` o `5xx`
- **THEN** el contador de requests se incrementa con el status real de error, permitiendo calcular la tasa de error por ruta

### Requirement: Volumen de ingestas y de consultas al asistente

El backend SHALL exponer un contador dedicado para el volumen de ingestas (`POST /jobs/ingest`) y otro para el volumen de consultas al asistente, independientes del contador genérico de requests HTTP.

#### Scenario: Se crea un job de ingesta

- **WHEN** se completa con éxito una petición a `POST /jobs/ingest`
- **THEN** el contador de ingestas se incrementa en 1

#### Scenario: Se realiza una consulta al asistente

- **WHEN** se completa con éxito una petición a un endpoint de `assistant.py`
- **THEN** el contador de consultas al asistente se incrementa en 1

### Requirement: Prometheus scrapea ambos servicios en el entorno local

El `docker-compose.yml` del proyecto SHALL incluir un servicio `prometheus` configurado para scrapear los endpoints `/metrics` de `backend` y `processor`.

#### Scenario: Levantar el stack local incluye Prometheus

- **WHEN** se ejecuta `docker compose up` con el stack completo
- **THEN** el servicio `prometheus` arranca y su configuración de scrape referencia `backend` y `processor` por nombre de servicio Docker

### Requirement: Dashboard de Grafana provisionado como código

El `docker-compose.yml` del proyecto SHALL incluir un servicio `grafana` cuyo datasource de Prometheus y dashboard mínimo (latencia, tasa de error, volumen de ingestas y consultas) se cargan por provisioning desde archivos versionados en el repositorio, sin configuración manual.

#### Scenario: Grafana arranca con el dashboard ya disponible

- **WHEN** se levanta el servicio `grafana` del compose por primera vez
- **THEN** el datasource de Prometheus y el dashboard mínimo están disponibles sin pasos manuales de configuración
