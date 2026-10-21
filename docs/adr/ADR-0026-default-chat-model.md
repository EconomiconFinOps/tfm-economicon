# ADR-0026: DeepSeek V4.1 Flash como modelo generativo único

- Fecha: 2026-10-21
- Estado: Proposed (implementación autorizada por Paris; ratificación del equipo pendiente)
- JUP: [JUP-132](https://trello.com/c/ERLZlPsT)
- Change: [jup-132-default-chat-model](../../openspec/changes/archive/2026-10-21-jup-132-default-chat-model/design.md)
- Antecedente histórico conservado: [ADR-0025](ADR-0025-chat-model-selection.md)

## Decisión
Mantener economicon-chat y resolverlo a openrouter/deepseek/deepseek-v4.1-flash
por deepinfra/fp8 normal, no flex/priority. Retirar GLM/Pro del ejemplo y de las
herramientas operativas por defecto. Sin fallback; ZDR, data_collection deny,
require_parameters y límites existentes conservados. Reasoning.enabled=false
será explícito en los consumidores generativos.

Recursos activos v4 con tokenizer Flash fijado a revisión y SHA256; instalación
sólo durante build/preparación. Lectores históricos y tokenizer anterior
exclusivamente para contratos originales. Sin migración ni reescritura de datos.
Embeddings text-embedding-3-small/1536 y su tokenizer no cambian.

## Diferencia respecto a las campañas
ADR-0025 registra una campaña histórica con forwarding no atestiguado; no valida
este cambio ni se reinterpreta su configuración. Comparativas y costes intactos.
Se cambia configuración versionada, no el gateway compartido ni DockerServer.
La memoria e/g recibe una propuesta separada, no una modificación ni aceptación.

## Compatibilidad y límites
[Catálogo OpenRouter](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash/endpoints)
identifica deepinfra/fp8 normal con structured_outputs, tools y reasoning.
[Routing](https://openrouter.ai/docs/guides/routing/provider-selection) documenta
la selección explícita. [Recurso oficial](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)
proporciona el tokenizer. El catálogo no acredita calidad ni privacidad efectiva
de una inferencia. Esta entrega verifica configuración y compatibilidad offline;
no ejecuta inferencias, campañas o comparaciones nuevas.
