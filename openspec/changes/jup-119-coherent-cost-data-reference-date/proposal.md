JUP: JUP-119
Trello: https://trello.com/c/HtjtmPaJ

## Why

Los datos de coste de la demo entran hoy por dos caminos distintos y no coinciden en el tiempo. La CLI de ingesta lee el dataset público de Microsoft a través de la API Azure simulada, pero ese dataset son 50 filas de junio de 2024. Los scripts de JUP-106 (`synthetic_costs.py`, enero a julio de 2026) y de JUP-107 (`synthetic_anomalies.py`, 1 a 21 de septiembre de 2026) escriben directamente en `azure_cost_records` y se saltan la API, la CLI y la normalización. El resultado es una demo con datos de tres épocas, que se acaban el 21 de septiembre y que no avanzan: la aplicación no parece viva.

Además, el «hoy» está repartido por el backend y el frontend (`datetime.now()` y `new Date()` en el periodo por defecto de billing, la detección de anomalías, la pregunta de responsables, la validación de la consulta de prueba y los selectores del frontend), así que no hay un solo sitio donde decidir hasta qué día debe verse la información.

## What Changes

- **Ruta única de carga.** Los datos de demostración se generan como CSV con el mismo formato de exportación de Azure que el dataset público, los sirve la API Azure simulada (ya acepta cualquier CSV por `AZURE_COST_DATASET_PATH`) y los carga la CLI de ingesta del processor. El generador es determinista (semilla fija). Los scripts que escribían directo en la base dejan de ser un segundo camino. La decisión y sus alternativas quedan en el ADR-0021.
- **Dataset público con fechas desplazadas.** Un derivado del dataset público con las fechas desplazadas un número fijo de días (de junio de 2024 a septiembre de 2026). Los importes y los identificadores públicos no cambian; las columnas de fecha sí. El fixture original queda intacto y el derivado se etiqueta como «fechas desplazadas» en su manifiesto, en la etiqueta de cada fila y en la documentación; nunca se presenta como facturación de 2026.
- **Datos sintéticos hasta el 30 de octubre de 2026.** Los costes (tipo JUP-106) y las anomalías (tipo JUP-107) se amplían con una serie diaria sintética hasta el 30/10/2026. Con la fecha de referencia en el 22/09/2026 (último día completo: 21/09) siguen saliendo exactamente los mismos totales semanales y los mismos tres episodios de JUP-107; las anomalías nuevas de octubre solo aparecen al avanzar la fecha.
- **Fecha de referencia configurable.** Un ajuste de configuración (`COST_REFERENCE_DATE`, `AAAA-MM-DD`; sin valor, el día UTC real) fija el «hoy» de la aplicación. El backend lo aplica en un solo servicio y la aplicación no muestra costes, episodios ni respuestas del asistente posteriores a ese día. El frontend lo lee del backend en vez de usar su propio reloj y muestra un aviso «Fecha simulada» cuando está fijada.
- **BREAKING (solo herramientas de demo):** `scripts/synthetic_costs.py` y `scripts/synthetic_anomalies.py` pasan a ser el generador y el cargador de la ruta única; las guías `docs/demo/JUP-065`, `JUP-106` y `JUP-107` cambian sus comandos de carga.

Fuera de alcance: el servicio de carga diaria, la ejecución periódica de la detección y los avisos (JUP-115), cambiar la fecha desde la interfaz, datos reales de Azure y conversión de moneda.

## Capabilities

### New Capabilities

- `demo-reference-date`: fecha de referencia configurable que limita lo que ven billing, la detección de anomalías, los episodios y el asistente, y que el frontend lee del backend.
- `demo-cost-data-single-path`: los datos de demostración (dataset público desplazado y series sintéticas hasta el 30/10/2026) se generan en formato Azure, se sirven por la API simulada y se cargan por la CLI de ingesta, con carga idempotente y procedencia visible en cada fila.

### Modified Capabilities

- `synthetic-cost-data`: el conjunto de costes se genera como CSV de la ruta única y cubre hasta el 30/10/2026.
- `synthetic-anomaly-data`: el conjunto de anomalías se genera como CSV de la ruta única, se amplía hasta el 30/10/2026 y conserva los esperados de JUP-107 con la fecha de referencia en el 22/09/2026 (último día evaluado: 21/09); se retira el requisito de «no interferir» de aquel change.
- `azure-public-cost-dataset`: se añade el derivado con fechas desplazadas junto al fixture original sin modificar.
- `synthetic-cost-demo`: la guía de demo declara la fecha de referencia que supone y deja de exigir que el cargador de JUP-106 quede byte a byte igual, porque pasa a ser la ruta única.

## Impact

- `apps/backend`: servicio de fecha de referencia, `billing.py`, `ownership_questions.py`, `schemas/anomalies.py`, `database.py` (tope de fecha en las lecturas de coste y de episodios) y un endpoint de lectura de la referencia.
- `apps/frontend`: periodo por defecto del dashboard y del compositor del asistente, y aviso de fecha simulada.
- `apps/azure-cost-api`: sin cambios de código previstos; se usa su configuración de CSV. `apps/processor`: la CLI de ingesta se usa tal cual; se verifica que acepta las filas del derivado y de las series.
- `scripts/`, `fixtures/azure-cost/` (derivado nuevo, original intacto), `docker-compose.yml` o su perfil de demo, `.env.example`, `docs/demo/`, `docs/adr/ADR-0021`, `docs/architecture.md`, specs sincronizadas al archivar.
- Datos: los costes futuros respecto a la referencia existen en la base pero no se leen. No hay migración de esquema.
