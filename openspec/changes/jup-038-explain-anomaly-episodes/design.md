JUP-038 — Explicar anomalías detectadas. Carril `standard`.

## Context

Motivación y alcance en `proposal.md`; requisitos en `specs/`. Aquí solo el estado que condiciona el
enfoque, leído en el repositorio el 2026-10-12 sobre `develop` en `bfaf3983` (base de la rama
`feat/JUP-038-explain-anomaly-episodes`). Nada de esta sección se ha ejecutado todavía.

**Qué guarda un episodio y qué enseña la API.** La tabla `anomaly_episodes` guarda valores exactos;
`GET /billing/anomalies/episodes/{id}` los devuelve redondeados a dos decimales
(`apps/backend/app/services/anomaly_episodes.py`, `episode_payload`).

| Guardado (exacto) | Lo que devuelve la API | Relación |
| --- | --- | --- |
| `reference_week_cost` | `reference_daily_cost` | suma de los 7 días de referencia; la API la divide entre 7 |
| `opening_observed_cost` | `opening_observed_cost` | coste del día de apertura |
| `impact_numerator` | `accumulated_impact` | impacto acumulado multiplicado por 7; la API lo divide entre 7 |
| `rules`, `rules_version` | igual | umbrales con los que se abrió y `jup019-daily-v1` |

La regla y la criticidad se evalúan sobre esos valores multiplicados por 7 para no redondear nunca
una media (`triggers` y `severity` en el mismo módulo). `Database.fetch_anomaly_episode` devuelve
solo el resultado redondeado, así que hoy ningún consumidor puede calcular la subida exacta del día
de apertura. No se guarda la serie día a día: solo el día de apertura y los acumulados.

**Cómo responde hoy el asistente.** `POST /assistant/conversations/{id}/messages`
(`apps/backend/app/api/routes/assistant.py`) tiene dos ramas: con `ownership_query` llama a
`OwnershipQuestionService`, guarda el mensaje del usuario y la respuesta con `cost_evidence` en los
metadatos y termina, sin embeddings ni generación (JUP-037); sin él, embebe la pregunta, recupera
fragmentos y responde con una plantilla. No hay modelo generativo ni registro de herramientas en el
backend. En el frontend, `MessageComposer.tsx` tiene la casilla «Consultar costes por propiedad» y
`AnswerEvidence.tsx` pinta `cost_evidence` con `CostEvidence.tsx`, que no muestra nada cuya forma no
reconozca.

**Restricciones.**

- Las PR #120 y #121 (JUP-035, abiertas) modifican `routes/assistant.py`, `schemas/assistant.py` y
  `database.py` y añaden migraciones 002 a 004, cuando `develop` ya tiene `002_anomaly_episodes.py`.
- `anomaly_episodes.py` y la API de `/billing/anomalies` son de JUP-114: este cambio los usa y no
  los modifica.
- Los nombres de servicio llegan de la ingesta y el motivo de cierre lo escribe una persona: son
  datos del cliente. JUP-037 resolvió lo mismo con `display_label`
  (`apps/backend/app/services/ownership_questions.py`).
- `append_message` hace una transacción por mensaje; el par usuario/asistente no es atómico. Es el
  comportamiento actual de las dos ramas del asistente.
- La interfaz está en español con glosario (`apps/frontend/GLOSARIO.md`) y una prueba de regresión
  de textos (`apps/frontend/tests/spanish-ui.test.ts`). El panel llama «anomalía» al episodio y usa
  «Nueva», «Investigando», «Resuelta», «Falso positivo» y «Alta (P1)», «Media (P2)», «Baja (P3)».
- Las pruebas de la API de episodios usan dobles del almacén en SQLite y una variante opt-in con
  CockroachDB real que CI omite (`RF-096-004`).
- CORS admite `GET`, `POST` y `PATCH`; el cambio solo usa rutas y métodos que ya existen.

## Goals / Non-Goals

**Goals:**

- Que la explicación se pueda reproducir a mano desde la evidencia guardada: mismas cifras, mismo
  identificador.
- Que un solo explicador sirva hoy a la ruta del asistente y mañana a la herramienta del agente, sin
  reescribirlo.
- Que el cambio en los archivos que comparte con JUP-035 quepa en una rama, un campo y un método.
- Que ninguna explicación diga más de lo que el episodio guardado permite afirmar.

**Non-Goals:**

- Registrar o anunciar una herramienta del agente, o redactar con un modelo generativo.
- Explicar la evolución día a día del episodio: no está guardada.
- Interpretar la pregunta en texto libre para adivinar a qué anomalía se refiere.
- Arreglar la falta de atomicidad del par de mensajes o los hallazgos abiertos de JUP-114.

## Decisions

### 1. Selección estructurada en el mensaje, no una ruta nueva

`MessageCreateRequest` gana `anomaly_query`, opcional, con un único campo `episode_id` que debe
cumplir `^anomaly-[0-9a-f]{64}$` (el formato de `episode_id` en `anomaly_episodes.py`) y sin campos
adicionales. Un validador del mensaje rechaza con 422 que lleguen a la vez `anomaly_query` y
`ownership_query`. El esquema de la selección vive en un archivo propio,
`app/schemas/anomaly_explanations.py`, para tocar `schemas/assistant.py` en dos líneas.

- *Alternativa: `POST /assistant/conversations/{id}/anomaly-explanations`.* Descartada: duplica la
  persistencia de mensajes, añade una ruta que JUP-035 tendría que reconciliar y se aparta del
  precedente de JUP-037 sin ganar nada.
- *Alternativa: deducir la anomalía del texto de la pregunta.* Descartada: sin modelo sería una
  búsqueda por palabras con resultados ambiguos, y el texto del usuario no debe decidir qué datos se
  leen.

### 2. Un explicador puro, separado de la ruta

`app/services/anomaly_explanations.py` expone una función que recibe la fotografía del episodio
(decisión 3), el cliente y la fecha y hora de la explicación, y devuelve el texto y la evidencia. No
abre conexiones, no lee configuración, no registra nada y no conoce FastAPI: se prueba sin base de
datos y la futura herramienta `detect_cost_anomaly_candidates` puede llamarla tal cual. Importa de
`anomaly_episodes.py` lo que ya existe (`RULES`, `RULES_VERSION`, `triggers`, `severity`, `money`) y
no modifica ese módulo.

- *Alternativa: escribir la lógica en la ruta, como la rama documental.* Descartada: es justo lo que
  la decisión de alcance 2 quiere evitar.
- *Alternativa: añadirla a `anomaly_episodes.py`.* Descartada: mezcla la detección con la redacción
  y amplía un archivo de otra tarjeta recién integrado.

### 3. Una lectura nueva que devuelve los operandos exactos

`Database.fetch_anomaly_episode_snapshot(tenant_id, episode_id)` devuelve, o `None`, tres cosas: el
episodio como lo da la API (`episode_payload`), los operandos exactos de la tabla del contexto y la
marca `includes_synthetic_data`. Es **una sola sentencia SQL** filtrada por cliente (la fila del
episodio más un `EXISTS` sobre las ingestas sintéticas completadas, el mismo criterio que usa la
lista), de modo que todo sale de la misma fotografía sin transacción explícita ni reintentos.

- *Alternativa: reutilizar `fetch_anomaly_episode`.* Descartada: solo trae importes redondeados y
  haría imposible el escenario «Cifra redondeada igual al umbral».
- *Alternativa: dos lecturas (episodio y marca sintética).* Descartada: podrían ver estados
  distintos y obligarían a decidir un nivel de aislamiento.

### 4. Cifras derivadas con aritmética exacta

Con `R` = `reference_week_cost`, `O` = `opening_observed_cost` e `I` = `impact_numerator`:

| Cifra | Cálculo | Se muestra |
| --- | --- | --- |
| Referencia diaria | `R / 7` | dos decimales, HALF_UP |
| Subida absoluta del día de apertura | `(O × 7 − R) / 7` | dos decimales, HALF_UP |
| Subida relativa | `(O × 7 − R) × 100 / R` | dos decimales, HALF_UP, con `%` |
| Impacto acumulado | `I / 7` | dos decimales, HALF_UP |

Se redondea una sola vez, al mostrar, con el mismo criterio que `money`. Cuando la cifra mostrada
coincide con el umbral con el que se compara (subida absoluta igual a `absolute_increase`, subida
relativa igual a `relative_increase_percent`, impacto igual a 500.00 con P3 o a 2000.00 con P1), el
texto añade que el valor exacto queda por encima o por debajo del umbral y que la cifra está
redondeada, y la evidencia lo anota en `rounding_notes`. Así una explicación nunca parece
contradecir la regla.

- *Alternativa: restar los importes redondeados de la API.* Descartada: 100,004 se vería como
  «100.00, que no supera 100».

### 5. Solo se explica lo que se sabe explicar

El explicador admite `rules_version == "jup019-daily-v1"` con unas `rules` guardadas iguales a las
de esa versión, y comprueba que `triggers(O, R)` es cierto. Si algo no se cumple lanza
`ExplanationUnavailable`, que la ruta convierte en `409 anomaly_explanation_unavailable` sin guardar
mensajes. Los umbrales que aparecen en el texto se leen de las `rules` del episodio, no de
constantes del explicador. Una versión futura de las reglas dará 409 hasta que se enseñe al
explicador a contarla: es deliberado.

- *Alternativa: explicar «lo que se pueda» con una advertencia.* Descartada: una explicación
  aproximada de una regla que no se conoce es justo el mensaje inventado que la tarjeta quiere
  evitar.

### 6. Texto fijo en español, con los términos del panel

La respuesta es una lista de líneas con plantilla fija, en este orden: identificación (servicio
entrecomillado y moneda), por qué se marcó, regla y versión, impacto y criticidad, seguimiento,
causa no establecida, limitaciones, aviso de datos sintéticos cuando proceda, alcance de la
explicación (día de apertura y acumulados; sin detalle día a día), fecha y hora de la fotografía e
identificador de la evidencia. Los estados y criticidades usan las mismas palabras que el panel.
Importes con punto decimal y fechas ISO, como las respuestas de JUP-037.

El servicio y el motivo de cierre pasan por `display_label`, importado de
`ownership_questions.py`; un servicio `null` se escribe «sin servicio informado».

Las limitaciones del episodio están en inglés en la API (valores de la API, que JUP-117 dejó sin
traducir). El explicador lleva su redacción en español para la versión `jup019-daily-v1`, una por
cada limitación del episodio, y una prueba falla si el número deja de coincidir con `LIMITATIONS`.
La lista original en inglés se conserva dentro de la fotografía del episodio.

- *Alternativa: copiar las limitaciones en inglés en un texto en español.* Descartada: la respuesta
  la lee la persona que decide.
- *Alternativa: mover `display_label` a un módulo común.* Descartada por ahora: obliga a tocar el
  archivo de JUP-037 y sus pruebas para ahorrar un `import`.

### 7. Evidencia `anomaly_evidence` en los metadatos del mensaje

El mensaje del asistente se guarda con `metadata = {"citations": [], "anomaly_evidence": {...}}` y
el del usuario con `metadata = {"anomaly_query": {"episode_id": ...}}`. Sin migración.

| Campo | Contenido |
| --- | --- |
| `schema_version`, `adapter_version` | `"1.0"` y `"anomaly-explanation-1.0"` |
| `id` | `anomaly-explanation:` + sha256 |
| `status` | `"ok"` |
| `source` | `kind: "anomaly_episodes"`, `rules_version`, `data_as_of` (= `impact_through_date`) |
| `episode` | el episodio tal como lo devuelve la API en ese momento |
| `operands` | `reference_seven_day_total`, `opening_observed_cost` e `accumulated_impact_times_seven`, como cadenas decimales exactas |
| `opening` | referencia diaria, observado, subida absoluta y relativa, umbrales y `conditions_met: true` |
| `impact` | impacto acumulado, días, último día, criticidad y tramo |
| `rounding_notes` | lista de las cifras a las que se aplicó la nota de redondeo |
| `includes_synthetic_data` | booleano |
| `cause_status` | `"not_established"` |
| `assumptions`, `limitations` | lista vacía y limitaciones en español |
| `explained_at` | fecha y hora UTC de la explicación |

El `id` es el sha256 del JSON canónico (claves ordenadas, sin espacios) de todo lo anterior más el
cliente y menos `explained_at`, igual que `cost_evidence` deja fuera `queried_at`: el mismo estado
da el mismo identificador y cualquier cambio del episodio da otro. Los nombres `status`, `source`,
`assumptions` y `limitations` son los del resultado común de herramientas
(`docs/architecture/finops-agent-tools.md`); quien registre la herramienta solo añade
`correlation_id` y pone el `id` en `evidence_ids`. La correspondencia se documenta en
`docs/api/anomaly-explanations.md`.

- *Alternativa: guardar solo el identificador del episodio y releerlo al mostrar.* Descartada: el
  episodio cambia y la explicación guardada dejaría de corresponder a lo que se dijo.
- *Alternativa: no guardar los operandos exactos.* Descartada: quien valida no podría recalcular ni
  las cifras ni el identificador.

### 8. Orden en la ruta y errores

La rama nueva va después de comprobar la conversación y antes de la rama de propiedad:

1. Conversación del usuario y del cliente activo, o 404 de conversación (ya existe).
2. `fetch_anomaly_episode_snapshot`; `None` da `404 {"detail":{"code":"anomaly_episode_not_found"}}`,
   el mismo cuerpo que la API de episodios, sin distinguir otro cliente de inexistente.
3. Explicador; `ExplanationUnavailable` da `409 {"detail":{"code":"anomaly_explanation_unavailable"}}`.
4. Se guardan el mensaje del usuario y el del asistente, se incrementa `assistant_queries_total` y
   se responde 201 con `retrieved_context` vacío.

La explicación se calcula entera antes de escribir, así que 404, 409 y 422 no dejan ningún mensaje.
No se añaden eventos de registro ni métricas: sin registro nuevo no hay dónde filtrar un nombre de
servicio, y una prueba lo fija capturando los registros con un servicio reconocible.

Si falla la segunda escritura queda un mensaje de usuario sin respuesta. Es el comportamiento
actual de las otras dos ramas y no se cambia aquí; se registra como hallazgo si no lo está ya.

### 9. Redactor: una segunda casilla y un componente propio

`MessageComposer.tsx` gana la casilla «Explicar una anomalía». Activarla desactiva «Consultar
costes por propiedad» y al revés; la casilla existente y sus pruebas no cambian. Los campos del modo
viven en `AnomalyExplanationFields.tsx`: carga las anomalías del cliente con `fetchAnomalyEpisodes`
(todas, abiertas y cerradas), las enseña en un `select` con servicio, moneda, día de inicio,
criticidad y estado en el orden que da el backend, y cubre los estados vacío («Este cliente no
tiene anomalías guardadas. Se detectan desde el panel de Anomalías.») y de error. Con el modo
activo y la pregunta vacía se propone el texto «¿Por qué se ha marcado esta anomalía?», que se
puede cambiar; el botón no envía sin una anomalía elegida.

`AnomalyEvidence.tsx` pinta `anomaly_evidence` en un bloque desplegable y, como `CostEvidence`, no
muestra nada si `schema_version`, `adapter_version`, el formato del `id` o los campos que usa no
cumplen el contrato: dice «La evidencia de esta explicación no está disponible.».
`AnswerEvidence.tsx` añade esa rama después de `cost_evidence`. Los tipos y el validador van en
`services/contracts.ts`.

- *Alternativa: sustituir las casillas por un selector de tipo de consulta.* Descartada: cambia la
  interacción de JUP-037 y sus pruebas sin que la tarjeta lo pida.

### 10. Enlace del panel por parámetro de dirección

El detalle de la anomalía en `AnomaliesPanel.tsx` añade un `Link` a `/assistant?episode=<id>`.
`ConversationsPage.tsx` lee el parámetro y lo pasa al redactor, que abre el modo con esa anomalía
elegida si está en la lista del cliente activo; si no está, lo avisa y no elige ninguna. Tras un
envío correcto la página quita el parámetro con `replace`, para que recargar no vuelva a armar el
modo. El panel no hace ninguna petición nueva.

`/assistant` está bajo `TenantScopedOutlet`: al cambiar de cliente la pantalla se remonta, el
parámetro sigue en la dirección y cae en el caso «no está en el cliente activo».

- *Alternativa: estado del enrutador en lugar de parámetro.* Descartada: se pierde al recargar y es
  más difícil de probar; el identificador no autoriza nada, porque el backend filtra por cliente.
- *Alternativa: que el panel cree la conversación y envíe.* Descartada por Victor (opción no
  elegida): dos llamadas encadenadas en el panel, fallos a medias y conversaciones duplicadas.

### 11. Sin ADR nuevo; nota fechada en ADR-0020

Respuesta determinista con evidencia en los metadatos del mensaje es el patrón de JUP-037, y la
fuente (episodios) ya la decide ADR-0020. Lo único que cambia respecto a un ADR vigente es su punto
11, que asignaba a JUP-038 las aclaraciones del corpus. Se añade a
`docs/adr/ADR-0020-cost-anomaly-episodes.md` una nota fechada: JUP-038 entrega el explicador sin
herramienta registrada y el corpus se aplaza con `RF-114-001` abierto, con el motivo del
`proposal.md`. El ADR sigue en `Proposed` y su decisión no se reescribe. Decisión de Victor del
2026-10-12; Lucia, autora del ADR, la ve en la revisión del PR.

### 12. Organización de las especificaciones

Capacidad nueva `anomaly-episode-explanation` para todo el comportamiento de la explicación,
incluida su presentación en el asistente (no existe una capacidad del chat donde ponerla).
`finops-agent-tool-contract` modifica el requisito de anomalías copiándolo entero y añadiendo un
párrafo y dos escenarios; no se quita ninguno. `anomalies-panel` añade un requisito para el enlace
en lugar de modificar «Episode detail with status actions», que no cambia.
`cost-anomaly-detection` no se toca: su escenario «Downstream explanation» ya es cierto.

### 13. Pruebas y validación

- **Explicador, sin base de datos:** cifras del ejemplo del contrato de episodios (400.00, 550.00,
  2026-09-08), bordes de redondeo de la decisión 4, cada estado y cada observación, episodio
  enlazado, servicio `null`, servicio y motivo hostiles (saltos de línea, comillas, caracteres
  invisibles, texto con aspecto de respuesta), USD, datos sintéticos, determinismo del `id`,
  dependencia del cliente y casos de `ExplanationUnavailable`.
- **Ruta, en SQLite:** autenticación y almacenamiento de mensajes reales con un doble de
  `fetch_anomaly_episode_snapshot`, como las pruebas de JUP-037 y de la API de episodios: 201, 404,
  409, 422, exclusión con propiedad, conversación ajena, nada guardado en los fallos, recarga de la
  conversación, la rama documental y la de propiedad sin cambios, y registros sin datos del cliente.
- **CockroachDB real, opt-in:** cargar una serie, detectar, explicar y comprobar cifras, aislamiento
  entre clientes y que explicar no mueve la marca de agua ni los episodios. CI no la ejecuta
  (`RF-096-004`) y así se dirá en la evidencia.
- **Frontend:** componente de evidencia, modo del redactor (elegir, vacío, error, preselección,
  anomalía ajena, exclusión, error del backend con el borrador conservado) y enlace del panel sin
  peticiones nuevas. La prueba de español existente recorre los componentes nuevos y debe pasar sin
  editarla.
- **Archivos de prueba:** todos nuevos. No se edita ningún archivo de pruebas ya commiteado; las
  pruebas existentes de propiedad, citas, panel y textos sirven de control y deben pasar tal cual.
- **Mutación** sobre el explicador, la rama de la ruta, el validador de la evidencia y el modo del
  redactor, según el harness local.
- **Stack real aislado** con el conjunto sintético de JUP-107: explicar las tres anomalías (P1, P2 y
  P3) desde el navegador, comparar con `docs/demo/JUP-107/esperados-anomalias.json` y recalcular a
  mano una evidencia.

Las pruebas de Python se ejecutan en un contenedor equivalente a CI (`python:3.12`), porque en
Windows fallan pruebas ajenas del backend (`RF-105-004`).

## Risks / Trade-offs

- [Conflicto con las PR #120 y #121 en `routes/assistant.py`, `schemas/assistant.py` y
  `database.py`] → el cambio en esos archivos es una rama, un campo y un método; lo demás va en
  archivos nuevos. Antes de abrir la PR se comprueba con `git merge-tree` contra las dos cabeceras y
  se anota el resultado para quien integre después.
- [Al integrarse JUP-035, la pantalla `/assistant` pierde su entrada de menú] → comprobado el
  2026-10-12 en las cabeceras de las PR #120 (`f63c1503`) y #121 (`5c071d93`), ambas abiertas y en
  conflicto con `develop`: no borran la ruta `/assistant`, `ConversationsPage` ni `MessageComposer`,
  pero `Layout.tsx` quita «Asistente» del menú y monta un panel de chat nuevo en todas las
  pantallas. El enlace «Explicar en el asistente» del panel de anomalías seguiría funcionando y
  pasaría a ser la entrada principal. El chat nuevo lee las mismas conversaciones y pinta los
  mensajes con `AnswerEvidence`, así que la explicación y su evidencia se verían también allí si el
  merge conserva la rama de `anomaly_evidence`. Ese chat envía por `/generations`, no por la ruta
  de mensajes, y no tiene herramienta de anomalías: pedir la explicación desde él es trabajo
  posterior. La ruta de mensajes se conserva, pero guarda el par con `prepare_message` y
  `append_pair`; la rama de este cambio habrá que adaptarla a eso en el merge (y el par pasa a ser
  atómico). No cambia el alcance de este cambio; se registra como hallazgo en la tarea 9.5.
- [La redacción en español de las limitaciones se desincroniza de `LIMITATIONS`] → prueba que falla
  si cambia el número, y 409 para cualquier versión de reglas que no sea la conocida.
- [La explicación solo cuenta el día de apertura y los acumulados] → el texto lo dice. Explicar la
  evolución exigiría guardar la serie diaria del episodio, que es trabajo de otra tarjeta.
- [«El agente explica» sin modelo generativo puede no coincidir con lo que alguien espera de la
  tarjeta] → decisión de alcance 1 de Victor, escrita en el `proposal.md`, en el contrato y en la
  evidencia; el explicador queda listo para JUP-035.
- [Una pregunta en texto libre sobre anomalías sigue respondiéndose con el corpus sin las
  aclaraciones de ADR-0020] → `RF-114-001` sigue abierto y se actualiza con la decisión de aplazarlo.
- [Mensaje de usuario sin respuesta si falla la segunda escritura] → comportamiento actual de las
  tres ramas; se registra como hallazgo y no se arregla aquí.
- [El parámetro `episode` queda en la dirección al cambiar de cliente o tras cerrar sesión] → se
  trata como dato no fiable: solo preselecciona si está en la lista del cliente activo.
- [La evidencia incluye identificadores de usuario del episodio (`status_changed_by`,
  `first_reviewed_by`)] → son los mismos que cualquier miembro del cliente lee en la API de
  episodios, y la conversación es privada de quien pregunta; no se añaden nombres ni correos.

## Migration Plan

Sin migración de base de datos ni configuración. El campo nuevo es opcional y las peticiones
actuales no cambian. Marcha atrás: revertir el commit de la PR; los mensajes ya guardados con
`anomaly_evidence` siguen leyéndose como texto, porque el frontend anterior ignora metadatos que no
conoce.

## Open Questions

Ninguna que cambie las especificaciones o las tareas. Queda para después de este cambio, y no lo
bloquea: confirmar con Paris (reglas de negocio) la lectura de los tramos P1/P2/P3 como impacto del
episodio, pendiente desde ADR-0020; la explicación cita el tramo tal como está guardado en las
`rules` del episodio.
