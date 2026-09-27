JUP: JUP-096

## Context

Estado en `develop` `3a1001d`:

```
                 CockroachDB (una base, dos registros de versiones)
   backend  --migra-->  schema_migrations            + tenants, users, user_tenants,
                                                       jobs, conversations, messages
   processor --migra--> processor_schema_migrations  + jobs (001), azure_cost_* (002-004)
```

- Cada servicio aplica sus migraciones en `Database.initialize()` al arrancar. El backend lo hace en una sola transaccion; el processor, en una transaccion por migracion y con un `threading.Lock` de proceso que solo coordina sus hilos API y worker (RF-044-001, JUP-049).
- `jobs` es el unico objeto que crean los dos. Ambas definiciones son identicas (`CREATE TABLE IF NOT EXISTS`), pero en CockroachDB dos transacciones que crean la misma tabla a la vez escriben la misma clave del catalogo y una de ellas recibe `SerializationFailure`.
- En Docker Compose el processor depende de CockroachDB, RabbitMQ, pgvector y la API de Azure simulada, pero no del backend.
- La exploracion (resultados en `proposal.md`) reprodujo la carrera con las migraciones reales y aisló la causa en `jobs` con un control.

## Goals / Non-Goals

**Goals:**
- Que ninguna tabla se cree desde dos servicios, para que la migracion simultanea de una base vacia no pueda fallar.
- Que el processor arranque en Docker Compose solo cuando el esquema del backend ya existe.
- No alterar datos ni historial de versiones de bases de datos ya migradas.

**Non-Goals:**
- Lock distribuido, servicio de migracion dedicado o registro de versiones unificado.
- Reintentos automaticos de migracion.
- Resolver el fallo intermitente de RabbitMQ (RF-096-001), que se registra para JUP-050.
- Coordinar varios procesos del processor entre si (por ejemplo `run_azure_cost_ingestion` lanzado a mano durante el primer arranque); hoy migran objetos propios del processor y ese caso no forma parte de RF-044-002.

## Decisions

### 1. El backend es el unico dueño de `jobs`

La migracion `001` del processor deja de crear `jobs` y queda sin operaciones de esquema; el fichero y su version `001` se conservan.

- Por que el backend: el backend crea los jobs (`POST /jobs/ingest`) y ya es dueño de las tablas de identidad y tenant con las que `jobs` se relaciona; el processor solo cambia su estado.
- Por que editar `001` en lugar de añadir una migracion nueva: la carrera ocurre dentro de `001` en una base vacia, asi que una migracion posterior no la evita. En bases existentes `001` ya consta como aplicada y no se vuelve a ejecutar, y la tabla que creo se conserva; el cambio solo afecta a bases nuevas.
- Por que conservar el fichero y la version: borrar `001` cambiaria la numeracion y el significado de las versiones ya registradas en bases existentes.
- Alternativa descartada, comprobar si `jobs` existe antes de crearla: los dos servicios pueden ver la tabla ausente a la vez y la carrera sigue.

### 2. El processor espera a que el backend este sano

Se añade `backend: condition: service_healthy` al `depends_on` del processor. El healthcheck del backend solo pasa despues de `Database.initialize()`, asi que su esquema existe cuando el processor arranca. No hay ciclo: el backend no depende del processor.

- Coste aceptado: el processor ya no arranca si el backend no esta sano. Hoy el processor no puede procesar jobs sin la tabla del backend, asi que no pierde ninguna capacidad util.

### 3. Sin reintentos ni lock

Tras la decision 1 ningun objeto de esquema se crea desde dos servicios, y el control de la exploracion dio 0/6 fallos sin `jobs`. Un reintento solo ocultaria una colision futura en lugar de impedirla; la spec `schema-migration-ownership` hace explicita la regla para que un revisor la detecte.

### 4. `/health` del processor tolera la ausencia de `jobs`

La revision adversarial (pasadas 1 a 3) mostro que, sin `jobs`, `/health` respondia 500 donde `develop` respondia 200. El endpoint cuenta los jobs primero y solo si la consulta falla con un error de base de datos comprueba si `jobs` existe: si no existe, responde 200 `degraded` con `jobs` nulo y registra un aviso; en cualquier otro caso el error se propaga como antes (base caida o fallo de programacion siguen siendo visibles). Asi el caso normal sigue siendo una sola consulta y la existencia se decide con la misma resolucion de nombres que la consulta real solo cuando hace falta.

### 5. Sin ADR nuevo

La regla duradera (un unico dueño por tabla) queda como requisito en la capacidad `schema-migration-ownership`, verificable con escenarios. El orden de arranque es un ajuste del requisito existente de `containerized-runtime`. Ademas, PR #47 ocupa ADR-0008 y ADR-0009, y un ADR aqui competiria por la numeracion sin aportar mas que la spec.

## Risks / Trade-offs

- [Un test o una herramienta dependia de que el processor creara `jobs`] -> Mitigacion: barrido de usos de `jobs` en `apps/processor` antes de implementar; `tests/test_azure_cost_cockroach_integration.py` (`_assert_schema`) ya se sabe afectado y pasara a comprobar que el processor no la crea.
- [El processor se ejecuta fuera de Compose antes que el backend, por ejemplo en local o con `pnpm dev`] -> Sus migraciones terminan bien y el worker no recibe jobs hasta que el backend los crea. `/health` lee `jobs`: se cambia para responder 200 `degraded` con `jobs` nulo y un aviso `backend_schema_missing` mientras la tabla no existe (decision 4). PR #47 retira esa lectura de `/health`; si se integra antes, la decision 4 deja de aplicar.
- [Conflicto con PR #47] -> #47 toca tests del processor y hace que el processor lea `users` y `user_tenants`. Si se integra antes, se actualiza esta rama y se repite la bateria; ambos cambios son coherentes (el processor ya no crea ninguna tabla del backend).
- [Arranque mas lento del stack completo] -> El processor espera al backend (unos 10-25 s medidos). Aceptado.
