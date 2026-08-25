# Azure Cost API simulada

Servicio FastAPI que implementa el recorrido normal del subconjunto Azure Cost
Management Query definido en JUP-073. Lee el fixture público
`EA-Cost-Actual.sample.csv`; no se conecta a Azure ni simula un tenant real.

## Ejecutar

Desde `apps/azure-cost-api`:

```powershell
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

Desde la raíz:

```powershell
docker compose up --build azure-cost-api
```

Endpoints:

- `GET http://localhost:8002/health`
- `GET http://localhost:8002/openapi.json`
- `POST http://localhost:8002/subscriptions/{subscriptionId}/providers/Microsoft.CostManagement/query?api-version=2025-03-01`

## Capacidades de JUP-074

- scope de suscripción;
- `Usage` y `ActualCost`;
- `Custom`, `MonthToDate` y `TheLastMonth`;
- granularidad `Daily` y `None`;
- suma de `PreTaxCost`;
- filtros `In` con `and`/`or`;
- hasta dos agrupaciones de dimensiones o tags;
- respuesta posicional `columns`/`rows` y `nextLink: null`;
- validación estricta de campos extra y coherencia entre la versión del
  servicio y el contrato OpenAPI versionado;
- ejecución en contenedor como usuario sin privilegios y filesystem de solo
  lectura mediante Docker Compose.

JUP-075 añadirá paginación, autenticación simulada, `429`, timeout, páginas
vacías forzadas y datos inválidos. En JUP-074, enviar `$skiptoken` devuelve un
error explícito para evitar aparentar una capacidad todavía no implementada.

## Tests

```powershell
python -m pytest tests -v
```
