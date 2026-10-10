# Dashboard operativo de costes — JUP-056

Verificación: 2026-10-10 (Europe/Paris). Origen: «JUP-056 — Diseñar dashboard operativo de análisis detallado», chat `01a124a6-3f2b-7452-9d53-403420b02851`; encargo desde `01a1248a-4e9e-7963-a891-5d8cb49345a6`.

## Alcance y decisiones confirmadas

- [Tarjeta](https://trello.com/c/4AbHqWKW), P1 Valor FinOps, sin fecha confirmada. Snapshot oficial `DockerServer:/home/danteadmin/economicon-collaboration/data/snapshots/snapshot-20261010T071423Z.json`; descripción/roles iguales al dispatch del 10/10. Victor lidera, Alejandro pairing, Lucia revisa y Paris valida. Ninguna atribución humana se da por realizada.
- Copia aislada `../tfm-economicon-jup056`, rama `feat/JUP-056-operational-analysis`, base `origin/develop` `c2995a1`. Sin rama/PR previa de JUP-056 encontrada. Checkout compartido intacto.
- La pantalla operativa era una demo estática. Agrupar el contrato v2 no permite combinar dimensiones: se añaden filtros AND de suscripción, servicio, proyecto y etiqueta antes de la agregación. Metadata de filtros protege frente a un backend anterior que los ignore.
- Se reutilizan API autenticada, React Query, componentes/tokens y precisión decimal por moneda. Cuenta significa suscripción Azure. No toca marca JUP-112, recomendaciones JUP-058 ni comportamiento ejecutivo.
- [OpenSpec](../../openspec/changes/jup-056-operational-analysis/proposal.md), [diseño](../../openspec/changes/jup-056-operational-analysis/design.md) y [evidencia por criterio](../evidence/JUP-056-validation.md).
- Implementación publicada en [PR #99 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/99), commit funcional `f1e0dd6`, como contribución para Victor. [CI técnica 7/7](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035433148): frontend 640 PASS, backend 909 PASS / 38 SKIP. Navegador con dobles PASS, 11 casos API nuevos y cuatro SQL nuevos con Cockroach real PASS; siete regresiones SQL previas PASS. Typecheck/lint/build correctos. Recibos conservan fallos de esperas de frontend local y fixture Windows/Python3.14 de salud ajeno al delta; no afirmar suite local completa verde.
- Entrega enlazada mediante integración oficial en [comentario Trello](https://trello.com/c/4AbHqWKW#comment-6ac9ee3cbd594dd83fa9eef2), 10/10 09:50 Europe/Paris. Lista Backlog, roles y criterios intactos. Contenedor/túnel SQL y servidor Vite propios retirados; sin deployment ni Discord.

## Pendientes

Victor revisa la contribución y dispone el OpenSpec activo antes de pasar a ready. Pairing humano, `Revision JUP-056` de Lucia, `Validacion JUP-056` de Paris y posterior merge pendientes. El gate `JUP reviews` falla por faltar esos dos dictámenes; no se elude. No se declara integración navegador-backend desplegado ni cobertura Azure real. Los commits posteriores de evidencia deben conservar idéntico código a `f1e0dd6` o requerir comprobación del delta.
