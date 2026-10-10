JUP: JUP-046
Trello: https://trello.com/c/R6CVFCif

## Why

El operador tiene logs y salud de infraestructura, pero no alertas de errores o
latencia de operaciones LLM. La liveliness del gateway no prueba una inferencia.
La ausencia de configuración o tráfico tampoco acredita degradación observada.

## What Changes

- Contador e histograma de operaciones completas LiteLLM de generación y embeddings,
  incluyendo reintentos y validación de respuesta, en los endpoints `/metrics` existentes.
- Tres reglas Grafana con mínimo de muestra, persistencia y recuperación; panel y runbook.
- Pruebas de gateways dobles y del PromQL real, sin llamadas de pago ni notificaciones.

## Capabilities

### New Capabilities
- `llm-degradation-alerting`: alertas operativas sobre errores y latencia observados.

### Modified Capabilities
(ninguna)

## Impact

Backend: embeddings de consulta. Processor: embeddings de ingesta y generación
mediante AgentRuntime. Monitoring: provisioning existente Prometheus/Grafana.
Reutiliza JUP-042/043/044/045/047/067/070/108. No implementa chat JUP-035, probes
de pago, evaluación semántica ni integración de notificaciones. Los objetivos
iniciales de alerta son política operativa revisable, no SLO ratificados.
