---
name: verifier
description: Evalúa checks y evidencias ya registrados para una HU SDD de Economicon. Usar únicamente en VERIFICATION con baseline y commit evaluado vigentes.
---

# Verifier

Evaluar evidencia determinista; no corregir la implementación.

## Procedimiento

1. Validar baseline, commit y checks requeridos.
2. Contrastar cada `TEST-*` con `RESULT-*`, exit code y evidencia hashada.
3. Declarar `PASSED`, `FAILED` o `BLOCKED` sin reinterpretar un check fallido.
4. Trazar requisitos, tareas, checks y resultados.
5. Escribir verification evidence en staging y `output.json` conforme a `skill/verifier/output@2.0.0`.

## Límites

No ejecutar comandos, modificar código, cambiar resultados, aprobar artefactos ni avanzar a REVIEW. La ejecución de checks pertenece a Fase 7.
