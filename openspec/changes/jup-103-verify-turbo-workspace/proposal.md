JUP: JUP-103
Trello: https://trello.com/c/P33co27E/95-jup-103

## Why

Desde [JUP-093](../archive/2026-09-06-jup-093-configure-typescript/) el hallazgo `RF-093-001` impide
usar los scripts de la raíz (`lint`, `build`, `test`, `typecheck`) en al menos una máquina Windows
del equipo: turbo lanza cada tarea con un pnpm `v11.9.0` en lugar del `9.0.0` que fija
`packageManager`. Seis tarjetas de frontend (JUP-093, 094, 095, 097, 098 y 099) han tenido que
verificar con el sustituto `corepack pnpm --filter @finops/frontend <script>`, que no pasa por turbo,
y documentar la sustitución cada vez. Nadie ha comprobado todavía que el frontend migrado participe
bien en el pipeline del monorepo, que es lo que cierra F4 de la épica de migración.

El hallazgo llegó a esta tarjeta sin causa conocida. Al verificar el alcance contra el código
(2026-10-03, `develop` en `dad5662`) la causa quedó localizada y no está en el repositorio:

- `corepack pnpm lint` falla en las 4 tareas; **`pnpm lint`, sin `corepack`, pasa las 4**.
- La máquina tiene un pnpm `11.9.0` instalado globalmente con npm (`%APPDATA%\npm\pnpm.cmd`) y
  **nunca se ejecutó `corepack enable`**: no existe el lanzador de pnpm de corepack en el `PATH`.
- turbo lanza cada tarea como `pnpm run <script>` resolviendo `pnpm` por `PATH`, así que ejecuta el
  global. Ese pnpm hereda la variable `COREPACK_ROOT` del `corepack pnpm` exterior, deduce que lo
  invocó corepack y se niega a cambiar a la versión fijada.
- En CI no ocurre porque cada job ejecuta `corepack enable` antes de usar pnpm.

Es decir: el repositorio documenta `corepack pnpm <script>` como forma de invocación, pero no
documenta el paso previo que la hace funcionar a través de turbo. Ese hueco es lo que hay que cerrar.

## What Changes

- **Reproducir y registrar la causa** de `RF-093-001` con las salidas reales, antes de corregir nada.
- **Corregir la máquina afectada** activando los lanzadores de corepack (`corepack enable`), de modo
  que el `pnpm` del `PATH` sea el `9.0.0` fijado también dentro de las tareas de turbo. Es un cambio
  de entorno, no del repositorio (ver `design.md`, decisión 2).
- **Documentar el requisito previo** en `README.md`: el paso de activación por única vez, un comando
  de diagnóstico de una línea (`corepack pnpm exec pnpm --version`) y qué hacer si existe un pnpm
  global de otra versión. De paso, alinear el bloque "Con Turborepo", que hoy usa `pnpm install` y
  `pnpm dev` sin `corepack`, con el resto del documento.
- **Verificar la batería desde la raíz** vía turbo (`lint`, `build`, `test`, `typecheck`) sin
  sustitutos, con salidas de antes y de después.
- **Verificar `pnpm dev`**: que turbo arranca en paralelo frontend, backend, processor y Azure Cost
  API.
- **Verificar el grafo de turbo**: que `@finops/frontend` tiene sus tareas y que `build` respeta las
  dependencias internas del workspace.
- **Preguntar al resto del equipo** si lo reproduce, con el comando de diagnóstico, y dejar escrito
  el resultado por persona.
- **Cerrar `RF-093-001`** en `openspec/findings/backlog.md` con la causa documentada, corrigiendo las
  dos afirmaciones del hallazgo que resultaron inexactas.
- **Dejar F4 cerrada en el spike** `docs/spikes/frontend-migration.md`: la tarjeta de Docker marcada
  como resuelta por JUP-049 y JUP-050, sin tarjeta propia, y el marcador
  `jup-0xx-verificar-turbo-workspace` sustituido por `jup-103-verify-turbo-workspace`.

No se modifica `package.json`, `turbo.json`, `pnpm-lock.yaml` ni `.github/workflows/ci.yml`. No se
cambia de gestor de paquetes ni de orquestador, y no se sube la versión de pnpm.

## Capabilities

### New Capabilities

- `workspace-task-pipeline`: los scripts de la raíz del monorepo orquestan las tareas de cada paquete
  con la versión del gestor de paquetes que fija el repositorio; el requisito previo para que eso
  ocurra está documentado y se puede diagnosticar con un comando; `dev` arranca las aplicaciones en
  paralelo, y el frontend participa en el grafo de tareas. Ninguna spec vigente cubre hoy este
  comportamiento: [`frontend-typescript-tooling`](../../specs/frontend-typescript-tooling/spec.md) y
  [`frontend-quality-baseline`](../../specs/frontend-quality-baseline/spec.md) describen las tareas
  del paquete del frontend, no su orquestación desde la raíz.

### Modified Capabilities

<!-- Ninguna. Las specs del frontend no cambian de requisitos: sus tareas son las mismas, solo se
     verifica que se pueden lanzar desde la raíz. `local-runtime-operations` (JUP-050) tampoco:
     `local:doctor` y `local:smoke` no pasan por turbo y no se tocan. -->

## Impact

- **Modificado:** `README.md` (requisitos previos, bloque "Con Turborepo" y "Comandos Principales"),
  `openspec/findings/backlog.md` (fila `RF-093-001`) y `docs/spikes/frontend-migration.md` (F4).
- **Nuevo:** `docs/evidence/JUP-103-validation.md` y, al archivar, la spec
  `openspec/specs/workspace-task-pipeline/spec.md`.
- **Solo lectura:** `package.json`, `turbo.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`,
  `.github/workflows/ci.yml`, `tools/ci-workflow.test.mjs` y todo `apps/**`.
- **Fuera del repositorio:** la máquina afectada cambia (`corepack enable` desde una consola con
  permisos de administrador). El resto del equipo solo tiene que hacer algo si el comando de
  diagnóstico falla en su máquina.
- **CI:** sin cambios en los jobs. El criterio "CI sigue en verde" se acredita con los checks del
  pull request.
- **Coordinación con JUP-051 (PR #58, abierto):** modifica `ci.yml` y `tools/ci-workflow.test.mjs`.
  Esta tarjeta no toca ninguno de los dos; si la corrección acabara necesitándolo, se trae `develop`
  antes y se comprueba que no se pisa.
- **Findings:** `RF-093-001` pasa a `Fixed`. Si la batería desde la raíz destapa fallos ajenos al
  gestor de paquetes (por ejemplo, tests de Python que necesitan una base de datos), se registran
  como hallazgos nuevos y no se corrigen aquí.
- **Tarjetas siguientes:** JUP-104 y JUP-105 pueden ejecutar la batería desde la raíz sin sustituto.
- **ADR:** no aplica; no se toma ninguna decisión de arquitectura nueva (ver `design.md`,
  decisión 7).
