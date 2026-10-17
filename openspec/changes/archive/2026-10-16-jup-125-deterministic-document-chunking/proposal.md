JUP: JUP-125
Trello: https://trello.com/c/H0RUnArf

# Chunking documental determinista y enriquecido

## Why

La división por caracteres no conserva de forma suficiente la estructura y la
procedencia necesarias para recuperar y citar documentos. La etapa 2 consume
el normalizado durable de JUP-124 y conserva contenido, relaciones disponibles,
límites por tokens y compatibilidad con documentos ya indexados.

Este change se formaliza **retrospectivamente el 16/10/2026**, después de la
implementación experimental autorizada del 15–16/10 y de sus correcciones
independientemente evaluadas. No representa un diseño OpenSpec anterior al
código. La rama normativa es `feat/JUP-125-deterministic-document-chunking`;
su checkpoint R2 es `5dc6374743f66370c9f50ade1a73abc287d329e5`.

## What Changes

- Registrar los quince criterios oficiales, incluidas recuperación legacy real,
  nueve formatos con extracción identificada, reconstrucción desde chunks y
  correspondencia textual de rangos/citas.
- Documentar `structural_recursive/1.0.1`: estructura y recursión por formato,
  objetivo 600/máximo 800 tokens, overlap configurable y metadatos reproducibles.
- Conservar normalizado v1, sustitución atómica de generación, aislamiento tenant,
  reprocesamiento explícito y lectura compatible de vectores/chunks antiguos.
- Registrar preparación offline de cl100k_base y la decisión duradera existente
  en ADR-0023 Proposed, sin ratificar otras decisiones.
- Enlazar evidencia y límites de campañas anteriores y de la formalización,
  preservando informes adversos y diferenciando evaluaciones locales y humanas.

## Capabilities

### New Capabilities

- `deterministic-document-chunking`: fragmentación estructural determinista,
  metadatos/procedencia y reconstrucción exacta del contenido normalizado.

## Impact

La implementación existente afecta processor, publicación vectorial, metadata,
citas backend, migración aditiva 003, locks/tokenizador, Compose/CI y smoke.
**Esta formalización sólo modifica documentación.** El código de chunking,
fixtures y corpus quedan intactos. La base incorpora el arreglo de sandbox de
JUP-124 evaluado separadamente; no se rediseña ni desactiva ese límite.

Dependencia: JUP-124/PR #133, en borrador y sin integración confirmada en develop
al recibir el encargo del 16/10. Los cambios de base se identifican en la evidencia;
una rama dependiente no equivale a un merge oficial. La PR de JUP-125 se preparará
hacia `develop`. Tras las evaluaciones locales y el control PM, Paris autorizó
el archivo el16/10/2026; la publicación de PR espera la presentación de su mensaje.

Roles proporcionados por PM: Paris Arcos, liderazgo; Víctor Méndez, pairing;
Lucía Mateo, revisión; Alejandro Aguado, validación/pruebas/documentación.
Asignación no acredita aportaciones ni reviews realizadas. Fuera de alcance:
nuevos lectores/OCR, modelos/dimensiones, contextualización de embeddings,
recuperación híbrida/BM25, reranking, prompts, producción y fase 3.
