# Evidencia de validación JUP-107

Tarjeta: [JUP-107](https://trello.com/c/ADFz3fpR). Change: `openspec/changes/archive/2026-10-08-jup-107-synthetic-cost-demo/` (tras archivarlo). Paquete: [`docs/demo/JUP-107/`](../demo/JUP-107/README.md).

Esta evidencia recoge lo que se ejecutó al implementar el change. **No es una validación independiente** (esa corresponde al rol de validación de la tarjeta) y **no es un ensayo con una persona presentando**: la ejecución de la receta es automatizada.

## Entorno

- Commit de la aplicación y del paquete de demo: `c1cc7bd` (rama `feat/JUP-107-synthetic-cost-demo`, sobre `develop` `2f9a5f5`).
- Stack Docker Compose aislado (`-p jup107`, volúmenes nuevos), Windows, Docker Desktop. Datos sintéticos cargados con `scripts/synthetic_costs.py` en `tenant-growth`.
- Receta de navegador: Node `v24.15.0`, `playwright-core` `1.63.0`, Chromium `153.0.8010.12` (revisión `1243`). Ejecución fuera del repositorio.

## Ejecución automatizada de la receta (modo: automatizada)

Fecha: 2026-10-08, sobre `c1cc7bd`. Resultado por paso (segundos medidos por la receta, no cronometraje de una persona):

| Paso | Resultado | s | Qué comprobó |
| --- | --- | --- | --- |
| D1 | pass | 2 | Core Finance activo y ningún importe en pantalla antes de la declaración |
| D2 | pass | 4 | Periodo «enero de 2026 – junio de 2026 (UTC)», totales EUR 90.00 (6) y USD 35.75 (2) |
| D3 | pass | 2 | Desglose por servicio, incluida la fila «Sin dimensión» |
| D4 | pass | 2 | Febrero 0.00 (1), marzo «—» y «Sin datos de esta moneda.», enero 100.00 (2), abril 40.00 (2); la curva del gráfico se interrumpe |
| D5 | pass | 2 | Mayo -50.00 (1); comparación mayo frente a enero, -150.00 EUR y -150.00 % |
| D6 | pass | 2 | Febrero 10.50 (1), junio 25.25 (1); comparación junio frente a febrero, +14.75 USD y +140.48 % |
| D7 | pass | 2 | Etiqueta `cost_center`: finance, ops y sin dimensión |
| D8 | pass | 2 | Aviso de 1 registro sin fecha excluido |
| D9 | pass | 3 | Core Finance sin datos y, al volver a Growth Ops, el periodo y los totales se conservan |
| D10 | pass | 2 | Paso hablado, sin comprobación de interfaz |
| D11 | pass | 5 | Opcional: aviso del límite de representación y 9007199254740993.01 (1) |

No se midió ni se afirma la duración de una presentación con una persona. Un ensayo humano solo existe cuando hay un registro relleno en `registro-ensayo.md`; no hay ninguno.

## Controles positivos

La receta se ejecutó con `esperados.json` alterado y con entornos alterados; cada uno falla nombrando la causa y marca los pasos siguientes `not_run`:

- cifra de desglose `F03` alterada: `D3 fail: F03: falta la fila Compute EUR 100.01 (2)`;
- mes sin datos tratado como cero (`F11`): `D4 fail: F11: falta la fila mensual 2026-03 EUR 0.00`;
- porcentaje de la comparación en dólares alterado (`F17`): `D6 fail: F17: falta la variación porcentual +140.49`;
- una marca `no_amounts` puesta en un paso que muestra importes: `hay importes en pantalla antes de la declaración`;
- la comprobación del hueco aplicada a un mes sin curva: el paso falla;
- contraseña incorrecta: sale con código 2 y «No se pudo iniciar sesión».

## Comprobante por API

Con los datos cargados, el fragmento de `preparacion.md` imprime `data_status: partial`, `EUR 90.00 6` y `USD 35.75 2` para `tenant-growth` entre 2026-01-01 y 2026-07-01 (julio no entra), e imprime `data_status: empty` para `tenant-core`. Tras `remove`, imprime `data_status: empty` para `tenant-growth`.

## Estado inicial recuperado

`remove` repetido: `Retiradas 2 ingestas y 10 registros sinteticos.` y `Retiradas 0 ingestas y 0 registros sinteticos.`; `status` en `absent`; stack parado con `docker compose -p jup107 down -v` y sin volúmenes restantes. `apply` repetido informa `already-present` y no duplica nada.

## Pruebas y batería

| Comando | Resultado |
| --- | --- |
| `corepack pnpm synthetic-demo:test` | 40 pruebas correctas; también en `python:3.12-slim` sin paquetes |
| `corepack pnpm synthetic-costs:test` | 46 pruebas, 8 omitidas |
| `node --test tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 25 de 25 |
| `corepack pnpm openspec:validate` | 53 de 53 |
| `corepack pnpm jup:check:all`, `jup:cleanup:check` | correctos (913 archivos) |
| `git diff --check` | limpio |

## Hallazgos de la ejecución contra la interfaz real

- La pantalla arranca con los seis últimos meses completos según la fecha del día; el guion fija siempre el periodo.
- El total se muestra como «TOTAL EUR» (mayúsculas); la receta lo detectó al fallar el primer intento.
- El periodo se conserva al cambiar de cliente (comprobado). Por la lectura del código, el cliente activo se recupera del almacenamiento del navegador entre sesiones; no se comprobó en pantalla, pero la preparación pide abrir con Core Finance antes de D1 y la receta comprueba que lo está.
- Durante una ejecución la base de datos del stack aislado se paró por lentitud de disco (un fallo del entorno, no de la demo); se reinició con su volumen y los datos seguían cargados.

## No validado

- Cronometraje con una persona presentando y reproducción independiente de la demo por otra persona.
- La validación funcional de la tarjeta por quien tenga el rol de validación.
- El vídeo final, que no es parte de este change.
- La lógica de la receta no tiene pruebas automáticas propias (RF-107-001).
- Navegadores distintos de Chromium y pantallas móviles.
