# JUP-123: reproducir la admisión presupuestaria de la N5

Verificación: 17/10/2026. Corrección del [Request changes de Lucía en PR140](https://github.com/EconomiconFinOps/tfm-economicon/pull/140#pullrequestreview-5559649459).
Esta reproducción es offline: no autoriza continuar una campaña, renovar claves,
liberar reservas ni enviar inferencias.

## Fuente medida, integración y corrección nueva

La N5 final midió el producto `f3ec760d3c483e8798df2be32ea90bb901ebe36d`:
140 respuestas conformes y825 comprobaciones PASS en el alcance local asistido.
La integración publicada antes de esta corrección es `7e7a294b`.
Este delta sólo cambia herramientas presupuestarias, sus pruebas y documentación;
no vuelve a medir ni cambia el chat, sus prompts, corpus, modelo o configuración.

El código base de `tools/chat-eval-budget.py` medido tenía `CAP=20.00` y no se
editó durante aquella campaña. Los operadores externos v2/v3/v4 sí aplicaban:

```python
_budget = module('budget')
_ledger = module('ledger')
assert _budget.CAP == _ledger.budget.CAP == Decimal('20.00')
_budget.CAP = _ledger.budget.CAP = Decimal('30.00')
```

Ambas instancias importadas debían recibir el mismo tope. Sus políticas estaban
fijadas por SHA256, exigían30 USD, verificaban el plan, el runtime y el historial
protegido, y conservaban frescura, claves, reservas desconocidas y duplicados.
No se atribuye a la nueva opción versionada una ejecución histórica que no tuvo.

## Dónde están las variantes originales

[Procedencia por hashes](JUP-123-budget-provenance.json) identifica el código
base de Git, los tres pares step/common, controllers y políticas exactos, con
su ubicación dentro del paquete congelado. Se verificaron los497 archivos sin
importar ni ejecutar operadores. El paquete está en
`materiales/07-evidencias/PR121-local-evaluation/currency-024-f3ec760d-n5-full140-frozen-v1/`
del espacio de coordinación; manifest SHA256
`4838711dac437ce7f63f5e68aa382dc9e8dd0343c4e8f3024579d39346c32984`.
Los originales externos y sus hashes no se modifican ni se copian credenciales.

| Segmento | Admisión | Política | Muestras |
| --- | --- | --- | --- |
| Inicial | api-step-v2 / api-common-v2 | currency-024-policy-v2 |84 |
| Continuación | api-step-v3 / api-common-v3 | currency-024-resume-policy-v3 |36; el último recibo se recuperó por GET |
| Final | api-step-v4 / api-common-v4 | currency-024-resume-policy-v4 |20 nuevas |

Estos operadores están terminados y no deben relanzarse. Las políticas de las
N3 o de campañas d965/CoreWeave anteriores no identifican esta N5 currency.

## Interfaz versionada nueva, con opción explícita

`admit(..., authorized_cap_usd="30.00")` y
`Ledger.reserve(..., authorized_cap_usd="30.00")` permiten reproducir la
decisión sin mutar constantes de módulos. Omitir el argumento conserva20 USD;
cada admisión que necesite30 lo declara explícitamente. El parámetro exige
una cadena decimal finita, positiva y como máximo30. Configurarla no prueba
una autorización humana: el operador debe tenerla antes, junto con las guardas
de ejecución y contabilidad que correspondan. No se añade un flag CLI ni un
runner que reabra campañas; las rutas existentes sin el argumento siguen en20.

Los campos de contabilidad conservan su significado. La auditoría final registra:

```text
cota de cuenta = 8.077111746
máximos desconocidos íntegros = 15.04040862
cota cubierta = 23.117520366 USD
```

La cota cubierta no es factura ni coste de la N5. Tampoco es el contador upstream:
usar23.117520366 como contador y sumar otra vez los15.04040862 obliga correctamente
a rechazar la operación. La fixture versionada
`tools/fixtures/chat-eval/currency-n5-budget.json` usa identidades sintéticas y
los importes agregados para reproducir la suma correcta con historial completo.
Otra prueba usa literalmente `cumulative_usd="23.117520366"`, una reserva sintética
de1 USD y una nueva operación de0.01:30 explícito admite y20 por defecto rechaza.
Ninguna fixture representa el ledger histórico ni da permiso para continuar.

## Comprobación sin red ni cuenta real

```sh
python -m unittest discover -s tools -p test_chat_eval_budget.py -v
python -m unittest discover -s tools -p test_chat_eval_ledger.py -v
```

Se comprueban20 por defecto frente a30 explícito; equivalencia con el override
histórico; frontera exacta y exceso de1e-9; datos obsoletos/futuros, ámbito y prueba
contable; historial e identidad; IDs/costes inválidos; máximos desconocidos
conservados; duplicados y persistencia/reapertura de un SQLite temporal.
Los rechazos no añaden filas y la reserva se conserva antes de cualquier dispatch.
No se toca la cuenta, ledger1744, contadores, reservas ni claves reales.

Resultado propio del 17/10:27 pruebas budget y13 ledger pasan en Windows
(Python3.14) y Linux (Python3.12.3); las185 pruebas offline `test_chat*.py`
pasan en Windows. No se suman las40 focales dos veces al recuento de185.
Linux usó sólo un temporal acotado y retirado en DockerServer, después de
comprobar identidad/carga/memoria, sin contenedores, puertos, volúmenes ni
servicios. Un primer fallo de serialización del arnés, anterior a los tests,
se conserva separado de los resultados del producto.

Logs, verificación estática de los operadores, comparación antes/después y
recibos de ambas plataformas se conservan en
`materiales/07-evidencias/JUP-123-collector/PR140-budget-20261017/` del espacio
de coordinación. OpenSpec estricto78/78, trazabilidad e higiene conformes.
Estos resultados propios no se atribuyen a CI: el pipeline aún no selecciona
esas suites, como recoge el finding siguiente.

## Reutilización y orden de integración

Este delta presupuestario no necesita integrar otras PR y se publica una sola
vez en PR140 sobre7e7a294b, sin rebase de RAG. Puede revisarse focalmente ahora.
La secuencia propuesta desde Sala de Control (todavía no acordada externamente)
sitúa135→138 y133→134→139 antes de integrar B140; después63 y congelación RC para
071/065. No modifica el alcance de esta corrección ni autoriza otras campañas.

La N5, los dictámenes y los builds previos conservan sus identidades y límites.
Las nuevas pruebas de admisión/SQLite son reutilizables si sus fuentes e inputs
siguen idénticos. La revisión del delta de integración se reserva para la base
consolidada: si cambia recuperación, corpus, prompts o configuración efectiva,
la N5 de f3ec760d no acepta automáticamente el SHA resultante. No se solicita
una validación general de B por cada merge intermedio.

La omisión de estas suites del pipeline se registra como
[RF-123-001](../../openspec/findings/backlog.md#rf-123-001--herramientas-de-evaluacion-b-fuera-del-pipeline),
fuera de este delta; no se modifica CI/package por inferencia.
