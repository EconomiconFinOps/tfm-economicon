# JUP-037 — Consultas de ownership

Tarjeta: https://trello.com/c/n4Aplko2

El chat admite una selección estructurada de coste por proyecto, aplicación,
equipo, centro de coste o etiqueta. La respuesta es determinista sobre ingestas
completadas; el texto de la pregunta no se interpreta como filtro ni autorización.

## Petición

`POST /assistant/conversations/{id}/messages`, con Bearer y `X-Tenant-Id`:

```json
{
  "content": "Gasto de la aplicación Portal en junio",
  "ownership_query": {
    "group_by": "application",
    "value": "Portal",
    "currency": "EUR",
    "start_date": "2024-06-01",
    "end_date": "2024-07-01"
  }
}
```

`group_by` admite `project`, `application`, `owner`, `cost_center`, `tag`.
`tag_key` es obligatorio solo para `tag`. Se reutilizan las claves canónicas de
billing y normalización: `CostCenter`/`costcenter`/`cost_centre` → `cost_center`,
`env` → `environment`, `org` → `organization`. **No** se transforma `project` en
`application`, ni `organization` o `ProjectOwner` en `owner`.

`value` es opcional, exacto y sensible a mayúsculas, con trim del argumento.
Los valores observados, incluidos `Unknown`, no implican catálogo aprobado.
`currency` admite tres letras ASCII, se convierte a mayúsculas y no convierte
importes. No se combinan múltiples etiquetas. `value`/`tag_key`: 1–256 caracteres
sin controles. Campos adicionales, tenant o SQL en la selección se rechazan.

Las fechas son ambas ISO `YYYY-MM-DD` o ambas omitidas (mes actual UTC). El
intervalo es `[inicio, fin)`. La UI muestra el periodo resuelto al enviar. Scope:
tenant completo autorizado, con conversación perteneciente al usuario actual.

## Semántica y evidencia

Proyecto usa la columna promovida con fallback a `tags.project`. Las demás
dimensiones leen exclusivamente su tag canónico. La agregación SQL billing v2
suma valores exactos antes de redondear, conserva signos y separa monedas.
La selección de valor usa el grupo agregado de ese valor; el total contextual
proviene de SQL, nunca de sumar grupos ya redondeados.

El mensaje guarda `metadata.cost_evidence`: `schema_version=1.0`,
`adapter_version=ownership-1.0`, `id=cost:<sha256>`, selección resuelta, summary
billing v2, `selected_groups`, `selected_totals`, `missing_groups`, estado/motivo,
limitaciones, fecha de consulta y procedencia. El hash liga tenant (internamente),
selección, versiones y resultado; no incluye la hora de consulta.
`provenance` conserva ingestas completadas, primer/último día observado y número
de días distintos en la misma transacción serializable que las cifras.
IDs financieros no se presentan como citas de chunks documentales.

| Estado | Interpretación |
| --- | --- |
| `ok` | Selección observada sin carencias conocidas en su moneda |
| `partial` | Hay coste sin dimensión en esas monedas o registros sin fecha |
| `insufficient_data` / `dimension_unobserved` | Todo el coste contextual carece de la dimensión; no es gasto cero |
| `no_data` / `empty_period` | No hay filas fechadas del periodo |
| `no_data` / `currency_not_found` | La moneda no aparece en el periodo |
| `no_data` / `value_not_found` | No existe ese valor exacto; contexto y coste sin etiqueta se conservan |

Un grupo de coste neto `0.00` sigue siendo dato; ajustes negativos conservan su
signo. Coste sin dimensión se conserva aun al seleccionar otro valor.
`missing_dimension_count` es del tenant/periodo completo (todas las monedas);
`excluded_undated_count` cuenta filas del tenant sin fecha, no atribuibles a ese
periodo. La disponibilidad de la dimensión en la fuente, actualidad y cobertura
completa se declaran desconocidas. `queried_at` no equivale a `data_as_of`.

## Errores y límites

401/403 para sesión/membresía, 404 para conversación ajena, 422 para selección
inválida; 409 `ambiguous_cost_source` si hay ingestas solapadas por suscripción/día.
Se calcula antes de guardar mensajes y sin invocar modelo, embeddings ni vector.
Más de 1000 grupos o evidencia superior a 256 KiB: 422
`ownership_result_too_large`, sin truncar silenciosamente ni guardar respuesta.
Este límite de salida no limita el trabajo previo de agregación SQL.
El texto muestra hasta 20 grupos identificados y lo avisa; la evidencia conserva
el desglose completo aceptado. La consulta debe usar un periodo menor si excede
el límite; un filtro de valor se aplica después de agregar y no lo elimina.

## Dependencias y disponibilidad

Se reutilizan los contratos de JUP-036 (selección explícita, periodo UTC,
`cost_evidence` 1.0 y procedencia) sin incorporar su PR #69 todavía draft.
`ownership_query` es aditivo y separado de su `cost_query`. Al integrar ambos se
deberá rechazar su envío simultáneo y probar la convivencia. JUP-037 no declara
probada esa combinación ni implementa consultas de cuenta/servicio/suscripción.

La taxonomía y los catálogos pertenecen a JUP-015. Se mantienen los aliases ya
implementados en normalización; no se inventan valores válidos ni mapeos nuevos.
El mapping de Azure simulado actual admite CostCenter, Project, env y org;
no materializa application/owner mediante esos groupings. Los escenarios que
contienen application/owner utilizan datos sintéticos explícitos en una base
aislada. No acreditan disponibilidad en una ingestión desplegada. Sin etiquetas,
el comportamiento funcional es informar datos insuficientes con su coste.

No incluye interpretación libre general, showback/reparto contable, métricas de
cumplimiento de tags, modificación de ingesta o del dataset público, despliegue
ni proveedor de IA. Pairing, revisión y validación humanas se registran aparte.
