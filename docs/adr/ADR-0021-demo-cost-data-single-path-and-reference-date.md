# ADR-0021 — Datos de demostración por una sola ruta y fecha de referencia configurable

- Status: Accepted
- Date: 2026-10-13
- Related JUP/OpenSpec: JUP-119, [jup-119-coherent-cost-data-reference-date](../../openspec/changes/archive/2026-10-13-jup-119-coherent-cost-data-reference-date/design.md)
- Trello: https://trello.com/c/HtjtmPaJ
- Supersedes: none
- Superseded by: none

## Context

Los datos de coste de la demostración entraban por dos caminos: la CLI de ingesta, a través de la API Azure simulada ([ADR-0001](ADR-0001-azure-cost-api-simulation.md)), con el dataset público de junio de 2024 (50 filas), y dos scripts (`synthetic_costs.py` de JUP-106 y `synthetic_anomalies.py` de JUP-107) que escribían directamente en `azure_cost_records`. Los datos eran de tres épocas distintas, acababan el 21 de septiembre de 2026 y no avanzaban con la fecha. Además, el «hoy» se decidía con el reloj en varias rutas del backend y del frontend.

Un sondeo del 2026-10-13 con CockroachDB real (nodo desechable, API y CLI locales) midió qué puede cruzar la ruta API → CLI: la API agrupa como máximo por dos campos; devuelve como número decimal en coma flotante lo que no es entero (`9007199254740993.01` se guardó como `9007199254740994`); rechaza una fila sin fecha y la etiqueta `dataset_origin` (no está en el mapa de etiquetas); y la ingesta de las siete parejas de la demo tarda unos 15 s (una primera medida de 133 s por llamada de la CLI era un artefacto de usar `localhost` en el DSN en Windows, que espera a agotar el tiempo de conexión por IPv6; con `127.0.0.1`, la inicialización de la base tarda 0,4 s).

## Decision

1. **Una sola ruta para los datos de demostración:** un generador determinista produce un CSV en formato de exportación de Azure y un manifiesto; la API simulada lo sirve con `AZURE_COST_DATASET_PATH`; la CLI de ingesta lo carga por pareja tenant/suscripción. `scripts/demo_data.py` (`generate`, `apply`, `status`, `remove`) es el único punto de entrada y no inserta filas por sí mismo.
2. **Dos agrupaciones por consulta: servicio y etiqueta `Project`.** Es el máximo que admite la API y lo que necesitan el dashboard, las anomalías y los responsables por proyecto. Una segunda definición sobre la misma suscripción solaparía ingestas (ADR-0010).
3. **La demo solo lleva lo que una API de Azure puede entregar.** La fila sin fecha, el importe con céntimos por encima de 2^53 y los grupos de recurso que solo difieren en mayúsculas pasan a pruebas de inserción directa, con CockroachDB real y su propio tenant, y no se cargan en ningún tenant de la demo. Que esas filas no entren al sistema (validación en la ingesta) es un cambio de producto y se registra como hallazgo.
4. **Procedencia por suscripción**, no por etiqueta: suscripciones con prefijo `synthetic-` o la pública del manifiesto. `apply` se niega si un tenant tiene datos de una suscripción ajena al manifiesto.
5. **Una ventana común de 1/7 a 30/10/2026** para los tenants de la demo, con el dataset público desplazado (1 a 19/9) como complemento documentado. El derivado público desplaza las fechas un número fijo de días, deja el fixture original intacto y se declara como derivado.
6. **Fecha de referencia** (`COST_REFERENCE_DATE`; vacío, el día UTC real) resuelta por un único servicio del backend. El tope vive en la capa de lectura (`Database`) para que ninguna ruta pueda olvidarlo, y los episodios cuyo último día visto no es anterior a la referencia se ocultan con el mismo 404 que un id desconocido. El frontend la lee del backend y muestra «Fecha simulada» cuando está fijada.
7. **Carga opt-in:** el `docker compose up` normal no carga nada; un perfil `demo` ejecuta `apply` una vez, es idempotente y solo funciona con `RUNTIME_ENVIRONMENT=development` o `test` (valor exacto). Una ingesta original del dataset público de una suscripción de la demo cuenta como datos ajenos y no se borra.

## Consequences

- La demo pasa por la ingesta real y la fecha de la aplicación es una sola; la aplicación puede «avanzar» cambiando un ajuste.
- Tres pantallas muestran lo ausente con los datos de demo: la cobertura de etiquetas («Cumple: 0,00 %»: la política exige las cinco etiquetas y un registro incompleto no cumple), los responsables por centro de coste, propietario o aplicación («datos insuficientes») y el desglose por grupo de recursos (todo «Sin dimensión», por suscripción). Es una limitación de la demo y de la API, no del producto.
- Los datos posteriores a la referencia existen en la base aunque no se lean: no es un control de acceso.
- Retroceder la fecha oculta episodios; para repetir la demo desde cero se usa `remove` y `apply`.
- La carga completa es rápida: unos 15 s de ingesta más el arranque de cada una de las siete llamadas a la CLI. Medido en Docker Desktop sobre Windows; en otro entorno puede variar.

## Alternatives Considered

- **Mantener los inserts directos y compartir solo el generador:** descartada; deja dos caminos y la ingesta real nunca ve los datos de demo.
- **Un endpoint de importación masiva en el backend:** descartada; superficie nueva de escritura sin necesidad.
- **Ampliar la API simulada con más agrupaciones e importes exactos:** descartada; se aleja de la API real de Azure, que es lo que ADR-0001 quería imitar.
- **Servicio de carga diaria y proceso batch de la detección:** fuera de alcance; JUP-115.
- **Recalcular el impacto de los episodios hasta la referencia al retroceder:** descartada; obliga a guardar el detalle diario o a releer costes en cada listado.

## Evidence And Follow-up

- Sondeo y decisiones: [design.md](../../openspec/changes/archive/2026-10-13-jup-119-coherent-cost-data-reference-date/design.md) (D2 y D6).
- Pendiente de comprobar al implementar: que un importe entero grande sin céntimos cruza la API y la CLI sin pérdida (tarea 2.1).
- Trabajo futuro, registrado en `openspec/findings/backlog.md`: validación de las filas en la ingesta, importes en coma flotante en la API y tiempo de inicialización de la CLI.
