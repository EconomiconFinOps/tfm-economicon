# Contrato de herramientas del agente FinOps

- JUP: JUP-084
- Trello: https://trello.com/c/m1i7iXBm
- Estado: contrato propuesto; no implica que las herramientas esten implementadas

## Objetivo

Este documento define que puede pedir el agente FinOps de Economicon y que
servicio debe ejecutar cada operacion. El modelo selecciona herramientas y
explica resultados; Economicon controla autorizacion, datos, calculos,
evidencia y efectos.

## Funciones para el usuario

| Funcion | Resultado esperado |
| --- | --- |
| Visibilidad de costes | Gasto por periodo, suscripcion, servicio, resource group, ubicacion, precio o tag |
| Comparacion | Variacion absoluta, relativa y principales contribuidores entre dos periodos |
| KPIs | Metricas calculadas con formula, operandos, moneda y cobertura |
| Tagging y showback inicial | Cobertura por coste y dimensiones organizativas disponibles |
| Proyeccion | Run rate de cierre de periodo con advertencias de cobertura |
| Anomalias | Desviaciones candidatas con baseline, impacto y evidencia |
| Conocimiento | Explicaciones del corpus con citas |
| Optimizacion | Candidatos sustentados y datos adicionales necesarios |

## Arquitectura de ejecucion

```text
sesion autenticada
  -> ToolExecutionContext
  -> agente LiteLLM/OpenRouter
  -> validacion JSON Schema
  -> ToolRegistry
  -> servicio determinista o retrieval
  -> ToolResult
  -> respuesta explicada y citada
```

OpenRouter y LiteLLM aplican el patron en el que el modelo propone una llamada,
la aplicacion ejecuta la funcion y el resultado vuelve al modelo. Economicon no
delega la ejecucion al proveedor.

## Contexto no controlado por el modelo

```json
{
  "tenant_id": "tenant de la sesion",
  "user_id": "usuario autenticado",
  "roles": ["finops_viewer"],
  "correlation_id": "uuid",
  "locale": "es-ES"
}
```

Estos campos no aparecen en el schema que recibe el LLM. Una suscripcion pedida
por el modelo se valida contra los scopes permitidos por este contexto.

## Resultado comun

```json
{
  "status": "ok",
  "correlation_id": "uuid",
  "source": {
    "kind": "azure_cost_simulator",
    "dataset": "EA-Cost-Actual.sample.csv",
    "data_as_of": "2024-06-19"
  },
  "data": {},
  "evidence_ids": ["cost-query:sha256:..."],
  "assumptions": [],
  "limitations": []
}
```

Estados permitidos:

- `ok`
- `no_data`
- `partial`
- `insufficient_data`
- `unsupported`
- `forbidden`
- `confirmation_required`
- `error`

## Herramientas contratadas con los datos actuales

### `get_finops_capabilities`

Informa al agente antes de analizar:

- rango de fechas y moneda;
- scopes visibles;
- metricas, dimensiones y tags;
- herramientas habilitadas y experimentales;
- limitaciones conocidas.

Entrada:

```json
{}
```

No acepta tenant, usuario ni nombres inventados.

### `list_dimension_values`

Permite descubrir valores validos sin adivinarlos.

```json
{
  "dimension": "ServiceName",
  "search": "storage",
  "limit": 25
}
```

`dimension` pertenece a:

- `SubscriptionId`
- `SubscriptionName`
- `ResourceGroup`
- `ResourceLocation`
- `ServiceName`
- `MeterCategory`
- `ChargeType`
- `PublisherType`
- `PricingModel`
- `CostCenter`
- `Project`
- `env`
- `org`

`limit` se restringe a 1-50. Los tags se identifican en metadata para no
confundirlos con dimensiones Azure.

### `query_costs`

```json
{
  "subscription_id": "string",
  "period": {
    "from": "2024-06-01",
    "to": "2024-06-20"
  },
  "granularity": "daily",
  "group_by": [
    {"type": "dimension", "name": "ServiceName"},
    {"type": "tag", "name": "Project"}
  ],
  "filters": [
    {
      "type": "tag",
      "name": "env",
      "operator": "in",
      "values": ["prod"]
    }
  ],
  "top_n": 20
}
```

Reglas:

- coste `actual` y suma de `PreTaxCost`;
- scope de suscripcion;
- intervalo `[from, to)`;
- granularidad `daily` o `none`;
- cero, una o dos agrupaciones;
- filtros `in` sobre campos permitidos;
- `top_n` entre 1 y 50;
- importes negativos y cero conservados;
- moneda obligatoria en la salida.

### `compare_cost_periods`

```json
{
  "subscription_id": "string",
  "current_period": {"from": "2024-06-11", "to": "2024-06-20"},
  "baseline_period": {"from": "2024-06-02", "to": "2024-06-11"},
  "group_by": {"type": "dimension", "name": "ServiceName"},
  "filters": [],
  "top_n": 10
}
```

Devuelve coste actual y baseline, diferencias absoluta y relativa, duracion de
ambos periodos, cobertura y contribuidores. Si el baseline es cero, la
diferencia porcentual queda sin valor y se explica el motivo.

### `calculate_finops_kpis`

```json
{
  "subscription_id": "string",
  "period": {"from": "2024-06-01", "to": "2024-06-20"},
  "metrics": ["total_cost", "average_daily_cost", "tagging_compliance_by_cost"],
  "filters": []
}
```

Metricas contratadas inicialmente:

- `total_cost`
- `average_daily_cost`
- `tagging_compliance_by_cost`

`budget_variance`, `forecast_vs_budget`, `savings_realization` y
`unallocated_cost_pct` se anuncian solo cuando existen sus operandos y reglas.

### `analyze_tag_coverage`

```json
{
  "subscription_id": "string",
  "period": {"from": "2024-06-01", "to": "2024-06-20"},
  "required_tags": ["CostCenter", "Project", "env", "org"],
  "group_by": "Project"
}
```

Devuelve coste elegible, coste con y sin cada tag, porcentaje por coste y
principales scopes afectados. No denomina `unallocated` al coste sin `owner`
porque el dataset no contiene ese campo.

Aliases funcionales del MVP:

| Campo del dataset | Concepto Economicon |
| --- | --- |
| `CostCenter` | `costcenter` |
| `Project` | `application` |
| `env` | `environment` |
| `org` | `businessunit` |
| no disponible | `owner` |

### `search_finops_knowledge`

```json
{
  "query": "diferencia entre budget y forecast",
  "categories": ["finops", "business-rules", "glossary"],
  "top_k": 5
}
```

Devuelve para cada resultado:

- `document_id`
- `path`
- `section`
- `chunk_id`
- `content`
- `score`
- metadata de scope

Solo consulta documentos incluidos en el manifest del corpus y visibles para
el tenant.

## Herramientas condicionadas

### `project_period_end_cost`

Usa exclusivamente `run_rate`:

```text
projection = observed_cost / observed_days * period_days
```

Debe declarar dias observados, huecos, periodo proyectado y que no es un
forecast estadistico. No se ejecuta por debajo del minimo de cobertura
configurado.

### `detect_cost_anomaly_candidates`

La regla MVP inicial es:

```text
relative_delta > 20 % AND absolute_delta > 100 EUR/day
```

Devuelve candidatos con baseline, observado, scope, severidad y evidencia. No
confirma causa raiz ni utiliza la palabra anomalia sin calificarla como
candidata cuando faltan historico y contexto operativo.

## Herramientas futuras

| Herramienta | Precondicion |
| --- | --- |
| `evaluate_budget` | Repositorio de presupuestos o budget suministrado y validado |
| `get_rate_optimization_candidates` | Fuente de recomendaciones de Reservations integrada |
| `estimate_recommendation_impact` | Baseline y supuestos versionados |
| `create_recommendation_draft` | Persistencia, rol y confirmacion |
| `update_recommendation_status` | Workflow e idempotencia |
| `record_anomaly_outcome` | Persistencia de investigacion y ownership |

Las herramientas futuras no se envian al modelo mientras esten deshabilitadas.

## Superficie prohibida

No se registran:

- `execute_sql`
- `http_request`
- `run_shell`
- `execute_code`
- busqueda web general
- lectura de secretos o variables de entorno
- modificaciones Azure
- compra de Reservations o Savings Plans
- mensajeria Discord/Trello/GitHub

Una necesidad valida se implementa como herramienta de dominio con schema,
autorizacion y limites propios.

## Politica de orquestacion

1. Resolver si la pregunta es documental, numerica o mixta.
2. Consultar capacidades cuando el scope o la cobertura sean ambiguos.
3. Descubrir valores antes de usar un filtro no confirmado.
4. Ejecutar como maximo dos consultas de coste y cinco rondas totales.
5. Calcular mediante herramientas, nunca en el prompt.
6. Redactar separando hechos, inferencias, supuestos y limitaciones.
7. Citar documentos y evidence IDs de consultas.
8. Si faltan datos, decir que dato falta y que funcion podria habilitarlo.

La linea base usa llamadas secuenciales para comportarse igual con GLM-5.2 y
DeepSeek. El soporte de llamadas paralelas no forma parte del contrato.

## Ejemplos de enrutado

Pregunta: `Cuanto gastamos en Storage por proyecto en junio`.

```text
list_dimension_values(ServiceName, "Storage")
-> query_costs(group_by=Project, filter ServiceName=Storage)
-> respuesta con total, moneda, periodo y evidence ID
```

Pregunta: `Por que subio el coste`.

```text
compare_cost_periods(group_by=ServiceName)
-> si procede, segunda comparacion por ResourceGroup
-> explicacion de contribuidores; no causa raiz sin evidencia operativa
```

Pregunta: `Que VM deberia reducir`.

```text
get_finops_capabilities()
-> respuesta unsupported para rightsizing
-> explica que faltan CPU, memoria, I/O, picos y SLA
```

## Evaluacion minima

La implementacion posterior debe probar con GLM-5.2 y DeepSeek:

- seleccion correcta de herramienta;
- argumentos validos;
- rechazo de campos adicionales;
- aislamiento por tenant;
- precision numerica y moneda;
- no_data y cobertura insuficiente;
- citas y evidence IDs;
- ausencia de rightsizing inventado;
- limite de rondas;
- logs sin prompts, filas ni secretos.

## Fuentes de diseno consultadas

Consulta realizada el 27 de agosto de 2026:

- FinOps Framework: https://www.finops.org/framework/
- Reporting and Analytics: https://www.finops.org/framework/capabilities/reporting-analytics/
- Allocation: https://www.finops.org/framework/capabilities/allocation/
- Anomaly Management: https://www.finops.org/framework/capabilities/anomaly-management/
- Usage Optimization: https://www.finops.org/framework/capabilities/usage-optimization/
- Azure Cost Management Query: https://learn.microsoft.com/en-us/rest/api/cost-management/query/usage
- LiteLLM Function Calling: https://docs.litellm.ai/docs/completion/function_call
- OpenRouter Tool Calling: https://openrouter.ai/docs/guides/features/tool-calling

Estas fuentes orientan el diseno. El contrato normativo del MVP sigue siendo el
OpenSpec y el subconjunto Azure versionado en el repositorio.
