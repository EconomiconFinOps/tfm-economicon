# JUP-076 — Evidencia de validación

Fecha: 2026-08-08

Rama: `feat/JUP-076-azure-cost-ingestion-client`

## Resultado

- Cliente configurable añadido a `apps/processor/app/clients/azure_cost.py`.
- Bearer almacenado como `SecretStr`.
- Paginación completa con validación del origen de `nextLink`.
- Reintentos acotados de `429` y `500`, con `Retry-After` y backoff.
- Timeout, límite de páginas y detección de ciclos.
- Validación estricta de `columns`, `rows`, tipos y columnas obligatorias.
- Eventos JSON sin credenciales ni contenido del dataset.

## Pruebas locales

Se creó un `.venv` ignorado por Git dentro de `apps/processor` y se instalaron
exclusivamente `requirements-dev.txt` y sus dependencias declaradas.

| Comprobación | Resultado |
| --- | --- |
| Suite completa de `apps/processor` | 25 pruebas superadas |
| Pruebas específicas del cliente | 22 pruebas superadas |

La suite cubre bearer y timeout configurables, dos páginas, `Retry-After`,
backoff exponencial, agotamiento de reintentos, `401` sin retry, página vacía,
respuesta vacía válida, JSON/columnas/filas/tipos inválidos, cambio de columnas,
`nextLink` externo, ciclos, límite de páginas y ausencia de secretos en logs.

## Prueba externa contra JUP-075

Comando ejecutado desde la raíz del worktree:

```powershell
python scripts/smoke_azure_cost_ingestion.py --base-url http://dockerserver:18003
```

Resultado:

```json
{
  "rows": 30,
  "pages": 3,
  "auth401": true,
  "rateLimitRetry": 1,
  "retryAfterSeconds": 1.0,
  "serverErrorRetry": 1,
  "timeoutDetected": true,
  "emptyPageDetected": true,
  "invalidDataDetected": true,
  "status": "ok"
}
```

Los escenarios `429` y `500` se aplicaron únicamente al primer intento; el
siguiente request fue normal y permitió demostrar el retry real contra el
servicio remoto. El timeout se probó con un límite de `0.2` segundos frente al
retardo remoto de dos segundos.

## Cierre pendiente

La tarjeta permanece en curso hasta revisión humana e integración. Roles:
Victor liderazgo, Alejandro pairing/coautoría, Lucia revisión y Paris
validación, pruebas y documentación.
