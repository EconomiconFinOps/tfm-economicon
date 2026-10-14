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
