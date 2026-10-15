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


## Resolución de conflictos con JUP-119 — 2026-10-14

Base nueva: develop `c30a7d0f` (PR127). El único conflicto textual en
`fetch_billing_summary` combina el tope `reference_date.visible_end(end_date)`
con los filtros parametrizados `selected_subscription` y `selected_value` de JUP-036.
La selección de cuenta y la procedencia del subconjunto se conservan.

La fusión automática introduce la fecha de referencia en el formulario. Se adapta
`AzureCostQuestionService` al mismo reloj para su mes por defecto y se registra
`reference_date` en el hash/evidencia y en la respuesta. Así, omitir fechas con
una demo de diciembre consulta diciembre y conserva el corte de filas visible.

Nuevas regresiones: las tres dimensiones Azure devuelven cinco registros/50.00EUR
con referencia05/10 aunque la base contenga días posteriores; se verifica la recarga
del mismo JSONB. El formulario se prueba en ambos modos con fecha simulada y fallo
de carga de referencia. Typecheck, lint, build, higiene y OpenSpec70/70 pasan.
Resultados SQL: **195 pasan, cero omisiones** en costes Azure, fecha de referencia, billing, presupuestos, ownership y etiquetas. Publicación/CI pendientes en este corte. No se repite ni atribuye
al candidato nuevo la suite completa registrada para c1d4ef51 el13/10.


## Correcciones de la revisión de Lucía — 15/10/2026

[Revision JUP-036, cambios pedidos](https://github.com/EconomiconFinOps/tfm-economicon/pull/69#pullrequestreview-5528549577), sobre47a8df7a.
Se integra develop cf821570, que incorpora JUP-038 y la entrega A JUP-122.
La validación de Paris5519177796 corresponde al head anterior y debe revalidarse.

| Petición | Corrección y regresión |
| --- | --- |
| Suscripciones sin distinguir mayúsculas | `AzureCostSelection` aplica casefold a subscription_id y a value para group_by=subscription, conservando cuenta/servicio exactos. Casos SUB-A/sUb-A y SUB-B/sUb-B en SQL real. |
| Etiquetas que suplantan líneas de respuesta | Se reutiliza ownership_questions.display_label para selección y grupos. Regresiones con salto de línea y U+2028 verifican la presentación escapada y el dato original en metadata. |
| Alcance del conflicto según selección | value con group_by=subscription delimita selected_subscription cuando no se indica éste. Regresión con solapamiento ajeno: sub-a responde igual por ambos campos y sub-b mantiene409. |
| Fechas estrictas | Mismo patrón YYYY-MM-DD de ownership; se rechazan timestamp en texto y ambas formas con hora además del entero. |

Compatibilidad de base: la ruta Azure utiliza assert_conversation_idle,
prepare_message/append_pair y la respuesta de chat_history de JUP-122; los tres
modos estructurados son excluyentes. Las regresiones de bloqueo y exclusión
Azure/anomalía pasan. Se conserva la rama de explicación JUP-038 y su formulario.

Sugerencias no bloqueantes: se corrige la ayuda del formulario para hablar del mes
de referencia y ocultar la explicación de etiquetas de ownership en modo Azure;
se aclara que los IDs de suscripción no distinguen mayúsculas. El límite de más
1000 grupos, traducción general de errores JSON y captura única del reloj siguen
sin ampliarse en esta corrección. No se atribuye su aceptación a Lucía.

Frontend focal final: **63/63**, seis archivos; prueba de ocupación y exclusión Azure/anomalía: **2/2**.
SQL amplio: 287 pasan y dos fallos de pruebas, no defectos del producto: la nueva
fixture de solapamiento usó un día distinto al de la fuente original y se corrige
a15/06; el recorrido JUP-038 esperaba exactamente dos claves de metadata aunque
JUP-122 ya añade generation. Ahora también verifica el vínculo a la pregunta.
Repetición final de Azure completo y recorrido JUP-038: **46/46 PASS**, sin omisiones,
con CockroachDB real. Los recuentos se solapan y no se suman; no quedan fallos
conocidos de los casos ejecutados. Log: `tmp/jup036-lucia-sql-final.log` del workspace.
Build y tipos pasan; lint sin errores, con advertencia ya presente en
ChatPresentation.tsx:101. OpenSpec73/73, políticas84/84, higiene y trazabilidad PASS.
Los primeros fallos de tipos/lint se debieron a dependencias anteriores al merge;
resueltos con pnpm install --frozen-lockfile sin modificar el lockfile integrado.
La prueba de periodo inventado se acota al rótulo de fecha, para permitir la ayuda
general que menciona el mes de referencia sin mostrar fechas cuando la API falla.
