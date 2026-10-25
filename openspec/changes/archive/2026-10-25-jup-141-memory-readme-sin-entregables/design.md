JUP: JUP-141

## Context

Ver `proposal.md` (Why). El estado actual es el siguiente:

- `docs/memoria/README.md` cita `materiales/06-entregables/` en dos viñetas: la de exportaciones fechadas de «Dónde vive» y la de «Para herramientas y asistentes» que equipara esas exportaciones con la memoria.
- El requisito «Dated exports are immutable and stay outside Git» de `openspec/specs/project-memory-governance/spec.md` exige que cada exportación vaya fechada, se guarde fuera de Git «next to the other final deliverables», tenga su SHA-256 en un manifiesto y no se edite una vez registrada. No nombra la ruta, y ningún escenario exige que el README documente las exportaciones.
- El requisito de revisión de la misma spec pide identificar la versión revisada por su fecha y su SHA-256, y el README lo repite en «Revisión y validación del entregable».
- La carpeta cae fuera del repositorio, así que no hay nada que comprobar ni validar sobre ella desde aquí.
- Otros documentos versionados citan la carpeta como registro de hechos pasados: `docs/evidence/`, `docs/continuidad/`, `openspec/changes/jup-062-business-memory/` y el review archivado de `jup-062-memory-source-rules`.

## Goals / Non-Goals

**Goals:**

- Que `docs/memoria/README.md` no contenga la cadena `06-entregables`.
- Que las dos viñetas afectadas, y el resto del README, sigan siendo frases completas y coherentes.

**Non-Goals:**

- No se retira ni se debilita el régimen de exportaciones (fechadas, fuera de Git, SHA-256 en un manifiesto, inmutables): solo deja de describirse en el README y de ubicarse junto a los entregables finales.
- No se reescriben los registros históricos que citan la carpeta.
- No se alinean las menciones a «exportación» que no nombran la ruta (revisión por fecha y SHA-256, lectura de una exportación completa, prohibición de guardar exportaciones en el repositorio).

## Decisions

### D1. Eliminar la viñeta completa y no reescribirla sin ruta

Se borra la viñeta de exportaciones de «Dónde vive» en lugar de dejarla sin la ruta. Es lo que pide la tarjeta, y evita mantener en el repositorio la descripción de un proceso que ocurre fuera de él.

Alternativa descartada: reponerla como «las exportaciones fechadas se guardan fuera de Git, con su SHA-256 en un manifiesto, y no se editan». Elimina el desfase con la spec, pero contradice la petición de borrar la viñeta.

### D2. Delta mínimo: quitar «next to the other final deliverables» del requisito de exportaciones

Ningún requisito ni escenario de `project-memory-governance` nombra la ruta ni exige que el README documente las exportaciones. Pero el requisito «Dated exports are immutable and stay outside Git» las ubica «next to the other final deliverables», que es la misma referencia a la carpeta en forma genérica. Se modifica solo esa frase con un delta MODIFIED que conserva el requisito completo y sus dos escenarios.

Alternativas descartadas:

- `skip_specs: true`: `tools/jup-check.mjs` exige al menos un delta spec y no respeta ese marcador, y los cambios de documentación anteriores (por ejemplo JUP-138) llevan delta.
- Retirar el requisito de exportaciones: sería un cambio de fondo (un MODIFIED no puede eliminar escenarios, habría que usar REMOVED más ADDED con nombre nuevo) y excede esta tarjeta.
- Un requisito nuevo sobre el contenido del README: dejaría una spec sobre algo accidental.
- Cambiar `jup-check` para respetar `skip_specs`: amplía el alcance a tooling compartido.

### D3. Cláusula de «Para herramientas y asistentes»

La viñeta termina en «no se busca ni se regenera desde Git.». Se quita la equiparación entre las exportaciones y la memoria porque dependía de la ruta. La regla sobre qué puede leer una herramienta sigue en la spec y en las viñetas posteriores, que hablan de «una exportación completa» sin citar la carpeta.

### D4. Los registros históricos no se tocan

Las evidencias, la continuidad y los changes archivados describen lo que pasó con rutas concretas. Editarlos reescribiría el historial y la trazabilidad de JUP-062, JUP-063 y JUP-111.

No se requiere ADR: no es una decisión arquitectónica duradera ni transversal, y no se crea `docs/adr/` para este cambio.

## Risks / Trade-offs

- [El README deja de describir un requisito que la spec sigue exigiendo (exportaciones fechadas, fuera de Git, con manifiesto SHA-256 e inmutables)] → El requisito no se pierde: sigue en `project-memory-governance`, que es su fuente. Si el equipo quiere volver a documentarlo, se repone una viñeta sin ruta en otro cambio.
- [La spec ya no dice dónde se guardan las exportaciones, solo que es fuera de Git] → Es intencionado: la ubicación concreta la decide el equipo fuera del repositorio.
- [La sección «Revisión y validación del entregable» pide identificar la exportación revisada por su SHA-256 sin explicar de dónde sale] → La spec lo define; queda como mención pendiente fuera de alcance.
- [Referencias históricas a una carpeta que el README ya no describe] → Son registros fechados de hechos pasados y se aceptan como están.

## Open Questions

- ¿Se repone en otro cambio una viñeta sin ruta con el régimen de exportaciones, o se retira el requisito de la spec? No altera ni las specs ni este cambio, así que se puede decidir después.
