# JUP-121 — Dashboard de Grafana con los resultados de evaluación del asistente

Trello: https://trello.com/c/aIdxwsXR
Fecha: 2026-10-15. Rama: `feat/JUP-121-assistant-evaluation-dashboard`. Change de OpenSpec:
`openspec/changes/archive/2026-10-15-jup-121-assistant-evaluation-dashboard/` (evidencia por tarea en su `review.md`).
Decisión: [ADR-0022](../adr/ADR-0022-assistant-evaluation-results-in-grafana.md). Guía:
[evaluation-dashboard.md](../validation/evaluation-dashboard.md).

Evidencia técnica de implementación; no sustituye a las reviews humanas `Revision JUP-121` y
`Validacion JUP-121`, que están pendientes. PR: pendiente de abrir contra `develop`
(enlace: _por rellenar_). CI de GitHub: _por rellenar_; la CI no se ha ejecutado todavía con
este change.

Entorno: Windows 11, Docker con proyecto Compose aislado (`jup121e2e`, volúmenes y puertos
propios, `.env` sintético; no se tocó el `.env` real ni los contenedores de otras tareas),
Python 3.13 local (la CI usa 3.12; la suite también se ejecutó con 3.12.13), PostgreSQL 17 con
pgvector, Grafana 11.3.0 y Prometheus 2.55.1 con las imágenes ya presentes.

## Resultado por criterio de aceptación de la tarjeta

| Criterio | Evidencia |
| --- | --- |
| Dashboard provisionado con `docker compose up` con los datos de JUP-070 (ejecuciones 1 y 2), JUP-078, JUP-022 y JUP-068 | La pila real arranca con el dashboard `economicon-assistant-evaluation` (21 paneles) junto al técnico y el datasource `Evaluacion`. `corepack pnpm evaluation-dashboard:load` carga 5 ejecuciones y 269 resultados; dos cargas seguidas dejan la misma huella de contenido. Cada panel responde HTTP 200 por la API de Grafana con el rol de lectura. Capturas en [`JUP-121/`](JUP-121/) (02, 03, 04, 06 y 07) |
| Cada panel indica su tipo (A/B/C), qué mide y qué no demuestra | Prueba estructural `test_evaluation_dashboard_structure.py`: cada panel lleva `Tipo: A`, `B` o `C`, `Mide:` y `No demuestra:`, ninguno mezcla `prometheus` con `evaluation-postgres`, y existen las secciones A, B, C y la de robustez |
| Una serie con una sola ejecución muestra «Sin datos» y no una línea ni un 0 % | Con el conjunto versionado, los dos paneles de evolución devuelven 0 filas y muestran «Sin datos: no hay con qué comparar» (captura 06). La vista `comparable_runs` exige al menos dos puntos medidos; con un manifiesto local de prueba de dos ejecuciones comparables sí se dibuja la línea, discontinua si no es real y con la anotación del cambio de modelo (captura 07) |
| Pruebas añadidas y en verde: adaptadores, conciliación de recuentos, no medidos ≠ 0 %, ausencia de texto de preguntas y respuestas, descripción A/B/C | `corepack pnpm evaluation-dashboard:test`: **1623 pruebas OK en 257 s** (2026-10-15, sobre el árbol integrado con `develop`). Adaptadores (`test_evaluation_adapter_*`), conciliación de las mismas consultas del dashboard con los informes originales calculados sin los adaptadores (`test_evaluation_reconciliation.py`, 22), permisos del rol (`test_evaluation_permissions*.py`), idempotencia y atomicidad (`test_evaluation_atomicity.py`), y reglas de no medido y de alfabeto cerrado (sin texto libre) en `test_evaluation_rows_contract.py`. Además 29 pruebas de backend (`test_retrieval_failure_series.py`) |
| Documentación y ADR actualizados | ADR-0022 y su fila en `docs/adr/README.md`; guía de uso, regeneración y puesta en marcha; nota de despliegue de la variable nueva; tema en `docs/continuidad/`; enlace desde `docs/architecture.md` y `docs/validation/README.md` |
| PR revisado y validación con evidencia | Pendiente: la PR aún no existe; este fichero es la evidencia técnica previa |

## Qué se comprobó con la pila real

- **Sección A:** la ejecución 2 de JUP-070 (plantilla) muestra sus 28 casos por estado y va rotulada «no real» con su motivo; las métricas no medidas salen como «No medido», nunca como 0 %; calibración (140 filas) y benchmark cargados; robustez con «Sin datos: todavía no hay informe de robustez de JUP-071».
- **Sección B:** 23 filas de JUP-068, rotuladas como sintéticas.
- **Sección C:** sin tráfico, consultas por minuto en 0 (cero medido) y el resto sin datos; con 59 mensajes al asistente (201) las cinco gráficas tienen valor; con PostgreSQL parado (503) aparecen los fallos de recuperación y vuelven a bajar al recuperarse.
- **Permisos:** el rol `grafana_evaluation_reader` solo lee `evaluation` y no puede escribir, ni leer las tablas de embeddings, ni reconceder privilegios (pruebas con PostgreSQL real).
- **Variable obligatoria:** sin `GRAFANA_EVALUATION_DB_PASSWORD` (ausente o vacía) `docker compose config` y `up` fallan con el mensaje de la variable. Antes de la primera carga, las secciones A y B muestran `password authentication failed` porque el rol aún no existe.
- **Defecto hallado y corregido durante la validación:** las proporciones de la sección C (paneles 20 y 21) quedaban en «Sin datos» con consultas y sin fallos porque el contador con etiqueta no tenía series. Corregido en `apps/backend/app/api/routes/assistant.py` (Red `d804ebdb`, Green `18c3b902`) y comprobado con `promtool test rules` ([prueba](JUP-121/section-c-promql-test.yml), SUCCESS). Detalle en `review.md`, tarea 6.1.

## Verificaciones finales (2026-10-15)

| Comando | Resultado |
| --- | --- |
| `corepack pnpm evaluation-dashboard:test` | 1623 OK, 257 s |
| `corepack pnpm openspec:validate` | 74 pasan, 0 fallan |
| `corepack pnpm jup:check -- --change jup-121-assistant-evaluation-dashboard` | `[OK]` |
| `corepack pnpm jup:cleanup:check` | `[OK]` 1640 archivos |
| `corepack pnpm jup:check:test` | sin fallos |
| `node .claude/harness/check-dod.mjs` | `lint`, `type-check` y escaneo de secretos pasan; la regresión sigue en rojo por causas ajenas (ver abajo) |

**Excepción de entorno de la regresión completa.** (1) 11 pruebas del processor de JUP-035 fallan en esta máquina por `FileNotFoundError` de `apps/processor/app/agents/prompt_resources/jup035/chat/v2/tokenizer.json`, un fichero generado (`build_tokenizer.py`, ignorado por Git) que no se ha generado aquí; `git diff origin/develop -- apps/processor` está vacío. (2) En el backend fallan las suites de salud de JUP-047 (unas 145 pruebas; en esta máquina por el bucle de eventos de Windows, `RF-119-004`) y, con `tokenizers` ya instalado, no dependen de este change: son las mismas con y sin él. (3) La inestabilidad del frontend por carga de CPU ya registrada en JUP-119. El único cambio de producto de este change en `apps/backend` son 8 líneas de `assistant.py`; las pruebas relacionadas (203 en nueve ficheros) pasan.

## Mutación

Mutador de AST propio (`mutmut` no maneja un módulo con guion en el nombre), con baseline en verde obligatorio y copias de cada superviviente revisadas una a una. Resultados por tarea en `review.md`: entre el 88 % y el 95 % por sección sobre `tools/evaluation-dashboard.py`; los supervivientes son prosa de mensajes o equivalentes documentados. El arreglo del backend: 9 de 9 mutantes muertos.

## Lo que NO se ha validado

- **Robustez (JUP-071):** no existe informe; la sección muestra «Sin datos». Solo se ha probado el contrato `rows-v1` con datos sintéticos.
- **Despliegue en DockerServer:** sin acceso desde esta máquina; la variable `GRAFANA_EVALUATION_DB_PASSWORD` hay que añadirla allí antes de actualizar la pila.
- **CI de GitHub:** no se ha ejecutado con este change. Riesgo estimado por el QA: la suite tarda varios minutos y descarga por primera vez la imagen de PostgreSQL por digest (~630 MB); el job de OpenSpec tiene `timeout-minutes: 20`.
- **Tráfico del asistente con un gateway real:** el tráfico de la sección C se generó contra el entorno de pruebas (proveedor simulado); no hay una medición con modelo real.
- **Captura en navegador de la sección C tras el arreglo de las series:** la pila ya estaba desmontada; se comprobó con `promtool` sobre la misma expresión.
- **Calidad real del asistente:** las ejecuciones cargadas de JUP-070 son de plantilla y los datos de JUP-068 son sintéticos; el dashboard no demuestra calidad ni beneficio real.
- **Hallazgos diferidos** (sin corregir por decisión): cargas simultáneas de `load` pueden hacer fallar una de las dos; la contraseña va en claro en el `ALTER ROLE` si el servidor registra sentencias; el mensaje de error de `psql` usa la última línea y no la que empieza por `ERROR:`; panel 19 heredado de JUP-043; Grafana sin `healthcheck`. Registrados en `openspec/findings/backlog.md`.

## Ajustes tras la PR #132 (change `jup-121-lectura-dashboard`)

La validación de Paris y el comentario de pairing de Lucia pidieron cambios que se resolvieron en un change propio ([`jup-121-lectura-dashboard`](../../openspec/changes/jup-121-lectura-dashboard/), con su `review.md`): `local:doctor` con la variable obligatoria, dos correcciones de la sección C, la matriz «Resultados por métrica y ejecución» con nombres del catálogo e IC95, el resumen de la última campaña, etiquetas, unidades de la sección B, la evolución de la latencia de la campaña, la guía («Calculado y no mostrado») y los ajustes visuales encontrados al validar.

- **Pruebas nuevas:** 177 (`test_evaluation_readability_*.py`), 163 + 14 de la tarea de ajustes; mutación sobre el JSON real y la guía: 345 mutantes, 98,0 % muertos y 7 supervivientes equivalentes.
- **Grafana 11.3.0 real, 1440 y 1600 px:** los 24 paneles responden sin error; la matriz muestra sus 44 métricas sin scroll interno, con 2 y con 3 ejecuciones; las horas de las tablas y de la cabecera de la matriz coinciden en UTC; «Tipo de ejecución» sale completo; la sección B está en minutos, euros y variantes en español; la tasa de error vale 0 % con tráfico y sin 5xx. Capturas en [`JUP-121/lectura/`](JUP-121/lectura/).
- **No validado:** la segunda pasada usa un exporter de métricas sintético, no el backend real; con tres ejecuciones la tercera es sintética (copia modificada de la ejecución 2 de JUP-070), solo para ver cómo crece la matriz. Los detalles por fila («Exactitud…» y «Latencia, formato y disponibilidad…») siguen mostrando parte de sus filas con scroll interno: son el detalle de auditoría.
- **Diferido (baja):** columna «Hito» y «Commit» de «Ejecuciones cargadas» a 1440 px, «Denominador» recortado en el detalle de exactitud a 1440 px, suma por instancia en las consultas por minuto, identificadores crudos en la leyenda de las evoluciones, «50.0%» en la calibración y cabecera idéntica para dos ejecuciones del mismo minuto y tipo.
