# Evidencia JUP-103 — Verificar el pipeline de turbo y el workspace de pnpm

- Fecha: 2026-10-03 (línea base, corrección, grafo y `dev`) y 2026-10-04 (consulta al equipo y
  batería final).
- Trello: https://trello.com/c/P33co27E/95-jup-103
- Rama: `chore/JUP-103-verify-turbo-workspace`.
- Base: `develop` en `dad5662`. La batería final se ejecutó con la rama en `12bc179`. Entretanto
  `origin/develop` avanzó a `c3aa9d6` (JUP-022, #67 y JUP-061, #60), que se fusionó en la rama y se
  reverificó: ver «Reverificación tras fusionar `develop`».
- OpenSpec: [jup-103-verify-turbo-workspace](../../openspec/changes/archive/2026-10-04-jup-103-verify-turbo-workspace/).
- Hallazgo que reformula: `RF-093-001` (`openspec/findings/backlog.md`), que **se mantiene `Open`**
  hasta confirmar la corrección en dos máquinas más (decisión del gate post-review).
- Pull request: [#75](https://github.com/EconomiconFinOps/tfm-economicon/pull/75), contra `develop`.
- CI sobre `f6e01c5`: [7 de 7 jobs correctos](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37249343055)
  (`JUP policy`, `OpenSpec`, `Frontend build`, `Frontend type check` y los tres de Python). El check
  `JUP reviews` ([ejecución](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37249342986))
  figura en rojo hasta que haya reviews, que es lo que la política espera. La CI del commit que añade
  estos enlaces se consulta en la pestaña de checks del propio PR.

> Estado de este documento: completo. Paris y la consola externa de Alejandro figuran como no
> confirmados, y `JUP reviews` queda a la espera de las reviews del PR.

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

## Documentación del requisito previo (grupo 4)

Cambios en `README.md`, el único archivo versionado que modifica este grupo:

- **Sección nueva «Requisito previo: pnpm con corepack»** al inicio de «Como correrlo»: por qué
  turbo necesita los lanzadores de corepack, `corepack enable` una vez por máquina (consola de
  administrador en Windows, verificado solo en Windows), que no hace falta desinstalar un pnpm global
  si el directorio de Node va antes en el `PATH`, el efecto de que `pnpm --version` fuera del
  repositorio pase a mostrar la versión por defecto de corepack, el comando de diagnóstico
  `corepack pnpm exec pnpm --version` (debe imprimir `9.0.0`), la salida de emergencia de `pnpm
  <script>` sin `corepack` (verificada con `11.9.0`, declarada como no documentada) y la advertencia
  sobre la caché de turbo y `--force`.
- **«Con Turborepo»:** `pnpm install` y `pnpm dev` pasan a `corepack pnpm install --frozen-lockfile` y
  `corepack pnpm dev`; se enlaza el requisito previo y se sugiere un entorno virtual de Python. Se
  documenta, tal como se midió en 3.3, que `dev` por sí solo no deja sirviendo a backend ni processor
  y los tres pasos que sí lo consiguen (infraestructura de Compose sin servicios de aplicación,
  archivo de entorno fuera del repositorio con `127.0.0.1` y puertos publicados, y
  `corepack pnpm dev --env-mode=loose` con `ECONOMICON_ENV_FILE`). Se declara como limitación
  conocida del repositorio y se enlaza `RF-103-001`.
- **«Comandos Principales»:** nota de equivalencia entre `pnpm <script>` y `corepack pnpm <script>`,
  descripción de `dev` con su salvedad, `typecheck` (faltaba en la lista) y la nota de `test` con
  `RF-098-004` y `--maxWorkers=1`.

Comprobación de que el cambio no rompe nada (tarea 4.3), con las salidas reales:

| Comando | Resultado |
| --- | --- |
| `corepack pnpm repository:governance:test` | código `0` |
| `corepack pnpm ci:check:test` | código `0` |
| `corepack pnpm pr:check:test` | código `0` |
| `corepack pnpm docker:validate` | código `0` |
| `corepack pnpm jup:cleanup:check` | `[OK] 778 archivos sin agentes personales, binarios ni tareas paralelas.` |
| `corepack pnpm local:test` con la infraestructura de Compose levantada | **código `1`**, 1 fallo: `ports already published by this Compose project are not busy` |
| `corepack pnpm local:test` tras `docker compose stop cockroachdb rabbitmq postgres-pgvector` | código `0`, 74 de 74 |

El fallo de `local:test` no lo causa el `README.md`: el test usa un proyecto de Compose nuevo y
comprueba que los puertos `26257`, `8080`, `5672` y `15672` están libres, y los tenía ocupados la
infraestructura que se levantó para la tarea 3.3. Con los puertos libres pasa. **Consecuencia
práctica: `local:test` no se puede ejecutar con la infraestructura de Compose levantada.**
Se anota para la batería final (7.1). Los volúmenes se conservaron; el primer arranque creó el
volumen `rabbitmq-data`, como describe el propio `README.md` para instalaciones anteriores a JUP-050.

## Consulta al equipo (grupo 5)

Se pidió a Paris, Lucía y Alejandro que ejecutaran, desde `develop` actualizada y con
`corepack pnpm install --frozen-lockfile`, sin cambiar nada en su máquina: sistema operativo y
versión de Node, la ruta de `pnpm` en el `PATH`, `npm ls -g --depth=0`,
`corepack pnpm exec pnpm --version` y `corepack pnpm lint --force`. Resultados recibidos el
2026-10-04, tal como los entregaron:

| Persona | Entorno | `pnpm` que resuelve el `PATH` | `corepack pnpm exec pnpm --version` | `corepack pnpm lint --force` | `corepack enable` |
| --- | --- | --- | --- | --- | --- |
| Victor (referencia) | Windows 11, Node `v24.15.0` | `%APPDATA%\npm\pnpm.cmd` (pnpm global `11.9.0` con `npm -g`) | error de versión (`v11.9.0`), código `1` | 0 de 4 | ejecutado: pasa a `9.0.0` y 4 de 4 (grupo 2) |
| Lucía | Windows 10 Home `10.0.19045`, Node `v24.15.0`, `develop` en `dad5662` | `%APPDATA%\npm\pnpm.cmd` (pnpm global `11.1.3` con `npm -g`) | error de versión (`v11.1.3`) | 0 de 4; la línea `Failed:` nombra solo `azure-cost-api#lint` y `backend#lint` | **ejecutado** (y desinstalado además el pnpm global): ver «Segunda respuesta de Lucía» |
| Alejandro | Windows 11 Pro, Node `v24.14.1`, worktree aislado de `develop` en `dad5662`, **entorno de ejecución de Codex, no una consola externa** | `...\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd`; sin pnpm global de npm (solo `@openai/codex@0.129.0` y `agent-slack@0.7.1`) | **`11.19.0`, sin error** (`corepack pnpm --version` da `9.0.0`) | 0 de 4; `@finops/backend#lint` falla con `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY` | no ejecutado (no cambió configuración) |
| Paris | — | — | — | — | **no confirmado** (consulta cerrada sin respuesta el 2026-10-04) |

Lectura, separando lo medido de lo inferido:

- **Se reproduce en las tres máquinas que han contestado** (Windows 11 dos veces y Windows 10 una), con
  Node `24.14.1` y `24.15.0`. En las tres, el `pnpm` que resuelve el `PATH` dentro de
  `corepack pnpm exec` **no es el de corepack y es una `11.x`**: `11.9.0`, `11.1.3` y `11.19.0`. Con
  una `9.0.0` no se ha probado ninguna.
- **El síntoma no es el mismo en todas.** Con `11.9.0` y `11.1.3` aparece el error de versión que
  describe `RF-093-001`. Con `11.19.0` (Alejandro) el diagnóstico no imprime error sino la versión
  equivocada, y las tareas de turbo abortan por otro motivo: el pnpm `11.19.0` intenta una
  instalación desde el subproceso y se detiene por falta de terminal. Es **consistente con** el
  mismo mecanismo (un pnpm que no es el de corepack por delante en el `PATH`), pero el mensaje depende
  de la versión de ese pnpm. Se infiere, no se ha comprobado con una `11.19.0` propia.
- **Alejandro no tiene un pnpm global de npm**: el que se cuela lo aporta el entorno de ejecución de su
  asistente (carpeta `fallback` de `codex-runtimes`). Esto amplía la causa: no es solo un `npm -g
  pnpm`; vale cualquier `pnpm` anterior a corepack en el `PATH`. Su propia lectura es separar este
  caso del de una consola habitual, y se acepta: **no se ha probado el diagnóstico en su consola
  externa**, que es la pregunta pendiente.
- **La corrección está comprobada en dos máquinas** (Victor y Lucía, ver la sección siguiente). En el
  caso de Alejandro no se sabe si bastaría: depende de si el directorio de Node va antes que la
  carpeta `fallback` en el `PATH` del entorno de Codex, que no se ha mirado.
- La línea `Failed:` de turbo no lista todas las tareas que fallan (Lucía: 0 de 4 con dos nombradas),
  por eso se mira `Tasks:` y no `Failed:`.

Consecuencia para el `README.md` (ya aplicada): el diagnóstico debe leerse como «imprime exactamente
`9.0.0`»; cualquier otra salida, sea el error o una versión distinta, indica que hay otro `pnpm` por
delante en el `PATH`. Antes solo mencionaba el error.

### Segunda respuesta de Lucía

Lucía ejecutó `corepack enable` **y además desinstaló el pnpm global**. Resumió el resultado en un
mensaje, sin pegar las salidas, y no con los comandos exactos que se le pidieron (usó `pnpm` y no
`corepack pnpm`, equivalentes una vez activado corepack y sin otro pnpm por delante):

- `pnpm` resuelve a `9.0.0`.
- `pnpm lint --force` y `pnpm build --force` ejecutan las 4 tareas.
- Los tests pasan en los 4 servicios con **Python 3.12** (el de CI y las imágenes). Con el Python
  **3.14** de su sistema falla un test del processor; ella lo atribuye al intérprete. **No se ha
  reproducido ni examinado aquí** (en esta máquina todo se ejecutó con 3.13.7), así que se registra
  como observación suya, sin causa confirmada y sin hallazgo propio.

Dos límites de esta confirmación: **no se sabe cuál de las dos acciones fue la que importó**, porque
hizo las dos a la vez (en la máquina de Victor basta `corepack enable` con el global instalado), y
no se tiene la salida literal del diagnóstico `corepack pnpm exec pnpm --version`.

### Cierre de la consulta (tareas 5.2 y 5.3, 2026-10-04)

Por decisión de Victor, la consulta se **cierra con dos puntos como «no confirmado»**, sin darlos por
validados, y puede reabrirse:

- **Paris**: no respondió. No se sabe si reproduce el fallo ni si la corrección le funciona.
- **Alejandro en una consola externa**: solo se tiene su resultado desde el entorno de ejecución de
  Codex. No se sabe si le ocurre en su consola habitual ni si `corepack enable` bastaría allí.

Respuesta a «¿tiene el equipo que hacer algo en sus máquinas?» (criterio 5): **sí**, ejecutar una vez
`corepack enable` si `corepack pnpm exec pnpm --version` no imprime exactamente `9.0.0`. Comprobado
que funciona en dos máquinas (Victor y Lucía); en las otras dos, no confirmado.

## Hallazgos y spike (grupo 6)

- **`RF-093-001` se reformula y se mantiene `Open`** en `openspec/findings/backlog.md`, con la causa, la
  corrección, las dos afirmaciones corregidas, las 3 máquinas donde se reprodujo y las 2 donde se
  confirmó la corrección. Se redactó primero como `Fixed` con lo pendiente escrito dentro; en el gate
  post-review se decidió dejarlo `Open` hasta tener la respuesta de Paris y la de Alejandro en consola
  externa. Pasa a `Fixed` cuando ambos confirmen sin contradecirla; si alguno la contradice, se revisa
  la causa.
- **Hallazgos nuevos**, todos `Open`, sin corregir aquí: `RF-103-001` (`pnpm dev` no puede arrancar
  backend ni processor), `RF-103-002` (`--parallel` obsoleto en turbo `2.9.18`), `RF-103-003`
  (`localhost` bloquea el arranque del backend; causa sin verificar) y `RF-103-004` (`local:test`
  falla con la infraestructura de Compose levantada).
- **`RF-098-004`**: añadida la observación de esta tarjeta (14 a 21 fallos con los workers por
  defecto, también ejecutando solo el frontend; 443 de 443 con `--maxWorkers=1`), que corrige lo que
  decía de que «pasan aislados».
- **Spike, F4**: la tarjeta de Docker marcada como resuelta por JUP-049 y JUP-050 sin tarjeta propia,
  con cada punto **verificado contra el código** (`apps/frontend/Dockerfile` líneas 7 y 9,
  `docker-compose.yml`, `README.md`, `RF-090-001` y `RF-090-002` en `Fixed`,
  `tools/docker-topology.test.mjs`, `docs/evidence/JUP-050-validation.md`); la de turbo con su slug
  real y sus casillas, con la salvedad de `dev`; F4 declarada completa y una entrada nueva en
  «Próximos pasos».

## Batería final desde la raíz (tarea 7.1)

Entorno: Windows 11, `C:\Program Files\nodejs\pnpm` el primero del `PATH` (corepack),
`corepack pnpm exec pnpm --version` = `9.0.0`, entorno virtual de Python `3.13.7` activo,
infraestructura de Compose **parada** y los puertos 5173, 8000, 8001, 8002, 5672, 15672, 26257, 8080
y 5433 libres. Sin sustitutos `--filter @finops/frontend` como atajo para esquivar turbo: los
filtros de `test` que figuran abajo van igualmente a través de turbo y de los scripts de la raíz.

| Comando | Código | Resultado |
| --- | --- | --- |
| `corepack pnpm install --frozen-lockfile` | `0` | `git status` limpio |
| `corepack pnpm lint --force` | `0` | 4 de 4 |
| `corepack pnpm build --force` | `0` | 4 de 4 |
| `corepack pnpm typecheck --force` | `0` | 1 de 1 |
| `TURBO_FORCE=true corepack pnpm run test "--filter=!@finops/frontend"` | `0` | 3 de 3, 1 min 34 s: `azure-cost-api` 59; `processor` 448 y 57 omitidos; `backend` 329 y 17 omitidos |
| `TURBO_FORCE=true corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1` | `0` | 1 de 1, 3 min 9 s: 48 archivos, 443 tests |
| `corepack pnpm openspec:validate` | `0` | 42 de 42 |
| `corepack pnpm jup:check -- --change jup-103-verify-turbo-workspace` | `0` | enlazado con Trello y completo |
| `corepack pnpm jup:check:all` | `0` | todos los changes enlazados |
| `corepack pnpm jup:check:test` | `0` | 7 de 7 |
| `corepack pnpm jup:cleanup:check` | `0` | 778 archivos sin agentes personales, binarios ni tareas paralelas |
| `corepack pnpm jup:cleanup:test` | `0` | 6 de 6 |
| `corepack pnpm pr:check:test` | `0` | 57 de 57 |
| `corepack pnpm ci:check:test` | `0` | 10 de 10 |
| `corepack pnpm repository:governance:test` | `0` | 13 de 13 |
| `corepack pnpm roadmap:test` | `0` | 5 de 5 |
| `corepack pnpm docker:validate` | `0` | 31 de 31 |
| `corepack pnpm local:test` | `0` | 74 de 74 (con la infraestructura parada) |
| `corepack pnpm assistant-corpus:test` | `0` | 8 de 8 |
| `corepack pnpm llm-gateway:test` | `0` | 7 de 7 |
| `corepack pnpm validation-questions:test` | `0` | 8 de 8 |

En las 5 ejecuciones de turbo (`lint`, `build`, `typecheck` y las dos mitades de `test`) **todas las
tareas figuran como `cache bypass, force executing`, ninguna como `cache hit`, y el error de versión
de pnpm aparece 0 veces.**

### `test` con los cuatro paquetes a la vez: falla, y no por pnpm

El comando literal de la tarjeta, sin dividir, **no es fiable en esta máquina**:

| Ejecución | Código | Qué falla |
| --- | --- | --- |
| `TURBO_FORCE=true corepack pnpm test` | `1` | `processor`: 1 fallo, `test_jup023_attempt_deadline_accepts_complete_response` (`assert 0.358 < 0.2`, umbral de reloj de pared contra un gateway simulado). Turbo cancela el resto (`Tasks: 1 successful, 4 total`) |
| `TURBO_FORCE=true corepack pnpm run test --continue` | `1` | `backend`: 2 fallos en `test_managed_resolver.py` (`...cancel_wins_before_delivery...[result-ready]` y `...real_blocked_child_has_expected_os_pid...`), ambos `Bounded observation deadline expired`. `azure-cost-api` 59, `processor` 448 y 57 omitidos, **`frontend` 443 de 443** con los workers por defecto |
| Medición del grupo 1 (`pnpm exec turbo run test --continue`, y la del `venv`) | `2` | `frontend`: 14 a 21 fallos por timeout (`RF-098-004`) |

Cada ejecución falla en un sitio distinto, y los tests que fallan **pasan aislados**: el de
`processor` 10 de 10 (y su módulo 3 de 3), el módulo de `backend` 3 de 3 (14 correctos cada vez). En
las 3 mediciones con todos los paquetes a la vez no hay dos fallos iguales. Es consistente con
contención de CPU al competir las cuatro suites (8 procesadores lógicos), pero **no se midió la
carga y no se descartó una carrera**, así que no se afirma causa. Procede de tests con plazos de
tiempo de otras tarjetas (JUP-023 y JUP-086) y se registra como `RF-103-005`.

En ninguna de estas ejecuciones aparece el error de versión de pnpm.

### Qué no se ejecutó en la batería

- `corepack pnpm pr:check` (necesita un pull request abierto): tarea 7.6.
- `docker compose up --build` y `corepack pnpm local:smoke`: requieren el stack completo y no
  guardan relación con el cambio (solo documentación).
- `corepack pnpm docker:build`: construye imágenes y no pasa por la corrección de esta tarjeta.

## Reverificación tras fusionar `develop` (tarea 7.6, 2026-10-04)

`origin/develop` avanzó de `dad5662` a `c3aa9d6` con dos pull requests de otras tarjetas: JUP-061 (#60,
registro de decisiones técnicas) y JUP-022 (#67, recuperación semántica, con 70 archivos y +7 908
líneas). Se comprobó antes de fusionar con `git merge-tree` (sin tocar el árbol) y se fusionó con
`git merge --no-commit --no-ff origin/develop`.

- **Conflictos:** uno, mecánico, en `openspec/findings/backlog.md`: las dos ramas añadieron filas al
  principio de la tabla. Se conservaron las dos series (`RF-103-001` a `005` y `RF-022-001` a `006`) y
  se comprobó que ninguna fila nueva rompe la estructura de la tabla (las únicas con otro número de
  celdas siguen siendo `RF-044-001` y `RF-045-001`, anteriores a esta tarjeta). `README.md` se
  fusionó sin conflicto: conserva mis tres secciones y las variables que añade JUP-022.
- **Lo que `develop` cambia y podía afectar a esta tarjeta**, revisado: `package.json` solo añade tres
  scripts (`retrieval-labels:validate`, `retrieval-labels:test`, `retrieval-calibration:test`) y
  `ci.yml` solo los invoca; **los tres jobs que usan pnpm siguen ejecutando `corepack enable`**.
  Ningún `requirements*`, `package.json` de aplicación ni lockfile cambia, de modo que el entorno
  virtual de Python sirve tal cual. En el frontend solo cambia un test, sin colores literales nuevos.
  El último ADR de `develop` es `ADR-0017`; esta tarjeta no añade ninguno.
- **Verificación del árbol fusionado**, desde la raíz y con `--force`:

| Comando | Código | Resultado |
| --- | --- | --- |
| `corepack pnpm install --frozen-lockfile` | `0` | sin cambios |
| `corepack pnpm lint --force` / `build --force` / `typecheck --force` | `0` | 4 de 4 / 4 de 4 / 1 de 1; todas `cache bypass`; 0 errores de versión |
| `TURBO_FORCE=true corepack pnpm run test "--filter=!@finops/frontend"` | `0` | 3 de 3: `azure-cost-api` 59; `processor` 448 y 57 omitidos; `backend` **578** y 28 omitidos (JUP-022 añade tests) |
| `TURBO_FORCE=true corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1` | `0` | 48 archivos, 443 tests |
| `corepack pnpm openspec:validate` | `0` | 45 de 45 (42 más los de `develop`) |
| `corepack pnpm jup:check -- --change jup-103-verify-turbo-workspace` y `jup:check:all` | `0` | enlazados |
| `corepack pnpm jup:cleanup:check` | `0` | 817 archivos sin agentes personales, binarios ni tareas paralelas |
| `corepack pnpm repository:governance:test`, `ci:check:test`, `pr:check:test` | `0` | 13, 10 y 57 de 57 |
| `corepack pnpm retrieval-labels:validate` y `retrieval-labels:test` | `0` | 28 etiquetas coherentes; 17 de 17 |

No se repitió la batería completa de herramientas ni `test` con los cuatro paquetes a la vez: lo
primero no depende de `develop` y lo segundo ya se sabe no fiable en esta máquina (`RF-103-005`).

## Trazabilidad con los criterios de la tarjeta

| # | Criterio | Estado | Evidencia y salvedades |
| --- | --- | --- | --- |
| 1 | `lint`, `build`, `test` y `typecheck` se ejecutan desde la raíz vía turbo sin el error de versión de pnpm, en la máquina donde se reproducía | **Cumplido en lo que pide el criterio; con una salvedad sobre `test`** | `lint` 4/4, `build` 4/4 y `typecheck` 1/1 con código `0` y `--force`, y 0 apariciones del error de versión en todas las ejecuciones. `test` tampoco muestra el error y pasa en dos mitades, pero **el comando literal `corepack pnpm test` termina con código `1` en esta máquina** por tests con plazos de tiempo (`RF-103-005`, `RF-098-004`), no por pnpm |
| 2 | `pnpm dev` levanta frontend, backend y processor en paralelo | **Cumplido con salvedades** | Turbo lanza las cuatro tareas en paralelo con el pnpm correcto. Tal como está documentado, `dev` no deja sirviendo a backend ni a processor y turbo termina todo cuando falla uno; con `--env-mode=loose` y un archivo de entorno con `127.0.0.1` las cuatro responden `200` (grupo 3, `RF-103-001` a `RF-103-003`). Documentado en el `README.md` |
| 3 | CI sigue en verde | **Cumplido sobre `f6e01c5`** (PR #75): el workflow `CI` pasa sus 7 jobs. `JUP reviews` es otro workflow y espera las reviews | Esta rama solo cambia `README.md`, `docs/` y `openspec/` (verificado con `git diff --name-only origin/develop...HEAD`): ni `package.json`, `turbo.json`, lockfile, `pnpm-workspace.yaml`, `.github/`, `apps/`, `tools/` ni `packages/`. Los jobs de CI ya ejecutan `corepack enable` antes de pnpm. Acreditado con los checks del pull request (ver la cabecera) |
| 4 | `RF-093-001` cerrado con la causa documentada, o reformulado si es de entorno | **Cumplido por la vía de la reformulación; el hallazgo no se cierra** | Se mantiene `Open` con la causa (de entorno) documentada con precisión, la corrección, las dos afirmaciones del texto original que eran inexactas, 3 reproducciones y 2 máquinas corregidas. Pasa a `Fixed` cuando confirmen el entorno de Codex de Alejandro (en consola externa) y la máquina de Paris |
| 5 | Queda escrito si el equipo debe hacer algo en sus máquinas, y qué | **Cumplido de forma provisional** | `README.md`, «Requisito previo: pnpm con corepack»: `corepack enable` una vez si `corepack pnpm exec pnpm --version` no imprime `9.0.0`. Comprobado en 2 de 4 máquinas; el caso de un `pnpm` aportado por el entorno de un asistente queda sin resolver |
| 6 | Las tarjetas futuras de frontend pueden usar los scripts de la raíz sin sustituto, o queda documentado por qué no | **Parcial, y documentado** | `lint`, `build` y `typecheck` sí, con `corepack enable` hecho y `--force` para comprobar. `test` con los cuatro paquetes a la vez no es fiable en todas las máquinas: se documenta ejecutarlo por mitades. `dev` necesita los pasos del `README.md`. `RF-098-004` y `RF-103-005` |
| 7 | El spike refleja F4 completa, con la tarjeta de Docker marcada como resuelta por JUP-049 y JUP-050 | **Cumplido** | `docs/spikes/frontend-migration.md`, F4 y entrada 11 de «Próximos pasos». Los puntos de Docker se verificaron contra `apps/frontend/Dockerfile`, `docker-compose.yml`, `README.md`, `RF-090-001`/`RF-090-002` y `tools/docker-topology.test.mjs` |

## No validado

- **La CI del commit que añade los enlaces del PR y de la CI a esta evidencia**: solo cambia
  documentación, pero no se ha consultado al escribir esto.
- **La corrección en la máquina de Paris** (sin respuesta) y **el diagnóstico en la consola externa de
  Alejandro**; si `corepack enable` bastaría en el entorno de Codex.
- **La salida literal** de Lucía: confirmó con un resumen, sin pegar los comandos exactos, y hizo a
  la vez `corepack enable` y la desinstalación del pnpm global, de modo que no se sabe cuál de las dos
  fue la determinante en su máquina.
- **macOS y Linux**: todo se verificó en Windows (10 y 11); `sudo` para `corepack enable` es una
  suposición.
- **La causa del bloqueo con `localhost`** (`RF-103-003`): la resolución a IPv6 es solo una hipótesis.
- **La causa de los fallos intermitentes de `test`** (`RF-103-005`, `RF-098-004`): se observó que
  cambian de una ejecución a otra y que aislados pasan; no se midió la carga ni se descartó una carrera.
- **El orden de `build` entre paquetes con dependencias internas**: ningún paquete depende de otro,
  así que la regla `^build` de `turbo.json` no se ha ejercitado.
- **Python `3.12`** (el de CI y las imágenes) en la máquina de verificación: se usó `3.13.7`. Lucía
  informa de que con `3.12` pasa y con `3.14` falla un test del processor; no se reprodujo aquí.
- **Los 57 tests omitidos de `processor` y los 17 de `backend`**: no se examinaron; se sospecha que
  son los que necesitan base de datos real (`RF-096-004`).
- **El resto de la batería de CONTRIBUTING con un PR**: `corepack pnpm pr:check`.
- **La rama integrada con `develop` actual** (`c3aa9d6`): resuelto, ver «Reverificación tras fusionar
  `develop`».

_Pendiente: las reviews del PR (`Revision JUP-103` y `Validacion JUP-103`). Paris y la consola externa
de Alejandro quedan como no confirmados._
