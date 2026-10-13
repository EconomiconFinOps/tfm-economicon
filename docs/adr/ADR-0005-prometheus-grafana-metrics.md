# ADR-0005: Métricas técnicas con Prometheus + Grafana

- Status: Proposed
- Date: 2026-09-01
- Related JUP/OpenSpec: JUP-043 and jup-043-technical-metrics
- Trello: https://trello.com/c/TI46x9Sr
- Supersedes: none
- Superseded by: none

## Context

JUP-042 dejó logging estructurado JSON con correlación por `request_id` (`apps/backend/app/core/logging.py`, `apps/processor/app/core/logging.py`), pero un log es un evento puntual, no una métrica agregable en el tiempo. El operador necesita conocer latencia, tasa de errores y volumen de consultas/ingestas de la plataforma sin tener que grepear logs manualmente. No existe hoy ningún stack de métricas ni de monitorización en el proyecto.

## Decision

Instrumentar `apps/backend` y `apps/processor` con la librería `prometheus_client`, exponiendo un endpoint `GET /metrics` en formato Prometheus en cada servicio. Añadir un servicio `prometheus` a `docker-compose.yml` que scrapea ambos `/metrics`, y un servicio `grafana` con un dashboard mínimo provisionado como código (archivos de provisioning versionados, no configuración manual desde la UI).

## Consequences

- Se añade una dependencia de librería (`prometheus-client`) y dos nuevos contenedores al stack local de desarrollo — más recursos y más tiempo de arranque de `docker compose up`.
- Las métricas quedan versionadas como código (definiciones de contador/histograma en el propio servicio, configuración de scrape y dashboards en el repo), coherente con cómo ya se gestiona el logging.
- Se abre un camino directo a alertas futuras (JUP-045, JUP-046) sobre las mismas métricas, sin reinstrumentar.
- El formato de exposición Prometheus es el estándar de facto en el ecosistema cloud-native; cualquier integración futura (p. ej. un Prometheus gestionado en la nube) puede scrapear el mismo endpoint sin cambios de código.

## Alternatives Considered

- **Métricas derivadas solo de los logs JSON existentes** (agregación externa tipo Loki/Grafana Loki): evita instrumentar código nuevo, pero requiere montar un backend de logs con capacidad de agregación que hoy tampoco existe, y separa la definición de "qué es una métrica" del código que la produce. Se descarta por añadir una pieza de infraestructura distinta sin ganar nada frente a instrumentar directamente.
- **Solo Prometheus, sin Grafana** (consultar métricas vía la UI nativa de Prometheus o `curl /metrics`): más simple, pero decidido explícitamente en contra por el usuario del proyecto — se quiere visualización utilizable como demo del MVP.
- **Un servicio de métricas gestionado externo** (Datadog, New Relic, etc.): fuera de alcance para un proyecto académico local sin presupuesto ni necesidad de multi-tenancy de observabilidad.

## Evidence And Follow-up

Ninguna evidencia operativa todavía (ADR propuesto junto con la implementación). Seguimiento: JUP-045 (alertar fallos de ingesta) y JUP-046 (alertar degradación del modelo/API LLM) deberían reutilizar las métricas expuestas aquí en lugar de instrumentar de nuevo.

## Reconciliación de evidencia — 01/10/2026

La frase «Ninguna evidencia operativa todavía» describe la propuesta inicial y
queda superada por el [review archivado JUP-043](../../openspec/changes/archive/2026-09-01-jup-043-technical-metrics/review.md):
metrics 200, scrape up=1, provisioning y cuatro paneles verificados entonces.
[PR #25](https://github.com/EconomiconFinOps/tfm-economicon/pull/25) está integrada
(08/09), con APPROVED de Victor el 08/09; las reviews anteriores figuran DISMISSED.
El registro histórico de aprobación pendiente en review.md no describe esa PR hoy.

Se conserva **Proposed**: la revisión de implementación y el merge se enlazan como
evidencia, sin inventar una ratificación explícita del estado de este ADR. Paris,
como revisor de JUP-061, debe confirmar la aceptación documental o registrar el
motivo para mantener la propuesta antes del freeze. Las alertas posteriores se
acreditan aparte en [JUP-045](../evidence/JUP-045-validation.md).
