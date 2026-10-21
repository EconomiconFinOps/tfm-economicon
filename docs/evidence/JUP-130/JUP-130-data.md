# Frescura y reconciliación de los datos de coste (JUP-130)

Fecha de referencia: 2026-10-30. Comando: `python tools/memory-indicators.py data --reference 2026-10-30`. Con `--base-url` se mide contra el API de una pila levantada; sin ella la frescura y la reconciliación quedan como no medidas. Con `--run-at` y `--commit` se fijan la fecha y el commit del informe.

## Por inquilino

| Inquilino | Frescura (días) | Días sin registro en la fuente |
| --- | --- | --- |
| tenant-core | 0 | 0 |
| tenant-growth | 0 | 0 |

## Reconciliación por inquilino y divisa

| Inquilino y divisa | Diferencia (unidades menores) | Reconciliado |
| --- | --- | --- |
| tenant-core/EUR | 0 | sí |
| tenant-growth/USD | 0 | sí |
| tenant-growth/EUR | 0 | sí |

## Qué no demuestra

- La fuente es un conjunto sintético generado por el propio proyecto: reconciliar contra él no demuestra la integridad de datos reales de Azure.
- La frescura se mide contra la fecha de referencia configurada; con una fecha simulada no demuestra puntualidad de una ingesta real.
- Un día sin registro es un hueco de datos, no un día de coste cero; los huecos se cuentan en la fuente.
- Una diferencia de cero demuestra que la suma almacenada coincide con la de la fuente, no que la fuente sea correcta.
