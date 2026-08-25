# Flujo E2E de costes Azure

Estado: implementado y validado en JUP-077 para integración en `develop`.

## Recorrido

```text
dataset público de Microsoft
  → Azure Cost fake API
  → cliente paginado y resiliente
  → normalización
  → CockroachDB
```

El cliente de JUP-076 obtiene todas las páginas y entrega filas tipadas. El
normalizador exige un `PreTaxCost` numérico y finito, convierte su valor a
decimal, valida `Currency` como código ISO de tres letras y convierte
`UsageDate` a una fecha estricta `yyyyMMdd`, conservando el resto de columnas
como dimensiones. Los costes cero y negativos son válidos porque el dataset
público puede contener consumo sin coste y créditos. El hash canónico trata
como equivalentes representaciones numéricas como `1` y `1.0`.

## Persistencia

`azure_cost_ingestion_runs` registra el estado y las métricas de cada recorrido.
`azure_cost_records` contiene las filas normalizadas. El identificador de la
ejecución es un UUID v5 derivado de tenant, suscripción y definición de consulta;
por eso la misma petición es idempotente. Al completar una repetición, las filas
anteriores de esa ejecución se reemplazan dentro de una única transacción.

Cada fila tiene además un hash SHA-256 del contenido normalizado y un UUID v5
derivado de la ejecución, posición y hash. No se persisten tokens Bearer ni se
incluyen en logs o mensajes de error.

El tenant y la suscripción se validan antes de crear ninguna ejecución; esta
última se canoniza sin distinguir mayúsculas. La migración exige estados
conocidos y vincula cada registro con su ejecución mediante una clave foránea.
Las actualizaciones y reemplazos de registros se limitan al tenant y la
suscripción correspondientes.

La conexión SQLAlchemy usa el adaptador de CockroachDB y el esquema
`cockroachdb+psycopg`; el dialecto PostgreSQL genérico no modela correctamente
las diferencias del servidor.

## Estados y errores

- `running`: la ejecución se ha registrado antes de llamar a la API;
- `completed`: todas las páginas se normalizaron y persistieron;
- `failed`: la API, la validación o la normalización falló; `error_code` guarda
  únicamente el nombre estable de la clase de error.

La inserción de registros y el cambio a `completed` son atómicos. Una ejecución
fallida elimina en la misma transacción cualquier fila previa de esa ejecución,
incluidas las de una repetición fallida, para no dejar estados inconsistentes.
Los errores controlados del cliente siguen
incluyendo `401`, `403`, agotamiento de `429`/`500`, timeout, página intermedia
vacía y respuesta malformada.

## Ejecución reproducible

Desde la raíz del repositorio, con la API falsa y CockroachDB disponibles:

```powershell
docker compose run --rm --no-deps processor python -m app.run_azure_cost_ingestion `
  --tenant-id tenant-demo `
  --subscription-id 64e355d7-997c-491d-b0c1-8414dccfcf42
```

El proceso termina con código `0` e imprime un resumen JSON si el número de
filas persistidas coincide con el resultado normalizado. Ante un error del
cliente termina con código `1` e imprime solo `status` y `error_code`.
