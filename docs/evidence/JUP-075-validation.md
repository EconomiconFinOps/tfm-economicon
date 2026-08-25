# JUP-075 — Evidencia de validación

Fecha: 2026-08-25

Rama: `feat/JUP-075-azure-api-resilience`

Base integrada: `develop`, incluyendo JUP-072, JUP-073 y JUP-074.

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
- selección por `X-Fake-Azure-Scenario` o valor por defecto de entorno;
- validación anticipada de tamaño de página, timeout, `Retry-After`, secretos,
  escenarios permitidos e identidades inconsistentes;
- conservación de validación estricta, contrato cargado en startup y contenedor
  sin privilegios con filesystem de solo lectura.

## Validación local

| Comprobación | Resultado |
| --- | --- |
| `python -m pytest tests -v` en `apps/azure-cost-api` | 58 pruebas superadas |
| `python -m unittest discover -s scripts/tests -v` | 21 pruebas de dataset y contrato superadas |
| `corepack pnpm openspec:validate` | 10 especificaciones/cambios válidos |
| `corepack pnpm jup:check -- --change jup-075-azure-api-resilience` | Trazabilidad Trello/OpenSpec correcta |
| `corepack pnpm build` | Frontend, backend, processor y Azure API compilados |
| `corepack pnpm test` | 58 pruebas Azure, 10 backend y 3 processor superadas |
| Checkers JUP y corpus documental | 6 + 6 + 8 pruebas superadas |
| Redocly CLI 2.46.0 | OpenAPI válido, sin advertencias contractuales |

Las advertencias de pytest proceden del uso local de Python 3.14 con una API de
`asyncio` deprecada por FastAPI. La imagen usa Python 3.12.

## Validación Docker real en `dockerserver`

- Host: `dockerserver`.
- Imagen construida: `economicon-azure-cost-api:jup-075`.
- Contexto de construcción: aproximadamente `1.272 MB`.
- Contenedor temporal: `economicon-jup-075-smoke`.
- Puerto de verificación: `18075` del host hacia `8002` del contenedor.
- Usuario: UID `10001` (`azureapi`).
- Endurecimiento: root filesystem de solo lectura, `/tmp` efímero y
  `no-new-privileges:true`.
- Configuración Compose comprobada directamente mediante Docker Compose en el
  servidor; el contenedor temporal se retira al terminar la prueba.

El healthcheck remoto confirmó 50 filas y 4 suscripciones. El script
`scripts/smoke_azure_cost_api.py`, ejecutado desde la estación de desarrollo
contra `http://dockerserver:18075`, confirmó:

```json
{
  "rows": 30,
  "pages": 3,
  "pageSize": 10,
  "auth": [401, 403],
  "errors": [429, 500],
  "timeoutSeconds": 0.117,
  "emptyPage": true,
  "invalidData": true,
  "status": "ok"
}
```

El timeout se configuró en `0.1` segundos para acelerar el smoke test. Las 30
filas se recuperaron en tres páginas sin duplicados. También se verificó el
rechazo de un `$skiptoken` alterado con `400 InvalidSkipToken`.

## Participación y entrega

Trello conserva los roles rotatorios: Paris liderazgo, Victor pairing/coautoría,
Alejandro revisión y Lucia validación, pruebas y documentación. La rama se
publica en el repositorio oficial `EconomiconFinOps/tfm-economicon` mediante un
pull request independiente hacia `develop`; el enlace y el estado final se
registran en la tarjeta JUP-075.
