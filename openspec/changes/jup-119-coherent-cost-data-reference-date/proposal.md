JUP: JUP-119
Trello: https://trello.com/c/HtjtmPaJ

## Why

Los datos de coste de la demo entran hoy por dos caminos distintos y no coinciden en el tiempo. La CLI de ingesta lee el dataset público de Microsoft a través de la API Azure simulada, pero ese dataset son 50 filas de junio de 2024. Los scripts de JUP-106 (`synthetic_costs.py`, enero a julio de 2026) y de JUP-107 (`synthetic_anomalies.py`, 1 a 21 de septiembre de 2026) escriben directamente en `azure_cost_records` y se saltan la API, la CLI y la normalización. El resultado es una demo con datos de tres épocas, que se acaban el 21 de septiembre y que no avanzan: la aplicación no parece viva.

Además, el «hoy» está repartido por el backend y el frontend (`datetime.now()` y `new Date()` en el periodo por defecto de billing, la detección de anomalías, la pregunta de responsables, la validación de la consulta de prueba y los selectores del frontend), así que no hay un solo sitio donde decidir hasta qué día debe verse la información.

## What Changes

- **Ruta única de carga.** Los datos de demostración se generan como CSV con el mismo formato de exportación de Azure que el dataset público, los sirve la API Azure simulada (ya acepta cualquier CSV por `AZURE_COST_DATASET_PATH`) y los carga la CLI de ingesta del processor. El generador es determinista (semilla fija). Los scripts que escribían directo en la base dejan de ser un segundo camino. La decisión y sus alternativas quedan en el ADR-0021.
- **Solo lo que la API puede entregar.** Un sondeo con CockroachDB real (2026-10-13) mostró que la API agrupa como máximo por dos campos, que un importe con céntimos por encima de 2^53 pierde precisión (pasa a coma flotante) y que rechaza una fila sin fecha. Por eso la demo agrupa por **servicio y etiqueta `Project`** y no lleva filas sin fecha ni importes con céntimos por encima de 2^53. Se pierden en la demo el grupo de recursos, el centro de coste y el resto de etiquetas: la cobertura de etiquetas muestra cuatro de las cinco etiquetas exigidas sin cubrir, la pregunta de responsables por centro de coste, propietario o aplicación contesta «datos insuficientes» y el desglose por grupo de recursos queda en «no aplica». La carga completa tarda unos 133 s por pareja tenant/suscripción.
- **Los casos raros de JUP-106 pasan a pruebas automáticas.** La fila sin fecha, el importe enorme con céntimos y los grupos de recurso que solo difieren en mayúsculas no son datos que una API de Azure entregaría; se cubren con pruebas de inserción directa en su propio tenant y no se cargan en la demo. Las cifras de enero a julio de JUP-106 se conservan, salvo los céntimos del importe enorme.
- **Hallazgo, fuera de alcance:** que una fila sin fecha o con datos raros no entre al sistema (validación en la ingesta, por ejemplo con modelos Pydantic) es un cambio de producto; se registra en `openspec/findings/backlog.md`.
- **Dataset público con fechas desplazadas.** Un derivado del dataset público con las fechas desplazadas un número fijo de días (de junio de 2024 a septiembre de 2026). Los importes y los identificadores públicos no cambian; las columnas de fecha sí. El fixture original queda intacto y el derivado se etiqueta como «fechas desplazadas» en su manifiesto, en la etiqueta de cada fila y en la documentación; nunca se presenta como facturación de 2026.
- **Datos sintéticos hasta el 30 de octubre de 2026.** Los costes (tipo JUP-106) y las anomalías (tipo JUP-107) se amplían con una serie diaria sintética hasta el 30/10/2026. Con la fecha de referencia en el 22/09/2026 (último día completo: 21/09) siguen saliendo exactamente los mismos totales semanales y los mismos tres episodios de JUP-107; las anomalías nuevas de octubre solo aparecen al avanzar la fecha.
- **Fecha de referencia configurable.** Un ajuste de configuración (`COST_REFERENCE_DATE`, `AAAA-MM-DD`; sin valor, el día UTC real) fija el «hoy» de la aplicación. El backend lo aplica en un solo servicio y la aplicación no muestra costes, episodios ni respuestas del asistente posteriores a ese día. El frontend lo lee del backend en vez de usar su propio reloj y muestra un aviso «Fecha simulada» cuando está fijada.
- **BREAKING (solo herramientas de demo):** `scripts/synthetic_costs.py` y `scripts/synthetic_anomalies.py` pasan a ser el generador y el cargador de la ruta única; las guías `docs/demo/JUP-065`, `JUP-106` y `JUP-107` cambian sus comandos de carga y sus esperados.

Fuera de alcance: el servicio de carga diaria, la ejecución periódica de la detección y los avisos (JUP-115), cambiar la fecha desde la interfaz, datos reales de Azure y conversión de moneda.

## Capabilities

### New Capabilities

- `demo-reference-date`: fecha de referencia configurable que limita lo que ven billing, la detección de anomalías, los episodios y el asistente, y que el frontend lee del backend.
- `demo-cost-data-single-path`: los datos de demostración (dataset público desplazado y series sintéticas hasta el 30/10/2026) se generan en formato Azure, se sirven por la API simulada y se cargan por la CLI de ingesta con dos agrupaciones (servicio y `Project`), con carga idempotente, procedencia por suscripción y pantallas que muestran lo ausente como ausente.

### Modified Capabilities

- `synthetic-cost-data`: el conjunto de costes se genera como CSV de la ruta única, cubre hasta el 30/10/2026, no lleva fila sin fecha ni importes con céntimos por encima de 2^53, y los casos raros pasan a pruebas automáticas.
- `synthetic-anomaly-data`: el conjunto de anomalías se genera como CSV de la ruta única, se amplía hasta el 30/10/2026 y conserva los esperados de JUP-107 con la fecha de referencia en el 22/09/2026 (último día evaluado: 21/09); se retira el requisito de «no interferir» de aquel change.
- `azure-public-cost-dataset`: se añade el derivado con fechas desplazadas junto al fixture original sin modificar.
- `synthetic-cost-demo`: la ruta de demo se prepara con `demo_data.py`, declara la fecha de referencia que supone, deja de mostrar el registro sin fecha excluido y deja de exigir que el cargador de JUP-106 quede byte a byte igual.

## Impact

- `apps/backend`: servicio de fecha de referencia, `billing.py`, `ownership_questions.py`, `schemas/anomalies.py`, `database.py` (tope de fecha en las lecturas de coste y de episodios) y un endpoint de lectura de la referencia.
- `apps/frontend`: periodo por defecto del dashboard y del compositor del asistente, y aviso de fecha simulada.
- `apps/azure-cost-api`: sin cambios de código previstos; se usa su configuración de CSV. `apps/processor`: la CLI de ingesta se usa tal cual; se verifica que acepta las filas del derivado y de las series.
- `scripts/`, `fixtures/azure-cost/` (derivado nuevo, original intacto), `docker-compose.yml` o su perfil de demo, `.env.example`, `docs/demo/`, `docs/adr/ADR-0021`, `docs/architecture.md`, specs sincronizadas al archivar.
- Datos: los costes futuros respecto a la referencia existen en la base pero no se leen. No hay migración de esquema.
