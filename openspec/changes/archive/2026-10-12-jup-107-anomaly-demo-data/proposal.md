JUP: JUP-107
Trello: https://trello.com/c/ADFz3fpR

## Why

JUP-030 ya expone `POST /billing/anomalies/evaluate`, pero el dataset público de Azure son céntimos de un mes y los datos sintéticos de JUP-106 no tienen dos periodos iguales comparables: casi todos los grupos tienen base ausente o cero, y la única subida sale de un importe de prueba de más de 9 billones. Con esos datos no se puede enseñar una alerta por subida creíble ni distinguirla de una alerta solo por umbral. La demo de JUP-107 (aprobada) cubre varios meses y dos monedas; falta el caso de anomalías.

## What Changes

- Una herramienta autocontenida `scripts/synthetic_anomalies.py` con `apply`, `status` y `remove`, con el mismo patrón que `synthetic_costs.py` (prefijo propio `synthetic-jup107-`, idempotente, se niega si el tenant tiene datos de coste que no son suyos, retira solo sus filas) que carga en `tenant-core` un conjunto sintético en EUR con dos periodos de siete días consecutivos y siete servicios diseñados: una subida clara con umbral superado, un servicio que solo supera el umbral, uno estable, uno que baja, una subida porcentual alta por debajo del incremento mínimo, una base con cero registrado y un servicio nuevo sin periodo anterior.
- Un fichero de valores esperados con las reglas de la demo (umbral `2000.00`, subida `50.00`, incremento mínimo `100.00`) y una prueba sin base de datos que los recalcula con suma exacta y falla si el conjunto o los esperados se desalinean.
- Una guía `docs/demo/JUP-107/anomalias.md` para enseñar las alertas llamando al endpoint (Swagger o un script que no imprime la contraseña), con la petición, las dos alertas esperadas, los cinco grupos sin alerta y por qué, la declaración de que los datos son sintéticos y la limitación de que el panel `/anomalies` sigue con su fixture.
- Un paso de CI y una comprobación de retirada y de que no interfiere con los datos de JUP-106.

Fuera de alcance: cambiar el código de `apps/` (incluido conectar el panel `/anomalies`, que será otro cambio con su propia tarjeta y su propia segunda opción de diseño), modificar los datos ni la herramienta de JUP-106, el dataset público o los artefactos de JUP-065, datos de un tenant real y medir la calidad de la detección: los importes ilustran cómo se comportan las reglas, no demuestran que detecten anomalías reales.

## Capabilities

### New Capabilities

- `synthetic-anomaly-data`: conjunto sintético de coste con dos periodos comparables para enseñar las alertas de JUP-030, con herramienta de carga y retirada, valores esperados verificados y guía de demostración.

### Modified Capabilities

Ninguna. No cambia ningún requisito de `cost-anomaly-detection`, `synthetic-cost-data` ni `synthetic-cost-demo`.

## Impact

- Nuevo: `scripts/synthetic_anomalies.py`, `scripts/tests/test_synthetic_anomalies.py`, `docs/demo/JUP-107/anomalias.md` y `docs/demo/JUP-107/esperados-anomalias.json`, y una sección en `docs/evidence/JUP-107-validation.md`.
- Cambios de configuración de CI y de scripts: `package.json`, `.github/workflows/ci.yml` y `tools/ci-workflow.test.mjs`, como hicieron JUP-106 y la primera parte de JUP-107.
- Sin cambios en `apps/`, migraciones, `scripts/synthetic_costs.py`, `docs/demo/JUP-065/` ni el dataset público.
- Afecta a quien ensaye: usa `tenant-core`, que debe estar sin costes; si tiene datos de la ingesta pública, la herramienta se niega.
