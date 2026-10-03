# JUP-061 — Auditoría del registro de decisiones

Verificación documental: 2026-10-01. Base `origin/develop` `de0d62e`.
[Tarjeta](https://trello.com/c/qXoHFxyy) · [inventario canónico](../adr/README.md) ·
[contrato de registro](../../openspec/specs/architecture-decisions/spec.md).

## Método y resultado

1. Lectura viva de JUP-061 mediante `Settings`/`TrelloClient.get_cards()` del puente
   desplegado en DockerServer, usando
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

Los logs originales dirigidos, de controles negativos y de la suite acotada
no están disponibles en Git ni son evidencia compartida reproducible. Los
resultados anteriores son el reporte histórico del autor; las revisiones
independientes y la CI enlazada permiten contrastar sus límites.
La corrección del test amplía el alcance inicial documental por autorización
expresa del 02/10; no modifica contrato ni comportamiento del login.

## Atención del P2 y nueva base — 02/10/2026

[Paris solicitó cambios](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5395470690)
sobre el head `a051339`: retirar de esta entrega la convención de continuidad
compartida. Se leyó la revisión completa y los comentarios antes de corregir.
Se retiran la regla añadida a AGENTS.md y los dos documentos de continuidad del
delta compartido. El resto de continuidad en el diseño no quedó corregido en
ese head: se subsana en la revisión del 03/10 descrita abajo. El
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

## Correcciones de las reviews y reconciliación — 03/10/2026

Se leyeron las cuatro reviews completas, los tres comentarios de conversación y
el listado inline vacío antes de corregir. Fuentes: [revisión de Paris](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5400647319),
[validación de Lucia](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5396865126)
y [validación de Victor](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5396889294).

- Evidencia histórica restaurada desde `724031c` con lectura/escritura UTF-8
  explícita; sección del P2 preservada y afirmación sobre el diseño corregida.
  Se elimina la ruta del host y se declara la indisponibilidad de logs originales
  en Git. Descripción y comentario afectados se corrigen sin alterar reviews ajenas.
- Develop `d6fc408b60e944b726605b242f3e7a64129282c7` incorporado sin conflicto.
  API GitHub: #51 integrada 01/10 21:36 UTC, #54 01/10 20:23 UTC,
  #59 02/10 19:14 UTC y #53 02/10 20:09 UTC. Índice y ADR-0013/15
  actualizados con fuentes locales y pendientes de integración resueltos.
- Responsabilidades vigentes: Alejandro liderazgo, Victor pairing previsto,
  Paris revisión y Lucia validación. El acuerdo consta en la review de Lucia;
  la lectura del puente encontró roles anteriores y ningún comentario del acuerdo
  entre las acciones devueltas. Se reconcilia Trello con esa fuente explícita.
  No se acredita pairing ni ratificación de ADR por esta corrección.
- `node --test tools/*.test.mjs`: **225/225 PASS**.
- `corepack pnpm openspec:validate`: **40/40 PASS**; `jup:check:all`: nueve
  cambios PASS; `jup:cleanup:check`: 758 archivos PASS; `git diff --check`: PASS.
- Comprobación del delta: UTF-8 sin secuencias dañadas, 15 ADR enlazados con
  estado consistente, **118 rutas locales y 15 anchors**, ninguno roto.
  El primer verificador solo reconocía Status, no Estado; se corrigió para
  comprobar ambas cabeceras y se repitió, sin modificar los estados ADR.

Estos son controles documentales y de tooling del autor sobre la nueva base.
No son validación humana ni nuevas pruebas locales Python, Docker, frontend o
benchmarks. Las ejecuciones anteriores mantienen fecha y head. La CI del nuevo
head se enlazará en la solicitud formal; JUP reviews continúa pendiente de
resolver las solicitudes de cambios de Paris, Lucia y Victor. ADR-0013/14/15
siguen Proposed; ADR-0005 y las condiciones de ADR-0002 no cambian.

## Integración de ADR-0016 y nueva base — 03/10/2026

Tras leer todas las reviews, conversación e inline, se incorpora develop
`6410950315b0e3c22057d09015e11e38c5e455ab` (#65/JUP-023). El único conflicto
era docs/adr/README.md: se preservan el inventario y la decisión de color 0012,
y se incorpora la fila ADR-0016 Proposed con su fuente y evidencia JUP-023,
sin secciones duplicadas ni ratificación de ADR. Archivos de producto aportados
por develop conservados íntegros, sin modificaciones propias adicionales.

API GitHub de #53: aprobación vigente de Victor **02/10 19:56:31 UTC**;
la del 01/10 fue DISMISSED. Se corrige en la fila 0013 y su ADR conservando
la precisión histórica. Las cuatro referencias al change activo en las cabeceras
ADR-0013/14/15 y esta evidencia se reemplazan por el contrato principal estable,
para que sigan resolviendo cuando el change se archive. Esta corrección no
archiva ni da por completas las tareas de aprobación/ratificación pendientes.

La validación de Lucia y la resolución de Victor sobre 0659816 conservan su
head y fecha. La combinación nueva requiere revisión de Paris y validación
incremental de Lucia conforme a CONTRIBUTING punto 7. No se acredita aceptación
por integrar develop ni se presentan smokes históricos como nuevas ejecuciones.
