# JUP-075 — Evidencia de validación

Fecha: 2026-08-08

Rama: `feat/JUP-075-azure-api-resilience`

Commit funcional desplegado: `8592829`

## Cobertura funcional

- autenticación Bearer simulada con `401 AuthenticationFailed` y cabecera
  `WWW-Authenticate`;
- identidad denegada con `403 AuthorizationFailed`;
- paginación mediante `$skiptoken` firmado con HMAC y ligado al body canónico,
  subscription ID y checksum del fixture;
- `429 TooManyRequests` con `Retry-After`;
- `500 InternalServerError`;
- timeout configurable y determinista;
- página vacía forzada que conserva continuación;
- coste inválido forzado para verificar validación del cliente;
- selección por `X-Fake-Azure-Scenario` o valor por defecto de entorno.

## Validación local

| Comprobación | Resultado |
| --- | --- |
| `python -m pytest tests -v` en `apps/azure-cost-api` | 34 pruebas superadas |
| `python -m unittest discover -s scripts/tests -v` | 8 pruebas superadas |
| `python -m compileall` de aplicación y pruebas | Correcto |
| Conversión de OpenAPI, mapping, casos y package JSON | Correcto |
| `git diff --check` | Correcto; solo avisos LF/CRLF de la estación Windows |
| Redocly CLI 2.46.0 | OpenAPI válido |

Las advertencias de pytest proceden del uso local de Python 3.14 con una API de
`asyncio` deprecada por FastAPI. La imagen usa Python 3.12.

## Despliegue remoto

- Host: `dockerserver`.
- Directorio: `/home/danteadmin/economicon-deployments/jup-075-8592829`.
- Proyecto Compose: `economicon-jup075`.
- Servicio: `economicon-jup075-azure-cost-api-1`.
- Puerto: `18003` hacia `8002`.
- Estado de Compose: `Up (healthy)`.

El healthcheck remoto confirmó 50 filas y 4 suscripciones. El script
`scripts/smoke_azure_cost_api.py`, ejecutado desde la estación de desarrollo
contra `http://dockerserver:18003`, confirmó:

```json
{
  "rows": 30,
  "pages": 3,
  "pageSize": 10,
  "auth": [401, 403],
  "errors": [429, 500],
  "timeoutSeconds": 2.006,
  "emptyPage": true,
  "invalidData": true,
  "status": "ok"
}
```

Las 30 filas se recuperaron en tres páginas sin duplicados. También se verificó
el rechazo de un `$skiptoken` alterado con `400 InvalidSkipToken`.

JUP-074 permanece disponible en `dockerserver:18002` como referencia del flujo
normal anterior, y JUP-075 en `dockerserver:18003` como entorno de resiliencia.

## Cierre pendiente del equipo

La implementación y la validación técnica están completas, pero la tarjeta debe
permanecer en curso hasta la revisión humana, la confirmación del remoto y la
creación del PR. Roles: Paris liderazgo, Victor pairing/coautoría, Alejandro
revisión y Lucia validación, pruebas y documentación.
