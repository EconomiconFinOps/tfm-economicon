# Evidencia JUP-038 — Explicar anomalías detectadas

Tarjeta: [JUP-038](https://trello.com/c/QzkjVY7P). Change: `jup-038-explain-anomaly-episodes`. Rama: `feat/JUP-038-explain-anomaly-episodes`. Contrato: [anomaly-explanations.md](../api/anomaly-explanations.md). Decisión: nota fechada en [ADR-0020](../adr/ADR-0020-cost-anomaly-episodes.md).

Abierta el 2026-10-12 sobre `develop` en `bfaf3983` (merge del PR #122, JUP-114, más el PR #126 de notas). Esta evidencia la prepara la persona que lidera la tarjeta durante el `apply`. **No sustituye a `Revision JUP-038` (Lucia Mateo) ni a `Validacion JUP-038` (Alejandro Aguado)**, que siguen pendientes, ni acredita pairing de Paris Arcos Martin. Hasta que se ejecute una comprobación, aquí figura como pendiente.

## Alcance acordado

La explicación es determinista: la arma código a partir del episodio guardado, sin modelo generativo, sin embeddings y sin herramienta registrada del agente (eso es JUP-035). `RF-114-001` (aclaraciones en el corpus del asistente) se aplaza y sigue abierto. Detalle en `proposal.md` y en el bloque `Human Approval` del change.

## Criterios de la tarjeta

| # | Criterio | Estado | Evidencia |
| --- | --- | --- | --- |
| 1 | Resultado funcional verificable. | Pendiente | Grupo 8 de las tareas: explicación de las tres anomalías (P1, P2, P3) de JUP-107 en el stack real, cifras frente a `docs/demo/JUP-107/esperados-anomalias.json` y recálculo a mano de una evidencia. |
| 2 | Pruebas necesarias añadidas y en verde. | Pendiente | Grupos 2 a 7, con Red, Green y mutación por grupo, y suites completas en el grupo 10. |
| 3 | Documentación y decisiones actualizadas. | En curso | Contrato [anomaly-explanations.md](../api/anomaly-explanations.md) y nota en ADR-0020 (grupo 1); resto en el grupo 9. |
| 4 | Pull request revisado y vinculado. | Pendiente | Se abre al terminar el grupo 10; enlace por rellenar. |
| 5 | Validación funcional y evidencia enlazadas. | Pendiente | Este archivo, `review.md` del change y enlaces de PR y CI por rellenar. |

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
- Hallazgo: la base guarda los importes con 12 decimales (`NUMERIC(38,12)`), así que los operandos de la evidencia son p. ej. `2800.000000000000`. Decisión de Victor: se conservan tal cual; la corrección de una prueba commiteada fue un bypass puntual del candado, autorizado y registrado en `review.md`.
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

Aún no se ha ejecutado nada en un navegador real ni con el stack completo de Compose, y todavía no existe en el frontend la entrada para pedir la explicación: eso llega con los grupos 6 a 8.

Nada más se ha ejecutado. Los resultados de pruebas, mutación, DoD y stack real de los demás grupos se añaden aquí al completarlos.

## Pendiente

- PR: por abrir.
- CI: por rellenar con el run del último commit.
- `Revision JUP-038` y `Validacion JUP-038`: pendientes.
- Lo no validado se lista aquí al cerrar el grupo 10.
