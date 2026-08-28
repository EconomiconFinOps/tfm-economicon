# Evidencia de validacion JUP-084

- Fecha: 2026-08-27.
- Tarjeta: https://trello.com/c/m1i7iXBm.
- Rama: `docs/JUP-084-finops-agent-tool-contract`.
- Base: `origin/develop` en `a746d48`.
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/17.

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

La rama se publico y el pull request se abrio hacia `develop`. La tarjeta se
actualizo con rama, commit, PR, OpenSpec y evidencia, y paso a `En revision`.

No se ha implementado el runtime ni se han realizado llamadas LLM. No se ha
enviado ningun mensaje a Discord.

## Revalidacion de liderazgo - 2026-08-28

Alejandro Aguado reviso de nuevo el contrato completo contra `origin/develop`
y las fuentes oficiales vigentes. La comprobacion confirma que:

- OpenRouter conserva el patron de herramientas definidas por la aplicacion:
  el modelo propone la llamada y Economicon ejecuta la funcion localmente;
- OpenRouter permite desactivar llamadas paralelas, por lo que la linea base
  secuencial del contrato sigue siendo portable;
- LiteLLM documenta la deteccion de soporte de function calling y el ciclo de
  enviar herramientas, validar la propuesta, ejecutar y devolver el resultado;
- Azure Cost Management Query mantiene `Usage` como coste real, agregacion de
  `PreTaxCost`, moneda en la respuesta y un maximo de dos agrupaciones.

La validacion local repetida obtuvo 17/17 elementos OpenSpec validos,
trazabilidad JUP-084 correcta, 318 archivos aceptados por higiene, 7/7 pruebas
del validador JUP, 6/6 pruebas de higiene y `git diff --check` limpio. No se
realizaron llamadas autenticadas ni se consumieron creditos LLM.

Alejandro aprueba como lider el catalogo, la frontera de autorizacion, los
calculos deterministas, la trazabilidad y las limitaciones documentadas. Esta
aprobacion no acredita pairing de Victor, revision de Lucia ni validacion de
Paris; la tarea 3.5 y la revision protegida del pull request siguen pendientes.

## Participacion prevista

- Liderazgo: Alejandro Aguado.
- Pairing/coautoria: Victor Mendez.
- Revision de PR: Lucia Mateo.
- Validacion, pruebas y documentacion: Paris Arcos Martin.
