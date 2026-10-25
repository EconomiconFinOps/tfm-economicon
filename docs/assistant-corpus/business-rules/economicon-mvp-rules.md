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

Los dos limites son estrictos: un aumento de exactamente 20 % o de exactamente 100 EUR/dia no activa la regla.

La doble condicion reduce ruido: una variacion porcentual grande con impacto minimo puede no ser prioritaria, y una variacion absoluta relevante puede requerir otra regla.

### Episodio y valor esperado

Una anomalia es un episodio: una anomalia candidata por cliente, moneda y servicio. Se abre el dia en que salta la regla y sigue siendo la misma mientras la regla vuelva a saltar dentro de 3 dias.

El valor esperado de un dia es la media diaria de los 7 dias anteriores. Mientras un episodio esta en seguimiento, el valor esperado es su referencia anclada: la media de los 7 dias previos a su inicio. Asi una subida que se mantiene sigue viendose aunque la media reciente ya la alcance.

El ultimo dia con datos del cliente se considera incompleto y no se evalua, ni el dia tomado como hoy ni los posteriores. Un dia solo se evalua si el y los 7 anteriores tienen datos del cliente.

Cuando pasan mas de 3 dias desde la ultima vez que salto la regla (es decir, al cuarto dia sin saltar), el episodio se muestra como "Ya no se observa". No se cierra solo: una persona debe cerrarlo. Si despues vuelve a saltar, se abre un episodio nuevo enlazado al anterior.

### Servicio sin gasto previo

Sin datos previos no se puede afirmar que un recurso nuevo cumpla o no cumpla la regla: con referencia cero el aumento relativo no esta definido. Por eso el primer dia de gasto de un servicio nuevo no abre un episodio. Desde el segundo dia la referencia incluye ese primer dia, de modo que un gasto nuevo y estable puede abrir un episodio desde el segundo dia si es lo bastante alto.

### Severidad

La severidad se calcula sobre el impacto acumulado del episodio: la suma, por cada dia evaluado mientras se sigue, de lo que el gasto observado supera la referencia. Se mide en la moneda del episodio y no se proyecta a un mes.

- P1 (Alta): impacto acumulado mayor que 2.000;
- P2 (Media): de 500 a 2.000, ambos incluidos;
- P3 (Baja): menor que 500.

Los umbrales son nominales en EUR y USD, sin conversion entre monedas. Otras monedas no se evaluan.

### Estados

Una anomalia es siempre una candidata: indica que hay que investigar si el cambio era esperado. No establece una causa, un ahorro ni una confianza estadistica. El reconocimiento que mide MTTA es el primer cambio de estado desde Nueva.

- `new`: abierta y sin revisar;
- `investigating`: una persona la esta investigando;
- `resolved`: cerrada porque se resolvio;
- `false_positive`: cerrada porque no era una anomalia.

Cerrar un episodio exige un motivo y es definitivo: si el gasto vuelve a subir, se abre un episodio nuevo. No existe un estado "reconocida" (`acknowledged`).

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

Campos conceptuales de un episodio:

- `id`;
- `service`;
- `currency`;
- `start_date`;
- `last_seen_date`;
- `expected_cost` (referencia);
- `accumulated_impact`;
- `impact_day_count`;
- `severity`;
- `status`;
- `closure_reason`.

La causa de una anomalia no se registra: queda sin establecer hasta que una persona la investigue.

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
