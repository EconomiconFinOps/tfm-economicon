# Evidencia de validacion JUP-084

- Fecha: 2026-08-27.
- Tarjeta: https://trello.com/c/m1i7iXBm.
- Rama: `docs/JUP-084-finops-agent-tool-contract`.
- Base: `origin/develop` en `a746d48`.
- Pull request: pendiente de publicacion.

## Alcance validado

- Funciones de usuario y catalogo de herramientas del agente FinOps.
- Contexto de autorizacion inyectado por el backend.
- Consultas y calculos deterministas separados de la explicacion LLM.
- Resultados comunes con fuente, evidence IDs, supuestos y limitaciones.
- Herramientas contratadas, condicionadas, futuras y prohibidas.
- Portabilidad secuencial para GLM-5.2 y DeepSeek.
- Restricciones derivadas de los 19 dias del dataset y ausencia de telemetria.

## Investigacion externa

El 27 de agosto de 2026 se contrasto el contrato con documentacion oficial de:

- FinOps Framework y sus capacidades de Reporting, Allocation, Budgeting,
  Forecasting, Anomaly Management y Usage Optimization.
- Azure Cost Management Query.
- LiteLLM Function Calling.
- OpenRouter Tool Calling y catalogo publico de modelos.

El catalogo de OpenRouter declaro `tools`, `tool_choice` y salidas estructuradas
para `z-ai/glm-5.2` y `deepseek/deepseek-v4-pro`. El contrato no depende de
llamadas paralelas para mantener una base portable.

## Resultados

| Comprobacion | Resultado |
| --- | --- |
| OpenSpec estricto | 17 cambios/especificaciones validos, 0 fallos |
| Trazabilidad `jup:check` | JUP-084 enlazada y completa |
| Higiene `jup:cleanup:check` | 317 archivos aceptados |
| Tests de validadores JUP e higiene | 13 superados, 0 fallos |
| `git diff --check` | Sin errores |

No se ha implementado el runtime ni se han realizado llamadas LLM. No se ha
enviado ningun mensaje a Discord.

## Participacion prevista

- Liderazgo: Alejandro Aguado.
- Pairing/coautoria: Victor Mendez.
- Revision de PR: Lucia Mateo.
- Validacion, pruebas y documentacion: Paris Arcos Martin.
