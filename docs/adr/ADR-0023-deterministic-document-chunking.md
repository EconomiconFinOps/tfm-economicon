# ADR-0023: Chunks estructurales reproducibles desde normalizado durable

- Status: Proposed
- Date: 2026-10-16
- Related JUP/OpenSpec: JUP-125, [jup-125-deterministic-document-chunking](../../openspec/changes/archive/2026-10-16-jup-125-deterministic-document-chunking/design.md)
- Trello: https://trello.com/c/H0RUnArf
- Supersedes: none
- Superseded by: none

## Context

JUP-124 conserva texto/bloques normalizados después de retirar originales.
Una división por caracteres no garantiza máximo en tokens ni conserva las
relaciones necesarias para recuperar y citar tablas, listas o subsecciones.
Normalizado y anotaciones pueden tener distinta cobertura; el texto canónico
no debe reconstruirse a partir de anotaciones incompletas.

Registro retrospectivo de decisiones ya implementadas y autorizadas durante
la fase experimental del 15–16/10. El checkpoint R2 `5dc63747` conserva sus
correcciones evaluadas. Se formaliza una decisión duradera de RAG/persistencia,
sin nuevo diseño, proveedor, servicio o dependencia. Ratificación documental
no se presume por la aceptación técnica; permanece Proposed.

## Decision

1. Usar el texto normalizado durable como referencia de integridad y bloques
   disponibles como anotaciones. Conservar unidades estructurales que caben y
   dividir recursivamente con fallback determinista, sin llamadas a modelos.
2. Medir contenido efectivo con tiktoken 0.14.0/cl100k_base fijado por hash,
   preparado fuera de Git y cargado offline. Separarlo del tokenizer GLM de chat.
3. Guardar procedencia/rangos, repetición y fragmentos reproducibles por chunk,
   y metadata documental/manifiesto en el padre. IDs distinguen generaciones
   deterministas; un identificador operativo separado controla publicación CAS.
4. Preservar texto omitido de embeddings sólo cuando es blanco, con datos
   exactos de reconstrucción en el primer chunk. Orden/rangos/hash/count y grupos
   permiten reconstruir sin usar el padre para rellenar ni debilitar negativos.
5. Publicar padre/chunks/vectores atómicamente mediante extensión JSONB aditiva.
   Conservar lookup/citas legacy y limitar reprocess a petición autorizada desde
   checkpoint, sin reextracción o reindexación masiva automática.

## Consequences

- Recuperación y citas tienen procedencia verificable por texto, incluso con
  overlap, tablas o varias páginas; no se inventan ubicaciones ausentes.
- Un cambio de algoritmo/configuración/tokenizador puede producir otra generación;
  las citas históricas son snapshots y no se reescriben automáticamente.
- La metadata añade coste de almacenamiento; guardar blancos excluidos de vectores
  es necesario para reconstrucción exacta. No se duplica indiscriminadamente
  el documento ni se añaden títulos al contenido enviado al embedding.
- La carga falla si falta el recurso fijado. Preparación/build deben verificarlo
  fuera del checkout; no se versionan vocabularios, recursos generados o entornos.
- Estructura PDF/Word ambigua conserva warnings y fallback, no una garantía de
  reconstrucción del layout. Legacy sin descriptor sigue consultable, pero no
  promete reconstrucción exacta desde chunks solos.
- Se conservan ADR-0008/0011/0013/0017/0022 y sus estados: tenant, propiedad SQL,
  retrieval, mismo modelo y ciclo del normalizado. No se amplía a fase 3.

## Alternatives Considered

- Seguir con caracteres 500/50: se conserva como baseline de calibración, pero
  no satisface el presupuesto real de tokens y la procedencia estructural.
- Chunking semántico/agentic: fuera del alcance aprobado; introduciría modelos,
  coste y decisiones de corte distintas del contrato determinista.
- Volver a extraer o retener originales para reprocesar: contradice el checkpoint
  durable y el ciclo aprobado de JUP-124; no es necesario para esta etapa.
- Reindexar automáticamente legacy: descartado; compatibilidad y reprocess
  explícito preservan disponibilidad y control de datos/coste.

Estas alternativas explican la implementación, no benchmarks nuevos ni una
aprobación colectiva retroactiva.

## Evidence And Follow-up

[Matriz JUP-125](../evidence/JUP-125-validation.md),
[diseño](../../openspec/changes/archive/2026-10-16-jup-125-deterministic-document-chunking/design.md)
y [runbook](../runbooks/document-chunking.md). R1/A/B/R2 conservan sus FAIL y
correcciones; R2 tiene revisión y validación independientes favorables y control
PM. La base/documentación formal exige nueva decisión de vigencia por los roles.

La muestra real de seis documentos/doce preguntas mantiene Recall 12/12 en ambos
métodos y reduce 25 a 9 chunks; no prueba mejora general. No se ratifica este ADR,
no se acredita participación humana y no se archiva/publica desde este registro.
