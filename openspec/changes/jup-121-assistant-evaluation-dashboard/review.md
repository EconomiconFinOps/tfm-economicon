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

### 2.4 Adaptador de la calibración de JUP-022

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_adapter_jup022.py` (118 tests), commit `905e47af`; los 377 errores (con `subTest`) son `AttributeError` por `adapt_jup022` ausente. El tester comprobó con una implementación de referencia fuera del repositorio que los esperados son alcanzables y que 12 de 13 mutantes de ella morían (el otro es equivalente) |
| Green | `adapt_jup022` y su sección en `tools/evaluation-dashboard.py`, commit `ac6685c0`; 382/382 |
| Mutación | Solo la sección nueva: **222/242 = 91,7 %**. Los 20 supervivientes son prosa de mensajes tras el prefijo `<campo>: `, revisados uno a uno con su diff |
| QA | `accept`, sin hallazgos BLOCKING. Recalculó por su cuenta las 140 filas (28 puntos × 5), los numeradores, los 20 `selected` y la huella del corpus con 0 diferencias, y mató 58 de 58 mutantes manuales de lógica |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend idénticos a los de 2.2 y 2.3 (`RF-119-004`) |

Decisiones de contrato: una tasa sobre cero casos es «sin datos», no 0; el numerador solo se reconstruye cuando `round(rate × casos)` reproduce la tasa con tolerancia 5e-5 (el informe redondea a 4 decimales); `by_category` no se publica porque trae tasas sin denominador; la huella `corpus_sha256` se deriva (sha256 de las líneas `clave=sha256` ordenadas por clave) y no depende de rutas; `points` vacía solo es válida si `selection.candidates` también lo está.

Hallazgos del QA resueltos o trasladados: M1, la clave de comparabilidad incluye ahora `suite_version` porque JUP-022 no trae `suite_sha256` (documentado y añadido a la tarea 2.7); L1 y L2, contrato aclarado (varios candidatos seleccionados; `retrieval` del `run` solo con el troceado); L3, el `behavior` de un `top_k` absurdo lo recogerá la validación común de 2.6; L4, qué hacer con un informe sin filas, trasladado a la tarea 2.8; L5 se acepta (se copia, no se recalcula).

### 2.5 Adaptador de las métricas de negocio de JUP-068

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_adapter_jup068.py` (103 tests), commit `8b698abe`; 496 errores (con `subTest`), todos `AttributeError` por `adapt_jup068`, `read_business_report` y `subprocess` ausentes, ninguno pasa por accidente. Los esperados se comprobaron con una implementación de referencia fuera del repositorio |
| Green | `adapt_jup068` y `read_business_report` con su sección en `tools/evaluation-dashboard.py`, commit `06852dc7`; 485/485 |
| Mutación (1.ª) | 227/249 (91,2 %). Superviviente de lógica: `pairs > 0` → `pairs > 1` (ningún test usaba exactamente una pareja elegible). Además se encontró un **defecto latente** en `_is_number`, compartido por los adaptadores de JUP-078, JUP-022 y JUP-068: un entero como `10**400` lanzaba `OverflowError` crudo |
| Remediación | `test_evaluation_adapter_jup068_gaps.py` (9 tests: 4 de una pareja y 5 en rojo del defecto, commit `eacfb7e2`) y Green de `_is_number` (commit `533cfae6`); 494/494 |
| Mutación (final) | Sección de JUP-068: **228/249 = 91,6 %**, 21 supervivientes de prosa. `_is_number`: 5/7, los 2 restantes son equivalentes (`return False` → `return None`, igual de falsos para quien llama) |
| QA | `accept`, sin hallazgos BLOCKING. Recalculó por su cuenta las 23 filas con Node real (y 6 casos extremos) con 0 diferencias, probó rutas con `&`, `;` y `$(…)` sin inyección y mató 56 de 63 mutantes manuales de lógica; los supervivientes eran equivalentes salvo `shell=True` y tres excepciones sin test |
| Tests del QA | `test_evaluation_adapter_jup068_cli.py` (9 tests, commit `66a728ec`): la llamada es una lista sin `shell` con la ruta intacta, la primera línea no vacía de `stderr`, `ValueError`/`OSError`/`SubprocessError` al ejecutar, `RecursionError` al parsear y la ruta relativa desde la raíz; cada uno mata su mutante. Total 503/503 |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend idénticos (`RF-119-004`) |

Hallazgos del QA trasladados: `run_id` del informe de JUP-068 es texto libre en Node y el cargador de 2.8 deberá pasarlo (2.6 lo rechaza si no cabe en `IDENTIFIER_RE`); `suite_sha256` es la huella del registro entero, así que dos ejecuciones de negocio con el mismo `dataset_version` y datos distintos no comparten clave (hoy no hay serie de tipo B); `run_at` `null` deja las ejecuciones de negocio fuera de las series y los paneles de tipo B deben mostrar «fecha no registrada»; el contrato describe ya el criterio no uniforme de «no medido» (sumas de nada frente a importes copiados).

### 2.6 Validación común de filas y adaptador rows-v1

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_rows_contract.py` (150 tests), commit `51aaaa9d`; 1050 errores (con `subTest`), todos `AttributeError` por `validate_rows` y `adapt_rows_v1` ausentes. El tester comprobó con una referencia fuera del repositorio que los esperados son alcanzables y que 37 mutantes de ella morían |
| Green | `validate_rows` y `adapt_rows_v1` con su sección en `tools/evaluation-dashboard.py`; 653/653. La validación se aplica a la **salida de los cuatro adaptadores** (hallazgo M2 del QA de 2.2) además de a la entrada `rows-v1` |
| Mutación (1.ª) | 235/267 (88,0 %). De los 32 supervivientes: 25 de prosa de mensajes, 5 sobre las tuplas de claves «obligatorias» de la entrada (equivalentes: la clave que falta se rellena con `None` y `validate_rows` la rechaza con el mismo prefijo de ruta) y 2 de lógica real: la tupla de campos prohibidos de `not_measured` no probaba `ci_low`/`ci_high`. `test_evaluation_rows_contract_gaps.py` (13 tests, commit `c65ac7da`) los cubre |
| QA (1.ª) | `accept` con 3 MEDIUM. M1: `datetime.fromisoformat` de Python 3.13 acepta cualquier separador (comilla, `;`, NUL) y `run_at` acaba en un script SQL. M2: ni `count` ni `denominator` tenían cota (`10**400`, `2**63`) y no caben en una columna `bigint`. M3: el contrato sin commitear |
| Remediación | `test_evaluation_rows_contract_bounds.py` (36 tests, 97 fallos en rojo, commit `2735168c`): `run_at` con formato exacto sin citar el valor recibido, `ROW_MAX_INTEGER = 2^53 - 1` y los órdenes de error con dos defectos a la vez. Fix en `tools/evaluation-dashboard.py` (commit `f06be2e2`) |
| Excepción de proceso | Dos tests antiguos de `test_evaluation_rows_contract.py` (un `run_at` sin zona y `value = 10**300`) contradecían el contrato endurecido y el candado del harness impide editar tests commiteados. Lo cambió el usuario a mano, quitando exactamente `"2026-10-08T20:13:54"` y `10 ** 300` (commit `afef8419`); no se debilitó nada más |
| Mutación (final) | Funciones tocadas: 31/34 = 91,2 %, los 3 supervivientes son prosa. El QA mató 22 de 28 mutantes manuales nuevos; los 6 restantes son equivalentes (defensa en profundidad de la regex frente a `fromisoformat`) |
| QA (final) | `accept` sin hallazgos BLOCKING ni MEDIUM. Acepta las salidas reales (`2026-10-08T21:01:44Z`, `2026-10-03T07:15:32.826486+00:00`) y rechaza la inyección; el alfabeto de identificadores deja fuera comillas, NUL, saltos de línea, espacios y caracteres no ASCII |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend idénticos (`RF-119-004`) |

Hallazgos LOW trasladados: nombres de clave desconocidos dentro de los mensajes (2.8 los escapa o trunca); `run.retrieval` sin cota de enteros (3.1 lo guarda como `jsonb`); los identificadores admiten `--` y `,` en medio, inofensivo con literales escapados (3.1 nunca interpola sin escapar).

### 2.7 Clasificación de ejecuciones, clave de comparabilidad y tabla de juicio

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_classification.py` (88 tests), commit `73185b5c`; 235 errores, todos `AttributeError` por símbolos ausentes (el único fallo de aserción es el de determinismo entre procesos, que falla porque el proceso hijo no encuentra `comparability_key`). Esperados comprobados con una referencia fuera del repositorio |
| Green | Sección «Clasificación de ejecuciones y clave de comparabilidad» (`NON_REAL_REASONS`, `classify_run`, `comparability_key`, `AUTOMATIC_METRICS`, `unclassified_metrics`, `CLASSIFICATION_KEYS`, `classify_run_row`), commit `b8777894`; 790/790 |
| Mutación | **92/97 = 94,8 %**. 5 supervivientes: 4 de prosa y `ensure_ascii=True` → `False`, equivalente para ejecuciones válidas (todos los campos son ASCII por la regla 3) |
| QA | `accept`, sin hallazgos BLOCKING ni MEDIUM. Recalculó por su cuenta los motivos y las cinco claves con `hashlib`, verificó el determinismo con `PYTHONHASHSEED` 0, 1 y 12345, que las dos ejecuciones de JUP-070 no forman serie y que `AUTOMATIC_METRICS ∪ HUMAN_METRICS` es el catálogo exacto; mató 66 de 71 mutantes manuales (los 5 restantes, equivalentes) |
| Tests del QA | `test_evaluation_classification_gaps.py` (6 tests) fija `ensure_ascii=True` con un valor no ASCII y que `unclassified_metrics({})` no carga el catálogo real; cada uno mata su mutante |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend idénticos (`RF-119-004`) |

Resultado con los datos reales: JUP-070 run-1 `("plantilla","doble")`, run-2 `("plantilla",)`, JUP-078 y JUP-022 reales, JUP-068 `("sintetica",)`; las cinco claves de comparabilidad son distintas. La clave incluye `suite_version` (hallazgo M1 del QA de 2.4) y `design.md` queda alineado.

Hallazgos trasladados: la tabla de juicio por fila (calibración, benchmark, recuentos de casos) no pasa por `unclassified_metrics`, que solo cubre el catálogo de JUP-067; `classify_run_row` debe aplicarse al `run` crudo (tarea 2.8), y `comparability_key` no revalida el `run` (lo hace `classify_run`).

### 2.8 Normalización de entradas y subcomando `rows`

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_rows_command.py` (114 tests), commit `5bc48986`; 117 errores, todos `AttributeError` por símbolos ausentes; la CLI se prueba por `subprocess` real y Node. Esperados comprobados con una referencia fuera del repositorio (21 de 22 mutantes morían; el restante se cubrió con un test que parchea la salida de cada adaptador) |
| Green | `derive_run_id`, `report_digest`, `normalize_entry`, `build_dataset`, `main` (CLI `rows`) y el escape de nombres de clave en los mensajes, commit `03b67226`; 910/910. `python tools/evaluation-dashboard.py rows` imprime las 5 ejecuciones reales (48, 48, 10, 140 y 23 filas) |
| Mutación (1.ª) | 133/181 (73,5 %) sobre la sección. Supervivientes: unos 35 de prosa (mensajes, textos de ayuda de `argparse`) y ramas defensivas sin test que añadió el coder: error al escribir `--output`, fecha extrema que desborda al pasar a UTC, JSON anidado, informe de negocio sin `run_id` y etiqueta de fichero del duplicado. `test_evaluation_rows_command_gaps.py` (13 tests, commit `c826f4ab`) mata los 7 mutantes |
| QA | `accept`, sin BLOCKING. Recalculó por su cuenta los `run_id` derivados y las 5 huellas, comprobó que no cambian reescribiendo los informes con CRLF y otra sangría, probó la CLI (salida idéntica byte a byte entre ejecuciones, `--output` atómico, códigos 0/1/2, ninguna ruta absoluta con el informe fuera de la raíz, alfabeto cerrado en las 269 filas) y mató 68 de 71 mutantes manuales |
| Remediación | M1 (la raíz de `report_path` debe resolverse), L1 (un `OSError` al leer no cita la ruta) y **L2, un defecto real**: en Windows `sys.stdout.write` convertía `\n` en `\r\n`, así que `rows > f` y `--output f` daban bytes distintos. `test_evaluation_rows_command_stdout.py` (9 tests, 2 en rojo, commit `d4e7d6b8`); fix en `main` (commit `0424e713`, salida en bytes UTF-8); 932/932 |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend idénticos (`RF-119-004`) |

Decisiones de contrato: un informe sin filas es un error; la huella se calcula sobre el JSON canónico del documento parseado y no sobre los bytes (el fin de línea cambia con `autocrlf` y los `run_id` derivados deben ser iguales en todas las máquinas); `report_path` solo se registra para informes dentro del repositorio con alfabeto cerrado (una ruta absoluta local puede llevar nombres de usuario); los errores citan la ruta relativa o solo el nombre del fichero.

Hallazgos LOW trasladados: los mensajes de JUP-068 repiten el nombre del fichero (`bad68.json: business-metrics: bad68.json: …`) y la capa de manifiestos cita rutas absolutas en sus errores, código previo de 2.1 que no se cambia; la huella de JUP-068 es la de la entrada, así que un cambio en `business-metrics.mjs` no cambia el `run_id`.

### 3.1 Generación del script SQL y subcomando `sql`

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_sql.py` (116 tests), commit `1c696753`; 0 en verde (`AttributeError` por símbolos ausentes y «invalid choice: 'sql'» en la CLI). Esperados comprobados con una referencia fuera del repositorio, cuyos 34 mutantes morían |
| Green | `SCHEMA_DDL`, `sql_literal`, `build_sql`, `SqlError` y el subcomando `sql` (parser padre común con `rows`, despacho por `args.command`), commit `ec0c8e56`; 1048/1048 |
| Mutación | Sección contra su fichero de tests: 217/268 (81,0 %). Supervivientes: prosa y ayuda de `argparse`, ramas cubiertas por otros ficheros (escritura atómica, `required=True` del subparser) y los **prefijos exactos de ruta de los errores de forma** de `build_sql` (clave desconocida en la raíz, `results` que no es lista, `run` mal formado, duplicado de `run_id`). `test_evaluation_sql_shape.py` (15 tests, commit `67b5a380`) mató esos y otros 3 mutantes |
| QA | `accept`, sin BLOCKING ni MEDIUM. **Ejecutó el script en un PostgreSQL 17 real** (`pgvector/pgvector:pg17`, contenedor desechable y limpiado): carga correcta con 5 ejecuciones y 269 filas; tres cargas seguidas dejan lo mismo; un fallo a mitad de script deja los datos anteriores intactos (hash md5 idéntico); las `CHECK` rechazan un `not_measured` con valor y un `measured` sin valor; la ida y vuelta con `rows` no tiene ninguna diferencia en 3766 celdas (267 floats); cadenas hostiles (`x'); DROP SCHEMA evaluation; --`, saltos de línea, barras invertidas, unicode) se cargan como dato, también con `standard_conforming_strings` desactivado en la base; `\x00` da `SqlError`. Mató 66 de 70 mutantes manuales |
| Tests del QA | `test_evaluation_sql_literal_gaps.py` (19 tests): subclases hostiles de `int`, `float`, `str` y `list` rechazadas, y el texto literal `\u0000` dentro de `jsonb` no es un NUL (regla de la paridad de barras) |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend idénticos (`RF-119-004`) |

Esto adelanta la mayor parte de la comprobación manual de la tarea 5.1 (conciliación con PostgreSQL real), que aun así se automatizará como prueba repetible.

Hallazgos LOW trasladados: las dos `CHECK` no tienen nombre (los mensajes de PostgreSQL son `results_check` y `results_check1`; no se cambia para no tocar tests que comparan el DDL exacto); las tablas con `IF NOT EXISTS` no migran bases ya cargadas (documentado en la guía); a la tarea 3.3: el rol y los permisos van en un script aparte y después del esquema, `CREATE ROLE` no tiene `IF NOT EXISTS`, `load` pasa bytes UTF-8 a `psql` y el `TRUNCATE` bloquea brevemente la lectura de Grafana; a la 3.2: `CREATE OR REPLACE VIEW` no puede cambiar las columnas de una vista ya creada, y los paneles deben filtrar `run_at IS NOT NULL`.

### 3.2 Vistas `evaluation.config_changes` y `evaluation.comparable_runs`

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/evaluation_pg_helper.py` (ayudante reutilizable: PostgreSQL desechable con la imagen exacta de `docker-compose.yml`, nombre y contraseña aleatorios, puerto efímero en `127.0.0.1`, espera con tope de 90 s y limpieza con `atexit` y `tearDownModule`) y `scripts/tests/test_evaluation_views.py` (42 tests: 5 sin base y 37 con **PostgreSQL real**), commit `f462df80`. Los 42 fallan por `VIEWS_DDL` ausente o por «relation … does not exist». El tester comprobó con una referencia fuera del repositorio que los esperados son alcanzables y que sus 38 mutantes del SQL morían (dos de ellos hicieron añadir casos: una serie por fuente y el cambio de hora del 25-10-2026 en Europa/Madrid) |
| Green | `VIEWS_DDL` y `DDL_BLOCKS = (SCHEMA_DDL, VIEWS_DDL)`, commit `e1412ef0`; 1124/1124 (~35 s con el contenedor) |
| Mutación | La mutación automática no aplica a una constante SQL (cualquier cambio del literal rompe la sintaxis y «mata» por razones triviales). Se sustituye por 38 mutantes de SQL del tester y 35 del QA sobre `VIEWS_DDL`: 33 muertos y 2 equivalentes (`prompt` con solo una de las dos guardas `IS NOT NULL`: con un NULL, `<>` ya da NULL) |
| QA | `accept`, sin BLOCKING ni MEDIUM. Con PostgreSQL real: con los datos versionados las dos vistas salen vacías (cada clave tiene una sola ejecución con fecha; las dos de JUP-070 solo difieren en el proveedor de embeddings); datos sintéticos con cambio de modelo, de batería y corpus a la vez, prompt nulo→valor (sin anotación) y valor→valor distinto (con anotación), una ejecución sin fecha entre dos con fecha (no rompe la cadena), recarga repetida con `CREATE OR REPLACE VIEW`. No quedan contenedores ni volúmenes |
| DoD | Lint, type-check y secretos en verde. Regresión: 148 fallos del backend en la pasada del DoD, que coincidió con la mutación y los contenedores del QA en marcha; el backend ejecutado a solas da exactamente 145, todos de las cuatro suites de `RF-119-004` (`test_health_provider_*_jup047.py` y `test_system_health_jup047.py`). Los 3 de más eran pruebas sensibles al tiempo bajo carga |

Hallazgos LOW trasladados a la tarea 4.3 (ya anotados en `tasks.md`): `array_to_string(changes, ',')` para las etiquetas de las anotaciones, `noValue` en cada panel de evolución (el mensaje no sale de la vista), filtrar por `comparability_key` y `is_real`, y castear los `bigint` si un panel los mezcla con `value`.

### 3.3 Subcomando `load` y rol de solo lectura de Grafana

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_load.py` (173 tests, unos 28 s con PostgreSQL real), commit `56a27145`; 0 en verde (símbolos ausentes e «invalid choice: 'load'»). El tester comprobó con una referencia fuera del repositorio que los esperados son alcanzables y que sus 131 mutantes morían; los tests incluyen un `psql` falso que repite la sentencia con la contraseña, un timeout real y un ejecutable inexistente |
| Green | `READER_ROLE`, `PASSWORD_ENV`, `build_role_sql`, `load_command`, `run_load`, `LoadError`, redacción de la contraseña y el subcomando `load` (parser separado: `--output` solo en `rows` y `sql`, `--psql-command` solo en `load`), commit `db641a0e`; 1297/1297 |
| Mutación | La mutación automática de la sección es impracticable (cada pasada incluye el contenedor, ~47 s por mutante): se sustituye por los 131 mutantes del tester y los ~80 del QA (68 muertos; 12 supervivientes) |
| QA | `accept`, sin BLOCKING. Contraseñas con comillas, barras, `$$`, unicode, 200 caracteres y metacomandos de `psql` (`\!`) no aparecen en argumentos, entorno, stdout, stderr, trazas, `docker logs` ni `pg_stat_activity`; el rol no es superusuario ni puede leer `pg_authid`, otras bases o ficheros del servidor, ni escribir; la rotación conserva permisos y datos; un fallo a mitad de la parte de datos deja los datos y el rol anteriores intactos y no ejecuta el script del rol |
| Remediación | `test_evaluation_load_gaps.py` (18 tests, commit `222be1b2`): comando vacío o comillas sin cerrar (código 2), `load_command([])`, ejecutable con la contraseña en el nombre, escape de caracteres de control, `from None`, orden de la redacción (la forma con comillas dobladas antes que la simple), subclase hostil de `str`, límite exacto de 300 caracteres y orden de validación. Un test fijaba un defecto real: `main` validaba la contraseña **después** de leer los manifiestos; fix en commit «fix(JUP-121): load valida la contraseña antes…»; 1315/1315 |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend (`RF-119-004`), idénticos |

Decisiones y hallazgos diferidos:
- **No se implementa** (hallazgo del QA) que el detalle del error de `psql` sea la línea `ERROR:` en vez de la última línea (que con errores con posición es `^` y con `CONTEXT:` pierde el motivo): contradice tres tests ya commiteados de `test_evaluation_load.py` y el candado del harness impide editarlos; solo afecta a la legibilidad. Queda como hallazgo diferido para el backlog.
- **Limitación documentada** (hallazgo MEDIUM del QA): `ALTER ROLE … PASSWORD` lleva la contraseña en claro, así que quedaría en el registro del servidor si este registra sentencias (`log_statement` en `ddl` o `all`); con el `postgres` superusuario del Compose y la configuración por defecto no ocurre. Mejora posible: enviar el hash SCRAM-SHA-256 calculado en Python. Diferido al backlog (cambiaría tests que comparan el literal).
- A la tarea 3.4: `docker compose exec` necesita la pila levantada y el `.env` completo (Compose interpola todo `docker-compose.yml`); en CI o DockerServer se puede usar `--psql-command "docker exec -i <contenedor> psql …"`.

### 3.4 Scripts de `package.json`, paso de CI y doble guion de pnpm

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_scripts.py` (16 tests, commit `ae262f77`: valores exactos de los cuatro scripts, contigüidad, la línea de CI en su sitio y una sola vez, cobertura del patrón de descubrimiento y la guía) y `test_evaluation_scripts_args.py` (17 tests, commit `dd07da46`). El segundo nace de un hallazgo del tester: pnpm 9 reenvía el `--` literal al script, así que `evaluation-dashboard:load -- --manifest …` (la convención del repositorio, como `jup:check -- --change …`) fallaba con `argparse` |
| Green | Cuatro scripts (`evaluation-dashboard:rows`, `:sql`, `:load`, `:test`) entre `assistant-eval:test` y `synthetic-demo:test`, la línea `corepack pnpm evaluation-dashboard:test` en «Validate governance tooling» y `_drop_pnpm_double_dash` en `main` (ignora UN `--` suelto, salvo tras una opción con valor), commit `dde7480b`; `corepack pnpm evaluation-dashboard:test` da 1348/1348 en 67 s |
| Mutación | `_drop_pnpm_double_dash`: 15/16; el superviviente (`index > 0` → `index > 1`) es equivalente, porque con subcomando delante una opción con valor nunca está en el índice 0. El QA mató 13 de 13 mutantes manuales de la función y de `_VALUE_OPTIONS` |
| Python 3.12 | La CI usa 3.12 y el desarrollo local 3.13: la suite de evaluación completa (1315 tests) y el fichero del doble guion pasan con Python 3.12.13 |
| QA | `accept`, sin BLOCKING. Probó los cuatro scripts con `corepack pnpm`, que el patrón del script `:test` cubre los 27 ficheros `test_evaluation_*.py` y no el ayudante, y que el patrón con comillas dobles se comporta igual en `sh` y en `cmd`. Razonó que `ubuntu-latest` trae Docker (los tests con PostgreSQL real se saltan solos sin él), Node para JUP-068 y `docker-compose.yml` por el checkout |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend (`RF-119-004`), idénticos |

Decisión: el job «OpenSpec» tenía `timeout-minutes: 10` y el paso nuevo suma unos 70 s más la descarga de la imagen de PostgreSQL; se sube a 20 (el mismo que el job de pruebas de Python) para no arriesgar un fallo por tiempo. Queda por comprobar en la primera ejecución real de la CI cuánto tarda el paso. Los tests con PostgreSQL real se saltan sin avisar si el runner no tuviera Docker (hoy `ubuntu-latest` lo trae).

### 4.1 Datasource PostgreSQL de Grafana y variable de su contraseña

| Fase | Evidencia |
| --- | --- |
| Red | `scripts/tests/test_evaluation_grafana_datasource.py` (30 tests de solo lectura de ficheros, ejecutados también por `corepack pnpm evaluation-dashboard:test` y la CI), commit `864a1c31`: 20 en rojo; los 10 que pasan fijan lo que no debe cambiar (el datasource de Prometheus, el dashboard técnico por huella, el resto del servicio `grafana` y de `postgres-pgvector`, el resto de `.env.example`). El test congelado `tools/docker-topology.test.mjs` no hace falta tocarlo: solo fija ciertas variables y que `depends_on` sea únicamente `prometheus` |
| Green | `apps/monitoring/grafana/provisioning/datasources/evaluation-postgres.yml`, una línea en `docker-compose.yml` (`GRAFANA_EVALUATION_DB_PASSWORD: ${GRAFANA_EVALUATION_DB_PASSWORD:?required}`, sin `depends_on` ni puertos nuevos) y una en `.env.example`, commit `0aef3359`; `docker:validate` 36, `ci:check:test` 12 y `repository:governance:test` 13 en verde |
| Mutación | Configuración: no aplica un mutador de código. El tester mató 26 mutantes de configuración (contraseña en claro, `isDefault: true`, `:-` en lugar de `:?`, variable en otro servicio, `depends_on`, uid duplicado, tipo `postgres`, `sslmode`, tabuladores…) con copias de los ficheros |
| QA | `accept`, sin BLOCKING. **Runtime real** con una red desechable, PostgreSQL 17 y Grafana 11.3.0 con los montajes de solo lectura del compose: el datasource se provisiona aunque la base aún no tenga esquema ni rol; tras `load` el health devuelve «Database Connection OK», `SELECT count(*) FROM evaluation.results` por `/api/ds/query` devuelve 269 y la consulta de anotaciones funciona (vacía con los datos reales); `Prometheus` sigue siendo el predeterminado; el rol no puede crear tablas ni leer `pg_authid`; con una contraseña equivocada el health falla sin filtrar la contraseña en el mensaje, la API ni los logs. Compose se niega a arrancar, y nombra la variable, tanto si falta como si está vacía. Todo se limpió (contenedores, red y volúmenes iguales que al inicio) |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend (`RF-119-004`), idénticos |

**Para quien despliegue o pruebe en local:** el `.env` del repositorio no tiene `GRAFANA_EVALUATION_DB_PASSWORD`, así que `docker compose up` (y `docker compose config`) fallará con `required variable GRAFANA_EVALUATION_DB_PASSWORD is missing a value: required` hasta que se añada una línea `GRAFANA_EVALUATION_DB_PASSWORD=<valor>`. Debe ser el mismo valor con el que se ejecute `corepack pnpm evaluation-dashboard:load`. Lo mismo en el `.env` de DockerServer antes de desplegar.

Hallazgos para la tarea 4.3 (anotados en `tasks.md`): el tipo del datasource en los paneles, el `format` por tipo de panel, `$__timeFilter` y el rango del dashboard, y `run_at IS NOT NULL` en las series.

### 4.2 y 4.3 Dashboard `assistant-evaluation.json` (prueba estructural y dashboard)

Es el entregable principal del change. Un solo ciclo TDD con tres rondas de remediación tras el QA.

| Fase | Evidencia |
| --- | --- |
| Red (4.2) | `test_evaluation_dashboard_structure.py` (68 tests estáticos) y `test_evaluation_dashboard_queries.py` (23 tests que **ejecutan todas las consultas del dashboard contra PostgreSQL real** con el conjunto versionado y con uno sintético), commit `cb405378`: 99 fallos por «no existe el dashboard». El tester comprobó con un dashboard de referencia fuera del repositorio que los esperados son alcanzables y que 52 mutantes del JSON morían |
| Green (4.3) | `apps/monitoring/grafana/dashboards/assistant-evaluation.json` (21 paneles: A con introducción, ejecuciones, estados de los casos, calidad, latencia/formato/disponibilidad de la campaña, dos gráficas de evolución, calibración, benchmark y robustez; B con introducción y una tabla; C con introducción y cinco series de Prometheus), commit `8e5440f0`. El coder lo comprobó en un Grafana 11.3.0 real: provisiona sin errores, 10 consultas SQL y la anotación responden con los datos reales |
| QA (1.ª) | `changes-requested`. **BLOCKING B1**: con varias series intercaladas en el tiempo, las gráficas de evolución solo dibujaban la serie cuyas ejecuciones eran adyacentes; las demás quedaban como puntos sueltos (el formato `time_series` con `metric` se pivota a ancho y `spanNulls: false` deja un null en cada fila ajena): los tests solo validaban el SQL, no cómo Grafana dibuja los marcos. **M1**: seis tablas de resultados no traían fecha, versión, commit ni modelo; **M2**: una serie con un solo punto medido (o de hito) se dibujaba como punto suelto, contra «ni una línea ni un punto»; **M3/M4**: comportamientos visibles sin test (unidad `tasa`, `percentunit`, texto de tasas, filtro de la anotación, `timeFrom` de C, sin `$__timeFilter`). Reprodujo además la sección C con un exportador de métricas simulado: las proporciones coinciden con el cálculo a mano y, sin tráfico, no devuelven resultado (la misma expresión sin la guarda `> 0` da NaN) |
| Red (remediación) | `test_evaluation_dashboard_visible.py` (31 tests, 12 en rojo; commit `b01add54`): metadatos en a3, a4, a7, a8, a9 y B, series con al menos dos puntos medidos (con series intercaladas, no medidas en medio, hitos y no hitos, no reales), unidad, texto de tasas, anotación, `timeFrom`, altura de la tabla de B |
| Green (remediación) | Commit `5d32a805`. **B1**: cadena de transformaciones de panel en las dos gráficas de evolución (`prepareTimeSeries` multi → `seriesToRows` → `filterByValue` → `partitionByValues` por Metric), elegida empíricamente en un Grafana real con capturas antes/después (la transformación sola, `prepareTimeSeries`, conservaba los nulos; `spanNulls: true` contradecía la decisión D6 y los tests). **M2**: `count(*) OVER (PARTITION BY comparability_key, metric_id, behavior) >= 2` sobre las filas medidas. **M1**: `run_at`, `suite_version`, `commit_sha`, `generation_model` en todas las tablas |
| Tests de B1 | `test_evaluation_dashboard_transformations.py` (18 tests, commit `338c5939`; 35 de 35 mutantes mueren): fija la cadena exacta, sus opciones, que las dos gráficas son iguales y que ninguna otra parte del dashboard lleva transformaciones de partición. También `test_evaluation_dashboard_labels.py` (8 tests; 12 de 12 mutantes): las etiquetas de las series «no real» llevan sus motivos en las dos gráficas |
| QA (2.ª) | `accept`. En un Grafana real: con series intercaladas se dibujan las líneas de **todas** las series; una serie con un punto medido y otro `not_measured`, o con una sola ejecución de hito, no aparece; con los datos versionados las dos gráficas dicen «Sin datos: no hay con qué comparar»; la serie «no real» sale discontinua y con el motivo en el nombre (la transformación no altera la leyenda ni los overrides); a 1600 px ninguna columna final queda cortada y la fila «Ahorro realizado: No medido» es visible sin desplazar |
| Retoque | L-1 (la línea une los puntos medidos y una ejecución sin medida no genera punto), L-3 (columnas de robustez legibles), L-4 (la tabla de calidad muestra sus 32 filas), commit «fix(JUP-121): línea que une puntos medidos…» |
| Decisión de proceso | Dos tests congelados contradecían los cambios exigidos por el QA y el candado del harness impide editarlos: lo cambió el usuario a mano (commit `5c0be70f`: una línea de `test_a5_evolucion_automatica_solo_de_ejecuciones_comparables_y_medidas`, que ya no espera el punto suelto de REL-1 de SC-A-2). Antes se había hecho lo mismo con dos líneas de `test_evaluation_rows_contract.py` (2.6) |
| DoD | Lint, type-check y secretos en verde. Regresión: 145 fallos del backend (`RF-119-004`), idénticos. Suite `test_evaluation_*.py`: 1526 OK |

Hallazgos LOW diferidos: con cientos de ejecuciones la evolución devuelve muchas series (un panel de 500 ejecuciones y 30 000 filas da 1808 series en 0,67 s: rinde, pero se vuelve ilegible; haría falta un selector de fuente o de ejecución); la tabla de robustez tiene `h = 5` y habrá que subirla cuando exista el informe de JUP-071; los textos de «Unidad original» se ocultaron en lugar de traducirse. El rango por defecto del dashboard es el último año: las ejecuciones más antiguas desaparecen de la evolución hasta ampliar el rango (documentado en el panel de introducción de A).

### 5.1, 5.2 y 5.3 Pruebas de integración con PostgreSQL real

La funcionalidad ya existía (grupos 2 a 4), así que estas pruebas no tienen Red previo: su valor es detectar regresiones y su eficacia se demostró con mutantes del producto y del dashboard.

| Tarea | Módulo | Tests | Qué fija | Mutantes |
| --- | --- | --- | --- | --- |
| 5.1 | `test_evaluation_reconciliation.py` | 22 (~9 s) | Concilia las **mismas consultas del dashboard**, ejecutadas con el rol de solo lectura sobre el conjunto versionado, con los **informes originales**, calculados sin los adaptadores: JUP-070 (`counts`, y `k`, `n` y `rate` de cada métrica, LAT, REL-4, GRD-2, STR-2), JUP-078 por modelo, JUP-022 (28 puntos × 5 tasas y 20 `selected`), JUP-068 con Node (tiempo, asignación, ahorro y `realized_savings` nulo), 269 filas en total, ninguna `measured` sin valor ni `not_measured` con valor | 32, 27 muertos; los 5 equivalentes con los datos versionados (ningún modelo sin llamadas correctas, ningún `available: false`, 269 filas por debajo del bloque de 500) los matan las pruebas de los adaptadores y de SQL |
| 5.2 | `test_evaluation_permissions.py` y `test_evaluation_permissions_grant_options.py` | 37 + 11 (~24 s y ~8 s) | Por introspección del catálogo (frente a un rol de control sin concesiones) y por conexión real como el rol: `SELECT` de las dos tablas y las dos vistas y nada más; 46 operaciones denegadas (escritura, DDL, `pg_authid`, `pg_read_file`, `COPY … PROGRAM`, `SET ROLE postgres`, `ALTER SYSTEM`, tablas de embeddings y de `public`); sin atributos de poder; privilegios por defecto solo en `evaluation`; no se acumulan con otra carga y sobreviven al `TRUNCATE`; **ningún privilegio es reconcedible** en ninguno de los 13 catálogos con ACL | 24 + 17, todos muertos (el QA encontró que `USAGE … WITH GRANT OPTION` y `CONNECT … WITH GRANT OPTION` sobrevivían: el segundo módulo los cierra) |
| 5.3 | `test_evaluation_atomicity.py` | 26 (~31 s) | Idempotencia (huella md5 de todo el contenido tras 2 y 3 cargas), reemplazo completo, atomicidad ante fallo a mitad (contenido, identidad y ACL intactos, script del rol no ejecutado y contraseña anterior vigente, también con un `psql` que corta la conexión), nada fuera de `evaluation`, conjunto vacío, manifiesto local que suma y se quita, y la concurrencia | 17 + `FIX-advisory-lock`, todos muertos |

QA: `accept`, sin BLOCKING. Ejecutó cada módulo 3 veces (deterministas) y los tres juntos (85 tests, 63 s, no se pisan), sin Docker los tests se saltan con el motivo y no fallan, la suite de evaluación completa da 1611 OK en 177 s, comprobó a mano tres valores contra los informes originales (REL-2 de la ejecución 2 = 16/20, LAT-2 total = 4561,659 ms, `time_saved_percent` = 40) y 39 mutantes propios más (27 muertos; los 12 supervivientes no son visibles con los datos versionados).

**Hallazgo real de producto (diferido): cargas simultáneas.** Dos `load` a la vez hacen que una falle en 28 de 30 rondas con `tuple concurrently updated` o `deadlock detected` (nunca las dos, y sin dejar datos a medias): el script del rol y el de las vistas, que son transacciones de catálogo, actualizan las mismas tuplas. El arreglo validado en una copia es anteponer `SELECT pg_advisory_lock(<clave>);` a la entrada de `psql`, pero cambiaría la entrada exacta que fijan tests ya commiteados y congelados; queda como limitación documentada y el test fija el comportamiento real y seguro (al menos una carga termina bien, la otra bien o con un error limpio de motivo conocido, contenido de una sola carga y rol intacto).

Riesgos para la CI (QA): primera descarga de la imagen de PostgreSQL por digest (~630 MB, 30 a 90 s) compartida por los 9 módulos con contenedor, y arranque de cada contenedor con tope de 90 s; se estima 3 a 5 minutos para `evaluation-dashboard:test` en un runner de GitHub (`timeout-minutes: 20`). Falta confirmarlo en la primera ejecución real de la CI.
