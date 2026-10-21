# JUP-130 — Indicadores medibles para la memoria: anomalías, coste de IA y datos, visibles en Grafana

Trello: https://trello.com/c/mkwnaPz2
Fecha: 2026-10-21. Rama: `feat/JUP-130-indicadores-memoria`. Change de OpenSpec: `openspec/changes/jup-130-indicadores-memoria/` (propuesta, diseño, cuatro specs, tareas y `review.md` con la revisión adversarial). Nota de continuidad: [indicadores-memoria.md](../continuidad/indicadores-memoria.md). Guía: [evaluation-dashboard.md](../validation/evaluation-dashboard.md).

Evidencia técnica de implementación; no sustituye a las reviews humanas `Revision JUP-130` y `Validacion JUP-130`, que están pendientes. PR: pendiente de abrir contra `develop`. CI de GitHub: no ejecutada todavía con este change.

Entorno: Windows 10, Docker Desktop. Pila mock en un proyecto Compose aislado (`tfm-economicon-jup130`, volúmenes y puertos propios; subred del chat distinta para no chocar con `economicon-ai`) y el gateway aislado de `economicon-ai` con su volumen de pruebas anteriores. Python 3.14 local para las pruebas de la herramienta y de los scripts; Python 3.12 de los entornos del repositorio para el API de costes. Grafana 11.3.0, PostgreSQL 17 con pgvector, Chromium 153 de Playwright para las capturas.

## Resultado por criterio de aceptación de la tarjeta

| Criterio | Evidencia |
| --- | --- |
| Precisión, recall y retraso de anomalías, con eventos escritos a partir del generador y no de la salida del detector | `docs/validation/JUP-130-injected-events.json` (siete eventos) y `scripts/tests/test_memory_indicators_events.py` (12 pruebas): cada evento es un salto real de `anomaly_levels()`, todo salto del generador tiene su evento y cinco variantes que rompen la lista hacen fallar la prueba. Medición: `docs/evidence/JUP-130/JUP-130-anomalies.md`; con la referencia 2026-10-30, 5 episodios de 7 eventos (precisión 5/5, recall 5/7, y 5/5 sobre los detectables por diseño). Los dos que faltan, un pico desde cero y la aparición de un servicio, no se detectan por diseño. El retraso vale 0 por construcción (límite declarado, RF-130-002) |
| Coste de IA facturado por consulta y tasa de 429: el gateway aporta las consultas y OpenRouter lo facturado, con la diferencia y la cobertura | `docs/evidence/JUP-130/JUP-130-ai-cost.md`: ventana 2026-10-09 a 2026-10-21, 100 consultas de chat, 100 de 100 confirmadas por OpenRouter, 0,002601 USD por consulta; estimado 0,250394 USD, facturado 0,260096 USD, diferencia −0,009702 USD. Una consulta a OpenRouter con `total_cost` idéntico al gasto del gateway dio la primera comprobación; la medición completa las leyó todas. La diferencia la explican cuatro consultas del 2026-10-20 con gasto 0 en el gateway (facturadas entre 0,0018 y 0,0029 USD); las otras 96 coinciden hasta el noveno decimal. Los 429 (3 de 924) son del límite por clave del gateway y los errores del proveedor (6 de 924) son 5xx: se informan por separado |
| Frescura y reconciliación de los datos de coste | `docs/evidence/JUP-130/JUP-130-data.md`, medido contra el API real de la pila con los datos de la demo cargados: reconcilian a cero los tres pares inquilino-divisa (incluido el USD de `tenant-growth`, 9007199254741838,37, sin perder un céntimo), frescura de 0 días y 0 días sin registro. Pruebas con un API simulado: diferencia de un céntimo, dos divisas sin compensación, API caída, inquilino sin datos, datos atrasados y redondeo único |
| Un panel de Grafana por indicador, con «Mide:» y «No demuestra:», que pasa las pruebas estructurales | Tres paneles nuevos en `assistant-evaluation.json` (anomalías en la sección A; coste de IA y datos en la B). `corepack pnpm evaluation-dashboard:test`: 1846 pruebas, OK, tras extender los clasificadores y los recuentos (ocho ejecuciones y 308 filas). La prueba de conciliación comprueba que los paneles muestran cada una de las 308 filas de la base |
| Con el stack levantado y el comando de carga existente, sin pasos manuales nuevos, los paneles muestran datos; comprobado en el navegador | Pila levantada con `docker compose up` desde un proyecto nuevo, datos de la demo cargados con la skill del stack y `corepack pnpm evaluation-dashboard:load` (8 ejecuciones y 308 resultados). Después se reinició Grafana, como indica la guía para la primera carga, y se abrió cada panel en Chromium: capturas en `docs/evidence/JUP-130/grafana-*-claro.png` y `-oscuro.png`. El panel «Tiempo, asignación y ahorro» no muestra filas de JUP-130 y la evolución automática sigue en «Sin datos: no hay con qué comparar» |
| Una tabla por indicador lista para la memoria, con el comando, la versión de código y la fecha | `docs/evidence/JUP-130/JUP-130-{anomalies,data,ai-cost}.md` y sus informes `.rows.json` con `commit` y `run_at`. Con los mismos argumentos el informe y la tabla salen idénticos byte a byte (comprobado en las pruebas y repitiendo la medición) |
| Lo no medido aparece como «no medido» o «Sin datos», nunca como 0 | Pruebas por indicador (gateway caído, clave ausente, sin consultas, sin API, sin inquilino). La revisión adversarial halló un caso en el que la cobertura salía como un 0,0 % medido sin haber consultado a OpenRouter; corregido con prueba de regresión (ADV-1) |
| Cada cifra declara sus límites | Cada tabla lleva «Qué no demuestra» (datos sintéticos, pocos eventos, etiquetas escritas por quien diseñó los datos, gasto local a la máquina, reconciliación contra el propio generador) y cada panel, su línea «No demuestra:» con la limitación de su sección |
| Script, evidencia y nota de continuidad actualizados | `tools/memory-indicators.py` con 149 pruebas, evidencia en `docs/evidence/JUP-130/`, guía del dashboard, `docs/continuidad/indicadores-memoria.md` y su fila en el índice |

## Qué se comprobó

- `python -m unittest discover -s scripts/tests -p "test_memory_indicators_*.py"`: 149 pruebas, OK. Se aplicaron mutantes deliberados a la herramienta y cada uno hizo fallar alguna prueba; los que sobrevivieron al principio llevaron a añadir pruebas.
- `corepack pnpm evaluation-dashboard:test`: 1846 pruebas, OK (PostgreSQL desechable en Docker).
- `corepack pnpm lint` y `corepack pnpm build`: OK (4 de 4 tareas cada uno).
- API de costes (pytest, Python 3.12): 81 pruebas, OK. Frontend (vitest): 1380 pruebas en 92 ficheros, OK.
- `corepack pnpm openspec:validate` (83 de 83), `jup:check -- --change jup-130-indicadores-memoria`, `jup:check:test`, `jup:cleanup:check` y `jup:cleanup:test`: OK.
- Dos vueltas de revisión adversarial independiente (`review.md`): ambas accept-with-findings, sin BLOCKING; los dos HIGH de la primera se corrigieron.

## Qué no se validó

- **Backend y procesador (pytest):** no se pudieron ejecutar en esta máquina porque falta el paquete `tokenizers` incluso en los entornos del repositorio principal. No se ha cambiado ningún fichero de `apps/backend` ni de `apps/processor` respecto a develop; los ejecuta la CI.
- **La pila de la medición usó la imagen de backend ya construida de `economicon-ai` (de hace unas 40 horas)**, no una construida desde esta rama: la construcción falló al descargar el tokenizer («download limit exceeded»). Contiene `/billing/summary` y `/billing/reference-date`, pero no es el backend de esta rama.
- **El renderizado de la fila `measurement_cause` en el panel de coste de IA** no se ha visto en Grafana: ningún informe versionado trae causas (todas las cifras están medidas), así que solo está comprobado por las pruebas del informe y por la lectura del SQL (ADV-R2-3).
- **La CI de GitHub** no se ha ejecutado, y las reviews humanas (`Revision JUP-130`, `Validacion JUP-130`) están pendientes.
- **Hallazgos aceptados sin corregir:** RF-130-001 (robustez de la herramienta ante entradas atípicas) y RF-130-002 (el retraso vale 0 por construcción), en `openspec/findings/backlog.md`.
- **El gasto es local a la máquina que ejecutó las consultas** (el gateway aislado de esta máquina, del 9 al 20 de octubre); no es el coste de un uso real ni de otros equipos.
- Lo medido es una vez y sobre datos sintéticos y pocos eventos: ilustrativo, no estadístico.
