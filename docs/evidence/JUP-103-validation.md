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

- **Python:** no se habían instalado los `requirements-dev.txt` de las aplicaciones en esta máquina;
  el `README.md` lo pide en el bloque "Con Turborepo". Es estado de la máquina, no del repositorio.
  Se corrige en la sección siguiente.
- **Frontend:** coincide en archivos y en tipo de fallo con `RF-098-004` (timeouts de `findBy*` y
  `waitFor`). El número de fallos varía entre ejecuciones: 18 y 21 con `turbo` en paralelo con los
  demás paquetes, 14 con `pnpm --filter @finops/frontend test` (Vitest con sus workers por defecto,
  que también es paralelo entre archivos). Ver la sección siguiente para la ejecución con un solo
  worker. Se registra como observación sobre `RF-098-004` (tarea 6.2) y no se corrige en esta
  tarjeta.

### Preparación de Python y el frontend con un solo worker (aún sin corregir pnpm)

Para poder distinguir los fallos de entorno de los de pnpm, se preparó Python **sin tocar el
repositorio** (`git status` limpio) y se repitió `test`. La máquina de pnpm sigue como en la línea
base: pnpm global `11.9.0`, sin `corepack enable`.

- Entorno virtual en `C:\Users\victo\Pontia\.venv-tfm`, **fuera del repositorio**, con Python
  `3.13.7`. Difiere de CI y de los Dockerfiles, que usan `3.12`; no hay un `3.12` instalado en la
  máquina. Instalado con `python -m pip install -r apps/<app>/requirements-dev.txt` para
  `backend`, `processor` y `azure-cost-api`, sin errores.
- `turbo` usa el `python` que encuentra en el `PATH`, así que el entorno hay que activarlo en la
  consola que lanza `pnpm`. En Git Bash: `export PATH="/c/Users/victo/Pontia/.venv-tfm/Scripts:$PATH"`
  (una ruta con unidades `C:/...` no funciona ahí y deja el Python global; ocurrió en el primer
  intento). En PowerShell: `$env:Path = "C:\Users\victo\Pontia\.venv-tfm\Scripts;$env:Path"`.

Resultado de `pnpm exec turbo run test --continue --force` con ese entorno, para los tres paquetes de
Python (3 de 3 tareas, código `0`, 1 min 54 s):

| Paquete | Resultado |
| --- | --- |
| `@finops/azure-cost-api` | 59 correctos |
| `@finops/processor` | 448 correctos, 57 omitidos |
| `@finops/backend` | 329 correctos, 17 omitidos |

Los omitidos no se han examinado; se sospecha que son tests que necesitan base de datos real
(`RF-096-004`), pero no está comprobado.

Frontend: `pnpm --filter @finops/frontend exec vitest run --maxWorkers=1` pasa **48 de 48 archivos y
443 de 443 tests** (144 s, código `0`). Con los workers por defecto fallan entre 14 y 21 con
timeouts. Esto concuerda con lo que dejó escrito `RF-098-004` (pasan limitando el paralelismo), pero
**no distingue entre contención de CPU y estado compartido entre archivos**: pasar en serie no
descarta una carrera. No se afirma una causa.

Consecuencia para esta tarjeta: `corepack pnpm test` desde la raíz, con todos los paquetes a la vez,
termina con código distinto de cero **en esta máquina** por los timeouts del frontend, aunque pnpm
funcione. No se puede pasar `--maxWorkers=1` a todos los paquetes (`pytest` no lo entiende) ni
declarar variables de entorno para Vitest sin tocar `turbo.json`, que esta tarjeta no modifica.
Para la batería final se ejecutan por separado, siempre desde la raíz y a través de turbo:
`corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1` y
`corepack pnpm run test "--filter=!@finops/frontend"`. Se usa `pnpm run test` y no `pnpm test`
porque este último es un comando propio de pnpm que rechaza opciones desconocidas (`Unknown option:
'dry'`, `'force'`); `pnpm run` las reenvía a turbo. Comprobado con `--dry=json`: el primero deja
`cliArguments: ["--maxWorkers=1"]` solo en `@finops/frontend#test`, y el segundo planifica
`azure-cost-api`, `backend`, `processor` y `shared-config`, sin el frontend.

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

### Corrección aplicada (tarea 2.1)

Victor ejecutó `corepack enable` en una consola de PowerShell **como administrador**, sin
desinstalar el pnpm global `11.9.0` (que sigue instalado). No imprimió nada y devolvió el control.
Es la única acción sobre la máquina; no se cambió ningún archivo del repositorio.

### Comprobación del entorno (tarea 2.2)

| Comprobación | Antes | Después |
| --- | --- | --- |
| Lanzadores de pnpm en `C:\Program Files\nodejs` | ninguno | `pnpm`, `pnpm.CMD`, `pnpm.ps1` |
| `where.exe pnpm` | solo `%APPDATA%\npm\pnpm.cmd` | `C:\Program Files\nodejs\pnpm.CMD` primero y después el de `%APPDATA%\npm` |
| `pnpm --version` (dentro del repositorio) | `9.0.0` (lo daba el pnpm global al cambiar de versión) | `9.0.0` (lo da corepack) |
| `pnpm --version` (fuera del repositorio) | `11.9.0` | `12.4.1` |
| `corepack pnpm --version` | `9.0.0` | `9.0.0` |
| `corepack pnpm exec pnpm --version` | error de versión, código `1` | `9.0.0`, código `0` |

Fuera del repositorio, `pnpm --version` pasa de `11.9.0` a `12.4.1`: ahora lo resuelve corepack, y sin
un `packageManager` que mande usa su versión por defecto, no el pnpm global. No afecta a este
repositorio y es la consecuencia esperada de activar corepack; se menciona en la documentación.
`npm ls -g --depth=0` sigue mostrando `pnpm@11.9.0`: el global no se tocó.

### Batería desde la raíz con `corepack pnpm` (tarea 2.3)

Con el entorno virtual de Python activo y `--force` (o `TURBO_FORCE=true` en `test`). En cada
ejecución, **todas las tareas figuran como `cache bypass, force executing`, ninguna como
`cache hit`, y hay 0 apariciones del error de versión de pnpm**.

| Comando | Tareas | Código | Tiempo |
| --- | --- | --- | --- |
| `corepack pnpm lint --force` | 4 de 4 | `0` | 4,5 s |
| `corepack pnpm build --force` | 4 de 4 | `0` | 7,0 s |
| `corepack pnpm typecheck --force` | 1 de 1 | `0` | 8,0 s |
| `corepack pnpm run test "--filter=!@finops/frontend"` | 3 de 3 | `0` | 1 min 24 s |
| `corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1` | 1 de 1 | `0` | 2 min 20 s |

Detalle de `test`: `azure-cost-api` 59 correctos; `processor` 448 correctos y 57 omitidos;
`backend` 329 correctos y 17 omitidos; `frontend` 48 archivos y 443 tests correctos.
`@finops/shared-config` no declara `test`, por eso la mitad de Python cuenta 3 tareas.

Con esto, el fallo de la línea base (0 de 4 en `lint`, `build` y `test`, 0 de 1 en `typecheck`)
desaparece **en la misma máquina, con la misma invocación documentada y sin cambiar el
repositorio**. Se mantienen los dos puntos de la línea base que no son de pnpm: el entorno de Python
y el paralelismo del frontend (`RF-098-004`).

### Instalación reproducible (tarea 2.4)

`corepack pnpm install --frozen-lockfile` termina con código `0` en 1,3 s y `git status` queda
limpio: no modifica `pnpm-lock.yaml` ni ningún otro archivo versionado.

## Grafo de turbo y `pnpm dev` (grupo 3)

### Grafo (tareas 3.1 y 3.2)

`corepack pnpm exec turbo run build lint test typecheck dev --dry=json`: modo de entorno `strict`,
25 tareas (5 paquetes × 5 scripts), **todas con `dependencies: []`**.

| Paquete | `build` | `lint` | `test` | `typecheck` | `dev` |
| --- | --- | --- | --- | --- | --- |
| `@finops/frontend` | `vite build` | `eslint src tests` | `vitest run` | `tsc` (3 proyectos) | `vite --host 0.0.0.0 --port 5173` |
| `@finops/backend` | `python -m compileall app` | ídem | `python -m pytest tests` | no declarado | `python -m app.run --reload` |
| `@finops/processor` | `python -m compileall app` | ídem | `python -m pytest tests` | no declarado | `python -m app.run_all` |
| `@finops/azure-cost-api` | `python -m compileall app` | ídem | `python -m pytest tests` | no declarado | `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8002` |
| `@finops/shared-config` | no declarado | no declarado | no declarado | no declarado | no declarado |

- El frontend tiene las cinco tareas.
- `turbo.json` declara `build` con `dependsOn: ["^build"]` y `outputs: ["dist/**", "build/**"]`.
  Ninguna tarea tiene dependencias porque ningún paquete del workspace declara a otro como
  dependencia (comprobado en los cinco `package.json`). La regla `^build` es la que ordenaría el
  `build` cuando eso cambie; no se ha creado una dependencia artificial para demostrarlo, así que
  **el orden de `build` entre paquetes con dependencias internas no se ha ejercitado**.
- `typecheck` solo existe en el frontend; el resto de paquetes no lo declara (los tres de Python
  usan `compileall` como `lint` y `build`).

### `pnpm dev` (tarea 3.3)

Preparación: Docker Desktop arrancado (daemon `29.8.1`), `corepack pnpm local:doctor` en verde
(instalación existente con 4 volúmenes) y **solo la infraestructura** levantada con
`docker compose up -d --wait cockroachdb rabbitmq postgres-pgvector` (las tres `healthy`); los
servicios de aplicación de Compose, parados. Puertos 5173, 8000, 8001 y 8002 libres antes de cada
ejecución. Entorno virtual de Python activo.

**Lo que hace turbo** (idéntico en las cuatro ejecuciones): `Running dev in 5 packages`, lanza en
paralelo `vite`, `python -m app.run --reload`, `python -m app.run_all` y `uvicorn` (azure-cost-api),
con `C:\Program Files\nodejs\pnpm.CMD` (el lanzador de corepack) y sin error de versión de pnpm.
Aviso nuevo de turbo `2.9.18`: `--parallel is deprecated and will be removed in a future major
version`; el script `dev` de `package.json` lo usa.

**Lo que queda sirviendo depende de la configuración, no de pnpm:**

| # | Ejecución | Resultado |
| --- | --- | --- |
| 1 | `corepack pnpm dev`, tal como lo documenta el `README.md` | El backend muere al arrancar con `StartupError: Invalid runtime configuration`; turbo aborta (`run failed`) y **termina el resto**: nada escucha en 5173, 8000, 8001 ni 8002 |
| 2 | Igual, con `ECONOMICON_ENV_FILE` apuntando a un archivo de entorno válido | El mismo fallo |
| 3 | `corepack pnpm dev --env-mode=loose`, archivo con `localhost` | Frontend (5173) y azure-cost-api (8002) responden `200`; el backend se queda **más de dos minutos** en "Waiting for application startup" y el processor no escribe nada; 8000 y 8001 no responden |
| 4 | `corepack pnpm dev --env-mode=loose`, archivo con `127.0.0.1` | Las cuatro responden `200` y se mantienen (sondeadas a 20, 50, 80 y 110 s, sin errores en el log) |

Respuestas de la ejecución 4, con la salida real:

```
5173 -> <!doctype html> ... (Vite)
8000 -> {"status":"ok","services":{"database":"ok","rabbitmq":"ok","vector_store":"ok"},...}
8001 -> {"status":"ok","services":{"database":"ok","rabbitmq":"ok","vector_store":"ok"}}
8002 -> {"status":"ok","dataset":"EA-Cost-Actual.sample.csv","rows":50,"subscriptions":4}
```

Qué distingue cada caso, con lo que se comprobó:

- **Ejecuciones 1 y 2:** `Settings` del backend y del processor se leen solo del entorno del proceso
  (`env_file=None`; el archivo solo entra por `ECONOMICON_ENV_FILE`). `turbo` está en modo `strict`
  y para `@finops/backend#dev` declara `env: []` y `passThroughEnv: null`, de modo que **ninguna
  variable del shell llega a la tarea**. Prueba directa de que no es la configuración: el mismo
  archivo con `ECONOMICON_ENV_FILE=... python -c "from app.core.config import get_settings; ..."`
  desde `apps/backend` da `configuracion valida`, y la ejecución 3 (`--env-mode=loose`) deja pasar
  la variable y el backend arranca.
- **El `.env` de Compose usa los nombres internos de Compose** (`cockroachdb:26257`, `rabbitmq:5672`,
  `postgres-pgvector:5432`), que un proceso del host no resuelve; con el host publicado hay que usar
  `26257`, `5672` y `5433`. El archivo de las ejecuciones 3 y 4 es una copia del `.env` con solo esas
  tres URLs cambiadas, **fuera del repositorio**.
- **`localhost` frente a `127.0.0.1`** (ejecuciones 3 y 4, y backend en solitario sin turbo): con
  `localhost` el backend no completa el arranque en más de dos minutos; con `127.0.0.1` arranca
  en 1,2 s y `/health` responde `200` mientras está vivo. Los puertos de Compose se publican solo en
  `127.0.0.1`. **La causa no está verificada**; la hipótesis es la resolución de `localhost` a IPv6
  en esta máquina Windows.

Conclusión sobre el criterio 2 de la tarjeta (`pnpm dev` levanta frontend, backend y processor en
paralelo): **se cumple en lo que corresponde a pnpm y turbo** (arranca las cuatro tareas en paralelo
con el pnpm correcto) y **se cumple de extremo a extremo solo con dos requisitos que el repositorio
no documenta**: pasar `--env-mode=loose` y un archivo de entorno con hosts alcanzables desde el host
(`127.0.0.1` con los puertos publicados). Tal como está documentado, `pnpm dev` deja solo el frontend
y azure-cost-api como mucho y termina todo en cuanto falla el backend.

Hallazgos candidatos del repositorio (tarea 6.2), sin corregir aquí:

1. `pnpm dev` desde la raíz no puede arrancar backend ni processor: modo `strict` sin variables
   declaradas y aplicaciones que no leen `.env`. Corregirlo exige tocar `turbo.json` (`passThroughEnv`)
   o las aplicaciones.
2. El bloque "Con Turborepo" del `README.md` no menciona ninguno de los dos requisitos.
3. El script `dev` usa `--parallel`, obsoleto en turbo `2.9.18`.
4. `localhost` en las URLs bloquea el arranque del backend en esta máquina (causa sin verificar).

Estado al terminar: procesos de `dev` parados y puertos libres; la infraestructura de Compose
**sigue levantada** (`docker compose ps`: las tres `healthy`).

_Pendiente: tareas 4.x a 7.x de `tasks.md` (documentación, consulta al equipo, hallazgos, spike y
batería final)._

## Trazabilidad con los criterios de la tarjeta

_Pendiente: tarea 7.2._

## No validado

_Pendiente: tarea 7.2._
