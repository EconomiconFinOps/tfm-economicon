# Decisiones técnicas

Actualizado/verificado: 2026-10-01. Origen: JUP-061 — Documentar decisiones técnicas,
chat `01a0f8dc-a64b-7e93-8f96-a146b08bf612`.

- Problema: decisiones dispersas, enlaces rotos por archivo OpenSpec y estado
  histórico presentado como actual. Alcance documental, sin cambiar el producto.
- Fuente única: [índice ADR](../adr/README.md); razones y alternativas en cada fuente,
  aprobación/integración separadas. [Evidencia](../evidence/JUP-061-validation.md).
- Rama `docs/JUP-061-architecture-decision-register`, base `de0d62e` de develop.
  Se preservó el checkout JUP-021 y su documentación local sin modificarlo.
- Trello leído exclusivamente mediante el puente DockerServer en
  `/home/danteadmin/economicon-collaboration`; tarjeta https://trello.com/c/qXoHFxyy.
- 10 ADR integrados y 2 en PR abiertas; nuevos ADR-0013/14/15 documentan razones de
  pgvector, auth demo y Compose como Proposed. No inventan aprobaciones ni cambian
  contratos. ADR-0002/0005 conservan Proposed. Razón comparativa original de
  CockroachDB y hosting productivo siguen sin evidencia localizada.
- PR #53 tiene validación APPROVED de Victor al corte (01/10); aún abierta. PR #51
  y #54 también abiertas con aprobaciones; #59 abierta. Esto supera los estados
  más antiguos de otras notas locales, sin afirmar integración.
- Siguientes pasos: revisión Paris, validación Victor y pairing Lucia según Trello;
  ratificar propuestas con evidencia, reconciliar merges y usar enlaces desde la
  memoria canónica. No se acredita participación humana por asignar esos roles.
- Reproducción: `node tools/jup-check.mjs --change jup-061-architecture-decision-register`,
  `corepack pnpm openspec:validate`, `node tools/jup-cleanup-check.mjs`.

## Publicación y seguimiento

[PR #60](https://github.com/EconomiconFinOps/tfm-economicon/pull/60) publicada como
borrador contra develop. Trello actualizado mediante el puente autorizado y
releído: descripción/enlaces verificados, roles preservados, **30 — En curso**.
El trabajo documental está entregado; revisión, validación y ratificaciones humanas
siguen pendientes. No se ha enviado ningún mensaje a Discord ni realizado merge.

## Solicitudes formales — 01/10/2026

El usuario autorizó pasar la PR a lista para revisión y solicitar ambas revisiones.
PR #60 ya no es draft; review requests enviadas a ParisArcos y Victorh1397.
[Solicitud publicada](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#issuecomment-5939532783):
Paris revisa coherencia/ratificación de ADR; Victor valida criterios y evidencias.
Se señalan ADR-0013/14/15, estado de ADR-0005 y aceptación conjunta separada de ADR-0002.
Trello actualizado por DockerServer y releído en **40 — En revisión**, roles intactos.
Este estado sustituye el borrador/30 anterior. Pendientes las respuestas humanas;
no se acredita aprobación, pairing, merge ni cierre. No se envió mensaje a Discord.
