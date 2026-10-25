# Evidencia JUP-088 — Reconciliacion documental M1

- Fecha: 2026-08-28.
- Trello: https://trello.com/c/RJjK2Z6L
- Rama: `docs/JUP-088-documentation-reconciliation`.
- Base: `origin/develop` en `a746d48`.
- Commit principal: `04a9f6c06d96e905432fbcde0391ebdd84ea9d66`.
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/19
- CI inicial: https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/33184619670
- CI final tras higiene: https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/33185815093

Los apartados siguientes hasta la revalidacion del 02/09 conservan la captura
historica del 28/08; sus cifras y consolidacion local no describen el estado actual.

## Fuentes contrastadas

- Trello consultado mediante el puente de `dockerserver`: 79 tarjetas abiertas,
  76 JUP y 50 P0 tras crear JUP-088 como tarjeta de coordinacion no P0.
- Codigo y documentacion canónicos de `origin/develop`.
- Cambios OpenSpec activos, tareas, specifications base y findings.
- Materiales locales de requisitos y coordinacion del espacio Economicon.

## Resultado documental

- JUP-080 contiene una captura fechada de las 50 P0 y asigna JUP-085/086/087
  exactamente una vez a M1. El test deriva la cobertura desde el JSON versionado.
- JUP-085 define login, perfil, JWT, TTL, expiracion, logout y separacion de secretos.
- JUP-086 define autorizacion y propagacion tenant para API, cola, persistencia,
  vector store y herramientas del agente.
- JUP-087 define lint sin errores y pruebas frontend reales de recorridos criticos.
- Findings RF-082-002 y RF-083-002 ya apuntan a JUP-087 y JUP-035/JUP-087.
- README, arquitectura y manual de Turborepo distinguen capacidades integradas,
  providers mock, CI existente y CD/RAG/frontend todavia pendientes.
- Los materiales locales registran decisiones ya tomadas y mantienen como
  pendientes solo calendario, aprobación JUP-078/JUP-080, retencion y `setup/sdd`.
- `.gitattributes` fija LF para texto y trata PNG, PDF, ZIP, MP4 y PPTX como
  binarios, sin renormalizar en bloque archivos históricos dentro de este PR.
- La estrategia limita a dos los worktrees de tarea, exige que no contengan
  trabajo único y ordena retirarlos al mezclar o cerrar el pull request.

## Consolidacion operativa

- El clon principal quedo limpio en `develop` y alineado con
  `origin/develop` (`a746d48`).
- `git worktree list` quedo en una linea y `tmp/` sin contenido.
- Se retiraron 15 ramas locales historicas y 13 ramas remotas previamente
  verificadas como ancestros de `origin/develop`.
- Se conservaron `main`, `develop`, `setup/sdd` y las seis ramas con pull
  request abierto, sin decidir su promocion, integracion o cierre.
- Antes de la limpieza se verifico un bundle con 69 refs y se respaldo por
  separado el conector local; el despliegue de `dockerserver` no se modifico.

## Archivo OpenSpec

Se contrastaron tareas completas y estado `70 — Hecho` en Trello antes de archivar:

- Con promocion a specification base: JUP-019 y JUP-072 a JUP-077.
- Con `--skip-specs` por ser cambios de proceso/documentacion: JUP-082 y JUP-083.

JUP-048, JUP-078, JUP-079 y JUP-080 permanecen activos porque Trello sigue en
revision/validacion o existen tareas de aprobacion/participacion abiertas.

## Validaciones

- OpenSpec estricto: 17/17 specifications y cambios activos válidos.
- Trazabilidad: 7/7 cambios JUP activos enlazados y completos estructuralmente.
- Roadmap: 5/5 pruebas; 50 P0 únicas y asignadas exactamente una vez.
- Checker JUP: 7/7 pruebas.
- Higiene: 335 archivos aceptados y 6/6 pruebas del checker.
- Enlaces Markdown relativos: todos resuelven, incluidos los changes archivados.
- `git diff --check`: sin errores de whitespace.
- CI remoto: seis comprobaciones obligatorias completadas correctamente.

La ejecución no modifica código funcional, no acredita las tareas de
implementacion pendientes de JUP-085/086/087 y no marca como realizada la
participación de ningún miembro.

## Revalidacion contra develop — 2026-09-02

- Base integrada: `6e34f1f` (`origin/develop`), sobre el head anterior de la PR
  `7ee3175`. Se incorpora mediante merge a la rama de JUP-088, sin reescribir
  su historia. El contenido funcional resultante coincide con `develop`.
- Se preservan los cambios posteriores de JUP-042 (logging), JUP-062 (memoria),
  JUP-078 (aprobacion atribuible y precios fechados) y JUP-090 (inventario frontend).
- El unico conflicto de Git estaba en `openspec/findings/backlog.md`:
  RF-083-002 conserva JUP-035/JUP-087 y distingue origen visual de destino
  funcional; RF-090-001/002/003 conservan integramente sus datos y estados.
- Se reparan dos enlaces al spike en el archivo de JUP-090 y el ejemplo de
  trazabilidad de `AGENTS.md` usa un cambio activo.

### Coherencia de contratos y roadmap

- JUP-085 explicita `user` en login y el perfil directo en `/me`, con escenario
  positivo de perfil. El frontend toma el perfil de login y no invoca `/me`;
  RF-090-003 sigue abierto. La limpieza automatica tras `401` sigue pendiente.
- JUP-086 conserva el bootstrap autenticado de `/tenants` sin selector previo;
  las operaciones sobre datos de tenant exigen el contexto autorizado.
- JUP-087 enlaza el inventario JUP-090 y mantiene casos positivos y de error
  para login, tenant, dashboard, ingesta y conversacion. No acredita tests
  frontend ni lint limpio que el baseline aun no proporciona.
- La lectura de Trello se hizo exclusivamente mediante la integracion desplegada
  en `/home/danteadmin/economicon-collaboration` de `DockerServer`.
- JUP-088 sigue en `40 — En revision`, con liderazgo Alejandro, pairing Lucia,
  revision Paris y validacion Victor; M1 es el 04/09/2026 en la descripcion,
  mientras el campo `due` de esta tarjeta sigue vacio.
- JUP-080 conserva la captura de 50 P0 del 28/08, con JUP-085/086/087 una vez
  en M1. El tablero actual tiene 52 P0 por JUP-090/091, sin hito ni fecha en sus
  tarjetas. El roadmap registra el desfase y la tarea 4.5 deja su asignacion
  pendiente de acuerdo. JUP-088 no es P0. No se cambian fechas en Trello.

### Validaciones locales del resultado integrado

| Comprobacion | Resultado |
|---|---|
| `corepack pnpm install --frozen-lockfile` | Correcto, sin cambios de dependencias |
| `corepack pnpm openspec:validate` | 19/19 |
| `corepack pnpm jup:check:all` | 9/9 cambios activos |
| `jup:check:test`, `pr:check:test`, `ci:check:test` | 7/7, 11/11, 7/7 |
| `roadmap:test`, `repository:governance:test` | 5/5, 5/5 |
| `jup:cleanup:test`, `jup:cleanup:check` | 6/6; 364 archivos aceptados |
| `assistant-corpus:test`, `assistant-corpus:validate` | 8/8; manifiesto valido |
| `llm-gateway:test` | 6/6 |
| `corepack pnpm --filter @finops/frontend build` | Correcto |
| `corepack pnpm --filter @finops/frontend lint` | 49 errores heredados `react/prop-types` en nueve archivos; RF-082-002 / JUP-087 |
| Destinos de enlaces Markdown relativos | 30 comprobados; los dos enlaces de archivo reparados |
| `git diff --check` y conflictos sin resolver | Sin errores ni entradas pendientes |

Los seis checks de CI, incluidas las tres suites Python, se ejecutan de nuevo
al publicar el head reconciliado. Su resultado y enlace se registran en la
descripcion de la PR #19; las ejecuciones de agosto no acreditan este head.
La revision solicitada a `ParisArcos` sigue pendiente. La validacion automatica
no sustituye pairing, revision humana ni evidencia funcional atribuible a los
roles de la tarjeta y no autoriza el merge ni el cierre de JUP-085/086/087.

## Revalidacion contra develop — 2026-09-07

- Base integrada: `b6eaa8709856b4c120bb94dc2ce7304dcf722a26`, verificada en la
  rama remota `develop`, sobre el head de JUP-088 `f8e7ac9`. Se incorpora mediante
  merge a la rama de la PR #19, conservando el historial publicado.
- Se preservan JUP-081 (puente y su CI), JUP-084 (contrato de herramientas del
  agente), JUP-091 (inventario del origen) y JUP-092 (ADR-0003 de TypeScript).
- El unico conflicto textual estaba en RF-082-002 de
  `openspec/findings/backlog.md`. La resolucion conserva su seguimiento en
  JUP-087 y la decision aceptada de ADR-0003: F2 solo desactiva `react/prop-types`
  para `.ts`/`.tsx`; el finding sigue abierto hasta migrar los nueve `.jsx`
  afectados o sus sustitutos con cobertura real de tipos en F3/F5.
- RF-083-002 mantiene JUP-035/JUP-087 y distingue TypeScript ya aprobado del
  tooling pendiente y de la decision del salto Vite 5 a 6. Los hallazgos
  RF-090-001/002/003 y RF-091-001/002/003/004 se conservan integros.
- El design de JUP-087 se alinea con ADR-0003, sin cambiar sus escenarios ni dar
  por implementados lint limpio o pruebas frontend reales. La arquitectura
  conserva tanto las aclaraciones de mocks/RAG como el nuevo contrato JUP-084
  y la advertencia sobre los datos mock de `/billing/summary`.
- Codigo de las aplicaciones, puente, CI, dependencias y lockfile coinciden con
  `develop`. La resolucion agrega solo reconciliacion documental y esta evidencia.

### Validaciones del resultado integrado

| Comprobacion | Resultado |
|---|---|
| `corepack pnpm install --frozen-lockfile` | Correcto, sin cambios de dependencias |
| Ocho suites Node de gobernanza, roadmap, higiene, corpus y gateway | 55/55 |
| `corepack pnpm jup:check:all` | 11/11 cambios activos |
| `corepack pnpm jup:cleanup:check` | 397 archivos aceptados |
| `corepack pnpm assistant-corpus:validate` | Manifiesto valido |
| `corepack pnpm openspec:validate` | 21/21 |
| `python -m unittest discover -s tools/collaboration/tests -v` | 12/12, con clientes simulados |
| `corepack pnpm --filter @finops/frontend build` | Correcto |
| `corepack pnpm --filter @finops/frontend lint` | 49 errores heredados `react/prop-types` en nueve `.jsx`; RF-082-002 sigue abierto |
| Destinos Markdown relativos en archivos cambiados respecto de `develop` | 22 comprobados, ninguno roto |
| Revision independiente de la resolucion | Sin regresiones nuevas detectadas |
| `git diff --check` y entradas de conflicto del indice | Sin errores ni conflictos pendientes |

Los tests Node y Vite necesitaron ejecutarse fuera del aislamiento local de
Windows, que bloqueaba sus subprocesos con `spawn EPERM`. La instalacion con
lockfile congelado y las validaciones posteriores finalizaron correctamente,
salvo el lint heredado indicado. Las tres suites de servicios Python se validan
en el CI remoto del nuevo head; esta tabla no las presenta como ejecutadas en
local. El resultado remoto se consulta en los checks de la PR #19.

La solicitud de revision a `ParisArcos` se conserva. Las capturas de Trello y del
roadmap de apartados anteriores siguen siendo historicas: esta actualizacion
no vuelve a consultar el tablero ni cambia responsables, fechas o estados.
