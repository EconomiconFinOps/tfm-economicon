# Evaluacion de anomalias de coste

JUP-030 — [Trello](https://trello.com/c/ScxJi1TO). Contrato HTTP version 1.
Fuentes ejecutables: [schema](../../apps/backend/app/schemas/anomalies.py),
[servicio](../../apps/backend/app/services/anomalies.py) y
[ruta](../../apps/backend/app/api/routes/billing.py).

`POST /billing/anomalies/evaluate` devuelve candidatos de investigacion por
umbral de coste observado o aumento frente al periodo anterior. Es una
evaluacion bajo demanda sobre costes normalizados; no persiste alertas, envia
notificaciones ni diagnostica su causa. El panel JUP-057 sigue mostrando su
fixture de demostracion; no consume este endpoint.

## Peticion y acceso

Requiere el bearer de la sesion y `X-Tenant-Id` con pertenencia comprobada por
`get_active_tenant`, igual que `/billing/summary`. El cuerpo no acepta tenant,
usuario, costes suministrados por el cliente ni campos adicionales.

```http
POST /billing/anomalies/evaluate
Authorization: Bearer <token-de-la-sesion>
X-Tenant-Id: <tenant-autorizado>
Content-Type: application/json

{
  "start_date": "2026-04-08",
  "end_date": "2026-04-15",
  "group_by": "service",
  "currency": "EUR",
  "absolute_threshold": "150.00",
  "deviation_threshold_percent": "50.00",
  "min_absolute_increase": "1.00"
}
```

| Campo | Contrato |
| --- | --- |
| `start_date`, `end_date` | Fechas `YYYY-MM-DD`; intervalo UTC `[inicio, fin)` de 1 a 366 dias. `end_date` no puede superar el dia UTC actual, de modo que todos los dias solicitados estan cerrados. |
| `group_by` | `subscription`, `resource_group`, `service` o `project`; default `service`. |
| `currency` | Tres letras ASCII mayusculas; sin comprobacion contra un registro ISO ni conversion de moneda. |
| `absolute_threshold` | Opcional/null; importe positivo como string canonico de dos decimales y hasta 26 digitos enteros. Umbral sobre el coste del grupo durante todo el periodo. |
| `deviation_threshold_percent` | Opcional/null; porcentaje positivo como string canonico de dos decimales, hasta `1000.00`. |
| `min_absolute_increase` | Importe positivo con el formato del umbral absoluto; default `0.01`. Solo condiciona la regla de desviacion. |

Al menos una de las dos reglas debe estar habilitada. No se aceptan numeros
JSON en lugar de strings monetarios, exponentes, signos positivos, ceros
iniciales ni formatos locales. Una definicion invalida devuelve 422 antes de
consultar costes. Si se habilita desviacion, el periodo anterior de igual
duracion debe poder representarse como fecha; se calcula automaticamente y
termina en `start_date`. Si solo se habilita el umbral absoluto, no se consulta
el periodo anterior y sus campos son null.

## Reglas, agrupacion y precision

Para cada grupo observado de la moneda solicitada, con coste actual `C`,
coste anterior `B`, umbral absoluto `T`, porcentaje `P` e incremento minimo `M`:

```text
absolute_threshold: C >= T
period_increase: B > 0 AND C - B >= M AND (C - B) * 100 >= B * P
delta_amount = C - B
deviation_percent = (C - B) * 100 / B, solo cuando B > 0
```

Las reglas son independientes: basta cualquiera para crear una alerta; cuando
se cumplen ambas, una sola alerta incluye ambos `trigger_reasons`. Igualdad
dispara la regla. La comparacion porcentual usa multiplicacion cruzada antes
de redondear. Los calculos usan `Decimal` con precision local; se conservan
creditos y ceros. Los importes de entrada ya son agregados de billing v2
redondeados a centimos; porcentajes e importes derivados se presentan con dos
decimales y HALF_UP, normalizando cero negativo.

Se usan exclusivamente registros de ingestas completadas y autorizadas. No se
suman monedas ni grupos independientemente redondeados para reconstruir un
total. `subscription` y `resource_group` conservan `subscription_id`; los grupos
de recursos se comparan en minusculas dentro de la misma suscripcion, conforme
a billing. `service` y `project` son agregados del tenant y llevan
`subscription_id: null`; no permiten atribuir el importe a una suscripcion
concreta. Se conserva `group_value: null` para una dimension desconocida.
La seleccion por proyecto hereda el fallback de billing al tag `project`.

Solo los grupos presentes en el periodo actual producen assessments. Un grupo
ausente no equivale a coste cero. Baseline ausente produce `baseline_missing`;
baseline cero o negativo produce `baseline_nonpositive`, porcentaje null y no
dispara desviacion. Con baseline negativo se conserva la diferencia absoluta.
El umbral absoluto puede dispararse aunque la desviacion no sea evaluable.

## Respuesta y evidencia

El objeto completo tiene estos campos:

| Campo | Significado |
| --- | --- |
| `contract_version`, `source` | `1`, `billing_summary_v2`. |
| `definition` | Peticion validada, incluidos defaults y reglas deshabilitadas como null. |
| `current_period`, `baseline_period` | Fechas inclusiva/exclusiva y `timezone: UTC`; baseline null cuando no se solicita desviacion. |
| `current_quality`, `baseline_quality` | `data_status`, `record_count`, `missing_dimension_count`, `excluded_undated_count`; baseline null cuando no se consulta. |
| `evaluation_status` | `unavailable` sin grupos de la moneda; `provisional` con calidad partial en cualquier periodo o comparaciones no evaluables; `evaluated` en los demas casos. |
| `completeness` | Siempre `not_verified`, incluso con estado evaluated. |
| `limitations` | Limitaciones explicitas de cobertura/frescura, lecturas separadas, redondeo/monedas y ausencia de causa o ahorro demostrado. |
| `assessments` | Todos los grupos actuales evaluados, incluidos los que no disparan reglas. |
| `alerts` | Subconjunto disparado, con `id`, `evidence_id` y `cause_status: not_established`. |

Cada assessment contiene `group_value`, `subscription_id`, `currency`,
`current_cost`, `current_record_count`, `baseline_record_count`, `baseline_cost`,
`delta_amount`, `deviation_percent`, `threshold_status`, `deviation_status` y
`trigger_reasons`. Los campos del baseline y derivados pueden ser null.
`threshold_status` es disabled/below/triggered. `deviation_status` permite esos
tres valores mas baseline_missing/baseline_nonpositive. Las listas se ordenan
por moneda, suscripcion y clave de grupo; no representan una prioridad por
severidad. No se calcula severidad ni probabilidad estadistica.

`id` empieza por `cost-` y contiene SHA-256 del contrato, tenant autenticado,
definicion y clave del grupo. Identifica la misma seleccion aunque cambien sus
importes. `evidence_id` empieza por `evidence-` y tambien incorpora assessment
y calidad de ambos periodos; cambia cuando cambia esa evidencia agregada.
Ninguno es un token de acceso, un identificador de fila original ni prueba de
integridad del origen. No existe almacenamiento o endpoint de recuperacion por
ID: el consumidor debe conservar la respuesta si necesita citarla despues.

`record_count` de quality corresponde a la moneda solicitada. El contador de
dimensiones ausentes procede de todo el periodo consultado, incluidas otras
monedas; `excluded_undated_count` corresponde a registros sin fecha de todas
las ingestas completadas del tenant, sin poder asignarlos a este periodo.
Billing no informa dias cubiertos, fecha de frescura ni IDs de ingesta. Los
periodos se leen por separado y una ingesta tardia puede cambiar la siguiente
evaluacion. `available` no certifica cobertura completa. Una lista de alertas
vacia, especialmente con provisional/unavailable, no demuestra gasto normal.

Errores de autenticacion/pertenencia mantienen las respuestas existentes
401/403 y se resuelven antes de leer costes. Fuentes solapadas en cualquiera
de los periodos devuelven `409 {"detail":{"code":"ambiguous_cost_source"}}`
sin publicar importes parciales. Se conserva
[ADR-0010](../adr/ADR-0010-azure-cost-source-overlap.md).
Los nombres de grupos son datos del tenant: no publicarlos en logs o evidencia
compartida indiscriminadamente; los hashes no anonimizan el resto del payload.

## Ejemplo reproducible con doble explicito

Desde la raiz del repositorio, con las dependencias Python del backend,
ejecutar este codigo Python (por ejemplo, pegarlo en `python`). No accede a
Cockroach, Azure ni al HTTP: construye dos `BillingSummary` sinteticos para
comprobar el contrato del servicio. La misma peticion HTTP obtiene datos reales
del tenant autorizado y no garantiza estos importes.

```python
import sys
sys.path.insert(0, "apps/backend")
from app.schemas.anomalies import AnomalyDefinition
from app.schemas.billing import BillingSummary
from app.services.anomalies import evaluate_anomalies

definition = AnomalyDefinition(
    start_date="2026-04-08", end_date="2026-04-15", group_by="service",
    currency="EUR", absolute_threshold="150.00",
    deviation_threshold_percent="50.00", min_absolute_increase="1.00",
)

def summary(start, end, cost):
    return BillingSummary(
        period={"start_date": start, "end_date": end},
        group_by="service", tag_key=None, data_status="available",
        totals=[{"currency": "EUR", "cost": cost, "record_count": 7}],
        groups=[{"subscription_id": None, "value": "Compute",
                 "currency": "EUR", "cost": cost, "record_count": 7}],
        missing_dimension_count=0, excluded_undated_count=0,
        monthly_spend=cost, open_ingestions=0, currency="EUR",
    )

result = evaluate_anomalies(
    definition,
    summary("2026-04-08", "2026-04-15", "160.00"),
    summary("2026-04-01", "2026-04-08", "100.00"),
    tenant_id="example-tenant",
)
print(result.model_dump_json(indent=2))
```

La respuesta completa impresa contiene `evaluation_status: evaluated`,
`completeness: not_verified`, un assessment y esta alerta:

```json
{
  "group_value": "Compute",
  "subscription_id": null,
  "currency": "EUR",
  "current_cost": "160.00",
  "current_record_count": 7,
  "baseline_record_count": 7,
  "baseline_cost": "100.00",
  "delta_amount": "60.00",
  "deviation_percent": "60.00",
  "threshold_status": "triggered",
  "deviation_status": "triggered",
  "trigger_reasons": ["absolute_threshold", "period_increase"],
  "id": "cost-17b700eb95ccf24b7cc2794ee3a79c6a5ef0737b69e3a0bfc0e783a5b2bf4b02",
  "evidence_id": "evidence-03bd43f644d70342b4649f54e2851c6998c648551b608d37b027636b9756a90a",
  "cause_status": "not_established"
}
```

## Consumo por JUP-038 y contrato de agente

JUP-038 puede explicar que Compute fue marcado porque 160.00 EUR alcanza el
umbral de 150.00 EUR y aumenta 60.00 EUR (60.00%) frente a 100.00 EUR del periodo
anterior. Debe conservar moneda, periodos, reglas, quality, limitaciones e
`evidence_id`; el LLM explica los calculos ya realizados, sin recalcularlos o
inventar causa, ahorro, despliegues, uso o severidad. El contexto de sesion se
inyecta fuera de los argumentos LLM. Una respuesta provisional debe conservar
esa condicion y cualquier baseline no evaluable.

La adaptacion al envelope comun de herramientas (correlation ID, source,
evidence IDs, assumptions y limitations) corresponde al consumidor. Este
endpoint no registra ni habilita por si mismo una herramienta del agente y no
ha probado una integracion JUP-038. Su consumidor puede usar un doble explicito
del objeto versionado mientras implementa y prueba dicha integracion.

La regla diaria de `detect_cost_anomaly_candidates` en
[JUP-084](../architecture/finops-agent-tools.md#detect_cost_anomaly_candidates)
es `relative_delta > 20% AND absolute_delta > 100 EUR/day`. Este evaluador
compara agregados de periodo con limites inclusivos y reglas independientes;
no cumple ni reemplaza silenciosamente aquella regla. Una futura adaptacion
debe resolver granularidad, cobertura, igualdad y combinacion de condiciones
mediante su cambio de contrato y pruebas. No se divide un agregado entre dias
para afirmar que se ha verificado una serie diaria.
