# JUP-061 — Auditoría del registro de decisiones

Verificación documental: 2026-10-01. Base `origin/develop` `de0d62e`.
[Tarjeta](https://trello.com/c/qXoHFxyy) · [inventario canónico](../adr/README.md) ·
[contrato de trabajo](../../openspec/changes/jup-061-architecture-decision-register/proposal.md).

## Método y resultado

1. Lectura viva de JUP-061 mediante `Settings`/`TrelloClient.get_cards()` del puente
   desplegado en `/home/danteadmin/economicon-collaboration` (DockerServer), usando
   `docker compose run --rm -T --entrypoint python collaboration -`. Sin API Trello
   alternativa ni escritura Discord. Se conservaron roles y aceptación pendiente.
2. `git fetch origin`, inventario de `docs/adr/` en develop y lectura de ADR/diseños,
   contratos y evidencia enlazada. Diez ADR integrados; ADR-0011 y ADR-0012 en las
   ramas abiertas JUP-096 y JUP-099. Se reservaron ambos números.
3. `gh pr list --repo EconomiconFinOps/tfm-economicon --state all --limit 80
   --json number,title,state,mergedAt,url,headRefName` y consultas `gh pr view`
   de #25/#51/#53/#54/#59. El índice distingue los merges observados y las reviews
   APPROVED de las notas antiguas en los documentos. No se solicitó nueva review
   ni se atribuyó actividad por los roles de Trello.
4. Tres justificaciones retrospectivas Proposed: pgvector, auth demo y Compose.
   Se conservan las fuentes de implementación y sus límites. No hay comparativa
   de motores, hosting productivo o presupuesto nuevo aprobados por esta auditoría.
5. Se reparan seis enlaces de ADR a OpenSpec archivado y se añaden referencias
   concretas de aceptación/evidencia a los registros que solo tenían referencias
   genéricas o notas anteriores a la integración.

## Comprobaciones ejecutadas

- OpenSpec `validate --all --strict --no-interactive`: **36/36 PASS**.
  Se usó el binario 1.8.0 ya instalado en el checkout principal, ejecutado desde
  esta rama; equivalente a `corepack pnpm openspec:validate` sin reinstalar paquetes.
- `node tools/jup-check.mjs --change jup-061-architecture-decision-register`: PASS.
- `node tools/jup-cleanup-check.mjs`: PASS.
- `git diff --check`: PASS.
- 109 rutas Markdown locales y 15 anchors de los documentos afectados: PASS, comprobados
  contra archivos/cabeceras del checkout; sin solicitar los enlaces externos de
  precios/proveedores. Las PR se verificaron con GitHub CLI autenticado.

Los tests de backend/frontend/processor y los smokes enlazados son evidencia
histórica de sus tareas. No se ejecutan de nuevo ni se presentan como pruebas
nuevas de producto en esta modificación documental.

## Límites y siguiente puerta

- No se cambia ningún estado Accepted/Proposed preexistente. ADR-0005 permanece
  Proposed pese al merge; requiere ratificación documental. ADR-0002 conserva
  sus condiciones explícitas de aceptación conjunta.
- PR #51, #53, #54 y #59 estaban abiertas al corte. No se atribuye su producto a
  develop. Las fuentes externas de los registros 0011/0012 y pgvector se fijan
  por commit para que la auditoría pueda reproducirse.
- La memoria canónica y su exportación no se han editado: este registro proporciona
  referencias reutilizables. La selección comparativa original de CockroachDB
  sigue sin evidencia localizada; se declara, no se inventa una motivación histórica.
- Revisión de Paris, validación de Victor y pairing de Lucia de JUP-061 pendientes
  de evidencia atribuible. Esta entrega no cierra la tarjeta ni fusiona el PR.

## Publicación y seguimiento

[PR #60](https://github.com/EconomiconFinOps/tfm-economicon/pull/60) publicada como
borrador contra develop. Trello actualizado mediante el puente autorizado y
releído: descripción/enlaces verificados, roles preservados, **30 — En curso**.
El trabajo documental está entregado; revisión, validación y ratificaciones humanas
siguen pendientes. No se ha enviado ningún mensaje a Discord ni realizado merge.

## Reconciliación y corrección del test — 02/10/2026

El usuario autorizó reconciliar develop y resolver el fallo de CI. Base consumida
`5a54ce2ed9001dfb9d4b9d8e06eae84cffe91124`; merge local `2650e69`.
El único conflicto, ADR-0004, se resolvió conservando aprobación de JUP-094 y
seguimiento de tokens/atribuciones de JUP-099. ADR-0011/12 ya están integrados en
la base; el índice enlaza sus archivos locales y conserva el corte anterior.

CI anterior fallaba con `{ sessionExpired: true }` en la aserción inmediata tras
encontrar Sign in. Encontrar el botón acredita render, pero no finalización del
efecto de limpieza/navegación. Se espera con waitFor el estado null del router
antes de observar el historial. No cambia LoginPage ni se añaden sleeps/retries
al test. Se preserva la captura completa de transiciones al navegar hacia atrás.

Comprobaciones del incremento:

- Antes de editar, las dos suites dirigidas pasaron 10/10: el fallo de CI no se
  reprodujo en esa ejecución local. Se corrige la precondición asíncrona observable.
- Test corregido: tres ejecuciones dirigidas PASS.
- Mutantes manuales `replace:false` y opciones `{}`: ambos detectados por la
  aserción original not.toContainEqual de las transiciones de historial. El
  producto fue restaurado íntegramente tras cada prueba; diff de LoginPage vacío.
- Primera suite completa con concurrencia automática y lint/tipos simultáneos:
  430 PASS y 7 FAIL, con timeouts y elementos ausentes. No se cuenta como PASS.
- Reejecución aislada `corepack pnpm --filter @finops/frontend test -- --maxWorkers=2`:
  **437/437 PASS, 47/47 archivos**, 86,40 s. Los fallos anteriores son compatibles
  con carga local, sin acreditar una causa exhaustiva para cada uno.
- Frontend lint, typecheck y build PASS; build conserva aviso de bundle >500 kB.
- OpenSpec estricto **37/37 PASS**; trazabilidad e higiene PASS (724 archivos).
- 115 rutas Markdown locales verificadas en el delta; diff check PASS.

Logs dirigidos, controles negativos y suite acotada conservados fuera de Git en
`materiales/07-evidencias/JUP-061-reconciliacion-2026-10-02/` dentro del workspace.
La corrección del test amplía el alcance inicial documental por autorización
expresa del 02/10; no modifica contrato ni comportamiento del login.
