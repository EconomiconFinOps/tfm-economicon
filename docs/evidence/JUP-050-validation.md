# Evidencia de validacion JUP-050

- Fecha: 2026-10-01.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `feat/JUP-050-reproducible-local-runtime` hacia `develop` (base `1e897dc`).
- Tarjeta: https://trello.com/c/4VYnTkuD.
- Change: [`jup-050-reproducible-local-runtime`](../../openspec/changes/jup-050-reproducible-local-runtime/proposal.md).
- Liderazgo: Lucia Mateo; pairing: Paris Arcos Martin; revision de PR: Victor Mendez; validacion, pruebas y documentacion: Alejandro Aguado.
- Entorno: Windows 10 con Git Bash, Docker Desktop (Engine 29.7.2), Node.js 24.

## Alcance

- `docker-compose.yml`: healthcheck de RabbitMQ como usuario `rabbitmq`, volumen `rabbitmq-data` con `hostname` fijo y `start_period` de 300 s en el processor.
- `local:doctor` (`tools/local-doctor.mjs`): diagnostico previo de `.env`, puertos y volumenes, sin mostrar valores.
- `local:smoke` (`tools/local-smoke.mjs`): smoke unico del recorrido minimo.
- README y arquitectura; findings RF-090-001 (cerrado) y RF-050-001 (registrado y cerrado).

## Tests

| Comando | Resultado |
|---|---|
| `corepack pnpm local:test` | 69 passed (doctor y smoke; 61 antes de las pasadas adversariales 2 y 3) |
| `corepack pnpm docker:validate` | 30 passed |
| `corepack pnpm ci:check:test` | 8 passed (incluye `local:test` en el job "OpenSpec") |
| Resto del job "OpenSpec" (`pr:check:test`, `repository:governance:test`, `jup:check:test`, `jup:cleanup:test`, `roadmap:test`, `llm-gateway:test`, `assistant-corpus:test`, `validation-questions:test`, validaciones y `openspec:validate`) | todos correctos; `openspec:validate` 36/36 |
| Bateria final de cierre (2026-10-01): `jup:check -- --change jup-050-reproducible-local-runtime`, `jup:cleanup:check`, `jup:check:test` (7), `jup:cleanup:test` (6), `openspec:validate` (36/36) y los tres grupos anteriores | todos con salida 0 |

Cada grupo se escribio primero en rojo (doctor: 17 fallos sobre un esqueleto vacio; smoke: 12; topologia: 4) y despues se implemento. Mutantes, todos detectados por algun test: sin decodificar las URL, precedencia del entorno invertida, un valor en un mensaje, sin la sonda de loopback o de IPv6, sin excluir los puertos del propio proyecto, sin comentario en linea, opt-in o entorno sin distinguir mayusculas, sin guarda de `@`, `$$` sin escapar, `${VAR-x}` como `${VAR:-x}`, longitud en UTF-16, placeholders sensibles a mayusculas, sin relajar en `test`, opciones repetidas en la DSN, sin guarda UUID, sin bearer, resumen vacio aceptado, job `failed` sin cortar, sin chequeo del seed, motivo de error crudo, y `start_period` de 299 s.

## RF-096-001: RabbitMQ `eacces`

Proyecto aislado con solo RabbitMQ y volumen nuevo; el ping se lanza en el acto, como el primer healthcheck:

| Configuracion | Resultado en 3 arranques |
|---|---|
| Antes: `rabbitmq-diagnostics -q ping` como root | 3/3 el contenedor sale con codigo 1 y 9 lineas `eacces` en el log |
| Despues: `gosu rabbitmq rabbitmq-diagnostics -q ping` | 3/3 `running`, sin `eacces`, `.erlang.cookie` de `999:999` |

Con un volumen existente y otro valor en `RABBITMQ_ERLANG_COOKIE`, RabbitMQ arranca sano y registra "Overriding Erlang cookie using the value set in the environment": el valor del entorno prevalece sobre el guardado en `rabbitmq-data`.

La fila de RF-096-001 en el backlog llega con el PR #51 (JUP-096), aun sin integrar; se cerrara con esta evidencia al traer `develop` a la rama.

## Stack completo en un proyecto aislado

Proyecto `jup050e2e` con puertos propios y volumenes nuevos; secretos del `.env` local (no se muestran) y usuario demo activado por variables de entorno con una password aleatoria que no se imprimio.

| Prueba | Resultado |
|---|---|
| `local:doctor` antes de arrancar | `[OK]`, instalacion nueva |
| `docker compose up --build --wait` en frio (build incluido) | Exito al primer intento en 489 s; los nueve servicios arriba y sanos (Grafana sin healthcheck) |
| `local:doctor` con el stack en marcha | `[OK]`: los puertos del propio proyecto no cuentan como ocupados |
| `local:smoke` dos veces seguidas | 5/5 pasos en ambas, 8 s cada una |
| Control negativo: `docker compose stop processor` y `local:smoke` | Falla en el paso 1 nombrando `processor` a los 62 s (espera acotada de 60 s) |
| Job publicado con el processor parado (`202`, 1 mensaje en `processor:jobs`), `down` y `up --wait` | Los cinco volumenes siguen tras `down`; `up` en 106 s; el job pasa a `completed` tras el reinicio |
| Datos tras el reinicio | 3 jobs, 1 usuario, 38 registros de costes en CockroachDB y 4 chunks en pgvector; `local:smoke` vuelve a pasar |
| `down -v` | No queda ningun volumen del proyecto; `local:doctor` informa de instalacion nueva |
| Tras las correcciones de la revision adversarial: `down -v`, `up --build --wait` y `local:smoke` con `DEMO_SEED_ENABLED=yes` | Arranque en frio en 334 s a la primera; `local:doctor` `[OK]`; smoke 5/5 con la consulta de `jobs` en la base de `DATABASE_URL` |

## RF-090-001: build del frontend con lockfile

Contexto temporal con `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml` y el `package.json` y `Dockerfile` del frontend:

| Contexto | Resultado |
|---|---|
| Sin cambios (control) | `pnpm install --frozen-lockfile` termina; el build falla despues en `vite build` solo porque el contexto minimo no incluye las fuentes |
| `apps/frontend/package.json` con una dependencia que no esta en el lockfile | Falla en la instalacion con `ERR_PNPM_OUTDATED_LOCKFILE` |

## Limites

- Medidas en un solo host Windows con Docker Desktop; la duracion del primer arranque depende de la maquina y la cache de imagenes.
- El tiempo hasta sano del processor no se aislo del arranque total; `start_period` de 300 s cubre los ~160 s medidos en la exploracion del 2026-09-29.
- El smoke escribe datos de prueba en `tenant-core` del stack contra el que se ejecuta.
- No se ha probado en Linux ni macOS: los tests de puertos usan servidores reales y se ejecutan en la CI (Ubuntu).
