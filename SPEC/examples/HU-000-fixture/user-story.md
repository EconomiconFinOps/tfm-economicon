---
artifact_schema_version: "1.0.0"
artifact_type: user-story
story_id: HU-000
documentation_consulted: []
architecture_invariants: []
traceability: [HU-000, AC-001, AC-002]
---
# HU-000 — Fixture del manifiesto SDD

## Contexto

El harness necesita un caso mínimo aislado para verificar la carga y validación de `manifest.yaml`.

## Objetivo

Demostrar que el estado de una HU de tipo `harness-docs` puede reconstruirse sin interpretar texto libre ni consultar memoria externa.

## Alcance

- Validar estructura, referencias, hashes, artefactos y políticas del manifiesto.
- No modificar aplicaciones ni comportamiento de runtime.

## Criterios de aceptación

- `AC-001`: el manifiesto cumple el schema `2.0.0`.
- `AC-002`: el validador confirma la aprobación vigente del workflow.
