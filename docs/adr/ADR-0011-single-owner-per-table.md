# ADR-0011: Un unico servicio dueño por tabla compartida

- Status: Accepted
- Date: 2026-09-30
- Related JUP/OpenSpec: JUP-096, [jup-096-coordinate-migrations](../../openspec/changes/archive/2026-09-28-jup-096-coordinate-migrations/proposal.md), spec [`schema-migration-ownership`](../../openspec/specs/schema-migration-ownership/spec.md)
- Trello: https://trello.com/c/yKAMRvbK
- Supersedes: none
- Superseded by: none

## Context

Backend y processor comparten una misma CockroachDB y cada uno ejecuta sus propias migraciones al arrancar. Hasta JUP-096 los dos creaban la tabla `jobs`. Si migraban a la vez una base vacia, CockroachDB rechazaba una de las transacciones (`SerializationFailure` / `WriteTooOldError`) y el servicio perdedor no arrancaba (RF-044-002, reproducido 7/7 en la exploracion). En `docker compose` no se veia solo porque el processor tardaba en llegar a migrar.

La decision de quien crea cada tabla afecta a cualquier migracion futura de cualquier servicio, por eso se registra como decision duradera y no solo como requisito de un cambio. La revision del PR #51 lo señalo al contrastar el diseño con la capacidad `architecture-decisions`.

## Decision

- Cada tabla de la base compartida tiene un unico servicio dueño, que es el unico que la crea y la altera en sus migraciones. El backend es dueño de `users`, `tenants`, `user_tenants`, `jobs`, `conversations` y `messages`; el processor, de `azure_cost_ingestion_runs` y `azure_cost_records`.
- Un servicio puede leer o escribir filas de tablas de otro, pero nunca ejecuta DDL sobre ellas.
- Cada servicio lleva su propio registro de versiones (`schema_migrations` del backend y `processor_schema_migrations` del processor).
- El processor arranca despues de que el backend este sano (en Docker Compose, `depends_on` con `condition: service_healthy`), porque lee y actualiza `jobs`, tabla del backend. Las lecturas bajo demanda del backend sobre las tablas de costes del processor no imponen orden de arranque: el backend no depende del processor.
- Una migracion que deja de ser necesaria en el servicio que no es dueño se conserva sin DDL, con su fichero y su version, para no alterar bases existentes.

## Consequences

- Migrar a la vez una base vacia deja de tumbar servicios: solo un servicio compite por cada tabla.
- El processor depende del backend para arrancar, y su primer arranque en frio es mas lento.
- Añadir una tabla compartida obliga a decidir su dueño y a declararla en la guarda estatica `tests/test_schema_ownership_static.py` del processor, que falla si un servicio toca en sus migraciones una tabla que no es suya.
- La guarda es heuristica: no cubre DDL importado de otros modulos ni ficheros `.sql` (RF-096-004).
- El backend aun lee tablas pgvector que crea el processor en otra base (RF-096-002, riesgo aceptado).

## Alternatives Considered

- Reintentar la migracion ante `SerializationFailure`: oculta la carrera sin eliminarla y sigue dejando dos definiciones de la misma tabla.
- Un servicio `migrate` que ejecute todas las migraciones antes de backend y processor: separa migrar de servir y resolveria tambien RF-096-003, pero es un cambio mayor de topologia; queda como opcion para JUP-050.
- Bloqueo distribuido entre servicios en la base: añade coordinacion y un punto de fallo para un problema que desaparece con un dueño unico.

## Evidence And Follow-up

- Evidencia: [JUP-096-validation.md](../evidence/JUP-096-validation.md).
- Spec verificable: [`schema-migration-ownership`](../../openspec/specs/schema-migration-ownership/spec.md).
- Seguimiento: RF-096-001 a RF-096-004 en [findings](../../openspec/findings/backlog.md).
- Numeracion: ADR-0010 es de JUP-026 (PR #52) y ADR-0012 lo usa JUP-099 (PR #54).
