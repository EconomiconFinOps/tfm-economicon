# Evidencia de validacion JUP-049

Ultima reconciliacion: **2026-09-08**, documentada en la seccion
"Reconciliacion de migraciones, TypeScript y observabilidad". Los resultados
anteriores se conservan como evidencia historica.

- Tarjeta: https://trello.com/c/yZnjgiSp
- Rama: `chore/JUP-049-dockerize-services`
- Base: `origin/develop` en `a746d48`
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/16
- CI remota: https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/33096401448
- Fecha: 2026-08-27

## Auditoria inicial

El Compose heredado declaraba los siete servicios del MVP y las cuatro imagenes
de aplicacion. Una construccion limpia en `dockerserver` confirmo que backend,
processor y Azure Cost API construian, pero frontend fallaba porque Corepack
descargaba pnpm 11.24.0 sobre Node 20.20.2 y este runtime no ofrece
`node:sqlite`.

Tambien se observo que backend y processor no declaraban usuario no privilegiado
ni healthcheck en su imagen; esos dos servicios y frontend mantenian el
filesystem raiz escribible. Las imagenes base y dos dependencias de
infraestructura usaban referencias mutables.

El primer smoke de la correccion construyo las cuatro imagenes, pero frontend
termino al intentar que Corepack crease `/home/node/.cache` sobre la raiz de
solo lectura. El runtime se corrigio para invocar directamente el binario Vite
ya instalado; pnpm y Corepack quedan limitados a la fase de build.

El segundo arranque encontro que `vite preview` genera temporalmente una copia
compilada de su configuracion junto al archivo original. El comando final copia
la configuracion a `/tmp` y carga esa copia, manteniendo inmutable el codigo de
la imagen y limitando la escritura al tmpfs declarado. `NODE_PATH` conserva la
resolucion de los modulos instalados desde esa ubicacion temporal.

El siguiente intento dejo frontend saludable y revelo un defecto distinto en
processor: `PROCESSOR_PORT` se reutilizaba como puerto publicado e interno. Al
publicar `18050`, Uvicorn escuchaba dentro del contenedor en `18050` mientras el
healthcheck consultaba el puerto contractual `8001`. Compose separa ahora todos
los `*_HOST_PORT` de los cuatro puertos internos fijos.

## Correcciones versionadas

- Las cuatro imagenes de aplicacion y las tres de infraestructura fijan digest.
- Frontend activa pnpm 9.0.0, usa el lockfile del workspace y sirve un build
  previo mediante `vite preview`.
- Las cuatro aplicaciones declaran usuario no root y healthcheck.
- Compose añade init, raiz de solo lectura, `/tmp` temporal y
  `no-new-privileges` a las aplicaciones.
- `tools/docker-topology.test.mjs` comprueba topologia, digests, healthchecks,
  dependencias y baseline de privilegios dentro del check CI `OpenSpec`.

## Validaciones locales

| Validacion | Resultado |
|---|---:|
| Topologia Docker | 7/7 |
| Contrato del workflow CI | 7/7 |
| OpenSpec estricto | 17/17 |
| Trazabilidad JUP-049 | OK |
| Higiene del repositorio | 319 archivos, OK |
| `git diff --check` | OK |
| Azure Cost API | 58/58 |
| Backend | 10/10 |
| Processor | 126/126 |
| Frontend production build | 89 modulos, OK |

## Smoke aislado en dockerserver

Se construyeron desde cero las cuatro imagenes desde `f278a2e` con el proyecto Compose
`economicon-jup049-audit`. Se publicaron puertos alternativos `18049`, `18050`,
`15173` y `18052`; las dependencias se enlazaron solo a loopback en `26259`,
`18080`, `5674`, `15674` y `5435`.

Los siete servicios alcanzaron estado `healthy`. Los endpoints observados
fueron:

| Servicio | Resultado |
|---|---|
| Backend `GET /health` | database, rabbitmq y vector_store en `ok` |
| Processor `GET /health` | dependencias en `ok`; cuatro contadores de jobs a cero |
| Azure Cost API `GET /health` | 50 filas y 4 suscripciones |
| Frontend `GET /` | HTTP 200 |

La inspeccion de las aplicaciones confirmo:

| Aplicacion | UID | Root filesystem | Privilege escalation |
|---|---:|---|---|
| Azure Cost API | 10001 | solo lectura | deshabilitada |
| Backend | 10001 | solo lectura | deshabilitada |
| Processor | 10001 | solo lectura | deshabilitada |
| Frontend | 1000 | solo lectura | deshabilitada |

Todas pudieron escribir y borrar exclusivamente en `/tmp`. Tras la prueba se
retiraron por nombre exacto los siete contenedores, la red, los dos volumenes,
las cuatro imagenes de aplicacion y `/tmp/jup049-audit-KD85A9`. No quedaron
recursos con la etiqueta de proyecto `economicon-jup049-audit` y no se modifico
ningun workload estable de `dockerserver`.

## Reconciliacion con develop — 2026-09-02

### Conflicto y resolucion

- Cabeza original de la PR: `b226f21ec379f29e52be7fff92acbeb9c6ecb4bc`.
- Base comprobada: `develop` en `6e34f1ff431b53dc293dc06b1303ba719d458c28`.
- GitHub informaba `CONFLICTING` / `DIRTY`; `git merge-tree --write-tree`
  reprodujo un unico conflicto, en `apps/backend/Dockerfile`.
- Merge de reconciliacion: `547c6c72c11033786cd1fae75e531bd50bd431b0`.
- Se conserva `CMD ["python", "-m", "app.run"]` de JUP-042 junto al digest,
  usuario `economicon` y healthcheck de JUP-049. El entrypoint mantiene
  `access_log=False` y `log_config=None`, necesarios para los logs JSON.

### Fallo descubierto durante el arranque en frio

Las cuatro imagenes construyeron con `--pull --no-cache`, pero el primer
arranque sobre volumenes vacios termino con codigo 3 en processor. El worker y
la API ejecutaban migraciones simultaneamente y PostgreSQL rechazo la creacion
duplicada de `vector_schema_migrations` con `pg_type_typname_nsp_index`.

El commit `3888813d6cbbdebbc6556665b9a7ad2dd903b13c` serializa las transacciones
del migration runner entre los hilos del mismo proceso. La prueba de regresion
lanza dos runners con engines independientes y comprueba que cada migracion se
aplica una sola vez sin transacciones concurrentes. No se presenta como una
solucion de coordinacion entre replicas independientes.

La primera ejecucion del harness de pytest encontro ademas permisos insuficientes
en su montaje `/source`: el directorio temporal se habia creado con modo 0700.
Se cambio a 0755 para permitir su lectura por los usuarios no root de las
imagenes; no fue necesario cambiar los permisos de las aplicaciones.

### Construccion y pruebas repetidas

Entorno: `dockerserver`, Docker Engine 29.6.2, Compose v5.3.1. Proyecto aislado:
`economicon-jup049-reconcile-20260902`. Las cuatro imagenes se construyeron sin
cache desde `547c6c7`; processor se reconstruyo tambien sin cache tras
`3888813`. Las otras tres aplicaciones no cambiaron entre ambos commits.

| Validacion | Resultado |
|---|---:|
| Construccion de las cuatro imagenes | OK |
| Frontend production build | 89 modulos |
| Topologia Docker y contrato CI | 14/14 |
| OpenSpec estricto | 19/19 |
| Trazabilidad JUP-049 e higiene | OK |
| Backend sobre imagen construida | 17/17 |
| Processor sobre imagen construida | 135/135 |
| Azure Cost API sobre imagen construida | 58/58 |
| Dos arranques consecutivos con volumenes vacios | 7/7 healthy en ambos |
| HTTP en cada smoke | 4/4 endpoints HTTP 200 |

Pytest se ejecuto con Python 3.12 y las dependencias de cada imagen, instalando
`requirements-dev.txt` en un venv temporal con `--system-site-packages`.
Los contenedores de prueba mantuvieron usuario no root, root de solo lectura,
`/tmp` temporal y `no-new-privileges`. Las suites emitieron avisos por la clave
corta usada en tests JWT y la deprecacion de Starlette/httpx; no hubo fallos.

En ambos smokes, backend y processor devolvieron `database`, `rabbitmq` y
`vector_store` en `ok`; processor mostro los cuatro contadores de jobs a cero.
Azure Cost API devolvio 50 filas y 4 suscripciones y frontend sirvio su HTML.
Se verificaron los UID 10001/1000, root de solo lectura, init,
`no-new-privileges` y escritura temporal en `/tmp` en las cuatro aplicaciones.

Todos los registros capturados de backend y processor fueron JSON e incluyeron
su nombre de servicio. Los accesos a `/health` conservaron `request_id` UUIDv4,
timestamp, nivel, duracion y estado 200, sin registros de acceso duplicados
del logger `uvicorn.access`.

### Reproduccion

Variables del archivo temporal `.smoke.env` (puertos de aplicaciones enlazados
solo a loopback para este smoke):

```dotenv
API_HOST_PORT=127.0.0.1:18049
PROCESSOR_HOST_PORT=127.0.0.1:18050
FRONTEND_HOST_PORT=127.0.0.1:15173
AZURE_COST_API_HOST_PORT=127.0.0.1:18052
COCKROACH_SQL_PORT=26259
COCKROACH_HTTP_PORT=18080
RABBITMQ_PORT=5674
RABBITMQ_MANAGEMENT_PORT=15674
PGVECTOR_PORT=5435
VITE_API_BASE_URL=http://localhost:18049
```

Comandos principales ejecutados sobre la copia aislada del codigo:

```sh
docker compose --env-file .smoke.env -p economicon-jup049-reconcile-20260902 config -q
docker compose --env-file .smoke.env -p economicon-jup049-reconcile-20260902 build --pull --no-cache
docker compose --env-file .smoke.env -p economicon-jup049-reconcile-20260902 up -d --wait --wait-timeout 240
```

Entre arranques se utilizo `down --volumes` con ese mismo nombre de proyecto.
El smoke comprobo `/health` en los puertos 18049, 18050 y 18052, `/` en 15173,
`docker inspect`, `docker exec ... id -u` y los logs de backend y processor.

Al terminar se ejecuto `down --volumes --rmi local` sobre el proyecto exacto.
Se comprobo que no quedaban contenedores, volumenes, redes ni imagenes de ese
proyecto y se retiro `/tmp/jup049-reconcile-20260902` junto a su archivo fuente.
Los logs de construccion, pytest, ambos smokes, el fallo inicial y la limpieza
se conservaron fuera del repositorio en el directorio local de evidencias
`materiales/07-evidencias/jup049-reconciliation-20260902/`.

## Reconciliacion de CI con develop — 2026-09-07

- Cabeza original de la PR: `747e83708cd52179aa6c6fa9d28aa6d822c2c4ae`.
- Base comprobada: `develop` en `b6eaa8709856b4c120bb94dc2ce7304dcf722a26`.
- GitHub informaba `CONFLICTING` / `DIRTY`, sin revisores solicitados.
- Los conflictos afectaban a `.github/workflows/ci.yml` y
  `tools/ci-workflow.test.mjs`: ambas ramas habian anadido una validacion
  distinta en el mismo punto de la lista.
- La resolucion conserva `docker:validate` de JUP-049 y `collaboration:test`
  de JUP-081, junto a la preparacion de Python 3.12 incorporada en `develop`.

| Validacion de la reconciliacion | Resultado |
|---|---:|
| Topologia Docker y contrato CI | 14/14 |
| Puente de colaboracion, con servicios simulados | 12/12 |
| OpenSpec estricto | 21/21 |
| Trazabilidad de todos los cambios activos | OK |
| Higiene del repositorio | 382 archivos, OK |
| `git diff --check --cached` | OK |

Esta reconciliacion no cambia codigo de aplicaciones, Dockerfiles ni Compose.
No se repitieron los builds ni los smokes Docker del 2 de septiembre.

## Reconciliacion de migraciones, TypeScript y observabilidad — 2026-09-08

- Cabeza original de la PR: `3d8e704537d5989b882e65b56593fe0c428d55ca`.
- Base comprobada: `develop` en `199f9be789f52712b59a95805d74df59a81509bc`.
- Antes de publicar se integro tambien `ae538aadbf8012c144d540644691a9d80a5a4508`
  (JUP-088), incorporado a `develop` durante la validacion. Esta segunda
  integracion solo afecta a documentacion, especificaciones y gobernanza;
  aplicaciones, Dockerfiles, Compose y dependencias mantienen el codigo
  comprobado en DockerServer.
- El conflicto `add/add` en `apps/processor/tests/test_migration_runner.py`
  se resuelve conservando las pruebas de concurrencia de JUP-049 y las de
  rollback, reintento y autocommit de JUP-013.
- La fusion automatica del runner liberaba el bloqueo antes de aplicar las
  migraciones. La prueba de concurrencia reprodujo el fallo. El bloqueo ahora
  cubre toda la ejecucion, conservando las transacciones individuales y el modo
  autocommit de `develop`; la prueba cubre ambos modos.
- El frontend carga `vite.config.ts` desde `/tmp`, compatible con JUP-093 y
  la raiz de solo lectura. Se conservan las dependencias de JUP-094.
- La topologia acepta los nueve servicios y cuatro volumenes tras JUP-043,
  manteniendo los controles originales y comprobando tambien los montajes,
  dependencias y puertos de Prometheus/Grafana.

| Validacion local | Resultado |
|---|---:|
| Migraciones: concurrencia, rollback y reintentos, Python 3.11 | 8/8 |
| Herramientas del repositorio, incluida topologia Docker y contrato CI | 63/63 |
| Puente de colaboracion con servicios simulados | 12/12 |
| OpenSpec estricto tras integrar JUP-088 | 26/26 |
| Trazabilidad, higiene y corpus | OK |
| Frontend typecheck | OK |
| Frontend build | 89 modulos, OK |
| `git diff --cached --check` | OK |

El bloqueo sigue limitado a los hilos del mismo proceso; no coordina replicas
independientes. Los controles de digest y endurecimiento de JUP-049 mantienen
su alcance original sobre las cuatro aplicaciones y las tres dependencias
base; los servicios de monitorizacion conservan su configuracion de JUP-043.

### Build y smoke aislados

Fuente de codigo comprobada: git tree `1d05259b2db193bded864d7491a238d89e0f524c`.
Entorno: DockerServer, Docker Engine 29.6.2 y Compose v5.3.1. Proyecto exclusivo:
`economicon-jup049-reconcile-20260908`, con puertos alternativos enlazados a
loopback y volumenes inicialmente inexistentes.

- Las cuatro imagenes construyen con `docker compose build --pull`, permitiendo
  reutilizar cache; el frontend compila 89 modulos.
- `docker compose up --wait` completa el arranque. Las cuatro aplicaciones
  responden HTTP 200, igual que `/metrics` de backend y processor.
- Prometheus responde a sus endpoints de salud y disponibilidad y ambos
  targets estan UP. Grafana responde a `/api/health` con la base de datos en OK.
- Frontend ejecuta como `node`, UID 1000, con raiz de solo lectura y `/tmp`
  en tmpfs. Carga `vite.config.ts` desde `/tmp`; una escritura en la raiz
  devuelve EROFS.
- CockroachDB registra las migraciones 001, 002 y 003 del processor tras el
  arranque en frio, incluida la migracion autocommit de normalizacion.

Las suites se ejecutaron sobre las imagenes construidas con Python 3.12,
fuentes montadas en solo lectura y un venv temporal. Las pruebas de integracion
usaron otro nodo CockroachDB vacio, marcado expresamente para pruebas, separado
de las bases de datos de las aplicaciones.

| Suite sobre imagen | Resultado |
|---|---:|
| Processor, incluidos 34 casos con CockroachDB real | 188/188, sin omisiones |
| Backend | 24/24 |
| Azure Cost API | 58/58 |

Los logs y el harness quedan fuera del repositorio en
`materiales/07-evidencias/jup049-reconciliation-20260908/`.

## Participacion prevista inicialmente

La solicitud actual de revision se dirige a Victor Mendez (`Victorh1397`),
por indicacion del 7 de septiembre. La distribucion original se conserva
a continuacion como referencia; la revision humana sigue pendiente.

- Pairing/coautoria: Lucia Mateo.
- Revision de PR: Paris Arcos Martin.
- Validacion, pruebas y documentacion: Victor Mendez.
