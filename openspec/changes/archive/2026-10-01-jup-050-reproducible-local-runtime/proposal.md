JUP: JUP-050
Trello: https://trello.com/c/4VYnTkuD

## Why

Levantar el MVP en local con Docker Compose no es fiable desde cero: en frio, RabbitMQ puede morir con `eacces` (RF-096-001) y `docker compose up --wait` falla porque el processor tarda mas en migrar CockroachDB que su ventana de healthcheck. Ademas, nada dice que falta cuando `.env` esta incompleto o un puerto esta ocupado, no hay un smoke unico que pruebe el recorrido minimo y un `down`/`up` pierde el estado de RabbitMQ sin avisar. Cada validacion de PR paga este coste, y la tarjeta es P0.

## What Changes

- El healthcheck de RabbitMQ se ejecuta como el usuario `rabbitmq`, de modo que ya no puede crear un `.erlang.cookie` de root antes de que arranque el servidor (cierra RF-096-001).
- La ventana de salud del processor cubre el arranque en frio medido (~162 s hasta sano): `start_period` de unos 300 s. Se registra como finding nuevo y se cierra en este cambio.
- RabbitMQ pasa a tener volumen con nombre (`rabbitmq-data`), como CockroachDB y pgvector: `docker compose down` y `up` conservan colas y estado; solo `down -v` los borra.
- Nuevo diagnostico previo al arranque (`corepack pnpm local:doctor`): dice que variables obligatorias de `.env` faltan o no cuadran entre si, que puertos del host estan ocupados y que volumenes del proyecto existen, sin mostrar nunca valores secretos. No genera ni modifica `.env`: los secretos siguen siendo externos (JUP-053).
- Nuevo smoke unico del recorrido minimo (`corepack pnpm local:smoke`): health de cada servicio, login demo, ingesta de costes Azure simulados, resumen de costes con datos y un job de ingesta de documento publicado en RabbitMQ y completado por el processor.
- Prueba de parada y reinicio: tras `down` y `up` los datos de CockroachDB, pgvector y RabbitMQ siguen ahi.
- RF-090-001 se cierra con un control positivo: un `pnpm-lock.yaml` desincronizado hace fallar el build del frontend.
- README: recorrido desde clon limpio (copiar `.env.example`, rellenar secretos, `local:doctor`, `up --wait`, `local:smoke`) y que se conserva o se pierde en cada forma de parar.

## Capabilities

### New Capabilities
- `local-runtime-operations`: diagnostico previo al arranque, smoke unico del recorrido minimo y comportamiento documentado de parada y reinicio del entorno local.

### Modified Capabilities
- `containerized-runtime`: el healthcheck de RabbitMQ no puede alterar la propiedad de su estado; la ventana de salud cubre el arranque en frio medido; RabbitMQ conserva su estado en un volumen con nombre.

## Impact

- `docker-compose.yml` (healthcheck y volumen de RabbitMQ, `start_period` del processor) y `tools/docker-topology.test.mjs`.
- Nuevos `tools/local-doctor.mjs` y `tools/local-smoke.mjs` con sus tests, y scripts en `package.json`. Node sin dependencias nuevas.
- `README.md`, `docs/architecture.md` si cambia la topologia descrita, `openspec/findings/backlog.md` (RF-096-001, RF-090-001 y el finding nuevo del processor).
- Instalaciones existentes: el primer `up` tras el cambio crea `rabbitmq-data` vacio; lo que hubiera en el volumen anonimo anterior no se migra (se documenta).
- Sin cambios en codigo de producto de backend, processor ni frontend. Fuera de alcance: RF-044-002, RF-085-002, RF-093-001, RF-096-004 y el timeout de la fixture de billing (JUP-054).
