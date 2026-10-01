JUP: JUP-050

## Context

La exploracion del 2026-09-29 (rama de JUP-096) midio el arranque en frio y reprodujo los dos fallos:

- **RabbitMQ `eacces` (RF-096-001).** La imagen fija `HOME=/var/lib/rabbitmq`, que hoy es un volumen anonimo. El healthcheck `rabbitmq-diagnostics -q ping` se ejecuta como root; si corre antes de que el servidor lea su cookie, el CLI de Erlang crea `.erlang.cookie` como root (0400) y el servidor, usuario `rabbitmq` (uid 999), muere con `eacces`. Reproduccion determinista: arrancar solo RabbitMQ y lanzar el ping en el acto, 3/3 fallos con cookie 0/0; sin el ping, 2/2 correctos con cookie 999/999. Un reintento funciona porque el entrypoint hace `chown` al reiniciar.
- **Ventana de salud del processor.** `start_period` 20 s, `interval` 15 s y `retries` 10 dan unos 170 s. El primer arranque tarda unos 162 s hasta estar sano, casi todo DDL de CockroachDB (migracion 003 ~75 s, 004 ~22 s, primera conexion ~55 s); un reinicio en caliente tarda 14 s. Las migraciones corren en el `lifespan` de FastAPI antes de servir `/health`. Con carga en el host, `up --wait` falla.
- **RF-090-001** ya esta corregido desde JUP-049 (PR #16): el Dockerfile del frontend copia `pnpm-lock.yaml` e instala con `--frozen-lockfile`. Falta el control positivo que lo demuestre.
- `.env.example` deja vacios los secretos a proposito (JUP-053) y Compose los exige con `:?required`; CockroachDB sin autenticacion solo arranca con `RUNTIME_ENVIRONMENT=development|test` y `ALLOW_INSECURE_LOCAL_DATABASE=true`. Lucia decidio mantenerlo asi: rellenar `.env` sigue siendo manual y el diagnostico dice que falta.
- La cola de jobs es durable y los mensajes se publican persistentes (`delivery_mode=2`), pero sin volumen con nombre se pierden en un `down`/`up`.
- No existe endpoint para consultar el estado de un job; el estado vive en la tabla `jobs` de CockroachDB. La ingesta de costes Azure se lanza con `python -m app.run_azure_cost_ingestion` dentro del contenedor del processor. La sesion demo usa `operator@example.com` y los tenants `tenant-core` y `tenant-growth`.

## Goals / Non-Goals

**Goals:**

- `docker compose up --build --wait` correcto en frio y en caliente, sin reintentos.
- Diagnostico previo que explique cualquier `.env` incompleto, puerto ocupado o instalacion existente, sin mostrar secretos.
- Un smoke unico que recorra los siete servicios de la aplicacion y sus dependencias.
- `down`/`up` sin perdida de datos, y documentado que borra `down -v`.

**Non-Goals:**

- Generar secretos o `.env` (se mantiene la frontera de JUP-053).
- Cambiar codigo de backend, processor o frontend, o reescribir migraciones.
- Un servicio `migrate` separado (alternativa descartada abajo; RF-096-003 sigue abierto).
- RF-044-002, RF-085-002, RF-093-001, RF-096-004 y el timeout de la fixture de billing (JUP-054).

## Decisions

1. **Healthcheck de RabbitMQ como usuario `rabbitmq`**: `["CMD", "gosu", "rabbitmq", "rabbitmq-diagnostics", "-q", "ping"]`. `gosu` ya viene en la imagen oficial (lo usa su entrypoint). Probado en la exploracion con un override: arranque completo en frio en un solo `up --wait`. Alternativas descartadas: montar el cookie como fichero y retirar `RABBITMQ_ERLANG_COOKIE` (cambio mayor que toca la frontera de secretos de JUP-053); solo alargar `start_period` (no evita la carrera, solo la hace menos probable).
2. **`start_period: 300s` en el processor**, manteniendo `interval` y `retries`. Durante `start_period` los fallos no cuentan, y en cuanto el servicio responde pasa a sano: un arranque en caliente no se retrasa. Alternativas descartadas: un servicio `migrate` de una sola ejecucion (resolveria tambien RF-096-003, pero cambia la topologia y necesitaria ADR); reescribir las migraciones 003/004 (alteraria bases existentes).
3. **Volumen `rabbitmq-data` en `/var/lib/rabbitmq`.** Iguala a RabbitMQ con CockroachDB y pgvector. Se fija `hostname: rabbitmq`, porque RabbitMQ guarda sus datos por nombre de nodo y el hostname por defecto de un contenedor cambia al recrearlo. En instalaciones existentes, el primer `up` crea el volumen vacio; lo que hubiera en el volumen anonimo anterior no se migra (cola efimera de jobs de desarrollo; se documenta).
4. **Herramientas en Node sin dependencias nuevas** (`tools/local-doctor.mjs`, `tools/local-smoke.mjs`), como el resto de `tools/`: funcionan en Windows y Linux, y no exigen instalar las dependencias Python en el host. Llaman a `docker compose` con `child_process` cuando necesitan el estado de Compose.
5. **El diagnostico lee `.env` con las reglas de Compose** (comentarios, comillas, sin interpolacion anidada) y aplica la misma precedencia: el entorno del proceso gana. Los mensajes nombran variables, nunca valores; las comparaciones de credenciales decodifican las URL. Los puertos se comprueban intentando escuchar en `127.0.0.1` (y `0.0.0.0` para los de aplicacion); un puerto publicado por un contenedor de este proyecto (`docker compose ps`) no cuenta como ocupado. Los volumenes se listan con `docker volume ls` filtrando por la etiqueta del proyecto de Compose.
6. **Pasos del smoke**: `GET /health` del backend, processor y Azure Cost API, y la raiz del frontend; `POST /auth/login`; ingesta con `docker compose exec processor python -m app.run_azure_cost_ingestion --tenant-id tenant-core --subscription-id <suscripcion del simulador>`; `GET /billing/summary` con `X-Tenant-Id: tenant-core` y comprobacion de que hay coste; `POST /jobs/ingest` con un texto corto y espera hasta que `jobs.status` sea `completed`, leyendo CockroachDB con `docker compose exec cockroachdb cockroach sql`. Se usa `exec` y no `run`, para no arrancar un segundo processor que migre a la vez (RF-096-003). La ingesta de costes es idempotente (el id de ejecucion es un UUID v5 de tenant, suscripcion y consulta), asi que el smoke puede repetirse.
7. **Control positivo de RF-090-001**: construir la etapa de dependencias del frontend con un `pnpm-lock.yaml` alterado en un contexto temporal y comprobar que falla. Se ejecuta en local y queda en la evidencia; no entra en la CI, porque exige Docker.
8. **ADR: no aplica.** Son ajustes de la topologia local dentro de las decisiones existentes (JUP-049 y ADR-0011); el servicio `migrate`, que si lo necesitaria, queda descartado.

## Risks / Trade-offs

- [`start_period` de 300 s retrasa la deteccion de un processor que nunca arranca] → Compose sigue mostrando el contenedor reiniciando o saliendo, y el smoke falla con el paso concreto; es preferible a que `up --wait` falle con un stack correcto.
- [El cookie queda tambien en el volumen y `RABBITMQ_ERLANG_COOKIE` puede cambiar despues] → se comprueba en la implementacion que pasa si el valor del entorno y el del volumen no coinciden, y el README y el diagnostico recuerdan conservar el valor existente.
- [Las comprobaciones de puertos dependen del sistema operativo] → tests con un servidor real ocupando un puerto efimero; la comprobacion contra `docker compose ps` se prueba con una salida simulada.
- [El smoke depende de `docker compose exec` y del nombre del proyecto] → usa el proyecto de Compose del directorio actual o `COMPOSE_PROJECT_NAME`, como el propio Compose.
- [Medidas de tiempo tomadas en un solo host] → la evidencia registra la duracion del arranque en frio en la validacion; si supera la ventana, se ajusta con el dato.
