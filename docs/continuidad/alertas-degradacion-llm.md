# Alertas de degradación LLM — JUP-046

Verificación: 2026-10-10 (Europe/Paris). Encargo: «JUP-046 — Alertar degradación
del modelo o de la API LLM», delegado por chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`.
[Tarjeta](https://trello.com/c/R6CVFCif), id `69da41f6f6debfbd8bc43761`.

## Alcance y decisiones confirmadas

Lectura completa del registro oficial `materiales/07-evidencias/hito-mvp-2026-10-09/backlog-dispatch-source.json`
en workspace padre, contrastada con snapshot oficial DockerServer
`snapshot-20261010T071404Z.json`: Backlog, P1, sin dependencias refinadas y sin PR.
Sin cambios de prioridad, roles, fechas o criterios de aceptación.
Lucía liderazgo, Paris pairing, Víctor revisión, Alejandro validación.
Asignaciones no equivalen a participación realizada.

Revisados checkout, worktrees, ramas y PR: sin rama/PR JUP-046 previa.
Worktree propio `../tfm-economicon-jup046`, rama `feat/JUP-046-llm-alerts`,
base `c2995a118d419dfe725247bac9c6f219a3f0ea77` de origin/develop.
Checkout compartido y trabajo de otras tarjetas preservados.

Métricas por operación completa real, después de reintentos y validación; errores
y latencia separados de mock, configuración y salud. Prometheus/Grafana existentes,
tres reglas y dashboard; mínimo cinco operaciones en 5m, error >20%, p95 >10s
embeddings / >20s generación durante 2m. Umbrales iniciales revisables, no SLO
ratificados ni evaluación semántica nueva. Contadores cero por categoría desde la
primera operación evitan perder la primera ráfaga de un tipo de error posterior.

## Entrega y comprobación

- [Propuesta y diseño](../../openspec/changes/jup-046-llm-degradation/proposal.md).
- [Runbook](../runbooks/llm-degradation.md).
- [Evidencia por criterio](../evidence/JUP-046-validation.md).
- `apps/{backend,processor}/app/core/llm_metrics.py`, reglas en
  `apps/monitoring/grafana/provisioning/alerting/llm-degradation.yml` y dashboard.
- `node tools/llm-alerts-promtool.mjs --prepare <tmp>` extrae expresiones del YAML;
  Prometheus 2.55.1 ejecuta 19 escenarios sintéticos sin red. Grafana 11.3.0
  verifica provisioning por API aislada; no ejecución LLM ni notificación real.

## Pendientes concretos

Linux: processor 466 pass/57 skip y backend 910 pass/34 skip; 198 archivos Python
contrastados por SHA256 con las fuentes actuales. Windows: processor 6 fallos en
pruebas existentes (todos pasan Linux), backend completo interrumpido sin diagnóstico
confirmado; focales 63/12 correctos. No se relajan pruebas. Recibos en evidencia.
Publicación del enlace de contribución para liderazgo pendiente en este corte.
Adopción de la contribución, pairing atribuible, revisión de Víctor y validación
independiente siguen pendientes; esta implementación no emite dictámenes propios
de aceptación. Confirmar umbrales con tráfico representativo y revisar políticas
de notificación existentes antes de activar en entorno real. Archivar OpenSpec,
fusionar y cerrar tarjeta sólo mediante flujo humano del proyecto.

No desplegado, sin gasto de modelos ni Discord. Límite: primera muestra no reconstruible,
histograma aproximado, worker/API separados necesitan scrape/multiprocess, calidad
semántica y chat JUP-035 no demostrados. La evidencia histórica de JUP-067/070/047
se usa como contexto, no se presenta como prueba recién ejecutada.
