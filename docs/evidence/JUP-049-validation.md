# Evidencia de validacion JUP-049

- Tarjeta: https://trello.com/c/yZnjgiSp
- Rama: `chore/JUP-049-dockerize-services`
- Base: `origin/develop` en `a746d48`
- Pull request: pendiente
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

Se construyeron desde cero las cuatro imagenes con el proyecto Compose
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

## Participacion pendiente

- Pairing/coautoria: Lucia Mateo.
- Revision de PR: Paris Arcos Martin.
- Validacion, pruebas y documentacion: Victor Mendez.
