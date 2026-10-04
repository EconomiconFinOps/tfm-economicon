# Evidencia JUP-103 — Verificar el pipeline de turbo y el workspace de pnpm

- Fecha: 2026-10-03 (línea base).
- Trello: https://trello.com/c/P33co27E/95-jup-103
- Rama: `chore/JUP-103-verify-turbo-workspace`.
- Base: `develop` en `dad5662`; la rama estaba en `fe087c3` al capturar la línea base.
- OpenSpec: [jup-103-verify-turbo-workspace](../../openspec/changes/jup-103-verify-turbo-workspace/).
- Hallazgo que cierra: `RF-093-001` (`openspec/findings/backlog.md`).
- Pull request: _pendiente de abrir_.
- CI: _pendiente de abrir el pull request_.

> Estado de este documento: **solo la línea base (grupo 1 de `tasks.md`)**. Las secciones marcadas
> _pendiente_ se completan con el resto de las tareas.

## Máquina donde se reproduce

| Dato | Valor |
| --- | --- |
| Sistema operativo | Windows 11, versión `10.0.26200.9550` |
| Procesador y memoria | 8 procesadores lógicos, 15,6 GB |
| Node / corepack / turbo | `v24.15.0` / `0.34.6` / `2.9.18` |
| Python | `3.13.7` |
| `where pnpm` | `C:\Users\victo\AppData\Roaming\npm\pnpm.cmd` (único resultado) |
| `where corepack` | `C:\Program Files\nodejs\corepack.cmd` |
| `npm ls -g --depth=0` | `aws-cdk@2.1141.0` y `pnpm@11.9.0` |
| Lanzadores de pnpm en `C:\Program Files\nodejs` | ninguno (solo `corepack` y `corepack.cmd`): `corepack enable` nunca se ejecutó |
| Orden en el `PATH` | `C:\Program Files\nodejs` va **antes** que `%APPDATA%\npm` (las posiciones concretas cambian según la consola; el orden no) |
| Variable de corepack presente | `COREPACK_ENABLE_AUTO_PIN=0` |

## Línea base: antes de corregir nada

Comandos ejecutados desde la raíz, en este orden. Las salidas completas se guardaron durante la
sesión; aquí figura lo que sostiene cada conclusión.

### Versiones de pnpm que ve cada invocación

| Comando | Resultado |
| --- | --- |
| `pnpm --version` (dentro del repositorio) | `9.0.0` |
| `pnpm --version` (fuera del repositorio) | `11.9.0` |
| `corepack pnpm --version` | `9.0.0` |
| `corepack pnpm exec pnpm --version` | error de versión, código de salida `1` |

El `9.0.0` de `pnpm --version` dentro del repositorio no lo produce corepack: lo produce el pnpm
global `11.9.0`, que cambia de versión por sí mismo al leer `packageManager`. Fuera del repositorio
no hay nada que lo cambie y responde `11.9.0`.

Salida de `corepack pnpm exec pnpm --version`:

```
[ERROR] This project is configured to use 9.0.0 of pnpm. Your current pnpm is v11.9.0
Corepack invoked pnpm with this version, and pnpm does not switch versions when running under corepack.
Align the "packageManager" field in package.json with "devEngines.packageManager", or invoke pnpm directly (without corepack) so it can switch versions automatically.
If you want to bypass this version check, you can set the "pmOnFail" configuration to "warn" or "ignore" (e.g. via --pm-on-fail=ignore). If using "devEngines.packageManager", you can set its "onFail" to "warn" or "ignore"
```

Este comando reproduce el fallo sin turbo de por medio: el pnpm exterior lo lanza corepack y el
interior se resuelve por `PATH` al global.

### Con `corepack pnpm <script>` (invocación documentada)

| Script | Tareas correctas | Código | Qué ocurre |
| --- | --- | --- | --- |
| `lint` (1.ª ejecución) | 0 de 4 | 1 | Error de versión de pnpm en las 4 tareas |
| `build` | 0 de 4 | 1 | Error de versión de pnpm en las 4 tareas |
| `test` | 0 de 4 | 1 | Error de versión de pnpm en las 4 tareas |
| `typecheck` | 0 de 1 | 1 | Error de versión de pnpm (solo el frontend declara el script) |
| `lint` (repetido, sin `--force`) | 4 de 4 | 0 | **Falso positivo, ver abajo** |
| `lint --force` | 0 de 4 | 1 | Error de versión de pnpm en las 4 tareas |

Los errores de las tareas llevan el mismo texto que el bloque anterior y terminan con
`ERROR  @finops/<paquete>#<script>: command (...) C:\Users\victo\AppData\Roaming\npm\pnpm.cmd run <script> exited (1)`:
turbo ejecutó el pnpm global.

**Falso positivo por la caché de turbo.** La repetición de `corepack pnpm lint` pasó 4 de 4 en
129 ms (`cache hit`, `FULL TURBO`) sin lanzar ningún subproceso. Lo había dejado cacheado la
ejecución de `pnpm lint` sin `corepack` hecha antes para comparar: la clave de la caché de turbo no
depende del gestor de paquetes. Consecuencia para esta tarjeta: **una comprobación que pase con
`cache hit` no demuestra nada sobre pnpm**. Las verificaciones de "después" usan `--force` (o, donde
el comando no lo admite, `TURBO_FORCE=true`) y comprueban que cada tarea figura como
`cache bypass, force executing`.

### Sin `corepack` (`pnpm <script> --force`)

| Script | Tareas correctas | Código | Qué ocurre |
| --- | --- | --- | --- |
| `lint` | 4 de 4 | 0 | Sin error de versión |
| `build` | 4 de 4 | 0 | Sin error de versión |
| `typecheck` | 1 de 1 | 0 | Sin error de versión |
| `test` | 1 de 4 | 2 | Sin error de versión; fallan otras cosas (ver siguiente tabla) |

`pnpm test` no admite `--force` (`ERROR  Unknown option: 'force'`, es un comando propio de pnpm): se
ejecutó con `TURBO_FORCE=true pnpm test`. Con ese error, turbo cancela el resto de tareas, así que
para ver cada paquete por separado se repitió con
`pnpm exec turbo run test --continue --force`.

### Fallos de `test` ajenos al gestor de paquetes

Con las tareas ya ejecutándose con la versión correcta de pnpm, `test` falla por motivos propios de
cada paquete. **No se atribuye ninguno a pnpm.**

| Paquete | Resultado | Causa observada |
| --- | --- | --- |
| `@finops/azure-cost-api` | 59 correctos | — |
| `@finops/backend` | 14 errores de recolección, 0 tests ejecutados | Faltan módulos de Python en esta máquina: `structlog`, `pika`, `email_validator` |
| `@finops/processor` | 18 errores de recolección, 0 tests ejecutados | Faltan módulos de Python en esta máquina: `structlog`, `langchain_core`, `pika` |
| `@finops/frontend` | `turbo` en paralelo: 18 fallos de 443 (8 archivos). Aislado (`pnpm --filter @finops/frontend test`): 14 fallos de 443 (8 archivos), 183 s | `Test timed out in 5000ms` / `30000ms` y `Unable to find ...` en `ingestion`, `conversations`, `session-and-dashboard`, `tenant-switching`, `login-session-expired-notice*`, `dashboard-tenant-transition`, `quality-gates` |

- **Python:** no se han instalado los `requirements-dev.txt` de las aplicaciones en esta máquina; el
  `README.md` lo pide en el bloque "Con Turborepo". Es estado de la máquina, no del repositorio.
- **Frontend:** coincide en archivos y en tipo de fallo con `RF-098-004` (timeouts de `findBy*` y
  `waitFor`), pero **no con su descripción**: ese hallazgo afirma que pasan aislados, y aquí fallan
  también aislados (14). No se atribuye a la carga de la máquina ni se da por conocido: la causa no
  está descartada y el número de fallos varía entre ejecuciones (18 en paralelo, 14 aislado).
  Se registra como observación nueva sobre `RF-098-004` (tarea 6.2) y no se corrige en esta tarjeta.

## Causa

Reproducida con las salidas de arriba, sin turbo de por medio (`corepack pnpm exec pnpm --version`) y
con turbo (`corepack pnpm lint --force`):

1. `corepack pnpm <script>` arranca pnpm `9.0.0` y deja `COREPACK_ROOT` en el entorno de sus hijos.
2. turbo lanza `pnpm run <script>` por paquete y el `PATH` lo resuelve a `%APPDATA%\npm\pnpm.cmd`
   (pnpm `11.9.0`), porque no hay lanzador de corepack: nunca se ejecutó `corepack enable`.
3. Ese pnpm `11.9.0` ve que el proyecto pide `9.0.0`. Sin `COREPACK_ROOT` cambiaría de versión por sí
   mismo (es lo que ocurre con `pnpm <script>` a secas, que pasa); con `COREPACK_ROOT` entiende que
   corepack ya eligió y aborta.

Dos afirmaciones del texto original de `RF-093-001` resultan inexactas:

- «`packageManager: pnpm@9.0.0` resuelve correctamente en shell interactiva»: el `9.0.0` que
  devuelve `pnpm --version` lo obtiene el pnpm global cambiando de versión, no corepack.
- «`pnpm lint`/`pnpm build` ya fallaban igual»: sin `corepack`, `pnpm lint`, `build` y `typecheck`
  pasan. Falla la combinación de `corepack pnpm` con un pnpm global en el `PATH`.

## Después de la corrección

_Pendiente: tareas 2.x a 7.x de `tasks.md` (corrección en la máquina, `dev`, grafo, consulta al
equipo, hallazgos, spike y batería final)._

## Trazabilidad con los criterios de la tarjeta

_Pendiente: tarea 7.2._

## No validado

_Pendiente: tarea 7.2._
