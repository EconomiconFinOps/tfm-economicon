# Evidencia JUP-038 — Explicar anomalías detectadas

Tarjeta: [JUP-038](https://trello.com/c/QzkjVY7P). Change: `jup-038-explain-anomaly-episodes`. Rama: `feat/JUP-038-explain-anomaly-episodes`. Contrato: [anomaly-explanations.md](../api/anomaly-explanations.md). Decisión: nota fechada en [ADR-0020](../adr/ADR-0020-cost-anomaly-episodes.md).

Abierta el 2026-10-12 sobre `develop` en `bfaf3983` (merge del PR #122, JUP-114, más el PR #126 de notas). Esta evidencia la prepara la persona que lidera la tarjeta durante el `apply`. **No sustituye a `Revision JUP-038` (Lucia Mateo) ni a `Validacion JUP-038` (Alejandro Aguado)**, que siguen pendientes, ni acredita pairing de Paris Arcos Martin. Hasta que se ejecute una comprobación, aquí figura como pendiente.

## Alcance acordado

La explicación es determinista: la arma código a partir del episodio guardado, sin modelo generativo, sin embeddings y sin herramienta registrada del agente (eso es JUP-035). `RF-114-001` (aclaraciones en el corpus del asistente) se aplaza y sigue abierto. Detalle en `proposal.md` y en el bloque `Human Approval` del change.

## Criterios de la tarjeta

| # | Criterio | Estado | Evidencia |
| --- | --- | --- | --- |
| 1 | Resultado funcional verificable. | Cumplido en la rama (validación propia; la independiente sigue pendiente) | Grupo 8 y apartado «Cierre» más abajo: las tres anomalías (P1, P2, P3) de JUP-107 se explican en el stack real con las cifras de `esperados-anomalias.json`. |
| 2 | Pruebas necesarias añadidas y en verde. | Cumplido en local; CI por rellenar | 209 pruebas nuevas de backend y 357 de frontend, con Red, Green y mutación por grupo; suites completas en el apartado «Cierre». |
| 3 | Documentación y decisiones actualizadas. | Cumplido | Contrato [anomaly-explanations.md](../api/anomaly-explanations.md), nota en ADR-0020, arquitectura, READMEs, demo, backlog, continuidad y pruebas críticas (grupos 1 y 9). |
| 4 | Pull request revisado y vinculado. | Pendiente | La PR no está abierta; `Revision JUP-038` y `Validacion JUP-038` sin publicar. |
| 5 | Validación funcional y evidencia enlazadas. | Parcial | Esta evidencia y `review.md` existen y se enlazarán en la PR; falta el enlace de CI y la `Validacion JUP-038` de Alejandro. |

## Fuentes verificadas

- `origin/develop` en `bfaf3983` el 2026-10-12, al abrir esta evidencia y al aprobar el gate pre-código.
- Contrato de episodios [anomaly-episodes.md](../api/anomaly-episodes.md), ADR-0020 y las especificaciones `cost-anomaly-episodes`, `cost-anomaly-detection`, `finops-agent-tool-contract` y `anomalies-panel`, leídas en `develop`.
- PR #120 (`f63c1503`) y PR #121 (`5c071d93`), abiertas el 2026-10-12 y en conflicto con `develop`: se midió su efecto sobre la entrada del asistente (ver el riesgo correspondiente de `design.md`).

## Trazabilidad

| Requisito | Dónde se prueba |
| --- | --- |
| `anomaly-episode-explanation` (8 requisitos, 33 escenarios) | Grupos 2 a 6 de las tareas |
| `finops-agent-tool-contract`, requisito de anomalías (modificado) | Grupos 2 y 4 |
| `anomalies-panel`, enlace a la explicación (añadido) | Grupo 7 |

## Validación ejecutada

Gate pre-código, 2026-10-12: `corepack pnpm openspec:validate` (68 de 68), `corepack pnpm jup:check -- --change jup-038-explain-anomaly-episodes` y `corepack pnpm jup:cleanup:check`, las tres correctas.

Cálculo del ejemplo del contrato (tarea 1.2): script independiente del backend, con aritmética exacta, que da 150.00 EUR de subida absoluta, 37.50 % de subida relativa, 400.00 EUR de impacto acumulado en 2 días y criticidad P3. Coincide con la salida que ya documenta [anomaly-episodes.md](../api/anomaly-episodes.md) (`2026-09-08 2026-09-09 400.00 400.00 2 P3`). Es un cálculo de documentación, hecho en el grupo 1 antes de que existiera código de este change.

**Grupo 2 — explicador** (commits `4d96ff74`, `435e4df5` y `18adbe9f`, 2026-10-12):

- Pruebas del explicador: 95 (75 del Red y 20 de remediación de mutantes), todas en verde en Python 3.12.15; el Red las dejó en `75 failed` por la ausencia del módulo.
- Regresión backend completa en contenedor equivalente a CI: 1350 pasan, 118 omitidas, 0 fallos; el control sobre `develop` (`bfaf3983`) da 1255, 118 y 0, es decir, +95 exactas.
- Mutación: mutmut 2.5.1, 256 mutantes, 255 muertos y 1 superviviente equivalente justificado (`_PRECISION` 120 a 121); 18 de 18 mutantes manuales muertos.
- Lint (`compileall`, `eslint`), `tsc` y escaneo de secretos: sin hallazgos.
- Revisión del agente `qa`: `accept`. Detalle en `review.md` del change.

**Grupo 3 — lectura con operandos exactos** (commits `356012c4`, `95dc4bac` y `35cf49c0`, 2026-10-12):

- `Database.fetch_anomaly_episode_snapshot`: una sola sentencia SQL, filtrada por cliente, que devuelve el episodio, los operandos exactos y la marca sintética. 22 pruebas contra CockroachDB v24.1.11 real (13 del Red y 9 de remediación de mutantes), 0 omitidas; el Red las dejó en `13 failed`.
- Hallazgo: los importes llevan 12 decimales (vienen de `pretax_cost DECIMAL(38,12)`; las columnas del episodio son `DECIMAL` sin precisión), así que los operandos de la evidencia son p. ej. `2800.000000000000`. Decisión de Victor: se conservan tal cual; la corrección de una prueba commiteada fue un bypass puntual del candado, autorizado y registrado en `review.md`.
- Regresión backend completa: como CI, 1350 pasan, 140 omitidas, 0 fallos; con CockroachDB real, 1469 pasan, 21 omitidas (integraciones externas), 0 fallos.
- Mutación: 14 mutantes manuales dirigidos al método, 13 muertos y 1 equivalente justificado (`SERIALIZABLE`, que CockroachDB ya usa por defecto). Es una muestra dirigida, no un barrido.
- Revisión del agente `qa`: `accept`.
- **Estas pruebas no corren en CI** (`RF-096-004`): solo existe la evidencia de la ejecución local contra un nodo desechable.

**Grupo 4 — ruta del asistente** (commits `f055eed6`, `cd52cc17`, `cef8a152` y `367e96f0`, 2026-10-12):

- `POST /assistant/conversations/{id}/messages` acepta `anomaly_query` y responde con la explicación guardada y su evidencia. Tres archivos de producto, solo inserciones: esquema `AnomalySelection`, el campo con su exclusión frente a `ownership_query` y la rama de la ruta.
- 92 pruebas nuevas: 83 corren en CI (esquema 45, ruta 27 con SQLite y un doble de la lectura, y 11 de mutantes del esquema) y 9 contra CockroachDB real (recorrido completo por HTTP, solo opt-in). El Red las dejó en `71 failed, 1 passed` y `9 failed`.
- Regresión backend completa: como CI, 1433 pasan, 149 omitidas, 0 fallos; con CockroachDB real, 1561 pasan, 21 omitidas (integraciones externas), 0 fallos. Ninguna prueba ya existente se editó.
- Mutación: `mutmut` sobre el esquema (11 mutantes, 9 muertos) y 22 mutantes manuales dirigidos a la ruta y al validador (21 muertos); los tres supervivientes son equivalentes y están justificados en `review.md`. Es una muestra dirigida, no un barrido.
- Revisión del agente `qa`: `accept`.
- **Las 9 pruebas de CockroachDB no corren en CI** (`RF-096-004`): solo existe la evidencia de la ejecución local contra un nodo desechable.

**Grupo 5 — evidencia de la explicación en el frontend** (commits `f678ee09`, `d31639de` y `531003d3`, 2026-10-12 y 2026-10-13):

- `isAnomalyEvidence` (validador estricto con coherencia interna y frontera de confianza sobre los metadatos del mensaje), el componente `AnomalyEvidence` y su rama en `AnswerEvidence`. Producto: 70 líneas añadidas en `contracts.ts`, un componente nuevo de 52 líneas y +4/−1 en `AnswerEvidence.tsx`. El componente no calcula nada: muestra las cadenas de la evidencia, operandos de 12 decimales incluidos.
- 271 pruebas nuevas (261 del Red y 10 de remediación de mutantes). El Red las dejó en `257 failed | 4 passed`.
- Suite completa del frontend: 71 archivos, 1151 pruebas pasan, 0 fallos; lint, typecheck y build con código 0; escaneo de secretos sin hallazgos.
- Mutación: Stryker sobre el validador y la rama de `AnswerEvidence` (212 mutantes, 211 muertos, 1 equivalente justificado) y 32 mutantes manuales sobre el componente (32 muertos), porque Stryker no ejecuta sus pruebas. Es una muestra dirigida, no un barrido.
- Incidente de proceso: el lint falló en las pruebas del Red (49 errores, tipos `any` y un literal); se corrigió con una excepción puntual al candado de pruebas, autorizada por Victor y verificada (solo cambiaron tipos). El Red incluirá desde ahora lint y typecheck.
- Revisión del agente `qa`: `accept`.

**Grupo 6 — modo «Explicar una anomalía» del redactor** (commits `1a22a1ae`, `2ac1d794` y `1ae0e1d9`, 2026-10-13):

- Segunda casilla del redactor, excluyente con la de propiedad; el `select` de anomalías del cliente activo (solo ids con formato válido); el `POST` con `anomaly_query`; errores traducidos por `detail.code`; y la entrada `/assistant?episode=<id>`, que solo preselecciona y exige pulsar «Enviar». Producto: un componente nuevo y +88/−9 líneas en tres archivos existentes, con props opcionales que no cambian los usos anteriores.
- 67 pruebas nuevas en cuatro archivos (38 de integración del Red, que fallaban todas por la casilla inexistente, y 29 de remediación de mutantes). Las de integración montan la aplicación con el enrutador y un servidor simulado en el que cualquier petición no prevista hace fallar la prueba.
- Lint, typecheck y build con código 0; escaneo de secretos sin hallazgos. Suite completa del frontend: 1218 de 1219 en cada una de dos ejecuciones; el único fallo de cada ejecución es una prueba distinta de JUP-098, y el `develop` previo a JUP-038 falla esas mismas dos pruebas en el control (no atribuibles a este cambio).
- Mutación: Stryker sobre exactamente el código añadido (175 mutantes), 82.86 % antes de la remediación y **92.57 %** después; los 13 supervivientes son equivalentes o no especificados y están justificados.
- Revisión del agente `qa`: `accept`.

**Grupo 7 — enlace «Explicar en el asistente» del panel de anomalías** (commits `8d3834a8` y `8fddc0b3`, 2026-10-13):

- Un enlace en el detalle de cada anomalía (en cualquier estado, y solo si su identificador tiene el formato real) hacia `/assistant?episode=<id>`. Solo navega: no hace ninguna petición. Producto: 11 líneas añadidas y 2 de `import` ampliadas en `AnomaliesPanel.tsx`.
- 19 pruebas nuevas (el Red las dejó en `19 failed`).
- Suite completa del frontend, dos ejecuciones seguidas: 76 archivos, 1238 pruebas, 0 fallos; lint, typecheck y build con código 0; escaneo de secretos sin hallazgos.
- Mutación: Stryker 4 de 4 y 7 mutantes manuales sobre el destino y el texto (6 muertos, 1 equivalente justificado). Es una muestra dirigida.
- Revisión del agente `qa`: `accept`. Su observación sobre el formato del identificador se incorporó a la spec del change.

**El frontend queda completo.**

**Grupo 8 — validación con el stack real** (2026-10-13, sobre `df65c3ca`; archivos en `docs/evidence/JUP-038/`):

- Stack aislado de Compose (`-p jup038v`, 7 servicios sanos, volúmenes nuevos, secretos aleatorios fuera del repositorio) con el conjunto sintético de JUP-107; borrado al terminar (`down -v --rmi local`, sin restos).
- **Navegador (Chrome real):** «Detectar ahora» abre las 3 anomalías esperadas; por cada una, enlace del panel → asistente con la anomalía preseleccionada → **cero `POST` antes de «Enviar»** → un `POST` 201 → explicación y evidencia con las cifras de `esperados-anomalias.json`: Compute (P1) 24/24, Database (P2) 23/23, Analytics (P3) 23/23 comprobaciones; 0 errores de consola; sin desbordamiento a 390 px. Capturas `01` a `04`.
- **Recálculo independiente** (script con `BigInt` y `crypto`, sin código del backend) de la evidencia de Compute: cifras e **identificador sha256 coinciden**, 10/10.
- **HTTP:** el 404 de otro cliente y el de un id inexistente son idénticos byte a byte; con pgvector parado la explicación responde; tras cambiar el estado el `id` cambia y el mensaje anterior se conserva; el cierre real con un motivo con comillas y acentos sale escapado y con la fecha UTC; ningún registro del backend contiene un nombre de servicio ni un motivo.
- **Conflictos con JUP-035 (#120 y #121):** este cambio añade conflicto en solo 2 archivos, `routes/assistant.py` y `AnswerEvidence.tsx`; los otros 8 ya existían entre `develop` y esas PR.
- Dos fallos de la primera pasada fueron **de mis scripts, no del producto** (un selector ambiguo y un error de redondeo del oráculo); se corrigieron y se repitieron. Detalle en `review.md`.
- **No validado:** tema oscuro, otros anchos y navegadores, un usuario sin pertenencia al cliente por HTTP (lo cubren las pruebas de CI) y datos reales. No sustituye a `Validacion JUP-038`.

### Cómo reproducir la validación

1. Crear un archivo de entorno privado **fuera del repositorio** a partir de `.env.example` (`RUNTIME_ENVIRONMENT=development`, `ALLOW_INSECURE_LOCAL_DATABASE=true`, `DEMO_SEED_ENABLED=true`, secretos aleatorios, `COMPOSE_PROJECT_NAME` y puertos propios, `CORS_ALLOWED_ORIGINS` con el origen del frontend y el DSN de CockroachDB `cockroachdb+psycopg://root@cockroachdb:26257/defaultdb?sslmode=disable`).
2. `docker compose -p <proyecto> --env-file <archivo> up -d --build --wait backend processor frontend`.
3. Cargar el conjunto de demo: `docker compose -p <proyecto> --env-file <archivo> --profile demo run --rm demo-data python scripts/demo_data.py apply`. La validación original se hizo antes de JUP-119 con `scripts/synthetic_anomalies.py` (retirado por esa tarjeta); el conjunto de septiembre da las mismas tres anomalías, con las cifras de `docs/demo/JUP-107/esperados-anomalias.json`.
4. Con `playwright-core` y Chrome: `node docs/evidence/JUP-038/validar-navegador.cjs <directorio>` y `node docs/evidence/JUP-038/validar-http.cjs <directorio>`, donde `<directorio>` contiene `stack/jup038.env` (los puertos del script son los de esta validación) y `capturas/`.
5. `docker compose -p <proyecto> --env-file <archivo> down -v --rmi local`.

## Cierre (grupo 10, 2026-10-13)

Sobre `d0095619` (la rama contiene `origin/develop` en `bfaf3983`; sin commits nuevos en `develop` al comprobarlo).

### Suites completas (tarea 10.1)

| Suite | Base (`develop` `bfaf3983`) | Con JUP-038 | Diferencia |
| --- | --- | --- | --- |
| Backend como CI (Python 3.12, sin CockroachDB) | 1255 pasan, 118 omitidas, 0 fallos | **1433 pasan, 149 omitidas, 0 fallos** | +178 que pasan y +31 omitidas (las 9 de `test_anomaly_explanation_cockroach.py` y las 22 de `test_anomaly_episode_snapshot*.py`) |
| Backend con CockroachDB v24.1.11 real | no medida con la base | **1561 pasan, 21 omitidas, 0 fallos** | las 21 omitidas son integraciones externas (RabbitMQ, pgvector…); 1561 + 21 = 1582 = 1433 + 149 |
| Frontend (Vitest) | 66 archivos, 881 pruebas | **76 archivos, 1238 pruebas** | +10 archivos, +357 pruebas |

- `compileall` del backend, lint de los cuatro paquetes, y lint, `tsc` y build del frontend: código 0.
- Las 209 pruebas nuevas del backend son 75 + 20 (explicador), 13 + 9 (lectura del episodio), 45 + 11 (esquema), 27 (ruta) y 9 (recorrido con CockroachDB); las 357 del frontend son las de los diez archivos nuevos. Ninguna prueba que ya existía se editó (el diff contra la base solo añade archivos de prueba).
- **Frontend intermitente en esta máquina.** Tres ejecuciones completas seguidas con el paralelismo por defecto dieron 1 fallo (`conversations.test.tsx`, formato de fecha), 0 fallos y 2 fallos (dos pruebas de JUP-098); con `--maxWorkers=1`, 1238 de 1238. Las pruebas fallidas pasan solas y ninguna toca archivos de este cambio; el control sobre `develop` ya falla las de JUP-098 (`RF-098-004`, `RF-103-005`). Es una intermitencia de plazos con carga, no un verde limpio con el paralelismo por defecto: se declara así.
- Las pruebas de CockroachDB (31 en total) **no corren en CI** (`RF-096-004`): solo hay evidencia de la ejecución local con un nodo desechable, ya eliminado.

### Alcance del diff (tarea 10.2)

`git diff --stat origin/develop...HEAD`: 62 archivos, 8933 inserciones y 27 borrados. El producto cambiado son exactamente los archivos del `proposal.md`: en el backend `services/anomaly_explanations.py` y `schemas/anomaly_explanations.py` (nuevos), `database.py`, `schemas/assistant.py` y `routes/assistant.py` (solo inserciones); en el frontend `contracts.ts`, `AnomalyEvidence.tsx`, `AnomalyExplanationFields.tsx`, `AnswerEvidence.tsx`, `MessageComposer.tsx`, `ConversationsPage.tsx` y `AnomaliesPanel.tsx`. Los 27 borrados son líneas de esos archivos de producto y de documentación, no de pruebas. **No cambian** migraciones, dependencias, CI, processor, azure-cost-api, infraestructura ni el corpus del asistente (búsqueda por ruta: sin coincidencias).

### Comprobaciones de higiene (tarea 10.3)

`corepack pnpm lint`, `corepack pnpm openspec:validate` (68 de 68), `corepack pnpm jup:check -- --change jup-038-explain-anomaly-episodes`, `corepack pnpm jup:cleanup:check` (1334 archivos), `corepack pnpm jup:check:test` (7 de 7), `corepack pnpm jup:cleanup:test` (6 de 6) y `git diff --check`: todas correctas. Enlaces relativos de los documentos tocados: ninguno roto nuevo (`docs/continuidad/README.md` ya enlazaba a `metricas-funcionales-negocio.md` y `cobertura-etiquetado.md`, que no existen en esta rama).

### Por criterio de la tarjeta

1. **Resultado funcional verificable.** Grupo 8: en un navegador real, las tres anomalías explicadas con las cifras esperadas (Compute 24/24, Database 23/23, Analytics 23/23 comprobaciones), cero peticiones antes de «Enviar», 404 idéntico para un episodio ajeno y uno inexistente, y recálculo independiente de la evidencia de Compute (cifras e identificador sha256 coinciden). La explicación es determinista y siempre candidata, sin causa ni ahorro.
2. **Pruebas.** Apartado 10.1. Mutación dirigida por grupo: explicador 255 de 256 (superviviente equivalente), esquema y ruta con `mutmut` y 22 mutantes manuales (tres supervivientes equivalentes justificados) y frontend 92.57 % con Stryker sobre el código añadido más un harness manual donde Stryker no ejecuta las pruebas. Son muestras dirigidas, no barridos completos.
3. **Documentación y decisiones.** Contrato con ejemplo real, nota fechada en ADR-0020 (sin ADR nuevo), `architecture.md`, `finops-agent-tools.md`, READMEs, paso opcional de la demo, `critical-flows.md`, continuidad y backlog (`RF-114-001` aplazado, `RF-038-001` a `009`).
4. **PR revisado y vinculado.** Sin cumplir: la PR aún no existe. Revisión de Lucía Mateo y validación de Alejandro Aguado pendientes; no se da por hecho ningún dictamen ni el pairing de Paris Arcos Martin.
5. **Validación funcional y evidencia enlazadas.** Esta evidencia, `review.md`, `docs/evidence/JUP-038/` (capturas, scripts e informes) y el contrato. Falta el enlace del run de CI y la `Validacion JUP-038` independiente.

### Lo que NO se ha validado

- **Ningún dictamen humano:** ni la revisión, ni la validación independiente, ni el pairing. La validación de esta evidencia la hizo quien lidera la tarjeta con ayuda de agentes.
- **CI:** no hay run de CI de este cambio. Las 31 pruebas de CockroachDB no están en CI.
- **Navegador:** solo Chrome, tema claro y anchos de escritorio y 390 px. Sin tema oscuro, otros navegadores ni dispositivos reales; sin pruebas automáticas de navegador en el repositorio (los scripts de `docs/evidence/JUP-038/` son manuales).
- **Datos:** solo el conjunto sintético de JUP-107; sin datos reales de Azure ni tenants reales; sin carga, concurrencia ni despliegue en la nube.
- **Aislamiento por HTTP de un usuario sin pertenencia al cliente:** cubierto por pruebas de CI con la base doblada y con CockroachDB, no en el stack real.
- **Integración con JUP-035:** los conflictos con las PR #120 y #121 están medidos (dos archivos nuevos), no resueltos; la herramienta `detect_cost_anomaly_candidates` no existe (`RF-038-006`) y el par de mensajes no se guarda de forma atómica (`RF-038-005`).
- **Mutación:** muestras dirigidas, no barrido completo; Stryker no ejecuta algunas pruebas de componentes (`RF-038-007`).
- **Frontend completo en verde con el paralelismo por defecto:** no garantizado en esta máquina (intermitencias descritas arriba); sí con un solo worker.
- **Corpus del asistente:** no cambia, así que el asistente no sabe que lo esperado es la media de 7 días ni cómo se calcula la criticidad (`RF-114-001`).

### Corrección tras la revisión de la PR #128 (2026-10-13)

`Revision JUP-038` pidió dos cambios (datos guardados incoherentes y operandos no finitos o enormes, que debían dar 409 y no 200 o 500). Se atendieron en la rama con spec, Red, Green, mutación y QA; el detalle, las tres excepciones autorizadas al candado de pruebas y los errores propios están en el apartado «Adenda» de `review.md`.

- Backend como CI: **1623 pasan, 149 omitidas, 0 fallos** (antes 1433 y 149: +190 pruebas nuevas, 140 de la ronda 1 y 50 de la ronda 2). Con CockroachDB v24.1.11 real: **1751 pasan, 21 omitidas, 0 fallos**.
- Mutación dirigida al código nuevo: 28 de 32 muertos; los 4 supervivientes son equivalentes y están justificados. QA independiente: la ronda 1 pidió cambios (exponentes negativos enormes) y la ronda 2 dio `accept` tras un fuzz de 60000 tripletas sin excepciones inesperadas.
- Lint, `openspec:validate` y `git diff --check` correctos. El frontend no cambia y no se reejecutó.
- Sigue sin hacerse: `Validacion JUP-038`, el run de CI de la nueva cabeza de la rama y la reverificación en navegador (no aplica: no cambia la interfaz).

- **Con CockroachDB real (validación de Paris sobre `49641cec`):** una prueba nueva corrompe filas con SQL (`NaN`, `Infinity`, `1E+200`, `-5`, `1E-150`, días 0 y -1, fecha final anterior, motivo vacío, `JPY`) y pide la explicación por HTTP: 16 casos, de los que 6 daban 500 (`InvalidOperation` en la lectura, antes del explicador) y ahora dan 409 sin guardar mensajes. Con la corrección: 25 de 25 con la base real (16 + las 9 del recorrido completo). Mutación de la ruta: 5 de 5 muertos.

- **Cifras finales tras las dos revisiones (cabeza `46f4fc79`):** backend como CI, **1623 pasan, 165 omitidas, 0 fallos** (las 16 pruebas nuevas con CockroachDB se omiten sin base; antes del PR #128: 1433 y 149); con CockroachDB v24.1.11 real, **1767 pasan, 21 omitidas, 0 fallos** (antes 1561). `corepack pnpm lint`, `openspec:validate`, `jup:check:all`, `jup:cleanup:check` y `git diff --check` correctos. Frontend sin cambios y sin reejecutar. Contenedor de la base eliminado.

## Pendiente

- PR: por abrir (tarea 10.6, tras la aprobación posterior a la revisión).
- CI: por rellenar con el run del último commit.
- `Revision JUP-038` (Lucía Mateo) y `Validacion JUP-038` (Alejandro Aguado): pendientes.
