# Impacto potencial de recomendaciones — JUP-034

[Trello](https://trello.com/c/Hdwz4SXw). Contrato `1.0`, 2026-10-10.

`POST /recommendations/impact/evaluate` requiere Bearer y `X-Tenant-Id` con
pertenencia comprobada por el backend. Es una calculadora sin persistencia:
acepta escenarios del solicitante, no consulta facturas ni ejecuta cambios cloud.
El resultado declara siempre `basis=caller_supplied_scenario`.

## Contrato para JUP-033

El productor de recomendaciones aporta `recommendation_id` estable,
`cost_scope_ids`, moneda, evidencias, supuestos y los dos costes mensuales.
Los IDs de alcance son unidades **atómicas de coste** cualificadas por
suscripción/recurso; toda alternativa que reduzca ese mismo gasto debe incluir
la misma clave. Una recomendación de varios recursos enumera todas sus claves.
No usar el ID de la recomendación como alcance ni mezclar claves de suscripción
global con claves de recursos individuales. Se normaliza mayúsculas/minúsculas,
espacio exterior y barra final; no se interpreta una jerarquía de rutas.

JUP-033 debe mapear su identificador estable a `recommendation_id`, no reconstruirlo
desde el texto de la acción. Sin baseline y objetivo verificables, enviar ambos
como `null`: no inferir importes a partir de categorías ni de texto de un LLM.
La referencia histórica `processor.Recommendation.estimated_savings` no tiene
periodo y por ello **no se convierte** automáticamente a mensual/anual.
Este endpoint no resuelve los IDs contra un catálogo de recomendaciones y no
afirma verificar evidencias del solicitante. La conexión al productor JUP-033
requiere adaptar su contrato definitivo y probarla; no está acreditada aquí.

Contraste local 2026-10-10 con el candidato simultáneo de JUP-033
(`contract_version=1`, todavía sin integrar): su `recommendations[].id` y
`evidence_ids` caben sin transformación en este contrato. Su
`observed_cost.amount` es coste neto de un proyecto para `period`, **no ahorro**,
y no aporta coste objetivo ni recursos atómicos. No se copia automáticamente a
baseline: el periodo puede ser parcial, incluir créditos o agregar recursos.
El consumidor debe reunir el escenario completo, las claves de coste y evidencia
de un objetivo antes de calcular. Si faltan, conserva `insufficient_data`; no
deduce un porcentaje de ahorro para tagging/investigation.

## Semántica

- `baseline_month` es el primer día de un mes calendario completo. Los importes
  ya representan ese mes; no se extrapolan días parciales silenciosamente.
- Baseline y objetivo deben compartir alcance, mes, uso y criterio de precio.
  Se aceptan cadenas decimales no negativas, hasta 18 enteros y 6 decimales.
- Mensual = `max(baseline_monthly_cost - target_monthly_cost, 0)`.
  Anual = mensual sin redondear × 12: adopción inmediata completa y precios/uso
  estables. Es potencial bruto; no incluye coste de implantación, estacionalidad,
  riesgo, demora ni probabilidad de adopción. No es una previsión garantizada.
- `insufficient_data` conserva ambos potenciales `null`; `no_savings` significa
  cálculo disponible cuyo ahorro no es positivo, incluido un objetivo más caro.
  El escenario original permanece visible para evaluar ese incremento.
- `observed_savings` siempre es `null`, también en los totales. No hay medición
  posterior a la acción ni ahorro realizado. El body rechaza ese campo.
- `totals` separa monedas, sin conversión. Ordena escenarios calculables por
  ahorro mensual descendente y, en empate, ID ascendente. Incluye sólo escenarios
  cuyas claves no intersectan con otros ya elegidos; `excluded_by` identifica
  las alternativas elegidas. Los importes individuales excluidos siguen visibles.
  Es una cartera factible bajo los alcances declarados, no una optimización global.
- Una misma clave de coste con monedas diferentes es error 422. IDs de
  recomendación duplicados también. Alcances incompletos o falsamente distintos
  pueden ocultar solapes: su productor debe garantizar equivalencia y completitud.
- Totales sin estimaciones quedan `null`; una entrada vacía devuelve listas vacías.
  Los IDs sin estimar aparecen en cada total, por lo que se distingue un subtotal
  de una cobertura completa. Se calcula con Decimal antes de redondear a dos
  decimales (`ROUND_HALF_UP`); puede haber diferencias de céntimos al sumar la
  presentación individual o multiplicar el mensual mostrado por 12.

## Ejemplo reproducible

Enviar [recommendation-impact-example.json](recommendation-impact-example.json)
con una sesión del entorno autorizado:

```sh
curl -X POST "$BACKEND_URL/recommendations/impact/evaluate" \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H "X-Tenant-Id: $TENANT_ID" \
  -H 'Content-Type: application/json' \
  --data-binary @docs/contracts/recommendation-impact-example.json
```

Datos sintéticos: `rightsize-vm` ahorra 40 EUR/mes, 480 EUR/año; `schedule-vm`
ahorra 30/360 sobre el mismo recurso y queda excluida del total. `cleanup-disk`
añade 15/180. Total factible **55 EUR/mes y 660 EUR/año**; `investigate-storage`
sin baseline permanece desconocida. Estos números no son beneficios observados.

La calculadora, sus límites y autorización se prueban sin cloud, gateway ni LLM:

```sh
cd apps/backend
python -m pytest tests/test_recommendation_impact.py -q
```

El panel de recomendaciones existente sigue siendo demostración; esta entrega
no lo conecta, no cambia el contrato del asistente y no altera el KPI
`billing.savings_identified`. La evaluación de negocio JUP-068 debe consumir una
selección única y mantener la distinción potencial/observado; no sumar otra vez
las estimaciones individuales junto al total de este endpoint.
