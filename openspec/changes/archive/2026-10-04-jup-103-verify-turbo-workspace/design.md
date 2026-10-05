JUP-103 — Verificar el pipeline de turbo y el workspace de pnpm. Carril `light`.

## Context

Motivación y alcance en [`proposal.md`](proposal.md). Aquí solo el estado que condiciona el enfoque,
medido el 2026-10-03 sobre `develop` en `dad5662`, en la máquina donde se reproduce `RF-093-001`
(Windows 11, Node `v24.15.0`, corepack `0.34.6`, turbo `2.9.18`).

**Configuración del repositorio.** `package.json` declara `packageManager: pnpm@9.0.0` y
`turbo ^2.0.0`. Los scripts `dev`, `build`, `lint`, `test`, `typecheck` y `docker:build` son
`turbo run <tarea>`; el resto de scripts de la raíz son `node ...` y no pasan por turbo. `turbo.json`
solo ordena `build` (`dependsOn: ["^build"]`).

**Qué hace turbo.** Para cada paquete lanza `pnpm run <script>` buscando `pnpm` en el `PATH`. No usa
el pnpm que lo invocó.

**Qué hay en la máquina afectada.**

| Comprobación | Resultado |
| --- | --- |
| `where pnpm` | `%APPDATA%\npm\pnpm.cmd` (único) |
| `npm ls -g --depth=0` | `pnpm@11.9.0` instalado globalmente con npm |
| Lanzadores de corepack en `C:\Program Files\nodejs` | Solo `corepack` y `corepack.cmd`: `corepack enable` nunca se ejecutó |
| `pnpm --version` dentro del repositorio | `9.0.0` |
| `pnpm --version` fuera del repositorio | `11.9.0` |
| `corepack pnpm --version` | `9.0.0` |
| `corepack pnpm lint` | 0 de 4 tareas; error de versión en las 4 |
| `pnpm lint` (sin `corepack`) | 4 de 4 tareas |
| `corepack pnpm exec pnpm --version` | Mismo error de versión, código de salida 1 |
| Orden en el `PATH` | `C:\Program Files\nodejs\` antes que `%APPDATA%\npm` (las posiciones cambian según la consola) |
| Escritura en `C:\Program Files\nodejs` sin elevar | No permitida |

El mensaje de error completo:

```
[ERROR] This project is configured to use 9.0.0 of pnpm. Your current pnpm is v11.9.0
Corepack invoked pnpm with this version, and pnpm does not switch versions when running under corepack.
```

**Grafo de turbo** (`turbo run build lint test typecheck dev --dry=json`): modo de entorno `strict`;
`@finops/frontend` tiene las cinco tareas; `@finops/backend`, `@finops/processor` y
`@finops/azure-cost-api` tienen `build`, `lint`, `test` y `dev`, y no declaran `typecheck`;
`@finops/shared-config` no declara ningún script. Ninguna tarea tiene dependencias, porque ningún
paquete del workspace depende de otro.

**CI.** Los jobs ejecutan `corepack enable` antes de usar pnpm. El job del frontend ya pasa por turbo
en `corepack pnpm lint --filter=@finops/frontend` y `corepack pnpm test --filter=@finops/frontend`.

**Documentación.** `README.md` usa `corepack pnpm ...` en el arranque con Docker Compose y
`pnpm install` / `pnpm dev`, sin `corepack`, en el bloque "Con Turborepo". En ningún sitio menciona
`corepack enable`.

## Goals / Non-Goals

**Goals:**

- Que la causa de `RF-093-001` quede demostrada con salidas reales y no solo razonada.
- Que la corrección se pueda repetir en cualquier máquina del equipo con un paso y comprobar con un
  comando.
- Que la verificación de `dev` y del grafo distinga lo que hace turbo de lo que hace cada
  aplicación.

**Non-Goals:**

- Automatizar la comprobación del gestor de paquetes en una herramienta del repositorio (ver
  decisión 4).
- Corregir fallos de `build` o `test` de las aplicaciones Python que la batería desde la raíz pueda
  destapar: se registran como hallazgos.
- Declarar `typecheck` en los paquetes Python o dar scripts a `@finops/shared-config`.
- Reescribir la documentación archivada de las seis tarjetas que usaron el sustituto.

## Decisions

### 1. La causa es de entorno: falta el lanzador de corepack y un pnpm global ocupa su lugar

La cadena, paso a paso:

1. `corepack pnpm lint` arranca pnpm `9.0.0` y exporta `COREPACK_ROOT` a sus procesos hijos.
2. pnpm `9.0.0` ejecuta `turbo run lint`.
3. turbo lanza `pnpm run lint` por paquete y el `PATH` lo resuelve al pnpm global `11.9.0`, porque no
   hay lanzador de corepack que se resuelva antes.
4. pnpm `11.9.0` ve que el proyecto pide `9.0.0`. Normalmente descargaría esa versión y se cambiaría
   a ella, pero al encontrar `COREPACK_ROOT` entiende que corepack ya eligió la versión y aborta.

Dos datos lo confirman: el comando `corepack pnpm exec pnpm --version` reproduce el error sin turbo
de por medio, y `pnpm lint` sin `corepack` pasa, porque sin `COREPACK_ROOT` el pnpm global sí cambia
de versión, tanto en el proceso exterior como en los que lanza turbo.

Esto corrige dos afirmaciones del hallazgo original:

- "`packageManager: pnpm@9.0.0` resuelve correctamente en shell interactiva": el `9.0.0` que devuelve
  `pnpm --version` no viene de corepack sino del cambio automático de versión del pnpm global.
- "`pnpm lint`/`pnpm build` ya fallaban igual": hoy `pnpm lint` sin `corepack` pasa. Lo que falla es
  la combinación de `corepack pnpm` con un pnpm global en el `PATH`.

El diagnóstico hecho al proponer no sustituye a la evidencia: las tareas lo repiten y guardan las
salidas antes de cambiar nada en la máquina.

### 2. Corrección: activar los lanzadores de corepack en la máquina; el repositorio no cambia de configuración

`corepack enable`, desde una consola con permisos de administrador, crea `pnpm.cmd` en
`C:\Program Files\nodejs`. Ese directorio va antes que `%APPDATA%\npm` en el `PATH`, así que turbo
pasa a encontrar el lanzador de corepack, que respeta `packageManager` y ejecuta `9.0.0`. Es lo mismo
que hace CI, que nunca ha fallado.

Desinstalar el pnpm global (`npm uninstall -g pnpm`) es opcional: el orden del `PATH` ya da prioridad
al lanzador. Se recomienda en la documentación para no tener dos pnpm, pero lo decide quien usa la
máquina, porque afecta a sus otros proyectos.

Alternativas consideradas:

| Alternativa | Por qué no |
| --- | --- |
| Invocar `pnpm <script>` sin `corepack` | Funciona hoy en esta máquina, pero solo porque el pnpm global es reciente y sabe cambiar de versión. Con otro pnpm global, o sin ninguno, el resultado es distinto. Contradice la invocación que documentan `AGENTS.md`, `CONTRIBUTING.md` y CI. Se documenta como salida de emergencia, no como norma. |
| Añadir `devEngines.packageManager` a `package.json`, como sugiere el mensaje | El mensaje se refiere a que los dos campos discrepen. Aquí el problema es que pnpm no cambia de versión bajo corepack, y un campo más no lo altera. Añadiría una segunda fuente de verdad para la versión. |
| Relajar la comprobación (`pmOnFail`, `package-manager-strict=false`) | Las tareas correrían con pnpm `11.9.0` mientras la instalación usa `9.0.0`. Quita la protección que evita que alguien reescriba el lockfile con otra versión. |
| Subir `packageManager` a `pnpm@11.9.0` | Solo coincide con esta máquina; cualquier otro pnpm global reproduce el fallo. La tarjeta lo excluye salvo que sea la solución, y no lo es. |
| Envolver turbo en un script que borre `COREPACK_ROOT` | Arregla el síntoma dentro del repositorio a costa de una pieza propia que mantener y de depender de un detalle interno de corepack y pnpm. |

### 3. Se mantiene `corepack pnpm <script>` como invocación del repositorio

No se cambia la convención. El bloque "Con Turborepo" de `README.md` pasa a usar
`corepack pnpm install --frozen-lockfile` y `corepack pnpm dev`, como el resto del documento, y se
añade el paso `corepack enable` a los requisitos previos. Con los lanzadores activados, `pnpm` a
secas también ejecuta `9.0.0`, así que la lista "Comandos Principales" sigue siendo válida tal cual;
solo se le añade una nota que remite al requisito previo.

`AGENTS.md` y `CONTRIBUTING.md` no se tocan: sus comandos ya son correctos con el requisito previo
cumplido y `README.md` es el documento de arranque.

### 4. Diagnóstico con un comando documentado, sin herramienta nueva

`corepack pnpm exec pnpm --version` desde la raíz imprime `9.0.0` en una máquina preparada. En una
afectada imprime el error de versión o **otra versión**, según la del pnpm que se resuelva: con
`11.9.0` y `11.1.3` dio el error; con `11.19.0` (entorno de ejecución de un asistente, en la máquina
de Alejandro) imprimió `11.19.0` sin error. Por eso el criterio es «imprime exactamente `9.0.0`», no
«no da error». Sirve para tres cosas: comprobar la corrección, preguntar al equipo y resolver dudas
futuras.

Alternativa considerada: añadir la comprobación a `local:doctor` o a una herramienta nueva con sus
tests. Se descarta en esta tarjeta porque `local:doctor` pertenece a la spec
`local-runtime-operations` (diagnóstico del entorno Docker), el carril es `light` y el fallo solo
está confirmado en una máquina. Si el equipo lo reproduce en más máquinas, se propone como tarjeta
propia.

### 5. Verificación de `dev` y del grafo, separando turbo de las aplicaciones

- **Grafo.** `turbo run build lint test typecheck dev --dry=json` da el plan sin ejecutar nada. El
  resultado esperado es el de la sección Context: el frontend con cinco tareas y ninguna dependencia.
  Que `build` no dependa de nada es correcto mientras ningún paquete dependa de otro; la regla
  `^build` de `turbo.json` es la que garantiza el orden cuando eso cambie, y se comprueba leyendo la
  configuración, sin crear una dependencia artificial.
- **`dev`.** Se registra por separado que turbo inicia los cuatro procesos y que cada aplicación
  queda sirviendo. Backend y processor necesitan la infraestructura de `docker-compose.yml`
  (CockroachDB, RabbitMQ y pgvector); si una aplicación se cae por falta de infraestructura, eso se
  anota como tal y no como fallo del pipeline. Cada aplicación se comprueba con una petición a su
  puerto: 5173, 8000, 8001 y 8002.
- **Batería.** Los cuatro scripts se ejecutan antes y después de la corrección. El criterio de la
  tarjeta es la ausencia del error de versión; cualquier otro fallo se anota con su tarea y su causa.

### 6. `RF-093-001` se cierra como `Fixed` con la causa reformulada

La fila conserva su descripción original y añade en la columna de resolución la causa de la
decisión 1, la corrección de la decisión 2, las dos afirmaciones corregidas y el enlace a la
evidencia. Estado `Fixed`, no `Open` reformulado: aunque la causa es de entorno, el hueco del
repositorio (el requisito previo sin documentar) queda cerrado y la máquina afectada, corregida.

Si la corrección no funcionara en la máquina, el hallazgo se queda `Open` con la causa precisa y la
evidencia de lo que se probó.

**Revisión en el gate post-review (2026-10-04):** la corrección funcionó en dos máquinas, pero Paris no
respondió y de Alejandro solo se tiene su entorno de Codex. Se decidió mantener `RF-093-001` en `Open`,
reformulado con la causa y la corrección, hasta confirmar esas dos. El resto de esta decisión no cambia.

### 7. ADR: no aplica

No se introduce ninguna decisión de arquitectura duradera: el gestor de paquetes, su versión, el
orquestador y la forma de invocarlo siguen como estaban. Solo se documenta un requisito previo que
CI ya cumplía. Si durante la implementación la solución acabara siendo subir la versión de pnpm o
cambiar la invocación, sí haría falta un ADR en `docs/adr/` con la plantilla `docs/templates/adr.md`,
tomando el primer número libre en ese momento, y una revisión de la aprobación pre-código.

### 8. Sin ciclo Red/Green

La tarjeta no añade ni cambia código: solo documentación, el backlog de hallazgos, el spike y la
evidencia. No hay comportamiento que cubrir con tests unitarios ni mutantes que medir. La
verificación son los comandos reales con su salida, y la excepción se deja escrita en `review.md`.

## Risks / Trade-offs

- [La consola no tiene permisos de administrador y `corepack enable` no puede escribir en
  `C:\Program Files\nodejs`] → Alternativa a probar: desinstalar el pnpm global y ejecutar
  `corepack enable --install-directory "%APPDATA%\npm"`, que es un directorio del usuario ya presente
  en el `PATH`. Si se usa, se documenta esa variante.
- [La evidencia de "antes" se pierde al corregir la máquina] → Las tareas del grupo 1 guardan las
  cuatro salidas en `docs/evidence/JUP-103-validation.md` antes de ejecutar `corepack enable`.
- [La caché de turbo da un falso positivo: su clave no depende del gestor de paquetes, así que una
  ejecución previa sin `corepack` deja las tareas cacheadas y `corepack pnpm <script>` pasa sin
  lanzar subprocesos. Ocurrió al capturar la línea base] → Toda comprobación de "después" usa
  `--force` (o `TURBO_FORCE=true` en `pnpm test`, que no admite el indicador) y verifica que las
  tareas figuran como `cache bypass, force executing`.
- [`build` o `test` fallan desde la raíz por motivos ajenos a pnpm: dependencias de Python sin
  instalar, tests que necesitan base de datos, timeouts del frontend. Ocurrió en la línea base: 14 y
  18 errores de recolección en backend y processor, y entre 14 y 21 tests del frontend con timeout]
  → Python se prepara en un entorno virtual fuera del repositorio (`C:\Users\victo\Pontia\.venv-tfm`)
  y se activa en la consola que lanza pnpm; con él pasan los tres paquetes de Python. El frontend
  pasa 443 de 443 con `--maxWorkers=1` (`RF-098-004`), así que la batería de `test` se ejecuta en dos
  mitades, siempre desde la raíz y vía turbo; no se puede pasar el indicador a `pytest` ni declarar
  variables de entorno para Vitest sin tocar `turbo.json`, que esta tarjeta no modifica. → Se registra tarea por tarea. Si es un problema del
  repositorio, hallazgo nuevo; si es de la máquina, se anota como tal. No se da por verificado lo que
  no pasó.
- [`pnpm dev` choca con el stack de Docker Compose por los puertos 5173, 8000, 8001 y 8002] → Parar
  antes los servicios de aplicación de Compose y dejar solo la infraestructura.
- [El equipo no contesta a tiempo] → Se anota quién contestó y quién no, con fecha. El criterio queda
  como "no confirmado en la máquina de X", nunca como validado.
- [Una reinstalación de Node elimina los lanzadores de corepack] → El comando de diagnóstico lo
  detecta; la documentación lo menciona.
- [`develop` avanza durante la tarjeta] → Solo se tocan `README.md`, el backlog y el spike. Al traer
  `develop` se revisan conflictos en esos tres archivos, sobre todo en el backlog, que es un registro
  compartido.
- [Corrección de entorno en vez de corrección del repositorio] → Un clon nuevo en una máquina con
  pnpm global seguirá fallando hasta que se ejecute `corepack enable`. Se acepta: es un paso, está
  documentado en el arranque y tiene diagnóstico.

## Migration Plan

Cambio en la máquina afectada: `corepack enable` desde una consola elevada. Para deshacerlo:
`corepack disable`, que elimina los lanzadores; si se desinstaló el pnpm global,
`npm install -g pnpm@11.9.0` lo restaura.

Cambio en el repositorio: solo documentación; se revierte con el commit.
