# Datos de demo por una sola ruta y fecha de referencia — JUP-119

Verificación: 2026-10-13. [Tarjeta](https://trello.com/c/HtjtmPaJ). Change `jup-119-coherent-cost-data-reference-date`,
rama `feat/JUP-119-coherent-cost-data-reference-date`. [ADR-0021](../adr/ADR-0021-demo-cost-data-single-path-and-reference-date.md).

## Qué contiene

- **Ruta única:** `scripts/demo_dataset.py` genera `fixtures/azure-cost/demo/demo-cost.csv` (formato de exportación de Azure),
  su manifiesto y la definición de ingesta; el derivado del dataset público con fechas desplazadas (822 días) está en
  `fixtures/azure-cost/derived/`. `scripts/demo_data.py` (`generate`, `apply`, `status`, `remove`) carga por la ingesta del
  processor, nunca insertando filas; es idempotente y se niega ante costes ajenos o con `RUNTIME_ENVIRONMENT=production`.
- **Compose:** el perfil `demo` añade `azure-cost-api-demo` y el cargador `demo-data`. El `up` normal no carga nada.
- **Datos:** ventana común del 1/7 al 30/10/2026; solo servicio y etiqueta `Project` (la API agrupa por dos campos). Los casos
  raros de JUP-106 (fila sin fecha, importe con céntimos por encima de 2^53, mayúsculas del grupo de recursos) los cubren
  pruebas de billing con CockroachDB real, no la demo.
- **Fecha de referencia:** `COST_REFERENCE_DATE` (sin valor, el día UTC real). Un servicio del backend decide el «hoy»; las
  lecturas de coste y los episodios no muestran nada posterior; `GET /billing/reference-date` ([API](../api/reference-date.md))
  alimenta al frontend, que avisa con «Fecha simulada».
- **Demo:** el paquete `docs/demo/JUP-107/` se rehízo sobre la ventana común y supone la referencia `2026-10-30`; la guía de
  anomalías usa `2026-09-21` (los tres episodios de JUP-107) y enseña qué cambia con `2026-10-30` (cinco episodios).

## Estado y límites

- Los datos son de demostración (sintéticos o públicos con fechas desplazadas): no son facturas de Azure de 2026.
- La cobertura de etiquetas, los responsables por centro de coste, propietario o aplicación y el desglose por grupo de
  recursos no tienen datos en la demo (limitación de la API de consulta, no del producto).
- El tope por fecha es de lectura, no de acceso: los datos posteriores existen en la base.
- Hallazgos en `openspec/findings/backlog.md` (`RF-119-001` a `RF-119-007`), entre ellos que en Windows un DSN con
  `localhost` espera ~200 s por IPv6 (usar `127.0.0.1`) y que las suites de salud del proveedor fallan en esta máquina con
  `ProactorEventLoop` con o sin estos cambios.
- No hay ensayo humano de la demo; la receta de navegador es una ejecución automatizada.

## Cómo retomar

1. Leer `docs/demo/JUP-107/preparacion.md` y el ADR-0021.
2. Pruebas: `corepack pnpm demo-dataset:test`, `demo-data:test`, `synthetic-demo:test`; con CockroachDB real (nodo desechable en
   memoria con `cluster.organization = 'processor-integration-tests'`, URL con `127.0.0.1`): `JUP086_COCKROACH_TEST_URL` para
   las pruebas del backend y `PROCESSOR_COCKROACH_TEST_URL` para `tests/test_demo_data_end_to_end.py` del processor.
