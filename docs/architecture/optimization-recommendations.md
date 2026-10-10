# Recomendaciones de optimización — JUP-033

[Tarjeta](https://trello.com/c/ndrittYl). Contrato de lectura v1, 10/10/2026.

`GET /billing/recommendations?start_date=2024-06-01&end_date=2024-07-01`
requiere el bearer de sesión y un `X-Tenant-Id` autorizado. Ambas fechas son
obligatorias, formato `YYYY-MM-DD`, intervalo UTC `[start_date,end_date)`, de
1 a 366 días. Devuelve 401/400/403 según los controles de sesión/tenant,
422 para periodo inválido y 409 `ambiguous_cost_source` cuando hay ingestas
completadas solapadas. Una propuesta no crea jobs, mensajes ni cambios cloud.

## Fuente y reglas

Se llama una sola vez a `fetch_billing_summary(group_by="project", tag_key=None)`
con el tenant autorizado. Reutiliza la selección de registros fechados e ingestas
completadas, los controles de [solapamiento](../adr/ADR-0010-azure-cost-source-overlap.md)
y [aislamiento](../adr/ADR-0008-tenant-isolation-boundaries.md).
No hay nueva SQL ni llamadas a proveedores o modelos.

Los proyectos agregan suscripciones del tenant; no se inventa un recurso,
suscripción ni owner para una propuesta. Se utiliza la columna `project`, con
fallback al tag normalizado `project`. El literal `Unknown` es un nombre; sólo
la ausencia y los blancos normalizados indican falta de contexto.

| Regla v1 | Condición | Resultado y límite |
| --- | --- | --- |
| `missing_project` | Grupo sin proyecto con registros, incluso con coste cero o crédito | `tagging`, `supported`: proponer contexto de aplicación con el equipo de negocio. No implica ahorro. |
| `largest_project_cost` | Mayor coste neto positivo entre proyectos identificados, por moneda | `investigation`, `investigation_candidate`: reunir utilización y requisitos. Empates por nombre, orden lexicográfico sensible a mayúsculas. No demuestra desperdicio. |

No se calculan porcentajes ni se comparan monedas. El orden de presentación es
`(currency, rule_id, project)`; no es prioridad por ahorro. Se devuelven hasta 50
candidatos con `total_candidates` y `truncated` explícitos. En ausencia de
grupos: `status=insufficient_data`, sin propuestas ni evidencia. Los grupos
nombrados con coste neto no positivo producen `available` con lista vacía: hay
datos, pero ninguna regla aplicable.

## Contrato consumible

La fuente de tipos y validación es
[`RecommendationReport`](../../apps/backend/app/schemas/recommendations.py),
publicada también en `/openapi.json` del backend. La envoltura contiene
`contract_version=1`, periodo, `source=azure_cost_records`, `cloud=azure`,
`data_environment=simulated`, estado de datos heredado, candidatos, evidencia,
supuestos, limitaciones y acciones `not_evaluated` con sus entradas ausentes.

Cada recomendación tiene `id`, `rule_id`, `rule_version`, categoría,
`qualification`, acción, motivo, scope de proyecto, coste observado, confianza,
riesgo, dificultad, referencias de evidencia y `requires_human_approval=true`.
`observed_cost.amount` es una cadena decimal exacta con dos decimales;
`observed_cost.currency` es su moneda, y `record_count` el número de registros.
Los créditos permanecen en el coste neto, sin convertirlos en ahorro.

`estimated_savings` y `currency` son **ambos null**: esta última es la moneda
del ahorro según JUP-024, distinta de la del coste observado. No se rellenan
con cero, ni se suman costes como ahorro. `confidence` describe la conclusión
de la regla, no un ahorro; `risk=low` corresponde a investigar/asignar contexto,
y `difficulty=unknown` evita inferir esfuerzo de cambios no evaluados.

La evidencia incluye `id`, `kind=cost_query`, fuente, `query` con periodo,
agrupación y tag, regla/version, scope e importe observado. Cada referencia
debe existir y coincidir con su propuesta y periodo. El ID de candidato es un
SHA-256 de tenant, consulta, regla/version, scope y moneda; el ID de evidencia
incluye también todos los grupos comparados y los indicadores de calidad.
Así un cambio de coste o competidor invalida la evidencia, conservando la
identidad del candidato que sigue seleccionado. No son IDs persistidos ni
una instantánea histórica recuperable; guardar el informe es responsabilidad
del futuro consumidor si necesita reproducir una decisión pasada.

| Consumidor | Contrato y responsabilidad pendiente |
| --- | --- |
| JUP-034 | Usar `id` y `evidence_ids` como referencias de entrada; reunir baseline, propuesta y supuestos versionados antes de estimar impacto. Mantener ahorro realizado separado. No modificar la semántica de null en v1. |
| JUP-039 | Presentar categoría, qualification, acción, evidencia y limitaciones; adaptar de forma explícita al schema JUP-024. Este informe no es por sí solo un `FinOpsResponse`. Autorización de tenant siempre fuera del modelo. |
| JUP-058 | Mostrar coste observado separado del ahorro «No calculado», distinguir investigación de acción sustentada, conservar moneda, estado parcial y aviso de truncamiento. No tratar la lista como un inventario de desperdicio. |

Las integraciones con esos consumidores no están implementadas ni probadas en
esta entrega. El frontend de demostración existente no cambia. No hay estado
de aplicación, workflow de aprobación, historial o endpoint de mutación.

## Calidad y comprobación

`missing_dimension_count` mide registros del periodo sin proyecto.
`excluded_undated_count` hereda el total de registros sin fecha de ingestas
completadas del tenant: no puede atribuirse a este periodo. `data_status=partial`
no mide frescura ni completitud de días. No se inventan timestamps de fuente
ni se acredita conexión a Azure real.

Rightsizing, scheduling, eliminación de huérfanos, optimización de tarifas e
impacto económico quedan en `not_evaluated`: faltan utilización, inventario,
dependencias, SLA, tarifas o baseline, según la acción. Ninguna cifra del
informe es ahorro potencial o realizado.

Desde `apps/backend`, ejecutar:

```text
python -m pytest tests/test_recommendations.py tests/test_recommendations_api.py -q
```

Las pruebas de API usan auth/membership reales con SQLite y un doble explícito
de la agregación. Tres pruebas Cockroach optativas usan la fixture aislada
`JUP086_COCKROACH_TEST_URL`; no apuntar esta variable a una base compartida.
La fixture exige un clúster vacío de pruebas en un puerto local no estándar y
crea/elimina sólo su base propia. [Evidencia y límites](../evidence/JUP-033-validation.md).
