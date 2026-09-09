JUP: JUP-024
Trello: https://trello.com/c/8SDUi2t9

## Why

El agente del processor devuelve actualmente un texto libre y su prompt acepta
metadata sin una frontera explicita. Esto no permite validar cifras, evidencia,
recomendaciones ni estados de datos insuficientes, y prepara mal la integracion
real de LiteLLM/OpenRouter. Economicon necesita una respuesta versionada y
guardrails verificables antes de habilitar modelos reales y tool calling.

## What Changes

- Definir `FinOpsResponse` version 1.0 con scope Azure simulado, evidencia,
  metricas, recomendaciones, supuestos, limitaciones y siguientes acciones.
- Generar un `response_format` JSON Schema estricto y validar de nuevo con
  Pydantic toda respuesta del provider.
- Sustituir el prompt generico por un prompt de sistema FinOps con jerarquia de
  instrucciones y limites del MVP.
- Tratar metadata como datos no confiables, redactar claves asociadas a secretos
  y omitir el identificador del tenant en el prompt.
- Rechazar fuentes no Azure, campos adicionales, cifras sin evidencia,
  referencias inexistentes y recomendaciones sin aprobacion humana.
- Actualizar el provider mock y cubrir el contrato con pruebas unitarias.

## Capabilities

### New Capabilities

- `finops-response-guardrails`: salida estructurada, prompt de sistema,
  prevalidacion, postvalidacion y comportamiento seguro del agente FinOps.

### Modified Capabilities

- Ninguna especificacion base. La integracion real de proveedor continua en
  JUP-023 y el renderizado final de citas en JUP-025.

## Out of Scope

- Implementar el cliente real LiteLLM/OpenRouter o consumir creditos.
- Implementar tool calling o las herramientas definidas en JUP-084.
- Detectar semanticamente toda prompt injection mediante listas de palabras.
- Aplicar recomendaciones, modificar Azure o habilitar busqueda web.
- Cambiar el contrato HTTP del backend o la interfaz del frontend.

## Impact

Afecta al modulo `apps/processor/app/agents`, a su salida interna y a las
pruebas del processor. El campo libre `insight` se sustituye por un objeto
`response` versionado dentro del resultado del agente. No existen consumidores
externos del campo anterior en el repositorio.
