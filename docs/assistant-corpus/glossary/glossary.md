# Glosario Del Asistente Economicon

## Proposito

Este glosario fija definiciones breves para que el asistente use terminologia consistente en el MVP. Incluye terminos de FinOps, Azure, Economicon y RAG, aunque JUP-019 no implemente embeddings, retrieval ni citas finales.

## Terminos

### Tenant

Contexto de identidad y organizacion. En Azure suele asociarse a Microsoft Entra ID. En Economicon MVP no hay tenant real de cliente, pero el concepto se mantiene para compatibilidad futura con aislamiento por tenant.

### Management Group

Contenedor de gobierno para agrupar subscriptions y aplicar politicas o permisos a escala.

### Subscription

Contenedor administrativo y de facturacion de Azure. Es una frontera importante para acceso, cuotas, politicas y analisis de coste.

### Resource Group

Agrupacion logica de recursos Azure que normalmente comparten ciclo de vida, aplicacion o entorno.

### Resource

Instancia concreta consumida, como una VM, base de datos, Storage Account, App Service o recurso equivalente del dataset simulado.

### Scope

Conjunto de costes consultados o administrados. Puede corresponder a subscription, resource group, management group u otro contexto de analisis.

### Tag

Par clave-valor usado para anadir contexto a recursos compatibles. En FinOps ayuda a ownership, allocation, filtrado y reporting.

### Allocation

Practica de asignar costes y consumo a los grupos responsables o beneficiarios.

### Allocated Cost

Coste que puede asignarse de forma suficiente a un owner, aplicacion, cost center u otra dimension responsable.

### Shared Cost

Coste compartido conocido, como plataforma, observabilidad o red central, que requiere una regla de reparto.

### Unallocated Cost

Coste sin informacion suficiente para asignarse. No debe confundirse automaticamente con shared cost.

### Excluded Cost

Coste excluido explicitamente del modelo por una regla documentada.

### Showback

Practica de mostrar internamente a equipos o unidades el coste que generan o se les asigna, sin repercusion contable formal.

### Chargeback

Practica de repercutir costes formalmente a la unidad responsable mediante procesos financieros internos.

### Budget

Objetivo o limite financiero para un periodo. En Azure Cost Management genera seguimiento y alertas, pero no detiene recursos por defecto.

### Forecast

Prediccion del gasto futuro basada en comportamiento historico, tendencia o datos disponibles.

### Budget Variance

Diferencia entre coste real o previsto y presupuesto.

### Forecast Error

Diferencia entre un forecast previo y el coste real observado.

### Anomaly

Coste o uso inesperado respecto al comportamiento normal o previsto. No equivale necesariamente a coste alto.

### Baseline

Referencia historica o esperada contra la que se compara una metrica para detectar desviaciones.

### Recommendation

Hallazgo accionable que propone una optimizacion con evidencia, riesgo, owner y ahorro estimado.

### Savings Realization

Relacion entre ahorro identificado y ahorro efectivamente verificado tras aplicar una accion.

### Rightsizing

Ajuste de capacidad o configuracion de un recurso a la necesidad real del workload. No significa siempre reducir tamano.

### Commitment

Compromiso financiero de uso o gasto a cambio de descuento, como Reservations o Savings Plans.

### Reservation

Modelo de descuento basado en reservar capacidad o uso durante un periodo.

### Savings Plan

Modelo de descuento basado en comprometer gasto durante un periodo para determinados servicios o familias de compute.

### Actual Cost

Vista de coste cercana a la facturacion real del periodo.

### Amortized Cost

Vista de coste que distribuye commitments a lo largo de su periodo para representar mejor el coste economico del consumo.

### Azure Cost Management

Conjunto de herramientas de Microsoft para analizar, monitorizar, asignar y optimizar costes de Microsoft Cloud.

### Cost Analysis

Herramienta de Azure Cost Management para investigar costes por scope, periodo y dimensiones como servicio, resource group, recurso o tags.

### Azure Advisor

Servicio de Microsoft que genera recomendaciones, incluidas recomendaciones de coste. En Economicon debe tratarse como senial, no como orden automatica.

### Dataset

Conjunto de datos usado por el MVP. En JUP-019 se asume un contexto simulado y repo-local, no una fuente cloud real.

### Dataset ID

Identificador que permite asociar documentos del corpus a un dataset o contrato simulado concreto.

### Source Type

Tipo de fuente documental del corpus, por ejemplo contenido curado, documentacion de producto o reglas internas.

### Embedding

Representacion vectorial de texto que permite comparar similitud semantica. JUP-019 solo prepara documentos; los embeddings pertenecen a historias posteriores.

### Retrieval

Proceso de recuperar contexto relevante antes de responder. JUP-019 no implementa retrieval; solo define documentos para que otras historias los consuman.

### Citation

Referencia a la fuente usada para sustentar una respuesta. JUP-019 prepara metadata para citas futuras, pero no renderiza citas finales.
