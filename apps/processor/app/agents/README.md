# Agents Module

Módulo interno del processor para encapsular la lógica LLM sin separarlo como servicio de red.

## Responsabilidades

- definir prompts y formato de salida
- seleccionar provider LLM
- exponer una interfaz Python estable para el processor

## Extensión

Para añadir una nueva estrategia de agente:

1. crear o extender el provider en `providers.py`
2. ajustar la plantilla en `service.py`
3. invocar el runtime desde `tasks/ingest.py` o desde un nodo del grafo

## Provider Actual

La v1 usa `mock` por defecto para que el stack arranque sin credenciales externas.

