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
la imagen y limitando la escritura al tmpfs declarado.

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
| Topologia Docker | 5/5 |
| Contrato del workflow CI | 7/7 |
| OpenSpec estricto | 17/17 |
| Trazabilidad JUP-049 | OK |
| Higiene del repositorio | 319 archivos, OK |
| `git diff --check` | OK |

## Smoke aislado en dockerserver

Pendiente. Se utilizara un nombre de proyecto exclusivo y puertos alternativos;
no se reemplazara ningun contenedor estable del servidor.

## Participacion pendiente

- Pairing/coautoria: Lucia Mateo.
- Revision de PR: Paris Arcos Martin.
- Validacion, pruebas y documentacion: Victor Mendez.
