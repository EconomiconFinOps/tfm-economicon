# Revisión de jup-038-explain-anomaly-episodes

JUP: JUP-038
Trello: https://trello.com/c/QzkjVY7P

Registro de ejecución del `apply`, grupo a grupo. El resultado final, el checklist y el gate
posterior a la revisión se completan al terminar el grupo 10. Nada de lo que no figure aquí con su
comando y su resultado se da por validado.

## Grupo 1 — Preparación y contrato (tareas 1.1 a 1.3)

**Excepción doc-only.** El grupo solo escribe documentación (evidencia, contrato y una nota en el
ADR), sin código de producto ni comportamiento testeable: no hay ciclo tester/coder, ni mutación, ni
QA de código. Se registra aquí como pide el flujo.

| Tarea | Resultado | Archivo |
| --- | --- | --- |
| 1.1 | Evidencia abierta con fecha, rama, SHA base (`bfaf3983`), enlace a Trello y los cinco criterios, todos pendientes salvo el 3 («en curso») | `docs/evidence/JUP-038-validation.md` |
| 1.2 | Contrato de la petición, respuestas, evidencia, fórmulas y correspondencia con el resultado común de herramientas, con ejemplo calculado a mano | `docs/api/anomaly-explanations.md` |
| 1.3 | Nota fechada en ADR-0020 con la decisión de no registrar herramienta y el aplazamiento del punto 11; el estado y el texto de la decisión no cambian | `docs/adr/ADR-0020-cost-anomaly-episodes.md` |

**Comprobaciones ejecutadas el 2026-10-12** (sobre `feat/JUP-038-explain-anomaly-episodes`, con
`develop` aún en `bfaf3983`):

- `corepack pnpm openspec:validate`: 68 de 68.
- `corepack pnpm jup:check -- --change jup-038-explain-anomaly-episodes` y
  `corepack pnpm jup:cleanup:check` (1301 archivos): correctos.
- `git diff --check`: sin avisos.
- Enlaces relativos y anclas de los tres documentos, con un comprobador propio: 0 rotos.
- Texto sin doble codificación UTF-8 en los tres documentos.

**Ejemplo de 1.2.** Calculado con un script independiente del backend, con aritmética exacta y sin
usar sus constantes: 150.00 EUR de subida absoluta, 37.50 % de subida relativa, 400.00 EUR de
impacto acumulado en 2 días hasta el 2026-09-09 y criticidad P3. Coincide con la salida del ejemplo
ejecutable de `docs/api/anomaly-episodes.md`. Los tres bordes de redondeo del contrato (subida
100.004, subida relativa 20.0002 % e impacto 499.996) están calculados en el mismo script. No se ha
ejecutado todavía ningún código de este change.

**Lo que este grupo no demuestra.** Que el explicador produzca esas cifras (grupo 2), que la ruta
las guarde (grupo 4) o que la interfaz las muestre (grupos 5 a 7). El contrato describe lo acordado,
no comportamiento implementado, y así lo dice su cabecera.

## Grupo 2 — Explicador, fase Red (tareas 2.1 a 2.4)

**Pruebas escritas por el `tester`:** `apps/backend/tests/test_anomaly_explanations.py` (archivo
nuevo, 653 líneas, 75 casos con las parametrizaciones). Cubre el texto completo del ejemplo A frente
a un literal, los bordes de redondeo del contrato (100.004, 20.0002 %, 499.996 y 2000.004), el
redondeo HALF_UP en un solo paso, los cuatro estados con y sin observación, el cierre con fecha en
UTC, la anomalía anterior, USD, las limitaciones en español, el aviso sintético, el servicio nulo,
los datos hostiles (salto de línea, comillas, U+202E, U+200B, U+2028), que no se escribe nada en
registros ni en salida, que no se muta la fotografía, la forma de la evidencia, el identificador
recalculado por el propio test con `hashlib` y diez casos de `ExplanationUnavailable`. Todas las
cifras esperadas están calculadas a mano; el código de producción no actúa como oráculo.

**Interfaz fijada antes del Red** (la implementará el `coder`): `explain_episode(snapshot, *,
tenant_id, explained_at) -> {"content", "anomaly_evidence"}`, `ExplanationUnavailable` y
`LIMITATIONS_ES` (tupla) en `app.services.anomaly_explanations`. Las frases exactas de la respuesta
son las de los literales del archivo de pruebas.

**Evidencia Red** (2026-10-12, imagen `jup054-py-backend`, Python 3.12.15):

```
export MSYS_NO_PATHCONV=1
R="$(cygpath -w "$PWD")"; docker run --rm -v "$R:/repo:ro" -w /work jup054-py-backend sh -c "mkdir -p /work && cp -r /repo/apps /work/apps && cd /work/apps/backend && python -m pytest tests/test_anomaly_explanations.py -q -p no:cacheprovider --tb=line"
```

- Resultado: `75 failed`, 0 pasan. Con `--tb=line` el único motivo es
  `No module named 'app.services.anomaly_explanations'`. Los 75 fallan por separado porque el
  módulo se importa dentro de cada prueba.
- Control, mismo entorno: `tests/test_anomaly_episode_rules.py` y `tests/test_ownership_questions.py`
  siguen en `104 passed, 1 skipped`.
- El orquestador reejecutó el comando y leyó el archivo completo antes de aceptar el Red.

**Resolución de las ambigüedades que señaló el `tester`** (ninguna cambia el alcance aprobado):

1. En USD el texto sigue diciendo «EUR y USD» en la limitación 5, que es texto fijo: se acepta; el
   resto de líneas va en la moneda del episodio.
2. La línea de impacto termina siempre en un punto tras el tramo, también en P2 y P1: se acepta.
3. En `opening`, los importes y porcentajes son cadenas con dos decimales y los umbrales cadenas
   tomadas de `rules`: se acepta y se añade al contrato (`docs/api/anomaly-explanations.md`).
4. `operands` son el texto exacto del `Decimal` recibido (`"2800.00"`, `"500.004"`), sin normalizar:
   al implementar hay que usar `format(valor, "f")` y no `str`, que podría dar notación científica.
5. `closed_at` en la evidencia sale como lo devuelve la API; el texto lo convierte a UTC: se acepta.
6. Limitaciones del episodio distintas de `LIMITATIONS`: no es motivo de `ExplanationUnavailable`;
   solo cambia el identificador. Se acepta.
7. **Sin cubrir:** una fotografía incoherente (operandos que no cuadran con el episodio). La lectura
   de la tarea 3.2 trae las dos partes de una sola sentencia SQL, así que no debería darse; el
   explicador usa los operandos para las cifras y el episodio para lo demás.
8. Reglas con una clave de más se tratan como distintas y dan `ExplanationUnavailable`: se acepta.

**Lo que este Red no demuestra.** Que las pruebas sean correctas contra una implementación real:
nunca se han ejecutado contra una. Si en el Green aparece un fallo atribuible a una prueba, el
`coder` no la toca; se escala al `tester`.

## Grupo 2 — Explicador, fase Green (tarea 2.5)

**Producto creado por el `coder`:** `apps/backend/app/services/anomaly_explanations.py` (228 líneas),
el único archivo de producto del grupo hasta ahora. Importa de `anomaly_episodes.py` y
`ownership_questions.py` sin modificarlos. Ninguna prueba ni otro archivo existente se tocó
(`git status` solo muestra el archivo nuevo y `tasks.md`).

**Evidencia Green** (2026-10-12, mismo comando y entorno que el Red):

- `tests/test_anomaly_explanations.py`: `75 passed` (antes `75 failed`).
- Control: `tests/test_anomaly_episode_rules.py` y `tests/test_ownership_questions.py` siguen en
  `104 passed, 1 skipped`.
- El orquestador reejecutó ambas y leyó el módulo completo.

**Ajuste de tareas.** El esquema de la selección (`app/schemas/anomaly_explanations.py`) pasa de la
2.5 a la 4.6: no tiene pruebas hasta la 4.1 y crearlo ahora sería código sin pruebas.

**Decisiones del `coder` que no estaban en el encargo** (revisadas por el orquestador):

1. `ExplanationUnavailable` también se lanza con un `status` desconocido, con un estado cerrado sin
   `closed_at` o sin `closure_reason`, y con `no_longer_observed` sin fecha. Evita un `TypeError` o un
   texto con «None», que en la ruta sería un 500. **Ninguna prueba lo cubre todavía:** son ramas
   sin test, así que la mutación de la 2.6 las señalará y el `tester` las cubre con casos nuevos en
   un archivo nuevo. Amplían el 409 más allá de los tres casos de la spec; al cubrirlas se añadirá a
   `specs/anomaly-episode-explanation/spec.md` un escenario «Episodio con datos incoherentes».
2. Los tramos de criticidad del texto (500.00 y 2000.00) se leen de `episode["rules"]["severity"]`
   cortando su texto (`"> X"`, `"A to B"`, `"< Y"`). Es seguro porque `rules` debe ser igual a `RULES`
   antes de llegar ahí; cumple la decisión 5 del diseño (los umbrales salen de las reglas del
   episodio).
3. `triggers` se evalúa con precisión 120 para que `O × 7` y los productos no se redondeen con la
   precisión por defecto (28).
4. `LIMITATIONS` no se importa: la evidencia usa `LIMITATIONS_ES` y conserva las limitaciones en
   inglés de `episode["limitations"]`.
5. El identificador de la anomalía anterior se escribe sin `display_label`: tiene formato
   `anomaly-<hex>` y la prueba espera texto plano.

**Observación para la tarea 3.1.** `_utc(closed_at)` supone un `datetime` con zona horaria, que es lo
que devuelve CockroachDB. Con un `datetime` sin zona, `astimezone` lo interpretaría en la hora local
del proceso. La prueba con CockroachDB real (3.1) debe incluir un episodio cerrado para confirmarlo.

**Lo que este Green no demuestra todavía.** Que las pruebas maten mutantes (2.6), que la regresión
completa y el lint pasen (DoD) ni el veredicto de QA. El grupo sigue abierto.

## Grupo 2 — Explicador, mutación (tarea 2.6)

**Herramienta.** `mutmut 2.5.1` en el contenedor Python 3.12.15 (no hay `pipx` en esta máquina),
acotado al único archivo de producto del grupo, más 18 mutantes manuales propios que mutmut no genera
(borrado de guardas, hash sin el cliente, criticidad sobre la cifra redondeada, precisión por defecto,
`str` en lugar de `format`, entre otros), con control sin mutar. El arnés manual vive en el espacio de
trabajo temporal y no se versiona.

**Antes de la remediación** (solo `test_anomaly_explanations.py`, 75 pruebas):

- mutmut: 256 mutantes, 253 muertos, 3 supervivientes (31, 34 y 67).
- Manuales: 13 muertos de 16 aplicados; sobrevivían el borrado de las tres guardas sin prueba y `str`
  en lugar de `format(…, "f")`. Un mutante no se aplicó por una ancla ambigua y se corrigió.

**Remediación** por el `tester`, en un archivo nuevo (el anterior está bloqueado):
`apps/backend/tests/test_anomaly_explanations_mutants.py`, 20 pruebas: guardas de estado desconocido,
cierre incompleto y no observada sin fecha (con control positivo); aliasing entre la evidencia y la
fotografía en los dos sentidos; operandos con exponente (`2.8E+3`) sin notación científica; y un caso
de importes de 30 cifras con valores esperados calculados con `fractions.Fraction` y un HALF_UP hecho
a mano, donde una subida relativa exacta de 50.005 delata la precisión por defecto.

**Después** (95 pruebas, reejecutado por el orquestador el 2026-10-12):

- Contra el código real: `95 passed` (75 existentes y 20 nuevas).
- mutmut: **256 mutantes, 255 muertos, 1 superviviente** (el 31).
- Manuales: **18 de 18 muertos**, control `95 passed`.

**Superviviente justificado.** El mutante 31 cambia `_PRECISION = 120` por `121`. Es equivalente: la
precisión solo tiene que ser holgada para que `O × 7`, la división entre 7 y el porcentaje no pierdan
cifras antes del único redondeo, y una cifra más de 120 no cambia ningún resultado observable. El
mutante `_PRECISION = 28` sí está matado, por la prueba de 30 cifras.

**Spec actualizada.** Al cubrir las guardas que el `coder` añadió se añade el escenario «Episodio con
datos incoherentes» a `specs/anomaly-episode-explanation/spec.md` (ahora 34 escenarios en esa spec y
43 en total; el bloque `Human Approval` conserva las cifras del gate, 33 y 42) y se amplía la frase
del 409 en el contrato. Es un refinamiento aditivo del mismo requisito: no cambia el alcance aprobado.

**Lo que esta mutación no demuestra.** Las pruebas se ejecutan solo contra el explicador puro: el
formato real de las filas de CockroachDB (p. ej. un `closed_at` con zona horaria) se comprueba en el
grupo 3. La regresión completa, el lint y el veredicto de QA del grupo siguen pendientes.

## Grupo 2 — Definition of Done y veredicto de QA

**DoD** (2026-10-12, sobre `18adbe9f`). `check-dod.mjs` ejecuta `corepack pnpm test` en Windows, donde
fallan 145 pruebas ajenas de JUP-047 (`socketpair` de asyncio frente a su guarda de red, `RF-105-004`,
ya rojas en `develop`). Para no mezclarlas con este cambio, cada control se ejecutó por separado:

| Control | Comando | Resultado |
| --- | --- | --- |
| Regresión backend completa, HEAD | `python -m pytest tests` en `jup054-py-backend` (Python 3.12.15), con `apps`, `docs`, `fixtures`, `scripts`, `infra`, `tools`, `packages` y `openspec` copiados | **1350 passed, 118 skipped, 0 failed** (134 s) |
| Control, `develop` en `bfaf3983` | mismo comando sobre `git archive bfaf3983` | 1255 passed, 118 skipped, 0 failed |
| Diferencia | | +95 pasan = las 75 + 20 pruebas nuevas; omitidas iguales |
| Lint backend | `python -m compileall -q app` | OK |
| Lint frontend | `corepack pnpm --filter @finops/frontend lint` | exit 0 (el grupo no toca el frontend) |
| Type-check frontend | `corepack pnpm --filter @finops/frontend typecheck` | exit 0 |
| Escaneo de secretos | patrones de `check-dod.mjs` sobre las 2588 líneas añadidas desde `bfaf3983` | 0 hallazgos |

No se ejecutó la suite del frontend ni la del processor: el grupo no toca ninguno de los dos. Las
pruebas opt-in con CockroachDB, RabbitMQ y pgvector reales quedan omitidas, como en CI (`RF-096-004`).
La primera ejecución falló en la recolección porque la suite lee `docs/` y `fixtures/` de la raíz del
repositorio; se repitió copiándolos, igual para HEAD y para el control.

**Veredicto del agente `qa`: `accept`.** Reejecutó las 95 pruebas del grupo (`95 passed`) y comprobó
el historial (el Red solo trae pruebas, el Green solo el módulo; `test_anomaly_explanations.py` no se
modificó tras el Red; no cambió ningún archivo ajeno al grupo), la ausencia de `skip`/`xfail`, que las
pruebas validan comportamiento real con oráculo independiente, el alcance del módulo y los comentarios
en español. No reejecutó la regresión completa, el lint, el type-check ni mutmut: usó los resultados
de arriba.

**Observaciones no bloqueantes del QA**, aceptadas:

1. «No menciona despliegues, uso, tráfico ni ahorro como hechos» solo queda cubierto por la igualdad
   exacta del texto con el literal, sin una aserción negativa explícita sobre esas palabras.
2. **Supuestos de tipo que deben respetar los grupos 3 y 4** y fijarse con pruebas allí:
   - la fotografía tiene la forma de `episode_payload` **sin `_order`** (el módulo no lo quita y
     entraría en la evidencia y en el hash);
   - `start_date`, `impact_through_date` y `no_longer_observed_on` son `date`;
   - `closed_at` y `explained_at` llevan zona horaria (sin ella, `astimezone` usaría la hora local);
   - los tres operandos son `Decimal` y salen de la misma sentencia SQL que el episodio: el explicador
     valida que cumplan la regla, no que cuadren con él;
   - el texto exacto del `Decimal` (escala y ceros finales) entra en `operands` y en el hash, así que
     la escala de la columna afecta al identificador; hay que comprobar que dos lecturas del mismo
     episodio dan el mismo `id`;
   - `tenant_id` es `str`.
3. La ruta debe convertir `ExplanationUnavailable` en 409 antes de guardar ningún mensaje; un
   `KeyError` o `TypeError` por una fotografía mal formada sería un 500 (cobertura del grupo 4).

**Estado del grupo 2:** tareas 2.1 a 2.6 hechas, mutación sin supervivientes salvo el equivalente
justificado, DoD en verde y QA en `accept`.

## Grupo 3 — Lectura con operandos exactos, fase Red (tarea 3.1)

**Entorno.** CockroachDB v24.1.11 desechable en un contenedor propio (`jup038-crdb`, puerto 36415, almacén
en disco con caché de 256 MiB porque había 1.8 GB de RAM libres), marcado con
`cluster.organization = 'processor-integration-tests'` como exigen las guardas de las pruebas. Las
pruebas se ejecutan en `jup054-py-backend` (Python 3.12.15) con `--network container:jup038-crdb` y el
código copiado dentro del contenedor, no desde un montaje de Windows. **Control del entorno:**
`tests/test_anomaly_episode_store.py` y `tests/test_anomaly_episode_api.py`, que ya existían, dan
`82 passed` y 0 omitidas contra ese nodo.

**Pruebas escritas por el `tester`:** `apps/backend/tests/test_anomaly_episode_snapshot.py` (archivo
nuevo, 234 líneas, 13 pruebas): el `episode` es idéntico a `fetch_anomaly_episode` y sin `_order`; tipos
`date`, `datetime` con zona horaria y `Decimal`; operandos iguales a las columnas de la tabla leídas con
SQL directo, por valor y por texto; importes con más de dos decimales (500.004 y 700.028, mientras la API
muestra 500.00 y 100.00); marca sintética solo con una ingesta completada del mismo cliente; aislamiento
(`None` para otro cliente y para un id inexistente); la lectura no cambia episodios ni
`anomaly_detection_state`; **una sola sentencia SQL**, contada con el evento `before_cursor_execute`;
episodio cerrado con `closed_at` con zona horaria; tres integraciones con `explain_episode` sobre la
fotografía real (serie base, nota de redondeo y episodio cerrado con fecha UTC); y estabilidad del `id`
de evidencia entre dos lecturas.

**Evidencia Red** (2026-10-12):

```
S="C:/Users/victo/AppData/Local/Temp/claude/c--Users-victo-Pontia-tfm-economicon/1f99f606-320c-4e2b-aaaa-58c034f436e4/scratchpad"; R="$(cygpath -w "$PWD")"
docker run --rm --network container:jup038-crdb -v "$R:/repo:ro" -v "$(cygpath -w "$S"):/scr:ro" -w /work jup054-py-backend sh /scr/crdb-test.sh tests/test_anomaly_episode_snapshot.py
```

- Resultado: `13 failed`, 0 pasan, **0 omitidas**. Los 13 por el mismo motivo,
  `AttributeError: 'Database' object has no attribute 'fetch_anomaly_episode_snapshot'`; ninguno por la
  preparación de datos (series, detección e ids ya funcionan antes de llamar al método nuevo).
- El orquestador reejecutó el comando y leyó el archivo.

**Ambigüedades señaladas por el `tester`** (sin cambiar el contrato):

1. La prueba de una sola sentencia exige exactamente 1 ejecución de cursor. Si el `coder` usara una
   transacción explícita o aislamiento SERIALIZABLE, el driver podría emitir sentencias extra: se
   resuelve con una lectura simple de un solo `SELECT` (`engine.connect()`).
2. `status_changed_at` es `None` en un episodio sin cambios; solo se exige zona horaria cuando existe.
3. `fetch_anomaly_episode` ya devuelve el payload sin `_order` (lo quita `order_payloads`).

**Lo que este Red no demuestra.** Que las pruebas sean correctas contra una implementación real; se
sabrá en el Green. El nodo es de un solo proceso y no prueba concurrencia.

## Grupo 3 — Lectura con operandos exactos, fase Green (tareas 3.2 y 3.3)

**Producto del `coder`:** `Database.fetch_anomaly_episode_snapshot` en `apps/backend/app/db/database.py`,
un único bloque aditivo de 30 líneas colocado tras `fetch_anomaly_episode` (`git diff --stat`: 1 archivo,
30 inserciones). Una sola sentencia `SELECT e.*, EXISTS (…) AS includes_synthetic_data FROM anomaly_episodes e
WHERE e.tenant_id = … AND e.id = …`, con `engine.connect()` y sin transacción, aislamiento ni reintentos; el
`episode` sale de `episode_payload` y `order_payloads`, igual que `fetch_anomaly_episode`.

**El `coder` se paró con 12 de 13** y escaló una prueba que consideraba incorrecta, que es lo que debe
hacer. El orquestador lo verificó: `azure_cost_records.pretax_cost` es `NUMERIC(38,12)` y la detección guarda
sumas con esa escala, de modo que las columnas del episodio valen `2800.000000000000`, `500.004000000000` y
`700.028000000000`. La prueba 2 exigía que el texto del operando coincidiera con el de la columna y la 3 exigía
el literal `"500.004"`: incompatibles entre sí.

**Decisión de Victor, 2026-10-12.** (a) Los operandos de la evidencia se escriben **tal como los guarda la
tabla**, sin normalizar, con 12 decimales; es el valor exacto, coincide con el diseño aprobado y no añade
código. El identificador depende de ese texto, que es estable porque la columna tiene una escala fija. (b)
Corrección de la prueba 13 con un **bypass puntual del candado del harness**, autorizado expresamente por
Victor: no se tocó la configuración de los hooks y solo se cambiaron dos líneas de
`apps/backend/tests/test_anomaly_episode_snapshot.py`.

**Adenda a la regla «no se edita ninguna prueba ya commiteada».**

- Qué cambió: las dos aserciones `format(operando, "f") == "500.004"` y `== "700.028"` pasan a comparar con el
  texto de la propia columna (leída con SQL directo, como el resto del archivo) y a exigir que empiece por
  `500.004` y `700.028`. Es +8/−2 líneas, con un comentario que lo explica.
- Qué no cambió: las otras 12 pruebas y el resto de la prueba 13 (valores `Decimal` y payload redondeado).
- Por qué es legítimo: el literal ignoraba la escala real de la columna; lo que protege la prueba (que no se
  pierde ningún decimal significativo y que el texto es el exacto de la tabla) se mantiene y gana precisión.
- No se debilitó para pasar: el método no cambió entre el Red y esta corrección.

**Evidencia Green** (2026-10-12, CockroachDB real, 0 omitidas):

- `tests/test_anomaly_episode_snapshot.py`: `13 passed` (antes `13 failed`).
- Junto a `test_anomaly_episode_store.py`, `test_anomaly_episode_api.py` y las dos del explicador:
  `190 passed` (13 + 82 + 95).
- **3.3:** las pruebas se ejecutaron contra un CockroachDB v24.1.11 desechable (`jup038-crdb`), con el
  comando del Red. CI las omite (`RF-096-004`): sin `JUP086_COCKROACH_TEST_URL` los `skip` de las guardas las
  dejan fuera, así que este resultado no está cubierto por CI.

**Contrato.** Se añade al de `docs/api/anomaly-explanations.md` que `operands` conserva la escala de la
columna (`2800.000000000000`) y que los ejemplos usan dos decimales por claridad.

**Pendiente del grupo 3:** mutación sobre el método, DoD y QA.

## Grupo 3 — Lectura con operandos exactos, mutación

**Herramienta.** `mutmut` no se usa aquí: el método es un único bloque de 30 líneas dentro de
`database.py` (800 líneas), y mutar el archivo entero costaría mucho tiempo y ruido (cientos de
mutantes de métodos ajenos) para medir 30 líneas. Se usan 14 **mutantes manuales dirigidos** al método,
cada uno aplicado solo dentro de su texto (así un fragmento repetido en `fetch_anomaly_episode_list` no
se confunde con el del método nuevo), con un control sin mutar al principio. Corren contra CockroachDB
real, con el código copiado dentro del contenedor; el arnés edita la copia y nunca el repositorio. Es
una muestra dirigida, no un barrido: cubre el filtro por cliente, los tres criterios de la marca
sintética, el `None`, la exactitud de cada operando, la clave `_order` y el número de sentencias.

**Antes de la remediación** (13 pruebas): 12 muertos de 14. Sobrevivían:

1. **`COALESCE(request->'synthetic' = 'true'::JSONB, false)` → `(request->'synthetic' IS NOT NULL)`.**
   Hueco real: una ingesta completada con `{"synthetic": false}`, `"true"` (cadena), `null`, `1` o sin la
   clave contaría como sintética y el explicador avisaría de datos de demostración que no lo son.
2. **Aislamiento SERIALIZABLE** (mutante informativo, se añadió para saber si la prueba de una sola
   sentencia lo detecta).

**Remediación** por el `tester`, en un archivo nuevo (el anterior está commiteado):
`apps/backend/tests/test_anomaly_episode_snapshot_mutants.py`, 9 pruebas: siete valores del campo que
no son el booleano `true` (`false`, `"true"`, `null`, `1`, `"yes"`, otra clave y `{}`), un control positivo
con `{"synthetic": true}` y un caso mixto con dos ingestas completadas (basta una sintética).

**Después** (22 pruebas, reejecutado por el orquestador el 2026-10-12, CockroachDB real, 0 omitidas):

- Control sin mutar: `22 passed`.
- **13 de 14 mutantes muertos.** El mutante 1 muere en el caso `{"synthetic": false}`.

**Superviviente justificado.** El aislamiento `SERIALIZABLE` no produce ninguna diferencia observable:
CockroachDB ejecuta todas las transacciones en `SERIALIZABLE` por defecto, así que el resultado es el mismo
y no hay comportamiento que probar. Es equivalente.

**Lo que esta mutación no demuestra.** Es una muestra dirigida de 14 mutantes sobre un método, no un
barrido con una herramienta. No cubre concurrencia (el nodo es de un solo proceso). La regresión
completa, el lint y el veredicto de QA del grupo siguen pendientes.

## Grupo 3 — Definition of Done y veredicto de QA

**DoD** (2026-10-12, sobre `35cf49c0`). Como en el grupo 2, `corepack pnpm test` en Windows no es fiable
(145 fallos ajenos de JUP-047, `RF-105-004`), así que se ejecutó cada control por separado. Este grupo toca
`database.py`, que usa casi todo el backend, por lo que se hizo además una regresión con la base real:

| Control | Resultado |
| --- | --- |
| Regresión backend completa **como CI** (sin base de datos real), Python 3.12.15 | **1350 passed, 140 skipped, 0 failed** (129 s). Respecto a `develop` (1255 y 118): +95 del explicador; las 22 nuevas de este grupo necesitan CockroachDB y se omiten sin él, de ahí 118 + 22 = 140 |
| Regresión backend completa **con CockroachDB v24.1.11 real** (`jup038-crdb`) | **1469 passed, 21 skipped, 0 failed** (201 s). Las 21 omitidas son integraciones externas (RabbitMQ, pgvector…); 1469 + 21 = 1490 = 1350 + 140 |
| Lint backend | `python -m compileall -q app` OK |
| Escaneo de secretos | 490 líneas añadidas desde `a75817fe`, 0 hallazgos |

No se repitieron `eslint` ni `tsc` del frontend: el grupo no cambia ningún archivo del frontend desde el DoD
del grupo 2 (`git diff --stat` solo muestra `database.py`, dos archivos de pruebas, el contrato, `review.md`
y `tasks.md`). No se ejecutó un control sobre `develop` con la base real porque no hubo ningún fallo que
atribuir. Con CockroachDB activado la ejecución incluye las pruebas opt-in de aislamiento, episodios y
tenants, que CI omite (`RF-096-004`).

**Veredicto del agente `qa`: `accept`.** Reejecutó las 22 pruebas del grupo contra CockroachDB real
(`22 passed`, 0 omitidas) y comprobó: el cambio de producto es un único bloque aditivo de 30 líneas, una
sola sentencia, siempre filtrada por cliente y de solo lectura, sin nada más allá de lo que piden las
pruebas; el producto no cambió entre el Green y el último commit; el oráculo de operandos es independiente
(SQL directo a la tabla); no hay `skip` ni `xfail`; el diff del bypass del candado es exactamente +8/−2 y no
debilita la prueba (sigue detectando la pérdida de un decimal significativo); y los supuestos de tipo que el
QA del grupo 2 anotó para este grupo quedan fijados con pruebas (sin `_order`, `date` puro, `closed_at` con
zona horaria, `Decimal` de la misma sentencia, `id` estable entre lecturas). No reejecutó las regresiones
completas: usó las cifras de arriba.

**Observaciones no bloqueantes del QA**, aceptadas:

1. Estas 22 pruebas se omiten en CI (`RF-096-004`): la lectura no tiene red de seguridad automática allí.
   La ruta del grupo 4 debe llevar sus propias pruebas con un doble en memoria (que sí corren en CI), y el
   DoD final lo recordará.
2. La estabilidad del `id` solo se comprueba entre dos lecturas seguidas. No se comprueba que una nueva
   ejecución de la detección, sin datos nuevos, deje los operandos con el mismo texto. Conviene cubrirlo en
   la ruta (tarea 4.5, con la base real) porque el `id` se muestra al usuario.
3. La mutación fue dirigida (14 mutantes manuales), no un barrido con herramienta, y no hay prueba de
   concurrencia: ya constaba en la sección de mutación.

**Estado del grupo 3:** tareas 3.1 a 3.3 hechas, mutación con un único superviviente equivalente justificado,
DoD en verde y QA en `accept`. El contenedor `jup038-crdb` sigue en marcha porque el grupo 4 (tarea 4.5) lo
necesita; se apagará al cerrar ese grupo.

## Grupo 4 — Ruta del asistente, fase Red (tareas 4.1 a 4.4)

El grupo se parte en dos Red para tener commits pequeños: este (4.1 a 4.4, pruebas que **sí corren en CI**
porque usan SQLite y un doble de la lectura) y después la 4.5 (recorrido con CockroachDB real, que CI
omite). El Green (4.6) cubre las dos.

**Contrato fijado antes del Red** (lo implementará el `coder`): esquema `AnomalySelection` en
`app/schemas/anomaly_explanations.py` (`episode_id` con `^anomaly-[0-9a-f]{64}$` por coincidencia completa,
sin campos adicionales); `MessageCreateRequest.anomaly_query` y rechazo de las dos selecciones a la vez;
rama de la ruta con el orden de la decisión 8 (conversación, lectura con el cliente de la sesión, 404
`anomaly_episode_not_found`, explicador, 409 `anomaly_explanation_unavailable`, y solo entonces se guardan
los dos mensajes).

**Pruebas escritas por el `tester`** (archivos nuevos, 72 pruebas):

- `apps/backend/tests/test_anomaly_explanation_schema.py` (4.1, 45 pruebas, sin HTTP): 26 ids inválidos
  (vacío, longitudes, mayúsculas hex, `\n` final, espacios, unicode, tipos no `str`…), campos adicionales,
  exclusión con `ownership_query` y que las peticiones sin `anomaly_query` validan como hoy.
- `apps/backend/tests/test_anomaly_explanation_api.py` (4.2 a 4.4, 27 pruebas, SQLite con auténticas
  autenticación y mensajes y un doble de `fetch_anomaly_episode_snapshot` que devuelve una fotografía real
  construida con el ayudante del explicador): 201 con la forma de metadatos exacta y la evidencia igual a la
  del explicador real con el cliente de la sesión; usuario con dos clientes; el texto de la pregunta no filtra
  ni autoriza nada; 404 de anomalía (otro cliente e inexistente, cuerpos idénticos), 409, 422, 401/403 y 404
  de conversación sin leer ninguna anomalía y sin guardar nada; recarga de una conversación mixta
  (documental, propiedad y anomalía) con cada evidencia separada; nada del cliente en los registros; servicio
  y motivo hostiles escapados en una línea.
- Una prueba de las 72 **pasa de entrada** a propósito: `test_sin_sesion_o_con_cliente_ajeno_se_rechaza_antes_de_leer_nada`
  (401 sin token y 403 con cliente ajeno). Fija un comportamiento que ya existe, porque las dependencias
  resuelven 401/403 antes de validar el cuerpo, y protege que la rama nueva no lo altere.
- Para que las pruebas de rechazo no pasen por el motivo equivocado (hoy el modelo ya rechaza
  `anomaly_query` como campo desconocido), cada una exige antes que la misma petición bien formada se acepte.

**Evidencia Red** (2026-10-12, como CI: sin base de datos real, Python 3.12.15):

```
S="C:/Users/victo/AppData/Local/Temp/claude/c--Users-victo-Pontia-tfm-economicon/1f99f606-320c-4e2b-aaaa-58c034f436e4/scratchpad"; R="$(cygpath -w "$PWD")"
docker run --rm -v "$R:/repo:ro" -v "$(cygpath -w "$S"):/scr:ro" -w /work jup054-py-backend sh /scr/ci-test.sh tests/test_anomaly_explanation_schema.py tests/test_anomaly_explanation_api.py
```

- Resultado: **`71 failed, 1 passed`**, 0 omitidas. Motivos, contados por el orquestador: 33 por
  `ModuleNotFoundError` (`app.schemas.anomaly_explanations`), 21 + 4 por un 422 `Invalid request value`
  donde se esperaba 201 o 404 (el campo `anomaly_query` no existe), 11 + 1 por la validación de
  `MessageCreateRequest` (`ValidationError` en el control previo y campo ausente en `model_fields`).
- Control, mismo entorno: `test_ownership_questions.py`, `test_tenant_isolation_api.py` y
  `test_domain_metrics.py`: `71 passed, 3 skipped` (los 3 omitidos son del CockroachDB opt-in), igual que antes.
- El orquestador reejecutó el comando, agrupó los motivos y comprobó que no hay `skip` ni `xfail`.

**Decisiones del `tester`** (contrato sin cambios): la pregunta documental del caso mixto usa
`citation_record()` en lugar de `search_chunks=[]`, para que `source_citations` no esté vacío y se compruebe
de verdad que la evidencia documental queda separada; los argumentos del doble se leen por posición o por
nombre; la prueba del hash compara con `explain_episode` normalizado con `json.loads(json.dumps(...))`.

**Lo que este Red no demuestra.** Que las pruebas sean correctas contra la implementación real; que la
métrica no suba en los fallos solo es significativo cuando la rama exista. Falta el recorrido con
CockroachDB real (4.5).

## Grupo 4 — Ruta del asistente, fase Red con CockroachDB real (tarea 4.5)

**Pruebas escritas por el `tester`:** `apps/backend/tests/test_anomaly_explanation_cockroach.py` (archivo
nuevo, 343 líneas, 9 pruebas, opt-in). Recorren la ruta sin ningún doble de la lectura: carga real de
costes, detección real por HTTP, episodio guardado en CockroachDB, `fetch_anomaly_episode_snapshot` real,
explicador de producción, mensajes guardados y recargados por la API. Los únicos dobles son los de la
fixture `api` en fronteras externas (embeddings y almacén vectorial), para comprobar que no se usan.
Cubren: el recorrido completo con operandos de 12 decimales iguales al texto de la tabla; aislamiento (otro
cliente e id inexistente dan el mismo 404, sin guardar nada ni cambiar episodio o marca de agua); estabilidad
del identificador, incluido un `detect` intermedio que da `up_to_date` (**recomendación del QA del grupo 3**);
cambio de estado (la explicación nueva cambia y la guardada conserva «Nueva»); episodio cerrado con fecha UTC
y motivo; aviso de datos sintéticos con la ingesta marcada y sin él; un 409 real con `rules_version` cambiada
por SQL; servicio hostil escapado; y una serie en USD sin conversión.

**Evidencia Red** (2026-10-12, CockroachDB v24.1.11 real y desechable, `jup054-py-backend`, Python 3.12.15):

```
docker run --rm --network container:jup038-crdb -v "$R:/repo:ro" -v "$(cygpath -w "$S"):/scr:ro" -w /work jup054-py-backend sh /scr/crdb-test.sh tests/test_anomaly_explanation_cockroach.py
```

- Resultado: **`9 failed`**, 0 omitidas. Las 9 por el mismo motivo, contado por el orquestador sin recorte:
  `AssertionError` con el cuerpo `{"detail":[{"type":"validation_error", … "Invalid request value"}]}`, es
  decir, `assert 422 == 201` porque `anomaly_query` aún es un campo desconocido. Antes de ese punto la
  preparación (carga de la serie, `detect` con 200 y `GET` del episodio) ya funciona.
- Las pruebas de fallo (404 y 409) exigen antes un 201 con una petición equivalente bien formada, para no
  pasar por vacuidad. Los pasos posteriores al primer 201 los comprobó el `tester` con una sonda temporal
  contra el nodo real, ya borrada: operandos `2800.000000000000`, `550.000000000000` y `1050.000000000000`;
  `None` para otro cliente e id inexistente; `PATCH` a `investigating` y `resolved` con `closed_at`; y que los
  `UPDATE` de la ingesta y de `rules_version` surten efecto.
- Control: `tests/test_anomaly_episode_api.py` (54 pruebas del precedente) sigue en `54 passed`.
- **Como CI, sin la variable:** `9 skipped` («JUP086_COCKROACH_TEST_URL absent») y ningún fallo.

**Ambigüedades del `tester`** (resueltas por el orquestador):

1. Fechas de `evidence["episode"]`: el explicador las escribe con `isoformat()` (`+00:00`) y la API con `Z`.
   Es una imprecisión del contrato, no un defecto. Se **documenta en `docs/api/anomaly-explanations.md`**
   (mismo instante, distinto desfase) en lugar de forzar un formato. La prueba 1 compara los campos de fecha y
   hora como instantes y el resto literalmente.
2. En USD el texto sigue diciendo «EUR y USD» en la limitación fija: la prueba busca una cifra seguida de `EUR`.
3. La prueba de estabilidad ignora la línea `Fotografía…` (lleva la hora de cada petición). Si cambiara ese
   prefijo habría que ajustarla.

**Lo que este Red no demuestra.** Que las pruebas sean correctas contra la implementación real. Estas 9 se
omiten en CI (`RF-096-004`); la evidencia es la ejecución local contra el nodo desechable.

## Grupo 4 — Ruta del asistente, fase Green (tarea 4.6)

**Producto del `coder`** (`git diff --stat`: 46 inserciones, 0 borrados, más un archivo nuevo):

- `apps/backend/app/schemas/anomaly_explanations.py` (nuevo): `AnomalySelection`, sin campos adicionales y con
  `episode_id` estricto (no coacciona otros tipos a `str`). Se valida con `re.fullmatch` en un
  `field_validator` y no con `Field(pattern=…)`: ese patrón lo evalúa el motor de Rust de pydantic, cuyo
  comportamiento de `$` difiere del de `re`, y con `re` un `$` aceptaría un `\n` final. Las pruebas del `\n`
  final, mayúsculas, unicode y `int` pasan.
- `apps/backend/app/schemas/assistant.py` (+13): `anomaly_query` y un `model_validator` que rechaza enviarlo
  junto a `ownership_query`.
- `apps/backend/app/api/routes/assistant.py` (+33): rama nueva entre el 404 de conversación y la rama de
  propiedad, con el orden de la decisión 8: lectura con el cliente de la sesión, 404
  `anomaly_episode_not_found`, explicador, 409 `anomaly_explanation_unavailable` y **solo entonces** se
  guardan los dos mensajes. No se llama a embeddings ni al almacén vectorial y no se registra nada del
  episodio.

**Ajuste pedido por el orquestador.** El `coder` había modificado la línea
`from pydantic import BaseModel, ConfigDict, Field, StringConstraints`, y la PR #121 (JUP-035) modifica
exactamente esa misma línea (añade `field_validator`). Para que el diff sea puramente aditivo y ese conflicto
no exista, `model_validator` entra ahora en una línea de import independiente. Queda el detalle de estilo de
dos líneas `from pydantic import …` separadas; el repositorio no tiene linter de orden de imports (el lint del
backend es `compileall`).

**Evidencia Green** (2026-10-12, reejecutada por el orquestador tras el ajuste):

- Como CI, sin base de datos real: **`238 passed, 3 skipped`** (esquema 45 + API 27 + ownership, aislamiento,
  métricas y las 95 del explicador). Los 3 omitidos son preexistentes (`test_ownership_questions.py:363` y
  `test_tenant_isolation_api.py:209` y `:224`) y necesitan `JUP086_COCKROACH_TEST_URL`.
- Con CockroachDB v24.1.11 real: **`113 passed`**, 0 omitidas (incluye las 9 de
  `test_anomaly_explanation_cockroach.py` más lectura, mutantes de la lectura, API y almacén de episodios).
- Antes: `71 failed, 1 passed` (CI) y `9 failed` (CockroachDB).
- El orquestador leyó el diff completo de producto.

**Conflicto previsto con JUP-035.** Las PR #120 y #121 también modifican `routes/assistant.py` y
`schemas/assistant.py`. Los bloques añadidos aquí no tocan ninguna línea existente, así que el conflicto es
de contexto adyacente (los mismos puntos de inserción), no de líneas editadas. Se medirá con `git merge-tree`
en la tarea 8.4.

**Pendiente del grupo 4:** mutación (4.7), regresión completa (4.8), DoD y QA.
