# JUP-061 â€” AuditorÃ­a del registro de decisiones

VerificaciÃ³n documental: 2026-10-01. Base `origin/develop` `de0d62e`.
[Tarjeta](https://trello.com/c/qXoHFxyy) Â· [inventario canÃ³nico](../adr/README.md) Â·
[contrato de trabajo](../../openspec/changes/jup-061-architecture-decision-register/proposal.md).

## MÃ©todo y resultado

1. Lectura viva de JUP-061 mediante `Settings`/`TrelloClient.get_cards()` del puente
   desplegado en `/home/danteadmin/economicon-collaboration` (DockerServer), usando
   `docker compose run --rm -T --entrypoint python collaboration -`. Sin API Trello
   alternativa ni escritura Discord. Se conservaron roles y aceptaciÃ³n pendiente.
2. `git fetch origin`, inventario de `docs/adr/` en develop y lectura de ADR/diseÃ±os,
   contratos y evidencia enlazada. Diez ADR integrados; ADR-0011 y ADR-0012 en las
   ramas abiertas JUP-096 y JUP-099. Se reservaron ambos nÃºmeros.
3. `gh pr list --repo EconomiconFinOps/tfm-economicon --state all --limit 80
   --json number,title,state,mergedAt,url,headRefName` y consultas `gh pr view`
   de #25/#51/#53/#54/#59. El Ã­ndice distingue los merges observados y las reviews
   APPROVED de las notas antiguas en los documentos. No se solicitÃ³ nueva review
   ni se atribuyÃ³ actividad por los roles de Trello.
4. Tres justificaciones retrospectivas Proposed: pgvector, auth demo y Compose.
   Se conservan las fuentes de implementaciÃ³n y sus lÃ­mites. No hay comparativa
   de motores, hosting productivo o presupuesto nuevo aprobados por esta auditorÃ­a.
5. Se reparan seis enlaces de ADR a OpenSpec archivado y se aÃ±aden referencias
   concretas de aceptaciÃ³n/evidencia a los registros que solo tenÃ­an referencias
   genÃ©ricas o notas anteriores a la integraciÃ³n.

## Comprobaciones ejecutadas

- OpenSpec `validate --all --strict --no-interactive`: **36/36 PASS**.
  Se usÃ³ el binario 1.8.0 ya instalado en el checkout principal, ejecutado desde
  esta rama; equivalente a `corepack pnpm openspec:validate` sin reinstalar paquetes.
- `node tools/jup-check.mjs --change jup-061-architecture-decision-register`: PASS.
- `node tools/jup-cleanup-check.mjs`: PASS.
- `git diff --check`: PASS.
- 109 rutas Markdown locales y 15 anchors de los documentos afectados: PASS, comprobados
  contra archivos/cabeceras del checkout; sin solicitar los enlaces externos de
  precios/proveedores. Las PR se verificaron con GitHub CLI autenticado.

Los tests de backend/frontend/processor y los smokes enlazados son evidencia
histÃ³rica de sus tareas. No se ejecutan de nuevo ni se presentan como pruebas
nuevas de producto en esta modificaciÃ³n documental.

## LÃ­mites y siguiente puerta

- No se cambia ningÃºn estado Accepted/Proposed preexistente. ADR-0005 permanece
  Proposed pese al merge; requiere ratificaciÃ³n documental. ADR-0002 conserva
  sus condiciones explÃ­citas de aceptaciÃ³n conjunta.
- PR #51, #53, #54 y #59 estaban abiertas al corte. No se atribuye su producto a
  develop. Las fuentes externas de los registros 0011/0012 y pgvector se fijan
  por commit para que la auditorÃ­a pueda reproducirse.
- La memoria canÃ³nica y su exportaciÃ³n no se han editado: este registro proporciona
  referencias reutilizables. La selecciÃ³n comparativa original de CockroachDB
  sigue sin evidencia localizada; se declara, no se inventa una motivaciÃ³n histÃ³rica.
- RevisiÃ³n de Paris, validaciÃ³n de Victor y pairing de Lucia de JUP-061 pendientes
  de evidencia atribuible. Esta entrega no cierra la tarjeta ni fusiona el PR.

## PublicaciÃ³n y seguimiento

[PR #60](https://github.com/EconomiconFinOps/tfm-economicon/pull/60) publicada como
borrador contra develop. Trello actualizado mediante el puente autorizado y
releÃ­do: descripciÃ³n/enlaces verificados, roles preservados, **30 â€” En curso**.
El trabajo documental estÃ¡ entregado; revisiÃ³n, validaciÃ³n y ratificaciones humanas
siguen pendientes. No se ha enviado ningÃºn mensaje a Discord ni realizado merge.

## ReconciliaciÃ³n y correcciÃ³n del test â€” 02/10/2026

El usuario autorizÃ³ reconciliar develop y resolver el fallo de CI. Base consumida
`5a54ce2ed9001dfb9d4b9d8e06eae84cffe91124`; merge local `2650e69`.
El Ãºnico conflicto, ADR-0004, se resolviÃ³ conservando aprobaciÃ³n de JUP-094 y
seguimiento de tokens/atribuciones de JUP-099. ADR-0011/12 ya estÃ¡n integrados en
la base; el Ã­ndice enlaza sus archivos locales y conserva el corte anterior.

CI anterior fallaba con `{ sessionExpired: true }` en la aserciÃ³n inmediata tras
encontrar Sign in. Encontrar el botÃ³n acredita render, pero no finalizaciÃ³n del
efecto de limpieza/navegaciÃ³n. Se espera con waitFor el estado null del router
antes de observar el historial. No cambia LoginPage ni se aÃ±aden sleeps/retries
al test. Se preserva la captura completa de transiciones al navegar hacia atrÃ¡s.

Comprobaciones del incremento:

- Antes de editar, las dos suites dirigidas pasaron 10/10: el fallo de CI no se
  reprodujo en esa ejecuciÃ³n local. Se corrige la precondiciÃ³n asÃ­ncrona observable.
- Test corregido: tres ejecuciones dirigidas PASS.
- Mutantes manuales `replace:false` y opciones `{}`: ambos detectados por la
  aserciÃ³n original not.toContainEqual de las transiciones de historial. El
  producto fue restaurado Ã­ntegramente tras cada prueba; diff de LoginPage vacÃ­o.
- Primera suite completa con concurrencia automÃ¡tica y lint/tipos simultÃ¡neos:
  430 PASS y 7 FAIL, con timeouts y elementos ausentes. No se cuenta como PASS.
- ReejecuciÃ³n aislada `corepack pnpm --filter @finops/frontend test -- --maxWorkers=2`:
  **437/437 PASS, 47/47 archivos**, 86,40 s. Los fallos anteriores son compatibles
  con carga local, sin acreditar una causa exhaustiva para cada uno.
- Frontend lint, typecheck y build PASS; build conserva aviso de bundle >500 kB.
- OpenSpec estricto **37/37 PASS**; trazabilidad e higiene PASS (724 archivos).
- 115 rutas Markdown locales verificadas en el delta; diff check PASS.

Logs dirigidos, controles negativos y suite acotada conservados fuera de Git en
`materiales/07-evidencias/JUP-061-reconciliacion-2026-10-02/` dentro del workspace.
La correcciÃ³n del test amplÃ­a el alcance inicial documental por autorizaciÃ³n
expresa del 02/10; no modifica contrato ni comportamiento del login.

## Atención del P2 y nueva base — 02/10/2026

[Paris solicitó cambios](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5395470690)
sobre el head `a051339`: retirar de esta entrega la convención de continuidad
compartida. Se leyó la revisión completa y los comentarios antes de corregir.
Se retiran la regla añadida a AGENTS.md y los dos documentos de continuidad del
delta compartido, y se ajustan las referencias del diseño y las tareas. El
inventario ADR y esta evidencia permanecen; no se condiciona la entrega a PR #64.

Se integra develop `11d63ea03e6f8a2d19a8cace45d11c34bb9676a9`, incluido JUP-100.
AGENTS.md coincide con la nueva base y Git no registra documentos de continuidad.
Verificación del incremento: **93/93 tests** de gobernanza, trazabilidad, higiene,
política de PR y workflow; OpenSpec **38/38**, trazabilidad de nueve cambios e
higiene de 731 archivos PASS. Las rutas Markdown locales del delta y diff check
pasan. No se reejecuta producto localmente por este incremento documental y de
gobernanza; los resultados frontend anteriores conservan su fecha y head.

CI técnica del head anterior `a051339`: siete controles SUCCESS en
[run 36991796052](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/36991796052).
La nueva publicación requiere comprobar su propia CI. JUP reviews exige revisión
y validación tituladas según JUP-100; atender el P2 no levanta automáticamente
CHANGES_REQUESTED ni acredita validación de Victor. Trello permanece en revisión.
