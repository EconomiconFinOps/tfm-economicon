# Agents Module

Módulo interno del processor para encapsular la lógica LLM sin separarlo como servicio de red.

## Responsabilidades

- definir el prompt de sistema y el contrato estructurado de salida
- validar respuestas del proveedor con Pydantic y guardrails locales
- seleccionar provider LLM
- exponer una interfaz Python estable para el processor

## Contrato de respuesta

`FinOpsResponse` usa schema version `1.0`, rechaza campos adicionales y separa:

- respuesta y scope Azure simulado;
- evidencia y metricas referenciadas;
- recomendaciones sujetas a aprobacion humana;
- supuestos, limitaciones y siguientes acciones.

El runtime pasa un `response_format` JSON Schema estricto al provider y vuelve
a validar el JSON recibido. Una respuesta no accionable no puede incluir
metricas ni recomendaciones, y una cifra sin evidencia estructurada se rechaza.

## Guardrails

- El tenant se valida en la aplicacion y no se incluye en el prompt.
- Solo se acepta el alcance Azure simulado del MVP.
- Metadata y documentos recuperados se tratan como datos no confiables.
- Claves de metadata asociadas a secretos se redactan antes de invocar el LLM.
- No se permiten recomendaciones sin evidencia y aprobacion humana.
- Datos insuficientes producen una respuesta explicita, no cifras inventadas.

## Extensión

Para añadir una nueva estrategia de agente:

1. crear o extender el provider en `providers.py`
2. ajustar la plantilla en `service.py`
3. invocar el runtime desde `tasks/ingest.py` o desde un nodo del grafo

## Provider Actual

La v1 usa `mock` por defecto para que el stack arranque sin credenciales externas.

