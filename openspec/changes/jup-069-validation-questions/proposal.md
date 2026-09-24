JUP: JUP-069
Trello: https://trello.com/c/Qi5uwxgW

## Why

El equipo necesita consultas FinOps con entradas y expectativas estables para
repetir las pruebas sin improvisar preguntas o confundir ejemplos con gasto real.

## What Changes

- Versionar 28 consultas representativas con contexto sintético, fuentes y rúbricas.
- Cubrir costes, allocation, tagging, budgets, anomalías, recomendaciones y límites.
- Validar estructura, cobertura y referencias; preparar prompts sin respuestas.
- Documentar protocolo de ejecución y transferencia a JUP-070 y JUP-071.

## Capabilities

### New Capabilities

- `finops-validation-questions`: contrato reproducible de preguntas de validación.

### Modified Capabilities

Ninguna.

## Impact

Solo datos de evaluación, documentación, herramienta Node sin dependencias nuevas
y checks en CI. No cambia runtime, ingesta, prompts del sistema ni corpus indexable.
No acredita calidad del asistente ni sustituye las evaluaciones JUP-070/JUP-071.
