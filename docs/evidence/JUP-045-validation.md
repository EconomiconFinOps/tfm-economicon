# Evidencia de validación JUP-045

## Estado (2026-09-12)

Alertado de fallos de ingesta implementado sobre Grafana Unified Alerting, sin receptor externo (decisión explícita del equipo tras consultar en Discord sobre la política de solo-lectura de JUP-081).

## Suite de tests

```
apps/processor: 259 passed, 34 skipped
```

Nuevos: `apps/processor/tests/test_ingest_failure_metrics.py` (2 casos, TDD RED→GREEN): `mark_failed` incrementa `processor_ingest_jobs_failed_total`; `mark_completed` no lo incrementa.

## Verificación en vivo (Docker, stack completo)

1. **Provisioning de Grafana**: `docker compose up` carga `apps/monitoring/grafana/provisioning/alerting/ingest-failures.yml` sin pasos manuales. Se detectaron y corrigieron dos errores reales del YAML durante esta verificación:
   - Un `contactPoint` de tipo `grafana` con `settings: {}` es rechazado por Grafana (`no settings are set`); se eliminó por innecesario (sin receptor externo no hace falta contact point propio).
   - La expresión de umbral (`refId: C`, tipo `threshold`) necesitaba el campo `expression: A` explícito; sin él, Grafana no podía resolver sobre qué serie evaluar (`no variable specified to reference for refId C`).
2. **Scrape de Prometheus**: confirmado via `GET /api/v1/query` que `processor_ingest_jobs_failed_total` llega a Prometheus con el valor real expuesto por el `processor`.
3. **Transición de estado real** (`Normal → Pending → Firing`): login con usuario demo (`POST /auth/login`), 4 llamadas reales a `POST /jobs/ingest`, procesadas por el worker real del `processor` (mismo proceso que sirve `/metrics`). Los jobs fallaron por un bug preexistente no relacionado (`RF-045-001`, ver `openspec/findings/backlog.md`), lo que sirvió igualmente para demostrar el alertado sobre fallos reales:
   - `processor_ingest_jobs_failed_total` subió (RabbitMQ reintenta el mensaje fallido automáticamente).
   - La regla pasó a `Pending` en cuanto `increase(...[5m]) > 2`.
   - Tras el `for: 2m`, la regla pasó a `state: "firing"`, confirmado vía `GET /api/prometheus/grafana/api/v1/rules`.
4. Limpieza tras la verificación: purga de la cola `processor:jobs` para detener el bucle de reintentos del bug preexistente; `postgres-pgvector` restaurado.

## Hallazgo colateral

`RF-045-001` estaba abierto durante la validación del 12/09. Era un duplicado del residual de contrato de JUP-020 y quedó corregido por la PR #34, integrada en esta rama antes de la revisión. El registro actualizado está en `openspec/findings/backlog.md`; no requiere una tarjeta nueva.

## Revisión y validación adicional (2026-09-17)

Revisión realizada sobre `ac02815b4476cef9afa449fd42c4bdf61dcea872` y las correcciones de esta revisión. Por petición del usuario, se completa el trabajo pendiente de revisión y validación mediante la cuenta `Iber1to`, sin atribuir su ejecución a Paris o Victor ni modificar los roles rotatorios de Trello. Lucia conserva la autoría de la PR.

### Correcciones de revisión

- El dashboard no tenía ningún panel de estado de alertas pese a exigirlo la especificación. Se añade **Estado de alertas de ingesta**, de tipo `alertlist`, filtrado por nombre y visible también en estado normal.
- Se corrige el estado histórico de RF-045-001 y se documenta cómo retirar la regla de una instancia de Grafana con almacenamiento persistente.
- Se añade una regresión que comprueba que un error al persistir el estado `failed` no incrementa el contador. El contador mide marcas de fallo persistidas, incluidos los reintentos, no jobs únicos.

### Pruebas ejecutadas

| Comprobación | Resultado |
| --- | --- |
| `python -m pytest tests -q` en `apps/processor` | 266 passed, 34 skipped |
| Métricas y tarea de ingesta, ejecución focalizada | 14 passed |
| `openspec validate --all --strict --no-interactive` | 31 passed, 0 failed |
| `node --test tools/docker-topology.test.mjs` | 27 passed |
| Trazabilidad JUP, higiene del repositorio y `git diff --check` | Correctos |

Python local: 3.14; aparecen avisos de compatibilidad/deprecación de dependencias. Los 34 casos omitidos no se contabilizan como ejecutados. CI utiliza Python 3.12.

### Validación aislada de la regla y del dashboard

Se arrancaron Grafana **11.3.0** y Prometheus **v2.55.1** en una red Docker temporal, cargando sin modificaciones la regla, el datasource y el dashboard del repositorio. Se utilizó un exporter sintético con la métrica `processor_ingest_jobs_failed_total`, inicialmente a cero, scrapeado cada cinco segundos. Tras una evaluación normal se aumentó a cuatro y se mantuvo constante. Se conservaron la evaluación cada minuto, la ventana de cinco minutos y el `for: 2m` de la regla real.

Esta prueba verifica el motor de alertado y la visualización, no sustituye ni se presenta como una nueva ejecución de la ingesta completa con RabbitMQ y bases de datos. El recorrido real original está descrito en la evidencia del 12/09; el contador y sus llamadas se comprueban adicionalmente mediante la suite del processor.

El navegador, en modo Viewer, mostró la regla dentro del nuevo panel del dashboard, con su estado y sus etiquetas. No se configuró ningún receptor externo ni se envió ningún mensaje a Discord.

Estados confirmados mediante `GET /api/prometheus/grafana/api/v1/rules` (horas UTC del 17/09/2026; `health: ok` en todos los casos):

| Evaluación de Grafana | Estado |
| --- | --- |
| 14:59:10 | `inactive` / Normal, antes de incrementar el contador |
| 15:00:10 | `pending` |
| 15:02:10 | `firing`, confirmado también en el panel por navegador |
