# JUP-021 — Evidencia de despliegue y recuperacion

Fecha: 2026-09-29. Base: `origin/develop` en `2efef1a`.
Trello: https://trello.com/c/0oUtjfnH
Rama: `feat/JUP-021-vector-database-runtime`.

## Despliegue observado

- Host: DockerServer, directorio `/home/danteadmin/economicon-deployments/jup021-vector-20260929`.
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

La revision humana del PR y la validacion asignada al equipo siguen pendientes.
Estas ejecuciones automatizadas no se atribuyen a los cuatro responsables de
Trello y no justifican marcar la tarjeta Hecho antes de su revision.
