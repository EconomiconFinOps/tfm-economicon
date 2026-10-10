# Marca del frontend — JUP-112

Verificación: 2026-10-10 Europe/Paris. Encargo: «Implementa JUP-112 — Adaptar el
frontend a la guía de estilo e imagen de marca». Chat origen delegado:
`01a1248a-4e9e-7963-a891-5d8cb49345a6`; identificador propio no proporcionado.

- Tarjeta: https://trello.com/c/XTZU3vj3. Integración exclusiva consultada:
  `DockerServer:/home/danteadmin/economicon-collaboration`.
- Roles vigentes: Paris Arcos Martin liderazgo, Victor Mendez pairing,
  Alejandro Aguado revisión, Lucia Mateo validación. Cuenta de herramientas:
  `Iber1to`. Candidato en rama propia para responsable; no revisión propia,
  coautoría, aceptación o reasignación inferida.
- Copia aislada `tfm-economicon-jup112`, rama `feat/JUP-112-brand`, base
  `origin/develop` `c2995a1`. No PR JUP-112 existente al consultar títulos;
  checkout compartido no editado.
- JUP-099 / PR54 ya integrado: reutilizar tokens/guardianes. Dossier existente
  y assets oficiales, procedencia en [frontend-brand.md](../frontend-brand.md).
- [Diseño y contratos](../../openspec/changes/jup-112-brand-frontend/design.md):
  paleta clara, fuentes locales, responsive; API/rutas/cálculos intactos.
- JUP-056/JUP-058/JUP-089 tienen alcance funcional separado. Pendiente comprobar
  reconciliación sobre sus futuros heads; no se editan sus copias.
- Entrega: [PR draft #102](https://github.com/EconomiconFinOps/tfm-economicon/pull/102).
  Primer commit `105bcb0`; código final y evidencia en `58174df` (los commits
  posteriores pueden completar solamente enlaces documentales).
- [Nota de entrega Trello](https://trello.com/c/XTZU3vj3#comment-6ac9f0090d16be592106c9c6)
  publicada mediante la integración oficial el 2026-10-10. Recibo en el
  workspace: `materiales/07-evidencias/JUP-112-brand-2026-10-10/trello-receipt.json`.
- Evidencia: [informe](../evidence/JUP-112-validation.md), capturas portables y
  resúmenes JSON en `docs/evidence/JUP-112/`. Matriz visual 50 combinaciones a
  320/390/768/1440 px, sin overflow global, errores JS o fallos de fuentes.
  Contraste y evaluación visual favorable, API simulada. Preferencias de color
  iguales y máximo violeta observado 3,7647 %.
- Typecheck/lint/build frontend, OpenSpec 56/56, gobernanza 82/82 y trazabilidad
  pasan. CI inicial detectó cuatro expectativas antiguas de estilo; corregidas.
  Pruebas específicas 64/64 (guardia) y 61/61 (salud) pasan. Suite final completa:
  **55 archivos / 667 pruebas PASS**, timeout original, 241,78 s.
  Repetir desde `apps/frontend`: `node node_modules/vitest/vitest.mjs run --maxWorkers=1`.
- Limitaciones conservadas: sin backend real; Turbo toma pnpm11 fallback y falla
  en el entorno local. Se usan comandos Corepack9/directos para el frontend.

Estado CI: consultar los checks del head en PR102; al publicar el candidato
seguían ejecutándose. `JUP reviews` permanece pendiente de dictámenes humanos,
por lo que no equivale a un fallo de las 667 pruebas locales.

Próximo paso operativo: transferencia al responsable. Paris debe
reutilizar la contribución en PR propia o el equipo regularizar explícitamente
los roles: Alejandro conserva revisión, pero `Iber1to` publica este candidato y
no puede autoaprobarlo. Pairing, revisión, validación independiente, aceptación
de marca y merge quedan pendientes de personas responsables. No se modifica
estado, prioridad ni atribuciones de la tarjeta, ni se envían mensajes Discord.
