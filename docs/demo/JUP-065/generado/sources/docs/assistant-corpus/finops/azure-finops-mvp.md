# FinOps Para Azure Cost Management Simulado

## Proposito

Este documento resume el conocimiento FinOps minimo que el asistente de Economicon debe usar en el MVP. El contexto es Azure Cost Management en un escenario simulado: no describe una integracion con Azure real ni sustituye documentacion oficial de Microsoft o FinOps Foundation.

## Alcance Del MVP

Economicon debe ayudar a convertir datos de coste en visibilidad, responsabilidad y acciones verificables. Para el MVP, el asistente debe razonar sobre:

- coste y consumo en Azure;
- jerarquia de tenant, subscription, resource group y resource;
- tags como base de allocation;
- showback inicial;
- budgets, forecast y desviaciones;
- anomalias de coste;
- recomendaciones de optimizacion;
- commitments como Reservations y Savings Plans.

El asistente no debe afirmar que puede modificar recursos, consumir Azure real, ejecutar optimizaciones automaticas o consultar servicios cloud externos dentro de JUP-019.

## Idea Fundamental De FinOps

FinOps es una practica operativa y cultural para maximizar el valor empresarial de la tecnologia mediante colaboracion entre ingenieria, finanzas, producto y negocio.

No significa simplemente reducir factura. Una organizacion puede gastar mas y, aun asi, mejorar su eficiencia si ese gasto genera mas valor de negocio. La pregunta central no es solo cuanto se gasta, sino quien genera ese gasto, si era esperado, si esta optimizado y quien puede actuar.

## Ciclo Inform, Optimize, Operate

### Inform

La fase Inform crea visibilidad y contexto:

- coste total y coste por dimension;
- ownership por equipo, aplicacion o unidad;
- coste asignado, compartido y no asignado;
- evolucion temporal del gasto;
- cumplimiento de presupuesto;
- calidad de tagging.

En Azure, esta fase se apoya en Cost Analysis, exports, tags, presupuestos y reporting.

### Optimize

La fase Optimize identifica oportunidades:

- rightsizing;
- apagado programado;
- limpieza de recursos huerfanos;
- optimizacion de almacenamiento;
- optimizacion de observabilidad y logs;
- Reservations;
- Savings Plans;
- Azure Hybrid Benefit;
- cambios arquitectonicos que reduzcan coste sin romper requisitos.

### Operate

La fase Operate convierte el analisis en disciplina repetible:

- responsables claros;
- politicas y guardrails;
- alertas;
- revisiones periodicas;
- seguimiento de recomendaciones;
- verificacion del ahorro realizado.

## Conceptos FinOps Basicos

**Coste** es lo que se paga por tecnologia. **Valor** es lo que esa tecnologia permite conseguir. **Eficiencia** relaciona ambos conceptos.

Un **budget** es un objetivo o limite financiero para un periodo. En Azure Cost Management genera seguimiento y alertas, pero no apaga recursos por defecto.

Un **forecast** es una prediccion de gasto futuro. Es distinto del budget: el budget dice cuanto se esperaba gastar; el forecast estima cuanto se terminara gastando.

El **actual cost** se aproxima a la vista de facturacion. El **amortized cost** distribuye compromisos como Reservations o Savings Plans durante su periodo y suele ser mas util para showback.

## Jerarquia Azure Relevante

Una vista simplificada de Azure para Economicon es:

```text
Tenant -> Management Groups -> Subscriptions -> Resource Groups -> Resources
```

El **tenant** representa el contexto de identidad de la organizacion. La **subscription** es una frontera administrativa y de coste. El **resource group** agrupa recursos por ciclo de vida, aplicacion o entorno. El **resource** es la instancia concreta consumida.

El asistente debe evitar asumir que una subscription equivale siempre a un equipo o producto. La asignacion depende de la estructura organizativa, tags y reglas internas.

## Cost Management Y Cost Analysis

Cost Management permite analizar, monitorizar, asignar y optimizar costes de Microsoft Cloud. Para el MVP de Economicon son relevantes:

- Cost Analysis;
- budgets y alertas;
- anomaly detection;
- tags y tag inheritance;
- cost allocation;
- exports;
- Azure Advisor;
- Reservations y Savings Plans.

Metodo basico para investigar un aumento de costes:

1. Confirmar scope y periodo.
2. Comparar periodo actual contra baseline.
3. Agrupar por servicio.
4. Bajar a resource group y resource.
5. Revisar tags de ownership y aplicacion.
6. Correlacionar con despliegues, trafico o cambios de configuracion.
7. Decidir si el aumento es esperado, optimizable o anomalico.

## Tagging Y Allocation

Los tags son pares clave-valor que anaden contexto a recursos compatibles. Economicon usa tagging como una herramienta de allocation, no como unica fuente de verdad.

Tags minimos propuestos para el MVP:

| Tag | Objetivo |
| --- | --- |
| `costcenter` | Imputacion financiera |
| `owner` | Responsable operativo |
| `application` | Producto o aplicacion |
| `environment` | Entorno como prod, dev o test |
| `businessunit` | Unidad de negocio |

El cumplimiento debe medirse por coste, no solo por numero de recursos. Un unico recurso sin tags puede concentrar la mayor parte del gasto.

## Showback Y Chargeback

**Showback** muestra costes asignados a equipos o unidades sin repercusion contable formal. Es apropiado para el MVP porque mejora visibilidad y accountability sin requerir procesos financieros estrictos.

**Chargeback** repercute el coste formalmente a una unidad responsable. Debe esperar a que la calidad de allocation sea suficiente.

## Coste No Asignado Y Coste Compartido

El coste no asignado es coste que no puede asociarse con informacion suficiente a un owner, aplicacion, cost center u otra unidad responsable.

No debe confundirse con coste compartido. Un coste puede ser compartido y estar identificado; unallocated significa que falta informacion suficiente.

Estados recomendados:

- `allocated`: responsable conocido;
- `shared`: coste compartido conocido;
- `unallocated`: sin informacion suficiente;
- `excluded`: excluido por regla documentada.

## Budgets, Forecast Y Alertas

Un presupuesto ayuda a establecer expectativas. Un forecast ayuda a actuar antes de que ocurra un exceso. Para el MVP, el asistente debe explicar ambos conceptos y no tratarlos como equivalentes.

Un esquema simple de alertas puede incluir umbrales informativos, warning, criticos y excedidos. Cualquier automatizacion que modifique recursos queda fuera de JUP-019 y debe diseniarse explicitamente en otra historia.

## Anomalias De Coste

Una anomalia no es simplemente un coste alto. Es una desviacion inesperada respecto al comportamiento normal o previsto.

Ejemplo: si Log Analytics pasa de un gasto diario estable a un gasto muy superior tras una release, Economicon puede tratarlo como anomalia candidata y pedir investigacion.

Un workflow razonable:

1. Detectar desviacion.
2. Identificar scope y dimension responsable.
3. Encontrar owner.
4. Confirmar si el cambio era esperado.
5. Investigar causa tecnica o de negocio.
6. Estimar impacto.
7. Proponer accion.
8. Documentar resolucion o falso positivo.

## Recomendaciones De Optimizacion

Una recomendacion FinOps debe incluir evidencia, impacto estimado, riesgo y owner. No debe aplicarse automaticamente solo porque una herramienta la sugiera.

Categorias MVP:

- rightsizing;
- scheduling o apagado programado;
- limpieza de recursos huerfanos;
- optimizacion de almacenamiento;
- optimizacion de observabilidad;
- optimizacion de tarifa mediante commitments.

## Azure Advisor, Rightsizing Y Commitments

Azure Advisor puede ser una fuente de seniales, pero no una orden automatica. Antes de aplicar rightsizing hay que validar CPU, memoria, I/O, picos, SLA, crecimiento esperado y restricciones de negocio.

Un commitment es un compromiso financiero a cambio de descuento, como Reservations o Savings Plans. Antes de comprar commitments conviene aplicar rightsizing y confirmar una base de uso estable.

## Errores Comunes

- Reducir FinOps a "bajar factura".
- Pensar que un budget apaga recursos automaticamente.
- Aplicar recomendaciones sin validacion.
- Considerar todo recurso sin tag como unallocated.
- Mezclar shared cost con unallocated cost.
- Tratar rightsizing como downsizing.
- Confundir forecast y budget.
- Comprar commitments antes de optimizar consumo.

## Referencias De Contexto

- Microsoft Cost Management documentation.
- Azure Cost Analysis.
- FinOps Framework.
- FinOps Allocation, Anomaly Management y Forecasting capabilities.

Las referencias son contexto de diseno. JUP-019 no valida fuentes externas ni implementa integraciones.
