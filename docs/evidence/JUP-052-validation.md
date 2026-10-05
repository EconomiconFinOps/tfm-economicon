# JUP-052 — Evidencia de implementación

Verificación: 2026-10-03, Europe/Paris.
Origen: solicitud «Implementa JUP-052 — CD hacia DockerServer».
Trello: https://trello.com/c/q3TahHoj
Rama: `ci/JUP-052-dockerserver-cd`, desde develop `6410950`.

## Resultado confirmado

El workflow valida el SHA integrado de develop reutilizando todos los jobs
técnicos CI. El agente DockerServer comprueba elegibilidad, prepara una release
privada, ejecuta build/readiness/smoke y registra SHA/run id tras éxito.
Incluye lock, recuperación tras reboot, fallo cerrado, rollback y pausa/resume.

[CI real de la rama](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37154781064):
**SUCCESS**, head `0471e9212f8e8068a48ba0e0082811085edf439b`, seis jobs técnicos
verdes; JUP policy omitido por ser workflow_dispatch, no una PR.

Pruebas nuevas: **22** verdes (`pnpm cd:test`: 3 Node y 19 unittest).
Gobierno: jup:check:all, pr:check:test (57), ci:check:test (10),
repository:governance:test (13), openspec:validate (41), jup:cleanup:check,
local:test y docker:validate (31), todos en verde.
Build, lint y typecheck del workspace completados.
Frontend: 437/437 con `corepack pnpm --filter @finops/frontend exec vitest run --maxWorkers=1`.
Processor Linux/Python 3.12: 448 passed / 57 skipped. Los skipped dependen de
integraciones explícitas y no se presentan como verificadas por esa suite.

Incidencias del entorno local preservadas: el fallback pnpm de Turbo usaba
una versión distinta de pnpm 9; se resolvió anteponiendo un wrapper temporal
`pnpm.cmd` que invoca `corepack pnpm`. La primera suite frontend con workers
paralelos falló en seis esperas temporizadas; el recorrido completo con un
worker pasó. Processor en Windows/Python 3.14 falló en la prueba preexistente
de profundidad JSON; en Linux/Python 3.12, como CI, pasó. No se modificaron
esas pruebas ni se omitieron controles del pipeline.

## DockerServer real

Python 3.12.3, Engine 29.6.2, Compose 5.3.1. Root exclusivo del ensayo:
`/home/danteadmin/economicon-cd-validation`, puertos 19452–19462 / 19552–19562.

1. `validate-source`, SHA `e4a66a642b2d56b8a0e04b22e17eb57843bc900f`:
   nueve servicios saludables; salud HTTP, login demo, ingesta de costes,
   resumen con totales y job de documento completado: **5/5**.
2. Candidato `0471e9212f8e8068a48ba0e0082811085edf439b`: se cambió únicamente
   la contraseña que lee el smoke en `.env`, manteniendo la configuración
   renderizada del servicio. Login real **401**, candidato detenido y
   SHA anterior todavía vigente y sano. `.env` restaurado en finally.
3. Mismo candidato con configuración correcta: **5/5**, promovido; anterior
   detenido conservando volúmenes.
4. `rollback`: anterior reactivado con imágenes locales, **5/5**, puntero
   recuperado y `manual_rollback=true`.
5. Readback: nueve contenedores, once puertos publicados, todos **127.0.0.1**.
   Al terminar se detuvieron los contenedores de ensayo; fuentes, secretos
   protegidos, volúmenes y manifest se conservaron. Otros stacks no modificados.

Primeros ensayos detectaron doble escape de dólares de Compose y esquemas
de conexión incorrectos; corregidos en `8060fb3` y `e4a66a6` con regresiones.
Los primeros logs son fallos históricos, no evidencias de validación positiva.

Logs originales fuera de Git:
`materiales/07-evidencias/JUP-052-implementacion-2026-10-03/`
del espacio Economicon: `runtime-drivers.log`, `recovery-runtime.log`,
`runtime-readback.log`, `agent-install.log`, `frontend-tests.log`,
`processor-linux312.log`. No contienen secretos. Las pruebas funcionales
usan credenciales generadas exclusivamente en el servidor.

## Instalación y límites

Agente: `/home/danteadmin/economicon-cd/tools/cd/`; root automático:
`/home/danteadmin/economicon-cd-runtime`, base 19252. Timer de usuario habilitado
y activo; `Linger=yes`. Dos ejecuciones reales del servicio terminaron con
`Result=success`, `ExecMainStatus=0` y «CD workflow not yet integrated; no deployment».
El agente queda esperando la integración. No hay ejecución de PR con privilegios.

La selección y recuperación del agente se probaron con unittest; la parte
Compose/smoke/rollback se ejecutó realmente. **No se ha acreditado todavía
una promoción automática desde un run CD real integrado en develop.** Tampoco
se simuló un reboot del host compartido. Guía:
[dockerserver-cd](../deployment/dockerserver-cd.md), ADR-0018 Proposed.

Roles originales conservados: Victor liderazgo, Alejandro pairing, Lucia
revisión, Paris validación. Implementación técnica preparada por solicitud del
usuario; no se inventa una sesión de pairing ni las dos reviews humanas. Rama
publicada y cuerpo de PR preparado; no se abrió una PR atribuyendo liderazgo
a otra persona ni se hizo merge/cierre Trello. Siguiente paso: liderazgo abre
la PR, registra participación real, obtiene revisión/validación e integra;
después, contrastar run CD exitoso con state.json y cerrar la tarjeta.

## Entrega para revisión — 2026-10-04

El usuario autoriza abrir la PR desde la cuenta de Alejandro y solicitar las
reviews. Alejandro asume liderazgo, Victor pairing, Lucia revisión y Paris
validación; se actualizan Trello y Participacion. La nota del 03/10 sobre no
abrir PR queda superada por esta autorización. Pairing humano sigue pendiente
de acreditación. Rama actualizada con develop c3aa9d6: se conservan los nuevos
checks de recuperación y el contrato de embedding del backend. El ensayo
Docker previo cubre e4a66a6/0471e92, no acredita por sí mismo el nuevo árbol;
la validación formal deberá comprobar el head actualizado. Cambio técnico
archivado en `openspec/changes/archive/2026-10-04-jup-052-dockerserver-cd/`;
primera promoción automática y actuaciones humanas siguen pendientes.

## Primera vuelta de Revision Lucia (096be34 → c3f64ed) — 2026-10-05

Origen: [Revision JUP-052](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#pullrequestreview-5410106030)
sobre `096be34dfe9113815c5cbc4ee42194e5dc721d94`. La petición de cambios no
queda levantada por la implementación del autor; Lucia debe revisar el nuevo
head y Paris publicar Validacion JUP-052.

| Petición | Corrección y regresión propia |
| --- | --- |
| 1. Pilas huérfanas tras promoción/rollback | Reconciliación de releases inactivas en cada poll y antes de ocupar slot. Down fallido tras promover/rollback se reintenta incluso sin nuevo SHA o con pausa. Test con puertos simulados completa el siguiente SHA reutilizando el slot sin colisión. Fuentes y volúmenes conservados. |
| 2. Current rota bloquea candidatos | Error saneado en recovery.json; continúa consulta y candidato elegible puede promover. Poll completo probado con recuperación actual fallida. |
| 3. Down oculta fallo | Failure.json antes de down; conserva error original y registra tipo de fallo de limpieza. Regresión build+down fallidos comprueba identidad de excepción y evidencia. |
| 4. .preparing residual | Copia incompleta se elimina/reintenta bajo lock. Regresión conserva fuente válida y elimina marcador residual. |
| 5. ADR duplicado | ADR-0018, libre en develop y diffs de PR abiertas consultados el 05/10; fila en tabla canónica, referencias y enlace archivado corregidos. ADR-0017 JUP-022 conservado. |
| 6. AGENTS ajeno/enlace roto en Git | Se retira de la PR el cambio de AGENTS. El archivo de trabajo y continuidad locales conservan la instrucción humana de leer/mantener docs/continuidad; no se elimina documentación ni se publica el enlace ausente del árbol Git. |
| 7. Pruebas insuficientes | Poll feliz fetch/archive/prepare/deploy, carrera FETCH_HEAD, carrera tras preparación, head tras smoke, slot, lock no bloqueante simulado y real Linux, permisos 600, SHA completo, filtro develop, extracción data contra symlink externo, variantes dotenv anidadas, resume y validate-source. |

Verificación propia sobre fuente corregida:

- `corepack pnpm cd:test`: 3 Node correctas; 36 Python, 35 correctas y 1
  omitida en Windows (lock Linux). Suite Python en copia temporal DockerServer
  Python **3.12.3**: **36/36**, sin skips; incluye permisos reales y contención
  de dos handles flock. Compose/GitHub simulados, no despliegue Docker real.
- Diez mutantes seleccionados para esta vuelta (lista cerrada, no cobertura
  general de todas las guardas): **10/10 detectados, cero supervivientes**:
  fetch, current=head, slot, LOCK_NB, chmod
  dotenv, SHA corto, filtro branch, filtro tar, ignore dotenv y guard post-prepare.
  Sondas en copias desechables fuera del checkout; no mutación de rama.
- OpenSpec 45/45; tests CI/política/gobierno 80/80; diff check correcto.
  Los logs y script de mutantes se conservan en el espacio de trabajo, en
  `materiales/07-evidencias/JUP-052-review-fixes-20261005/`.

Disposición de las recomendaciones no bloqueantes de Lucia:

| Recomendación | Decisión |
| --- | --- |
| No reconstruir SHA fallido sin límite | Implementado: pausa por SHA; resume habilita retry conservando failure. |
| Validate-source/proyecto por root | Implementado rechazo de SHA existente y pausa manual, hash root en proyectos nuevos. Documentada promoción del state y responsabilidad del operador de relacionar etiqueta/source; no acredita elegibilidad GitHub. |
| Loopback no aísla usuarios locales | Documentada confianza en usuarios del host y SQL insegura local. Se conservan puertos para operaciones de desarrollo aprobadas; sin datos reales. |
| head_repository null | Falla cerrado sin AttributeError; regresión de gate incluida. |
| Dispatch desde otra rama | Guía precisa jobs omitidos y filtro branch del agente. |
| Logs no sobreviven down | Comentario y guía corregidos: volúmenes/fuentes sí, logs contenedor no. |
| Head avanza durante build/smoke | Recheck añadido antes de promover; regresión conserva current. Carrera inmediatamente posterior a API documentada, sin promesa transaccional con GitHub. |
| Rutas systemd y CI duplicada con JUP-051 | Se mantiene instalación específica del host; guía indica adaptar unidad. Doble CI aceptada/documentada por ahora. |

No validado en esta corrección: Docker/Compose real sobre este nuevo código,
caídas reales del motor, reboot, primera promoción automática, pruebas
funcionales independientes Paris y pairing Victor. Timer instalado y stack
compartido no modificados; no secretos impresos ni promoción al root automático.

## Segunda vuelta de Revision Lucia (base c3f64ed) — 2026-10-05

[Review completa](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#pullrequestreview-5416682895)
confirma los siete puntos anteriores y pide cuatro cambios nuevos. Esta sección
acredita las pruebas del autor para el delta posterior a c3f64ed; no atribuye
la validación Docker anterior de Paris a este nuevo código.

| Pendiente | Resultado y regresión |
| --- | --- |
| Reconcile aborta en primera release | Intenta todas las releases y .preparing válidas, recoge SHA/tipos y lanza CleanupError al final. Regresión A falla, B se detiene, current C intacta, D.preparing eliminada y copia sin SHA preservada. La guía explica detener/verificar proyecto y mover directorio completo a retired bajo lock; no borrar archivos sueltos ni eludir pila viva. |
| Guardas sin prueba | Segundo reconcile aún fallido bloquea fetch y deploy tras consultar elegibilidad; failure.json de otro SHA permite candidato. Pruebas de .preparing válida/noSHA y de esas dos guardas. |
| Error de API después de smoke | No pone en cuarentena permanente el SHA sano; conserva el fallo real anterior, registra eligibility-unavailable en events, intenta down y propaga el error original. URLError, HTTP403 y HTTP503 probados, también down fallido; siguiente poll promueve sin resume. Head avanzado registra superseded separado, conserva state y evidencia anterior. |
| Recovery obsoleta | Archivo refleja las fases aún pendientes del último intento y timestamp. Se elimina tras limpieza/recuperación correctas o reemplazo sano con cleanup correcto. Regresiones recuperación falla→funciona, cleanup bien con current aún rota y reemplazo sano. |

Pruebas propias del delta, sin Docker/Compose real:

- `cd:test`: 3 Node correctas; Python43, Windows42pass/1skipLinux. Tres
  ejecuciones Windows de la suite Python correctas para contrastar el aviso
  externo WinError145; este muestreo **no descarta ni diagnostica el flake**.
- Copia temporal DockerServer, Python3.12.3, **43/43 Python** sin skips,
  permisos/flock Linux reales; Docker/GitHub de las regresiones simulados.
- **13/13 sondas de mutantes seleccionadas**, cero supervivientes: las diez
  anteriores más rama .preparing de reconcile, segundo reconcile y cuarentena
  por SHA ajeno. No es cobertura exhaustiva ni un score general de mutación.
- OpenSpec45/45 y herramientas CI/política/gobierno80/80. Logs y script de
  sondas en `materiales/07-evidencias/JUP-052-review2-fixes-20261005/` del espacio.

Disposición de recomendaciones de segunda vuelta:

| Recomendación | Decisión |
| --- | --- |
| Coste histórico de reconcile | Mantener barrido completo ante interrupciones/arranques externos; guía fija política operativa de current, previous y último fallo útil, archivando otros fuera de releases después de verificar down/ausencia. Sin borrado automático ni coste medido. |
| Evidencia de fallos/carreras | Histórico privado events por intento, reason distinto para carrera/red/fallo funcional. Carrera/red no sobrescriben failure.json; reintento exitoso añade resolved_at. Retención manual documentada. |
| Resume después de rollback | Mantener semántica explícita, documentar riesgo de volver a intentar la release rota. Operador comprueba head/corrección antes de reanudar; no se promete elegir versión más segura. |
| SHA congelado en slot distinto | No migrar config inmutable/datos automáticamente. Guía pide conservar pausa y usar nuevo SHA/root aislado si prepare rechaza slot; no repetir resume ni editar puertos in-place. Riesgo no ensayado con Docker real. |
| Flake Windows | Tres muestras correctas, causa no establecida. Linux es control principal del agente; no se cambia tempfile ni se silencian fallos sin reproducción. |

Paris publicó [Validacion JUP-052 favorable sobre c3f64ed](https://github.com/EconomiconFinOps/tfm-economicon/pull/73#pullrequestreview-5412457330)
con Docker/Compose reales en Ubuntu y límites de API/Git/fallos simulados.
Ese ensayo no acredita este delta: se solicita revalidación incremental a Paris
y relectura a Lucia. Agente instalado, timer y stack compartido no modificados;
sin primera promoción automática, reboot, merge ni pairing Victor acreditados.
