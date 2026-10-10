# Recomendaciones de optimización — JUP-033

Verificado **10/10/2026**. [Trello](https://trello.com/c/ndrittYl), P1 Valor FinOps.
Encargo «Implementa JUP-033 — Generar recomendaciones de optimización»,
procedente del chat `01a1248a-4e9e-7963-a891-5d8cb49345a6`.

## Estado y decisiones

La autorización actual pide implementar; las notas históricas de no iniciar
código describían un encargo anterior. Tarjeta completa en
`materiales/07-evidencias/hito-mvp-2026-10-09/backlog-dispatch-source.json` del
workspace y contrastada en vivo por la integración oficial de DockerServer el
10/10: criterios genéricos, dependencias por refinar, sin cambios de prioridad,
fecha o roles. Alejandro lidera; Lucia pairing; Paris revisa; Victor valida.
Las asignaciones no acreditan participación realizada.

Sin rama/PR específica previa localizada. Copia propia `tfm-economicon-jup033`,
base `c2995a1`, rama `feat/JUP-033-recommendations`. Checkout compartido intacto.
[PR #97 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/97), código
validado `1c8dabf`; cambios posteriores sólo de documentación.
Trello **30 — En curso** mediante la integración oficial; comentario de entrega
`6ac9edbb7d64a2e99928110b` y enlaces de rama/PR/evidencia actualizados. Descripción
de criterios, prioridad, fechas y asignaciones preservadas. No Discord.

Implementado `GET /billing/recommendations` con periodo UTC obligatorio y
tenant autorizado. Una consulta existente por proyecto evita nueva SQL y
preserva controles de ingestas completadas/solapamientos. Reglas limitadas a
completar proyecto ausente y a investigar el mayor coste neto positivo por
moneda. No es un detector de desperdicio. IDs de candidato estables y evidencia
ligada a todos los grupos comparados; fuente simulada y calidad explícitas.

`estimated_savings` y su `currency` siempre null; importes observados separados.
Sin telemetría no se propone rightsizing, shutdown ni compromisos. No cambios
cloud, LLM, persistencia, aprobación automática o integración frontend.

## Fuentes y evidencia

- [Contrato para JUP-034/039/058](../architecture/optimization-recommendations.md).
- [Pruebas por criterio, versiones y límites](../evidence/JUP-033-validation.md).
- [Ejemplo sintético generado](../evidence/JUP-033-example.json).
- [OpenSpec archivado](../../openspec/changes/archive/2026-10-10-jup-033-optimization-recommendations/proposal.md)
  y [requisito canónico](../../openspec/specs/optimization-recommendations/spec.md).
- `python -m pytest tests/test_recommendations.py tests/test_recommendations_api.py -q`
  desde `apps/backend`: 30 pass; ejecución separada `-k real`: 3/3 Cockroach
  24.1.11 pasan. Instancia propia en memoria y túnel retirados.
- OpenSpec estricto 56/56; 95 pruebas de herramientas, trazabilidad y limpieza
  correctas; build4/4 con shim pnpm9 limitado al proceso por fallback del entorno.
- [CI Linux 38035246060](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035246060):
  backend928pass/37skip. Suite Windows general interrumpida67% con fallos:
  fixture de salud bloquea socket.connect usado por asyncio Windows; diagnóstico
  reproducido, módulos sin cambios. No afirmar regresión local verde.

## Próximos pasos

Pendientes pairing real de Lucia y dictámenes independientes de Paris/Victor;
`JUP reviews` falla
por su ausencia. No aceptación ni merge mientras falten. Los
consumidores JUP-034/039/058 deben integrar y probar este contrato en su alcance.
