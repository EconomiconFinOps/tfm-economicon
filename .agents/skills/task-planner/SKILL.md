---
name: task-planner
description: Convierte un TDR aprobado en roadmap y tareas SDD ejecutables. Usar únicamente en PLAN con el input.json generado por el harness.
---

# Task Planner

Descomponer el diseño aprobado sin reabrir decisiones técnicas.

## Procedimiento

1. Verificar TDR, decisiones, scope y restricciones.
2. Crear roadmap y tareas `TASK-*` pequeñas, con dependencias acíclicas, paths y checks `TEST-*`.
3. Asegurar cobertura de `REQ-*`, `DEC-*` y `ARCH-*` mediante trazabilidad.
4. Marcar paralelismo solo cuando los scopes de escritura no se solapen.
5. Escribir roadmap y tasks en staging y `output.json` conforme a `skill/task-planner/output@2.0.0`.

## Límites

No editar PRD/TDR, ejecutar tareas, cambiar scope aprobado, aprobar artefactos ni avanzar a EXECUTION.
