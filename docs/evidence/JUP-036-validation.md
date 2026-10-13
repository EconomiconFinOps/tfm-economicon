# JUP-036 — Evidencia de implementación

Verificación: 2026-10-13. Base integrada: `bfaf39839718` (develop).
Trello: https://trello.com/c/LxaVVLcH · PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/69

## Incremento actual

Resueltos los conflictos con la base actual sin sustituir consultas de propiedad,
citas ni traducciones. La selección Azure vive en `MessageComposer`, con el mismo
ciclo de vida por cliente/conversación. El backend rechaza dos selecciones simultáneas
antes de leer costes o persistir; `CostEvidence` reconoce el adaptador `azure-cost-1.0`
y presenta su procedencia con el alcance de la selección, manteniendo ownership.

| Comprobación | Evidencia actual |
| --- | --- |
| SQL real y regresiones | 178 pruebas pasan, sin omisiones: costes, billing, presupuestos, ownership y cobertura de etiquetas. CockroachDB v24.1.2 temporal, sin datos ajenos. |
| JUP-036 final con SQL | 32 pruebas pasan, sin omisiones. GET posterior conserva evidencia JSONB, adaptador y todos los grupos; otro cliente obtiene 404. Incluye consulta documental posterior y proveedor/vector indisponibles. |
| Frontend completo | 882 pruebas pasan en 66 archivos, con dos workers. Incluye envío exacto por cuenta, fechas inválidas y visor Azure; suites ownership, citas y cambio de cliente conservadas. |
| TypeScript y lint | Scripts oficiales frontend completos pasan (tres tsconfig y eslint src tests). |
| Build | `corepack pnpm -r build` pasa. Dependencias sincronizadas con `corepack pnpm install --frozen-lockfile`; lockfile sin cambios propios. Advertencia existente de chunk >500 kB. |
| Políticas | 82 pruebas PR/CI/gobernanza pasan; higiene y trazabilidad pasan. |
| Backend completo | Linux: **1280 pasan, 125 omisiones** por servicios/opt-ins ausentes, sin fallos. Runtime temporal basado en la imagen backend de develop bfaf3983, copia exacta del candidato y pytest/httpx instalados en /tmp. Windows: 1135 pasan, 125 omisiones y 145 fallos concentrados en cuatro suites de salud que bloquean socket.connect e impiden crear el socketpair de asyncio. No se modifica esa protección. |

Comandos SQL: `python -m pytest tests/test_azure_cost_questions.py tests/test_billing_summary.py tests/test_budget_evaluation.py tests/test_ownership_questions.py tests/test_tag_coverage.py -q --tb=short -p no:cacheprovider`, seguido del archivo JUP-036 completo con la regresión final de recarga.
Variable opt-in `JUP086_COCKROACH_TEST_URL` hacia loopback:56636/defaultdb; organización de la instancia propia `processor-integration-tests`. Las fixtures crean y eliminan sus bases.

Comandos frontend: `node node_modules/vitest/vitest.mjs run --maxWorkers=2`, `corepack pnpm --filter @finops/frontend typecheck`, `corepack pnpm --filter @finops/frontend lint`.

## Límites y aceptación pendiente

No se acreditan Azure real, interpretación libre, llamadas a modelos, recorrido
conjunto con JUP-035/PR121, ni nuevas intervenciones humanas. El alcance explícito
está confirmado por la tarjeta consultada el 13/10. PR121 continúa abierta; la
combinación generativa necesita su propia validación.

La evidencia del implementador no sustituye el contraste de liderazgo Victor,
el pairing real ni las reviews separadas de Lucia y Paris. No se da por cerrada
la tarjeta ni se atribuyen aprobaciones inexistentes. Los resultados inferiores
son históricos y no se suman ni se presentan como pruebas del candidato actual.

---

# Evidencia histórica — 2026-10-03

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
