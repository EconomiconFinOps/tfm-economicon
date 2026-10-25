# Normalizacion FinOps de costes Azure

JUP-013 extiende el recorrido de JUP-077 sin crear una segunda ingesta:

```text
Azure Cost Query
  -> filas dinamicas validadas
  -> NormalizedCostRecord
  -> columnas FinOps + dimensiones adicionales
  -> CockroachDB
```

## Contrato normalizado

| Campo | Tipo | Origen |
| --- | --- | --- |
| `pretax_cost` | decimal obligatorio | `PreTaxCost` |
| `currency` | ISO de tres letras | `Currency` |
| `usage_date` | fecha opcional | `UsageDate` |
| `billing_account_id` | texto opcional | `BillingAccountId` |
| `subscription_name` | texto opcional | `SubscriptionName` / `SubAccountName` |
| `resource_group` | texto opcional | aliases EA, FOCUS y Query |
| `service_name` | texto opcional | `ServiceName`, `MeterCategory` o `ServiceCategory` |
| `project` | texto opcional | tag `Project` |
| `consumed_quantity` | decimal opcional | aliases de cantidad |
| `consumed_unit` | texto opcional | aliases de unidad |
| `tags` | objeto | JSON, formato legado EA o columnas de tag |
| `dimensions` | objeto | columnas adicionales no promovidas |

La suscripcion de alcance sigue en `azure_cost_records.subscription_id`: procede
del path autenticado de la consulta y no depende de que Azure la repita como
agrupacion. Ningun campo opcional se inventa cuando la consulta no lo devuelve.

## Canonicalizacion

Los nombres equivalentes se promueven antes de calcular el SHA-256. Se recorta
espacio, se normalizan moneda y nombres de tag, y se conserva el valor textual
de origen. Costes y cantidades cero o negativos son validos. Cantidad y unidad
forman una pareja: si falta uno de los dos, toda la normalizacion falla antes de
persistir.

## Persistencia

La migracion `003_normalized_cost_dimensions` es aditiva. Crea las columnas
tipadas, rellena resource group, servicio y proyecto cuando ya estaban en el
JSON de JUP-077, y anade indices por scope/fecha, resource group y servicio.
Las dimensiones desconocidas siguen disponibles en JSON para no perder datos.

La consulta de ejemplo agrupa por resource group y servicio. Otras perspectivas,
como proyecto o centro de coste, se ejecutan con otro definition file; Azure
solo devuelve las agrupaciones solicitadas y cada definicion conserva su run ID
idempotente.
