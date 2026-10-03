# JUP-036 — Evidencia de implementación

Verificado el 2026-10-03. Base: develop `6410950`.
Trello: https://trello.com/c/LxaVVLcH

## Pruebas ejecutadas

- 48 pruebas seleccionadas backend: `python -m pytest tests/test_azure_cost_questions.py
  tests/test_billing_summary.py tests/test_assistant_service.py tests/test_domain_metrics.py -q`.
  Incluye SQL real sobre CockroachDB v24.1.2 aislado, todas pasan.
- Suite frontend: 439 pruebas en 47 archivos, todas pasan con
  `corepack pnpm --filter @finops/frontend test -- --maxWorkers=2 --minWorkers=1`.
- Suite processor: 448 pasan, 57 se omiten por servicios/opt-ins ausentes;
  ningún cambio en processor.
- `corepack pnpm --filter @finops/frontend lint` y `typecheck`: pasan.
- `corepack pnpm -r build`: backend, processor, frontend y configuración compartida pasan.
- OpenSpec: 41/41; trazabilidad JUP y limpieza pasan; diff sin errores.
- Políticas PR: 57 pruebas; CI: 10; gobernanza: 13, todas pasan.

## Cobertura funcional propia

| Caso | Evidencia |
| --- | --- |
| Servicio, suscripción y cuenta | `test_real_cost_sql`: respuesta del chat con importes esperados independientes y comparación con llamada directa |
| Precisión, créditos, cero, monedas | 9007199254740993.01 USD sin conversión float, crédito -1.00 EUR tras agregación, cero distinto de ausencia |
| Sin filas / valores ajenos / SQL injection | no_data, lista vacía, sin datos del tenant-b; filtros parametrizados |
| Fecha inicial y final | Fixtures con filas anteriores, finales y solapamientos fuera del periodo; resultados esperados excluyen fin |
| Fuentes solapadas | 409 antes de guardar mensajes, incluso cuando solo una fuente tiene el servicio pedido |
| Autorización | 403/404 sin consulta de coste ni escritura para tenant/conversación ajenos |
| Entrada inválida | Campos extra, periodos invertidos/incompletos, fecha inválida, controles y límites rechazados |
| Procedencia y recarga | IDs de ingesta/días esperados; evidencia persistida al GET de conversación; sin llamadas RAG |
| Periodo por defecto | Diciembre UTC resuelve 01/12 a 01/01 del año siguiente |
| Formulario | Selección account/valor/suscripción/fechas enviada con bearer/tenant; fecha incompleta o invertida deshabilita envío |
| Regresión documental | Tests assistant y conversaciones conservan envío y citas existentes |

## Incidencias resueltas y límites

La primera ejecución SQL falló por parámetros opcionales sin tipo inferible;
se corrigió con CAST AS STRING. El primer pase amplio de backend encontró
metadata=None en el doble del test de métricas; se corrigió a diccionario vacío,
y la repetición seleccionada pasó. La primera suite frontend con concurrencia
predeterminada falló por tiempos/esperas; el pase completo con dos workers pasa.

`corepack pnpm build` vía Turbo encontró el pnpm alternativo 11 del runtime e
intentó reinstalar node_modules sin TTY. `corepack pnpm -r build` usa el pnpm 9
fijado y ejecuta los mismos builds satisfactoriamente. No se modifican lockfile
ni configuración del repositorio para corregir el entorno local.
Vite advierte de un chunk mayor de 500 kB; build completado.

Instancia SQL efímera dedicada, loopback remoto 56436 y túnel SSH. La fixture
crea y elimina sus propias bases. No se prueba Azure real, parsing NL libre,
proveedor LLM, ensayo visual manual ni el stack completo. Esta evidencia es del
implementador; no acredita pairing real, revisión Lucia ni validación Paris.
