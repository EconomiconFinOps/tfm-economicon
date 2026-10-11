# Review JUP-030 — Detección de anomalías de coste

Fecha: 2026-10-11. Rama `feat/JUP-030-anomaly-evaluator`, desde `develop` en `4406477`. Trello: https://trello.com/c/ScxJi1TO

## Resumen

El backend ofrece `POST /billing/anomalies/evaluate`, autenticado y por tenant, que evalúa un umbral absoluto y una subida frente al periodo anterior de igual duración sobre billing v2, con aritmética decimal exacta, estados honestos de calidad de datos e identificadores de alerta y de evidencia estables, para que JUP-038 los consuma. Es la contribución de Alejandro Aguado del 10/10 (PR #91, cerrado sin integrar), traída con sus dos commits y su autoría sobre `develop`; en esta pasada se revisa de forma independiente, se cierra un hueco de test y se documentan los hallazgos menores. No incluye el panel `/anomalies`, persistencia, notificaciones ni la integración con JUP-038.

## Decisiones

- Se reutiliza el trabajo de Alejandro en lugar de reescribirlo: el código es sólido y sigue el patrón del evaluador de presupuestos (JUP-029). No se acredita participación de nadie ni revisión humana.
- Excepción temporal del 2026-10-11: sin revisión ni validación humanas de otras personas en GitHub. Se sustituyen por la revisión adversarial independiente de este archivo, la validación en `docs/evidence/JUP-030-validation.md` y la aprobación de Lucia.
- ADR: no aplicable. No introduce una decisión de arquitectura duradera ni transversal: es una ruta sin estado y sin migraciones, con reglas configurables sobre billing v2.

## Validación

Comandos ejecutados el 2026-10-11 en Windows con el entorno virtual del backend, primero sin CockroachDB y despues con Docker (ver la tabla siguiente):

| Comando | Resultado |
| --- | --- |
| `python -m pytest tests/test_anomaly_evaluation.py tests/test_budget_evaluation.py tests/test_billing_summary.py tests/test_tag_coverage.py` (apps/backend) | 149 aprobadas y 32 omitidas (las que necesitan CockroachDB real) |
| `corepack pnpm openspec:validate` | 62 de 62 correctos |
| `corepack pnpm jup:check -- --change jup-030-cost-anomalies` | correcto |
| `corepack pnpm jup:cleanup:check` | correcto |

| Mismos tests con CockroachDB real (`cockroachdb/cockroach:v24.1.11`, nodo desechable) | 181 aprobadas, 0 omitidas, 0 errores |
| Stack Docker aislado, ingesta del dataset publico y 13 llamadas HTTP al endpoint | Importes y alertas iguales a los calculados con SQL independiente; errores 401, 403 y 422 correctos; aislamiento entre tenants |

Detalle y limites en `docs/evidence/JUP-030-validation.md` (seccion "Validacion con Docker y CockroachDB real"). Para la ejecucion con base real se subio solo en local el plazo de migraciones de 60 a 400 s y se revirtio.

## Adversarial Review (pass 1)

Veredicto: **accept**. Sin hallazgos BLOCKING ni HIGH; 2 MEDIUM y 3 LOW. El revisor ejecutó 84 casos y ataques por la capa real.

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | MEDIUM | `resource_group` se normaliza con `lower()` de Python y la agrupación SQL con el de CockroachDB; con alfabetos exóticos pueden diferir (colisión que da 500, o grupo sin emparejar). Reproducido con `ΑΣ` y `ας`; **confirmado con CockroachDB real** (`lower('ΑΣ')` = `ασ`, `lower('ας')` = `ας`) | Aceptado por Lucia, `RF-030-001` |
| ADV-2 | MEDIUM | La respuesta no tiene límite de grupos: con 50.000 grupos son 41,7 MB y 3,9 s de CPU. Defecto heredado de `GET /billing/summary` | Aceptado por Lucia, `RF-030-002` |
| ADV-3 | MEDIUM | Ningún test comprobaba que un cambio solo en la calidad del periodo base cambia `evidence_id` | **Corregido**: test nuevo; la mutación que la quita del hash lo hace fallar |
| ADV-4 | LOW | Sin prueba con CockroachDB real de `resource_group` con distinta capitalización entre periodos | Aceptado por Lucia, `RF-030-003` |
| ADV-5 | LOW | Las dos lecturas (actual y base) son transacciones separadas | Aceptado por Lucia (ya lo acepta y documenta la spec), `RF-030-004` |

Ataques que resistieron: límites exactos de las tres reglas (`>=`), importes de más de 2**53 y hasta 40 dígitos sin perder céntimos, línea base ausente, cero, negativa o vacía, combinaciones con monedas y suscripciones distintas, errores por la ruta real (500 genérico sin filtrar mensajes, 409 de fuente ambigua, 401, 403 y 422 sin leer datos), aislamiento entre tenants, estabilidad de `id` y `evidence_id` y el ejemplo reproducible de `docs/api/cost-anomalies.md`.

## Barrido de patrón

La normalización de nombres usa tres mecanismos distintos (`lower()` en el servicio, `lower()` en SQL y `casefold` en el procesador): solo el primero y el segundo afectan a esta ruta y son el origen de `RF-030-001`. La ausencia de tope de grupos está también en `GET /billing/summary` y es el origen de `RF-030-002`. El patrón del hueco de ADV-3 no aparece en otros evaluadores.

## Riesgos

- **Probados**: límites, importes, estados de línea base, errores por la capa real, aislamiento entre tenants y estabilidad de los identificadores.
- **Aceptados por Lucia (2026-10-11)**: `RF-030-001` a `RF-030-004`.
- **No comprobados**: CPU y memoria con una base real de gran tamaño, el caso `RG`/`rg` entre periodos con base real (`RF-030-003`), el límite de grupos con volumen real (`RF-030-002`) y la integración con JUP-038 y con el panel `/anomalies`.

## Hallazgos registrados

`RF-030-001` a `RF-030-004` en `openspec/findings/backlog.md`.

## Pendiente

- La sección `## Human Approval` se rellena solo con la aprobación explícita de Lucia tras esta revisión.
- El panel `/anomalies` sigue con datos de demostración y su conexión es un cambio aparte.
