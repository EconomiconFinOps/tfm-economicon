# Landing pública — JUP-089

Verificado: 10/10/2026, Europe/Paris. Origen: encargo «Implementa JUP-089 — Crear
landing promocional pública de Economicon», chat `01a124a7-4af8-7670-9259-833c09c68477`.
Dispatch desde chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`.

## Alcance y decisiones

- [Tarjeta](https://trello.com/c/fD7nJKRl), P1 Valor FinOps. Descripción/roles
  contrastados el 10/10 07:21 Z exclusivamente mediante DockerServer. M4 funcional,
  M5 RC1 y dominio siguen dependencias; no se declara cierre de tarjeta.
- Nueva app estática `apps/landing`, separada de frontend/API/sesión. Reutiliza
  marca del dossier coherente con JUP-112, fuentes autoalojadas, mockup conceptual
  y captura histórica con API simulada. No se editó `apps/frontend`.
- [ADR-0018 Proposed](../adr/ADR-0018-public-landing-boundary.md) y
  [OpenSpec](../../openspec/changes/jup-089-public-landing/proposal.md).
  Preview noindex; dominio y vídeo se habilitan solo mediante configuración pública
  explícita. La validación de URL no prueba titularidad ni disponibilidad.

## Entrega y evidencia

Worktree aislado `tfm-economicon-jup089`, rama
`feat/JUP-089-economicon-promotional-landing`, base `origin/develop` c2995a1.
Checkout compartido preservado. [PR #106 en borrador](https://github.com/EconomiconFinOps/tfm-economicon/pull/106),
implementación publicada en `6966109`. [Nota de entrega en Trello](https://trello.com/c/fD7nJKRl#comment-6ac9ef25add980965e1843c6)
registrada el 10/10 a las 07:54:13 Z mediante la integración oficial; sin cambios
de roles, lista, prioridad ni fechas. La [CI general](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38036100966)
y el [workflow de landing con Node 22](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38036100954)
pasaron sobre `ffbeb0a`, el 10/10. El único control fallido fue
[JUP reviews](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38036100924):
faltan `Revision JUP-089` y `Validacion JUP-089` de personas distintas del autor.
Esto sustituye el estado de CI pendiente de la nota inicial de Trello. El registro
documental posterior no cambia código ni pruebas. Recibo local:
`materiales/07-evidencias/JUP-089-landing-2026-10-10/github-checks-ffbeb0a.json`.

[Evidencia](../evidence/JUP-089-validation.md)
y [runbook](../operations/public-landing.md). Build, 14 tests de landing, lint y
OpenSpec 56/56 correctos; frontend 629/629 en ejecución serial tras timeouts del
intento concurrente, build correcto. Navegador cuatro anchuras sin overflow e infracciones
axe tras corregir contraste. Fuentes WOFF2 suman 70.544 bytes. Pruebas anteriores
de producto y vídeo silenciado mantienen su fecha/alcance; no se convierten en
verificación de producción.

Ejecutar desde esta copia:

```sh
node apps/landing/build.mjs
node apps/landing/serve.mjs
```

Abrir `http://127.0.0.1:4179`. La preview es local, no exposición pública.

## Roles y siguiente paso

Trello propone Paris liderazgo, Victor pairing, Alejandro revisión y Lucia
validación. La preparación técnica asistida con cuenta Iber1to no acredita
participación ajena, no reasigna el liderazgo y no permite al autor revisar su
propia PR. Contribución en borrador para adopción/reasignación explícita por el
equipo. Dominio/responsable renovación/hosting, HTTPS, audio/subtítulos del vídeo,
M4/M5, revisión y validación humanas pendientes. Sin mensajes Discord.
