# JUP-021 — Evidencia de despliegue y recuperacion

Evidencia inicial: 2026-09-29, base `origin/develop` en `2efef1a`.
Actualizacion de correcciones: 2026-10-01, sobre `34aaa31`, que incorpora
`develop` hasta `de0d62e`. Las cifras de septiembre se conservan como historicas.
Trello: https://trello.com/c/0oUtjfnH
Rama: `feat/JUP-021-vector-database-runtime`.

## Despliegue observado

- Host de validacion del equipo; directorio de despliegue reservado al operador.
- Proyecto Compose: `economicon-jup021`, servicio `postgres-pgvector` healthy.
- Puerto: `127.0.0.1:55421`, volumen `economicon-jup021_pgvector-data`.
- Imagen: `pgvector/pgvector:pg17@sha256:cf134a767f474095eeba57e0117be8e568e011a63f33fbf252f14c9b760f8e6f`.
- Extension observada: pgvector `0.8.6`; dimensiones: ocho.
- Credencial aleatoria guardada exclusivamente en `.env` del host con permisos 600.
- Instancia auxiliar `economicon-jup021-restore` en puerto 55422, detenida tras validar.

## Resultados

| Verificacion | Resultado |
| --- | --- |
| Base sin tablas, migraciones 001 y 002 | PASS |
| Inicializacion repetida, ledger sin duplicados | PASS |
| Escritor processor y lector backend contra PostgreSQL real | PASS |
| Igualdad del embedding mock en ambos componentes | PASS |
| Consulta coseno exacta, distancia cercana a cero | PASS |
| Dos tenants, vector ajeno mas cercano, tenant inexistente | PASS |
| Reemplazo entre tenants rechazado, original intacto | PASS |
| Dimension incorrecta rechazada antes de reemplazo | PASS |
| Inicializacion con dimension nueve contra vector(8) rechazada | PASS |
| Indice tenant y UNIQUE de ambos joins presentes | PASS |
| Recreacion del contenedor con volumen conservado | PASS |
| pg_dump custom + pg_restore en otro volumen vacio | PASS |
| Retrieval y conteos despues de restaurar | PASS: 2 documentos, 2 chunks, 2 embeddings |
| Regresion processor completa, Python 3.12 | 327 passed, 49 skipped; 322 avisos de adapters SQLite obsoletos |
| Pruebas dirigidas de dimension y migrador | 12 passed |
| OpenSpec estricto | 35 passed, 0 failed |
| Trazabilidad de todos los cambios activos | PASS |
| Higiene del repositorio y git diff --check | PASS |

Los 49 skips corresponden a pruebas opt-in sin sus servicios/variables de entorno;
no se contabilizan como pruebas funcionales superadas. El smoke JUP-021 anterior
si utiliza PostgreSQL real. No se ejecuta un flujo HTTP/cola completo ni un
proveedor de embeddings externo. No hay ensayo de carga ni SLA acreditado.

Salidas JSON: `infra/vector/evidence/{before-restart,after-recreate,after-restore}.json`
en el host y copia local en
`materiales/07-evidencias/JUP-021-validacion-2026-09-29/`, fuera del repositorio.
El dump permanece en el host; no contiene datos reales, solo fixtures sinteticos.
La receta versionada esta en [el runbook](../runbooks/vector-database.md).

## Revision, validacion y correcciones del 1 de octubre

[Paris](https://github.com/EconomiconFinOps/tfm-economicon/pull/53#pullrequestreview-5376033463)
publico revision favorable sobre `07066a8`, como COMMENT, sin autorizar merge.
[Victor](https://github.com/EconomiconFinOps/tfm-economicon/pull/53#pullrequestreview-5383443171)
valido funcionalmente `34aaa31`, incluida actualizacion de base poblada 001 a
002, y solicito corregir el diagnostico de arranque y su cobertura automatizada.
Son evidencias de sus reviews; sus ensayos no se atribuyen a esta sesion.

Correcciones y nuevas comprobaciones sobre `34aaa31` mas este cambio:

- Desajuste de esquema lanza `StartupError` con texto fijo, sin datos sensibles;
  las fronteras de arranque conservan el diagnostico para el operador.
- Tests de dimension almacenada menor/mayor/no restringida y coincidente;
  tests de propagacion por `run_all.main` y lifespan real de API con dependencias
  sustituidas, sin abrir servicios externos.
- Processor: **333 passed, 49 skipped**, 322 warnings heredados; pruebas de
  dimension: **10 passed**. Mismos limites de los skips del registro anterior.
- Cuatro mutantes manuales detectados por esos tests: omitir chequeo, `!=` a `<`,
  `!=` a `>` y degradar `StartupError` a `ValueError`. No es analisis exhaustivo.
- Smoke `verify` contra PostgreSQL real del despliegue persistente: **PASS**,
  pgvector 0.8.6, ledger 001/002, conteos 2/2/2. Ahora prueba configuracion 7 y 9
  contra esquema 8 y la definicion del indice sobre tenant_id, no solo su nombre.
  Imagen del validador reconstruida con las correcciones; servicio DB healthy.
- No se repiten seed, recreacion ni restauracion: no cambia el esquema ni el
  procedimiento y sus evidencias iniciales y validacion de Victor se conservan.
- RF-021-001 registra el problema heredado de dimension solo en fichero de
  entorno; workaround documentado, sin atribuir una correccion inexistente.
- OpenSpec estricto **36/36**, trazabilidad de **9 cambios** e higiene correctas;
  `git diff --check` sin errores.

## Aceptacion y comprobacion del 2 de octubre

[Victor aprobo las correcciones](https://github.com/EconomiconFinOps/tfm-economicon/pull/53#pullrequestreview-5384205603)
el 1 de octubre, levantando su peticion de cambios. Su validacion identifica
`db2a047` y repite seed, recreacion, restauracion y actualizacion de base 001 a 002;
la review de GitHub esta asociada a `0591fd6`. Son ensayos del validador, no de
esta sesion. RF-021-001 permanece abierto y explicitamente no bloqueante.

[Lucia publico una revision incremental complementaria](https://github.com/EconomiconFinOps/tfm-economicon/pull/53#pullrequestreview-5385932832),
sin cambios solicitados; no sustituye la revision asignada a Paris.

El 2 de octubre se incorpora develop por Update branch, conservando la aprobacion:
head `2b90cec`, con el procedimiento JUP-100 y sin cambios adicionales en el runtime.
[CI tecnico](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37051419193)
y [JUP reviews](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37051419362)
pasan los ocho controles requeridos sobre ese head. Un run anterior de JUP reviews
fue cancelado y no se contabiliza como resultado satisfactorio.

El despliegue persistente remoto sigue healthy. Se repite `verify` del runbook
con `--confirm-dedicated-database`: PASS, pgvector 0.8.6, migraciones 001/002,
conteos 2/2/2 y las ocho comprobaciones del smoke. No se repiten seed,
recreacion ni restauracion en esta sesion; sus evidencias conservan su fecha.

Se marcan las tareas 2.6 y 3.5 conforme a las reviews publicadas y se archiva
OpenSpec en la misma rama, como requiere CONTRIBUTING. Este cierre documental
no cambia el codigo desplegado. El merge y el cierre en Trello quedan sujetos
a la aprobacion vigente y los controles del head final.
