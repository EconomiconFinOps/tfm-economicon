JUP: JUP-084
Trello: https://trello.com/c/m1i7iXBm

## Why

Economicon describe capacidades FinOps y dispone de piezas de ingesta, RAG y
proveedores LLM, pero no tiene un contrato unico que determine que operaciones
puede solicitar el modelo, que argumentos acepta cada una ni que evidencia debe
acompanar sus resultados. Sin esa frontera, JUP-023, JUP-024 y las historias
funcionales JUP-026 a JUP-039 pueden implementar interfaces incompatibles o
delegar calculos monetarios al LLM.

## What Changes

- Definir las funciones de usuario del agente para visibilidad, comparacion,
  KPIs, tagging, proyeccion, anomalias, conocimiento y recomendaciones.
- Versionar un catalogo inicial de herramientas con entradas estrictas,
  resultados comunes, estados de disponibilidad y limites de ejecucion.
- Separar seleccion y explicacion LLM de consultas y calculos deterministas.
- Inyectar tenant, usuario, roles y correlation ID desde la sesion autenticada.
- Documentar capacidades condicionadas por datos, futuras y expresamente
  prohibidas.
- Fijar una politica portable de tool calling para GLM-5.2 y DeepSeek mediante
  LiteLLM y OpenRouter.

## Capabilities

### New Capabilities

- `finops-agent-tool-contract`: frontera funcional, contratos de herramientas,
  autorizacion, trazabilidad, limites y comportamiento ante datos insuficientes.

### Modified Capabilities

- Ninguna. Este cambio prepara implementaciones posteriores sin modificar el
  runtime actual.

## Out of Scope

- Implementar el bucle de tool calling o sustituir el proveedor mock.
- Crear endpoints, tablas, presupuestos, forecasts o algoritmos de anomalias.
- Ejecutar SQL, HTTP, shell, busqueda web o mutaciones Azure desde el modelo.
- Afirmar rightsizing sin telemetria de utilizacion.
- Aplicar recomendaciones o escribir en sistemas externos.

## Impact

La especificacion afecta al diseno de JUP-023 a JUP-039, al servicio del
asistente, a los calculos FinOps y a la evaluacion de ambos modelos. No cambia
APIs ni despliegues en esta tarjeta. Se alinea con ADR-0001 para el Azure
simulado y ADR-0002 para LiteLLM, OpenRouter, GLM-5.2 y DeepSeek.
