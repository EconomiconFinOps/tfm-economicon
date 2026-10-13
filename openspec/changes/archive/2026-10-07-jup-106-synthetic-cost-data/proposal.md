JUP: JUP-106
Trello: https://trello.com/c/JwumJnIf

## Why

El dataset público que sirve el simulador de Azure cubre del 1 al 19 de junio de 2024 y una sola moneda (USD). Con él no se pueden ejercitar en la interfaz casos que la funcionalidad de costes ya contempla: series de varios meses con huecos, meses con cero registrado, créditos (importes negativos), dos monedas con meses distintos, importes fuera del rango seguro de `Number` o filas sin fecha. Se vio validando JUP-055 (#77), cuando no se pudo recorrer la comparación entre meses, y JUP-104 describe el mismo límite. Hoy esos casos solo los cubren pruebas automáticas con datos simulados, no un recorrido de quien valida.

## What Changes

- Un conjunto de datos de coste sintético, determinista y versionado, con varios meses de 2026, dos monedas, un cero registrado, un crédito, un importe por encima de `Number.MAX_SAFE_INTEGER`, registros sin dimensión y una fila sin fecha, con una tabla de valores esperados por mes, moneda y agrupación.
- Una herramienta de línea de comandos para cargar ese conjunto en las tablas de costes del stack local, comprobar su estado y retirarlo, de forma repetible y sin tocar datos que no sean sintéticos.
- Un documento para quien valida, con los valores esperados, los comandos y lo que cada caso ejercita, y la declaración explícita de que son datos sintéticos y no facturas de Azure ni valores del dataset público.
- Pruebas de la herramienta (conjunto, totales independientes, guardas, idempotencia) y su prueba contra una base CockroachDB real cuando se disponga de ella, más el paso en CI de las que no la necesitan.
- Una comprobación de extremo a extremo sobre el stack local: carga, consulta de `/billing/summary` frente a los valores esperados, retirada y vuelta al estado vacío.

Fuera de alcance: modificar el dataset público versionado, su procedencia o el simulador; cambiar el esquema, la ingesta o el contrato de `/billing/summary`; datos de un tenant real o de producción; pruebas de carga, rendimiento o accesibilidad; corregir los fallos que se encuentren al validar con estos datos (cada uno, su tarjeta); y automatizar el recorrido de navegador (no se versiona ningún Playwright).

## Capabilities

### New Capabilities

- `synthetic-cost-data`: conjunto de datos de coste sintético y herramienta para cargarlo, consultarlo y retirarlo en el entorno local, con valores esperados documentados.

### Modified Capabilities

Ninguna. No cambia ningún requisito de las capacidades existentes de costes.

## Impact

- Nuevo: `scripts/synthetic_costs.py`, `scripts/tests/test_synthetic_costs.py`, `docs/validation/JUP-106-synthetic-costs.md`.
- Cambios de configuración de CI y de scripts: `package.json` (`synthetic-costs:test`), `.github/workflows/ci.yml` y `tools/ci-workflow.test.mjs`.
- Sin cambios en `apps/`, en migraciones ni en el dataset público. Los datos viven solo en la base local de quien los carga.
- Afecta a quien valide costes con el tenant `tenant-growth`: tras cargar, ese tenant deja de estar vacío hasta que se retire (el documento lo avisa y la herramienta se niega a cargar si hay datos que no son sintéticos).
