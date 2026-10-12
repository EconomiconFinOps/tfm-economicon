# Chat conversacional - JUP-035

Actualizado: 12/10/2026. Este tema describe la entrega local, no un merge
ni una validacion humana. Los responsables y el estado oficial siguen en Trello.

## Recorrido vigente

La interfaz assistant-ui usa operaciones `/assistant/.../generations`.
Backend autentica al propietario, valida el contexto y consulta los costes.
Processor genera mediante el canal privado HMAC y solicita la herramienta RAG;
backend ejecuta esa busqueda filtrada por tenant. La respuesta validada, las
citas y la evidencia se guardan atomicamente en el historial JSONB.

El modo mock no llama a modelos. El modo IA utiliza LiteLLM/OpenRouter con
claves distintas de chat y embeddings; no cambia automaticamente a mock.
El resumen conserva los mensajes originales y bloquea el envio mientras comprime.
Las conversaciones antiguas siguen visibles, pero sus respuestas de plantilla
no entran en el contexto del modelo ni en nuevos resumenes.

## Lectura para revision y validacion

1. [Contrato publico](../../apps/backend/app/schemas/chat.py): autoridad financiera y procedencia.
2. [Operaciones](../../apps/backend/app/services/chat_operations.py): admision, espera, cancelacion y recuperacion.
3. [Repositorio](../../apps/backend/app/db/chat_repository.py): transacciones, fencing y persistencia.
4. [Contexto](../../apps/backend/app/services/chat_context.py): costes, RAG y limite de 20 conjuntos antes de consultar.
5. [Panel](../../apps/frontend/src/components/chat/ChatPanel.tsx): estados, historial y envio.
6. [Evaluador](../../tools/assistant-eval.py): usa el chat nuevo, espera estado terminal y conserva recuperacion real.

## Arranque y demo

Preparar `.env` siguiendo el README y ejecutar `corepack pnpm local:prepare`
antes de `docker compose up --build`; o `corepack pnpm local:up`.
La preparacion crea una clave HMAC solo si no hay una configurada. No reemplaza
una clave existente ni regenera una ruta explicita desaparecida.
CD hace lo mismo en su directorio privado, fuera de las releases.

Prompts y tokenizer estan incluidos en las imagenes. El tokenizer se descarga
al construir desde una revision oficial fija y se verifica por SHA256.
Para pruebas fuera de Docker: `corepack pnpm tokenizer:prepare`.
La ejecucion posterior no descarga el tokenizer.

La demo utiliza el panel nuevo; `/assistant` redirige a ese panel. El endpoint
antiguo de mensajes rechaza la generacion de plantilla con 410; la consulta
estructurada de ownership conserva su contrato especifico.
La evaluacion funcional usa `tools/assistant-eval.py collect`, no ese endpoint.
Se conservan los limites de espera y el presupuesto configurado; no se promete
HA, ejecucion multiproceso ni exactitud financiera sin evidencia autorizada.

## Evidencias y decisiones

- [Correcciones actuales](../evidence/jup-035-review-improvements-20261012.md).
- [ADR del runtime](../adr/ADR-0019-conversational-runtime.md).
- [OpenSpec archivado](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/proposal.md).
- [Notas historicas](../evidence/jup-035-historical-notes.md) y
  [temas historicos](../evidence/jup-035-historical-topics.md).

Los ensayos anteriores, incluidos sus fallos, no se sobrescriben. Las referencias
a discos personales son antecedentes no portables; la guia actual permite
repetir la evaluacion desde el banco versionado sin copiarlos.
