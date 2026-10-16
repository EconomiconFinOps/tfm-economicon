# Revisión de jup-121-lectura-dashboard

JUP: JUP-121 · [Trello](https://trello.com/c/aIdxwsXR) · ADR: [ADR-0022](../../../docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md) · PR [#132](https://github.com/EconomiconFinOps/tfm-economicon/pull/132)

## Resumen

Atiende la validación de Paris (`Validacion JUP-121`, cambios solicitados sobre `e4b403d4`) y el comentario de pairing de Lucia en la PR #132, en la misma rama y con la misma tarjeta. El cambio de Paris es de pruebas (`local:doctor`); el de Lucia afecta al dashboard: dos fallos de la sección C y siete mejoras de lectura, más la latencia de la campaña en la evolución, el intervalo de confianza visible y la documentación de lo calculado y no mostrado. Al validar con Grafana real aparecieron ajustes visuales (D10) que también se hicieron.

Sin cambios en `tools/evaluation-dashboard.py`, el esquema `evaluation`, el rol de Grafana ni el backend. Las pruebas congeladas que fijan lo que cambia se actualizaron con parches que aplicó el usuario (el hook de congelación impide que lo haga el asistente).

## Qué pidió cada revisión y dónde se resuelve

| Petición | Resolución | Tarea |
| --- | --- | --- |
| Paris [P2]: `tools/local-doctor.test.mjs` sin la variable `GRAFANA_EVALUATION_DB_PASSWORD` (11 fallos de CI) | Fixture, lista esperada del contrato y casos de ausencia y vacío; `node --test tools/local-doctor.test.mjs`: 57 pruebas OK. Commit `07f56a3c` | 1.1 |
| Lucia 1: «Tasa de error» dice «Sin datos» con tráfico sin 5xx | Numerador con `or vector(0)`; con tráfico y sin 5xx vale 0 %, sin tráfico sigue «Sin datos: no hubo peticiones». Comprobado con `promtool test rules` y en Grafana real | 2.1 |
| Lucia 2: la latencia p95 mezcla todas las rutas | Título «Latencia p95 del backend (todas las rutas, tráfico real)» y descripción que dice que no es la del asistente | 2.1 |
| Lucia 3: la tabla de calidad no se entiende | Panel «Resultados por métrica y ejecución»: una fila por métrica y variante con su nombre del catálogo, una columna por ejecución, sin metadatos repetidos, con IC95. Las tablas por fila quedan como «(detalle)» | 3.1 |
| Lucia 4: falta un resumen arriba | Panel «Resumen de la última campaña» | 3.2 |
| Lucia 5: etiquetas con dos sentidos | «Tipo de ejecución», sin columna «Resultado» en los detalles de medidas y variantes en español | 3.3 |
| Lucia 6: numeradores en bruto en la sección B | Numerador y denominador en minutos y euros | 4.1 |
| Lucia 7: «Cómo leer la sección A» se corta; «No demuestra» solo con el ratón | Tres viñetas y el resto en la guía; cada sección conserva a la vista su tabla «Qué no demuestra». El detalle por panel sigue en ⓘ (Grafana no puede mostrarlo en línea) | 4.2 |
| Lucia: IC95 y latencia en la evolución | IC95 en la matriz; panel «Evolución de la latencia de la campaña» | 3.1, 3.4 |
| Lucia: dejar escrito lo calculado y no mostrado | Apartado «Calculado y no mostrado» de la guía | 5.1 |
| Hallazgos visuales con Grafana real | Alturas, zona horaria UTC, cabecera y variantes de la sección B | 3.5 |

## Evidencia TDD

| Grupo | Red | Green | Mutación |
| --- | --- | --- | --- |
| Sección C, matriz, resumen, etiquetas, sección B, textos, latencia y guía | `6c139c9a`, 110 pruebas nuevas (70 fallos y 6 errores antes), 9 mutantes del tester sobre una referencia | `ba94c875` (dashboard y guía) con el parche de 2 pruebas congeladas (clasificador, sección C, alcance de las transformaciones) que aplicó el usuario | 345 mutantes sobre el JSON real y la guía: 69,3 % muertos con las pruebas anteriores, 98,0 % tras 53 pruebas nuevas (`4256c584`); los 7 supervivientes son equivalentes (orden de ramas con `run_id` nulo, JOIN redundante, `emptyValue` inalcanzable por el cruce completo, `NULLS FIRST` tras `IS NOT NULL`, `min` frente a `max` con una sola fila, nivel de encabezado de la última sección) |
| Ajustes visuales (3.5) | `b0bff579`, 14 pruebas (11 en rojo antes); 14 mutantes sobre una referencia, todos muertos | Alturas, `timezone` UTC, ancho de «Tipo de ejecución» y `variante` en la sección B, con el parche de 2 líneas de pruebas congeladas que aplicó el usuario | Cubierta por la mutación anterior y por los 14 mutantes de la referencia |

## Validación con Grafana 11.3.0 real

Dos pasadas con Edge headless a 1440 y 1600 px sobre PostgreSQL 17, Prometheus 2.55.1 con un exporter sintético y el provisioning del repo: los 24 paneles responden sin error. La primera encontró los ajustes de D10; la segunda, hecha tras corregirlos, está en `docs/evidence/JUP-121/`. `groupingToMatrix` con celdas de texto funciona en 11.3.0 y no hay un orden de filas garantizado por la transformación, por eso la consulta cruza ejecuciones con el catálogo de métricas y ordena en SQL.

## QA independiente

Veredicto `accept`, sin hallazgos BLOCKING. Ejecutó por su cuenta la suite completa (1801 OK), la conciliación (22), las pruebas de lectura (177) y `local-doctor` (57); reconstruyó 11 celdas de la matriz y el resumen contra `JUP-070-run-2-report.json`, y la sección B con 0 diferencias; probó con `promtool` que la tasa de error da 0 con tráfico sin 5xx y vector vacío sin ninguna petición; y mató 12 mutantes manuales sobre el JSON real. Hallazgos medios, ya corregidos: la guía decía que LAT-4 quedaba fuera de la evolución (sí se dibuja en la gráfica de proporciones); continuidad y backlog estaban desactualizados; la tarea 5.2 sin marcar. Bajos, ya diferidos: la prueba versionada de `promtool` solo cubre las proporciones (la tasa de error se prueba en `test_evaluation_readability_section_c.py`, que se salta sin Docker), y la tasa de error da NaN —que Grafana no dibuja— si el contador existe con tasa 0 en toda la ventana.

## Verificación final

`corepack pnpm evaluation-dashboard:test`: 1801 OK en 266 s. `openspec:validate` 75/75, `jup:check` y `jup:cleanup:check` en verde, `node --test tools/local-doctor.test.mjs` 57/57, `lint`, `type-check` y escaneo de secretos del DoD en verde. La regresión completa del DoD sigue en rojo por las pruebas del processor de JUP-035 sin el `tokenizer.json` generado (ajeno; `git diff origin/develop -- apps/processor` vacío).

## Hallazgos diferidos (severidad baja)

- «Ejecuciones cargadas» pierde la columna «Hito» y recorta el commit a 1440 px.
- «Consultas al asistente por minuto» no suma por instancia (`sum()`): con réplicas dibujaría una línea por instancia. Es la expresión idéntica a la del dashboard técnico de JUP-043.
- La leyenda de las evoluciones muestra identificadores crudos (`ACC-2 · judged`).
- La calibración muestra «50.0%» sin espacio, a diferencia del resto.
- Dos ejecuciones del mismo minuto y tipo darían la misma cabecera de columna en la matriz.
- El título «Latencia p95 del backend (todas las rutas, tráfico real)» se trunca en un panel de un tercio de ancho (el texto completo está en la descripción).
- La expresión de la tasa de error ya no es idéntica a la del dashboard técnico (JUP-043), que no se toca.
