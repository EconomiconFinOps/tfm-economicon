# JUP-035: esquema privado accionable, semantic3200i

Nota del 12/10/2026: esta evidencia conserva un ensayo historico y sus rutas
locales; esos recibos no son accesibles desde otro checkout. La
[guia reproducible](../validation/JUP-035-chat-reproduction.md) usa entradas
versionadas y el chat vigente. No sustituye ni revalida este resultado.

Anexo posterior: [focal013 real i](jup-035-battery-semantic3200i-focused013.md),
completed en un intento y validacion independiente PASS. Acredita solo la rama
no accionable de ese ensayo; no full28i ni ambas ramas remotas. Los resultados,
fallo013h y pendientes del corte offline siguiente se conservan como historia.

Paris aprobo el diseno de dos ramas anyOf y primero las pruebas offline.
Especificacion validada antes de programar:63/63. HEAD local954b442 sin Git writes.
Worktree exclusivo e5-battery-corrections-worktree, mismo expediente autonomo.

## Cambio y limites

Backend provider_response_schema y processor chat_provider_schema conservan
el objeto base, propiedades, required, additionalProperties y $defs compartidos.
Dos ramas completas restringen status a ok/partial con evidence minItems1 o a
los otros cinco estados que permiten evidence[]. financial_metrics_allowed
conserva metrics maxItems0 sin autoridad y20 con ella; costes cero validos intactos.
No cambios en FinOpsResponse1.0, validadores, campos publicos, prompts, modelo,
3200, plazos, reintentos, routing, runner ni limites financieros.

Hash privado base:fc96e7bd1078f48459a4658504b26b581d88491c456af68cd34f358ccf732a07.
Variante sin autoridad:f3d2a067acd0e09a80e321a7bfe9704fcd6314bb628d0ac11810a6bff8ac8a5c.
Publico intacto:baf067ac8fe35a693848012c5358cb1c6ab8883ebaa02a63166b00f7d8298018.
Bundle:jup-035.chat.v3:66f8743e5d0d022f26f92153e6d5ad92ab22a2081517c1f959a3a25c95e71922.

## Evidencia local, no aceptacion real

Expediente fuera del producto:
C:/Users/Trabajo/.codex/visualizations/2026/09/07/01a07c55-c454-7bb3-8053-cbf2ad70d2ec/e5-context-compression-evidence/restart-20261011/jup069-real-battery/corrections/

- semantic3200i-design-openspec.log:63/63 antes de Red.
- semantic3200i-red-backend-offline.log:2 fallos DID NOT RAISE, defecto real.
- semantic3200i-red-processor-offline.log:2 fallos por ausencia de anyOf.
- semantic3200i-green-backend.log:25 passed; battery/context assembly existentes.
- semantic3200i-green-processor.log:49 passed; battery/resources/gateway existentes.
- semantic3200i-count-backend.log y count-processor.log: esquemas y conteos identicos.
- semantic3200i-mutation-backend.json y mutation-processor.json:2/2 detectadas
  en copias desechables, exit1 por fallo conductual/asercion, no por import o hash.
- semantic3200i-product-stable.json: hashes de fuentes y acuerdo de recursos.
- Guards separados design/red/green/mutation/docs: limites de archivos,
  no sustituyen revision independiente ni garantizan sandbox de lectura.

Cada variante tiene1633 tokens de esquema. El ejemplo sintetico usa26 variables,
8919 total con reservas1024+3200 frente a1048576. No es consumo real ni presupuesto
de gasto. Se reutilizaron imagenes locales packaged-tests20261010 con pytest9.1.1,
pydantic2.14.0 ytokenizers0.22.1, red externa deshabilitada y origen solo lectura.
Primer intento Red en imagen de producto no tenia pytest; su log se conserva y
no cuenta como Red significativo. No se instalaron dependencias.

## Pendiente

Estado real comunicado:001-012 completadas;013 fallo actionable_requires_evidence,
finish_reason stop. El runner paro por coste no acreditado y conserva recibos.
No se conoce cual de ok/partial produjo el rechazo, ni se declara truncacion.
TOTAL autorizado0.20USD, sin incremento ni nuevas llamadas de este desarrollador.
Revision independiente y ensayo parent013 pendientes antes de repetir la bateria.

Este anyOf es una composicion JSON Schema; su soporte en el endpoint GLM-5.2 con
DeepInfra no esta probado. [OpenRouter](https://openrouter.ai/docs/guides/features/structured-outputs)
advierte variacion por endpoint/strict. [LiteLLM](https://docs.litellm.ai/docs/completion/json_mode)
permite consultar soporte de response_format/esquema, no demuestra cada keyword.
No se autoriza cambiar modelo/proveedor ni activar Response Healing. Cardinalidad
no acredita que las citas sustenten afirmaciones: conservamos los controles y la
evaluacion semantica separados. No se declara full28 ni cierre global.
