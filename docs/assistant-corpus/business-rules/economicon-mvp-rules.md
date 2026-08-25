# Reglas De Negocio MVP De Economicon

## Proposito

Este documento define reglas internas para el MVP de Economicon. Son decisiones de diseno para un escenario Azure simulado y no deben presentarse como estandares oficiales de Microsoft ni de FinOps Foundation.

## Alcance

Las reglas cubren:

- tagging minimo;
- estados de allocation;
- coste no asignado;
- KPIs base;
- anomalias;
- recomendaciones;
- modelo conceptual de datos.

No cubren cloud real, consumo real de Azure, automatizacion de recursos, embeddings, retrieval, modelos LLM ni UI.

## Reglas De Tagging

Economicon usara cinco tags minimos para el MVP:

| Tag | Ejemplo | Uso |
| --- | --- | --- |
| `costcenter` | `CC-1020` | Imputacion financiera |
| `owner` | `web-team` | Responsable operativo |
| `application` | `storefront` | Producto o aplicacion |
| `environment` | `prod` | Entorno |
| `businessunit` | `ecommerce` | Unidad de negocio |

Reglas:

- las claves se normalizan en minusculas;
- `environment` debe usar un catalogo controlado;
- `owner` debe apuntar preferentemente a equipo, no a persona;
- los tags no deben contener PII ni informacion sensible;
- el cumplimiento se mide por coste, no solo por numero de recursos.

## Estados De Allocation

Cada linea de coste elegible puede clasificarse como:

- `allocated`: se conoce responsable suficiente;
- `shared`: coste compartido conocido y sujeto a regla de reparto;
- `unallocated`: falta informacion suficiente para asignarlo;
- `excluded`: coste excluido por regla documentada.

Regla principal: shared no es lo mismo que unallocated. Un coste compartido puede estar identificado y gobernado; un coste no asignado representa falta de contexto.

## Coste No Asignado

KPI:

```text
Unallocated Cost % = Unallocated Cost / Total Eligible Cost * 100
```

Umbrales MVP propuestos:

- verde: menor o igual a 5 %;
- amarillo: mayor que 5 % y menor o igual a 10 %;
- rojo: mayor que 10 %.

Estos umbrales son internos y deben calibrarse con datos reales o con el dataset definitivo.

## KPIs Minimos

El MVP debe poder explicar estos KPIs:

| KPI | Formula o interpretacion |
| --- | --- |
| Monthly Cost | coste del periodo |
| Budget Variance | diferencia entre coste y presupuesto |
| Forecast vs Budget | desviacion prevista contra presupuesto |
| Forecast Error | diferencia entre forecast previo y coste real |
| Unallocated Cost % | coste no asignado sobre coste elegible |
| Tagging Compliance by Cost | coste correctamente etiquetado sobre coste etiquetable |
| Savings Realization | ahorro verificado frente a ahorro identificado |
| Anomaly MTTA / MTTR | tiempo hasta reconocimiento y resolucion |

KPIs opcionales si el escenario lo permite:

- commitment utilization;
- unit cost por pedido, cliente, llamada API o transaccion.

## Budgets Y Forecast

Un budget representa una expectativa o limite financiero. Un forecast representa una prediccion.

Reglas de interpretacion:

- forecast por encima de budget indica riesgo de overspend futuro;
- superar un umbral de budget debe generar investigacion, no apagado automatico;
- forecast y budget no deben mezclarse como si fueran la misma metrica.

## Anomalias

Una anomalia candidata puede detectarse con una regla determinista MVP:

```text
relative_delta > 20 % AND absolute_delta > 100 EUR/day
```

La doble condicion reduce ruido: una variacion porcentual grande con impacto minimo puede no ser prioritaria, y una variacion absoluta relevante puede requerir otra regla.

Severidad propuesta:

- P1: riesgo mayor que 2.000 EUR/mes o impacto critico;
- P2: entre 500 y 2.000 EUR/mes;
- P3: menor que 500 EUR/mes.

Estados sugeridos:

- `new`;
- `acknowledged`;
- `investigating`;
- `resolved`;
- `false_positive`.

Toda anomalia debe tener owner, scope, evidencia, impacto estimado y resolucion o motivo de falso positivo.

## Recomendaciones

Una recomendacion debe contener:

- recurso o scope afectado;
- categoria;
- evidencia;
- accion propuesta;
- ahorro estimado;
- confianza;
- riesgo;
- owner;
- estado;
- ahorro realizado si se verifica.

Categorias MVP:

- rightsizing;
- scheduling;
- orphan cleanup;
- storage optimization;
- observability optimization;
- rate optimization o commitments.

Estados sugeridos:

```text
new -> reviewed -> accepted/rejected -> implemented -> verified
```

Regla clave: ninguna recomendacion se aplica automaticamente dentro de JUP-019.

## Modelo Conceptual De Datos

El MVP debe separar datos originales del proveedor y datos derivados por Economicon.

### CostRecord

Campos conceptuales:

- `id`;
- `date`;
- `provider`;
- `subscription_id`;
- `resource_group`;
- `resource_id`;
- `service`;
- `cost`;
- `currency`;
- `tags`;
- `allocation_status`;
- `allocation_target`.

### Budget

Campos conceptuales:

- `scope`;
- `period`;
- `amount`;
- `currency`;
- `thresholds`.

### Anomaly

Campos conceptuales:

- `id`;
- `scope`;
- `metric_date`;
- `expected_cost`;
- `observed_cost`;
- `absolute_delta`;
- `relative_delta`;
- `severity`;
- `owner`;
- `status`;
- `root_cause`.

### Recommendation

Campos conceptuales:

- `id`;
- `resource_id`;
- `category`;
- `current_cost`;
- `estimated_saving`;
- `confidence`;
- `risk`;
- `owner`;
- `status`;
- `realized_saving`.

## Nota Sobre Reglas Internas

Las reglas de tags, umbrales, severidades y estados son propuestas MVP de Economicon. Deben revisarse si cambia el dataset, el volumen de gasto, la estructura organizativa o la madurez FinOps.
