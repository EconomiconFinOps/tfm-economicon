# Review: jup-105-close-frontend-migration

> **Actualización 10/10/2026:** el [aporte residual](../../../../docs/evidence/JUP-105-residual.md)
> corrige la salvedad del comentario Dashboard y añade notas a tasks/review de
> JUP-097. Alejandro ya entregó el diagnóstico Codex: consola normal y corrección
> permanente siguen pendientes. La CI técnica de `ca9e67f` terminó verde.
> El dictamen y `Human Approval` inferiores conservan el corte del 09/10;
> no acreditan aprobación de este aporte ni revisión independiente. #86 sigue
> abierta y requiere los dictámenes de Lucía y Paris y la integración del líder.

## Result

Listo para el gate post-review de Victor. **No es un veredicto independiente**: lo redacta quien
implementó. La revisión y la validación de terceros llegan con el pull request («Revision JUP-105» y
«Validacion JUP-105»). Evidencia completa, con las salidas reales, en
[`docs/evidence/JUP-105-validation.md`](../../../../docs/evidence/JUP-105-validation.md).

Resumen: la épica «Migrar frontend de Economicon» queda cerrada. Esta tarjeta no construye nada nuevo:
endurece lo que quedó provisional, pone al día lo que otras tarjetas dejaron desfasado y declara qué se
migró y qué no.

- **`allowJs` pasa a `false`** con una sola línea de diferencia, y un control positivo demuestra que
  el compilador rechaza un `.js` importado desde TypeScript (`TS7016`; con `true` pasa en silencio).
- **El spike queda cerrado**, con el punto 13 como estado final: la migración técnica está completa y
  lo que queda abierto es de producto y de tooling.
- **Un único recuento de pantallas**, fechado y verificado contra el código, en el README del
  frontend: 9 rutas bajo sesión, 5 con backend y 4 de demostración, 3 de ellas sin rótulo.
- **Deuda documental saldada:** enlaces relativos rotos de 66 a 2 (los falsos positivos) y menciones a
  configuración local de agentes de 42 a 0, sin tocar ninguna cifra ni veredicto.
- **Hallazgos de la épica:** 21 revisados; 3 pasan a `Fixed` y 18 siguen `Open` con motivo y con quién
  da el siguiente paso. Se registran 4 hallazgos nuevos (`RF-105-001` a `RF-105-004`).

De los 9 criterios de la tarjeta, **7 se cumplen sin reservas y 2 con salvedades escritas**: el 1 (la
batería no queda del todo en verde: el `test` del backend falla 145 tests de JUP-047 en Windows,
`RF-105-004`) y el 5 (queda un comentario de un test, anotado en `RF-105-001`).

## Scope Reviewed

Diff de la rama frente a `develop` (`ceb6520`): **45 archivos, 2106 inserciones y 200 eliminaciones.**

- **Configuración y comentarios de `apps/frontend`:** `tsconfig.json` (una línea), el comentario de
  cabecera de `src/routes.tsx` y un comentario de `vite.config.ts`. No cambia ninguna línea de código.
- **`apps/frontend/README.md`:** tabla de rutas con el recuento.
- **Documentación viva:** `docs/spikes/frontend-migration.md`, `docs/architecture.md` (recuadro de
  `GET /billing/summary`), `docs/planning/JUP-097-frontend-data-gap-map.md` y el seguimiento de
  `docs/adr/ADR-0003-frontend-typescript.md`.
- **`openspec/findings/backlog.md`:** 21 filas actualizadas y 4 nuevas.
- **Registros históricos:** 25 archivos de `openspec/changes/archive/` con enlaces o referencias
  corregidos, 5 de ellos además con una nota fechada, y 5 evidencias de `docs/evidence/` (JUP-013,
  085, 093, 095 y 097). Solo cambia el destino de un enlace o el texto de una referencia, más las
  notas fechadas que se añaden al inicio de algunos; nunca una cifra, un resultado ni un veredicto.
- **Nuevo:** `docs/evidence/JUP-105-validation.md` y este change (`proposal`, `design`, `tasks`, la
  spec delta de `frontend-typescript-tooling` y este `review.md`).
- **En solo lectura, sin tocar:** `package.json`, `turbo.json`, `pnpm-workspace.yaml`,
  `pnpm-lock.yaml`, `.github/**`, `tools/**`, `packages/**` y `apps/backend`, `processor`,
  `azure-cost-api` y `monitoring`. Verificado con `git diff --name-only origin/develop...HEAD`.

## Checklist

Requisitos de [`specs/frontend-typescript-tooling/spec.md`](specs/frontend-typescript-tooling/spec.md):

- [x] **El código fuente ya no admite JavaScript:** `allowJs: false` y `typecheck` en verde sobre
  `src/` y `tests/`, que no contienen ningún `.js` ni `.jsx`.
- [x] **Un import de JavaScript hace fallar la comprobación de tipos:** control positivo con
  `TS7016` y salida 1; con `allowJs: true` el mismo archivo pasa.
- [x] **Rigor máximo y configuración local al paquete:** sin cambios (`strict: true`).
- [x] **El lint acepta TypeScript y no reporta violaciones:** 0 violaciones; la línea base de 49 ya
  no existe.
- [x] **El build de producción no regresiona:** `build` con salida 0, también desde la raíz.
  [ ] **El escenario de arranque de desarrollo no se ejercitó** en esta tarjeta: no se lanzó `dev`;
  JUP-103 lo verificó y aquí solo cambia una opción de tipos.

Criterios de la tarjeta (detalle en la evidencia, «Trazabilidad de los criterios de aceptación»):

- [x] 1. Batería desde la raíz. **Salvedad:** todo en verde menos el `test` del backend en Windows
  (145 tests de JUP-047, `RF-105-004`); el frontend (629), `processor` (448) y `azure-cost-api` (59)
  pasan, por mitades, sin caché.
- [x] 2. `allowJs` en `false`, frontend compila y pasa sus pruebas.
- [x] 3. Spike sin placeholder pendiente ni casilla sin marcar sin explicación; el punto 13 declara el
  estado final.
- [x] 4. Un único recuento de pantallas; README, `RF-095-002`, `RF-091-003` y el mapa de carencias
  coinciden.
- [x] 5. Ningún documento afirma ya que `/overview-legacy` es el único dashboard con datos reales ni
  que `Frontend tests` es obligatorio sin una nota. **Salvedad:** el comentario de cabecera de
  `DashboardPage.test.tsx` (línea 6), que es código de pruebas y no un documento.
- [x] 6. Cada hallazgo abierto con responsable y motivo; los cerrados en `Fixed` con evidencia.
- [x] 7. Deuda documental resuelta.
- [x] 8. Decisión sobre `/overview-legacy` y el módulo huérfano registrada (`RF-105-001` y
  `RF-105-002`).
- [x] 9. Estado final declarado sin ambigüedad (punto 13 del spike).

## Decisiones tomadas durante la implementación

El plan aprobado en el gate pre-código se mantuvo. Estas son las decisiones que no estaban previstas
o que corrigieron el plan:

1. **La spec se cambió con retirada y sustitución, no con modificación.** `openspec validate` no deja
   que un requisito modificado pierda un escenario, así que los dos requisitos que tenían que
   perderlo se retiraron y se sustituyeron por otros con nombre nuevo (`design.md`, decisión 2).
2. **Las menciones a configuración local son 42, no 41.** La medida al proponer filtraba por el
   contenido de la línea y no por la ruta del archivo, y descartó una línea de más. Se corrigió en
   `proposal.md`, `design.md` y `tasks.md` antes de ejecutar nada.
3. **Donde no hay equivalente versionado la redacción es neutral y no se inventó ningún comando**
   (comprobador local de DoD, protección de tests, procedimiento de mutación), igual que JUP-099. Lo
   que ya eran comandos reales se dejó con esos comandos.
4. **`docs/architecture.md` se corrigió aunque la tarjeta no lo pedía**: su recuadro decía que
   `GET /billing/summary` devolvía valores fijos. Se comprobó en el código del backend antes de
   reescribirlo.
5. **Los comentarios de `Layout.tsx` y de `DashboardPage.test.tsx` no se tocaron.** El gate limita los
   archivos de `apps/**`; se anotaron en el inventario de `RF-105-001`.
6. **Notas fechadas en 5 registros archivados**, a petición del líder tras la batería, para cumplir el
   criterio 5 sin excepción en los documentos. Solo se añadieron líneas (51 y 0 eliminadas).
7. **Los responsables de los hallazgos son categorías, no personas.** Trello es la fuente de verdad
   de las asignaciones y esta rama no lo consulta; el único nombre propio es Alejandro en
   `RF-093-001`, donde consta que falta su confirmación.
8. **La tarea 6.6 (pedir las tarjetas) se dio por ejecutada** por indicación del líder, que la hace en
   Trello de forma independiente; ningún número de tarjeta consta en el repositorio.
9. **`RF-093-001` se mantiene `Open`:** Paris no reproduce el fallo pero no aplicó la corrección, y
   Alejandro no hizo la comprobación.
10. **`RF-091-004` se cierra por lo que dice** (el dato ficticio ya no existe) y la falta de un motor
    de ahorro pasa a `RF-091-003`. Comprobado leyendo el código del backend, sin ejecutarlo.
11. **ADR: no aplica uno nuevo.** El endurecimiento de `allowJs` ejecuta la decisión 2 de ADR-0003, ya
    aceptada, y se anota en su seguimiento.

## Validation

La batería completa, con códigos de salida y conteos, está en la evidencia («Batería completa»).
Desde la raíz, con `corepack pnpm`, sin caché (`--force` o `TURBO_FORCE=true`, verificando
`cache bypass, force executing`) y con el entorno virtual de Python activo en cada ejecución:
`install --frozen-lockfile` sin tocar el lockfile, `lint`, `typecheck` y `build` en verde;
`openspec:validate` 55 de 55, `jup:check` y `jup:cleanup:check` en verde; `test` por mitades:
`azure-cost-api` 59, `processor` 448 (57 omitidos), `frontend` 629 en 53 archivos con un worker, y
`backend` **753 pasan y 145 fallan** (34 omitidos).

Los 145 fallos son de cuatro archivos de JUP-047 y su causa está medida con las trazas: en Windows
`asyncio` crea su bucle con `socketpair`, que sin `AF_UNIX` se implementa con una conexión TCP a
`127.0.0.1`, y esos tests prohíben abrir sockets. Hay 145 trazas con esa ruta para 145 fallos.

Lo que **no** se validó está enumerado en la evidencia («Lo que no se validó»), entre otras cosas: que
los tests de JUP-047 pasen en Linux; `corepack pnpm test` literal con los cuatro paquetes a la vez;
ninguna pantalla en un navegador ni el backend en ejecución; `RF-093-001` en la máquina de Alejandro;
los responsables en Trello; y la CI del pull request.

## Excepción del ciclo Red/Green

No se invocó el ciclo Red/Green, ni la mutación, ni la validación de QA por tarea: **la tarjeta no
añade ni cambia comportamiento**. Cambia una opción del compilador, dos comentarios y documentación.
La verificación son los comandos reales con su salida y el control positivo de `allowJs`, que hace de
prueba del mecanismo. La excepción está prevista en la decisión 10 de `design.md`.

## Review Findings

Cerrados (`Fixed`), con su evidencia:

- **`RF-091-004`** el dato ficticio de `/billing/summary` ya no existe (JUP-026 y JUP-055).
- **`RF-099-001`** 42 menciones sustituidas; la búsqueda del hallazgo da 0.
- **`RF-099-004`** 64 de 66 enlaces corregidos; quedan 2 falsos positivos.

Nuevos:

- **`RF-105-001`** retirar la ruta puente `/overview-legacy`, con el inventario de lo que arrastra
  (Low, carril `standard`).
- **`RF-105-002`** módulos sin consumidor: `src/data/demo/executiveCostDashboard.ts` y
  `src/hooks/useCostKpis.ts` (Low).
- **`RF-105-003`** nada comprueba los enlaces relativos al archivar (Low).
- **`RF-105-004`** los tests de JUP-047 del backend no pueden ejecutarse en Windows (Medium).

Reformulados o actualizados, sin cerrar: `RF-091-003`, `RF-095-002`, `RF-104-004` y `RF-093-001`. Los
otros 14 siguen `Open` con una nota de motivo.

Incidencias del proceso, para que no se repitan:

- **Una medida mía descartaba por contenido y no por ruta** (decisión 2): se detectó al repetirla con
  la búsqueda exacta del hallazgo, antes de cambiar nada.
- **Las búsquedas por línea no ven frases partidas entre dos renglones.** La búsqueda de afirmaciones
  superadas del grupo 3 dejó fuera 7 líneas de registros archivados, y salieron al comprobar el
  criterio 5 tras la batería; se repitió con búsqueda multilínea. Hubo que corregir también dos
  cifras de la evidencia que habían quedado cortas.
- **La herramienta bloqueó dos comandos** por texto con patrones de ruta o entrecomillado que
  interpretó como un borrado. En uno de ellos el anexo a la evidencia no llegó a escribirse; se
  comprobó antes de seguir y se rehízo con la herramienta de edición.
- **Dos explicaciones mías erróneas en la evidencia**, corregidas al revisar: la causa de la
  diferencia entre inserciones y eliminaciones del grupo 5 (dos líneas añadidas, no cuatro
  reajustadas) y el primer enunciado de `RF-105-004`, que quedó mal escrito.

## Risks / Follow-Ups

- **`RF-093-001` espera a Alejandro** en una consola externa. Pasa a `Fixed` cuando confirme sin
  contradecir la corrección.
- **`RF-105-004`:** la CI del pull request corre en Linux; si `Python tests (backend)` sale en verde,
  confirma que el fallo es de Windows y no del repositorio. Si saliera en rojo, hay que revisar la
  inferencia de la evidencia.
- **`develop` puede volver a avanzar.** Los pull requests #66 (JUP-017, añade un panel a `/`) y #69
  (JUP-036, cambia `ConversationsPage`) siguen abiertos: si se fusionan antes del cierre, hay que
  repetir el recuento de pantallas y el recorrido de enlaces.
- **Los enlaces de esta tarjeta bajan un nivel al archivar** (tarea 8.5): los de este change a
  `docs/` y a `openspec/`, y el del spike, que hoy no enlaza al change archivado de JUP-105 porque su
  carpeta lleva la fecha del archivado. Tras archivar, el recorrido debe seguir dando 2.
- **Roles del pull request** (con las etiquetas sin tildes y con guion que busca el check
  `JUP policy`): Liderazgo, Victor Mendez; Pairing/coautoria, Alejandro Aguado; Revision de PR, Lucia
  Mateo; Validacion, pruebas y documentacion, Paris Arcos. «Revision JUP-105» la publica Lucía y
  «Validacion JUP-105» Paris; ninguno de los dos sube commits a la rama. La respuesta de Paris sobre
  `RF-093-001` es evidencia de esta tarjeta: su validación debe repetirla o declararla no validada.
- **Tarjetas de los hallazgos:** `RF-104-001`, `RF-103-001`, `RF-103-002` y `RF-098-003` dicen
  «tarjeta pedida» por indicación del líder; esta rama no lo comprueba.
- **Efectos en la máquina de verificación:** ninguno persistente. El entorno virtual se activó dentro
  de cada ejecución, Docker no se tocó (sin proyectos de Compose; el único contenedor era el
  constructor interno de Docker Desktop) y los guiones de un solo uso viven fuera del repositorio. De
  los tres que editan archivos, solo el de corrección de enlaces (con su comprobación) tiene el texto
  en la evidencia; los que escriben las celdas del backlog y la comprobación de anclas no se
  versionan, y lo que cambiaron se verificó comparando el backlog con `HEAD` fila a fila.

## Human Approval

- Change: jup-105-close-frontend-migration
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-10-09
- Archive decision: archive
- Scope reviewed: las tareas 1.1 a 8.4 de `tasks.md` (35 de 37; quedan el archivado y el pull
  request); este `review.md`; la evidencia `docs/evidence/JUP-105-validation.md` (línea base,
  `allowJs`, recuento de pantallas, enlaces, menciones, hallazgos, spike, batería completa y
  trazabilidad de los criterios); y los cambios en `apps/frontend`, `docs/`, `openspec/findings/` y
  los registros archivados.
- Conditions approved: (1) **`RF-093-001` se mantiene `Open`**, a la espera de la comprobación de
  Alejandro en una consola externa; Paris no reproduce el fallo pero tampoco aplicó la corrección.
  (2) **El comentario de cabecera de `DashboardPage.test.tsx` se deja como está**, anotado en el
  inventario de `RF-105-001`; no se amplía el alcance aprobado en el gate pre-código. (3) **Los roles
  del pull request son los vigentes**: Liderazgo, Victor Mendez; Pairing/coautoria, Alejandro Aguado;
  Revision de PR, Lucia Mateo; Validacion, pruebas y documentacion, Paris Arcos.
- Resultado verificado: desde la raíz, sin caché y con `corepack pnpm`, `install --frozen-lockfile`,
  `lint`, `typecheck` y `build` en verde; `openspec:validate` 55 de 55, `jup:check` y
  `jup:cleanup:check` en verde; `test` por mitades con el frontend (629), `processor` (448) y
  `azure-cost-api` (59) en verde. Enlaces relativos rotos de 66 a 2 (los falsos positivos conocidos)
  y menciones a configuración local de 42 a 0.
- Salvedades aceptadas: **el criterio 1 no se da por cumplido del todo**: el `test` del backend falla
  145 tests de JUP-047 en Windows (`RF-105-004`), con causa medida y sin verificar en Linux; **el
  criterio 5** queda cumplido en los documentos y con una excepción en un comentario de código
  (`RF-105-001`). `RF-105-001` a `RF-105-004` quedan registrados como hallazgos `Open`, sin corregir
  en esta tarjeta.
- Constraints: la aprobación **no** sustituye la revisión y la validación del pull request
  («Revision JUP-105» y «Validacion JUP-105»), no acredita el CI y no autoriza fusionar. Ninguna ruta
  de solo lectura aparece en el diff de la rama.
- Required changes before archive: ninguno. Al archivar se corrigen en el mismo paso los enlaces
  relativos de la tarjeta y se añade al spike el enlace al change archivado (tarea 8.5).
- Notes: la decisión se registra a partir de la respuesta del líder del 2026-10-09 («punto 1 déjalo
  Open, punto 2 déjalo como está actualmente, punto 3 es correcto. Continúa»), dada tras pedirle que
  revisara este documento y decidiera esos tres puntos. No hubo una frase aparte de «aprobado»; si
  esa lectura fuera incorrecta, el bloque se corrige antes de abrir el pull request.
