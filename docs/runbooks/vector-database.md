# JUP-021 — Operacion de la base vectorial

Trello: https://trello.com/c/0oUtjfnH

## Alcance y contrato

PostgreSQL 17 + pgvector, imagen fijada por digest en `infra/vector/compose.yaml`.
Este Compose despliega solo la dependencia vectorial; el Compose principal sigue
siendo el punto de entrada de la aplicacion completa. No conecta automaticamente
otro backend ni acredita produccion, alta disponibilidad o calidad semantica.

El runtime actual de escritura y consulta implementa embeddings `mock` de ocho
dimensiones (SHA-256 determinista). `EMBEDDING_MODEL=economicon-embedding` es un
alias de configuracion; actualmente no cambia ese algoritmo. No mezclar datos de
otro proveedor/modelo aunque tengan ocho dimensiones. Para cambiar de modelo,
implementar escritor y lector compatibles, crear una base nueva, reingerir el
corpus y validar antes de cambiar las conexiones. No modificar la dimension
sobre un volumen existente: el processor ahora rechaza ese desajuste al iniciar.

## Arranque y smoke en una base dedicada vacia

Desde la raiz de un checkout de esta rama, en Linux con Docker Compose:

```bash
cd infra/vector
umask 077
# Solo la primera vez; conservar el secreto para un volumen existente.
test -e .env || printf 'POSTGRES_PASSWORD=%s\nPGVECTOR_PORT=55421\n' "$(openssl rand -hex 24)" > .env
docker compose -p economicon-jup021 up -d --wait postgres-pgvector
docker compose -p economicon-jup021 build validate
docker compose -p economicon-jup021 run --rm -T validate seed --confirm-dedicated-database
```

`seed` exige cero tablas en public y genera exclusivamente dos documentos
sinteticos. `verify` presupone exactamente esos documentos: es una prueba de
aceptacion de una instancia dedicada, no un monitor para una base de usuarios.
No ejecutar con datos reales. No imprimir `docker compose config` con secretos
resueltos ni guardar `.env` en Git. El password generado es URL-safe; otras
credenciales requeririan escapar caracteres reservados en la URL.

La primera inicializacion aplica 001 y 002; posteriores ejecuciones conservan el
ledger. Para una base existente, tomar copia y detener ingesta antes de arrancar
un unico migrador. La creacion del indice 002 es transaccional y puede bloquear
escrituras mientras se construye. El lock del migrador es local al proceso:
no arrancar varios migradores en procesos independientes simultaneamente.

La URL interna es `postgresql+psycopg://postgres:<secreto>@postgres-pgvector:5432/embeddings`
dentro de esa red Compose. En el host se usa `127.0.0.1:55421`. Para acceso remoto
usar tunel SSH; el puerto no se publica en todas las interfaces. Esta instancia
de validacion usa el propietario postgres, sin credenciales de produccion.

## Persistencia y recuperacion

```bash
docker compose -p economicon-jup021 up -d --force-recreate --wait postgres-pgvector
docker compose -p economicon-jup021 run --rm -T validate verify --confirm-dedicated-database
mkdir -p evidence
umask 077
docker compose -p economicon-jup021 exec -T postgres-pgvector pg_dump -U postgres -d embeddings -Fc > evidence/embeddings.dump
# Usar un nombre de proyecto y puerto nuevos, con volumen vacio.
PGVECTOR_PORT=55422 docker compose -p economicon-jup021-restore up -d --wait postgres-pgvector
PGVECTOR_PORT=55422 docker compose -p economicon-jup021-restore exec -T postgres-pgvector pg_restore -U postgres -d embeddings --exit-on-error < evidence/embeddings.dump
PGVECTOR_PORT=55422 docker compose -p economicon-jup021-restore build validate
PGVECTOR_PORT=55422 docker compose -p economicon-jup021-restore run --rm -T --no-deps validate verify --confirm-dedicated-database
PGVECTOR_PORT=55422 docker compose -p economicon-jup021-restore stop postgres-pgvector
```

No ejecutar `down -v`: elimina la persistencia. No restaurar sobre el origen ni
usar `--clean` para resolver colisiones. Un fallo de restore requiere investigar
y elegir un destino nuevo, conservando el backup y el original. La copia contiene
texto/documentos: custodiar con permisos restrictivos y fuera del repositorio.

Para un MVP operativo: copia antes de migraciones y al finalizar cada ingesta
significativa, copia protegida fuera del host y ensayo regular de recuperacion.
Este cambio valida copia/restauracion manuales; no instala programacion de backups,
replicacion ni PITR. El RPO depende de la ultima copia completada y el RTO se debe
medir con el corpus real. Una copia en el mismo disco no protege de perder el host.
Ver [pg_restore de PostgreSQL 17](https://www.postgresql.org/docs/17/app-pgrestore.html).

## Indices y capacidad

Se conserva busqueda exacta con distancia coseno `<=>`, filtrada por tenant.
La migracion 002 agrega `knowledge_documents_tenant_id_idx`; los UNIQUE existentes
de chunks y embeddings soportan los joins. El optimizador puede preferir scans
secuenciales con pocos datos. No se afirma que el B-tree acelere el ranking
vectorial ni que exista HNSW. ANN puede perder resultados al filtrar; antes de
introducirlo medir recall por tenant y planes con el corpus representativo.
Ver [indices de pgvector](https://github.com/pgvector/pgvector#indexing).

Un vector ocupa aproximadamente `4 * dimension + 8` bytes sin contar filas,
texto, indices, WAL y copias. Para 100.000 vectores, ocho dimensiones son unos
4 MB solo de vectores; 1536 dimensiones son unos 615 MB. No son limites de
capacidad ni benchmarks: el ensayo funcional usa dos documentos. Presupuestar
espacio para datos, WAL y dos copias, y medir latencia bajo concurrencia antes
de fijar capacidad/SLA. Consultar consumo con:

```bash
docker compose -p economicon-jup021 exec -T postgres-pgvector psql -U postgres -d embeddings -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
docker compose -p economicon-jup021 exec -T postgres-pgvector psql -U postgres -d embeddings -c "SELECT relname,pg_size_pretty(pg_total_relation_size(relid)) FROM pg_catalog.pg_statio_user_tables;"
docker compose -p economicon-jup021 stats --no-stream
```

## Diagnostico

| Sintoma | Comprobacion y respuesta |
| --- | --- |
| Contenedor unhealthy | `docker compose -p economicon-jup021 logs --tail=100 postgres-pgvector`; comprobar disco, permisos y disponibilidad del puerto. |
| Auth falla tras cambiar .env | El password del volumen no se reinicializa; recuperar el secreto correcto o rotarlo de forma controlada. |
| Inicializacion rechazada por dimension | Mantener configuracion correspondiente al volumen; usar base nueva para reindexar. |
| Relation no existe | Ejecutar inicializacion del processor, no solo comprobar pg_isready. |
| Consulta sin resultados | Verificar tenant, filas de ese tenant y algoritmo/dimension del vector de consulta; no eliminar el filtro tenant. |
| Consulta lenta | Revisar EXPLAIN (ANALYZE, BUFFERS) con datos representativos y estadisticas; medir antes de introducir ANN. |
| Restore falla | Conservar origen/copia, revisar error y version de imagen; no continuar como si hubiera recuperacion completa. |

`pg_isready` solo acredita disponibilidad PostgreSQL. La aceptacion funcional usa
el smoke, que comprueba tablas, extension, ledger, dimensiones, indices, lectura,
aislamiento y rechazo de reemplazos incompatibles.
