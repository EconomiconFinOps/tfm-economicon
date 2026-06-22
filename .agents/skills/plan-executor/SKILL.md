---
name: plan-executor
description: Ejecuta tareas SDD que ya están RUNNING dentro del scope aprobado. Usar únicamente en EXECUTION con baseline vigente y un input.json preparado por el harness.
---

# Plan Executor

Implementar exactamente las tareas preparadas; el harness conserva la autoridad sobre sus estados.

## Procedimiento

1. Confirmar que cada tarea está `RUNNING`, sus dependencias están completas y el baseline sigue vigente.
2. Leer solo inputs declarados y modificar únicamente `requested_scope.write_paths`.
3. No ejecutar checks no autorizados; registrar solo resultados ya disponibles.
4. Crear evidencias para tareas `FAILED` o `BLOCKED` y un execution summary staged.
5. Emitir `output.json` conforme a `skill/plan-executor/output@2.0.0`.

## Límites

No modificar PRD, TDR, roadmap, backbone, manifest, journal ni archivos fuera de scope. No aprobar, reintentar ni completar tareas directamente; `submit` aplica solo transiciones `EX-*` válidas.
