JUP: JUP-124
Trello: https://trello.com/c/SEkdYIYs

# Ingesta documental avanzada

## Why

El producto necesita admitir archivos privados, extraer contenido localmente y
conservar una representación recuperable antes de ejecutar el RAG existente.
La etapa experimental autorizada se implementó y comprobó el 15/10/2026; sus
correcciones CD, de formato y de fixtures se completaron el 16/10/2026.

Este change se crea **retrospectivamente el 16/10/2026**, después de recibir
JUP-124. Describe la implementación existente en el commit local
`688dd7202bc9536f5bd6d4febafa3ee392764df5`; no simula un diseño OpenSpec anterior
al código ni convierte evaluaciones locales en revisiones humanas oficiales.

## What Changes

- Registrar los diez criterios de la tarjeta: formatos/OCR, admisión, aislamiento,
  almacenamiento, ejecución asíncrona, recuperación, limpieza, UI y operación.
- Documentar el contrato implementado: un archivo por envío, 20.000.000 bytes,
  reserva por usuario y original inmutable en MinIO privado del Compose general.
- Registrar extracción local aislada, documento normalizado durable y entrega
  compatible al pipeline actual, sin cambiar chunking, modelos o recuperación.
- Conservar las correcciones de credenciales/puertos CD, DOCX corruptos y
  fixtures de `local:doctor`, con evidencia histórica identificada.
- Formalizar la decisión duradera en ADR-0022 y su relación con ADR existentes.

## Capabilities

### New Capabilities

- `advanced-document-ingestion`: subida de archivos, extracción, almacenamiento
  temporal y normalización durable con recuperación y limpieza seguras.

## Impact

La implementación previa afecta backend, processor, UI de ingesta, MinIO,
migración aditiva 006, dependencias y herramientas CD/locales. **Este encargo de
formalización sólo modifica documentación**; no cambia producto, tests o política.

Quedan fuera chunking estructural de fase 2, recuperación híbrida de fase 3,
calidad semántica de modelos reales, AWS, despliegue productivo y nuevas campañas.
La PR se preparará hacia `develop`. Roles comunicados por el liderazgo el
16/10/2026: Paris Arcos lidera; Lucía Mateo pairing; Víctor Méndez revisión;
Alejandro Aguado validación/pruebas/documentación. La asignación no acredita
participación, pairing ni reviews realizados. Ratificación documental del ADR,
reviews humanas, aprobación final, archivo y publicación siguen separados.
No se archiva este change en la formalización.
