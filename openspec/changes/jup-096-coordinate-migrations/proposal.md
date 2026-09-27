JUP: JUP-096
Trello: https://trello.com/c/yKAMRvbK

## Why

`backend` y `processor` migran la misma CockroachDB al arrancar, cada uno con su propio registro de versiones, y los dos crean la tabla `jobs`. Cuando ambos migran una base de datos vacia a la vez, CockroachDB rechaza una de las transacciones (`SerializationFailure` / `WriteTooOldError` sobre la clave de `jobs`) y el servicio que pierde no arranca (RF-044-002).

La exploracion del 27/09/2026 sobre `develop` `3a1001d` confirma que el defecto sigue en el codigo, aunque hoy Docker Compose casi nunca lo dispara:

- Migraciones reales de ambos servicios lanzadas a la vez sobre una base vacia: 7/7 arranques con el backend caido; con el processor 0,5 s despues, 1/4; con 2 s, 0/4.
- Control: la misma prueba con el processor sin `jobs` en su migracion 001 da 0/6 fallos, luego `jobs` es la unica causa.
- Arranque en frio real con `docker compose` y volumenes nuevos: 0/5 fallos, porque el processor llega a migrar unos 90 s despues que el backend. Esa separacion es accidental (depende de lo que tarda en importar) y no una garantia.

Ademas, el processor necesita tablas que crea el backend (`jobs` hoy, y `users`/`user_tenants` si se integra JUP-086), pero nada garantiza que el backend haya migrado antes.

## What Changes

- La tabla `jobs` pasa a tener un unico dueño: el backend. La migracion `001` del processor deja de crearla. En bases de datos ya migradas no cambia nada, porque `001` ya consta como aplicada.
- En Docker Compose, el processor espera a que el backend este sano (`depends_on` con `condition: service_healthy`), de modo que el esquema del backend existe antes de que el processor lo use.
- Los tests del processor que daban por hecho que su propia migracion crea `jobs` se adaptan para crear el esquema del backend cuando lo necesiten.
- Se registra RF-096-001: RabbitMQ fallo una vez en un arranque en frio al leer `/var/lib/rabbitmq/.erlang.cookie` (`eacces`) y arranco al reintentar. Queda fuera de alcance, como candidato para JUP-050.

Fuera de alcance: locks distribuidos, un servicio de migracion aparte, reintentos automaticos y cambios en el registro de versiones de cada servicio. Tras el cambio ningun objeto de esquema se crea desde los dos servicios, asi que no hacen falta para cerrar RF-044-002.

## Capabilities

### New Capabilities

- `schema-migration-ownership`: cada tabla compartida de CockroachDB tiene un unico servicio que la crea, y dos servicios migrando a la vez una base vacia no se bloquean entre si.

### Modified Capabilities

- `containerized-runtime`: el requisito "Healthy dependency gates" añade que el processor espera a que el backend este sano.

## Impact

- `apps/processor/app/db/migrations/001_initial.py`: deja de crear `jobs`.
- `docker-compose.yml`: dependencia `processor` -> `backend` sana.
- Tests del processor que usan `jobs` tras `Database.initialize()` (por ejemplo `tests/test_azure_cost_cockroach_integration.py`).
- `openspec/findings/backlog.md`: RF-044-002 y nuevo RF-096-001.
- Coordinacion con el PR #47 (JUP-086, abierto), que tambien toca tests del processor y hace que el processor lea tablas del backend.
- Sin cambios de API, de esquema en bases existentes ni de dependencias.
