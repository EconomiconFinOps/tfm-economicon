# JUP-056 — Evidencia de implementación

Fecha: 2026-10-10 (Europe/Paris). [Tarjeta](https://trello.com/c/4AbHqWKW).
Base: `c2995a1`, rama `feat/JUP-056-operational-analysis`, copia aislada.
Esta evidencia es de la contribución técnica asistida; no sustituye la
`Validacion JUP-056` asignada a Paris ni la revisión asignada a Lucia.
Victor conserva liderazgo y Alejandro pairing, ambos pendientes de acreditación
humana para esta entrega. No hay coautoría, aceptación o revisión humana inventada.

## Resultado y criterios

| Criterio de Trello | Evidencia y estado |
| --- | --- |
| Resultado funcional verificable | `/operational` reemplaza la demo: filtros conjuntos de cuenta/suscripción, servicio, proyecto y etiqueta sobre billing v2; periodos UTC, agrupación, totales por moneda y CSV del ámbito. Código y escenarios verificables entregados; ver recibos abajo. |
| Pruebas necesarias añadidas y en verde | CI técnica 7/7 sobre `f1e0dd6`: frontend 640 PASS, backend 909 PASS / 38 SKIP. Nuevas pruebas propias: frontend16, API11 y SQL4 PASS, con Cockroach real para SQL. Fallos/limitaciones locales conservados en los recibos; no se afirma verde local global. |
| Documentación y decisiones actualizadas | [Contrato](../api/operational-cost-filters.md), [guía frontend](../../apps/frontend/README.md#análisis-operativo-de-costes-jup-056), [OpenSpec](../../openspec/changes/jup-056-operational-analysis/proposal.md), [continuidad](../continuidad/dashboard-operativo-costes.md). |
| Pull request revisado y vinculado | [PR #99 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/99), contribución contra develop; revisión humana pendiente. No se marca este criterio como completado. |
| Validación funcional y evidencia enlazadas | Comprobación técnica reproducible en esta evidencia. Validación funcional atribuible a Paris pendiente; no se marca aceptación humana. |

## Comprobaciones comunes

[CI técnica completa](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035433148)
**7/7 SUCCESS** sobre `f1e0dd6f5231276b19e685203fda2c3a8c3b2f4a`;
[recibo de estado](jup-056/ci-f1e0dd6.json). El gate separado `JUP reviews`
falla exclusivamente por faltar `Revision JUP-056` y `Validacion JUP-056`,
confirmado en [su log](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035433157).
No se interpreta el CI como aceptación humana. La PR/evidencia está enlazada
en [Trello](https://trello.com/c/4AbHqWKW#comment-6ac9ee3cbd594dd83fa9eef2)
por el puente oficial, conservando lista y roles.

- `corepack pnpm install --frozen-lockfile --ignore-scripts`: correcto, lockfile intacto. Primer intento offline no encontró OpenSpec en caché; instalación autorizada posterior completada.
- `node tools/jup-check.mjs --all`: 9 cambios correctos, incluido JUP-056.
- `corepack pnpm openspec:validate`: **56/56**, estricto, sin fallos.
- `node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs`: **82/82**. El primer intento dentro del sandbox no pudo crear procesos (EPERM); la repetición autorizada pasó sin modificar pruebas.
- `node tools/jup-cleanup-check.mjs` y `git diff --check`: correctos. El primer intento de higiene quedó bloqueado por `spawnSync git EPERM`; repetición autorizada correcta.
- Entorno local: Windows, Node **24.14.1**, pnpm **9.0.0**, Playwright **1.61.0**. Frontend/SQL registran sus versiones específicas en los recibos.
- Pase estático independiente del delta: sin hallazgos graves en SQL/tenant, metadata, caché, selección/sesión y exportación. Sin ejecutar suites ni atribuir revisión humana.

## Recibos y reproducción

Backend: [resultados y comandos](jup-056/backend-results.md).
Frontend: [resultados y comandos](jup-056/frontend-results.md).

Navegador: [recibo JSON de solicitudes y comprobaciones](jup-056/browser-double-results.json),
[escritorio](jup-056/double-desktop.png), [filtros aplicados](jup-056/double-filtered.png),
[tablet](jup-056/double-tablet.png), [móvil](jup-056/double-mobile.png),
[CSV descargado](jup-056/double-filtered-export.csv), estados de
[carga](jup-056/double-loading.png), [error](jup-056/double-error.png),
[vacío](jup-056/double-empty.png) y [parcial](jup-056/double-partial.png).

Evaluación independiente técnica **PASS** en 1440, 768 y 375 px. Comprobados:
valores mayores que `MAX_SAFE_INTEGER`, negativo y cero; edición sin peticiones;
cinco parámetros conjuntos y `env` → `environment`; exportación del ámbito;
reset, tag incompleto, fechas inválidas; refetch, 503, vacío, parcial y cambio
de tenant. Cero `pageerror`. El primer arranque de Vite agotó la espera de 30 s;
después de comprobar HTTP 200, la repetición con límite de arranque de 120 s
completó los escenarios. No fue un fallo funcional acreditado.

El ancho del contenido operativo coincide con cada viewport. El shell común
mide 1134 px en 768/375 px, limitación RF-026-002 conservada; no es un PASS
responsive global. Refinamientos menores pendientes: contraste del icono nativo
de fecha, salto de moneda con importes extremos y pista visual de scroll en la
tabla móvil. No se modificó el shell compartido para resolverlos.

Las pruebas del frontend usan dobles HTTP explícitos. Los escenarios SQL sólo
se consideran ejecutados cuando el recibo confirma CockroachDB real; las pruebas
de autorización con SQLite/dobles no acreditan agregación SQL. No se ha probado
una sesión de navegador conectada al backend desplegado ni facturación Azure real.

## Límites y siguiente paso

- Cuenta = suscripción Azure; valores exactos, sin catálogo/autocompletado ni filtro de dimensión ausente. Backend JUP-056 necesario para filtrar; sin metadata el frontend rechaza el resultado.
- El periodo sin fecha se contabiliza por tenant completo; la cobertura de costes no equivale a una factura completa. Fuentes solapadas conservan error 409 aun cuando se filtra otra dimensión.
- La responsabilidad visual se limita a la pantalla operativa. RF-026-002 del shell móvil, marca JUP-112 y recomendaciones JUP-058 siguen separados.
- La evaluación independiente disponible utiliza un segundo agente del mismo proveedor; no se dispone de evaluador de otro proveedor. No equivale a una review humana.
- Pendientes: conformidad de liderazgo/pairing, disposición del OpenSpec activo para ready, `Revision JUP-056` de Lucia, `Validacion JUP-056` de Paris y posterior merge. No se mueve ni cierra la tarjeta desde la contribución y no se envía Discord.
