---
name: prd-generator
description: Genera un PRD trazable para una HU SDD de Economicon. Usar únicamente en PRD con una user story aprobada y un input.json preparado por el harness.
---

# PRD Generator

Consumir solo el input preparado y la user story aprobada referenciada por hash.

## Procedimiento

1. Confirmar etapa, hashes y aprobación upstream.
2. Derivar problema, objetivos, `REQ-*`, supuestos, exclusiones y criterios de aceptación.
3. Trazar cada requisito a la HU o a un `AC-*`; no decidir arquitectura ni implementación.
4. Registrar conflictos documentales y bloquear cuando impidan requisitos inequívocos.
5. Escribir `prd.md` en staging y `output.json` conforme a `skill/prd-generator/output@2.0.0`.

## Límites

No modificar user story, TDR, plan, código, manifest, aprobaciones ni etapa. No usar documentos rechazados como decisiones vigentes.
