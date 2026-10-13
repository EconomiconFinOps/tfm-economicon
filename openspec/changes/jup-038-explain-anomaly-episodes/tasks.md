Cada grupo con código sigue el ciclo Red (prueba que falla por el motivo esperado), Green (mínimo de
producto) y mutación, y termina con un punto de parada para el commit. Las pruebas de Python se
ejecutan en un contenedor equivalente a CI (`python:3.12`), porque en Windows fallan pruebas ajenas
del backend (`RF-105-004`). Los grupos 1 y 9 son solo de documentación y no llevan ciclo Red/Green.

Todas las pruebas nuevas van en archivos nuevos: no se edita ningún archivo de pruebas ya
commiteado. Las tareas Red de un grupo se escriben seguidas y se confirman juntas, en un único
commit Red, antes del Green; los casos que pida la mutación van en otro archivo nuevo.

## 1. Preparación y contrato (antes de tocar producto)

- [x] 1.1 Comprobar `origin/develop`, fijar el SHA base y abrir `docs/evidence/JUP-038-validation.md`
  con fecha, rama, SHA base, enlace a Trello y los cinco criterios de la tarjeta.
- [x] 1.2 Redactar `docs/api/anomaly-explanations.md`: petición con `anomaly_query`, respuestas 201,
  404, 409 y 422, campos de `anomaly_evidence` (decisión 7 del `design.md`), fórmulas de la
  decisión 4 y correspondencia con el resultado común de herramientas. Incluir un ejemplo calculado
  a mano con la serie del contrato de episodios (400.00 de referencia, 550.00 y 650.00 observados,
  inicio el 2026-09-08): servirá de resultado esperado independiente para las pruebas.
- [x] 1.3 Añadir a `docs/adr/ADR-0020-cost-anomaly-episodes.md` la nota fechada de la decisión 11
  (JUP-038 entrega el explicador sin herramienta registrada; el punto 11 se aplaza con `RF-114-001`
  abierto y su motivo), sin cambiar el estado ni el texto de la decisión.

## 2. Explicador (backend, sin base de datos)

- [x] 2.1 Red, `apps/backend/tests/test_anomaly_explanations.py`: con la fotografía del ejemplo de
  1.2, el texto dice día de apertura, referencia, observado, subida absoluta y relativa, las dos
  condiciones con los umbrales de las `rules` del episodio y la versión; las cifras salen de los
  operandos exactos; los dos bordes de redondeo del día de apertura añaden la nota y aparecen en
  `rounding_notes`.
- [x] 2.2 Red: impacto acumulado, días y último día; criticidad con su tramo y los bordes 499.996
  (P3) y 2000.004 (P1); cada estado con las palabras del panel; «se sigue observando» y «ya no se
  observa desde»; cierre con fecha y motivo; anomalía anterior; USD sin conversión.
- [x] 2.3 Red: causa no establecida y limitaciones en español, una por cada entrada de
  `LIMITATIONS`; aviso de datos sintéticos solo cuando la marca es cierta; línea de alcance (día de
  apertura y acumulados); servicio `null`; servicio y motivo de cierre hostiles (salto de línea,
  comillas, caracteres invisibles y una frase con aspecto de respuesta) en una sola línea y
  escapados.
- [x] 2.4 Red: forma completa de la evidencia; el `id` cumple su formato, no cambia con
  `explained_at`, cambia con el cliente y con cualquier campo del episodio u operando; versión de
  reglas desconocida, `rules` distintas de las de la versión y operandos que no cumplen `triggers`
  lanzan `ExplanationUnavailable` sin devolver texto.
- [x] 2.5 Green: `app/services/anomaly_explanations.py` (explicador puro, decisiones 2, 4, 5, 6 y 7),
  sin modificar `anomaly_episodes.py` ni `ownership_questions.py`. El esquema de la selección
  (`app/schemas/anomaly_explanations.py`) pasa a la 4.6: no tiene pruebas hasta la 4.1.
- [x] 2.6 Mutación sobre el explicador (invertir comparaciones, cambiar el redondeo, quitar la nota
  de redondeo, quitar el cliente o un campo de la huella, saltarse la comprobación de versión o de
  `triggers`, quitar el entrecomillado) y cubrir los mutantes que sobrevivan.

## 3. Lectura del episodio con operandos exactos

- [x] 3.1 Red, prueba opt-in con CockroachDB real en un archivo nuevo que reutiliza
  `anomaly_episode_support.py`: tras cargar una serie y detectar, `fetch_anomaly_episode_snapshot`
  devuelve el mismo episodio que `fetch_anomaly_episode`, los tres operandos exactos y la marca de
  datos sintéticos (falsa, y cierta con una ingesta marcada); devuelve `None` para otro cliente y
  para un identificador inexistente; no cambia episodios ni la marca de agua.
- [x] 3.2 Green: método `fetch_anomaly_episode_snapshot` en `app/db/database.py`, en una sola
  sentencia SQL filtrada por cliente (decisión 3).
- [x] 3.3 Ejecutar 3.1 contra un CockroachDB desechable y anotar en la evidencia el comando, el
  resultado y que CI la omite (`RF-096-004`).

## 4. Ruta del asistente

- [x] 4.1 Red, en un archivo nuevo `apps/backend/tests/test_anomaly_explanation_api.py`, esquema:
  `anomaly_query` con identificador de otro formato, con campos adicionales (incluidos `tenant_id` y
  `user_id`) o junto con `ownership_query` da 422; un mensaje sin `anomaly_query` sigue validando
  igual que hoy.
- [x] 4.2 Red, ruta en SQLite con autenticación y mensajes reales y un doble de
  `fetch_anomaly_episode_snapshot`: 201 con los dos mensajes guardados, `anomaly_query` en los
  metadatos del usuario, `anomaly_evidence` en los del asistente y `retrieved_context` vacío; el
  doble recibe el cliente de la sesión; no se llama al proveedor de embeddings ni al almacén
  vectorial; `assistant_queries_total` sube en uno.
- [x] 4.3 Red, fallos: fotografía `None` da `404 anomaly_episode_not_found`; `ExplanationUnavailable`
  da `409 anomaly_explanation_unavailable`; conversación de otro usuario o cliente da el 404 de
  conversación sin llamar al doble; en todos, y en los 422 de 4.1, la conversación queda sin
  mensajes nuevos.
- [x] 4.4 Red: al reabrir una conversación con una pregunta documental, una consulta de propiedad y
  una explicación, cada mensaje conserva su evidencia; con un servicio y un motivo reconocibles, los
  registros capturados no los contienen.
- [x] 4.5 Red, prueba opt-in con CockroachDB real en otro archivo nuevo, de extremo a extremo: cargar
  una serie, detectar, explicar por HTTP y comprobar las cifras frente al ejemplo de 1.2; un usuario
  de otro cliente recibe 404 con el mismo identificador; explicar dos veces da el mismo `id`; tras
  una nueva detección que suma impacto, el `id` cambia y el mensaje anterior no. Se ejecuta contra un
  CockroachDB desechable y se anota que CI la omite (`RF-096-004`).
- [x] 4.6 Green: esquema de la selección `app/schemas/anomaly_explanations.py`, campo `anomaly_query` y
  validador de exclusión en `app/schemas/assistant.py`, y rama nueva en `app/api/routes/assistant.py`
  con el orden de la decisión 8.
- [x] 4.7 Mutación sobre la rama de la ruta y el validador (quitar la exclusión, escribir antes de
  explicar, cambiar los códigos, pasar un cliente distinto del de la sesión) y cubrir los mutantes
  que sobrevivan.
- [x] 4.8 Ejecutar la suite completa del backend y comprobar que las pruebas de
  `test_ownership_questions.py` y de la rama documental pasan sin editarlas. Si alguna falla, parar.

## 5. Frontend: contrato y bloque de evidencia

- [x] 5.1 Red: tipo y validador de `anomaly_evidence` en `services/contracts.ts` (acepta la evidencia
  del ejemplo de 1.2; rechaza otra `schema_version` o `adapter_version`, un `id` con otro formato e
  importes mal formados) y `AnomalyEvidence.test.tsx` (muestra identificador, fecha de la
  fotografía, cifras de apertura, impacto, criticidad, estado, reglas, limitaciones y aviso de datos
  sintéticos; con una evidencia irreconocible dice que no está disponible y no muestra cifras).
- [x] 5.2 Red, en un archivo nuevo `AnswerEvidence.anomaly.test.tsx`: `AnswerEvidence` muestra el
  bloque nuevo cuando los metadatos traen `anomaly_evidence`. Las pruebas existentes de citas y de
  `cost_evidence` (`AnswerEvidence.test.tsx`, `CostEvidence.test.tsx`) deben seguir pasando sin
  editarlas.
- [x] 5.3 Green: `AnomalyEvidence.tsx`, tipos y validador, y la rama en `AnswerEvidence.tsx`.
- [x] 5.4 Mutación sobre el validador y el componente; cubrir los mutantes que sobrevivan.

## 6. Frontend: modo «Explicar una anomalía» del redactor

- [x] 6.1 Red, en un archivo nuevo `apps/frontend/tests/anomaly-explanation-conversations.test.tsx`
  (las pruebas de `tests/ownership-conversations.test.tsx` deben seguir pasando sin editarlas): con
  el modo activo se cargan las anomalías del cliente y se listan con servicio,
  moneda, día de inicio, criticidad y estado; elegir una y enviar manda `content` y
  `anomaly_query.episode_id`, sin `ownership_query`; sin anomalía elegida no se envía; la pregunta
  vacía recibe el texto propuesto y se puede cambiar.
- [x] 6.2 Red: cliente sin anomalías (mensaje y envío bloqueado), fallo al cargar la lista (error y
  envío bloqueado), exclusión con «Consultar costes por propiedad» en los dos sentidos, y error 404
  o 409 del backend (se muestra, se conserva la pregunta y no aparece ninguna respuesta).
- [x] 6.3 Green: `AnomalyExplanationFields.tsx` y la segunda casilla en `MessageComposer.tsx`
  (decisión 9), sin cambiar la casilla existente ni sus pruebas.
- [x] 6.4 Red, en otro archivo nuevo (el de 6.1 ya está commiteado): `/assistant?episode=<id>` abre el modo con esa anomalía elegida cuando está en la
  lista del cliente activo; si no está, lo avisa y no elige ninguna; tras un envío correcto el
  parámetro desaparece de la dirección; al cambiar de cliente con el parámetro puesto se aplica el
  caso «no está».
- [x] 6.5 Green: lectura del parámetro en `ConversationsPage.tsx` y preselección en el redactor
  (decisión 10).
- [x] 6.6 Mutación sobre el modo del redactor y la preselección; cubrir los mutantes que sobrevivan.

## 7. Frontend: enlace del panel y textos

- [x] 7.1 Red, en un archivo nuevo `AnomaliesPanel.explain-link.test.tsx`: el detalle de una anomalía
  abierta y el de una cerrada ofrecen el enlace «Explicar en el asistente» hacia
  `/assistant?episode=<id>` con el identificador codificado; abrir el detalle y tener el enlace a la
  vista no añade ninguna petición al backend. `AnomaliesPanel.test.tsx` debe seguir pasando sin
  editarlo.
- [x] 7.2 Green: enlace en el detalle de `AnomaliesPanel.tsx`.
- [x] 7.3 Comprobar que `tests/spanish-ui.test.ts` recorre los componentes nuevos y pasa sin editarlo
  (su lista es de frases en inglés ya traducidas, no de textos nuevos) y, si aparece un término que
  no esté, añadirlo a `apps/frontend/GLOSARIO.md`.
- [x] 7.4 Ejecutar la suite completa del frontend, `typecheck`, `lint` y `build`, con una ejecución
  de control sobre la base de 1.1 antes de atribuir un fallo al cambio.

## 8. Validación con el stack real

- [x] 8.1 Levantar un proyecto de Compose aislado con volúmenes nuevos, cargar el conjunto sintético
  de JUP-107 (`scripts/synthetic_anomalies.py`), pulsar «Detectar ahora» y explicar en el navegador
  las tres anomalías (P1, P2 y P3) entrando por el enlace del panel. Comparar referencia, impacto,
  días y criticidad con `docs/demo/JUP-107/esperados-anomalias.json` y guardar capturas a 1280 y
  390 px.
- [x] 8.2 Recalcular a mano una de las evidencias guardadas, con un script independiente del
  backend: cifras a partir de `operands` e `id` a partir del JSON canónico. Anotar el script y el
  resultado.
- [x] 8.3 Comprobar por HTTP: identificador de otro cliente e inexistente dan el mismo 404; la
  explicación responde con pgvector parado; tras cambiar el estado de una anomalía y explicarla de
  nuevo, el `id` cambia y el mensaje anterior se conserva; ningún registro del backend contiene un
  nombre de servicio.
- [x] 8.4 Comprobar con `git merge-tree` la rama contra las cabeceras de las PR #120 y #121 y anotar
  los archivos en conflicto para quien integre después. No se resuelve aquí.

## 9. Documentación

- [x] 9.1 Completar `docs/api/anomaly-explanations.md` con un ejemplo real de 8.1 y actualizar las
  secciones «Consumo por JUP-038» de `docs/api/anomaly-episodes.md` y `docs/api/cost-anomalies.md`
  para que enlacen con él.
- [x] 9.2 `docs/architecture/finops-agent-tools.md` (la herramienta no la implementa JUP-038; existe
  el explicador que deberá usar) y `docs/architecture.md` (tercera rama del chat síncrono).
- [x] 9.3 `apps/backend/README.md` (campo `anomaly_query` y sus errores) y `apps/frontend/README.md`
  (filas de `/assistant` y `/anomalies`).
- [x] 9.4 `docs/demo/JUP-107/anomalias.md`: paso opcional para pedir la explicación de Compute desde
  el detalle, con lo que se debe ver. El guion de tres minutos no cambia.
- [x] 9.5 `openspec/findings/backlog.md`: actualizar `RF-114-001` con la decisión de aplazarlo (sigue
  `Open`) y registrar como `RF-038-NNN` lo que quede fuera, al menos la herramienta del agente
  pendiente de JUP-035, el par de mensajes no atómico si no está ya registrado y lo que aparezca en
  la validación.
- [ ] 9.6 Actualizar `docs/continuidad/deteccion-anomalias-coste.md` con un apartado de JUP-038 y su
  fila en `docs/continuidad/README.md`.
- [ ] 9.7 `docs/testing/critical-flows.md`: suites nuevas y qué queda opt-in.

## 10. Verificación y cierre

- [ ] 10.1 Ejecutar las suites completas de backend y frontend y anotar aprobadas, fallidas y
  omitidas frente a la base de 1.1.
- [ ] 10.2 Comprobar con `git diff --stat` contra la base que el producto cambiado se limita a los
  archivos del `proposal.md` y que no cambian migraciones, dependencias, CI, processor ni el corpus
  del asistente.
- [ ] 10.3 Ejecutar `corepack pnpm lint`, `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-038-explain-anomaly-episodes` y
  `corepack pnpm jup:cleanup:check`.
- [ ] 10.4 Escribir `review.md` con la evidencia Red, Green y de mutación de cada grupo, y cerrar
  `docs/evidence/JUP-038-validation.md` con un apartado por criterio de la tarjeta y lo no validado.
- [ ] 10.5 Comprobar `origin/develop` otra vez; si hay commits que tocan los archivos de producto de
  este cambio, integrarlos y repetir 10.1.
- [ ] 10.6 Registrar la aprobación posterior a la revisión, archivar el change en la rama y preparar
  la PR contra `develop` desde `feat/JUP-038-explain-anomaly-episodes` con los cuatro roles de la
  tarjeta.
