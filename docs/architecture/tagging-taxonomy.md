# Taxonomía mínima de etiquetas y asignación de costes

JUP: JUP-015 · [Trello](https://trello.com/c/UDIyjTyl) · Diseño verificable, 10/10/2026.

Esta es la fuente canónica del diccionario de Economicon. El
[contrato JSON](../finops/tagging-taxonomy.json), el
[verificador de referencia](../../tools/tagging_taxonomy.py) y sus
[casos sintéticos](../finops/tagging-taxonomy-cases.json) permiten comprobarlo
sin ejecutar la aplicación. No se configura Azure ni se cambia ingesta, API,
SQL o UI. Los catálogos corporativos y su aprobación siguen pendientes.

## 1. Diccionario y alcance

Las cinco claves son obligatorias **por fila de coste observada**. La presencia
de etiquetas adicionales no compensa una obligatoria ausente. Una etiqueta es
un par clave/valor; una aplicación, un equipo y una unidad son entidades distintas.

| Clave | Entidad y finalidad | Ejemplo exclusivamente sintético | No equivale a |
| --- | --- | --- | --- |
| `owner` | ID estable del equipo responsable de mantener la carga y resolver la atribución | `team-demo` | persona, `organization`, centro de coste |
| `environment` | Entorno de ejecución | `prod` | tenant o suscripción |
| `application` | Aplicación o carga de trabajo consumidora | `app-demo` | proyecto, servicio Azure, grupo de recursos |
| `cost_center` | Unidad presupuestaria que recibe la imputación | `cc-demo` | equipo o unidad organizativa por igualdad de nombre |
| `project` | Iniciativa financiada | `project-demo` | aplicación |
| `organization` (opcional, existente) | Clasificación organizativa declarada por la fuente | `division-source` | `owner` o unidad del catálogo sin mapping |
| `organization_unit` (catálogo, no sexta etiqueta obligatoria) | Unidad de estructura organizativa para showback | `unit-demo` | centro de coste, tenant, `organization` arbitraria |

Cada fila tiene un valor escalar por clave. Un equipo puede mantener varias
aplicaciones y participar en varios proyectos; un proyecto puede financiar varias
aplicaciones. No se genera ninguna de esas relaciones a partir de nombres. El
contrato mínimo de catálogo sólo relaciona explícitamente equipo y unidad; no
acredita compatibilidad entre las cuatro entidades ni exactitud contable.

Preferir IDs estables sin datos personales ni secretos. Los nombres visibles
pueden cambiar sin reciclar IDs históricos. Este documento no asigna equipos a
personas ni decide prioridades o funciones del equipo del TFM.

## 2. Política de conformidad sintáctica

`economicon-minimum-v1` reproduce la política de
[JUP-017 / PR #66](https://github.com/EconomiconFinOps/tfm-economicon/pull/66),
contrastada en `6e25b308d9a890f9b73e4df7a55d904ae34b0065`. No añade catálogos
a esa versión ni cambia sus porcentajes.

1. Entrada del verificador: objeto `tags` **ya normalizado con claves canónicas**.
   No acepta alias como sustituto silencioso ni promueve otras dimensiones.
2. Cada valor requerido debe ser texto; se recortan espacios exteriores para
   comparar, conservando el dato original. Null, listas, números y booleanos son
   defectos de tipo en esta frontera.
3. Vacío tras recortar es inválido. Los marcadores, sin distinguir mayúsculas,
   son `unknown`, `n/a`, `null`, `none`, `true`, `false`, `undefined`,
   `unassigned` y `-`.
4. `owner`, `application`, `cost_center` y `project` cumplen
   `^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$`: 1–128 caracteres ASCII, primer
   carácter alfanumérico. No se convierte su valor a minúsculas.
5. `environment` admite, sin distinguir mayúsculas, `dev/development`,
   `test/testing`, `staging/stage`, `prod/production`. Se recomiendan las formas
   cortas al crear etiquetas. Son equivalencias de vocabulario documentadas;
   no reescriben almacenamiento ni agrupaciones existentes.
6. La fila cumple únicamente si las cinco reglas se satisfacen. El resultado
   incluye defectos por clave: `missing`, `type`, `empty`, `placeholder` o
   `invalid_value`; una fila puede tener varios, pero su coste se cuenta una vez.

`minimum_compliant=true` significa conformidad de formato. Un ID desconocido
como `team-inexistente` puede cumplirla y no pertenecer a un catálogo.

## 3. Entrada de datos, alias y conflictos

El [normalizador vigente](../../apps/processor/app/normalization/azure_cost.py)
y su [contrato](azure-cost-normalization.md) son la frontera de ingesta. Tras
limpiar separadores y minúsculas en claves, reconoce:

| Entrada en `Tags` | Clave normalizada | Columnas individuales reconocidas hoy |
| --- | --- | --- |
| `costcenter`, `cost_centre`, `cost_center` | `cost_center` | `CostCenter`, `costcenter` |
| `env`, `environment` | `environment` | `env`, `Environment` |
| `org`, `organization` | `organization` | `org`, `Organization` |
| `project` | `project` | `Project` |
| `owner` | `owner` | ninguna |
| `application` | `application` | ninguna |

Las columnas individuales se comparan sin distinguir mayúsculas. Para obtener
`owner` y `application` hoy deben llegar en el objeto serializado `Tags`;
no basta una columna homónima. El simulador no expone ambas como agrupaciones
individuales. `CostCenter` es alias de clave; no es una equivalencia de valores.
`owner_team`, `team`, `ProjectOwner`, `app` o `business_unit` no se incorporan
como alias nuevos. `organization` no satisface `owner`; `project` no satisface
`application`.

Conflictos reales entre alias en nuevas ingestas producen error de normalización.
El comparador actual ignora mayúsculas del valor y conserva la primera grafía
cuando coincide; billing agrupa valores de etiquetas distinguiendo mayúsculas.
Por ello, el catálogo usa coincidencia exacta tras trim y no promete corregir
variantes históricas. El backfill de migración 003 aplica precedencias y no
acredita la misma detección de conflictos.

Límite importante: `_parse_tag_map` convierte escalares JSON a texto. Por tanto,
el rechazo de tipos del verificador se refiere al objeto recibido aquí, no al
tipo original de Azure. Un número de origen puede convertirse en `"123"` y
cumplir sintaxis; null/booleanos convertidos quedan rechazados por marcadores.
Preservar tipo/procedencia de origen exigiría un cambio separado de ingesta.

## 4. Contrato de catálogos organizativos

`economicon-catalog-v1` es una capa explícita adicional. No sustituye
`economicon-minimum-v1`. Se entrega una
[plantilla vacía](../finops/tagging-catalog-template.json) en estado `draft`
y un catálogo `example` dentro de los casos. Ninguno acredita entidades reales.

| Campo | Regla |
| --- | --- |
| `schema_version`, `policy_version` | `1`, `economicon-catalog-v1` |
| `catalog_version` | Identificador inmutable del snapshot; nueva versión para cambiar valores o relaciones |
| `tenant_id` | Tenant exacto; nunca usar catálogo de otro tenant |
| `status` | `draft`, `example` o `approved` |
| `approval_reference` | Evidencia externa de aprobación exigida para `approved`; el verificador comprueba que existe texto, no su autenticidad |
| `valid_from`, `valid_to` | Fechas ISO y vigencia `[desde, hasta)` sobre `usage_date`; `null` final significa sin fin declarado |
| `values` | Arrays de IDs únicos para `owner`, `application`, `cost_center`, `project`, `organization_unit`; todas estas claves y sólo estas |
| `owner_to_org_unit` | Mapa explícito owner → unidad; ambos IDs deben existir en `values`; puede ser parcial |

Los IDs de catálogo usan la misma sintaxis y rechazo de marcadores. Sin alias de
valores organizativos. El vocabulario de entornos ya está cerrado por la política.
Dos equipos pueden apuntar a una unidad; cada equipo tiene como máximo una unidad
en un snapshot. Si necesita repartirse entre unidades, queda pendiente una regla
de reparto versionada, no una lista de IDs en `owner`.

El verificador recibe **un snapshot elegido explícitamente** y la fecha de uso.
No selecciona automáticamente entre versiones ni prueba autorización de quien
las publica. Un futuro cargador debe rechazar solapamientos de snapshots aprobados
por tenant/fecha y registrar la versión usada; no elegir el último silenciosamente.
El registro real, su custodia y su publicación son trabajo de adopción pendiente.

| Salida | Interpretación |
| --- | --- |
| `catalog_status=not_provided` | No se suministró catálogo; membresía sin comprobar |
| `catalog_status=not_applicable` | Tenant o periodo diferentes; no usar valores ni mapping |
| `catalog_status=draft` | Incompleto/no aprobado; no evaluar membresía |
| `catalog_status=example` | Se puede probar membresía sintética; `organizationally_valid=null` |
| `catalog_status=approved` | Referencia declarada y snapshot aplicable; evaluar formato y membresía |
| `catalog_match` | `true/false` en example/approved aplicable, `null` cuando no procede; exige las cinco etiquetas válidas y las cuatro membresías |
| `unknown_catalog_values` | Claves organizativas de formato válido cuyo ID no pertenece al snapshot |
| `organizationally_valid` | `true/false` sólo para approved aplicable; `null` en el resto; no certifica relaciones entre entidades ni facturación correcta |
| `organization_unit` | Sólo mapping explícito de owner válido/miembro para example/approved aplicable; `null` si falta; siempre interpretar junto a `catalog_status` |

La unidad puede conocerse aunque falte otra etiqueta: la atribución por equipo
y el cumplimiento completo son preguntas distintas. Un equipo sin mapping no
se descarta ni se convierte en unidad por su nombre.

## 5. Costes, periodos, herencia y consumidores

La procedencia es la fila histórica normalizada (`usage_date`, `source_row_hash`,
tenant y fuente); no las etiquetas actuales del recurso. No se infiere herencia
desde suscripciones/grupos ni desde nombres. Contar etiquetas heredadas sólo si
están materializadas en la fila recibida y su procedencia está acreditada. No
reescribir historia al aprobar un catálogo: conservar fecha, política y versión
usadas y rotular cualquier recálculo como tal.

| Consumidor | Contrato de adopción | Límite explícito |
| --- | --- | --- |
| JUP-017 cobertura | Mínimo v1; `P` cargos positivos, `T` positivos conformes, `U=P-T`, cobertura `100*T/P`; negativos aparte y neto reconciliado, N/D si P=0; por tenant/periodo/moneda | Capa de catálogo requiere versión/rotulado propios y pruebas; PR66 no la implementa |
| JUP-027 showback | Agrupar aplicación/proyecto/centro/equipo por sus claves exactas; unidad sólo mediante mapping explícito vigente o una política de fuente documentada | No equiparar organización/centro/equipo; mostrar sin mapping y conservar total por moneda |
| JUP-028 gasto no asignado | Distinguir ausencia/invalidez, ID fuera de catálogo, catálogo no comprobado y equipo sin unidad; varios motivos pueden pertenecer a la misma fila | No sumar los costes de cada motivo como si fueran filas disjuntas; no llamar «sin dueño» a todo gasto no conforme |
| JUP-037 consulta | Aplicación desde `tags.application`, equipo desde `tags.owner`, proyecto/centro y etiquetas explícitas; mostrar política/procedencia al hablar de cumplimiento | Un literal `Unknown` puede consultarse como grupo observado y ser inválido para cobertura; no inferir aplicación desde proyecto |

Costes compartidos o no etiquetables permanecen visibles; ausencia no significa
cero. Sin regla de reparto aprobada se conservan en un grupo residual explícito,
sin reparto igualitario automático. Los ajustes negativos conservan signo y no
son necesariamente créditos; ninguna métrica mezcla monedas o fuentes solapadas.
JUP-015 no introduce un motor de coste ni ejecuta estos consumidores.

Ejemplo de conciliación para los consumidores: 60 EUR con mínimo válido + 40 EUR
con owner ausente y application ausente − 30 EUR de ajuste = 70 EUR netos;
cobertura sintáctica 60%, no conforme 40 EUR (no 80), ajustes −30 EUR. Si no hay
catálogo, esos 60 EUR no acreditan asignación corporativa. Es un ejemplo de
contrato, no un cálculo de facturación probado por este verificador.

## 6. Adopción, gobierno y reproducción

```console
python tools/tagging_taxonomy.py --cases docs/finops/tagging-taxonomy-cases.json
python -m unittest discover -s tools/tests -p test_tagging_taxonomy.py -v
```

Paris lidera JUP-015; Victor tiene pairing, Alejandro revisión y Lucia validación,
según Trello consultado el 10/10. Asignación no acredita participación. Antes de
usar un catálogo real: acordar valores con sus responsables organizativos,
registrar aprobación, publicar un snapshot por tenant y vigencia, validar el
consumidor y comparar resultados bajo ambas políticas. Cambios de significado,
alias o reglas requieren otra versión; no se modifica el mínimo v1 silenciosamente.

Pendientes concretos: catálogo real y autoridad de aprobación; pairing acreditado;
reviews independientes; adopción y pruebas de integración en 017/027/028/037.
El artefacto está listo para revisión técnica y no declara cerrados esos pasos.

## Fuentes y decisión

- [FinOps Foundation, Cloud Cost Allocation](https://www.finops.org/wg/cloud-cost-allocation/),
  consultada el 10/10/2026: estrategia de metadatos propia de la organización,
  distinción de etiquetas, jerarquías y reparto compartido. Las cinco claves
  proceden de JUP-015, no de un mínimo universal de FinOps.
- [Microsoft, tags de Azure](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/tag-resources),
  consultada el 10/10/2026: limitaciones de tags e inexistencia de herencia
  automática del recurso desde grupo/suscripción. Nuestra regla de 128 caracteres
  es una convención del proyecto, no el máximo general de Azure.
- [ADR-0018](../adr/ADR-0018-tagging-taxonomy.md),
  [OpenSpec](../../openspec/changes/archive/2026-10-10-jup-015-tagging-taxonomy/proposal.md) y
  [evidencia](../evidence/JUP-015-validation.md).
