---
name: spec-intake
description: Normaliza una historia de usuario dentro del workflow SDD de Economicon. Usar únicamente en INTAKE con el input.json generado por `sdd skill prepare` para completar alcance, criterios AC-* y preguntas bloqueantes.
---

# Spec Intake

Trabajar exclusivamente con el run preparado por el harness. Leer `input.json`, el user story indicado y la documentación declarada en `docs_context`.

## Procedimiento

1. Verificar que skill, HU, correlación y etapa coincidan con el input.
2. Aplicar la precedencia: workflow aprobado, arquitectura y ADRs, artefactos upstream, estado arquitectónico y código actual.
3. Normalizar contexto, objetivo, alcance y criterios `AC-*` sin introducir diseño técnico.
4. Registrar contradicciones como `DOC-CONFLICT` y bloquear si cambian el significado de la historia.
5. Escribir el candidato en `artifacts/` y `output.json` conforme a `skill/spec-intake/output@2.0.0`.

## Límites

Leer solo el scope, documentos aplicables y la HU. Escribir solo en staging. No aprobar, cambiar etapa, editar manifest ni tratar `sdd-planing.md` o `docs/rejected/` como normativa.
