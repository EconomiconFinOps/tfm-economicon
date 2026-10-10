# Degradación LLM — JUP-046

[Tarjeta](https://trello.com/c/R6CVFCif) ·
[Diseño](../../openspec/changes/jup-046-llm-degradation/design.md) ·
[Evidencia](../evidence/JUP-046-validation.md)

En Grafana, abrir **Economicon — Degradación LLM** o **Alerting → Alert rules**,
grupo `llm-degradation`. Prometheus usa los `/metrics` existentes de backend y
processor. El despliegue existente monta todo el directorio de provisioning.
No requiere nueva clave, sonda de inferencia, servicio o receptor externo.

## Señales y umbrales

| Regla | Condición inicial | Ventana / mínimo / persistencia |
| --- | --- | --- |
| Errores LLM | Fallos terminales / operaciones >20% | 5m / 5 / 2m |
| Embeddings lentos | p95 >10s | 5m / 5 / 2m |
| Generación lenta | p95 >20s | 5m / 5 / 2m |

Evaluación cada minuto, separada por `job`, `instance` y `operation`. Igualdad al
umbral no dispara. Un incremento Prometheus extrapola entre scrapes; el mínimo
es sobre ese incremento estimado, no sobre un registro auditable de solicitudes.
Los objetivos son provisionales y editables en
`apps/monitoring/grafana/provisioning/alerting/llm-degradation.yml`.
Tras modificarlos, ejecutar las pruebas y ajustar los casos frontera conscientemente.

`llm_provider_requests_total{operation,outcome,category}` cuenta operaciones
completas; `llm_provider_request_duration_seconds{operation}` incluye reintentos,
esperas y validación. Categorías: timeout, connection, transport, authentication,
request, redirect, rate_limit, upstream, invalid_response; éxito usa `none`.
Un 503 recuperado no aumenta los fallos terminales, pero sí la latencia total.
Al empezar la primera operación real se inicializan a cero todas las categorías
acotadas, de modo que una categoría nueva conserve una línea base para `increase`.
Prometheus necesita un scrape previo: eventos anteriores al primer scrape no son
reconstruibles. Esa limitación de arranque no se presenta como salud confirmada.

## Diagnóstico

1. Consultar volumen junto a la alerta. `Normal` con menos de cinco muestras no
   demuestra salud. Con series ausentes se obtiene `NoData`; `Error` identifica
   un problema de consulta/evaluación. Ninguno equivale a degradación observada.
2. Abrir [salud del sistema](system-health.md). `not_configured`, `not_verified`
   y `unknown` siguen sus significados; liveliness de LiteLLM no prueba el modelo.
   Mock o falta de clave no generan éxitos ni fallos LLM artificiales.
3. Filtrar logs `llm_observation` por operation/outcome/category y correlación
   existente `request_id`/traza del job. Para intentos, consultar `litellm_failure`
   y `litellm_response` del processor. No pegar prompts, cuerpos, claves o URLs privadas.
4. `authentication`: revisar clave virtual y permisos en el gestor de secretos;
   `rate_limit`: revisar cuota; `timeout/connection/upstream`: conectividad y proveedor;
   `invalid_response`: revisar contrato/alias/modelo sin registrar el contenido.
5. Tras corregir, observar tráfico válido. La condición debe desaparecer al salir
   los eventos malos de la ventana; Grafana vuelve a Normal sin reiniciar la app.
   Si cesa el tráfico, dejar registrada la falta de evidencia de recuperación.

## Límites y despliegue

Backend mide embeddings de preguntas; processor embeddings de ingesta y generación
a través de `AgentRuntime.invoke`. Las llamadas directas futuras a otros clientes
deben adoptar el mismo contrato. El chat generativo JUP-035 no se da por integrado.
El proceso combinado `app.run_all` comparte registro entre API y worker; ejecutar
worker/API separados necesita multiprocess o otro endpoint scrapeable. No se
prueba la calidad semántica ni alucinaciones: usar evaluación JUP-067/JUP-070.

Los histogramas aproximan p95; las llamadas en curso no se cuentan hasta terminar.
Tras un reinicio se necesita histórico nuevo. Las reglas no crean canales de envío.
En una instalación con políticas propias de Grafana, revisar esas políticas antes
de activar para evitar notificaciones no autorizadas. Las pruebas aisladas no
disponen de Discord ni receptores externos.

## Verificación reproducible

Desde cada servicio ejecutar `python -m pytest tests/test_llm_metrics_jup046.py -q`.
Desde la raíz: `node --test tools/llm-alerts.test.mjs`; preparar fixtures mediante
`node tools/llm-alerts-promtool.mjs --prepare <directorio-temporal>` y ejecutar
`promtool test rules llm-tests.yml` dentro de ese directorio con Prometheus 2.55.1.
Las expresiones provienen del YAML de Grafana; no hay una réplica Python de PromQL.
Consultar evidencia para versiones, comandos exactos ejecutados y verificaciones pendientes.
