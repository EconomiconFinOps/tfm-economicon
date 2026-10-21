JUP: JUP-130
Trello: https://trello.com/c/mkwnaPz2

# Revisión del change `jup-130-indicadores-memoria`

## Resumen

Se añaden tres mediciones reproducibles para la memoria, con su tabla, su informe `rows-v1` y su panel en el dashboard de evaluación:

- Calidad del detector de anomalías: 5 de 7 eventos inyectados detectados (precisión 5/5, recall 5/7, y 5/5 sobre los detectables por diseño). El retraso vale 0 por construcción.
- Coste de IA facturado frente a estimado: 100 de 100 consultas de chat confirmadas por OpenRouter, 0,002601 USD por consulta. El gateway estimó 0,250394 USD y OpenRouter facturó 0,260096 USD; la diferencia la explican cuatro consultas del 2026-10-20 que el gateway registró con gasto 0.
- Frescura y reconciliación de los datos de coste: reconcilian a cero los tres pares inquilino-divisa y la frescura es de 0 días.

No cambia el detector, el gateway ni el backend. En `apps/` solo cambia el JSON del dashboard de Grafana.

## Decisiones

- Cada indicador es su propia fuente (`JUP-130-anomalies`, `JUP-130-data`, `JUP-130-ai-cost`). Con una fuente común, `config_changes` anotaba «Cambia: batería» entre las tres medidas y `comparable_runs` las agrupaba como una serie.
- El panel «Tiempo, asignación y ahorro» (JUP-068) filtra ahora por su fuente: solo filtraba por `measure_type = 'B'` y habría mostrado el coste de IA y los datos.
- El gateway dice qué consultas hubo y OpenRouter lo que se facturó (decisión de Lucia, 2026-10-21). Los embeddings no llevan identificador de generación de OpenRouter y se informan aparte como estimados. Los 429 del registro son del límite por clave del gateway, no del proveedor.
- La reconciliación suma la fuente con aritmética exacta y redondea una sola vez con `ROUND_HALF_UP`, como el contrato de costes; la parte pública de la demo tiene costes de menos de un céntimo.
- Medir y cargar son pasos separados: la herramienta consulta al gateway y a OpenRouter y escribe un informe versionado; `evaluation-dashboard:load` solo lee ficheros.
- ADR: no hay ADR nuevo. La decisión de leer `/spend/logs` desde la herramienta de medición, y no desde Grafana, amplía ADR-0022 sin cambiar su sentido (anotada en la guía del dashboard).

## Validación

| Comprobación | Resultado |
| --- | --- |
| `python -m unittest discover -s scripts/tests -p "test_memory_indicators_*.py"` | 149 pruebas, OK |
| `corepack pnpm evaluation-dashboard:test` (1846 pruebas, con PostgreSQL desechable en Docker) | 1846 pruebas, OK tras actualizar las que fijaban cinco ejecuciones y 269 filas (ahora ocho y 308); resultado final con los últimos cambios |
| `corepack pnpm openspec:validate`, `jup:check -- --change jup-130-indicadores-memoria`, `jup:check:test`, `jup:cleanup:check`, `jup:cleanup:test` | OK (83 de 83 en la validación estricta) |
| `corepack pnpm lint` y `corepack pnpm build` | OK (4 de 4 tareas cada uno; un aviso de ESLint en el frontend, sin errores) |
| API de costes (pytest, Python 3.12) | 81 pruebas, OK |
| Frontend (vitest) | 1380 pruebas en 92 ficheros, OK |
| Backend y procesador (pytest) | **No ejecutables en esta máquina**: falta el paquete `tokenizers` incluso en los entornos del repositorio principal (el mismo cuya descarga falló al construir la imagen). No se ha tocado ningún fichero de `apps/backend` ni de `apps/processor` respecto a develop; lo ejecuta la CI |
| Medición real en navegador (Chromium por CDP) | Los tres paneles muestran datos tras `evaluation-dashboard:load`, en tema claro y oscuro; el panel de JUP-068 no muestra filas de JUP-130; capturas en `docs/evidence/JUP-130/` |

Pruebas con mutantes: se aplicaron cambios deliberados a la herramienta (frontera de la ventana, clase de error de los rechazos, redondeo, orden del tope de generaciones, validación de `total_cost`, cobertura sin consulta, causas) y cada uno hizo fallar alguna prueba. Los mutantes que sobrevivieron al principio llevaron a añadir pruebas (frontera del último día evaluado, orden del emparejamiento, validación de la respuesta de OpenRouter, recuento de días sin registro, fecha de referencia del API).

## Adversarial Review (pass 1)

Revisor independiente (agente `adversarial-reviewer`), base 88a6ce4c, sobre la cabeza `195e4b00`. Veredicto: **accept-with-findings** (sin BLOCKING; dos HIGH que incumplen escenarios explícitos de la spec).

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-1 | HIGH | La cobertura de lo facturado sale como 0,0 % medido cuando OpenRouter no es alcanzable o falta la clave | **Corregido** en `630f4f45` con prueba de regresión: sin consulta es `not_measured`; con consulta y 404 en todo, un cero medido |
| ADV-2 | HIGH | Con el gateway caído o sin clave, la causa no llega al informe | **Corregido** en `630f4f45`: filas `measurement_cause` (`gateway:conexion`, `gateway:http_401`, `gateway:clave_ausente`, `openrouter:clave_ausente`, `openrouter:conexion`…), sin secretos |
| ADV-3 | MEDIUM | El retraso hasta la detección vale 0 por construcción y no mide latencia | **No corregido, declarado**: tabla, panel y guía lo dicen; RF-130-002 en el registro de hallazgos |
| ADV-4 | MEDIUM | Una diferencia enorme de reconciliación aborta el informe; divisa en minúscula distinta | Aceptado por Lucia; RF-130-001 |
| ADV-5 | MEDIUM | `SubscriptionId` sin normalizar mayúsculas; inquilinos vacíos dan un informe vacío con código 0 | Aceptado por Lucia; RF-130-001 |
| ADV-6 | MEDIUM | Filas del gateway con campos ausentes o atípicos producen un error sin controlar | Aceptado por Lucia; RF-130-001 |
| ADV-7 | MEDIUM | La spec pedía frescura «por inquilino y en total» y solo hay por inquilino | **Spec ajustada** a lo entregado (por inquilino); la frescura total no se implementa |
| ADV-8 | LOW | Un alias de modelo fuera del alfabeto cerrado impide generar el informe; un alias `all` duplica la fila global | Aceptado por Lucia; RF-130-001 |
| ADV-9 | LOW | `--reference 0001-01-01` lanza `OverflowError` | Aceptado por Lucia; RF-130-001 |
| ADV-10 | LOW | El panel de evolución automática incluiría las tasas de anomalías con dos ejecuciones de igual clave | Aceptado por Lucia: es el comportamiento genérico previsto del panel (la clave incluye la fuente y las etiqueta bien); no probado en navegador |
| ADV-11 | LOW | `http.client.IncompleteRead` sin capturar; un fallo transitorio de OpenRouter descarta todas las confirmaciones | Aceptado por Lucia; RF-130-001 |
| ADV-12 | LOW | La ventana usa `startTime[:10]` e ignora el desfase horario | Aceptado por Lucia; RF-130-001 (el gateway real emite `Z`) |
| ADV-13 | LOW | Dos filas con el mismo `request_id` cuentan como dos consultas y una confirmada | Aceptado por Lucia; RF-130-001 |

Aceptación: Lucia pidió agilizar el cierre el 2026-10-21 («quiero agilizarlo lo más rápido posible, solo arreglamos si lo vemos prioritario»). Se corrigieron los dos HIGH y se registraron como aceptados el resto de MEDIUM y LOW, con su motivo y sin tocar su código. La lista completa se le presenta antes del `Human Approval`.

Ataques que resistieron (según el revisor): ninguna fuga de las claves ni de los identificadores `gen-` en informes, tablas o salida; gateway caído sin ceros ni error de carga; ventana sin consultas con coste total 0 medido y coste por consulta no medido; rechazos del gateway y errores del proveedor en tasas separadas; el tope de generaciones y la omisión de identificadores sin prefijo `gen-`; determinismo byte a byte de la medición de anomalías; los siete eventos coinciden exactamente con los saltos de al menos 100 EUR del generador; la caída de Compute no genera falso positivo; control positivo de la reconciliación (+0,01 marca `reconciled = 0`); los tres paneles filtran por fuente y grupo con «Tipo/Mide/No demuestra», y el panel de JUP-068 queda acotado.

Barrido de patrones del revisor: atributos de entradas externas sin tolerar ausencia (`item["spend"]`, `item["startTime"]`…), identificadores de Azure sin normalizar (los vecinos usan `casefold`), no medido frente a cero medido (`_rate_ai`, ya corregido para la cobertura), abortar el informe por un valor fuera de rango (`reconcile`) y excepciones solo capturadas en `main`. Los de la cobertura y la causa se corrigieron; el resto está en RF-130-001.

## Adversarial Review (pass 2)

Segunda vuelta del mismo agente independiente, limitada al delta `195e4b00..HEAD` (los arreglos de ADV-1 y ADV-2, la nota del retraso, la etiqueta del panel y la spec de frescura). Veredicto: **accept-with-findings**, sin BLOCKING ni HIGH. Ejecutó las 149 pruebas de la herramienta, que pasan; sus hallazgos salen de leer el código.

| ID | Sev. | Hallazgo | Resolución |
| --- | --- | --- | --- |
| ADV-R2-1 | MEDIUM | `data_report` descarta la causa cuando el API de frescura cae o devuelve 401: las filas pasan a `not_measured` sin motivo en el informe ni en la tabla. Solo `ai-cost` registra la causa; no cambia ninguna cifra, solo la trazabilidad | Aceptado por Lucia; RF-130-001. La guía y la spec de datos no prometen causa para `data` (la fila `measurement_cause` se documenta solo para el coste de IA) |
| ADV-R2-2 | LOW | Si OpenRouter falla a mitad, `_confirm` descarta las generaciones ya confirmadas: el informe queda coherente (facturado y cobertura no medidos, causa `openrouter:conexion`) pero se pierde información medida | Aceptado por Lucia: es una decisión de diseño conservadora (una cifra facturada a medias sería engañosa) |
| ADV-R2-3 | LOW | El renderizado de la fila `measurement_cause` en el panel no tiene control positivo: el mapeo está en el SQL pero ningún informe versionado trae causas, así que no se ha visto en Grafana | Aceptado por Lucia: queda sin verificar en el navegador |

Ataques que resistieron: la cobertura no medida distinta de 0 en los cuatro casos (sin consulta, OpenRouter caído, 404 en todo y sin identificadores de generación); la fuga de secretos en las causas (solo se construyen con cadenas fijas `http_<código>`, `conexion`, `respuesta_invalida`); causas con espacios rechazadas por el contrato; causas duplicadas deduplicadas; un informe totalmente medido no genera filas de causa; la afirmación del retraso coincide con la evidencia y la nota está en la tabla, el panel y la guía; y la spec de frescura coincide con la lógica de los días sin registro.

## Riesgos

- Las cifras de anomalías y de datos son de un conjunto sintético y la lista de eventos la escribió quien diseñó los datos: precisión 1,00 y retraso 0 son en parte esperables. Está declarado en cada tabla y en la nota de continuidad; no hay prueba que lo cierre, es un límite de lo que se mide.
- El coste de IA es local a la máquina que ejecutó las consultas. Declarado.
- La reconciliación y la frescura se midieron con la imagen de backend ya construida de `economicon-ai` (de hace unas 40 horas), porque la construcción falló al descargar el tokenizer. Declarado en la nota de continuidad.
- Conflicto previsto con el PR #144 (JUP-071) y con #141: tocan el manifiesto, el dashboard y las mismas pruebas del dashboard que fijan los recuentos. Quien se integre segundo reconcilia (tras ambos serían 9 ejecuciones y 444 filas).

## Hallazgos registrados

`openspec/findings/backlog.md`: RF-130-001 (robustez de la herramienta ante entradas atípicas) y RF-130-002 (el retraso vale 0 por construcción).

## ADR

No se crea un ADR nuevo; ver «Decisiones».

## Human Approval

- Change: jup-130-indicadores-memoria
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-10-21
- Adversarial review: accept-with-findings (pass 2, sin BLOCKING ni HIGH) | accepted findings: ADV-3 (declarado), ADV-4, ADV-5, ADV-6, ADV-8, ADV-9, ADV-10, ADV-11, ADV-12, ADV-13, ADV-R2-1, ADV-R2-2 y ADV-R2-3, con ADV-7 resuelto ajustando la spec
- Archive decision: archive
- Notes: Lucia aprobó el 2026-10-21 con «sí, acepto» tras ver la lista de lo corregido, lo declarado y lo aceptado sin corregir (RF-130-001 y RF-130-002 en `openspec/findings/backlog.md`). Quedan fuera de esta aprobación y pendientes en Trello: las reviews `Revision JUP-130` (Paris) y `Validacion JUP-130` (Alejandro), la ejecución de la CI en GitHub y las suites de backend y procesador, que no se pudieron ejecutar en local por falta del paquete `tokenizers`. El PR no está abierto.
