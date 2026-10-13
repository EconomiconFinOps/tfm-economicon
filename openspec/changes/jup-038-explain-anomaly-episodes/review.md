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
