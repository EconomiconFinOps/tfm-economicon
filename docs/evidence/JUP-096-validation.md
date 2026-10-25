# Evidencia de validacion JUP-096

- Fechas: 2026-09-27 y 2026-09-28.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `feat/JUP-096-coordinate-migrations` hacia `develop` (base `3a1001d`).
- Tarjeta: https://trello.com/c/yKAMRvbK.
- Change: [`jup-096-coordinate-migrations`](../../openspec/changes/archive/2026-09-28-jup-096-coordinate-migrations/proposal.md).
- Liderazgo: Lucia Mateo; pairing: Alejandro Aguado; revision de PR: Victor Mendez; validacion, pruebas y documentacion: Paris Arcos Martin.
- Entorno: Windows 10, Python 3.12.11 (misma version menor que CI y Docker), CockroachDB v24.1.11 desechable en loopback, Docker Desktop 29.7.2.

## Alcance

- La tabla `jobs` pasa a tener un unico dueño, el backend: la migracion `001` del processor queda sin DDL, conservando fichero y version.
- Docker Compose arranca el processor solo cuando el backend esta sano.
- `/health` del processor no depende de la tabla `jobs` del backend (ver Integracion con JUP-086).
- `MigrationRunner` del processor exige su tabla de versiones de forma explicita.
- Guarda estatica en CI y pruebas opt-in con CockroachDB real para la propiedad del esquema.

## Exploracion previa (sobre `develop` `3a1001d`)

Migraciones reales de ambos servicios, cada una en su proceso, sobre una base vacia (script temporal fuera del repo):

| Escenario | Resultado |
|---|---|
| Arranque simultaneo | 7/7 con el backend caido (`SerializationFailure` / `WriteTooOldError` sobre la clave de `jobs`) |
| Processor 0,5 s despues | 1/4 fallos |
| Processor 2 s despues | 0/4 fallos |
| Control: processor sin `jobs` en su `001`, arranque simultaneo | 0/6 fallos |
| `docker compose up` real con volumenes nuevos | 0/5 fallos: el processor llega a migrar ~90 s despues que el backend |

## Fase RED (codigo de produccion sin cambios)

Comando (desde `apps/processor`, nodo desechable en `127.0.0.1:36415`):

```
PROCESSOR_COCKROACH_TEST_URL='cockroachdb+psycopg://root@127.0.0.1:36415/defaultdb?sslmode=disable' \
  .venv/Scripts/python.exe -m pytest -p no:cacheprovider -v tests/test_schema_migration_ownership.py
```

Resultado: 3 failed, 3 passed en 13 min 45 s. Fallan `test_processor_alone_creates_no_backend_table` (`{'jobs'}`), `test_concurrent_cold_start_migrations_both_succeed[simultaneous]` y `[offset-0.5s]`. Pasan los de compatibilidad con bases existentes y el del backend solo.

`node --test tools/docker-topology.test.mjs` con el `docker-compose.yml` de `develop`: falla `starts the processor only after the backend owns the shared schema`.

## Fase GREEN

| Comando | Resultado |
|---|---|
| Opt-in CockroachDB: `test_schema_migration_ownership.py` + `test_azure_cost_cockroach_integration.py` | 40 passed (37 min) |
| Opt-in tras los ajustes de la revision (barrera de simultaneidad y columnas de `jobs`) | 6 passed (16 min); en los 10 arranques ambos procesos llegaron a la barrera antes de la señal |
| `pytest` backend | 259 passed |
| `pytest` processor (sin servicios) | 361 passed, 40 skipped (los opt-in) |
| `node --test tools/docker-topology.test.mjs` | 28/28 |

## Controles positivos

- Migracion `001` de `develop` restaurada temporalmente: `test_processor_alone_creates_no_backend_table` y `[simultaneous]` vuelven a fallar; el error del backend es el de reintento de transaccion de CockroachDB sobre `CREATE TABLE IF NOT EXISTS jobs`.
- Guarda estatica con la `001` de `develop`: falla `test_each_service_only_touches_its_own_tables[processor]`.
- Escaner de DDL: la primera version dejaba escapar 13 de 14 formas hostiles y la segunda 13 de 26; la actual detecta las 26, analiza los strings con `ast` (7 formas dentro de strings de Python, incluidas las que ocultaba el tratamiento de comentarios) y rechaza DDL sin tabla identificable.
- `/health` del processor contra CockroachDB real: sin `jobs` 200 `degraded`, con `jobs` 200 `ok` con cuentas, base inalcanzable 500.

## Docker Compose real

Proyecto aislado `jup096` con volumenes nuevos, imagenes construidas desde la rama:

- 3 arranques en frio: backend y processor sanos, 0 `SerializationFailure` en los logs.
- Orden medido con `docker events`: backend `health_status: healthy` a las 17:11:02, processor `start` a las 17:11:06, processor sano a las 17:12:46.
- Camino de error con un override que deja el backend sin sanar: `dependency failed to start: container jup096-backend-1 is unhealthy`; el processor queda en `created` sin arrancar (`StartedAt` vacio).
- Arranque en frio repetido tras los cambios de la revision adversarial (`/health`, `has_jobs_table`, runner): backend `StartedAt` 23:17:44, processor 23:18:25, ambos sanos, 0 `SerializationFailure`, y `GET /health` del processor en el contenedor: `{"status":"ok",...,"jobs":{"queued":0,"running":0,"failed":0,"completed":0}}`.
- Stack habitual del proyecto (`tfm-economicon`, datos existentes) levantado desde la rama: los 9 servicios sanos y el processor arrancado despues del backend.

## Integracion con JUP-086 (PR #47)

El 28/09 se integro en `develop` el PR #47, que quita los conteos globales de `jobs` de `/health` del processor por aislamiento entre tenants. Al resolver el conflicto se adopta esa version: `/health` ya no consulta `jobs`, por lo que la tolerancia a su ausencia (respuesta `degraded` con `jobs` nulo y `has_jobs_table`) deja de ser necesaria y se elimina. Las filas de `/health` de este documento anteriores a esta seccion son historicas. `test_processor_health.py` comprueba ahora que `/health` responde `ok` sin la tabla `jobs`, `degraded` si ademas falla RabbitMQ y la base inalcanzable como `failed`.

Arranque en frio repetido el 29/09 sobre la rama integrada (`86b604a`), proyecto aislado con volumenes nuevos: backend `StartedAt` 10:27:39 y processor 10:28:21, tras el backend sano; 0 `SerializationFailure` en ambos; cada servicio registra sus versiones una sola vez; `GET /health` del processor en el contenedor: `{"status":"ok","services":{"database":"ok","rabbitmq":"ok","vector_store":"ok"}}`, sin bloque `jobs`. RabbitMQ fallo con `eacces` en el primer intento (RF-096-001) y se repitio el `up`; la base de datos seguia vacia porque backend y processor aun no habian arrancado.

## Limites

- Los tests opt-in con CockroachDB real no se ejecutan en CI (RF-096-004).
- La guarda estatica es heuristica: no cubre DDL importado de otros modulos o ficheros `.sql` (riesgo aceptado, ver `review.md`).

## Nota de release

| Fecha | JUP | Nota de release | Review | ADRs |
| --- | --- | --- | --- | --- |
| 2026-09-28 | JUP-096 | `jobs` pasa a ser solo del backend y el processor arranca tras el backend sano: migrar a la vez una base vacia ya no tumba ningun servicio. | [review.md](../../openspec/changes/archive/2026-09-28-jup-096-coordinate-migrations/review.md) | [ADR-0011](../adr/ADR-0011-single-owner-per-table.md) |
