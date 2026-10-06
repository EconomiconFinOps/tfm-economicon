## 1. Línea base antes de levantar nada

- [x] 1.1 Crear `docs/evidence/JUP-104-validation.md` con la cabecera (fecha, enlace a Trello, rama,
  commit base de `develop`) y el entorno de la máquina de validación: sistema operativo, versiones
  de Node, Docker y Docker Compose, y `corepack pnpm exec pnpm --version`.
- [x] 1.2 Comparar `.env` con `.env.example` **solo por nombres de variable** y anotar cuáles faltan
  y qué valor por defecto les da Compose. Anotar el valor de las variables no secretas que fijan el
  modo (`RUNTIME_ENVIRONMENT`, `EMBEDDING_PROVIDER`, `EMBEDDING_DIMENSION`, `LLM_PROVIDER`,
  `DEMO_SEED_ENABLED`) y, de las secretas, únicamente si están definidas.
- [x] 1.3 Ejecutar `corepack pnpm local:test` con la infraestructura de Compose parada y guardar el
  recuento. Se hace ahora porque falla con CockroachDB, RabbitMQ o pgvector levantados.
- [x] 1.4 Comprobar con `docker ps` que el proyecto Compose por defecto no está levantado. Si lo
  está, pararlo sin borrar volúmenes y anotarlo. Hecho con Docker Desktop arrancado: el proyecto
  existe pero está parado y los puertos están libres; no hizo falta pararlo.

## 2. Stack local aislado

- [x] 2.1 Con `COMPOSE_PROJECT_NAME=jup104-e2e` definido en la consola, ejecutar
  `corepack pnpm local:doctor` y guardar la salida. Debe informar de una instalación nueva, sin
  volúmenes previos.
- [x] 2.2 En la misma consola, `docker compose up --build --wait` y registrar el estado de cada
  servicio con `docker compose ps` y el commit desde el que se construyeron las imágenes.
- [x] 2.3 Ejecutar `corepack pnpm local:smoke` **una sola vez** y guardar sus cinco pasos. A partir
  de aquí no se vuelve a ejecutar: cada ejecución añade un fragmento al corpus de `tenant-core`.
- [x] 2.4 Registrar el proveedor de embeddings que el backend declara al arrancar y la dimensión de
  la columna de vectores en pgvector. Criterio: `mock` y 8, como fija la decisión 1 del `design.md`.

## 3. Guion de navegador

- [ ] 3.1 Preparar, fuera del repositorio, un proyecto con Playwright y Chromium, y anotar sus
  versiones. Comprobar con `git status` que no deja nada dentro del repositorio.
- [ ] 3.2 Escribir el guion según la decisión 4 del `design.md`: Chromium sin opciones que relajen la
  seguridad, perfil vacío, sin interceptar ni responder peticiones, entrada por el formulario de
  acceso, contraseña leída de una variable de entorno y esperas por condición. Debe fallar si
  aparece un error de página no previsto.
- [ ] 3.3 Versionar el guion como receta en `docs/evidence/JUP-104-browser-recipe.md`, con cómo
  ejecutarlo y qué variables necesita, sin ningún valor secreto.

## 4. Recorrido: acceso, ámbito y costes

- [ ] 4.1 Acceso con la cuenta de demostración desde `/login`. Registrar que la sesión se crea, que
  aparece el armazón con el selector de ámbito y que no hay errores de CORS en la consola.
- [ ] 4.2 Con Core Finance, fijar en `/` el periodo `2024-06-01` a `2024-06-21` y registrar el total,
  la moneda y el número de grupos que muestra la sección de costes reales. Contrastar el total con
  la respuesta de `GET /billing/summary` para ese ámbito y periodo.
- [ ] 4.3 Cambiar a Growth Ops con el mismo periodo y registrar que la sección muestra ausencia de
  datos; volver a Core Finance y registrar que recupera los mismos valores.
- [ ] 4.4 Abrir `/operational`, `/cuts`, `/anomalies`, `/recommendations` y `/overview-legacy` y
  completar la tabla de la evidencia: por pantalla y bloque, si los datos son del backend o de
  demostración y si la interfaz lo advierte.

## 5. Recorrido: ingesta extremo a extremo

- [ ] 5.1 Con Growth Ops, enviar desde `/ingest` el contenido íntegro de
  `docs/assistant-corpus/finops/azure-finops-mvp.md`, con origen `assistant-corpus` y la ruta del
  archivo como URI del artefacto. Registrar el identificador, el estado y la cola que muestra la
  interfaz, y el tamaño y el hash SHA-256 del archivo enviado.
- [ ] 5.2 Consultar el estado de ese trabajo en la tabla `jobs` de CockroachDB hasta `completed`, con
  un plazo de 120 s, y guardar la consulta y su salida. Si no llega, registrar el estado y los
  registros del processor y marcar la ingesta como no acreditada.
- [ ] 5.3 Consultar en pgvector la fila de `knowledge_documents` de ese trabajo y ámbito y el número
  de filas de `document_chunks` y `chunk_embeddings` asociadas, y guardar las consultas y su salida.
  Comprobar que `tenant-core` no tiene ningún fragmento de ese documento.
- [ ] 5.4 Guardar las líneas del registro del processor que corresponden a ese trabajo, sin
  contenido del documento.

## 6. Recorrido: asistente, historial y cierre

- [ ] 6.1 Con Growth Ops, crear una conversación nueva en `/assistant` y enviar la pregunta del caso
  `JUP-069-004`. Registrar el texto de la respuesta y comprobar que cada fragmento que muestra
  procede del documento ingerido en 5.1.
- [ ] 6.2 Guardar el evento `retrieval` del backend para esa pregunta y comprobar que sus
  identificadores de documento son el del trabajo de 5.1.
- [ ] 6.3 Recargar la página, volver a abrir la conversación y registrar si se muestran la pregunta y
  la respuesta. Es la comprobación de `RF-087-002`: si falla, guardar el código de respuesta y el
  registro del backend.
- [ ] 6.4 Cambiar a Core Finance, crear una conversación nueva y enviar la misma pregunta. Registrar
  la respuesta y comprobar que no contiene fragmentos del documento de 5.1.
- [ ] 6.5 Cerrar la sesión, intentar abrir `/assistant` directamente y registrar que se presenta la
  pantalla de acceso.
- [ ] 6.6 Guardar el resultado completo del guion (pasos, errores de página y versión del navegador)
  y añadir a la evidencia la tabla de pasos con su estado: acreditado, fallido o no ejecutado.

## 7. Pasada manual

- [ ] 7.1 Quien valida repite en su navegador habitual, sin extensiones que alteren la red, los
  pasos 4.1 a 4.3, 5.1 y 6.1 a 6.5 siguiendo la lista de la evidencia, y anota navegador, versión y
  resultado de cada paso. No lo puede ejecutar la herramienta de implementación.
- [ ] 7.2 Registrar cualquier diferencia entre la pasada manual y el guion.

## 8. Hallazgos y límites

- [ ] 8.1 Redactar en la evidencia cada fallo como hallazgo `RF-104-NNN` con reproducción, resultado
  esperado y observado, severidad y acción propuesta. Si no hay ninguno, decirlo.
- [ ] 8.2 Redactar en la evidencia el resultado de `RF-087-002` según la decisión 6 del `design.md`.
- [ ] 8.3 Redactar la sección "Qué no acredita esta validación": pertinencia semántica con `mock`,
  modo `litellm`, citas visibles (JUP-025), preguntas de gasto en el chat (JUP-036) y lo que haya
  quedado como no ejecutado.
- [ ] 8.4 Completar la trazabilidad: cada criterio de aceptación de la tarjeta y cada escenario de
  la spec, con la tarea y la sección de la evidencia que lo respaldan.
- [ ] 8.5 Revisar la evidencia, la receta y las salidas guardadas: ninguna contraseña, token, clave
  ni cadena de conexión.
- [ ] 8.6 Parar el proyecto con `docker compose stop`, sin borrar volúmenes, y anotarlo.

## 9. Batería del carril

- [ ] 9.1 `corepack pnpm install --frozen-lockfile` y comprobar con `git status` que no modifica
  ningún archivo versionado.
- [ ] 9.2 Desde la raíz, con `--force`: `corepack pnpm lint`, `corepack pnpm typecheck` y
  `corepack pnpm build`. Guardar el recuento de tareas.
- [ ] 9.3 Pruebas por mitades, con el entorno virtual de Python activo:
  `corepack pnpm run test "--filter=!@finops/frontend"` y
  `corepack pnpm run test --filter=@finops/frontend -- --maxWorkers=1`. Guardar los recuentos y
  decir en la evidencia por qué no se usa el comando único.
- [ ] 9.4 `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-104-e2e-validation`, `corepack pnpm jup:cleanup:check` y
  `corepack pnpm repository:governance:test`.

## 10. Archivos compartidos con JUP-103

- [ ] 10.1 Traer `develop` y comprobar que contiene JUP-103 (PR #75). Si no está fusionado, parar y
  decidir según la decisión 10 del `design.md`. Si `develop` trae cambios en el chat, la pantalla
  principal o la ingesta, reconstruir y repetir el paso afectado antes de seguir.
- [ ] 10.2 `openspec/findings/backlog.md`: actualizar la fila `RF-087-002` y añadir las filas
  `RF-104-NNN` redactadas en 8.1.
- [ ] 10.3 `docs/spikes/frontend-migration.md`: sustituir `jup-0xx-validacion-e2e` por el enlace a
  `jup-104-e2e-validation`, marcar sus tres puntos con lo realmente hecho, corregir las dos
  menciones de `operator@example.com` / `secret` (en "Hechos del destino" y en F5) y añadir el punto
  de "Próximos pasos" con el resultado.
- [ ] 10.4 Repetir 9.4 tras estos cambios y comprobar que los enlaces relativos nuevos resuelven.

## 11. Revisión

- [ ] 11.1 Escribir `review.md`: resultado, criterios de la tarjeta uno a uno, validación ejecutada,
  hallazgos, la excepción al ciclo Red/Green (decisión 8), que no aplica ADR (decisión 11) y lo que
  no se validó y por qué.
- [ ] 11.2 Completar en la evidencia la sección de pendientes y dejar los huecos del PR y de CI para
  rellenarlos al abrirlo.
