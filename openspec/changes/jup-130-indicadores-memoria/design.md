JUP: JUP-130

## Context

El dashboard de evaluación (JUP-121, ADR-0022) lee del esquema `evaluation` de PostgreSQL, que `evaluation-dashboard:load` regenera por completo desde los informes listados en `docs/validation/evaluation-runs.json`. Todo informe se normaliza al contrato `rows-v1` (`docs/validation/evaluation-dashboard.md`); el panel se entera de una fuente nueva solo por sus filas. Lo no medido es `not_measured`, y el texto libre está prohibido (solo identificadores).

Los tres indicadores de esta tarjeta no tienen informe hoy:

- **Anomalías.** El detector (`apps/backend/app/services/anomaly_episodes.py`, `plan_detection`) es una función pura. El generador de datos (`scripts/demo_dataset.py`) define a mano los eventos inyectados en `SEPTEMBER` y `EXTENSION`. `docs/demo/JUP-107/esperados-anomalias.json` recoge la salida del detector, no etiquetas independientes, así que no sirve como verdad conocida.
- **Coste de IA.** El gateway aislado (`infra/litellm/`, perfil `ai`) tiene su propia base (`litellm-db`, red `gateway`, sin puerto público) y su API de administración en `127.0.0.1:44000`. Ya existe un precedente de lectura de `/spend/logs` en `tools/chat-eval-recover-failed-runtime.py`. El gateway no guarda prompts ni respuestas (`store_prompts_in_spend_logs: false`).
- **Datos.** Los costes normalizados viven en la base del producto y se leen por el API del backend; la fuente es el CSV que genera el generador de datos.

Restricciones: no se toca el detector, el gateway ni el backend; los PR #144 y #141 tocan también el manifiesto o Grafana; JUP-129 rediseñará los dashboards después.

## Goals / Non-Goals

**Goals:**

- Que cada cifra salga de un comando reproducible y deje un informe `rows-v1` y una tabla Markdown para la memoria.
- Que al levantar la pila y ejecutar el comando de carga existente los paneles ya muestren esos datos, como el resto, sin pasos manuales nuevos.
- Que cada cifra declare lo que no demuestra.

**Non-Goals:**

- Cambiar el detector (un fallo real se registra como hallazgo para otra tarjeta).
- Un datasource nuevo, o acceso de Grafana a la base del gateway.
- Medición continua en vivo, deriva del modelo o indicadores de ingeniería (ciclo de PR, CI).
- Cambiar el contrato `rows-v1`.

## Decisions

### D1. Medir y cargar son pasos separados; los informes se versionan

Una herramienta `tools/memory-indicators.py` con subcomandos `anomalies`, `ai-cost` y `data` mide y escribe un `rows-v1` más una tabla Markdown en `docs/evidence/JUP-130/`. Esos ficheros se listan en el manifiesto y los carga el comando existente, igual que los informes de JUP-070 o JUP-078.

*Por qué:* es el mismo patrón que el resto de fuentes; la carga sigue siendo determinista y offline, y funciona en una pila en modo mock; la cifra de la memoria queda atada a un commit y una fecha. *Alternativa descartada:* que `load` consulte el gateway en vivo en cada carga. Haría que la carga dependa de un servicio opcional y que dos cargas den cifras distintas.

### D2. Coste de IA: el gateway dice qué consultas hubo y OpenRouter lo que se facturó (decidido por Lucia el 2026-10-21)

La herramienta consulta `/spend/logs` del gateway con la clave de administración para saber qué consultas hubo (recuentos, alias de modelo, estado, 429) y su coste **estimado**. Después consulta `GET /api/v1/generation` de OpenRouter por cada generación de la ventana cuyo identificador conste en ese registro, para obtener el coste **facturado**. Las dos claves se leen de variable de entorno o fichero y nunca se imprimen ni se escriben en el informe. Se escriben solo recuentos, sumas y alias de modelo.

El coste por consulta del indicador es el facturado cuando existe. Se informa además la cobertura (generaciones confirmadas / generaciones de la ventana) y la diferencia entre estimado y facturado sobre las confirmadas, que cuantifica cuánto se puede fiar de la contabilidad del gateway. Una generación que OpenRouter no devuelve es «no confirmada» y nunca coste 0. `GET /api/v1/key` no se usa como coste de la ventana: es el acumulado de toda la clave, incluido el uso previo.

*Por qué:* el gateway calcula el gasto con una tarifa por token anotada a mano («derived accounting, not an individual upstream invoice», README del gateway) y ya se han visto desajustes con lo facturado; OpenRouter es quien factura. El gateway sigue siendo necesario porque es quien sabe qué consultas hubo y a qué modelo fueron. Grafana no entra en la red `gateway`, no hay rol ni contraseña nuevos y el dashboard no se acopla a una tabla interna de LiteLLM. *Alternativas descartadas:* un datasource de solo lectura sobre `LiteLLM_SpendLogs` (más superficie de seguridad y mantenimiento, y el importe seguiría siendo estimado) y usar solo OpenRouter (no distingue consultas, modelos ni 429 por consulta, y `/key` no se puede atribuir a una ventana).

### D2b. Lo que el registro real enseñó (2026-10-21)

- Los 429 del registro (3) son `ProxyRateLimitError`, el límite por clave del propio gateway; los fallos del proveedor (6) son errores 500 `APIError`. Se informan como dos tasas separadas y no como «429 del proveedor».
- Hay 4 consultas de chat correctas con gasto cero en el gateway. Es el caso en el que el contraste con OpenRouter aporta valor: solo OpenRouter puede decir si fue gratis o un error de contabilidad.
- Una consulta de chat es una fila `acompletion` con éxito; `aembedding` se informa aparte.

### D3. Verdad conocida de las anomalías escrita desde el generador

Los eventos inyectados se versionan en `docs/validation/JUP-130-injected-events.json` con servicio, día de inicio, naturaleza y si son detectables por diseño. Una prueba comprueba contra `anomaly_levels()` que cada evento corresponde a un salto real del generador, y que todo salto significativo del generador tiene su evento, para que la lista no derive del generador ni quede incompleta.

*Por qué:* usar la salida del detector como verdad sería circular. Aun así la lista la escribe quien diseñó los datos, y el informe lo declara en «No demuestra».

### D4. Detectable por diseño como segunda cifra de recall

La regla del detector exige una semana de referencia con coste positivo (`reference_week_cost > 0`) y sus `LIMITATIONS` lo documentan. Se informan dos recalls: sobre todos los eventos y sobre los detectables por diseño. Un evento se da por detectado si hay un episodio del mismo servicio que abre entre el día del evento y tres días después (la tolerancia del detector).

*Por qué:* mezclar ambos escondería la limitación real (servicio nuevo o pico desde cero) o la presentaría como un fallo.

### D5. Tipo y grupos de las filas

| Indicador | `measure_type` | `grp` | Métricas |
| --- | --- | --- | --- |
| Anomalías | A (`judgment: automatic`) | `anomaly_detection` | `precision`, `recall_all`, `recall_designed`, `detection_delay_days`, y recuentos `tp`, `fp`, `fn` |
| Coste de IA | B | `ai_cost` | `cost_per_query` (facturado), `cost_billed_total`, `cost_estimated_total`, `cost_gap`, `billed_coverage`, `cost_embeddings_estimated`, `zero_spend_queries`, `gateway_rejection_rate` (429 del gateway), `provider_error_rate` (5xx del proveedor) |
| Datos | B | `data_quality` | `freshness_days`, `reconciliation_delta_minor`, `reconciled` |

La fuente de las ejecuciones es `JUP-130`. Los indicadores de coste y de datos van como tipo B (decidido por Lucia el 2026-10-21); JUP-129 podrá reagruparlos en sus familias al rediseñar.

### D6. Lo no medido

Sin gateway alcanzable o sin consultas en la ventana, las filas de coste de IA son `not_measured`, nunca 0. Sin pila, la reconciliación es `not_measured`. Un cero medido (0 episodios falsos, 0 respuestas 429) sigue siendo `measured`. Un fallo del proveedor con gasto 0 no se interpreta como llamada gratuita (nota del README del gateway).

### D7. Reconciliación con aritmética independiente

La fuente se suma desde el CSV con `Decimal`, sin usar el código de normalización, y se compara con el total que devuelve el API de resumen de costes para el mismo periodo y divisa. La diferencia se informa en unidades menores como entero.

### D8. Paneles

Un panel por indicador en el dashboard actual, cada uno con tipo, «Mide:» y «No demuestra:» y un solo datasource, como exigen las pruebas estructurales. JUP-129 los integrará en su rediseño; esta tarjeta no reorganiza el dashboard.

### D9. ADR

La decisión D2 amplía ADR-0022 (resultados de evaluación en Grafana) sin cambiar su sentido, así que no se crea un ADR nuevo: se anota en la guía del dashboard y queda enlazada desde este diseño.

## Risks / Trade-offs

- **[Cifra circular]** Los datos se diseñaron para esta regla y la lista de eventos la escribe su diseñador, así que precisión 1,00 y retraso 0 son en parte esperables → «No demuestra» lo dice, la prueba de D3 ata las etiquetas al generador y no se presenta como validez estadística (7 eventos, datos sintéticos).
- **[Primera cifra real de coste de IA]** El gasto del gateway es local a cada máquina; solo hay datos en quien haya usado el gateway → el informe declara el origen y la ventana, y el panel muestra «Sin datos» si no hay medición.
- **[Claves del gateway y de OpenRouter]** La herramienta maneja las dos → se leen de entorno o fichero, no se imprimen, no entran en informes ni en el manifiesto, y una prueba comprueba que ningún informe contiene su valor ni identificadores de generación.
- **[Llamada externa a un tercero]** Consultar `generation` envía a OpenRouter solo identificadores de generaciones propias con la clave del proyecto, es de solo lectura y no consume crédito de modelo → se ejecuta a mano, no en la carga ni en la CI, y con un tope de generaciones por ejecución.
- **[Cobertura incompleta]** OpenRouter puede no devolver alguna generación → se informa la cobertura y la diferencia solo se calcula sobre las confirmadas; una cobertura baja se declara en «No demuestra».
- **[Conflicto con #144 y #141]** Tocan manifiesto o Grafana → el cambio es aditivo y se reconcilia al integrar.
- **[Retraso hasta detección limitado por la regla]** La regla es diaria, así que el retraso mínimo es de cero a un día por construcción → se declara.

## Open Questions

- Resuelto el 2026-10-21 con el gateway real (924 filas, del 9 al 20 de octubre): las 100 filas de chat llevan el identificador `gen-…` de OpenRouter en `request_id` y las filas de embeddings llevan un UUID del gateway, sin identificador de OpenRouter. Por eso el coste por consulta se calcula solo sobre chat y los embeddings se informan aparte como estimados. Una consulta de `GET /api/v1/generation` con esa clave devolvió `total_cost` idéntico al gasto del gateway en la muestra.
- ¿De qué ejecución sale la primera medición real de coste de IA que se versiona (la del gasto de las pruebas de JUP-123/JUP-071 en la máquina de Lucia o una medición dedicada)? Hasta que haya una, el panel muestra «Sin datos».
