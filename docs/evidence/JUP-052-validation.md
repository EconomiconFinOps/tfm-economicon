# JUP-052 â€” Evidencia de implementaciÃ³n

VerificaciÃ³n: 2026-10-03, Europe/Paris.
Origen: solicitud Â«Implementa JUP-052 â€” CD hacia DockerServerÂ».
Trello: https://trello.com/c/q3TahHoj
Rama: `ci/JUP-052-dockerserver-cd`, desde develop `6410950`.

## Resultado confirmado

El workflow valida el SHA integrado de develop reutilizando todos los jobs
tÃ©cnicos CI. El agente DockerServer comprueba elegibilidad, prepara una release
privada, ejecuta build/readiness/smoke y registra SHA/run id tras Ã©xito.
Incluye lock, recuperaciÃ³n tras reboot, fallo cerrado, rollback y pausa/resume.

[CI real de la rama](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37154781064):
**SUCCESS**, head `0471e9212f8e8068a48ba0e0082811085edf439b`, seis jobs tÃ©cnicos
verdes; JUP policy omitido por ser workflow_dispatch, no una PR.

Pruebas nuevas: **22** verdes (`pnpm cd:test`: 3 Node y 19 unittest).
Gobierno: jup:check:all, pr:check:test (57), ci:check:test (10),
repository:governance:test (13), openspec:validate (41), jup:cleanup:check,
local:test y docker:validate (31), todos en verde.
Build, lint y typecheck del workspace completados.
Frontend: 437/437 con `corepack pnpm --filter @finops/frontend exec vitest run --maxWorkers=1`.
Processor Linux/Python 3.12: 448 passed / 57 skipped. Los skipped dependen de
integraciones explÃ­citas y no se presentan como verificadas por esa suite.

Incidencias del entorno local preservadas: el fallback pnpm de Turbo usaba
una versiÃ³n distinta de pnpm 9; se resolviÃ³ anteponiendo un wrapper temporal
`pnpm.cmd` que invoca `corepack pnpm`. La primera suite frontend con workers
paralelos fallÃ³ en seis esperas temporizadas; el recorrido completo con un
worker pasÃ³. Processor en Windows/Python 3.14 fallÃ³ en la prueba preexistente
de profundidad JSON; en Linux/Python 3.12, como CI, pasÃ³. No se modificaron
esas pruebas ni se omitieron controles del pipeline.

## DockerServer real

Python 3.12.3, Engine 29.6.2, Compose 5.3.1. Root exclusivo del ensayo:
`/home/danteadmin/economicon-cd-validation`, puertos 19452â€“19462 / 19552â€“19562.

1. `validate-source`, SHA `e4a66a642b2d56b8a0e04b22e17eb57843bc900f`:
   nueve servicios saludables; salud HTTP, login demo, ingesta de costes,
   resumen con totales y job de documento completado: **5/5**.
2. Candidato `0471e9212f8e8068a48ba0e0082811085edf439b`: se cambiÃ³ Ãºnicamente
   la contraseÃ±a que lee el smoke en `.env`, manteniendo la configuraciÃ³n
   renderizada del servicio. Login real **401**, candidato detenido y
   SHA anterior todavÃ­a vigente y sano. `.env` restaurado en finally.
3. Mismo candidato con configuraciÃ³n correcta: **5/5**, promovido; anterior
   detenido conservando volÃºmenes.
4. `rollback`: anterior reactivado con imÃ¡genes locales, **5/5**, puntero
   recuperado y `manual_rollback=true`.
5. Readback: nueve contenedores, once puertos publicados, todos **127.0.0.1**.
   Al terminar se detuvieron los contenedores de ensayo; fuentes, secretos
   protegidos, volÃºmenes y manifest se conservaron. Otros stacks no modificados.

Primeros ensayos detectaron doble escape de dÃ³lares de Compose y esquemas
de conexiÃ³n incorrectos; corregidos en `8060fb3` y `e4a66a6` con regresiones.
Los primeros logs son fallos histÃ³ricos, no evidencias de validaciÃ³n positiva.

Logs originales fuera de Git:
`materiales/07-evidencias/JUP-052-implementacion-2026-10-03/`
del espacio Economicon: `runtime-drivers.log`, `recovery-runtime.log`,
`runtime-readback.log`, `agent-install.log`, `frontend-tests.log`,
`processor-linux312.log`. No contienen secretos. Las pruebas funcionales
usan credenciales generadas exclusivamente en el servidor.

## InstalaciÃ³n y lÃ­mites

Agente: `/home/danteadmin/economicon-cd/tools/cd/`; root automÃ¡tico:
`/home/danteadmin/economicon-cd-runtime`, base 19252. Timer de usuario habilitado
y activo; `Linger=yes`. Dos ejecuciones reales del servicio terminaron con
`Result=success`, `ExecMainStatus=0` y Â«CD workflow not yet integrated; no deploymentÂ».
El agente queda esperando la integraciÃ³n. No hay ejecuciÃ³n de PR con privilegios.

La selecciÃ³n y recuperaciÃ³n del agente se probaron con unittest; la parte
Compose/smoke/rollback se ejecutÃ³ realmente. **No se ha acreditado todavÃ­a
una promociÃ³n automÃ¡tica desde un run CD real integrado en develop.** Tampoco
se simulÃ³ un reboot del host compartido. GuÃ­a:
[dockerserver-cd](../deployment/dockerserver-cd.md), ADR-0018 Proposed.

Roles originales conservados: Victor liderazgo, Alejandro pairing, Lucia
revisiÃ³n, Paris validaciÃ³n. ImplementaciÃ³n tÃ©cnica preparada por solicitud del
usuario; no se inventa una sesiÃ³n de pairing ni las dos reviews humanas. Rama
publicada y cuerpo de PR preparado; no se abriÃ³ una PR atribuyendo liderazgo
a otra persona ni se hizo merge/cierre Trello. Siguiente paso: liderazgo abre
la PR, registra participaciÃ³n real, obtiene revisiÃ³n/validaciÃ³n e integra;
despuÃ©s, contrastar run CD exitoso con state.json y cerrar la tarjeta.

## Entrega para revisiÃ³n â€” 2026-10-04

El usuario autoriza abrir la PR desde la cuenta de Alejandro y solicitar las
reviews. Alejandro asume liderazgo, Victor pairing, Lucia revisiÃ³n y Paris
validaciÃ³n; se actualizan Trello y Participacion. La nota del 03/10 sobre no
abrir PR queda superada por esta autorizaciÃ³n. Pairing humano sigue pendiente
de acreditaciÃ³n. Rama actualizada con develop c3aa9d6: se conservan los nuevos
checks de recuperaciÃ³n y el contrato de embedding del backend. El ensayo
Docker previo cubre e4a66a6/0471e92, no acredita por sÃ­ mismo el nuevo Ã¡rbol;
la validaciÃ³n formal deberÃ¡ comprobar el head actualizado. Cambio tÃ©cnico
archivado en `openspec/changes/archive/2026-10-04-jup-052-dockerserver-cd/`;
primera promociÃ³n automÃ¡tica y actuaciones humanas siguen pendientes.

## Primera vuelta de Revision Lucia (096be34 â†’ c3f64ed) â€” 2026-10-05

Origen: [Revision JUP-052](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#pullrequestreview-5410106030)
sobre `096be34dfe9113815c5cbc4ee42194e5dc721d94`. La peticiÃ³n de cambios no
queda levantada por la implementaciÃ³n del autor; Lucia debe revisar el nuevo
head y Paris publicar Validacion JUP-052.

| PeticiÃ³n | CorrecciÃ³n y regresiÃ³n propia |
| --- | --- |
| 1. Pilas huÃ©rfanas tras promociÃ³n/rollback | ReconciliaciÃ³n de releases inactivas en cada poll y antes de ocupar slot. Down fallido tras promover/rollback se reintenta incluso sin nuevo SHA o con pausa. Test con puertos simulados completa el siguiente SHA reutilizando el slot sin colisiÃ³n. Fuentes y volÃºmenes conservados. |
| 2. Current rota bloquea candidatos | Error saneado en recovery.json; continÃºa consulta y candidato elegible puede promover. Poll completo probado con recuperaciÃ³n actual fallida. |
| 3. Down oculta fallo | Failure.json antes de down; conserva error original y registra tipo de fallo de limpieza. RegresiÃ³n build+down fallidos comprueba identidad de excepciÃ³n y evidencia. |
| 4. .preparing residual | Copia incompleta se elimina/reintenta bajo lock. RegresiÃ³n conserva fuente vÃ¡lida y elimina marcador residual. |
| 5. ADR duplicado | ADR-0018, libre en develop y diffs de PR abiertas consultados el 05/10; fila en tabla canÃ³nica, referencias y enlace archivado corregidos. ADR-0017 JUP-022 conservado. |
| 6. AGENTS ajeno/enlace roto en Git | Se retira de la PR el cambio de AGENTS. El archivo de trabajo y continuidad locales conservan la instrucciÃ³n humana de leer/mantener docs/continuidad; no se elimina documentaciÃ³n ni se publica el enlace ausente del Ã¡rbol Git. |
| 7. Pruebas insuficientes | Poll feliz fetch/archive/prepare/deploy, carrera FETCH_HEAD, carrera tras preparaciÃ³n, head tras smoke, slot, lock no bloqueante simulado y real Linux, permisos 600, SHA completo, filtro develop, extracciÃ³n data contra symlink externo, variantes dotenv anidadas, resume y validate-source. |

VerificaciÃ³n propia sobre fuente corregida:

- `corepack pnpm cd:test`: 3 Node correctas; 36 Python, 35 correctas y 1
  omitida en Windows (lock Linux). Suite Python en copia temporal DockerServer
  Python **3.12.3**: **36/36**, sin skips; incluye permisos reales y contenciÃ³n
  de dos handles flock. Compose/GitHub simulados, no despliegue Docker real.
- Diez mutantes seleccionados para esta vuelta (lista cerrada, no cobertura
  general de todas las guardas): **10/10 detectados, cero supervivientes**:
  fetch, current=head, slot, LOCK_NB, chmod
  dotenv, SHA corto, filtro branch, filtro tar, ignore dotenv y guard post-prepare.
  Sondas en copias desechables fuera del checkout; no mutaciÃ³n de rama.
- OpenSpec 45/45; tests CI/polÃ­tica/gobierno 80/80; diff check correcto.
  Los logs y script de mutantes se conservan en el espacio de trabajo, en
  `materiales/07-evidencias/JUP-052-review-fixes-20261005/`.

DisposiciÃ³n de las recomendaciones no bloqueantes de Lucia:

| RecomendaciÃ³n | DecisiÃ³n |
| --- | --- |
| No reconstruir SHA fallido sin lÃ­mite | Implementado: pausa por SHA; resume habilita retry conservando failure. |
| Validate-source/proyecto por root | Implementado rechazo de SHA existente y pausa manual, hash root en proyectos nuevos. Documentada promociÃ³n del state y responsabilidad del operador de relacionar etiqueta/source; no acredita elegibilidad GitHub. |
| Loopback no aÃ­sla usuarios locales | Documentada confianza en usuarios del host y SQL insegura local. Se conservan puertos para operaciones de desarrollo aprobadas; sin datos reales. |
| head_repository null | Falla cerrado sin AttributeError; regresiÃ³n de gate incluida. |
| Dispatch desde otra rama | GuÃ­a precisa jobs omitidos y filtro branch del agente. |
| Logs no sobreviven down | Comentario y guÃ­a corregidos: volÃºmenes/fuentes sÃ­, logs contenedor no. |
| Head avanza durante build/smoke | Recheck aÃ±adido antes de promover; regresiÃ³n conserva current. Carrera inmediatamente posterior a API documentada, sin promesa transaccional con GitHub. |
| Rutas systemd y CI duplicada con JUP-051 | Se mantiene instalaciÃ³n especÃ­fica del host; guÃ­a indica adaptar unidad. Doble CI aceptada/documentada por ahora. |

No validado en esta correcciÃ³n: Docker/Compose real sobre este nuevo cÃ³digo,
caÃ­das reales del motor, reboot, primera promociÃ³n automÃ¡tica, pruebas
funcionales independientes Paris y pairing Victor. Timer instalado y stack
compartido no modificados; no secretos impresos ni promociÃ³n al root automÃ¡tico.

## Segunda vuelta de Revision Lucia (base c3f64ed) â€” 2026-10-05

[Review completa](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#pullrequestreview-5416682895)
confirma los siete puntos anteriores y pide cuatro cambios nuevos. Esta secciÃ³n
acredita las pruebas del autor para el delta posterior a c3f64ed; no atribuye
la validaciÃ³n Docker anterior de Paris a este nuevo cÃ³digo.

| Pendiente | Resultado y regresiÃ³n |
| --- | --- |
| Reconcile aborta en primera release | Intenta todas las releases y .preparing vÃ¡lidas, recoge SHA/tipos y lanza CleanupError al final. RegresiÃ³n A falla, B se detiene, current C intacta, D.preparing eliminada y copia sin SHA preservada. La guÃ­a explica detener/verificar proyecto y mover directorio completo a retired bajo lock; no borrar archivos sueltos ni eludir pila viva. |
| Guardas sin prueba | Segundo reconcile aÃºn fallido bloquea fetch y deploy tras consultar elegibilidad; failure.json de otro SHA permite candidato. Pruebas de .preparing vÃ¡lida/noSHA y de esas dos guardas. |
| Error de API despuÃ©s de smoke | No pone en cuarentena permanente el SHA sano; conserva el fallo real anterior, registra eligibility-unavailable en events, intenta down y propaga el error original. URLError, HTTP403 y HTTP503 probados, tambiÃ©n down fallido; siguiente poll promueve sin resume. Head avanzado registra superseded separado, conserva state y evidencia anterior. |
| Recovery obsoleta | Archivo refleja las fases aÃºn pendientes del Ãºltimo intento y timestamp. Se elimina tras limpieza/recuperaciÃ³n correctas o reemplazo sano con cleanup correcto. Regresiones recuperaciÃ³n fallaâ†’funciona, cleanup bien con current aÃºn rota y reemplazo sano. |

Pruebas propias del delta, sin Docker/Compose real:

- `cd:test`: 3 Node correctas; Python43, Windows42pass/1skipLinux. Tres
  ejecuciones Windows de la suite Python correctas para contrastar el aviso
  externo WinError145; este muestreo **no descarta ni diagnostica el flake**.
- Copia temporal DockerServer, Python3.12.3, **43/43 Python** sin skips,
  permisos/flock Linux reales; Docker/GitHub de las regresiones simulados.
- **13/13 sondas de mutantes seleccionadas**, cero supervivientes: las diez
  anteriores mÃ¡s rama .preparing de reconcile, segundo reconcile y cuarentena
  por SHA ajeno. No es cobertura exhaustiva ni un score general de mutaciÃ³n.
- OpenSpec45/45 y herramientas CI/polÃ­tica/gobierno80/80. Logs y script de
  sondas en `materiales/07-evidencias/JUP-052-review2-fixes-20261005/` del espacio.

DisposiciÃ³n de recomendaciones de segunda vuelta:

| RecomendaciÃ³n | DecisiÃ³n |
| --- | --- |
| Coste histÃ³rico de reconcile | Mantener barrido completo ante interrupciones/arranques externos; guÃ­a fija polÃ­tica operativa de current, previous y Ãºltimo fallo Ãºtil, archivando otros fuera de releases despuÃ©s de verificar down/ausencia. Sin borrado automÃ¡tico ni coste medido. |
| Evidencia de fallos/carreras | HistÃ³rico privado events por intento, reason distinto para carrera/red/fallo funcional. Carrera/red no sobrescriben failure.json; reintento exitoso aÃ±ade resolved_at. RetenciÃ³n manual documentada. |
| Resume despuÃ©s de rollback | Mantener semÃ¡ntica explÃ­cita, documentar riesgo de volver a intentar la release rota. Operador comprueba head/correcciÃ³n antes de reanudar; no se promete elegir versiÃ³n mÃ¡s segura. |
| SHA congelado en slot distinto | No migrar config inmutable/datos automÃ¡ticamente. GuÃ­a pide conservar pausa y usar nuevo SHA/root aislado si prepare rechaza slot; no repetir resume ni editar puertos in-place. Riesgo no ensayado con Docker real. |
| Flake Windows | Tres muestras correctas, causa no establecida. Linux es control principal del agente; no se cambia tempfile ni se silencian fallos sin reproducciÃ³n. |

Paris publicÃ³ [Validacion JUP-052 favorable sobre c3f64ed](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#pullrequestreview-5412457330)
con Docker/Compose reales en Ubuntu y lÃ­mites de API/Git/fallos simulados.
Ese ensayo no acredita este delta: se solicita revalidaciÃ³n incremental a Paris
y relectura a Lucia. Agente instalado, timer y stack compartido no modificados;
sin primera promociÃ³n automÃ¡tica, reboot, merge ni pairing Victor acreditados.

## Tercera vuelta de Revision Lucia (base 028323e) â€” 2026-10-05

[RevisiÃ³n completa](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#pullrequestreview-5417957537)
confirma los cuatro puntos de la segunda vuelta y solicita tres correcciones.

- Escrituras de failure/events y estado diagnÃ³stico son best effort, con
  aviso de tipo saneado: no impiden down ni sustituyen la causa original.
  RegresiÃ³n events como fichero, fallo de escritura failure y down fallido,
  en combinaciones; API falla tras smoke y falla event; recovery/event fallan
  tras promociÃ³n con cleanup pendiente. state.json mantiene escritura obligatoria.
- resolved_at se intenta inmediatamente despuÃ©s del commit de promociÃ³n,
  antes de cleanup. CleanupError actualiza recovery pendiente con todos sus
  SHA/tipos y un evento histÃ³rico; CLI advierte que current ya cambiÃ³. Poll
  reintenta resolved_at al recuperar current incluso con API offline; Already
  deployed tambiÃ©n lo reintenta sin borrar cleanup no comprobado.
- Rollback bajo pausa manual es idempotente: verifica current y limpia otras
  releases sin volver a la retirada. RepeticiÃ³n tras CleanupError probada con
  state idÃ©ntico, sin up de la retirada, recovery borrada tras Ã©xito. Si la
  reverificaciÃ³n falla, conserva current y no la detiene.

Pruebas propias: **53/53 Python Linux3.12.3**, Windows52pass/1skipLinux y
3 Node CD. Docker/GitHub simulados; Linux permisos/flock reales, no despliegue
del agente instalado. **21/21 sondas seleccionadas detectadas**, lista cerrada:
las trece anteriores, agregaciÃ³n completa de errores, borrado de recovery en
cleanup de transiciÃ³n, filtro de fase cleanup, respeto retry_allowed en poll,
resolved_at, reconcile de validate-source, protecciÃ³n de evidencia e idempotencia
rollback. No cobertura universal ni score general de mutaciÃ³n.

Recomendaciones: se aÃ±aden regresiones de los seis mutantes seÃ±alados. La guÃ­a
acota quÃ© cleanup se guarda en events frente a recovery/CLI. Se mantiene timer
5min sin backoff adaptativo/reutilizar smoke; documentado coste mÃ¡ximo288/dÃ­a,
pausa operativa ante API persistentemente indisponible y retenciÃ³n privada manual.
No se diagnostica ni silencia flake Windows por falta de reproducciÃ³n.

Evidencias en `materiales/07-evidencias/JUP-052-review3-fixes-20261005/` del
espacio: logs, sondas y reviews. Paris c3f64ed sigue histÃ³rica; se requiere
revalidaciÃ³n del delta final y relectura Lucia. Sin stack compartido, reboot,
primera promociÃ³n ni pairing acreditado.

OpenSpec45/45, tooling80/80 y trazabilidad/higiene correctos. Base actualizada
con develop54bbbcd (ADR/documentación, sin cambios del agente CD); ADR0002
Accepted de JUP078 y fila ADR0018 Proposed preservadas. OpenSpec/trazabilidad/
higiene repetidos tras la actualización documental; se solicita revalidación
sobre el head final, no se atribuye a validaciones anteriores.
