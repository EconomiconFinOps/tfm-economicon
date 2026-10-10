# Showback por unidad organizativa — JUP-027

`GET /billing/showback?start_date=2024-06-01&end_date=2024-07-01&dimension=owner`

Requiere `Authorization: Bearer <sesión>` y `X-Tenant-Id: <tenant autorizado>` como las demás consultas de billing. Disponible también en `/docs` del backend. Dimensiones: `owner` (predeterminada), `project`, `application`, `cost_center`. Las dos fechas son opcionales conjuntamente; si se omiten se consulta el mes UTC actual. Inicio incluido y fin excluido. No hay parámetro de tenant en la URL.

## Lectura y reglas de reparto

1. Se lee `pretax_cost` normalizado, antes de impuestos, únicamente de ingestas `completed`. No se afirma que sea coste amortizado ni una factura completa.
2. Cada fila va íntegra a una unidad de la dimensión elegida. Las cuatro vistas son alternativas: sumarlas duplicaría gasto.
3. `owner`, `application` y `cost_center` usan etiquetas canónicas. `project` usa la columna normalizada con fallback a su etiqueta cuando está ausente o en blanco. No se infieren owner de organization ni application de project.
4. Se recortan espacios exteriores y se conserva la distinción de mayúsculas. Identificadores: `[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}`. Marcadores inválidos sin distinguir mayúsculas: `unknown`, `n/a`, `null`, `none`, `true`, `false`, `undefined`, `unassigned`, `-`. Ausente/blanco va a `missing`; tipo JSON no textual o valor inválido, a `invalid`.
5. No se redistribuyen costes compartidos. Un identificador explícito válido recibe el 100%; sin regla/identificador queda sin asignar. Tampoco se exige que otras dimensiones estén completas para atribuir la seleccionada.
6. Créditos y ceros se conservan. Las monedas se separan, sin conversión. Importes como `"10.004"` son cadenas exactas, con hasta doce decimales. No deben convertirse a float para reconciliar.

Por moneda, `currencies[]` expone `groups`, `unassigned` (motivos missing/invalid), `total_cost`, `assigned_cost`, `unassigned_cost` y los conteos correspondientes. Siempre se cumple:

```text
sum(groups.cost) = assigned_cost
sum(unassigned.cost) = unassigned_cost
assigned_cost + unassigned_cost = total_cost
assigned_record_count + unassigned_record_count = record_count
reconciliation_difference = "0.00"
```

`data_status` vale `partial` si hay filas sin asignar o exclusiones sin fecha; `empty` si no hay datos ni exclusiones; `available` en los demás casos, incluido un cero observado. `excluded_undated_count` cuenta filas completadas del tenant sin fecha en todo el ledger, pues no se pueden situar en el intervalo. No se inventa un importe del período para ellas. `available` no certifica exhaustividad de la ingesta.

Errores: 401 sesión inválida, 400 selector de tenant ausente/ambiguo, 403 tenant ajeno, 422 selección inválida y 409 `ambiguous_cost_source` cuando hay varios runs completados para una suscripción/día. Ese 409 no contiene importes ni identificadores.

## Dependencia de taxonomía

Se reutiliza la sintaxis `economicon-minimum-v1` del contrato de JUP-015, contrastada con su candidato `docs/finops/tagging-taxonomy.json` el 2026-10-10. El adaptador del servicio está aislado y declara `policy_version=jup027-provisional-syntax-v1-pending-jup015`; no importa código de otra rama ni certifica su integración. `catalog_status=not_provided` y `organizationally_valid=null` indican que los catálogos por tenant y las correspondencias `owner_to_org_unit` aún no están conectados. Una unidad aquí es el identificador de la dimensión, no una unidad jerárquica certificada. No se declaran aprobaciones de catálogos, pertenencia organizativa ni chargeback.

El contrato versionado y las pruebas están en [OpenSpec](../../openspec/changes/jup-027-organizational-showback/proposal.md). La evidencia ejecutada y sus límites se registran en [JUP-027](../evidence/JUP-027-showback.md). JUP-028 conserva su implementación independiente.
