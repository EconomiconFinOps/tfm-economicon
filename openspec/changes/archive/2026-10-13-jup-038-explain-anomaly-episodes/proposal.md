JUP: JUP-038
Trello: https://trello.com/c/QzkjVY7P

## Why

El panel `/anomalies` enseña desde JUP-114 las anomalías de coste guardadas como episodios, con su
criticidad, su impacto y su estado, pero no dice con palabras por qué se marcó cada una: quien decide
si investigarla o cerrarla tiene que deducirlo de las cifras del detalle y conocer la regla de
negocio. La historia de la tarjeta pide eso mismo: «como usuario quiero que el agente explique por
qué una anomalía ha sido marcada, para tomar decisiones con contexto».

El primer intento (PR #94, cerrada sin integrar el 2026-10-10) explicaba las alertas de la consulta
de prueba de JUP-030. Ya no sirve de base: las especificaciones vigentes dicen que se explican los
episodios guardados (`cost-anomaly-detection`, escenario «Downstream explanation», y
`finops-agent-tool-contract`, escenario «Candidato persistido con reglas versionadas»), y el
contrato de episodios reserva el encargo en su sección «Consumo por JUP-038». Se empieza de nuevo
sobre `develop`, sin reutilizar esa rama ni su código.

Se hace ahora porque el PR #122 dejó la fuente integrada el 2026-10-12 y la entrega es el
2026-10-23.

## What Changes

- El asistente admite en un mensaje la selección estructurada de una anomalía guardada
  (`anomaly_query` con el identificador del episodio) y responde con una explicación determinista:
  por qué se abrió (coste observado frente a la referencia, subida absoluta y relativa, las dos
  condiciones de la regla y su versión), cuánto lleva (impacto acumulado, días contados y
  criticidad), en qué estado de seguimiento está y con qué limitaciones. No interviene ningún
  modelo generativo ni la recuperación documental, igual que en las consultas de propiedad de
  JUP-037.
- La explicación se guarda en la conversación con su evidencia: la fotografía del episodio que se
  explicó, los operandos exactos y un identificador reproducible. Un episodio que cambia después
  (más impacto, otro estado) no altera las explicaciones ya guardadas.
- La explicación presenta siempre la anomalía como candidata: sin causa establecida, sin ahorro,
  sin conversión de moneda, y avisa cuando el cliente tiene datos sintéticos de demostración.
- Las diferencias y los porcentajes salen de los valores exactos guardados, no de los importes
  redondeados de la API; cuando el redondeo deja una cifra igual al umbral, el texto lo dice.
- Los nombres de servicio y el motivo de cierre son datos del cliente: se muestran entrecomillados
  en una línea para que no puedan pasar por frases de la respuesta, y no se escriben en registros.
- Si el episodio no existe o es de otro cliente, la respuesta es el mismo 404 que en la API de
  episodios; si no se puede explicar con las reglas que conoce el explicador, 409. En ningún caso
  se guarda un mensaje.
- El explicador es una función aparte, sin dependencias de la ruta ni de HTTP, para que la futura
  herramienta `detect_cost_anomaly_candidates` del agente (JUP-035) dé la misma explicación. **Este
  cambio no registra ninguna herramienta del agente.**
- Frontend: el redactor de mensajes de `/assistant` gana el modo «Explicar una anomalía», con la
  lista de anomalías del cliente activo; el detalle de una anomalía en `/anomalies` gana el enlace
  «Explicar en el asistente», que abre el asistente con esa anomalía ya elegida. La respuesta
  muestra su evidencia en un bloque propio.
- Documentación: contrato nuevo de la explicación, ajuste de los textos que decían que JUP-038
  implementaría la herramienta del agente y nota fechada en ADR-0020.

Decisiones de Victor (liderazgo de la tarjeta) del 2026-10-12, que fijan el alcance:

1. Se construye sobre `develop` con el patrón de JUP-037, sin depender de las PR #120 y #121
   (JUP-035, abiertas).
2. El explicador queda separado para envolverlo como herramienta cuando JUP-035 entre.
3. `RF-114-001` (aclaraciones de lo esperado, la criticidad por impacto acumulado y los estados en
   el corpus del asistente) **se aplaza y sigue abierto**. ADR-0020, punto 11, lo asignaba a
   JUP-038. Motivo: `docs/assistant-corpus/business-rules/economicon-mvp-rules.md` está fijado por
   sha256 en las evaluaciones de JUP-069, JUP-022 y JUP-070; cambiarlo obliga a regenerar esas
   huellas en cadena y a repetir la calibración y las comprobaciones de etiquetas de tres tarjetas
   ajenas, a diez días de la entrega. La explicación de este cambio no depende del corpus.
4. Punto de entrada: enlace desde el panel más selección en el asistente.
5. Sin ADR nuevo: el patrón ya existe desde JUP-037; se añade una nota fechada a ADR-0020.

## Capabilities

### New Capabilities

- `anomaly-episode-explanation`: explicación determinista y con evidencia guardada de un episodio de
  anomalía, pedida desde una conversación del asistente; cubre la selección autorizada, el contenido
  de la explicación, sus límites, la evidencia y su presentación en el asistente.

### Modified Capabilities

- `finops-agent-tool-contract`: el requisito «Anomalias siempre candidatas y evidenciadas» añade que
  la explicación de un episodio es la de `anomaly-episode-explanation`, también cuando la pida la
  herramienta del agente, y que mientras esa herramienta no esté registrada la explicación se ofrece
  solo por selección estructurada.
- `anomalies-panel`: requisito nuevo para el enlace del detalle de una anomalía hacia su explicación
  en el asistente. Los requisitos existentes no cambian.

## Impact

- **Backend, nuevo:** `apps/backend/app/schemas/anomaly_explanations.py` (selección) y
  `apps/backend/app/services/anomaly_explanations.py` (explicador).
- **Backend, modificado:** `apps/backend/app/schemas/assistant.py` (campo `anomaly_query` y
  exclusión con `ownership_query`), `apps/backend/app/api/routes/assistant.py` (rama nueva antes de
  la recuperación documental) y `apps/backend/app/db/database.py` (lectura del episodio con sus
  operandos exactos y la marca de datos sintéticos).
- **Frontend, nuevo:** `apps/frontend/src/components/AnomalyExplanationFields.tsx` y
  `apps/frontend/src/components/AnomalyEvidence.tsx`.
- **Frontend, modificado:** `MessageComposer.tsx`, `AnswerEvidence.tsx`, `ConversationsPage.tsx`,
  `AnomaliesPanel.tsx`, `services/contracts.ts` y, si aparece un término nuevo,
  `apps/frontend/GLOSARIO.md`.
- **Pruebas:** todas en archivos nuevos de `apps/backend/tests` y `apps/frontend`; no se edita
  ningún archivo de pruebas existente.
- **Documentación, nueva:** `docs/api/anomaly-explanations.md` y `docs/evidence/JUP-038-validation.md`.
- **Documentación, modificada:** `docs/api/anomaly-episodes.md` y `docs/api/cost-anomalies.md`
  (secciones «Consumo por JUP-038»), `docs/architecture/finops-agent-tools.md`, `docs/architecture.md`,
  `docs/adr/ADR-0020-cost-anomaly-episodes.md` (nota fechada), `apps/backend/README.md`,
  `apps/frontend/README.md`, `docs/demo/JUP-107/anomalias.md` (paso opcional),
  `docs/continuidad/deteccion-anomalias-coste.md`, `docs/continuidad/README.md`,
  `docs/testing/critical-flows.md` y `openspec/findings/backlog.md`; al archivar, las tres especificaciones de arriba.
- **API:** `POST /assistant/conversations/{id}/messages` acepta el campo opcional `anomaly_query`.
  Las peticiones actuales no cambian. No hay rutas ni métodos HTTP nuevos, así que la política de
  CORS no se toca.
- **Sin cambios:** esquema de la base (sin migración), la regla diaria y los episodios, la API de
  `/billing/anomalies`, el processor, dependencias, CI, variables de entorno y el corpus del
  asistente.
- **Coordinación con JUP-035:** las PR #120 y #121 modifican `routes/assistant.py`,
  `schemas/assistant.py` y `database.py`. El cambio en esos tres archivos se mantiene mínimo (una
  rama, un campo y un método) para que el conflicto sea pequeño. Quien integre JUP-035 después
  encuentra el explicador listo para envolverlo.
- **Fuera de alcance:** herramienta registrada del agente y redacción por modelo generativo
  (JUP-035), corpus del asistente (`RF-114-001`), causa raíz, ahorro, conversión de moneda,
  ejecución periódica y avisos (JUP-115), nuevas dimensiones de episodio (`RF-114-008`), cambios en
  la regla o en los episodios, y explicación de las alertas de la consulta de prueba de JUP-030.
- **ADR:** no aplica uno nuevo (ver `design.md`, decisión 11).

## Participación

Roles de la tarjeta, comunicados por Victor el 2026-10-12. No acreditan participación realizada.

- Liderazgo: Victor Mendez
- Pairing/coautoría: Paris Arcos Martin
- Revisión de PR: Lucia Mateo
- Validación, pruebas y documentación: Alejandro Aguado

## Criterios de aceptación de la tarjeta

Copiados de Trello por Victor el 2026-10-12. La evidencia por criterio irá en
`docs/evidence/JUP-038-validation.md`.

1. Resultado funcional verificable.
2. Pruebas necesarias añadidas y en verde.
3. Documentación y decisiones actualizadas.
4. Pull request revisado y vinculado.
5. Validación funcional y evidencia enlazadas.

## Human Approval

- Change: jup-038-explain-anomaly-episodes
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-10-12
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Pairing: no consta que Paris (pairing de la tarjeta) haya visto el diseño. No se le atribuye
  ninguna participación; `Revision JUP-038` (Lucia) y `Validacion JUP-038` (Alejandro) siguen
  pendientes y no se dan por hechas.
- Scope adjustment approved: «que el agente explique» se cumple en este cambio con una explicación
  determinista dentro del asistente, sin modelo generativo y sin herramienta registrada del agente,
  que quedan para JUP-035. `RF-114-001` (corpus del asistente) se aplaza y sigue abierto, aunque
  ADR-0020, punto 11, lo asignaba a JUP-038. Conviene reflejar los dos matices en la tarjeta de
  Trello.
- Decisions approved: se aprueban las trece decisiones del `design.md`. (1) **Selección
  estructurada `anomaly_query`** en el mensaje, excluyente con `ownership_query`, sin ruta nueva.
  (2) **Explicador puro**, separado de la ruta. (3) **Lectura nueva** del episodio con operandos
  exactos y marca de datos sintéticos, en una sola sentencia. (4) **Cifras con aritmética exacta** y
  nota cuando el redondeo iguala un umbral. (5) **Solo `jup019-daily-v1`**; lo que no se sabe
  explicar da 409. (6) **Texto fijo en español** con los términos del panel y los datos del cliente
  entrecomillados. (7) **Evidencia `anomaly_evidence`** en los metadatos, con fotografía, operandos
  e identificador reproducible. (8) **Orden de la ruta**: nada se guarda ante 404, 409 o 422; sin
  registros ni métricas nuevas. (9) **Segunda casilla** en el redactor y componentes propios.
  (10) **Enlace del panel** por parámetro de dirección; el panel no hace peticiones nuevas.
  (11) **Sin ADR nuevo**; nota fechada en ADR-0020. (12) **Capacidad nueva** más dos deltas.
  (13) **Estrategia de pruebas**, con todas las pruebas en archivos nuevos.
- Constraints: el producto cambiado se limita a los archivos del apartado Impact. Sin migración, sin
  rutas ni métodos HTTP nuevos, sin dependencias, sin cambios en CI, en el processor, en la regla
  diaria, en los episodios ni en el corpus del asistente. No se modifican `anomaly_episodes.py` ni
  `ownership_questions.py`. No se edita ningún archivo de pruebas ya commiteado ni se adapta una
  prueba existente para que pase. No se escribe el nombre del servicio ni el motivo de cierre en
  registros. No se da por validado nada que no se haya ejecutado, y las pruebas opt-in no se
  presentan como cubiertas por CI.
- Main risks: (a) conflicto con las PR #120 y #121 en `routes/assistant.py`, `schemas/assistant.py`
  y `database.py`; se mide en la tarea 8.4 y no se resuelve aquí. (b) La explicación solo cubre el
  día de apertura y los acumulados, porque no hay serie diaria guardada. (c) La lectura nueva y el
  recorrido de extremo a extremo solo se prueban con CockroachDB real, fuera de CI (`RF-096-004`).
  (d) Una pregunta en texto libre sobre anomalías sigue respondiéndose con el corpus sin las
  aclaraciones de ADR-0020. (e) El par de mensajes usuario/asistente no es atómico, como en las
  otras ramas del asistente.
- Required changes before execution: ninguno en los artefactos.
- Notes: nada de lo descrito en `design.md` se ha ejecutado todavía; se leyó en el repositorio
  sobre `develop` en `bfaf3983`, que sigue siendo la cabecera de `origin/develop` al registrar esta
  aprobación. Son 51 tareas en 10 grupos, 10 requisitos y 42 escenarios en tres especificaciones.
  Durante el gate se corrigieron tres cosas en los artefactos, sin cambiar el alcance: las pruebas
  nuevas van en archivos nuevos (antes tres tareas editaban archivos de prueba ya commiteados), la
  tarea 7.3 ya no añade textos a `tests/spanish-ui.test.ts` (su lista es de frases en inglés ya
  traducidas) y `docs/testing/critical-flows.md` figura en el Impact. Comprobaciones del gate el
  2026-10-12: `corepack pnpm openspec:validate` (68 de 68),
  `corepack pnpm jup:check -- --change jup-038-explain-anomaly-episodes` y
  `corepack pnpm jup:cleanup:check`, las tres correctas.
