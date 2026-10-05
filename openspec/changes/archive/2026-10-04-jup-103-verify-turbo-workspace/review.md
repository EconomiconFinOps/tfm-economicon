# Review: jup-103-verify-turbo-workspace

## Result

Listo para el gate post-review de Victor. **No es un veredicto independiente**: lo redacta quien
implementó. La revisión y la validación de terceros llegan con el pull request («Revision JUP-103» y
«Validacion JUP-103»). Evidencia completa, con las salidas reales, en
[`docs/evidence/JUP-103-validation.md`](../../../../docs/evidence/JUP-103-validation.md).

Resumen: `RF-093-001` **no era un fallo del repositorio**. En las máquinas afectadas faltaba
`corepack enable` y un pnpm `11.x` global se resolvía antes que el de corepack, de modo que turbo
lanzaba una versión que se negaba a cambiar a la fijada. La corrección es de entorno, se comprobó en
dos máquinas y queda documentada en el `README.md`. De los 7 criterios de la tarjeta, **solo el 7
(spike) se cumple sin reservas**; el 1, 2, 4, 5 y 6 se cumplen con salvedades escritas y el 3 (CI)
está pendiente del pull request (ver «Checklist»).

## Scope Reviewed

- `README.md`: sección nueva «Requisito previo: pnpm con corepack», bloque «Con Turborepo» y
  «Comandos Principales».
- `openspec/findings/backlog.md`: `RF-093-001` reformulado y en `Open`; observación nueva en `RF-098-004`;
  `RF-103-001` a `RF-103-005` nuevos.
- `docs/spikes/frontend-migration.md`: F4 completa (Docker resuelta por JUP-049 y JUP-050, sin
  tarjeta propia; turbo con su slug real) y entrada 11 de «Próximos pasos».
- `docs/evidence/JUP-103-validation.md` (nuevo).
- `openspec/changes/jup-103-verify-turbo-workspace/{proposal,design,specs,tasks,review}.md`.
- **En solo lectura, sin tocar:** `package.json`, `turbo.json`, `pnpm-workspace.yaml`,
  `pnpm-lock.yaml`, `.github/**`, `apps/**`, `tools/**` y `packages/**`. Verificado con
  `git diff --name-only origin/develop...HEAD`: solo `README.md`, `docs/` y `openspec/`.

## Checklist

Requisitos de [`specs/workspace-task-pipeline/spec.md`](specs/workspace-task-pipeline/spec.md):

- [x] **Los scripts de la raíz usan la versión fijada** en una máquina preparada: `lint`, `build` y
  `typecheck` con código `0` y 0 apariciones del error de versión. [ ] El escenario de CI queda
  pendiente del pull request (tarea 7.6).
- [x] **El requisito previo está documentado y se puede diagnosticar**: máquina preparada (`9.0.0`,
  código `0`), máquina con otro pnpm por delante (error o versión distinta) y acción requerida al
  equipo, todo en el `README.md`.
- [x] **`dev` arranca las aplicaciones en paralelo**: turbo lanza las cuatro tareas con el pnpm
  correcto y, con su configuración disponible, las cuatro responden `200`. Sin ella, no
  (`RF-103-001`); por eso el escenario lleva esa condición (ver «Decisiones», 5).
- [x] **El frontend participa en el grafo**: tiene las cinco tareas.
  [ ] **El escenario de orden de `build` con dependencias internas no se ha ejercitado**: ningún
  paquete del workspace depende de otro.

Criterios de la tarjeta (detalle en la evidencia, «Trazabilidad con los criterios»):

- [x] 1. Scripts desde la raíz sin el error de versión. **Salvedad:** `corepack pnpm test` literal
  termina con código `1` en esta máquina por tests con plazos de tiempo (`RF-103-005`,
  `RF-098-004`); en dos mitades pasa.
- [x] 2. `pnpm dev` en paralelo. **Salvedad:** necesita `--env-mode=loose` y un archivo de entorno
  con `127.0.0.1`.
- [x] 3. CI en verde: el workflow `CI` pasa sus 7 jobs sobre `f6e01c5` (PR #75); `JUP reviews` espera
  las reviews. Se registró después de la aprobación post-review, que lo daba por pendiente.
- [x] 4. `RF-093-001` reformulado con la causa y **mantenido en `Open`** (el criterio admite «o
  reformulado con precisión si resulta ser de entorno»), hasta confirmar a Paris y a Alejandro en
  consola externa.
- [x] 5. Qué debe hacer el equipo: escrito, **de forma provisional**. La consulta se cerró con Paris y
  la consola externa de Alejandro como no confirmados (comprobado en 2 de 4 máquinas).
- [x] 6. Scripts de la raíz para tarjetas futuras: `lint`, `build` y `typecheck` sí; `test` y `dev`
  con las salvedades documentadas.
- [x] 7. Spike con F4 completa.

## Decisiones tomadas durante la implementación

El plan aprobado en el gate pre-código se mantuvo (corrección de entorno más documentación, sin
tocar `package.json`, `turbo.json`, el lockfile ni CI). Estas son las decisiones que no estaban
previstas o que corrigieron el plan:

1. **La caché de turbo da falsos positivos.** Su clave no depende del gestor de paquetes: una
   ejecución previa sin `corepack` dejó `lint` cacheado y `corepack pnpm lint` pasó 4 de 4 en 129 ms
   sin lanzar un solo subproceso. Toda comprobación posterior usa `--force` (o `TURBO_FORCE=true` en
   `pnpm test`, que no admite el indicador) y verifica `cache bypass, force executing`. Se añadió a
   `design.md` (riesgos) y al `README.md`.
2. **`test` se ejecuta en dos mitades**: los paquetes de Python (con un entorno virtual fuera del
   repositorio) y el frontend con `--maxWorkers=1`. No se puede pasar el indicador a `pytest` ni
   declarar variables de entorno para Vitest sin tocar `turbo.json`, que esta tarjeta no modifica.
   Se usa `pnpm run test`, que reenvía las opciones a turbo; `pnpm test` es un comando propio de pnpm
   y las rechaza.
3. **`RF-098-004` se matiza**, no se cierra: pasa con `--maxWorkers=1` y falla entre 14 y 21 tests con
   los workers por defecto, también ejecutando solo el frontend. Contradice «pasan aislados».
4. **`dev` se documenta, no se arregla.** Arreglarlo exigiría `turbo.json` o las aplicaciones, que el
   gate excluyó. Se registra como `RF-103-001` y se escribe en el `README.md` lo que sí funciona,
   verificado.
5. **La spec se corrigió durante el `apply`** porque la evidencia contradijo dos escenarios: el
   diagnóstico de Alejandro imprimió `11.19.0` **sin error** (el escenario decía «termina con
   error»), y `dev` solo mantiene las aplicaciones con su configuración disponible (se añadió esa
   condición). `design.md`, decisión 4, y el `README.md` se alinearon con ello.
6. **El diagnóstico dice «imprime exactamente `9.0.0`»**, no «no da error», por el caso anterior.
7. **`RF-093-001` se mantiene `Open`, reformulado.** Se redactó primero como `Fixed` con los pendientes
   escritos dentro (el entorno de Codex de Alejandro y la máquina de Paris); en el gate post-review
   se decidió dejarlo `Open` hasta tener esas dos respuestas, y pasa a `Fixed` cuando ambas confirmen
   sin contradecir la corrección.
8. **ADR: no aplica.** No se introduce ninguna decisión de arquitectura duradera: el gestor de
   paquetes, su versión, el orquestador y la forma de invocarlo no cambian; se documenta un requisito
   previo que CI ya cumplía.

## Validation

La batería completa de la tarea 7.1, con códigos de salida y conteos, está en la evidencia
(«Batería final desde la raíz»). En resumen, desde la raíz y sin sustituto `--filter @finops/frontend`
que esquive turbo: `install --frozen-lockfile`, `lint`, `build` y `typecheck` en verde con `--force`;
`test` en verde en dos mitades (`azure-cost-api` 59, `processor` 448 con 57 omitidos, `backend` 329
con 17 omitidos, `frontend` 443); `openspec:validate` 42 de 42, `jup:check`, `jup:check:all`,
`jup:cleanup:check` y los tests de las herramientas del repositorio, todos en verde.

Lo que **no** se validó está enumerado en la evidencia («No validado»), entre otras cosas: CI, la
máquina de Paris, la consola externa de Alejandro, macOS y Linux, y las causas de los fallos
intermitentes de `test` (no se midió la carga ni se descartó una carrera).

## Excepción del ciclo Red/Green

No se invocó el ciclo Red/Green, ni la mutación, ni la validación de QA por tarea: **la tarjeta no
añade ni cambia código de producto**, solo documentación, el backlog de hallazgos, el spike y la
evidencia, más un cambio de entorno en una máquina. No hay comportamiento que cubrir con tests
unitarios ni mutantes que medir. La verificación son los comandos reales con su salida, que
sustituyen a la regresión de código; la excepción está prevista en la decisión 8 de `design.md`.

## Review Findings

- **`RF-093-001` reformulado y en `Open`**, con la causa de entorno y las dos afirmaciones del texto
  original que resultaron inexactas.
- **`RF-103-001`** `pnpm dev` no puede arrancar backend ni processor (Medium).
- **`RF-103-002`** `--parallel` obsoleto en turbo `2.9.18` (Low).
- **`RF-103-003`** `localhost` bloquea el arranque del backend; causa sin verificar (Low).
- **`RF-103-004`** `local:test` falla con la infraestructura de Compose levantada (Low).
- **`RF-103-005`** `test` con los cuatro paquetes a la vez falla de forma distinta en cada ejecución
  por tests con plazos de tiempo de JUP-023 y JUP-086 (Medium).
- **`RF-098-004`** con observación nueva.

Incidencias del proceso, para que no se repitan:

- **Falso positivo de la caché** (decisión 1): se detectó porque el resultado contradecía la
  reproducción anterior y se investigó antes de registrarlo.
- **Edición del backlog en la columna equivocada**: una primera edición dejó la resolución de
  `RF-093-001` en «Change/Fix» y sin el `|` final de la fila. Se detectó al comprobar celda por
  celda, se revirtió el archivo (solo contenía esa edición) y se rehízo con una comprobación de
  estructura. Dos filas del backlog (`RF-044-001` y `RF-045-001`) ya tenían otro número de celdas
  antes de esta tarjeta y no se tocaron.
- **Un resultado de `local:test` en rojo** que parecía del `README.md` era la infraestructura de
  Compose levantada para la tarea 3.3; se comprobó parándola.

## Risks / Follow-Ups

- **No confirmados** (consulta cerrada el 2026-10-04): la máquina de Paris (sin respuesta) y la
  consola externa de Alejandro. `RF-093-001` sigue `Open` hasta que ambos confirmen; si alguno
  contradice la corrección, se revisa la causa.
- **`develop` avanzó** a `c3aa9d6` (JUP-061 #60 y JUP-022 #67) mientras se implementaba. Se fusionó
  en la rama y se reverificó (evidencia, «Reverificación tras fusionar `develop`»): un conflicto
  mecánico en `backlog.md`, resuelto conservando las filas de ambas ramas; `README.md` sin conflicto;
  `lint`, `build`, `typecheck`, `test` por mitades y los checks, en verde. Lo que cambia `develop` en
  `package.json` y `ci.yml` no afecta a esta tarjeta (los jobs con pnpm siguen haciendo
  `corepack enable`); último ADR `ADR-0017`, esta tarjeta no añade ninguno.
- **Enlace que se rompe al archivar**: el del spike apunta a `openspec/changes/jup-103-verify-turbo-workspace/`
  y pasa a `openspec/changes/archive/<fecha>-jup-103-verify-turbo-workspace/` (tarea 7.5).
- **Efectos en la máquina de verificación**, ajenos al repositorio: se arrancó Docker Desktop, se
  levantó la infraestructura de Compose (que creó el volumen `rabbitmq-data`) y se paró de nuevo
  conservando todos los volúmenes, y se creó un entorno virtual de Python fuera del repositorio.
- **JUP-104 y JUP-105** pueden usar `lint`, `build` y `typecheck` desde la raíz sin sustituto, tras
  `corepack enable`; `test` por mitades; `dev` con los pasos del `README.md`.
- **JUP-051 (PR #58)**, abierto, modifica `ci.yml` y `tools/ci-workflow.test.mjs`: esta tarjeta no
  toca ninguno de los dos, así que no hay solapamiento.

## Human Approval

- Change: jup-103-verify-turbo-workspace
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-10-04
- Archive decision: archive
- Scope reviewed: las 27 tareas de `tasks.md`; este `review.md`; la evidencia
  `docs/evidence/JUP-103-validation.md` (línea base, corrección, grafo y `dev`, documentación,
  consulta al equipo, batería final y reverificación tras fusionar `develop`); y los cambios en
  `README.md`, `openspec/findings/backlog.md` y `docs/spikes/frontend-migration.md`.
- Condition approved: **`RF-093-001` se mantiene `Open`**, reformulado con la causa de entorno y la
  corrección documentadas, hasta obtener la respuesta de Paris y la de Alejandro en una consola
  externa. Pasa a `Fixed` cuando ambos confirmen sin contradecirla; si alguno la contradice, se
  revisa la causa. Cambia así lo redactado primero (`Fixed` con pendientes escritos dentro) y el
  criterio 4 de la tarjeta se cumple por la vía de la reformulación, no del cierre.
- Resultado verificado: `lint`, `build` y `typecheck` desde la raíz sin el error de versión de pnpm
  en la máquina donde se reproducía (4 de 4, 4 de 4 y 1 de 1, con `--force`); `test` en dos mitades
  (Python y frontend con `--maxWorkers=1`) y el árbol fusionado con `develop` (`c3aa9d6`) en verde;
  `openspec:validate` 45 de 45, `jup:check`, `jup:check:all` y `jup:cleanup:check` en verde. La
  corrección (`corepack enable` una vez por máquina) está comprobada en 2 de 4 máquinas.
- Salvedades aceptadas: el comando literal `corepack pnpm test` falla de forma distinta en cada
  ejecución con los cuatro paquetes a la vez (`RF-103-005`, `RF-098-004`); `pnpm dev` por sí solo no
  deja sirviendo a backend ni a processor (`RF-103-001` a `RF-103-003`); `local:test` falla con la
  infraestructura de Compose levantada (`RF-103-004`). Todos registrados como hallazgos `Open`, sin
  corregir en esta tarjeta.
- Constraints: ningún archivo de `apps/**`, `tools/**`, `packages/**` ni `.github/**`, ni
  `package.json`, `turbo.json`, `pnpm-workspace.yaml` ni `pnpm-lock.yaml`, en el diff de la rama. La
  aprobación **no** sustituye la revisión y la validación del pull request («Revision JUP-103» y
  «Validacion JUP-103»), no acredita el CI (criterio 3, pendiente del PR) ni autoriza fusionar.
- Required changes before archive: ninguno más; al archivar se corrige el enlace del spike a
  `openspec/changes/archive/<fecha>-jup-103-verify-turbo-workspace/` (tarea 7.5).
