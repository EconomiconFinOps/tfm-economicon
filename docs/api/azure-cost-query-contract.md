# Contrato Azure Cost Management Query de Economicon

Estado: propuesto para revisión del equipo en JUP-073.

## Objetivo

Este documento fija el subconjunto HTTP que compartirán el simulador de JUP-074
y el cliente de ingesta de JUP-076. La forma externa sigue la operación Query
Usage de Azure Cost Management; los datos proceden del fixture público aprobado
en JUP-072. No pretende emular toda la API de Azure.

Referencia oficial: <https://learn.microsoft.com/en-us/rest/api/cost-management/query/usage?view=rest-cost-management-2025-03-01>

Los artefactos normativos son:

- `docs/api/azure-cost-query.openapi.json`: ruta, schemas y respuestas HTTP.
- `docs/api/azure-cost-query-mapping.json`: correspondencia con el CSV.
- `docs/api/azure-cost-query-contract-cases.json`: casos que reutilizarán las pruebas.

Si este documento contradice el OpenAPI, prevalece el OpenAPI. Una ampliación
del subconjunto exige actualizar los tres artefactos y sus pruebas.

## Ruta y versión

```http
POST /subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query?api-version=2025-03-01
Content-Type: application/json
Authorization: Bearer <token-ficticio>
```

Solo se soporta scope de suscripción. `api-version` es obligatorio y debe ser
`2025-03-01`. Billing accounts, management groups y resource groups quedan fuera
del MVP y se podrán añadir sin cambiar el cliente para suscripciones.

## Autenticación simulada

El servicio podrá exigir un bearer configurado fuera del repositorio. No se
validan JWT, Entra ID, tenants, scopes OAuth ni credenciales Azure. En tests
unitarios la comprobación podrá deshabilitarse. Cuando esté activa:

- token ausente o diferente: `401 AuthenticationFailed`;
- la respuesta incluye `WWW-Authenticate: Bearer`;
- el mensaje nunca revela el token esperado.

## Request soportado

- `type`: `Usage` o `ActualCost`; ambos consultan `EA-Cost-Actual`.
- `timeframe`: `Custom`, `MonthToDate` o `TheLastMonth`.
- `timePeriod`: obligatorio únicamente con `Custom`; intervalo `[from, to)`.
- `dataset.granularity`: `Daily` o `None`.
- `dataset.aggregation`: entre una y dos expresiones, aunque el MVP solo define
  `Sum` sobre `PreTaxCost`.
- `dataset.grouping`: hasta dos dimensiones o tags.
- `dataset.filter`: comparaciones `In`, combinables recursivamente mediante
  `and` y `or` con al menos dos operandos.

Las fechas relativas usan un reloj configurable. En desarrollo, el reloj se
ancla a la fecha máxima del fixture para que `MonthToDate` y `TheLastMonth` sean
reproducibles sobre datos históricos.

### Dimensiones

| Nombre contractual | Columna de origen |
| --- | --- |
| `ResourceGroup` | `ResourceGroup` |
| `ResourceLocation` | `ResourceLocation` |
| `SubscriptionId` | `SubscriptionId` |
| `SubscriptionName` | `SubscriptionName` |
| `ServiceName` | `MeterCategory` |
| `MeterCategory` | `MeterCategory` |
| `ChargeType` | `ChargeType` |
| `PublisherType` | `PublisherType` |
| `PricingModel` | `PricingModel` |

Tags soportados: `CostCenter`, `Project`, `env` y `org`. El lector deberá tolerar
que `Tags` use el formato legado de la exportación EA. Los filtros de dimensiones
y tags ignoran mayúsculas; la respuesta conserva la grafía original.

## Response

El servicio devuelve `200` con un recurso Query:

```json
{
  "id": "/subscriptions/.../providers/Microsoft.CostManagement/Query/...",
  "name": "...",
  "type": "microsoft.costmanagement/Query",
  "properties": {
    "columns": [{"name": "PreTaxCost", "type": "Number"}],
    "rows": [[12.3456]],
    "nextLink": null
  }
}
```

Cada posición de `rows` corresponde a la misma posición de `columns`. El orden
es: agregaciones, agrupaciones, `UsageDate` cuando la granularidad es diaria y
`Currency` al final. `UsageDate` es un entero `yyyyMMdd`. Los importes se suman
sin eliminar valores negativos ni cero.

Una consulta válida sin datos devuelve `200`, conserva las columnas y usa
`rows: []` y `nextLink: null`. Se elige esta variante determinista en lugar del
`204` opcional documentado por Azure.

## Paginación

El tamaño de página es configuración del simulador. Cuando quedan filas,
`properties.nextLink` repite la ruta, `api-version` y añade `$skiptoken`. El
cliente reenvía exactamente el mismo body al seguir el enlace.

El token es opaco y queda ligado a:

- offset de la página siguiente;
- contenido canónico del request;
- subscription ID;
- checksum del dataset.

Un token alterado, caducado por cambio de dataset o utilizado con otra consulta
produce `400 InvalidSkipToken`. La última página usa `nextLink: null`.

## Errores contractuales

Todos usan `{"error": {"code": "...", "message": "..."}}`.

| HTTP | Código | Caso |
| ---: | --- | --- |
| 400 | `BadRequest` | Versión, timeframe, operador, dimensión, tag, agregación o granularidad no soportados |
| 400 | `InvalidSkipToken` | Token inválido o perteneciente a otra consulta/dataset |
| 401 | `AuthenticationFailed` | Bearer ficticio ausente o incorrecto con auth activa |
| 404 | `SubscriptionNotFound` | Suscripción no presente en el fixture |

Los errores no incluyen filas del dataset, secretos ni trazas internas.

## Límites deliberados

- Sin conexión a Azure ni validación Entra ID.
- Sin scopes distintos de suscripción.
- Sin `AmortizedCost`, `FocusCost` ni `PriceSheet` en este endpoint inicial.
- Sin operadores distintos de `In`.
- Sin ordenación configurable ni consultas de utilización de recursos.
- Sin promesa de forecasting: el fixture de costes solo cubre 19 días.

## Compatibilidad con las tareas siguientes

- JUP-074 implementará este OpenAPI en `apps/azure-cost-api`.
- JUP-075 añadirá fallos deterministas sin modificar el contrato normal.
- JUP-076 consumirá `columns`, `rows` y `nextLink` sin conocer el CSV.
- JUP-077 verificará el cambio entre URL simulada y URL real mediante
  configuración, sin afirmar que se ha probado contra un tenant real.
