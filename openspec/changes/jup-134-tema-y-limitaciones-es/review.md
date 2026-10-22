JUP: JUP-134
Trello: https://trello.com/c/zg2LSCjb/126-jup-134

# Revisión del change `jup-134-tema-y-limitaciones-es`

Documento en curso: se completa grupo a grupo durante el apply.

## Grupo 1: selector de tema con el tema activo (tareas 1.1 a 1.5)

### Resultado

El botón de tema muestra «Tema claro» con el tema claro activo y «Tema oscuro» con el oscuro, sin `aria-pressed` y con un `title` que describe la acción al pulsar. No cambia `useTheme`.

### Evidencia Red / Green / mutación

- **Red** (commit `69b4527b`): `ThemeToggle.test.tsx` (nuevo, 18 casos) y los ajustes de `useTheme.test.tsx` (de 11 a 13 casos) y `brand-spec.guard.test.tsx`. Con el producto antiguo fallaban 22 casos y pasaban 20. Entre estos, 6 de `ThemeToggle.test.tsx` que ya pasaban son guardas de no regresión (iconos `aria-hidden`, valor guardado inválido, `data-theme` y persistencia, y los casos que coincidían con el texto antiguo).
- **Excepción del candado `lock-committed-tests`**: las tareas 1.1 y 1.3 reescriben dos tests ya commiteados, que el hook impide editar. El tester preparó las versiones nuevas fuera del repo y generó un parche; lo aplicó la persona responsable de la rama con `git apply`, con aprobación expresa, y el commit Red incluye ese resultado. La Red se probó con copias temporales de esos ficheros, ya borradas.
- **Green** (commit `021dc931`): solo cambia `apps/frontend/src/components/ThemeToggle.tsx` (texto según `isDark`, `aria-pressed` fuera, `title` con la acción). 42 de 42 casos en verde en los tres ficheros.
- **Mutación** (Stryker 10.0.0, solo `ThemeToggle.tsx`, con los tres tests del selector): 9 mutantes, 9 muertos, 0 supervivientes, 0 sin cobertura. Puntuación 100 %. Se ejecutó con una configuración temporal de Vitest acotada a esos tests, ya eliminada.

### Comprobaciones

| Comprobación | Resultado |
| --- | --- |
| Pruebas del selector (`ThemeToggle.test.tsx`, `useTheme.test.tsx`, `brand-spec.guard.test.tsx`) | 42 de 42 |
| Frontend completo (vitest) | 1400 pruebas en 93 ficheros, OK |
| `lint` del frontend | 0 errores y 1 aviso previo (`ChatPresentation.tsx:101`, `react-hooks/exhaustive-deps`) |
| `typecheck` del frontend | OK |
| Escaneo de secretos del DoD | OK |
| Backend (pytest, venv `.venv-tfm`) | **No ejecutable completo en esta máquina**: 210 fallos y 102 errores por `tokenizer.json`, un artefacto generado que solo existe tras construir la imagen y que no está en el repositorio. Este grupo no toca ningún fichero de `apps/backend`; lo ejecuta la CI. Las pruebas de anomalías (`test_anomaly_explanations.py`, 75) pasan |
| Procesador (pytest) | **No ejecutable en esta máquina**: falta el módulo `markdown_it`. No se toca `apps/processor`; lo ejecuta la CI |

El DoD (`check-dod.mjs`) queda en rojo en local solo por los dos puntos anteriores, que son del entorno y no del cambio.

### QA

Veredicto del agente `qa`: **accept**. Reprodujo las pruebas, el lint y el type-check; revisó que cada escenario de la spec del control de tema tiene un test y que el parche a los tests existentes no pierde ni debilita cobertura (cada `aria-pressed` pasó a comprobar texto y ausencia del atributo). Comprobó la sensibilidad con cinco cambios manuales en `ThemeToggle.tsx` y los revirtió:

| Cambio manual | Casos que fallan |
| --- | --- |
| Textos de las dos ramas invertidos | 27 |
| `title` invertido | 3 |
| `aria-pressed={isDark}` reintroducido | 6 |
| `aria-label="Tema"` añadido | 25 |
| `aria-hidden` quitado del icono de la luna | 1 |

No hubo hallazgos. Quedó sin comprobar en esa pasada: la mutación Stryker (se reprodujo en este documento por quien orquesta), la suite completa del frontend y la comprobación en navegador (tarea 4.1).

### Pendientes detectados

- `apps/frontend/README.md:131` menciona el botón «Tema oscuro»: tarea 3.1.
- `docs/continuidad/identidad-marca-frontend.md`: revisar si describe el botón con ese literal: tarea 3.2.

## Grupo 2: limitaciones de los episodios en español (tareas 2.1 a 2.4)

### Resultado

`LIMITATIONS` de `anomaly_episodes.py` contiene ahora las cinco frases en español, con el mismo texto, carácter a carácter, y el mismo orden que la traducción `LIMITATIONS_ES` que ya usaba el asistente. `anomaly_explanations.py` importa esa lista y `LIMITATIONS_ES` desaparece, de modo que la API de episodios, el panel y la explicación del asistente comparten una sola lista. No cambian `SCHEMA_VERSION`, `ADAPTER_VERSION` ni el cálculo del identificador de evidencia.

### Evidencia Red / Green / mutación

- **Red** (commit `1c4d9470`): `test_anomaly_episode_limitations_es.py` (nuevo, 10 casos) y ajuste de `test_anomaly_explanations.py`. Con el producto antiguo fallaban 11 casos y pasaban 74. Entre los casos del fichero nuevo, uno pasaba de entrada: la guarda de cardinalidad y de `cause_status`.
- **Excepción del candado `lock-committed-tests`**: la tarea 2.2 reescribe dos pruebas de `test_anomaly_explanations.py`, ya commiteado. Como en el grupo 1, el tester preparó la versión nueva fuera del repo y la persona responsable de la rama aplicó el parche con `git apply`. La Red de esa versión se probó con una copia temporal ya borrada. Del test antiguo solo se pierde `all(spanish != original ...)`, que carece de sentido sin versión en inglés; se conservan `LIMITATIONS_ES_LITERAL` como redacción esperada, el número de frases y el tipo.
- **Green** (commit `27df989c`): solo `anomaly_episodes.py` (14 líneas) y `anomaly_explanations.py` (18 líneas). 105 casos en verde en los tres ficheros del grupo.
- **Mutación**: `mutmut` no es viable en esta máquina (no está instalado y no se admite en Windows), así que se aplicaron mutantes deliberados con un script que restaura cada fichero con `git checkout`. Se cubrieron el orden, el borrado, la duplicación, una frase en inglés, el recorte de una frase, la tupla, la referencia compartida en el episodio y en la evidencia, la evidencia vacía o invertida, el texto sin viñetas, sin la última o sin encabezado, la reaparición de `LIMITATIONS_ES` y una copia propia en el asistente. Resultado final: **15 de 15 muertos, 0 supervivientes**. Un mutante inicial era un error de sintaxis, no una mutación válida, y se sustituyó por una tupla válida.
- **Mutante superviviente detectado por el QA y remediado**: quitar `list(...)` en `"limitations": list(LIMITATIONS)` de la evidencia (`anomaly_explanations.py:251`) dejaba las 105 pruebas en verde. Antes lo detectaba el tipo tupla de `LIMITATIONS_ES`; al ser ahora listas las dos constantes, ningún test cubría el alias. El tester añadió `test_anomaly_evidence_limitations_copy.py` (commit `791e9426`, 3 casos); ahora el mutante muere (3 fallos) y se incorporó al script como M15.

### Comprobaciones

| Comprobación | Resultado |
| --- | --- |
| Ficheros del grupo (`test_anomaly_episode_limitations_es.py`, `test_anomaly_explanations.py`, `test_anomaly_explanations_mutants.py`, `test_anomaly_evidence_limitations_copy.py`) | 108 de 108 |
| Backend con `-k anomaly` | 555 pruebas en verde y 143 omitidas (CockroachDB opt-in, sin `JUP086_COCKROACH_TEST_URL`) |
| Backend completo (pytest, venv `.venv-tfm`) | 2278 en verde, 210 fallos y 102 errores. Los 210 y 102 son **idénticos a la base de antes del grupo** (2268 en verde, 210 fallos, 102 errores), todos por `tokenizer.json`, un artefacto generado que solo existe tras construir la imagen y no está en el repositorio. Las 10 pruebas nuevas explican la diferencia de 2268 a 2278 |
| `corepack pnpm lint` | OK (4 de 4 tareas) |
| Procesador (pytest) | **No ejecutable en esta máquina**: falta el módulo `markdown_it`. No se toca `apps/processor`; lo ejecuta la CI |

### QA

Primera pasada: **changes-requested** por un único hallazgo, el mutante superviviente descrito arriba, de tests y no de producto, que correspondía al tester. El QA confirmó además que las cinco frases son idénticas a las de `LIMITATIONS_ES` anterior (comparadas con `ast`), que el commit Green no toca nada más y que cada escenario de la spec tiene un test. Con cambios propios (una palabra de una frase, quitar `list()`, invertir o intercambiar viñetas, añadir una sexta limitación) comprobó que fallan entre 9 y 16 casos, salvo el del hallazgo.

Segunda pasada: **accept**. El mutante muere con los tres casos nuevos y otros cinco mutantes propios mueren (entre 6 y 18 fallos cada uno). Tiene los comentarios en español y no hay `skip`.

**Hallazgo no bloqueante aceptado.** Los casos 2 y 3 de `test_anomaly_evidence_limitations_copy.py` mutan una lista que, si reapareciera el alias, sería la global `LIMITATIONS`, y la dejarían contaminada para otros tests (de ahí los 17 y 18 fallos en cascada de algunos mutantes). Con el código correcto no hay contaminación y el primer fallo señala la causa. Una mejora opcional sería restaurar la lista en un `try/finally` o con un fixture; no se aplica en este change.

### Riesgo del identificador de evidencia

Se comprobó con Grep que `anomaly-explanation:` solo se calcula en `anomaly_explanations.py`, que ningún test fija un hash concreto y que ningún código lee `evidence.episode.limitations` de explicaciones guardadas (el frontend usa `evidence.limitations`). El riesgo documentado en `design.md` se sostiene.

### Pendientes detectados

- `openspec/specs/cost-anomaly-episodes/spec.md` se actualiza al archivar el change.
- Los documentos de continuidad y el README del frontend se tratan en el grupo 3.

## Grupo 3: documentación (tareas 3.1 y 3.2)

Tarea doc-only: mutación N/A y sin ciclo Red/Green (no cambia código de producto ni tests).

- `apps/frontend/README.md`: el botón de tema alterna y muestra el tema activo («Tema claro» o «Tema oscuro»).
- `docs/continuidad/identidad-marca-frontend.md`: nota de «Qué tocar si cambia algo» sobre el texto del conmutador (sin `aria-pressed`, nombre accesible igual al texto, `title` con la acción) y las tres pruebas que hay que actualizar si cambia.
- `docs/continuidad/frontend-espanol.md`: excepción de JUP-134 en «Límites» (limitaciones de los episodios en español en origen, una sola lista, efecto sobre el identificador de evidencia, y las limitaciones de `app/schemas/anomalies.py` que quedan fuera con su motivo).
- `docs/continuidad/README.md`: las filas de las dos notas, con la fecha 2026-10-22.
- `docs/api/anomaly-explanations.md` ya decía que las limitaciones van en español, y ninguna otra documentación describe las limitaciones en inglés (Grep sin resultados), así que no se toca.
