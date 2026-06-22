---
name: tdr-generator
description: Produce el TDR técnico de una HU SDD de Economicon. Usar únicamente en TDR con PRD aprobado y contexto vigente de ARCHITECTURE.md, ADRs y architecture-status.md.
---

# TDR Generator

Diseñar contra el backbone, no contra atajos del código existente.

## Procedimiento

1. Validar PRD aprobado, documentos y scope del input.
2. Identificar `ARCH-*`, gaps y ADRs aplicables.
3. Definir `DEC-*`, componentes, datos, failure modes, observabilidad, migración, rollback, pruebas y riesgos.
4. Emitir `DOC-CONFLICT` bloqueante ante contradicciones normativas; nunca relajar una invariante sin ADR aprobada.
5. Escribir `tdr.md` en staging y `output.json` conforme a `skill/tdr-generator/output@2.0.0`.

## Límites

No planificar tareas, modificar código, aprobar el TDR ni avanzar la etapa. `sdd-planing.md` es solo referencia no normativa.
