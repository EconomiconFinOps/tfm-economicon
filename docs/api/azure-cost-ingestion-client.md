# Cliente de ingesta Azure Cost Management

Estado: implementado localmente en JUP-076.

## Responsabilidad

`apps/processor/app/clients/azure_cost.py` consume el contrato definido en
JUP-073 sin conocer el CSV que usa el simulador. El mismo código puede apuntar a
la API falsa o a Azure real cambiando únicamente URL y bearer.

El cliente:

- envía el mismo body a cada `nextLink`;
- combina todas las páginas en filas identificadas por nombre de columna;
- reintenta solo `429` y `500` hasta el límite configurado;
- usa `Retry-After` para `429` y backoff exponencial para `500`;
- aplica timeout a cada request;
- rechaza JSON, columnas, tipos y longitudes de fila inválidos;
- detecta páginas intermedias vacías, ciclos y exceso de páginas;
- rechaza un `nextLink` que cambie protocolo o autoridad antes de reenviar el
  bearer;
- emite eventos JSON sin body, token ni query string.

## Configuración

| Variable | Defecto local | Descripción |
| --- | --- | --- |
| `AZURE_COST_API_BASE_URL` | `http://azure-cost-api:8002` | Origen HTTP(S) de la API |
| `AZURE_COST_API_TOKEN` | `jupiter-local-token` | Bearer tratado como `SecretStr` |
| `AZURE_COST_API_VERSION` | `2025-03-01` | Versión contractual |
| `AZURE_COST_API_TIMEOUT_SECONDS` | `5` | Timeout por request |
| `AZURE_COST_API_MAX_RETRIES` | `3` | Reintentos adicionales por página |
| `AZURE_COST_API_RETRY_BACKOFF_SECONDS` | `0.25` | Base para backoff de `500` |
| `AZURE_COST_API_MAX_RETRY_AFTER_SECONDS` | `30` | Límite defensivo de espera |
| `AZURE_COST_API_MAX_PAGES` | `1000` | Protección contra ciclos o streams infinitos |

Para Azure real, el valor de `AZURE_COST_API_BASE_URL` será
`https://management.azure.com` y el bearer se proporcionará mediante el gestor
de secretos del entorno. El cliente no implementa obtención de tokens Entra ID;
esa responsabilidad quedará fuera del pipeline de normalización.

## Salida validada

`AzureCostQueryResult` contiene columnas estables, filas como diccionarios,
número de páginas y número de reintentos. Siempre exige `PreTaxCost` y
`Currency`. Cada valor se valida contra el tipo posicional `Number` o `String`
antes de que JUP-077 pueda persistirlo.

Una página final sin filas es un resultado válido. Una página vacía que todavía
incluye `nextLink` se considera anomalía y produce `AzureCostEmptyPageError`.

## Eventos de log

- `azure_cost_request`;
- `azure_cost_retry`;
- `azure_cost_page_received`;
- `azure_cost_ingestion_completed`.

Cada línea es JSON ordenado y contiene únicamente contadores, estado HTTP,
retardo, número de página y path. Nunca se registran `Authorization`, body,
query string ni el token opaco de continuación.
