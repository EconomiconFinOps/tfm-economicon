# Dataset público de Azure para Economicon

## Decisión para el MVP

Economicon utilizará como fuente de desarrollo el activo `dataset-examples.zip`
de Microsoft FinOps Toolkit v14. El ZIP original se conserva fuera de Git y se
identifica por su checksum. En el repositorio solo se versionan el informe de
auditoría, el auditor reproducible y fixtures pequeños con los valores públicos
originales.

Para JUP-073, la fuente principal recomendada es
`EA-Cost-Actual.sample.csv`. Permite implementar filtros y agregaciones del
contrato de Azure Cost Management Query sin mezclar coste real, amortizado y
FOCUS. Los demás fixtures sirven para pruebas de normalización y evoluciones
posteriores.

## Procedencia y licencia

| Campo | Valor |
| --- | --- |
| Repositorio | `microsoft/finops-toolkit` |
| Release | `v14`, publicada el 29 de abril de 2026 |
| Activo original | `dataset-examples.zip` |
| URL | `https://github.com/microsoft/finops-toolkit/releases/download/v14/dataset-examples.zip` |
| Tamaño local | 109.532.323 bytes |
| SHA-256 | `d7769d9e759b5968a68affcb364235ad938a705168c546ab86cad5bbb27ff607` |
| Licencia del repositorio | MIT |

El ZIP no contiene una licencia separada. Se considera un activo de la release
del repositorio MIT, pero deberá conservarse el aviso de licencia de Microsoft
si se redistribuye fuera del proyecto. Esta conclusión debe revisarse si se
cambia de release o de fuente.

## Inventario

| Entrada | Filas | Columnas | Uso recomendado |
| --- | ---: | ---: | --- |
| `EA-Cost-Actual.csv` | 135.253 | 55 | Fuente canónica del fake API |
| `EA-Cost-Amortized.csv` | 135.271 | 55 | Pruebas de coste amortizado |
| `EA-Cost-FOCUS_1.0-preview.csv` | 135.272 | 94 | Compatibilidad histórica; no usar como canónica |
| `EA-Cost-FOCUS_1.0.csv` | 135.272 | 96 | Pruebas de normalización FOCUS 1.0 |
| `EA-Prices.csv` | 753.716 | 23 | Catálogo de precios, separado del consumo |
| `EA-Reservations-Details.csv` | 300 | 11 | Uso de reservas EA |
| `EA-Reservations-Recommendations.csv` | 23 | 17 | Recomendaciones EA |
| `EA-Reservations-Transactions.csv` | 1 | 23 | Transacciones EA |
| `MCA-Reservations-Details.csv` | 173 | 11 | Uso de reservas MCA |
| `MCA-Reservations-Recommendations.csv` | 23 | 17 | Recomendaciones MCA |
| `MCA-Reservations-Transactions.csv` | 4 | 20 | Transacciones MCA |

Total: 1.295.308 registros y 933.889.205 bytes sin comprimir.

## Diccionario funcional mínimo

| Dimensión | Esquema EA Cost | Esquema FOCUS 1.0 |
| --- | --- | --- |
| Cuenta/suscripción | `BillingAccountId`, `SubscriptionId`, `SubscriptionName` | `BillingAccountId`, `SubAccountId`, `SubAccountName` |
| Tiempo | `Date`, `BillingPeriodStartDate`, `BillingPeriodEndDate` | `ChargePeriodStart`, `ChargePeriodEnd`, `BillingPeriodStart`, `BillingPeriodEnd` |
| Recurso | `ResourceId`, `ResourceGroup`, `ResourceName`, `ResourceLocation` | `ResourceId`, `x_ResourceGroupName`, `ResourceName`, `RegionName` |
| Servicio | `ConsumedService`, `MeterCategory`, `MeterSubCategory`, `MeterName` | `ServiceCategory`, `ServiceName`, `x_SkuMeterCategory`, `x_SkuMeterName` |
| Consumo | `Quantity`, `UnitOfMeasure` | `ConsumedQuantity`, `ConsumedUnit` |
| Coste | `CostInBillingCurrency`, `EffectivePrice`, `UnitPrice` | `BilledCost`, `EffectiveCost`, `ListCost`, `ContractedCost` |
| Moneda | `BillingCurrencyCode` | `BillingCurrency` |
| Clasificación | `ChargeType`, `PricingModel`, `PublisherType`, `Tags` | `ChargeCategory`, `PricingCategory`, `PublisherName`, `Tags` |

El fake API deberá normalizar nombres y tipos en su capa de lectura; no debe
exponer el CSV como si fuese directamente la respuesta de Azure.

## Resultados de calidad

- Las 11 entradas son CSV, no hay rutas inseguras, columnas duplicadas, filas
  vacías ni filas con una longitud distinta a la cabecera.
- Los costes EA abarcan del 1 al 19 de junio de 2024 dentro del periodo de
  facturación de junio. Hay 12 suscripciones, 233 grupos de recursos y 34-35
  categorías de medidor.
- Todos los valores analizados de cantidad y coste son numéricamente válidos.
  En coste real hay 40.143 importes negativos y 4.270 importes cero. No deben
  descartarse: pueden representar ajustes, créditos o reversiones.
- `EA-Cost-Actual` y `EA-Cost-Amortized` son vistas alternativas; sumarlas
  duplicaría el gasto. Las dos exportaciones FOCUS representan esencialmente el
  mismo periodo con versiones de esquema distintas y tampoco deben acumularse.
- Los datos de coste cubren menos de un mes. Son adecuados para filtros,
  agregaciones y demostraciones, pero insuficientes para validar forecasting
  estacional o detección robusta de anomalías.
- Los datos de reservas MCA son de febrero de 2025, mientras que EA y costes son
  de junio de 2024. Las pruebas deben controlar explícitamente ese desfase.
- Hay diferencias de mayúsculas en ubicaciones, grupos y resource IDs. La
  normalización debe conservar el valor original y usar una variante canónica
  para comparar.
- `Tags` y `AdditionalInfo` contienen estructuras serializadas. No debe asumirse
  que todas las celdas sean JSON bien formado sin una estrategia tolerante.

El detalle completo por columna, incluidos nulos, rangos, cardinalidades y
estadísticas numéricas, está en `docs/data/azure-dataset-audit.json`.

## Tratamiento de los datos públicos

Microsoft publica este dataset de ejemplo en GitHub como parte de FinOps
Toolkit. Los fixtures conservan literalmente los valores seleccionados, sin
anonimización ni seudonimización, lo que mantiene intactas las relaciones y los
casos de prueba del material original.

El ZIP completo no se versiona por su tamaño —más de 100 MB comprimido y unos
934 MB descomprimido—, no por restricciones de privacidad. El checksum, la URL
de descarga, el aviso MIT y las muestras versionadas permiten reproducir el
trabajo sin incorporar el archivo completo al repositorio.

Esta decisión aplica únicamente al dataset público de ejemplo. Si en el futuro
se conectan exportaciones reales de un tenant, su tratamiento deberá definirse
por separado.

## Reproducción

Desde la raíz del repositorio:

```powershell
python scripts/audit_azure_dataset.py `
  C:\ruta\local\dataset-examples.zip `
  --output docs/data/azure-dataset-audit.json `
  --fixture-dir fixtures/azure-cost `
  --sample-size 50
```

La consistencia del informe, el manifiesto, las 11 muestras, los costes
negativos/cero y la licencia MIT puede verificarse sin descargar de nuevo el ZIP:

```powershell
python -m unittest discover -s scripts/tests -p "test_audit_azure_dataset.py" -v
```

El muestreo depende del checksum y del contenido de cada fila, no del orden de
ejecución. Los valores seleccionados se copian sin transformaciones. Si cambia
el ZIP, cambiarán el informe, el manifiesto y los fixtures, haciendo visible la
actualización en la revisión de código.

## Criterios para JUP-073

- Cargar únicamente `EA-Cost-Actual.sample.csv` como dataset predeterminado.
- Convertir fechas, cantidades y costes a tipos explícitos al iniciar el servicio.
- Rechazar filas malformadas y reportar el error sin incluir el registro completo.
- Implementar agrupación mínima por suscripción, resource group, servicio y fecha.
- Mantener `actual` y `amortized` como datasets seleccionables, nunca acumulados.
- Añadir paginación determinista y tests que incluyan costes negativos y cero.
