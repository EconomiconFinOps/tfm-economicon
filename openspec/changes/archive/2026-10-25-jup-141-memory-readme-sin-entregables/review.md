JUP: JUP-141
Trello: https://trello.com/c/2b2K962A/133-jup-141

# Revisión de jup-141-memory-readme-sin-entregables

## Resultado

Cambio solo documental, sin código de producto: no hay ciclo tester, coder, mutación ni QA. La comprobación independiente consistió en contrastar el README y el delta de spec con las fuentes.

## Cambios aplicados

- `docs/memoria/README.md`: eliminada la viñeta de exportaciones fechadas y manifiesto SHA-256 de «Dónde vive»; la viñeta de la memoria en «Para herramientas y asistentes» termina en «no se busca ni se regenera desde Git.».
- `specs/project-memory-governance/spec.md` (delta MODIFIED): el requisito «Dated exports are immutable and stay outside Git» pierde «next to the other final deliverables».

## Checklist

- [x] `docs/memoria/README.md` no contiene `06-entregables` ni «final deliverables» (búsqueda sin resultados).
- [x] Las viñetas editadas y sus vecinas son frases completas (lectura de «Dónde vive» y «Para herramientas y asistentes»).
- [x] El delta repite el requisito completo con sus dos escenarios; comparado con `openspec/specs/project-memory-governance/spec.md`, la única diferencia es la frase eliminada.
- [x] El diff de la rama solo toca `docs/memoria/README.md` y este change; `docs/evidence/`, `docs/continuidad/` y los demás changes de OpenSpec no se modifican.
- [x] No se crea `docs/evidence/JUP-141-validation.md`: es un cambio solo documental, y este `review.md` basta.
- [x] No se requiere ADR (ver `design.md`).

## Validación

- `corepack pnpm openspec:validate`: 93 aprobados, 0 fallidos.
- `corepack pnpm jup:check -- --change jup-141-memory-readme-sin-entregables`: OK, enlazado con Trello y completo.

## Verificación de la spec

Ningún requisito ni escenario de `project-memory-governance` nombra `materiales/06-entregables/`. Solo la frase genérica «next to the other final deliverables» del requisito de exportaciones apuntaba a la carpeta, y el delta la quita. Se conservan: fechadas, fuera de Git, SHA-256 en un manifiesto e inmutables.

## Findings aceptados (fuera de alcance)

- El README ya no describe el régimen de exportaciones, que la spec sigue exigiendo, y la sección «Revisión y validación del entregable» pide identificar la versión revisada por su SHA-256 sin explicar de dónde sale. Se repondría, si el equipo quiere, con una viñeta sin ruta en otro cambio.
- Las referencias históricas a la carpeta en `docs/evidence/`, `docs/continuidad/`, `jup-062-business-memory` y el review archivado de `jup-062-memory-source-rules` se mantienen como registro de hechos pasados.
- Menciones a «exportación» sin ruta en el README (líneas sobre revisión por fecha y SHA-256, lectura de una exportación completa y prohibición de guardar exportaciones en el repositorio): no se alinean aquí.

## Human Approval

- Change: jup-141-memory-readme-sin-entregables
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-10-25
- Adversarial review: no ejecutada; cambio solo documental, sin código de producto, y sin ciclo tester, coder, mutación ni QA. La comprobación independiente fue contrastar el README y el delta con la spec vigente (única diferencia: la frase «next to the other final deliverables»)
- Accepted findings: el README ya no describe el régimen de exportaciones que la spec sigue exigiendo; referencias históricas a la carpeta en evidencias, continuidad y changes de jup-062 sin tocar; menciones a «exportación» sin ruta en el README sin alinear
- Archive decision: archive
