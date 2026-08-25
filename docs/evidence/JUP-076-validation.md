# JUP-076 — Evidencia de validación

Fecha: 2026-08-25

Rama: `feat/JUP-076-azure-cost-ingestion-client`

## Resultado

- Cliente configurable añadido a `apps/processor/app/clients/azure_cost.py`.
- Bearer almacenado como `SecretStr`.
- Paginación completa con validación de origen, ruta, suscripción y versión de
  cada `nextLink`.
- Redirecciones HTTP deshabilitadas antes de reenviar credenciales.
- Reintentos acotados de `429` y `500`, con `Retry-After` y backoff.
- Timeout, límite de páginas y detección de ciclos.
- Validación estricta de `columns`, `rows`, tipos, costes finitos y columnas
  obligatorias.
- Configuración rechaza URLs inseguras, bearer vacío/inyección de cabeceras,
  intervalos inválidos y esperas no finitas.
- Eventos JSON sin credenciales ni contenido del dataset.

## Pruebas locales

Se reutilizó el `.venv` ignorado por Git dentro de `apps/processor`, con sus
dependencias declaradas, sin incorporar entornos generados al repositorio.

| Comprobación | Resultado |
| --- | --- |
| Suite completa de `apps/processor` | 66 pruebas superadas |
| Pruebas específicas del cliente | 63 pruebas superadas |
| Suite API Azure JUP-074/JUP-075 | 58 pruebas superadas |
| Dataset público y contrato compartido | 21 pruebas superadas |
| `corepack pnpm openspec:validate` | 11 cambios/especificaciones válidos |
| `corepack pnpm jup:check -- --change jup-076-azure-cost-ingestion-client` | Trazabilidad Trello/OpenSpec correcta |
| `corepack pnpm build` y `corepack pnpm test` | Workspace completo correcto |

La suite cubre bearer y timeout configurables, paginación completa,
`Retry-After` válido/no finito, backoff exponencial, agotamiento de reintentos,
`401` sin retry, página vacía, respuesta vacía válida, JSON/columnas/filas/tipos
inválidos, cambio de columnas, `nextLink` externo o manipulado, redirecciones
HTTP, ciclos, límite de páginas y ausencia de secretos en configuración/logs.

## Prueba externa contra JUP-075

Comando ejecutado desde la raíz del worktree:

```powershell
python scripts/smoke_azure_cost_ingestion.py --base-url http://dockerserver:18076
```

Resultado:

```json
{
  "rows": 30,
  "pages": 3,
  "auth401": true,
  "auth403": true,
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
retardo configurado de `0.5` segundos. La API se ejecutó en `dockerserver` como
UID `10001`, con root filesystem de solo lectura y `no-new-privileges`.

La imagen `economicon-processor:jup-076` también se construyó con un contexto
Docker aproximado de `227.8 kB`, sin incluir `.venv`, tokens locales ni tests.
Un contenedor processor independiente consultó la API a través de una red
Docker aislada utilizando `http://azure-cost-api:8002` y obtuvo las mismas
30 filas en tres páginas mediante el cliente incluido en la imagen.

## Participación y entrega

Trello conserva los roles rotatorios: Victor liderazgo, Alejandro
pairing/coautoría, Lucia revisión y Paris validación, pruebas y documentación.
La rama se publica en `EconomiconFinOps/tfm-economicon` mediante un pull request
independiente hacia `develop`; su estado y evidencias se enlazan en JUP-076.
