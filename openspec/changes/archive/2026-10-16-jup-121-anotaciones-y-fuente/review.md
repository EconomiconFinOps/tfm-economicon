# Revisión de jup-121-anotaciones-y-fuente

JUP: JUP-121 · [Trello](https://trello.com/c/aIdxwsXR) · ADR: [ADR-0022](../../../../docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md) · PR [#132](https://github.com/EconomiconFinOps/tfm-economicon/pull/132)

## Resumen

Atiende la segunda validación de Paris (cambios solicitados sobre `640686e0`: las anotaciones de cambio de configuración no aparecían en la evolución de la latencia) y las dos observaciones de Lucia sobre el encaje de JUP-071 (el panel de estado de los casos no filtraba por fuente y faltaba dejar escrito qué filas son `human` y cuáles `automatic`). Sin cambios en `tools/`, el esquema, los adaptadores, el backend ni el panel de robustez, cuya lectura se hará en la rama de JUP-071 con el informe real.

| Petición | Resolución | Tarea |
| --- | --- | --- |
| Paris [P2]: la capa «Cambios de configuración» omitía la evolución de la latencia | `filter.ids` pasa de `[7, 8]` a `[7, 8, 24]`; comprobado en Grafana 11.3.0 real con dos pares comparables y un cambio de batería el 12/10 | 1.1 |
| Lucia: «Estado de los casos por ejecución» no filtra por fuente | `AND r.source = 'JUP-070'` en el `WHERE` principal; una ejecución de JUP-071 con grupo y métrica `cases` ya no aparece | 1.2 |
| Lucia: qué es `human` y qué `automatic` para JUP-071 | Subsección «Contrato de clasificación para nuevas fuentes» en la guía | 2.1 |
| Lucia (2.ª vuelta, ajustes 1 y 5): las tablas «(detalle)» empujan la evolución, la calibración y el benchmark | Las dos tablas «(detalle)» pasan al final de la sección A y las evoluciones suben justo detrás de la matriz (sin plegar filas: una fila plegada anida sus paneles y la conciliación recorre los de primer nivel) | 1.3 |
| Lucia (ajuste 7): títulos de la sección C cortados | «Consultas al asistente por minuto», «Latencia p95, todas las rutas» y «Tasa de error del backend» (≤ 40 caracteres); «tráfico real» pasa a la descripción | 1.4 |
| Lucia (ajuste 8): `08-10` se lee como 10 de agosto | Cabecera de la matriz `2026-10-08 20:13 · tipo` | 1.5 |

## Evidencia TDD

| Fase | Commit | Evidencia |
| --- | --- | --- |
| Red | `bb2fdbd3` | `test_evaluation_readability_annotations_source.py`, 17 pruebas (12 en rojo antes): filtro exacto de la capa, escenario de Paris contra PostgreSQL real (una marca «Cambia: bateria» y las tres evoluciones con puntos a ambos lados), filtro por fuente estático y con una ejecución sintética de JUP-071 (con y sin el filtro, para demostrar que el escenario discrimina) y contrato de la guía. Sobre una referencia, 19 mutantes muertos |
| Green | commit siguiente a `bb2fdbd3` (título «Green 1.1 y 1.2»), con `evaluation-dashboard:test` 1818 OK en 175 s | `filter.ids` y `WHERE` del panel de estado de los casos; guía. Las 17 pasan; 194 pruebas de lectura, 149 del dashboard y 22 de conciliación en verde con el parche de una prueba congelada (`test_evaluation_dashboard_visible.py`, que exigía exactamente dos paneles anotados) aplicado por el usuario |
| Red (1.3 a 1.5) | `bbf6d218` | `test_evaluation_readability_order_titles_date.py`, 28 pruebas (21 en rojo antes); 21 mutantes sobre una referencia, todos muertos |
| Green (1.3 a 1.5) | commit siguiente (título «Green 1.3 a 1.5») | Reordenación de `gridPos` y de la lista de paneles, títulos de C y fecha ISO, con un parche a 5 ficheros de pruebas commiteadas que aplicó el usuario (cabeceras `DD-MM`, títulos antiguos; un método renombrado porque «tráfico real» ya no está en el título); 11 mutantes del JSON siguen muertos con las pruebas parcheadas; `evaluation-dashboard:test` sin fallos |

## Validación con Grafana 11.3.0 real

PostgreSQL 17 con el provisioning y el dashboard del repo; manifiesto versionado más cuatro ejecuciones sintéticas de JUP-070 (batería 1.0.0 los días 10 y 11 de octubre, otra batería los días 12 y 13) y una ejecución sintética de JUP-071. Las tres evoluciones (métricas automáticas, latencia de la campaña y juicio humano de hitos) dibujan la marca vertical naranja del cambio de batería del 12/10 en la misma posición. «Estado de los casos por ejecución» muestra las seis campañas de JUP-070 y no la de JUP-071, que sí aparece en «Ejecuciones cargadas». Capturas en `docs/evidence/JUP-121/lectura/` (`anotaciones-3-evoluciones.png`, `estado-casos-sin-jup071.png`). Una segunda recaptura con la sección A reordenada (`orden-seccion-a.png`) y los títulos de la sección C a 1440 px (`titulos-seccion-c-1440.png`) confirma el orden, las cabeceras `2026-10-08 20:13 · …` y que los tres títulos de C se leen enteros. El entorno y los datos de JUP-071 son sintéticos; no acreditan el informe real de robustez.

## QA independiente

Veredicto `accept`, sin hallazgos BLOCKING. Verificó por su cuenta: la tabla requisito → panel → prueba; las anotaciones con un escenario propio (dos pares en noviembre con cambio de batería: la consulta de la capa devuelve la marca y las tres evoluciones tienen puntos a ambos lados; `filter.ids` es exactamente las tres evoluciones); el estado de los casos con una ejecución de JUP-071 y una campaña extra de JUP-070; que el SQL de las dos tablas «(detalle)» es byte a byte el anterior; que el orden, los títulos de C (33, 29 y 25 caracteres) y las cabeceras de la matriz son los pedidos; que los parches a pruebas congeladas conservan el número de métodos y no bajan el de aserciones (194→200, 105→105, 83→83, 37→41, 16→16, 21→24); la suite completa (1846 OK, sin skips); y 25 mutantes manuales (20 del JSON y 5 de la guía), todos muertos. Hallazgos medios, ya corregidos: `RF-070-001` estaba duplicado en el backlog (pasa a `RF-070-012`) y la continuidad no mencionaba este change. Bajos: la spec principal exigía «backend» en el título de la latencia (el delta modifica el requisito: el título dice «todas las rutas» y la descripción, que son del backend), el resumen de la evidencia estaba desactualizado (corregido), las tablas «(detalle)» no se plegaron (queda dicho a Lucia y en la continuidad) y la cabecera de la primera columna de la matriz se corta a 1600 px (diferido).

## Hallazgos diferidos (severidad baja)

- «Evolución de la latencia de la campaña» tiene `decimals: 0` con unidad `ms`: con el panel ampliado el eje Y repite etiquetas (`6 s, 6 s, 5 s…`); en el tamaño normal no se nota.
- La leyenda en tabla de las evoluciones muestra unas tres filas a tamaño normal y hay que desplazarla; los nombres de serie son largos.
- La última etiqueta del eje X sale cortada en los tres paneles de evolución.
- «Ejecuciones cargadas» (h = 10) oculta por scroll la novena fila cuando hay 9 ejecuciones; con las 5 versionadas cabe. La matriz con 6 o más ejecuciones desborda horizontalmente a 1600 px.
- «Consultas al asistente por minuto» repite «consultas/min» en la leyenda si hay dos series (instancias) por la falta de `sum()` de la consulta heredada.
- La lectura del panel «Robustez (JUP-071)» (nombres y traducciones) queda para la rama de JUP-071.
- Propuestas de Lucia dejadas para una tarjeta de pulido: columnas repetidas (2), referencias JUP en el texto visible (3), descripciones de los ⓘ (4), calibración y benchmark en español (6), sección C sin duplicar el técnico (9) y gráficas para la sección B y la calibración (10). Cambian muchos títulos, descripciones y columnas que las pruebas fijan.

## Human Approval

- Change: jup-121-anotaciones-y-fuente
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-10-16
- Review accepted: yes
- Checks accepted: yes
- Documentation synchronized: yes
- Archive decision: archive
- Notes: 7/7 tareas; evaluation-dashboard:test 1846 OK; Red con 17 y 28 pruebas nuevas; mutación sobre referencias (19 y 21 mutantes muertos), sobre las pruebas parcheadas (11 muertos) y QA independiente accept con 25 mutantes manuales muertos; validado en Grafana 11.3.0 real. Pruebas congeladas actualizadas con tres parches aplicados por el usuario. Excepción de entorno del DoD: la regresión completa sigue en rojo por las pruebas del processor de JUP-035 (falta tokenizer.json generado), ajenas al change. Pendiente fuera de este gate: revalidación de Paris y revisión técnica de Alejandro; propuestas de pulido de Lucia (2, 3, 4, 6, 9 y 10) para una tarjeta aparte; lectura del panel de robustez en la rama de JUP-071.
