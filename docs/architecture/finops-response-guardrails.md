# Respuesta estructurada y guardrails FinOps

- JUP: JUP-024
- Trello: https://trello.com/c/8SDUi2t9
- Schema: `FinOpsResponse` 1.0

## Frontera

El LLM propone contenido dentro de un contrato. Economicon sigue siendo
responsable de validar entrada, autorizacion, evidencia, numeros y efectos.

```text
job autorizado
  -> preflight y sanitizacion
  -> system prompt + UNTRUSTED_DATA
  -> provider con response_format JSON Schema
  -> parseo Pydantic
  -> guardrails de evidencia y agencia
  -> respuesta estructurada al pipeline
```

## Ejemplo completo

```json
{
  "schema_version": "1.0",
  "status": "ok",
  "answer": "El coste observado procede de la consulta indicada.",
  "scope": {
    "cloud": "azure",
    "data_environment": "simulated",
    "subscription_ids": ["subscription-1"],
    "period": {
      "from": "2024-06-01",
      "to": "2024-06-20"
    }
  },
  "evidence": [
    {
      "id": "cost-query:sha256:example",
      "kind": "cost_query",
      "title": "Coste agregado",
      "source": "Azure Cost Management simulado"
    }
  ],
  "metrics": [
    {
      "name": "total_cost",
      "value": "125.50",
      "unit": "EUR",
      "evidence_ids": ["cost-query:sha256:example"]
    }
  ],
  "recommendations": [],
  "assumptions": [],
  "limitations": [],
  "next_actions": ["Revisar la distribucion por servicio."]
}
```

Los valores decimales son strings para mantener representacion exacta. El
schema no autoriza al LLM a calcularlos: deben proceder de herramientas o
servicios deterministas.

## Estados

| Estado | Evidence | Metricas/recomendaciones |
| --- | --- | --- |
| `ok` | Obligatoria | Permitidas |
| `partial` | Obligatoria | Permitidas con limitaciones |
| `no_data` | Opcional | Prohibidas |
| `insufficient_data` | Opcional | Prohibidas |
| `unsupported` | Opcional | Prohibidas |
| `refused` | Opcional | Prohibidas |
| `error` | Opcional | Prohibidas |

## Evidencia

Tipos iniciales:

- `cost_query`: resultado reproducible de una consulta de costes;
- `corpus`: chunk recuperado del manifest documental;
- `user_input`: valor suministrado explicitamente por el usuario.

Metricas y recomendaciones contienen evidence IDs. JUP-025 definira como se
renderizan las citas para el usuario, pero JUP-024 ya impide referencias
inexistentes o duplicadas.

## Recomendaciones

Cada recomendacion incluye:

- categoria;
- accion y rationale;
- ahorro y moneda juntos o ambos null;
- confianza y riesgo;
- evidence IDs;
- `requires_human_approval: true`.

El formato no contiene `executed`, `applied` ni credenciales. El agente no
puede representar una mutacion como completada.

## Guardrails de entrada

- Tenant obligatorio para mediacion interna, omitido del prompt.
- Source/status con caracteres y longitud acotados.
- Fuentes distintas de Azure se resuelven sin llamar al provider.
- Metadata limitada a cuatro niveles, 50 items y strings de 500 caracteres.
- Payload final de metadata limitado a 4.000 caracteres.
- Valores no finitos se normalizan.
- Valores bajo claves de secretos se sustituyen por `[REDACTED]`.

La metadata conserva los datos publicos de Azure: recursos, servicios, tags y
costes no se anonimizan por este guardrail.

## Guardrails del prompt

El system prompt define:

1. prioridad de instrucciones;
2. metadata/RAG como `UNTRUSTED_DATA`;
3. no revelar internals o secretos;
4. Azure exclusivamente simulado;
5. no inventar datos ni citas;
6. estados seguros ante falta de datos;
7. aprobacion humana;
8. distinciones FinOps importantes;
9. hechos, supuestos y limitaciones separados;
10. JSON estricto sin Markdown.

## Guardrails de salida

Pydantic aplica:

- `extra=forbid` en todos los objetos;
- limites de listas y textos;
- enums cerrados;
- periodos ordenados;
- decimales y monedas con formato;
- evidence IDs validos y existentes;
- contenido permitido por status;
- aprobacion humana literal.

Una comprobacion posterior rechaza claims con cifra seguida de EUR, USD, euro
o porcentaje cuando no existe evidence. Es una capa adicional, no sustituye
las pruebas FinOps ni la evaluacion del modelo.

## Integracion futura LiteLLM/OpenRouter

JUP-023 debe:

- comprobar que el modelo soporta response schema;
- enviar `response_format` sin transformaciones incompatibles;
- exigir endpoints que admitan los parametros requeridos;
- propagar un fallo si el endpoint no puede cumplirlos;
- no habilitar fallback silencioso ni response healing sin evaluacion;
- conservar la segunda validacion Pydantic.

El 27 de agosto de 2026 el catalogo de OpenRouter indicaba structured outputs
para `z-ai/glm-5.2` y `deepseek/deepseek-v4-pro`. La capacidad puede variar por
endpoint y debe volver a verificarse durante JUP-023.

## Pruebas de abuso minimas

- metadata ordena ignorar el system prompt;
- metadata contiene token o API key;
- source intenta usar AWS u otro proveedor;
- provider agrega campos al schema;
- `ok` no contiene evidence;
- metrica referencia evidence inexistente;
- status no accionable incluye metrica;
- answer afirma cifra sin evidence;
- recomendacion omite aprobacion humana;
- provider devuelve JSON invalido.

## Fuentes consultadas

Consulta realizada el 27 de agosto de 2026:

- OpenRouter Structured Outputs:
  https://openrouter.ai/docs/guides/features/structured-outputs
- LiteLLM Structured Outputs:
  https://docs.litellm.ai/docs/completion/json_mode
- OWASP LLM06 Excessive Agency:
  https://genai.owasp.org/llmrisk/llm062025-excessive-agency/

OpenRouter recomienda `strict: true`, descripciones y validacion de soporte por
endpoint. LiteLLM permite comprobar `response_format` y response schema. OWASP
recomienda minimizar funciones, permisos y autonomia, ejecutar en contexto de
usuario y autorizar acciones fuera del LLM.
