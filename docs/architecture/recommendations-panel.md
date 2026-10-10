# Panel de recomendaciones — JUP-058

Tarjeta: https://trello.com/c/kU8swHK1. Verificación de diseño: 2026-10-10.

El panel permite priorizar y consultar propuestas; no ejecuta cambios en Azure.
Mantiene el tema y el shell actuales, sin asumir el rediseño JUP-112. La ruta
de producto es `/recommendations`.

## Frontera entre componentes

| Fuente | Responsabilidad | Uso en el panel |
| --- | --- | --- |
| JUP-033, `RecommendationReport` v1 | Generar candidatos desde costes Azure y asociar evidencia | Tipo, acción, justificación, dificultad, riesgo, confianza, coste observado y evidencia |
| JUP-034, `ImpactReport` v1.0 | Evaluar escenarios explícitos de coste base/objetivo y evitar duplicar scopes | Ahorro potencial mensual/anual por ID, moneda y mes base; inclusión/exclusión y limitaciones |
| JUP-058 | Presentación y consulta | Filtros, orden, detalle, estados y exportación; nunca genera escenarios o calcula el impacto |

Los esquemas se contrastaron como **propuestas locales sin commit** en las
copias aisladas `tfm-economicon-jup033` y `tfm-economicon-jup034`, archivos
`apps/backend/app/schemas/recommendations.py` y `recommendation_impact.py`.
No estaban integrados en la base c2995a1. El contrato ejecutable de cada tarjeta
sigue siendo la fuente de verdad: hay que contrastarlo de nuevo antes de integrar.

En el contraste final del mismo día ya se publicaron las propuestas
[JUP-033 / PR #97](https://github.com/EconomiconFinOps/tfm-economicon/pull/97)
(`1c8dabf62c99a7ec55a0367d3e1c418a5c05733f`) y
[JUP-034 / PR #96](https://github.com/EconomiconFinOps/tfm-economicon/pull/96)
(`61001a2227d0d1609987de02ffc8a54d8b7f5f96`). Siguen sin integrar en develop;
los hashes de fuentes contrastadas están en la evidencia JUP-058.

## Contratos utilizados

JUP-033 propone `GET /billing/recommendations?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
bajo el prefijo API existente, con sesión y tenant. El periodo es UTC `[inicio,fin)`
y la fuente `azure_cost_records`; `data_environment: simulated` describe el origen
de datos incluso si se obtiene por HTTP. Una conexión HTTP no convierte la fuente
simulada en facturación Azure real.

Las reglas actuales son `missing_project` (tagging/supported, proyecto nulo) y
`largest_project_cost` (investigation/investigation_candidate, proyecto identificado).
Cada elemento referencia evidencia `cost_query` con la misma regla, proyecto,
coste observado y periodo. Ahorro y moneda de ahorro son nulos en JUP-033 v1;
el generador actual entrega dificultad `unknown`.

JUP-034 propone `POST /recommendations/impact/evaluate`, con escenarios aportados
explícitamente por el solicitante. JUP-058 no llama a ese endpoint ni infiere un
coste objetivo desde agregados de proyecto. Su adaptación recibe un informe ya
evaluado, enlazado por `recommendation_id`. El mes base, `basis`, supuestos,
`included_in_total` y `excluded_by` se conservan. Un informe de otra procedencia,
periodo o tenant no se debe unir por coincidencia accidental del identificador.

Los decimales son texto, desconocido es `null` y cero es una cifra válida. Los
totales de monedas distintas se mantienen separados; ordenar una lista no
autoriza conversión de divisas. El panel no suma alternativas solapadas ni
recalcula anualización: eso pertenece al evaluador.

## Muestra y límites de evidencia

La demo utiliza dobles serializables visibles e independientes del cliente
seleccionado. Permite comprobar variedad de dificultades e impactos aunque el
generador v1 todavía produzca dificultad desconocida y ahorro no estimado.
Esos ejemplos no acreditan resultados del motor ni ahorros obtenidos.

La consulta del cliente reutiliza la capa HTTP de sesión/tenant. Un fallo del
endpoint, falta de permiso o respuesta incompatible tiene un estado propio;
no se sustituye por la muestra. Las pruebas con dobles HTTP comprueban ese
comportamiento sin afirmar integración extremo a extremo.

La exportación se limita a recomendaciones visibles, con origen, periodo,
moneda y significado explícito de los importes. Se evita interpolar texto
externo en el generador HTML de PDF compartido.

## Integración pendiente

1. Integrar y contrastar las versiones definitivas JUP-033/034.
2. Ejecutar la lectura con backend autenticado y dos tenants; comprobar
   autorización, cambio de tenant, periodo, error y respuesta vacía.
3. Si se conecta una fuente de informes JUP-034, validar tenant, periodo y
   correspondencia de IDs antes de mostrar impacto; no inventar un endpoint
   de listado/persistencia inexistente.
4. Completar pairing y las reviews independientes según CONTRIBUTING. La
   evidencia propia de implementación no sustituye la validación humana.
