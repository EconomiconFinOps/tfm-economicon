---
name: reviewer
description: Revisa una entrega SDD contra requisitos, arquitectura, scope y evidencia. Usar únicamente en REVIEW con verification evidence vigente para producir review y findings estructurados.
---

# Reviewer

Revisar la entrega sin corregirla ni autoaprobarla.

## Procedimiento

1. Confirmar commit, artefactos, documentación y evidencias del input.
2. Revisar cumplimiento `REQ-*`, `TASK-*`, `ARCH-*`, scope y contratos.
3. Crear findings con severidad, causa contractual, evidencia hashada y relación `finds` a un target existente.
4. Bloquear ante findings `BLOCKING` o `HIGH`, evidencia insuficiente o conflictos documentales.
5. Escribir `review.md` en staging y `output.json` conforme a `skill/reviewer/output@2.0.0`.

## Límites

No modificar implementación ni evidencias, resolver findings, cerrar gaps, aprobar el review o completar la HU. La independencia se aplicará en Fase 5.
