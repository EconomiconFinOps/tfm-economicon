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

## Grupo 4 — Ruta del asistente, mutación (tarea 4.7)

**Herramientas.** `mutmut 2.5.1` sobre el esquema nuevo (`app/schemas/anomaly_explanations.py`, 11 mutantes) y
22 **mutantes manuales dirigidos** a la rama nueva de `routes/assistant.py` y al validador de exclusión de
`schemas/assistant.py`. Cada mutación manual se aplica solo dentro de su región (la rama de anomalías o el
validador) para que un fragmento repetido en la rama de propiedad no se confunda con el de la rama nueva;
hay un control sin mutar al principio y el arnés trabaja sobre una copia dentro del contenedor, con
CockroachDB real para que corran también las 9 pruebas opt-in. Es una muestra dirigida, no un barrido: cubre
el cliente de la sesión, los códigos y estados del 404 y del 409, que no se guarde nada antes de explicar, la
métrica (omitida y duplicada), embeddings, registros, los metadatos de cada mensaje, el contexto recuperado y
la exclusión entre las dos selecciones.

**Primera pasada** (72 pruebas de CI y 9 de CockroachDB): manuales 20 de 22 muertos; `mutmut` 8 de 11.

- **Mutante «se registra el servicio del episodio»: falso superviviente, defecto del mutante.** El mutante
  escribía `logger.info(…, service=…)`, pero `_add_service_name` (`app/core/logging.py`) **sobrescribe** la
  clave `service` con `"backend"`, así que el nombre del cliente nunca llegaba a la salida. Rehecho con otra
  clave (`afectado=`), la prueba `test_servicio_y_motivo_de_cierre_del_cliente_no_salen_en_los_registros` lo
  mata: la prueba de que el nombre no se filtra es sólida.
- **Mutante 5 de `mutmut`: `Field(strict=True)` → `Field(strict=False)`.** Hueco real: el modo laxo de
  pydantic decodifica `bytes` y `bytearray` a `str`, y ninguna prueba los enviaba.

**Remediación** por el `tester`, en un archivo nuevo (los anteriores están commiteados):
`apps/backend/tests/test_anomaly_explanation_schema_mutants.py`, 11 pruebas: `bytes` y `bytearray` con un
identificador por lo demás válido se rechazan, tanto en `AnomalySelection` como a través de
`MessageCreateRequest.anomaly_query` (con control positivo con `str`); otros tipos laxos (`int`, `float`,
`Decimal`, `bool`, `None`, lista) se rechazan; y una subclase de `str` con un identificador válido se acepta.
Contra el mutante, los 4 casos de bytes fallan con `DID NOT RAISE`.

**Segunda pasada** (92 pruebas, reejecutada por el orquestador el 2026-10-12, CockroachDB real):

- Control sin mutar: `92 passed`.
- `mutmut`: **11 mutantes, 9 muertos, 2 supervivientes** (el 9 y el 11, justificados abajo).
- Manuales: **21 de 22 muertos**; sobrevive el informativo «hora de la explicación sin zona».

**Supervivientes justificados:**

1. **`mutmut` 9: quitar `@classmethod` del validador.** Equivalente: `field_validator` de pydantic v2 envuelve la
   función como método de clase internamente, y el comportamiento es el mismo con o sin el decorador.
2. **`mutmut` 11: cambiar el texto del `ValueError`.** El mensaje nunca es observable: el 422 de la API está
   saneado (`Invalid request value`) y el texto no forma parte del contrato.
3. **Manual «hora de la explicación sin zona» (`datetime.now()` en lugar de `datetime.now(timezone.utc)`).**
   Equivalente en la práctica: el explicador pasa la hora con `astimezone`, que interpreta una hora sin zona
   como local y la convierte al mismo instante UTC; solo difiere en la ambigüedad de un cambio de hora de
   verano. El código usa una hora con zona UTC a propósito. No se persigue con una prueba.

**Lo que esta mutación no demuestra.** Es una muestra dirigida (11 de `mutmut` y 22 manuales), no un barrido
de todo `routes/assistant.py` ni de `schemas/assistant.py`; no hay prueba de concurrencia y el nodo de
CockroachDB es de un solo proceso. La regresión completa (4.8), el DoD y el veredicto de QA del grupo siguen
pendientes.

## Grupo 4 — Regresión completa (4.8), Definition of Done y veredicto de QA

**DoD** (2026-10-12, sobre `367e96f0`). Igual que en los grupos 2 y 3, `corepack pnpm test` en Windows no es
fiable (145 fallos ajenos de JUP-047, `RF-105-004`), así que cada control se ejecutó por separado:

| Control | Resultado |
| --- | --- |
| Regresión backend completa **como CI** (sin base real), Python 3.12.15 | **1433 passed, 149 skipped, 0 failed** (132 s). Respecto al cierre del grupo 3 (1350 y 140): +83 pasan (45 + 27 + 11 de CI) y +9 omitidas (las de CockroachDB) |
| Regresión backend completa **con CockroachDB v24.1.11 real** | **1561 passed, 21 skipped, 0 failed** (198 s). Las 21 omitidas son integraciones externas; 1561 + 21 = 1582 = 1433 + 149 |
| Pruebas ya existentes (ownership, aislamiento, métricas, episodios) | Pasan **sin editarlas** (`git diff e68e3f6d..HEAD -- apps/backend/tests` solo contiene archivos nuevos) |
| Lint backend | `python -m compileall -q app` OK |
| Escaneo de secretos | 1314 líneas añadidas desde `e68e3f6d`, 0 hallazgos |

No se repitieron `eslint` ni `tsc`: el grupo no toca el frontend. No se ejecutó un control sobre `develop`
porque no hubo ningún fallo que atribuir. Las 9 pruebas de `test_anomaly_explanation_cockroach.py` se omiten en
CI (`RF-096-004`); la evidencia de esa parte es la ejecución local contra el nodo desechable.

**Veredicto del agente `qa`: `accept`.** Reejecutó las 83 pruebas de CI del grupo (`83 passed`) y las 9 de
CockroachDB real (`9 passed`), y comprobó: `git diff e68e3f6d..HEAD -- apps/backend` son 1113 inserciones y 0
borrados; los cuatro archivos de pruebas son nuevos; el producto entra solo en el Green, después de los dos
Red; no hay `skip` ni `xfail`; el cliente sale siempre de la sesión y el cuerpo no puede traerlo; el 404 de una
anomalía ajena e inexistente es idéntico byte a byte; la conversación se comprueba antes de leer ninguna
anomalía; la rama no registra nada; nada se guarda antes de tener la explicación y la métrica sube solo tras
guardar los dos mensajes; la prueba que pasaba en el Red (401/403) es legítima; y las 9 de CockroachDB solo
añaden lo que SQLite no puede ver, porque las formas, los códigos, el orden y el aislamiento ya están en las
27 de CI. No reejecutó las regresiones completas ni la mutación: usó las cifras de arriba.

**Observaciones del QA, aceptadas:**

1. `from pydantic import model_validator` queda en un `import` suelto. Se mantiene así a propósito para no
   tocar la línea que modifica la PR #121; quien integre puede unificarlos.
2. **Integración con JUP-035 (PR #120 y #121).** Conflictos previsibles: los `import` y el cuerpo de
   `send_message`. La rama nueva va antes de la de propiedad y devuelve `AssistantReply` por su cuenta: si
   JUP-035 cambia `AssistantReply` o los metadatos, hay que revisarla. Si JUP-035 añade otra selección
   estructurada, `reject_two_structured_queries` debe ampliarse (hoy cubre dos campos). Se medirá con
   `git merge-tree` en la tarea 8.4.
3. Los dos `append_message` no son atómicos: si falla el segundo queda un mensaje de usuario sin respuesta. La
   rama de propiedad existente funciona igual; no es un hallazgo de este grupo. Las PR #120 y #121 lo
   resuelven con `append_pair`. Se registrará como riesgo conocido (tarea 9.5).
4. **Para los grupos 5 a 9 (frontend y validación):**
   - Un `episode_id` inválido da un 422 con cuerpo saneado genérico (`Invalid request value`), sin código
     `anomaly_…`: el frontend debe validar el formato `anomaly-` + 64 hex en minúscula **antes** de enviar.
   - Los 404 y 409 llevan `detail` como objeto `{"code": …}`, mientras que el 404 de conversación lleva
     `detail` como cadena: el cliente HTTP del frontend debe tratar ambas formas.
   - Evidencia: los operandos son cadenas con 12 decimales exactos (`"2800.000000000000"`) y las horas del
     episodio llevan `+00:00` donde la API de episodios escribe `Z`. El validador del frontend (tarea 5.1)
     debe aceptar ambas formas de fecha y no comparar texto contra la API de episodios.
   - Las cifras de apertura salen redondeadas a 2 decimales en el texto; los exactos solo están en
     `anomaly_evidence.operands`.

**Estado del grupo 4:** tareas 4.1 a 4.8 hechas; mutación con tres equivalentes justificados; DoD en verde y QA
en `accept`. **El backend de la tarjeta está completo.** El contenedor `jup038-crdb` se mantiene hasta la
validación con el stack real (grupo 8) y se apagará al terminar.

## Grupo 5 — Evidencia de la explicación en el frontend, fase Red (tareas 5.1 y 5.2)

**Herramientas.** Vitest 3 y Testing Library, ejecutados directamente en Windows. La suite completa del
frontend es intermitente en esta máquina cuando corre con otra carga (ya registrado en sesiones anteriores), así
que el Red y el control se ejecutan solo sobre los archivos del grupo.

**Contrato fijado antes del Red** (lo implementará el `coder`):

- `isAnomalyEvidence` y la interfaz `AnomalyEvidence` en `apps/frontend/src/services/contracts.ts`: acepta la
  evidencia exacta que genera el backend (versión `1.0` y `anomaly-explanation-1.0`, `id` con 64 hex, episodio
  válido según el `isAnomalyEpisode` existente, operandos como cadenas decimales de cualquier escala, importes
  de dos decimales, `conditions_met: true`, notas de redondeo conocidas, `explained_at` con `Z` o `+00:00`) y
  exige **coherencia interna** (la severidad, el impacto acumulado, la referencia diaria y el observado de la
  evidencia deben coincidir con los del episodio que contiene): los metadatos del mensaje son datos no fiables y
  una mezcla incoherente no debe mostrarse.
- Componente `AnomalyEvidence.tsx`: un `<details>` con las palabras del panel (`severityLabels`,
  `statusLabels`) y el texto de cada línea fijado en las pruebas; una evidencia no válida da un único párrafo
  «La evidencia de esta explicación no está disponible.» y **ninguna cifra**. **No calcula nada**: muestra solo
  las cadenas de la evidencia (importes, operandos con 12 decimales, fechas). El servicio se pinta como texto.
- `AnswerEvidence`: rama nueva tras `cost_evidence` y antes de «Sin fuentes documentales utilizadas.»; las
  citas documentales válidas y `cost_evidence` conservan su prioridad.

**Pruebas escritas por el `tester`** (tres archivos nuevos, 261 pruebas):

- `apps/frontend/src/services/anomalyEvidence.test.ts` (202): acepta la evidencia del ejemplo A con `+00:00` y
  con `Z`, con operandos de 12, 2, 1 y 0 decimales y con importes de más de 15 dígitos, y rechaza cada regla del
  contrato (versiones, `id` de 63/65 hex, mayúsculas y salto de línea final, `source`, episodio, cada operando,
  `opening`, `impact`, notas desconocidas, tipos erróneos) y las cuatro coherencias internas con diferencias de
  un céntimo.
- `apps/frontend/src/components/AnomalyEvidence.test.tsx` (44): texto exacto de cada línea; las tres
  criticidades y los cuatro estados; singular y plural de días; servicio nulo y servicio con HTML (sin crear
  elementos); USD sin ninguna mención de EUR; notas de redondeo y aviso sintético presentes y ausentes;
  operandos exactos tal cual; limitaciones tomadas de la evidencia y no del episodio; cifras «raras» (una
  aritmética que a propósito no cuadra) que salen idénticas, lo que demuestra que el componente no calcula; y 17
  formas de evidencia inválida sin ninguna cifra.
- `apps/frontend/src/components/AnswerEvidence.anomaly.test.tsx` (15): la rama nueva, su prioridad frente a las
  citas y a `cost_evidence`, evidencia no válida, y que las viñetas del texto no se vuelven enlaces de fuente.

**Evidencia Red** (2026-10-12, Windows, Node con `corepack pnpm`):

```
corepack pnpm --filter @finops/frontend exec vitest run src/services/anomalyEvidence.test.ts src/components/AnomalyEvidence.test.tsx src/components/AnswerEvidence.anomaly.test.tsx
```

- Resultado: **`257 failed | 4 passed (261)`**, ninguna omitida ni con `skip`. Motivos, contados por el
  orquestador: 202 por `isAnomalyEvidence is not a function`; 44 por `Cannot find module './AnomalyEvidence'`;
  11 por la ausencia de la rama nueva en `AnswerEvidence` (8 buscan «La evidencia de esta explicación no está
  disponible.» y 3 buscan el resumen del bloque).
- **4 pruebas pasan de entrada, a propósito**, todas en `AnswerEvidence.anomaly.test.tsx`: las viñetas del
  texto no se convierten en enlaces de fuente; las citas documentales válidas tienen prioridad; `cost_evidence`
  tiene prioridad; y sin evidencia de anomalía se mantiene «Sin fuentes documentales utilizadas.». Fijan
  comportamiento existente que la rama nueva no debe romper.
- Control, mismo entorno: `AnswerEvidence.test.tsx` y `CostEvidence.test.tsx` siguen en `11 passed`.

**Nota técnica del `tester`.** En `AnomalyEvidence.test.tsx` el import es `await import(/* @vite-ignore */ ruta)`
con la ruta en una variable: con el literal, Vite falla al transformar el archivo entero («Failed to resolve
import») y no llega a enumerar ninguna prueba; con la variable, cada prueba falla por separado. Comprobó con un
archivo temporal, ya borrado, que con el módulo presente el import se resuelve.

**Ambigüedades del `tester`** (contrato sin cambios): `assumptions` solo se exige que sea lista; un servicio `""`
no se fija; los operandos con `+`, `2800.`, `.5`, espacios o salto de línea final se rechazan; la coherencia
interna no incluye `day_count` ni `rules_version` (el contrato no las lista); y la evidencia `reference_daily_cost`
y `observed_cost` mal formadas se rechazan por forma o por coherencia sin aislar el motivo.

**Lo que este Red no demuestra.** Que las pruebas sean correctas contra la implementación real; se sabrá en el
Green. No hay prueba en navegador real todavía (grupo 8).

## Grupo 5 — Evidencia de la explicación en el frontend, fase Green (tarea 5.3)

**Producto del `coder`:**

- `apps/frontend/src/services/contracts.ts` (+70, 0 borradas): `AnomalyEvidence`, `AnomalyRoundingNote` e
  `isAnomalyEvidence`, que reutiliza `anomalyObject`, `anomalyMoney`, `anomalyDate`, `anomalyInstant`,
  `anomalyCount` e `isAnomalyEpisode` y añade solo dos ayudantes locales (`anomalyExact` y `anomalyThreshold`).
  Aplica las cuatro coherencias internas con el episodio.
- `apps/frontend/src/components/AnomalyEvidence.tsx` (nuevo): usa `severityLabels` y `statusLabels` del panel,
  no calcula nada y pinta el servicio y las limitaciones como texto de React. Con evidencia no válida da un
  único párrafo y ninguna cifra.
- `apps/frontend/src/components/AnswerEvidence.tsx` (+4/−1): un import y la rama nueva del ternario. Hubo que
  partir en dos líneas la línea existente `</section> : "cost_evidence" in metadata ? … : <p …>` para insertarla;
  la PR #121 (JUP-035) reescribe esas mismas líneas, de modo que ahí habrá conflicto de contenido que resolver
  al integrar (tarea 8.4).

**Decisiones del `coder` no cubiertas por el encargo** (revisadas): `Date.parse` de V8 acepta
`2026-02-30T00:00:00Z`, así que `anomalyInstant` por sí sola no rechaza un `explained_at` con día imposible; se
añade `anomalyDate(explained_at.slice(0, 10))` con su comentario, sin modificar `anomalyInstant`. Los umbrales
son `^\d+(\.\d+)?$` y los operandos `^-?\d+(\.\d+)?$`. `rules_version` y `severity_band` se rechazan si están
vacíos o solo con espacios (`isNonemptyString` no hace `trim`). No se exige coherencia entre
`source.rules_version` y `episode.rules_version` porque las pruebas no la fijan.

**Evidencia Green** (2026-10-12, reejecutada por el orquestador, Windows):

- Pruebas nuevas: **261 de 261** (`anomalyEvidence` 202, `AnomalyEvidence` 44, `AnswerEvidence.anomaly` 15);
  antes `257 failed | 4 passed`. El import dinámico con `/* @vite-ignore */` resuelve ahora que el módulo existe.
- Control (`AnswerEvidence`, `CostEvidence`, y los de episodios y panel): sigue en verde; en conjunto con las
  nuevas, `5 archivos, 272 pruebas pasan`.
- `corepack pnpm --filter @finops/frontend typecheck`: código 0.
- `corepack pnpm --filter @finops/frontend lint`: código 0 **tras la corrección de abajo**.

### Adenda: lint de las pruebas del Red y segunda excepción al candado

**Qué pasó.** El Green dejó al descubierto que `lint` fallaba con **49 errores, todos en las tres pruebas del
Red** (44 + 3 + 1 `no-explicit-any` y 1 `no-loss-of-precision`); el producto pasaba `eslint` limpio. Es un fallo
del **proceso**: el Red no incluyó lint ni typecheck de los archivos de pruebas nuevos. Desde ahora el encargo al
`tester` exige `lint` y `typecheck` de sus archivos ya en la fase Red.

**Decisiones de Victor, 2026-10-12.** Eligió el bypass puntual del candado (frente a relajar la regla de ESLint,
que debilitaría el lint de todo el equipo, o corregirlo a mano). El sistema de permisos de Claude Code
**denegó** el primer intento, hecho por el `tester` ("Auto-Mode Bypass"); el `tester` no insistió y lo escaló.
Victor autorizó entonces **directamente al orquestador** a aplicar la corrección, y así se hizo. No se tocó la
configuración de hooks ni `.claude/`.

**Qué cambió.** Solo los tres archivos de pruebas, y solo tipos:

- `Record<string, any>` → un alias `type Mut = { [key: string]: unknown }` con su comentario (48 sustituciones) y
  86 casts puntuales `(e.episode as Mut).x` en las mutaciones anidadas.
- El literal `9007199254740993` → `Number("9007199254740993")` con un comentario: se evalúa al mismo valor,
  `9007199254740992`, fuera del rango seguro.
- No se usó `eslint-disable`: `LoginPage.tsx` documenta que en este repositorio un `eslint-disable` hace
  crashear el linter entero.

**Verificación independiente de que solo cambiaron tipos.** Se deshicieron las sustituciones (los casts, el
alias y su comentario, `Mut` → `Record<string, any>` y el literal) sobre cada archivo y se comparó con la versión
commiteada en `f678ee09`: **los tres quedan idénticos byte a byte**. Los recuentos de `it(` y `expect(` no
cambian (27 y 67; 20 y 56; 8 y 26). Tras la corrección: `lint` y `typecheck` con código 0 y 272 pruebas en verde.

**Pendiente del grupo 5:** mutación (5.4), DoD del frontend y QA.

## Grupo 5 — Evidencia de la explicación en el frontend, mutación (tarea 5.4)

**Herramienta.** Stryker (`@stryker-mutator/core` y `vitest-runner`, con `typescript@5.9.3`) por `pnpm dlx` desde
`apps/frontend`, según `.claude/harness/mutation.md`, **más un arnés manual** para el componente (ver abajo).
La configuración se acotó con un archivo temporal de Vitest (`vitest.stryker.config.mts`, borrado al terminar)
que solo incluye las pruebas relevantes, con análisis por prueba. No se usó `mergeConfig`: concatena los
arrays y volvía a ejecutar toda la suite (749 pruebas y una estimación de 1 h 30 min frente a 228 pruebas y
unos 5 min).

**Hallazgo de herramienta.** Stryker **no ejecuta las 44 pruebas de `AnomalyEvidence.test.tsx`**: la ejecución
inicial da 228 pruebas, 44 menos que las 272 esperadas, y esas pruebas no aparecen en ningún informe. La causa
más probable es su `import(/* @vite-ignore */ ruta)` con la ruta en una variable (lo introdujo el Red para que
fallase cada prueba por separado), que no se instrumenta. Por eso, **la puntuación de Stryker sobre
`AnomalyEvidence.tsx` (87.80 % en la primera pasada, 20 supervivientes) no es una medida fiable** y no se usa.
Se midió el componente con mutantes manuales ejecutando Vitest directo, y `contracts.ts` y `AnswerEvidence` con
Stryker, donde sus pruebas sí corren.

**Primera pasada (Stryker, 3 archivos, 254 mutantes):** 87.80 %: 223 muertos, 29 supervivientes y 2 sin
cobertura. Los de `contracts.ts` eran 3:

1. `typeof value.id !== "string"` → `false`. **Hueco real.** Sin el `typeof`, `RegExp.test` convierte a texto: un
   `id` que fuese un array `["anomaly-explanation:<64 hex>"]` cumpliría el patrón y se aceptaría.
2. `["P1", "P2", "P3"]` → `["P1", "", "P3"]`. **Hueco real.** Ninguna prueba usaba una evidencia válida con
   criticidad P2 (ni P1).
3. `typeof note === "string"` → `true`. **Equivalente**: `Array.includes` usa igualdad estricta y una nota que no
   es cadena se rechaza igualmente.

**Arnés manual del componente (32 mutantes sobre `AnomalyEvidence.tsx`):** cada línea de texto vaciada, el
singular y plural de días, el servicio nulo, las condiciones de las notas de redondeo, del aviso sintético y de
las limitaciones (siempre, nunca, `||`, `>=`, `<=`), los elementos de la lista, el resumen, la causa y el servicio
como texto. **30 muertos de 32.** Sobrevivían «limitaciones siempre» y «limitaciones con `>=`»: **hueco real**,
con `limitations: []` se renderizaría una lista vacía y ninguna prueba lo comprobaba.

**Remediación** por el `tester`, en dos archivos nuevos (los anteriores están commiteados), ya con `lint` y
`typecheck` verificados y sin `any` ni `eslint-disable`:

- `apps/frontend/src/services/anomalyEvidence.mutants.test.ts` (7 pruebas): rechaza el `id` como array y como
  objeto con `toString`, con control positivo; acepta evidencias coherentes con criticidad P1, P2 y P3 y sigue
  rechazando una P4.
- `apps/frontend/src/components/AnomalyEvidence.mutants.test.tsx` (3 pruebas): con `limitations: []` el validador
  acepta la evidencia, no existe ninguna lista «Limitaciones» y el resto del bloque se muestra; con una limitación
  sí.

**Segunda pasada** (reejecutada por el orquestador el 2026-10-12, Windows):

- Stryker sobre `contracts.ts` (líneas 469 a 539) y la rama nueva de `AnswerEvidence` (líneas 73 y 74):
  **212 mutantes, 211 muertos, 1 superviviente: 99.53 %.** El superviviente es el equivalente 3.
- Arnés manual del componente: **32 de 32 muertos**, control `62 passed`, archivo restaurado sin cambios.
- `lint` y `typecheck`: código 0 (comprobado con el código de salida real).

**Superviviente justificado.** `typeof note === "string"` → `true` en `rounding_notes`: equivalente, `includes`
rechaza cualquier valor que no sea exactamente una de las tres cadenas conocidas.

**Lo que esta mutación no demuestra.** Stryker no mide el componente (ver arriba): su cobertura sale del arnés
manual (32 mutantes dirigidos, no un barrido). No hay prueba en navegador real todavía (grupo 8). El DoD del
frontend y el veredicto de QA del grupo siguen pendientes.

## Grupo 5 — Definition of Done y veredicto de QA

**DoD** (2026-10-13, sobre `531003d3`; máquina calmada: 3 GB de RAM libres, 9 % de CPU y ningún `node` ajeno
en marcha, porque la suite completa del frontend es intermitente en esta máquina con otra carga):

| Control | Resultado |
| --- | --- |
| Suite completa del frontend (`vitest run`, Windows) | **71 archivos, 1151 pruebas pasan, 0 fallos** (82 s), en la primera ejecución |
| `corepack pnpm --filter @finops/frontend lint` | código 0 (comprobado con el código de salida real) |
| `corepack pnpm --filter @finops/frontend typecheck` | código 0 |
| `corepack pnpm --filter @finops/frontend build` | código 0 |
| Escaneo de secretos | 1489 líneas añadidas desde `d0bd0e38`, 0 hallazgos |
| Pruebas anteriores al grupo | Ninguna modificada (`AnswerEvidence.test.tsx`, `CostEvidence.test.tsx`… intactas) |

No se ejecutó la regresión del backend: el grupo no toca el backend. No hizo falta un control sobre `develop`
porque no hubo ningún fallo que atribuir.

**Veredicto del agente `qa`: `accept`.** Reejecutó las 282 pruebas de los siete archivos relacionados
(`282 passed`) y comprobó: la corrección de lint de las pruebas del Red fue solo de tipos (normalizó las tres
contra el Green y quedan idénticas salvo el alias `Mut` y sus comentarios; recuentos de `it(` y `expect(`
27/67, 20/56 y 8/26); no hay `skip`, `only`, `todo` ni `xit`; `isAnomalyEvidence` es la frontera de confianza
y `AnomalyEvidence.tsx` no lee ninguna cifra antes de validarla; la coherencia interna es razonable y no
rechaza evidencia legítima; el servicio y las limitaciones van como texto de React; el componente no tiene
`Number(`, `parseFloat`, `toFixed` ni aritmética; `contracts.ts` solo inserta líneas y `AnswerEvidence.tsx`
añade un import y una rama, sin cambiar citas ni `cost_evidence`. No reejecutó la suite completa ni el build:
usó las cifras de arriba.

**Observaciones del QA, aceptadas:**

1. Grupos 6 y 7: el frontend debe validar `anomaly-` + 64 hex en minúscula antes de enviar y dar un mensaje
   propio, porque el backend responde un 422 genérico.
2. Grupos 6 y 7: los 404 y 409 de la explicación llevan `detail` como objeto `{code}` y el 404 de conversación
   como cadena; el cliente debe tratar ambas formas.
3. `AnswerEvidence` ya pinta la evidencia, pero la entrada para pedirla (modo «Explicar una anomalía»,
   `?episode=`, enlace del panel) aún no existe; una prueba de integración de extremo a extremo en el grupo 6
   cubrirá ese hueco.
4. **Deuda de herramienta:** Stryker no ejecuta las pruebas de `AnomalyEvidence.test.tsx` por el import con ruta
   en variable y `/* @vite-ignore */` (registrada en el apartado de mutación del grupo 5).
5. El texto «Candidata: causa no establecida.» está fijo en el componente aunque el validador exige
   `cause_status === "not_established"`; es coherente y hay que mantenerlo alineado si el contrato cambia.

**Estado del grupo 5:** tareas 5.1 a 5.4 hechas; mutación con un único equivalente justificado y una deuda de
herramienta documentada; DoD en verde y QA en `accept`.

## Grupo 6 — Modo «Explicar una anomalía» del redactor, fase Red (tareas 6.1, 6.2 y 6.4)

**Contrato visible fijado antes del Red** (lo implementará el `coder`; son decisiones de diseño del
orquestador, recogidas aquí porque no estaban en el `design.md`):

- **Redactor.** Segunda casilla `Explicar una anomalía`, excluyente con `Consultar costes por propiedad` en los
  dos sentidos. Al activarla se pide `GET /billing/anomalies/episodes?scope=all` (con el modo apagado no se hace
  ninguna petición de anomalías). Mientras carga, `Cargando anomalías...`. Un `<select>` `Anomalía` con la
  opción vacía `Elige una anomalía` y una opción por episodio, `{servicio} · {moneda} · desde {fecha ISO} ·
  {criticidad} · {estado}`; solo se ofrecen los episodios cuyo `id` cumple `^anomaly-[0-9a-f]{64}$`. Sin
  anomalías válidas, `Este cliente no tiene anomalías guardadas. Se detectan desde el panel de Anomalías.`; si
  la lista falla, un `alert` `No se han podido cargar las anomalías.`; `Enviar` queda deshabilitado en ambos
  casos y mientras no haya una elegida. La pregunta vacía se rellena con `¿Por qué se ha marcado esta anomalía?`
  (editable, sin sobrescribir texto previo). El `POST` lleva exactamente `{content, anomaly_query:
  {episode_id}}`, sin `ownership_query`.
- **Errores del servidor.** `anomaly_episode_not_found` → `No se ha encontrado esa anomalía en el cliente activo.
  Actualiza la lista y elige otra.`; `anomaly_explanation_unavailable` → `Esta anomalía no se puede explicar con
  las reglas actuales.`; cualquier otro error conserva el mensaje genérico que ya mostraba el redactor. En todos
  se conservan la pregunta y la elección y no se añade ningún mensaje a la conversación.
- **Entrada por dirección** (`/assistant?episode=<id>`). Con parámetro no vacío y una conversación seleccionada,
  el redactor aparece con el modo activo y, cuando la lista carga y el id está entre las del cliente, esa opción
  elegida; si no está (otro cliente, inexistente o formato inválido) un `status` `La anomalía indicada en el
  enlace no está entre las de este cliente.` y ninguna elegida. Tras un envío correcto el parámetro desaparece;
  tras uno fallido se conserva. Sin parámetro el redactor es el de hoy.

**Pruebas escritas por el `tester`** (dos archivos nuevos, 38 pruebas de integración montando la aplicación real
con el enrutador y un servidor simulado en el que cualquier petición no prevista falla):

- `apps/frontend/tests/anomaly-explanation-conversations.test.tsx` (6.1 y 6.2, 22): modo apagado sin peticiones;
  carga con la cabecera del cliente; `Cargando…`; contenido y orden de las opciones (con un orden que no
  coincide con fecha, criticidad, servicio ni id); siete formas de identificador inválido filtradas; `Enviar`
  deshabilitado; cuerpo exacto del `POST`; éxito con recarga y bloque `Evidencia de la anomalía — Baja (P3)`;
  lista vacía y solo con ids inválidos; fallo de carga por 500 y por forma inválida; exclusión entre modos en los
  dos sentidos; y los errores 404, 409, 404 de conversación, 422 y 503 con el texto exacto, pregunta y elección
  conservadas, sin artículos nuevos, cada uno con un reintento correcto como control positivo.
- `apps/frontend/tests/anomaly-explanation-link.test.tsx` (6.4, 16): preselección de una anomalía que no es la
  primera; aviso con id ausente, de formato inválido (aunque esté listado), con mayúsculas y con lista vacía;
  sin aviso mientras la lista carga; el parámetro desaparece tras un éxito y se conserva tras un fallo; sin
  parámetro o con `?episode=` vacío todo queda como hoy; cambio de cliente; y que sin conversación seleccionada
  el parámetro sobrevive hasta montar el redactor.

**Evidencia Red** (2026-10-13, Windows, reejecutada por el orquestador):

```
corepack pnpm --filter @finops/frontend exec vitest run tests/anomaly-explanation-conversations.test.tsx tests/anomaly-explanation-link.test.tsx
```

- Resultado: **`38 failed (38)`**, ninguna omitida ni con `skip`. **Las 38 por el mismo motivo**: `Unable to find
  role="checkbox" and name "Explicar una anomalía"`; ninguna por preparación, carga del archivo ni petición sin
  interceptar (0 `Unmocked HTTP request`).
- Control: `ownership-conversations`, `conversations` y `tenant-switching`: `26 passed`.
- `lint` y `typecheck` con los dos archivos nuevos: **código 0** (comprobado con el código de salida real).
  Es la lección del grupo 5: ahora el Red ya lo exige.
- **Comprobación extra del `tester`:** copió `apps/frontend` a un directorio temporal **fuera del repositorio**,
  escribió allí una implementación mínima de referencia y las 38 pruebas pasaron (y las 26 de control
  también). Demuestra que son satisfacibles y que el Red no falla por una aserción imposible. Esa
  implementación es suya, no el trabajo del `coder`, y no queda nada en el repositorio.

**Ambigüedades del `tester`** (contrato sin cambios): la pregunta queda vacía tras un éxito (el modo la vuelve a
proponer al reactivarse); no se muestra el aviso del enlace mientras la lista carga; con lista vacía y parámetro
se exigen a la vez el aviso del enlace y el texto de «no hay anomalías guardadas»; para el 404 de conversación, el
422 y el 503 el mensaje es el cuerpo crudo de la respuesta, como ya hacía el redactor; el parámetro sigue en la
dirección tras cambiar de cliente; y las etiquetas de las opciones se escriben literalmente en las pruebas, sin
importar `severityLabels` ni `statusLabels`, para que un cambio de etiquetas en el producto las haga fallar. No se
incluyó la prueba opcional de «un envío en curso no pierde la elección si cambia la lista».

**Lo que este Red no demuestra.** Que las pruebas sean correctas contra la implementación real del producto; no
hay prueba en navegador real todavía (grupo 8).

## Grupo 6 — Modo «Explicar una anomalía» del redactor, fase Green (tareas 6.3 y 6.5)

**Producto del `coder`** (`git diff --stat`: 3 archivos modificados con 88 inserciones y 9 borrados, más un archivo
nuevo):

- `apps/frontend/src/components/AnomalyExplanationFields.tsx` (nuevo): carga la lista del cliente con
  `useQuery` (clave `["anomaly-episodes-for-explanation", tenantId]`, `retry: false`), solo cuando el modo está
  activo; los estados `Cargando anomalías...`, error (`alert` con texto fijo, sin el cuerpo del servidor), vacío y
  el `select` «Anomalía» con los textos de las pruebas, en el orden del backend y solo con ids válidos; el aviso del
  enlace (`status`) únicamente con la lista ya cargada. La preselección desde el enlace se aplica **una sola vez**,
  al llegar la primera lista (con un `ref`), para no reimponerla si la persona vuelve a «Elige una anomalía».
- `apps/frontend/src/components/MessageComposer.tsx` (+71): la segunda casilla, excluyente en los dos sentidos;
  la pregunta propuesta solo con el cuadro vacío; `Enviar` deshabilitado sin elegir; el `POST` con exactamente
  `{content, anomaly_query: {episode_id}}`; `anomalyErrorText`, que traduce **por `detail.code`** y no por estado
  HTTP (un 404 también lo da la conversación inexistente, con `detail` como cadena); y las props opcionales
  `initialEpisodeId` y `onSent`, para no romper los usos actuales.
- `apps/frontend/src/pages/ConversationsPage.tsx` (+17): lee `episode` con `useSearchParams` en la **página** y no
  en el redactor, porque este solo existe con una conversación seleccionada y el parámetro debe sobrevivir hasta
  entonces; tras un envío correcto lo quita con `replace`.
- `apps/frontend/src/services/contracts.ts` (+9, solo inserciones): `anomaly_query?` en `MessageCreateRequest` e
  `isAnomalyEpisodeId`, con coincidencia completa `^anomaly-[0-9a-f]{64}$` y sin la bandera `m`.
- Estos archivos, a diferencia de `AnswerEvidence.tsx`, **no los modifican las PR #120 y #121** de JUP-035 (no
  aparecen en su lista de archivos del frontend): no se prevé conflicto de contenido en ellos.

**Evidencia Green** (2026-10-13, reejecutada por el orquestador, Windows):

- Pruebas nuevas: **38 de 38** (22 de conversaciones y 16 del enlace); antes `38 failed`.
- Control, sin editar ninguna prueba: `ownership-conversations`, `conversations`, `tenant-switching`,
  `ConversationsPage`, `AnswerEvidence` y `AnomalyEvidence`: en conjunto con las nuevas, `8 archivos, 117 pruebas
  pasan`. El `coder` comprobó además `spanish-ui.test.ts` (7 de 7).
- `lint` y `typecheck`: **código 0** los dos (código de salida real).

**Decisiones del `coder` no cubiertas por el encargo** (revisadas):

- Al apagar el modo de anomalía, o al activar el de propiedad, se reinicia la anomalía elegida. Con el enlace aún
  en la dirección, al reactivar el modo vuelve a preseleccionarse la del enlace (el componente se remonta); tras
  un envío correcto el parámetro desaparece y eso deja de ocurrir.
- Tras un envío correcto la anomalía elegida **se conserva**; solo se limpia la pregunta, como hoy.
- Si la lista se vuelve a pedir (p. ej. al recuperar el foco) y la anomalía elegida ya no está, no se corrige en
  el cliente: lo cubre el 404 del backend con su mensaje fijo.

**Pendiente del grupo 6:** mutación (6.6), DoD del frontend y QA.

## Grupo 6 — Modo «Explicar una anomalía» del redactor, mutación (tarea 6.6)

**Herramienta.** Stryker por `pnpm dlx` desde `apps/frontend` (`.claude/harness/mutation.md`), con un Vitest
temporal (`vitest.stryker.config.mts`, borrado al terminar) que solo incluye las pruebas nuevas y las de control
(se sustituye el `include` en vez de usar `mergeConfig`, que concatena los arrays y volvería a ejecutar toda la
suite) y análisis por prueba. Acotado a **exactamente el código que añadió la tarea**: el componente nuevo entero
y solo los bloques añadidos de `MessageComposer.tsx`, `ConversationsPage.tsx` y `contracts.ts`, con los rangos de
líneas sacados del diff del commit Green. 175 mutantes. Las pruebas del grupo son de integración (montan la
aplicación con el enrutador) y usan imports estáticos, así que **aquí Stryker sí las ejecuta** (65 pruebas en la
ejecución inicial), a diferencia de lo ocurrido con el componente del grupo 5.

**Primera pasada** (38 pruebas nuevas + 27 de control): **82.86 %**, 145 muertos, 29 supervivientes y 1 sin
cobertura. Clasificados uno a uno:

- **Huecos reales (16):**
  - `linkApplied.current`: la preselección del enlace se aplica **una sola vez**; sin eso, volver a «Elige una
    anomalía» reimpondría la del enlace.
  - `if (!episodeId) return`: un envío del formulario forzado sin anomalía elegida no debe salir, aunque el
    botón esté deshabilitado.
  - Reinicio de la elección al pasar a propiedad y al apagar el modo (sin él se arrastra una elección vieja).
  - No volver a proponer la pregunta al apagar el modo con el cuadro vacío; sustituir un texto de solo espacios.
  - `sendMutation.reset()`: cambiar de modo borra el error anterior.
  - El marcador del cuadro en el modo de propiedad (texto existente cuya línea se reestructuró).
  - La guarda `enabled: Boolean(token && tenantId)`: sin token o sin cliente no se pide la lista.
  - El valor por defecto de `initialEpisodeId` y `onSent?.()`: el redactor funciona sin esas props opcionales.
  - `onSent` de la página: el resto de parámetros de la dirección se conservan y la navegación es de **reemplazo**.
  - `isAnomalyEpisodeId`: **mismo hueco que en el grupo 5**; un array `["anomaly-<hex>"]` pasaba el `RegExp.test`
    porque se convierte a texto.
- **Equivalentes o no especificados (13), sin remediar** (ver abajo).

**Remediación** por el `tester`, en dos archivos nuevos (los anteriores están commiteados), con `lint` y
`typecheck` ya verificados y sin `any` ni `eslint-disable`:

- `apps/frontend/src/services/anomalyEpisodeId.mutants.test.ts` (10): acepta el id válido y rechaza el array, el
  objeto con `toString`, números, `null`, `undefined`, mayúsculas, 63 y 65 hex y el `\n` final.
- `apps/frontend/tests/anomaly-explanation-conversations.mutants.test.tsx` (19): una prueba o más por cada hueco
  de arriba, con controles positivos. Para afirmar que algo **no** ocurre usa una espera real de 40 ms
  (determinista en la práctica, pero tiempo real y no un reloj simulado). Para el mutante de la preselección
  única fuerza un refetch con datos distintos, porque un nuevo render por sí solo no vuelve a ejecutar el efecto.

**Segunda pasada** (reejecutada por el orquestador el 2026-10-13, 175 mutantes, 67 pruebas incluyendo las nuevas):
**92.57 %: 162 muertos, 13 supervivientes y 0 sin cobertura.** Son **exactamente los 13** clasificados de antemano
como equivalentes o no especificados:

1. `queryKey` con otro nombre de la clave de caché: equivalente, solo afecta al nombre interno.
2. `fieldClass = ""`: equivalente en comportamiento (solo cambia el estilo).
3. `query.isError || !options` → `&&`: solo difiere si falla un **refetch** teniendo ya datos (se vería la lista
   anterior en vez del error). Ese caso no está especificado; la spec cubre el fallo de la primera carga.
4. `if (!(error instanceof ApiError)) return error.message` → `false`: equivalente; un error que no es `ApiError`
   cae igualmente en el `catch` del `JSON.parse` y devuelve el mismo `message`.
5. Ocho controles de tipo (`typeof … === "object"`, `!== null`) dentro de `anomalyErrorText`: equivalentes; el
   `try/catch` absorbe cualquier excepción y el resultado es el mismo mensaje.
6. `if (event.target.checked)` de la casilla de propiedad → `true`: equivalente; con la propiedad apagada la
   anomalía ya está apagada, así que el reinicio es redundante.

**Lo que esta mutación no demuestra.** Es una medida de Stryker sobre el código añadido por la tarea, no sobre los
archivos enteros; las esperas de 40 ms son tiempo real. No hay prueba en navegador real todavía (grupo 8). El
DoD del frontend y el veredicto de QA del grupo siguen pendientes.

## Grupo 6 — Definition of Done y veredicto de QA

**DoD** (2026-10-13, sobre `1ae0e1d9`; máquina calmada: 3 GB de RAM libres, 18 % de CPU y ningún `node` ajeno):

| Control | Resultado |
| --- | --- |
| Pruebas del grupo (4 archivos, 67 pruebas) y de control (ownership, conversations, tenant-switching, ConversationsPage, AnswerEvidence, AnomalyEvidence) | Todas en verde, sin editar ninguna anterior (8 archivos, 117 pruebas en el Green; el `qa` reejecutó 94) |
| `corepack pnpm --filter @finops/frontend lint` | código 0 (código de salida real) |
| `corepack pnpm --filter @finops/frontend typecheck` | código 0 |
| `corepack pnpm --filter @finops/frontend build` | código 0 |
| Escaneo de secretos | 1561 líneas añadidas desde `e9a7a152`, 0 hallazgos |
| **Suite completa del frontend** (75 archivos, 1219 pruebas), 2 ejecuciones | **1218 pasan y 1 falla en cada una, y el fallo es distinto cada vez** (ver abajo) |
| Archivos de producto modificados | Solo los tres previstos: `MessageComposer.tsx`, `ConversationsPage.tsx` y `contracts.ts` |

**Los fallos de la suite completa no son de este cambio.**

- Primera ejecución: falla `tests/login-session-expired-notice.pending-attempt.test.tsx`. Segunda: falla
  `tests/login-session-expired-notice.test.tsx` (tarea 4.1). Las dos son de JUP-098 (aviso de sesión expirada en
  `/login`). Ese primer archivo pasa 3 de 3 ejecutado solo.
- **Control** sobre el `develop` previo a JUP-038 (`bfaf3983`), en un árbol aparte con sus dependencias instaladas:
  la **misma suite falla esas dos mismas pruebas en las dos ejecuciones** (2 de 66 archivos). Es decir, son
  intermitencias o fallos de la base en esta máquina, ya registradas (`RF-098-004` y `RF-103-005` en el backlog),
  y no se atribuyen a JUP-038. Ninguna prueba del grupo falló en ninguna ejecución completa.
- El árbol del control se retiró con `git worktree remove` (queda un directorio parcial sin registrar en el
  espacio temporal, por la ruta larga de Windows, inofensivo y fuera del repositorio).
- Los mensajes «The URL path "/%E0%A4%A" could not be decoded» del registro son salida esperada de una prueba que
  comprueba direcciones mal formadas, no errores.

**Veredicto del agente `qa`: `accept`.** Reejecutó 8 archivos (`94 passed`) y comprobó: el historial (el Red solo
trae pruebas, el producto entra en el Green y la mutación solo trae pruebas; ninguna prueba anterior modificada);
que cada escenario de la spec tiene una prueba que falla si se rompe (elegir y enviar, cliente sin anomalías,
lista que no carga, anomalía en la dirección, anomalía ajena, modos excluyentes y error al pedir la explicación);
que el parámetro solo preselecciona y exige pulsar «Enviar», que solo se ofrecen y envían ids válidos, que un
envío forzado queda bloqueado y que los textos van como nodos de React; que las props nuevas son opcionales y
nada anterior cambia; que la atribución del fallo de la suite completa a la base es correcta; y que la
justificación de los 13 supervivientes es razonable. No reejecutó la suite completa ni lint, typecheck o build.

**Observaciones del QA, aceptadas:**

1. Las esperas reales de 40 ms de las pruebas de mutantes solo afirman que algo **no** ocurre: el fallo sería un
   falso verde, no un falso rojo; riesgo de intermitencia bajo y ya declarado.
2. **Ninguna prueba afirma explícitamente «cero `POST` antes de pulsar Enviar» al llegar por enlace**; el código
   no autoenvía. Se comprobará en la receta de navegador del grupo 8 (tarea 8.1).
3. Si un id de formato inválido estuviera en la lista del cliente, se filtra y el aviso diría «no está entre las
   de este cliente», algo impreciso; caso poco realista, relevante para el grupo 7.
4. **Para el grupo 7:** `isAnomalyEpisodeId` ya garantiza `anomaly-<64 hex>`, que no necesita escape, pero el enlace
   debe generarse con `encodeURIComponent` o `URLSearchParams` por coherencia con `api.ts`, y solo debe renderizarse
   para episodios con id válido; si no, llevaría a un aviso y no a un error.
5. Un fallo de refetch teniendo ya datos (mutante `isError ||`) no está especificado: se mostraría la lista
   anterior en vez del error. No bloquea.
6. Al cambiar de conversación con `?episode=` aún en la dirección, el redactor se vuelve a armar con la
   preselección, porque el parámetro solo se limpia tras un envío correcto. Es coherente con la spec («en cuanto hay
   una conversación seleccionada») y se tendrá en cuenta en el grupo 8.

**Estado del grupo 6:** tareas 6.1 a 6.6 hechas; mutación con 13 supervivientes equivalentes o no especificados
justificados; DoD en verde salvo los fallos intermitentes de la base, atribuidos con control; QA en `accept`.

## Grupo 7 — Enlace «Explicar en el asistente» del panel de anomalías, fase Red (tarea 7.1)

**Contrato visible fijado antes del Red** (lo implementará el `coder`):

- En el detalle de una anomalía, un enlace (`role="link"`) con nombre exacto `Explicar en el asistente` y `href`
  `/assistant?episode=<id>` (el id con `encodeURIComponent`), en **cualquier** estado (`new`, `investigating`,
  `resolved`, `false_positive`) y con observación `observed` o `no_longer_observed`, también cuando ya no hay
  acciones de estado.
- **Solo si el `id` cumple `^anomaly-[0-9a-f]{64}$`.** Con otro formato el detalle no ofrece el enlace, porque el
  asistente rechazaría ese id y llevaría a un aviso y no a una explicación. Esto recoge la observación 4 del QA
  del grupo 6 y matiza el requisito de `anomalies-panel` («en cualquier estado»), que habla de estados y no de
  formatos de identificador; los ids reales siempre tienen ese formato.
- El enlace **solo navega**: lleva a `/assistant` con la búsqueda `?episode=<id>` y no envía ninguna petición
  HTTP (ni lectura, ni `POST`, ni `PATCH`). El resto del detalle no cambia.

**Pruebas escritas por el `tester`** (un archivo nuevo, 19 pruebas, con lint y typecheck ya verificados y sin `any`
ni `eslint-disable`): `apps/frontend/src/pages/AnomaliesPanel.explain-link.test.tsx`.

- 7 casos de presencia y `href` exacto (nueva, en investigación, resuelta y falso positivo, con y sin observación).
- 1 de que el resto del detalle no cambia (acciones de estado para las abiertas y ninguna para las cerradas).
- 8 de ausencia con ids inválidos (`anomaly-1`, mayúsculas, 63 y 65 hex, un carácter `g`, sin prefijo, espacio
  final y salto de línea final), cada una con el control positivo de una anomalía válida en la misma lista.
- 1 de navegación (monta un enrutador con una ruta `/assistant`): la ruta y la búsqueda correctas y ninguna
  llamada nueva a `fetch` tras cargar la lista.
- 1 con tres anomalías (el enlace apunta al id de la fila abierta) y 1 de cerrar y reabrir otra (cada detalle
  muestra el suyo).

**Evidencia Red** (2026-10-13, Windows, reejecutada por el orquestador):

- `corepack pnpm --filter @finops/frontend exec vitest run src/pages/AnomaliesPanel.explain-link.test.tsx`:
  **`19 failed (19)`**, ninguna omitida ni con `skip`, **todas por el mismo motivo**: `Unable to find role="link"
  and name "Explicar en el asistente"`. Las de ausencia fallan en su control positivo, no por vacuidad.
- Control: `AnomaliesPanel.test.tsx`: **34 de 34 en verde**.
- `lint` y `typecheck`: **código 0** (códigos de salida reales).

**Notas del `tester`:** las anomalías cerradas solo salen en la tabla con el filtro «Todos los estados» (por defecto
es «Abiertas»), así que las pruebas cambian el filtro y esperan al selector; el botón de cerrar el diálogo se llama
`Cerrar` y se distingue de la acción `Cerrar…`; los ids con espacio o salto de línea final se consideran inválidos,
lo que depende de que el producto use `^…$` sin `m` y no un `trim()`; y el comando de Vitest imprime al final
`ERR_PNPM_RECURSIVE_EXEC_FIRST_FAIL … "vitest" not found`, una rareza de `pnpm exec` en este entorno que no
invalida los resultados.

**Lo que este Red no demuestra.** Que las pruebas sean correctas contra la implementación real; no hay prueba en
navegador real todavía (grupo 8).

## Grupo 7 — Enlace «Explicar en el asistente» del panel de anomalías, fase Green (tareas 7.2 y 7.3)

**Producto del `coder`:** solo `apps/frontend/src/pages/AnomaliesPanel.tsx` (+11/−2). En `EpisodeDetail`, entre el bloque
de Limitaciones y el de errores, un `Link` de `react-router` con el texto `Explicar en el asistente` y destino
``/assistant?episode=${encodeURIComponent(episode.id)}``, con el estilo de los botones secundarios, **fuera de la
condición `isOpen`** (se ofrece también en las cerradas) y **solo si `isAnomalyEpisodeId(episode.id)`**. Solo navega:
no hace ninguna petición ni crea conversaciones. Un comentario JSX en español justifica el porqué de cada decisión,
incluida la de Victor del 2026-10-12 de no encadenar dos llamadas desde el panel.

**Ajuste pedido por el orquestador.** El `coder` había modificado además, sin motivo, una línea existente
(`{mutation.isError && <div …` quedó como `&&<div`, sin el espacio). La PR #120 y la #121 (JUP-035) también tocan
este archivo (añaden la captura de pantalla para el chat), así que se le pidió restaurarla. El diff final solo
elimina las dos líneas de `import` que se amplían (`react-router` y `@/services/contracts`); el resto son
inserciones. Aun así habrá que reconciliar este archivo al integrar JUP-035 (se mide en la tarea 8.4).

**Tarea 7.3.** `tests/spanish-ui.test.ts` pasa sin editarlo con el texto nuevo, y `apps/frontend/GLOSARIO.md` ya
define «Asistente de IA → asistente»: el enlace no introduce ningún concepto nuevo y no se tocó.

**Evidencia Green** (2026-10-13, reejecutada por el orquestador, Windows):

- Pruebas nuevas: **19 de 19** (antes `19 failed`).
- Control sin editar: `AnomaliesPanel`, `spanish-ui`, `quality-gates`, `AnomalyEvidence` y las dos de conversaciones del
  grupo 6: en conjunto `7 archivos, 144 pruebas pasan`; solo el panel y las del enlace: `53 de 53`.
- `lint` y `typecheck`: **código 0** (códigos de salida reales).
- **Aviso de consola** `Function components cannot be given refs … Primitive.div.Slot`: **ya existía**. Sale también
  con `AnomaliesPanel.test.tsx` (que no ofrece el enlace con sus ids `anomaly-1`) y su origen es un
  `DialogDescription asChild` presente en el `develop` previo (`bfaf3983`). No es de este cambio.

**Pendiente del grupo 7:** mutación, DoD del frontend (con la suite completa) y QA.

## Grupo 7 — Enlace del panel, mutación, DoD y veredicto de QA

**Mutación** (2026-10-13). Stryker sobre las líneas añadidas (99 a 107 de `AnomaliesPanel.tsx`, con un Vitest temporal de
solo dos archivos, borrado después): **4 mutantes, 4 muertos (100 %)**. Es una muestra pequeña, porque Stryker no muta el
destino del `Link` ni el texto, así que se completó con **7 mutantes manuales** sobre exactamente eso: otro parámetro
(`?ep=`), otra ruta, el id de otra cosa, otro texto, sin codificar el id, enlace solo para abiertas y sin comprobar el
formato. **6 de 7 muertos.** El superviviente, «sin `encodeURIComponent`», es **equivalente**: un id válido
(`anomaly-` más hexadecimal) no contiene caracteres reservados, así que la dirección resultante es la misma. No hubo
supervivientes reales, por lo que no se añadieron pruebas. Es una muestra dirigida, no un barrido.

**DoD (tarea 7.4)** (sobre `8fddc0b3`; máquina calmada: 5 % de CPU y 3 GB de RAM libres):

| Control | Resultado |
| --- | --- |
| Pruebas del grupo (19) y control del panel, `spanish-ui`, `quality-gates` y las del grupo 6 | `7 archivos, 144 pruebas pasan` sin editar ninguna anterior |
| **Suite completa del frontend** (76 archivos), **2 ejecuciones seguidas** | **1238 pruebas pasan, 0 fallos, las dos veces**. La intermitencia de JUP-098 del grupo 6 no apareció: la máquina estaba calmada |
| `lint`, `typecheck`, `build` | código 0 los tres (códigos de salida reales) |
| Escaneo de secretos | 310 líneas añadidas desde `d40e122b`, 0 hallazgos |
| Archivos modificados | Solo `AnomaliesPanel.tsx` de producto (+11/−2) y la prueba nueva |

**Veredicto del agente `qa`: `accept`.** Reejecutó 53 pruebas (19 del grupo y 34 de control) y comprobó: el diff de
producto son +11/−2 y las dos líneas eliminadas son solo los `import` ampliados (se restauró la línea ajena que el
`coder` había recortado); el Red solo trae la prueba y el Green solo el producto; los tres escenarios de la spec tienen
prueba; el enlace es un `<a>` real dentro del diálogo y reutiliza `buttonStyle`, así que sigue los temas; solo navega
(conteo de `fetch`, ningún `POST` ni `PATCH`); las pruebas de id inválido llevan control positivo; y no hay `skip`,
`only`, `todo`, `any` ni `eslint-disable`. No reejecutó la suite completa, `typecheck`, `build` ni la mutación.

**Observaciones del QA, atendidas o aceptadas:**

1. **La desviación de la spec no constaba en ella** (la spec decía «en cualquier estado» sin la condición del formato
   del id; solo la prueba y un comentario la documentaban). **Atendida:** se añade a
   `specs/anomalies-panel/spec.md` del change la frase sobre el formato y el escenario «Identificador sin el formato
   real» (4 escenarios en esa spec, 44 en total en las tres; el bloque `Human Approval` conserva las cifras del gate) y
   una frase a la decisión 10 del `design.md`. Es una adición, no una retirada de escenarios.
2. No hay prueba de tema claro y oscuro: no es necesaria porque el enlace reutiliza `buttonStyle`; la revisión visual del
   grupo 8 la cubre.
3. Para el grupo 8, comprobar en el navegador con el stack real que el clic desde el diálogo deja la anomalía
   preseleccionada en el asistente, que **no hay ningún `POST` hasta pulsar «Enviar»**, que el caso del id que no está
   en el cliente avisa sin elegir ninguna y que el parámetro se quita con `replace` tras un envío correcto. Los ids de
   los datos de demostración deben tener el formato `anomaly-<64 hex>` (los genera el backend con un SHA-256, así que
   lo cumplen).

**Reconciliación con JUP-035.** Las PR #120 y #121 también modifican `AnomaliesPanel.tsx` (añaden una captura de pantalla
para el chat). El cambio de este grupo son nueve líneas de producto en un bloque propio y dos líneas de `import`
ampliadas; lo único que puede dar conflicto textual son esas dos líneas. Se medirá en la tarea 8.4.

**Estado del grupo 7:** tareas 7.1 a 7.4 hechas; mutación sin supervivientes reales; DoD en verde; QA en `accept`.
**El frontend de la tarjeta está completo.**
