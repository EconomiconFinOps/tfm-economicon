# Evidencia JUP-114 — change 1: episodios de anomalía guardados

Tarjeta: [JUP-114](https://trello.com/c/F492abeY). Change: `jup-114-persisted-anomalies`. Rama: `feat/JUP-114-anomaly-circuit`. Decisión: [ADR-0020](../adr/ADR-0020-cost-anomaly-episodes.md). Contrato: [anomaly-episodes.md](../api/anomaly-episodes.md).

Validación hecha por la líder de la tarjeta bajo la excepción temporal del 2026-10-11. No sustituye la revisión ni la validación de las personas con esos roles en Trello.

## Criterios de la tarjeta

| Criterio | Este change | Evidencia |
| --- | --- | --- |
| Las anomalías detectadas de un cliente se conservan y no se ven desde otro cliente. | Cubierto en el backend | Tablas `anomaly_episodes` y `anomaly_detection_state` (migración `002`). Pruebas con CockroachDB real: ejecuciones por tenant, lectura de costes sin predicados de tenant detectada por mutante, mismo 404 para id ajeno e inexistente en lectura y cambio de estado. Stack real: `tenant-growth` no ve ni cambia los episodios de `tenant-core` (404 idéntico al de un id inexistente). |
| El panel muestra las anomalías abiertas con criticidad e impacto reales del cliente activo. | No (change 2) | El backend ya expone la lista ordenada por criticidad e impacto; el panel `/anomalies` sigue con su fixture. |
| El estado de una anomalía se puede seguir y se conserva. | Cubierto en el backend | Estados `new`, `investigating`, `resolved`, `false_positive`, transiciones con 409, motivo obligatorio al cerrar (422 sin él), quién y cuándo, primer cambio desde `new` y cierre. Dos cambios simultáneos: exactamente uno gana (CockroachDB real). Stack real: `investigating` y `false_positive` guardados con el usuario demo, cerrado es final. |
| El impacto se muestra por moneda, sin mezclarlas. | Cubierto en la API | Cada episodio lleva su moneda; la lista no tiene totales entre monedas (prueba con episodios EUR y USD). Otras monedas no se evalúan y se informan. La presentación en el panel es del change 2. |
| Hay datos de demostración reproducibles que enseñan varias criticidades. | No (change 2) | Con la regla diaria, el conjunto de JUP-107 abre 4 episodios, todos P2 (ver abajo); los datos de demo con gasto diario y varias criticidades son del change 2. |
| (Etapa 2) Se avisa de las anomalías antes del cierre. | No (change 3) | Sin ejecución periódica ni avisos. |
| Pruebas, documentación y decisiones actualizadas; PR revisado y vinculado; validación y evidencia enlazadas. | Parcial | Pruebas, ADR, contrato, arquitectura, continuidad y hallazgos en este change; el PR es único para los tres changes de la tarjeta y se abre al terminar el último. |

## Comprobación contra el stack real

Stack aislado `docker compose -p jup114` con volúmenes nuevos, construido desde la rama con el árbol limpio. Migraciones `001` y `002` aplicadas. Se cargó el conjunto de JUP-107 con `scripts/synthetic_anomalies.py apply` (1 ingesta, 22 registros sintéticos en `tenant-core`) y se ejecutó un script dentro del contenedor del backend que hace login con el usuario demo sin imprimir la contraseña ni el token: 15 de 15 comprobaciones correctas (detectar, leer, segunda pulsación `up_to_date` sin cambios, cuerpo en la detección 422, cierre sin motivo 422, `investigating`, `false_positive`, cerrado es final 409, lista abierta y completa, 404 idéntico para id ajeno e inexistente, PATCH ajeno 404, `tenant-growth` sin episodios de `tenant-core`, sin token 401).

Resultado de la detección: último día completo 2026-09-13 (el 14 es el último con datos y no se evalúa); evaluados del 8 al 13; el 7 se salta por no tener 7 días previos con datos; 4 episodios abiertos. Cifras comprobadas a mano con una consulta SQL independiente de los costes diarios:

| Servicio | Inicio | Referencia diaria | Impacto acumulado | Criticidad |
| --- | --- | --- | --- | --- |
| Compute | 2026-09-09 | 1000 / 7 = 142,86 | (7400 + 3900 + 2500) / 7 = 1971,43 | P2 |
| Analytics | 2026-09-08 | 2200 / 7 = 314,29 | (6900 + 4800) / 7 = 1671,43 | P2 |
| Database | 2026-09-10 | 600 / 7 = 85,71 | 4300 / 7 = 614,29 | P2 |
| Storage | 2026-09-09 | 800 / 7 = 114,29 | (2840 + 1300) / 7 = 591,43 | P2 |

El conjunto de JUP-107 concentra el gasto de cada semana en uno o dos días, así que, día a día, esos días son picos: Database abre episodio aunque su suma semanal baje. Es el comportamiento de la regla con esos datos, no un fallo; los datos de demo del change 2 tienen que tener gasto diario.

**Revalidación tras la revisión adversarial** (commit `53b5af9`, esquema con `first_reviewed_by`): stack reconstruido con volúmenes nuevos, migraciones `001` y `002` con la columna nueva, mismos datos y 18 de 18 comprobaciones (las 15 anteriores más motivo que se ve en blanco 422, `first_reviewed_by` guardado y conservado tras cerrar, y detección con cuerpo y sin token 401). Las cifras de los cuatro episodios son idénticas.

Al retirar los datos con `remove`, los costes quedan en 0 pero los 4 episodios y la marca de agua (`2026-09-13`) permanecen: confirma `RF-114-007`, que resuelve el change 2. El stack se paró con `down -v`.

## Pruebas automáticas

Backend completo con CockroachDB real: 1126 pasan, 21 omitidas (servicios externos) y 145 fallan, todas en las pruebas de salud de JUP-047 por el fallo conocido de Windows (`socketpair` de asyncio frente a la guarda de red), que también falla en `develop` sin este cambio. Pruebas nuevas: 46 de la regla, 6 de esquema, 11 de acceso a datos y 33 de la API. Las 151 pruebas de JUP-030 y billing pasan sin cambios. 19 mutantes detectados. La CI no ejecuta las pruebas con CockroachDB real (`RF-107-002`): se ejecutaron en local con un nodo desechable.

## No validado

- Panel `/anomalies`, datos de demo con varias criticidades, ejecución periódica y avisos: changes 2 y 3.
- La interpretación de la criticidad sobre el impacto acumulado no está confirmada por la responsable de las reglas de negocio.
- Calidad de la detección con gasto real: los importes son sintéticos.
- Rendimiento con mucha historia o muchos servicios: no medido.
- Revisión y validación de las personas con esos roles en Trello.

## Corrección posterior al archivado del change 1

Al explorar el change 2 se vio que la guarda de propiedad de tablas del processor (`apps/processor/tests/test_schema_ownership_static.py`, exigida por [ADR-0011](../adr/ADR-0011-single-owner-per-table.md)) fallaba: la migración `002` del backend crea `anomaly_episodes` y `anomaly_detection_state`, que no estaban declaradas como tablas del backend. Esa prueba corre en la CI («Python tests»), así que el PR habría salido en rojo; la batería del change 1 solo incluyó el backend. Se declararon las dos tablas en esa guarda y en `BACKEND_TABLES` de `test_schema_migration_ownership.py`. Resultado: guarda estática 76/76, migraciones con CockroachDB real 6/6 (arranque en frío de los dos servicios) y 644 pruebas del processor sin base de datos en verde. La batería de cierre de los changes siguientes incluye el processor.

## Change 2 — panel conectado y datos de demo diarios (2026-10-12)

Change: `jup-114-anomalies-panel-live`. Validación hecha por la líder de la tarjeta bajo la excepción temporal del 2026-10-11; no sustituye la revisión ni la validación de las personas con esos roles en Trello. Revisión adversarial independiente en dos pasadas, detalladas en el `review.md` del change.

### Criterios de la tarjeta

| Criterio | Este change | Evidencia |
| --- | --- | --- |
| Las anomalías detectadas de un cliente se conservan y no se ven desde otro cliente. | Sin cambios respecto al change 1 | Al cambiar de cliente el panel descarta el resultado de una detección que corría para el anterior (prueba nueva) y limpia filtros, detalle y selección. Aislamiento en SQL revisado de nuevo por el revisor adversarial. |
| El panel muestra las anomalías abiertas con criticidad e impacto reales del cliente activo. | Cubierto | Panel `/anomalies` conectado a la API: resumen, bandeja ordenada por criticidad e impacto, filtros, detalle y «Revisado hasta». Receta de navegador contra el stack real: 12 de 12 pasos, con D12 comprobando aviso sintético, «Revisado hasta 20/09», primera fila y detalle. Importes recalculados con aritmética exacta: 3619,43 EUR abiertos; P1 Compute 2807,71, P2 Database 642,86, P3 Analytics 168,86. |
| El estado de una anomalía se puede seguir y se conserva. | Cubierto en el panel | Cambio de estado y cierre con motivo desde el detalle (pruebas del panel); motivo de 500 caracteres sin espacios comprobado en el stack real. |
| El impacto se muestra por moneda, sin mezclarlas. | Cubierto en el panel | Una línea por moneda sin total combinado (prueba), total abierto exacto por moneda desde el backend y exportación CSV por moneda con escape de fórmulas (el PDF se retiró del panel tras la validación del PR #122: no era verificable). |
| Hay datos de demostración reproducibles que enseñan varias criticidades. | Cubierto | `scripts/synthetic_anomalies.py`: 134 registros diarios; la primera detección abre P1, P2 y P3 y `remove` deja 0 episodios, 0 marcas de agua y 0 costes (`RF-114-007`). Demo de 3 minutos con el paso D12. Control positivo de la receta: con una cifra alterada falla en D2 nombrando `F01`. |
| (Etapa 2) Se avisa de las anomalías antes del cierre. | No (change 3) | Sin ejecución periódica ni avisos. |
| Pruebas, documentación y decisiones actualizadas; PR revisado y vinculado; validación y evidencia enlazadas. | Parcial | Pruebas y documentación de este change al día; el PR es único para los tres changes y se abre al terminar el último. |

### Comprobación contra el stack real

Stack aislado `docker compose -p jup114v` con volúmenes nuevos, construido desde la rama; `down -v` al terminar. Panel recorrido en Chromium a escritorio (1440 px) y a 390 px, en tema claro y oscuro, sin errores de consola. Se encontraron y corrigieron dos defectos que las pruebas unitarias no veían: el `sr-only` de la última cabecera de la tabla alargaba la página a 817 px, y las filas del diálogo se estiraban a 390 px. La revisión adversarial añadió las cadenas largas en el diálogo, comprobadas con un motivo de 500 caracteres sin espacios (el diálogo mide 388 px de ancho y de contenido). Con el dataset público de 2024 y los datos de 2026 en el mismo cliente la detección no falla (0,05 s, 36 KB, `insufficient_data`, 778 días saltados; `RF-114-012`).

### Pruebas automáticas

| Comprobación | Resultado |
| --- | --- |
| Processor completo | 644 pasan, 65 omitidas, 0 fallos |
| Backend con CockroachDB real (episodios, anomalías, facturación, tenants, jobs, 13 ficheros) | 362 pasan, 4 omitidas, 0 fallos |
| Prueba del reintento de la lista (`40001`) con CockroachDB real | 3 pasan |
| Backend completo sin base de datos real | 1072 pasan; 145 fallan en `test_*jup047.py` por el fallo conocido de Windows (`socketpair` de asyncio frente a la guarda de red), que también falla en `develop` |
| Migraciones del processor con CockroachDB real | 2 de 5 pruebas repetidas tras un bloqueo de disco del nodo (pasan); la tanda del change 1 con el mismo contenido de pruebas dio 6/6 |
| Frontend | `vitest` 851 de 851 y `tsc` limpio |
| `openspec:validate` 67/67, `jup:check:all`, `jup:cleanup:check`, `lint`, `git diff --check develop` | OK |

### No validado

- Ejecución periódica y avisos (change 3).
- Las 3 pruebas de migración del processor que no se repitieron, y las 145 de JUP-047 en Windows (pasan en Linux/CI según el estado conocido; aquí no se ejecutaron).
- Un fallo intermitente de `vitest` en una primera pasada (1 de 848) que no se identificó; pasó en tres repeticiones.
- Primera detección sobre una historia muy larga o con solapes antiguos: aceptado como riesgo conocido (`RF-114-012`).
- Importes sintéticos: la calidad de la detección con gasto real no está medida.
- Revisión y validación de las personas con esos roles en Trello.

### Nota de release

| Fecha | JUP | Nota de release | Review | ADRs |
| --- | --- | --- | --- | --- |
| 2026-10-12 | JUP-114 (change 2) | El panel `/anomalies` lee los episodios guardados del cliente activo, detecta bajo demanda sin límite de días y cambia estados; los datos de demo diarios abren P1, P2 y P3 y `remove` limpia los episodios. | [review.md](../../openspec/changes/archive/2026-10-12-jup-114-anomalies-panel-live/review.md) | [ADR-0020](../adr/ADR-0020-cost-anomaly-episodes.md) |
