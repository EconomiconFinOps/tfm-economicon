## 1. Topologia de Compose

- [ ] 1.1 RED: en `tools/docker-topology.test.mjs`, exigir el healthcheck de RabbitMQ con `gosu rabbitmq`, el volumen `rabbitmq-data` montado en `/var/lib/rabbitmq` con `hostname` fijo, cinco volumenes con nombre y `start_period` del processor de al menos 300 s; comprobar que fallan.
- [ ] 1.2 GREEN: aplicar los cambios en `docker-compose.yml` y pasar `node --test tools/docker-topology.test.mjs`.
- [ ] 1.3 Reproducir RF-096-001 antes y despues: arrancar solo RabbitMQ en un proyecto aislado y lanzar el healthcheck en el acto; con el cambio, el servidor arranca y `.erlang.cookie` pertenece a `rabbitmq`.
- [ ] 1.4 Comprobar que pasa si `RABBITMQ_ERLANG_COOKIE` no coincide con el cookie guardado en `rabbitmq-data`, y documentarlo.

## 2. Diagnostico previo (`local:doctor`)

- [ ] 2.1 RED: tests de `tools/local-doctor.test.mjs` para cada escenario de la spec: `.env` ausente (no se crea), copia de `.env.example`, credenciales que no coinciden, password con `@`, `:` y `%` codificada que si coincide, entorno del proceso que gana a `.env`, puerto ocupado por un servidor real, puerto del propio proyecto, instalacion existente, y ningun valor secreto en stdout ni stderr con secretos centinela.
- [ ] 2.2 GREEN: implementar `tools/local-doctor.mjs` y el script `local:doctor` en `package.json`.
- [ ] 2.3 Mutantes: quitar la decodificacion de URL, invertir la precedencia del entorno e imprimir un valor en un mensaje; cada uno debe hacer fallar algun test.

## 3. Smoke del recorrido minimo (`local:smoke`)

- [ ] 3.1 RED: tests de `tools/local-smoke.test.mjs` con un backend HTTP simulado y un `docker compose` simulado: orden de los pasos, paso fallido nombrado, espera acotada, seed demo desactivado, sin password ni token en la salida.
- [ ] 3.2 GREEN: implementar `tools/local-smoke.mjs` y el script `local:smoke`.
- [ ] 3.3 Ejecutar el smoke dos veces seguidas contra un stack real recien levantado.
- [ ] 3.4 Control negativo: con el processor parado, el smoke falla en el paso del processor dentro de su espera.

## 4. Parada, reinicio y build bloqueado

- [ ] 4.1 Arranque en frio con volumenes nuevos: `docker compose up --build --wait` correcto a la primera; registrar la duracion.
- [ ] 4.2 `down` y `up --wait`: los datos siguen y el smoke vuelve a pasar.
- [ ] 4.3 Publicar un job con el processor parado, hacer `down` y `up`, y comprobar que el processor lo completa.
- [ ] 4.4 `down -v`: el diagnostico informa de instalacion nueva.
- [ ] 4.5 Control positivo de RF-090-001: un `pnpm-lock.yaml` desincronizado hace fallar el build del frontend.

## 5. Documentacion y findings

- [ ] 5.1 README: recorrido desde clon limpio (copiar `.env.example`, rellenar secretos y opt-ins, `local:doctor`, `up --build --wait`, `local:smoke`), duracion esperada del primer arranque y que conserva o borra cada forma de parar.
- [ ] 5.2 `docs/architecture.md` si describe volumenes o healthchecks afectados.
- [ ] 5.3 `openspec/findings/backlog.md`: cerrar RF-096-001 y RF-090-001 con su evidencia; registrar y cerrar el finding de la ventana de salud del processor.

## 6. Cierre y verificacion

- [ ] 6.1 Bateria completa: `corepack pnpm test` de las herramientas tocadas, `docker:validate`, `ci:check:test`, `openspec:validate`, `jup:check -- --change jup-050-reproducible-local-runtime` y `jup:cleanup:check`; registrar comandos y resultados.
- [ ] 6.2 Revision adversarial con el agente `adversarial-reviewer` hasta veredicto `accept`, o findings restantes aceptados explicitamente por Lucia.
- [ ] 6.3 `review.md` con resumen, decisiones, validacion, pasadas adversariales, barrido de patrones, riesgos, findings y aplicabilidad de ADR.
- [ ] 6.4 `docs/evidence/JUP-050-validation.md` con los arranques, el smoke, la parada y reinicio y los controles.
- [ ] 6.5 Bloque `## Human Approval` en `review.md` tras la aprobacion explicita de Lucia.
- [ ] 6.6 Archivar el change en la misma rama.
- [ ] 6.7 Abrir el PR hacia `develop`.
