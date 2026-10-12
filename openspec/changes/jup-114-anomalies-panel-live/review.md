# Review JUP-114 (change 2) — Panel de anomalías conectado y datos de demo diarios

JUP: JUP-114 · Trello: https://trello.com/c/F492abeY · Rama: `feat/JUP-114-anomaly-circuit`

## Resumen

Segundo change de JUP-114. Conecta el panel `/anomalies` con los episodios guardados (resumen, bandeja con filtros, «Detectar ahora», detalle con cambio de estado y exportación CSV/PDF), la detección sin límite de 7 días, la lista con «Revisado hasta», indicador sintético y total abierto por moneda, el conjunto de demo diario (134 registros con P1, P2 y P3) y la retirada de episodios con `remove` (`RF-114-007`).

## Revisión adversarial, pasada 1

Revisor independiente (agente `adversarial-reviewer`), que recibió solo los requisitos y el diff `0d98744..HEAD`, sin el razonamiento de quien implementó. Veredicto: `changes-needed`, sin hallazgos de severidad alta.

| Hallazgo | Severidad | Resultado |
| --- | --- | --- |
| ADV-1: la recarga de la lista tras una detección guardada fallaba y el panel decía «No se ha podido completar la detección» | Media | Corregido: se conserva el resultado y se avisa aparte de que la lista no se pudo recargar. Prueba nueva (falla sin el arreglo) |
| ADV-2: al cambiar de cliente con una detección en curso, su resultado aparecía en el cliente nuevo y su botón quedaba bloqueado | Media | Corregido: el resultado se descarta si el cliente ya no es el activo y el bloqueo es por cliente. Prueba nueva (falla sin el arreglo) |
| ADV-3: cadenas largas sin espacios en el detalle a 390 px (motivo de 500 caracteres, `previous_episode_id`, título) | Media | Corregido con `[overflow-wrap:anywhere]` y `pr-8` en el título. Comprobado en Chromium a 390 px, claro y oscuro: el diálogo mide 388 px de ancho y de contenido, sin desborde |
| ADV-4: la exportación CSV escapa con `JSON.stringify` (no RFC 4180) y sin BOM | Media | Registrado `RF-114-011`: componente compartido por seis dashboards y anterior a este change |
| ADV-5: la lista usa SERIALIZABLE sin tratar el reintento de CockroachDB (`40001`) | Media | Corregido: hasta 3 intentos, y el error pasa si no es `40001` o se agotan. Prueba con CockroachDB real |
| ADV-6: la primera detección recorre toda la historia del cliente sin tope ni medida de tiempo | Media | Registrado `RF-114-012`, con medidas del stack real. Aceptado por Lucia como riesgo conocido para el PR de JUP-114 (2026-10-12) |
| ADV-7: `tasks.md` con una línea suelta y casillas sin marcar en el árbol de trabajo | Baja | Restaurado desde `HEAD`; el fichero del disco se había sobrescrito con un buffer antiguo del editor |
| ADV-8: continuidad con «22 registros» como estado actual | Baja | Corregido |
| ADV-9: límite de motivo en UTF-16 frente a puntos de código, «Close» en inglés, nombre accesible ambiguo | Baja | Registrado `RF-114-014` |
| Barrido: nombres de servicio sin normalizar al agrupar | Baja | Registrado `RF-114-013` (change 1) |

Ataques que resistieron según el revisor: recálculo independiente de los esperados de la demo (3619,43 EUR; P1 2807,71, P2 642,86, P3 168,86), validación del motivo de cierre frente al backend, neutralización de fórmulas en CSV y escape de HTML en el PDF, tipos y validadores del contrato, aislamiento entre clientes en SQL y los totales semanales de JUP-030.

## Revisión adversarial, pasada 2

Mismo revisor independiente, sobre los arreglos de la pasada 1 (`git diff 56d2393..HEAD`). Veredicto: `accept`, sin hallazgos bloqueantes ni altos. Ejecutó los 30 tests del panel; no pudo ejecutar la prueba del backend (necesita CockroachDB) ni verlo en navegador.

| Hallazgo | Severidad | Resultado |
| --- | --- | --- |
| ADV-1: con ida y vuelta A→B→A durante una detección, `knownIds` se vaciaba y al terminar se marcaban como nuevos todos los episodios de A | Media | Corregido: lo conocido se guarda por cliente y no lo borra el cambio de cliente. Prueba nueva que, sin el arreglo, falla con 4 filas marcadas en vez de 1 |
| ADV-2: con A→B→A y la detección de A terminada mientras se estaba en B, el resumen de la detección se pierde | Baja | Aceptado: es la decisión de descartar el resultado de otro cliente; queda la lista actualizada |
| ADV-3: con una detección de B en marcha, el botón de A se activa aunque la de A siga corriendo | Baja | Aceptado: el backend serializa y responde `detection_conflict` (409), que el panel explica |
| ADV-4: la lista agota los reintentos sin pausa y devuelve un 500 sin traducir | Baja | Registrado `RF-114-015` |

Resistieron: reintento sin camino sin asignar, conexión nueva y cerrada por intento, solo `40001` se reintenta, filtro por cliente en `onError` y tras la recarga, `reloadFailed` junto al resultado, `[overflow-wrap:anywhere]` sin partir importes, fechas ni etiquetas, y `pr-8` sin solapar el botón de cerrar.

## Validación

| Comprobación | Resultado |
| --- | --- |
| Processor completo | 644 pasan, 65 omitidas, 0 fallos |
| Backend con CockroachDB real (13 ficheros de anomalías, facturación, tenants y jobs) | 362 pasan, 4 omitidas, 0 fallos |
| Backend completo sin base de datos real | 1072 pasan; 145 fallan en `test_*jup047.py` por el fallo conocido de Windows (`socketpair` de asyncio frente a la guarda de red), que también falla en `develop` |
| Migraciones del processor con CockroachDB real | 2 de 5 pruebas (las que cubren la lista de tablas tocada): pasan. Las otras 3 no se repitieron: el processor no cambia y las primeras ejecuciones se interrumpieron por un bloqueo de disco del nodo |
| Frontend | `vitest` 848 de 848 (una primera pasada tuvo 1 fallo intermitente no identificado; pasó en dos repeticiones), `tsc` limpio |
| `openspec:validate`, `jup:check:all`, `jup:cleanup:check`, `lint`, `git diff --check develop` | OK |
| Stack real aislado (`-p jup114v`, volúmenes nuevos) | receta de navegador de la demo: 12 de 12 pasos; control positivo (cifra alterada) falla en D2 nombrando `F01`; panel en escritorio y 390 px, claro y oscuro, sin errores de consola; `remove` deja 0 episodios, 0 marcas y 0 costes; `down -v` |
| Dataset público de 2024 y datos de 2026 en el mismo cliente | La detección no falla: `insufficient_data`, 0,05 s, 36 KB y 778 días saltados |

Defectos de maquetación encontrados en el stack real y corregidos antes de la revisión (`180aa2a`): el `sr-only` de la última cabecera de la tabla alargaba la página a 817 px, y las filas del diálogo se estiraban a 390 px.

## Pendiente

- Evidencia por criterio en `docs/evidence/JUP-114-validation.md` y bloque `## Human Approval` de Lucia.

## Human Approval

- Change: jup-114-anomalies-panel-live
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-10-12
- Adversarial review: accept (pass 2) | accepted findings: ADV-2 y ADV-3 de la pasada 2 (decisiones de diseño), `RF-114-012` (primera detección sobre una historia muy larga, aceptado por Lucia como riesgo conocido del PR) y `RF-114-011`, `013`, `014` y `015` (abiertos)
- Archive decision: archive
- Notes: change 2 de 3 de JUP-114 (panel conectado y datos de demo diarios). Se archiva en la rama `feat/JUP-114-anomaly-circuit` sin abrir PR: los tres changes van en un solo PR al terminar el último. Pendiente en Trello: revisión y validación de las personas con esos roles, confirmación de la criticidad por impacto acumulado con la responsable de las reglas de negocio y el change 3 (ejecución periódica y avisos).
