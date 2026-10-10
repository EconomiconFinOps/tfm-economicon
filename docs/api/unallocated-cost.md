# Detección de candidatos de gasto no asignado — JUP-028

`GET /billing/unallocated-cost?start_date=2024-06-01&end_date=2024-07-01`
requiere autenticación Bearer y `X-Tenant-Id` con pertenencia verificada. Ambas
fechas son obligatorias; el periodo es UTC `[inicio, fin)`. Un intervalo inválido
produce 422. La ruta es de lectura y no modifica costes ni etiquetas.

```bash
curl --get "$BACKEND_URL/billing/unallocated-cost" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Tenant-Id: $TENANT_ID" \
  --data-urlencode 'start_date=2024-06-01' \
  --data-urlencode 'end_date=2024-07-01'
```

## Qué mide

La respuesta declara `detection_basis: observed_required_tags` y
`allocation_status: not_evaluated`. Detecta **candidatos por metadatos incompletos**;
no calcula la asignación contable definitiva. Una regla organizativa puede imputar
un coste por centro de coste aunque falte `owner`. Un coste compartido gobernado
no equivale a gasto no asignado. No se aplican ni se inventan esas reglas aquí.

`economicon-minimum-v1` comprueba `owner`, `environment`, `application`,
`cost_center`, `project` con las mismas reglas de la PR #66/JUP-017:

- texto no vacío tras trim; identificadores portables de hasta 128 caracteres;
- entornos dev/development, test/testing, staging/stage, prod/production;
- rechazo de unknown, n/a, null, none, true, false, undefined, unassigned y `-`;
- no se infiere owner de organization ni application de project;
- se leen las claves canónicas ya normalizadas en almacenamiento.

Esta versión comprueba sintaxis y presencia; no verifica pertenencia a un
catálogo corporativo. La política se reutiliza sin incorporar el resto de la PR
#66, que sigue siendo una dependencia no integrada en la base de esta entrega.
JUP-015 podrá introducir nuevas versiones cuando acuerde catálogos y reglas.

## Importes y diagnóstico

Cada elemento de `currencies` mantiene una moneda independiente:

| Campo | Significado |
| --- | --- |
| `positive_cost` | Suma de cargos positivos observados |
| `complete_metadata_cost` | Cargos positivos con las cinco etiquetas válidas |
| `candidate_cost` | Cargos positivos que incumplen una o varias etiquetas |
| `negative_adjustments` | Suma firmada de los ajustes negativos |
| `complete_metadata_negative_adjustments`, `candidate_negative_adjustments` | Ajustes negativos separados por el mismo predicado |
| `net_cost`, `complete_metadata_net_cost`, `candidate_net_cost` | Positivos más sus ajustes negativos |
| `candidate_percent` | Complemento a 100 del porcentaje de coste con metadatos completos, redondeado como JUP-017 |
| `record_count`, `candidate_record_count` | Filas, incluyendo importes cero |
| `groups` | Partición de candidatos por conjunto exacto de etiquetas ausentes o inválidas |

Una fila pertenece a un único grupo. Cada grupo expone
`missing_or_invalid_tags`, `record_count`, `positive_cost`, `negative_adjustments`,
`net_cost`, y un motivo: `no_owner`, `unclassified` o
`no_owner_and_unclassified`. `unclassified` significa incumplimiento de alguna
de las cuatro etiquetas distintas de owner, incluyendo environment. No representa
el estado contable. Hay como máximo 31 grupos por moneda, sin muestras truncadas.

Ejemplo sintético: 60 EUR completos, 40 EUR sin owner ni application y -10 EUR
con esos mismos defectos producen `candidate_cost=40.00`,
`candidate_percent=40.00`, `candidate_negative_adjustments=-10.00`,
`candidate_net_cost=30.00`, `net_cost=90.00`. Las dos etiquetas defectuosas
**no** generan 80 EUR de gasto candidato.

Se agrega con Decimal a precisión almacenada. Los importes se presentan a dos
decimales con HALF_UP; el redondeo independiente puede producir diferencias de
un céntimo entre suma de importes presentados y total. No sumar porcentajes.
Si no hay cargos positivos, `candidate_percent=null`, con motivo
`negative_adjustments_only` o `zero_cost_only`. Un periodo vacío devuelve
`currencies=[]`. Un neto cero no elimina un porcentaje basado en cargos positivos.

## Ámbito, doble cómputo y dependencias

Sólo entran ingestas completadas con coincidencia de tenant y suscripción entre
fila e ingesta. Se conservan los mismos límites de fecha y política de fuentes
de `/billing/summary` y JUP-017. Más de una ingesta completada para una suscripción
y día dentro del periodo produce **409** con
`{"detail":{"code":"ambiguous_cost_source"}}`, sin importes. Se comprueba antes
de filtrar candidatos y con independencia de la moneda. No se elige una ingesta
arbitraria ni se deduplica por recurso o hash sin identidad de cargo acreditada.

JUP-027 puede agrupar por una dimensión: el grupo sin application no equivale al
grupo sin project ni a esta unión de defectos. No sumar importes entre dimensiones
de showback ni entre los diagnósticos de JUP-017 y esta ruta. La implementación
conjunta de JUP-015/027/017 no está validada por esta entrega.

Contraste local del 10/10/2026, sin incorporar cambios de otros chats: el candidato
`docs/finops/tagging-taxonomy.json` de JUP-015 conserva las mismas cinco claves,
marcadores, patrón y entornos. El contrato `docs/api/showback.md` de JUP-027
atribuye cada fila a una única dimensión y conserva importes netos exactos; para
project admite columna con fallback a tag. Esta ruta evalúa exclusivamente tags,
pondera cargos positivos y muestra dos decimales. Por eso sus resultados no son
intercambiables ni sumables con los importes sin asignar de showback.

## Límites visibles

- `excluded_undated_count` cuenta filas completadas sin fecha del tenant; no se
  atribuyen a ningún periodo. Su presencia produce `data_status=partial`.
- `available` significa que hay filas fechadas calculables, no que la factura
  esté completa ni que exista asignación contable verificada.
- Los datos disponibles pueden omitir owner/application; la API de origen admite
  agrupaciones limitadas a CostCenter/Project/env/org. Una ausencia en la consulta
  no demuestra una ausencia en Azure. Se analizan etiquetas históricas recibidas;
  no se consultan ni heredan etiquetas actuales del recurso.
- No hay catálogo empresarial, elegibilidad/etiquetabilidad, estados shared o
  excluded gobernados, reglas de reparto, conversión de monedas, impuestos,
  amortización, estimación de ahorro ni recuperación de créditos ya neteados.
- El corpus ilustrativo antiguo incluye businessunit. Para esta política se
  respetan las cinco dimensiones de Trello JUP-015/JUP-017, incluyendo project;
  no se cambia silenciosamente el corpus ni se declara aprobado un catálogo.
- Esta entrega expone API y pruebas. No incluye panel, listado de recursos,
  integración conversacional ni despliegue.

Véanse [evidencias](../evidence/JUP-028-validation.md) y
[continuidad](../continuidad/gasto-no-asignado.md).
