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

## Capacidades

- scope de suscripción;
- `Usage` y `ActualCost`;
- `Custom`, `MonthToDate` y `TheLastMonth`;
- granularidad `Daily` y `None`;
- suma de `PreTaxCost`;
- filtros `In` con `and`/`or`;
- hasta dos agrupaciones de dimensiones o tags;
- respuesta posicional `columns`/`rows`;
- autenticación Bearer simulada con respuestas `401` y `403`;
- paginación determinista mediante `$skiptoken` firmado y ligado al request,
  suscripción y checksum del fixture;
- escenarios `rate-limit`, `server-error`, `timeout`, `empty-page` e
  `invalid-data` seleccionables mediante `X-Fake-Azure-Scenario`.

## Configuración de JUP-075

| Variable | Valor local por defecto | Uso |
| --- | --- | --- |
| `AZURE_COST_AUTH_ENABLED` | `true` | Activa el Bearer simulado |
| `AZURE_COST_VALID_TOKENS` | `jupiter-local-token` | Tokens permitidos, separados por comas |
| `AZURE_COST_FORBIDDEN_TOKENS` | `jupiter-forbidden-token` | Tokens que devuelven `403` |
| `AZURE_COST_PAGE_SIZE` | `10` | Filas por página |
| `AZURE_COST_SKIPTOKEN_SECRET` | valor local de ejemplo | Firma HMAC del token opaco |
| `AZURE_COST_DEFAULT_SCENARIO` | `normal` | Escenario aplicado si no llega header |
| `AZURE_COST_FAKE_TIMEOUT_SECONDS` | `2` | Retardo del escenario `timeout` |
| `AZURE_COST_RETRY_AFTER_SECONDS` | `1` | Cabecera del escenario `rate-limit` |

Los valores incluidos son exclusivamente locales y ficticios. Para probar una
consulta normal hay que enviar `Authorization: Bearer jupiter-local-token`.
Los escenarios nunca se eligen al azar y pueden forzarse, por ejemplo, con:

```http
X-Fake-Azure-Scenario: rate-limit
```

La respuesta será `429 TooManyRequests` con `Retry-After`. El documento
`docs/api/azure-cost-query-contract.md` contiene la semántica completa.

## Tests

```powershell
python -m pytest tests -v
```
