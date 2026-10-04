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
[dockerserver-cd](../deployment/dockerserver-cd.md), ADR-0017 Proposed.

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
