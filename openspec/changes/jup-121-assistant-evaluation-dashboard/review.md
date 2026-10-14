# Revisión de jup-121-assistant-evaluation-dashboard

JUP: JUP-121 · [Trello](https://trello.com/c/aIdxwsXR) · ADR: [ADR-0022](../../../docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md)

## Resumen

Pendiente hasta cerrar la implementación.

## Excepciones doc-only

Las tareas sin código de producto no pasan por tester, coder ni mutación; se verifican con `openspec:validate` y `jup:check`.

| Tarea | Entregable | Verificación |
| --- | --- | --- |
| 1.1 | `docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md`, fila en `docs/adr/README.md` y enlace desde `design.md` | `openspec:validate` 70/70 y `jup:check` en verde |
| 1.2 | `docs/validation/evaluation-dashboard.md` (contrato `rows-v1`, manifiesto, clasificación, comparabilidad y juicio humano); `design.md` y la tarea 2.7 ajustados para incluir los recuentos `pass`/`fail` entre lo que depende de juicio humano, y la columna `selected` | `openspec:validate` y `jup:check` |
| 1.3 | `docs/validation/evaluation-runs.json` (`manifest_version` 1) con las cinco entradas de hito: JUP-070 ejecuciones 1 y 2, benchmark de JUP-078, calibración de JUP-022 y entrada de JUP-068; las cinco rutas existen | `openspec:validate` y `jup:check` |

## Evidencia TDD por tarea

Método de mutación para `tools/evaluation-dashboard.py`: no hay runner Python que maneje el nombre con guion (mutmut necesita un módulo importable), así que se usa un mutador mínimo basado en `ast` (comparaciones, `and`/`or`, `not`, aritmética, constantes, `if`, `return`, `raise`, `break`/`continue`) que vive fuera del repositorio. Apunta la misma suite a una copia mutada con la variable `EVALUATION_DASHBOARD_TOOL` (los tests de este change la leen), desactiva el bytecode (con la caché `__pycache__` mutantes de igual tamaño escritos en el mismo segundo reutilizaban el `.pyc` anterior y daban supervivientes falsos) y se niega a puntuar si el baseline sin mutar no pasa. Los tests se organizan en un fichero nuevo por tarea o remediación porque el candado del harness congela los ya commiteados.

### 2.1 Lectura y validación de manifiestos

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_manifest.py` (44 tests), commit `94655072`; falla porque `tools/evaluation-dashboard.py` no existe (`FileNotFoundError` al cargar el módulo) |
| Green | `tools/evaluation-dashboard.py` (`ROOT`, `FORMATS`, `IDENTIFIER_RE`, `ManifestError`, `read_manifest`, `merge_manifests`), commit `4e7d4d2c`; 44/44 |
| Mutación | Primera pasada válida 102/140 (72,9 %). `scripts/tests/test_evaluation_manifest_errors.py` (18 tests, commit `f9f1a595`) fija el formato `<manifiesto>: <campo>: <problema>`, el índice `runs[i]`, la redacción propia del JSON inválido y la conversión de los fallos de disco al resolver rutas. Segunda pasada **115/140 = 82,1 %**, 62 tests |
| Supervivientes | 25, todos de prosa de mensajes (por ejemplo `'XXdebe ser una lista'`). Se aceptan: el contrato fija fichero y campo, no la frase. Ninguno toca comparaciones, `raise`, `if`, `return`, bucles ni `and`/`or` |
| DoD | Lint, type-check y escaneo de secretos en verde. Regresión: ver la excepción de entorno de abajo |
| QA | `accept`, sin hallazgos BLOCKING ni MEDIUM. Reprodujo la mutación (115/140) y mató 18 mutantes manuales de lógica adicionales (`fullmatch`→`match`, `type() is`→`isinstance`, `utf-8-sig`→`utf-8`, resolver contra el cwd, una sola pasada de validación, no registrar duplicados, entre otros) |

Hallazgos LOW del QA: el mutador no está en el repositorio (se documenta el método aquí); `"abc\n"` no aparece como caso explícito, aunque el mutante `fullmatch`→`match` muere; el cableado de `evaluation-dashboard:test` en `package.json` y en la CI es la tarea 3.4.

### Excepción de entorno del DoD (regresión de la suite completa)

La regresión de `check-dod.mjs` no se ha podido dejar en verde por causas ajenas a este change:

1. Con el Python global falta `langchain_core` (dependencias del processor). Con el entorno virtual del proyecto en el `PATH` esa suite pasa; los siguientes DoD se lanzan así.
2. Con el entorno virtual, 1 de 887 pruebas del frontend falla en la suite completa (`tests/login-session-expired-notice.test.tsx`, «tarea 4.1»; en una pasada fueron 2) y pasa 9/9 en solitario. Es la misma inestabilidad por carga de CPU que ya registró JUP-119.
3. `git diff origin/develop --stat -- apps packages package.json pnpm-lock.yaml turbo.json` está vacío: la rama solo añade ficheros de documentación, OpenSpec, `tools/` y tests, así que no puede afectar a esas pruebas.

El QA valoró la excepción como bien justificada.

### 2.2 Adaptador del informe de JUP-070

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_adapter_jup070.py` (87 tests), commit `c6323257`; todos fallan por `adapt_jup070`, `AdapterError` y `RUN_KEYS` ausentes, ninguno pasa por accidente |
| Green | `adapt_jup070` y constantes en `tools/evaluation-dashboard.py`, commit `06d215b7`; 149/149 con la capa de manifiestos |
| Mutación (1.ª) | 202/226 (89,4 %). Huecos reales: catálogo ilegible sin test, nombre de campo en errores de forma, fila `behavior="all"` de GRD-2 no medida, y un **defecto**: una métrica conocida con forma interna rota lanzaba `KeyError`/`TypeError`/`AttributeError` crudos |
| Remediación | `test_evaluation_adapter_jup070_robustness.py` (27 tests; 16 en rojo por el defecto, commit `9aa280f6`) y Green de la validación de forma explícita (más quitar la rama `Z`→`+00:00`, muerta desde Python 3.11), commit `64cee586`; 176/176 |
| Mutación (2.ª) | 234/263 (89,0 %) sobre todo el módulo salvo los manifiestos |
| QA (1.ª) | `changes-requested`: M1, un `raise` de `k`/`n` no enteros sin test (yo había ocultado ese superviviente al filtrar los de prosa; ahora se revisan todos uno a uno). `test_evaluation_adapter_jup070_counts.py` (8 tests, commit `2f07a377`) lo cubre y fija la ruta anidada en el mensaje |
| Mutación (final) | **237/263 = 90,1 %**, 184 tests. Los 26 supervivientes son prosa de mensajes o la etiqueta de ruta dentro del texto (`'XXjudged'`, `'XXgroups'`, `'XXstages'`: el campo sigue en el mensaje) |
| DoD | Lint, type-check y secretos en verde. Regresión: la excepción de entorno de abajo |

Hallazgos del QA trasladados: M2 (validar también la salida de los adaptadores en 2.6, ya añadido a esa tarea), L1 (un catálogo sin `metrics` daría `KeyError`; riesgo de integridad del repositorio, se deja), L2 (negativos y `k > n` se copian; decidir en 2.6), L4 (dos reglas añadidas al contrato) y L5 (el estado del documento se actualiza en la tarea 6.2).

### Excepción de entorno del DoD, ampliada

En la pasada de la 2.2 la regresión falló por 145 pruebas del backend en las suites de salud del proveedor (`test_system_health_jup047.py` y `test_health_provider_*_jup047.py`), que es exactamente el hallazgo `RF-119-004` ya registrado (`AttributeError: 'ProactorEventLoop' object has no attribute '_ssock'` en esta máquina, con o sin los cambios). Con la de la 2.1 (una prueba inestable del frontend que pasa sola), la regresión completa no puede quedar en verde en este entorno por causas ajenas al change. Mientras `git diff origin/develop --stat -- apps packages package.json pnpm-lock.yaml turbo.json` siga vacío, el DoD de cada tarea exige lint, type-check, escaneo de secretos y todas las suites de `scripts/tests/test_evaluation_*.py` en verde, y que la regresión completa solo falle en esos casos conocidos.

### 2.3 Adaptador del benchmark de JUP-078

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_adapter_jup078.py` (80 tests), commit `c5006620`; los 170 errores (con `subTest`) son `AttributeError` por `adapt_jup078` ausente, ninguno pasa por accidente. El tester comprobó que los esperados son alcanzables con una implementación de referencia fuera del repositorio |
| Green | `adapt_jup078` y su sección en `tools/evaluation-dashboard.py`, commit `cb7a61da`; 264/264 |
| Mutación | Solo la sección nueva (`--from-line`): **115/127 = 90,6 %**. Los 12 supervivientes son prosa de mensajes tras el prefijo `<campo>: `. Esta vez no hizo falta remediación: el tester endureció los tests desde el principio (fronteras `successful` = `cases` ± 1, bool frente a entero, tres modelos con valores distintos, denominador `successful` frente a `cases`) |
| QA | `accept`, sin hallazgos BLOCKING ni MEDIUM. Reconstruyó las 10 filas del informe real por su cuenta, reprodujo la mutación (115/127) y mató 37 de 38 mutantes manuales de lógica; el superviviente es `models` aceptando una tupla, equivalente porque `json.loads` nunca la produce |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend, idénticos a los de la 2.2 (`RF-119-004`); el frontend pasó entero esta vez |

Decisión de contrato: con `successful == 0`, `tools/llm-benchmark.py::summarize` escribe `mean_keyword_score: 0` y ese 0 significa «sin datos», así que `keyword_score`, `latency_p95` y `cost` salen no medidos aunque el informe traiga un número; con `successful > 0` un cero sí es una medición.

Hallazgos LOW del QA, resueltos en el contrato: `synthetic` de JUP-078 es siempre `false` (sus «casos sintéticos» son preguntas públicas, no una ejecución sintética) y el vocabulario nuevo (`keyword_score`, `latency_p95`, `cost`, `puntuacion`, `usd`) queda en la fila de JUP-078 de «Qué toma cada adaptador».
