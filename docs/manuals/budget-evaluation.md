# Evaluacion de presupuestos — JUP-029

[Trello](https://trello.com/c/pBICTDDh) ·
[Diseno](../../openspec/changes/jup-029-budget-thresholds/design.md)

Primer incremento: calculo bajo demanda, sin guardar el presupuesto. La moneda
y el periodo se seleccionan explicitamente; el alcance es el tenant activo.
No hay recurrencia, bloqueo del gasto, forecast ni envio de alertas.

## Peticion

`POST /billing/budget/evaluate`, con bearer valido y `X-Tenant-Id` autorizado.

```json
{
  "amount": "1000.00",
  "currency": "EUR",
  "start_date": "2024-06-01",
  "end_date": "2024-07-01",
  "thresholds_percent": ["80.00", "100.00"]
}
```

Inicio incluido, fin excluido, UTC. No se aceptan timestamps. Importe positivo
con exactamente dos decimales (hasta 26 digitos enteros), moneda de tres letras
ASCII mayusculas. Entre uno y diez umbrales, positivos, crecientes sin duplicados,
hasta 1000.00%; si se omiten, 80.00 y 100.00. Inputs monetarios y porcentajes
son strings; campos adicionales se rechazan con 422.

## Como interpretar el resultado

Sobre consumo observado S y presupuesto B:

| Campo | Calculo | Ejemplo S=850.00, B=1000.00 |
| --- | --- | --- |
| observed_spend | Total v2 de la moneda seleccionada | 850.00 |
| consumption_percent | 100*S/B | 85.00 |
| remaining_amount | B-S | 150.00 |
| deviation_amount | S-B | -150.00 |
| deviation_percent | 100*(S-B)/B | -15.00 |
| reached_thresholds_percent | Todos los umbrales alcanzados | ["80.00"] |
| highest_reached_threshold_percent | Ultimo alcanzado | 80.00 |

La desviacion positiva significa exceso respecto al presupuesto completo. No
mide el ritmo del gasto durante el mes. Los creditos reducen el consumo y pueden
producir consumo negativo. Los umbrales se alcanzan por igualdad o exceso; se
comparan antes de redondear porcentajes. Por ejemplo, 799.99/1000.00 muestra
80.00% pero todavia no alcanza el umbral de 80.00%.

El calculo reutiliza el total monetario v2, ya redondeado a centimos; no suma
los grupos redondeados ni convierte divisas. Los porcentajes se redondean
HALF_UP a dos decimales, con aritmetica Decimal.

- `evaluated`: existe consumo observado para la moneda y data_status=available.
  No certifica cobertura completa de todas las facturas del periodo.
- `provisional`: existe total, pero billing informa datos parciales. Se conservan
  `missing_dimension_count` y `excluded_undated_count` para explicar omisiones.
- `unavailable`: no hay total observado para esa moneda. Importes, porcentajes
  y resultados de umbrales son null, no cero. `record_count` indica filas observadas.

Un total observado de 0.00 si se evalua. Otras monedas nunca se suman a EUR.
`409 / ambiguous_cost_source` impide mostrar importes de fuentes solapadas;
los fallos de autenticacion, permisos y base de datos no se convierten en cero.

## Pruebas

Desde `apps/backend`: `python -m pytest tests/test_budget_evaluation.py -q`.
La prueba con Cockroach real usa la fixture aislada existente de JUP-086; ver
[evidencia](../evidence/JUP-029-validation.md) para comando y resultado.

La persistencia, edicion de presupuestos, UI, agente y notificaciones necesitan
su siguiente alcance y revision; no se presentan como terminados por esta API.
