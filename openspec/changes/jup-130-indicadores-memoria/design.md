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

### D2. Coste de IA desde `/spend/logs`, no desde un datasource sobre `litellm-db` (decidido por Lucia el 2026-10-21)

La herramienta consulta `/spend/logs` del gateway con la clave de administración, que lee de variable de entorno o fichero y nunca imprime ni escribe en el informe. Agrega y escribe solo recuentos, sumas y alias de modelo.

*Por qué:* Grafana no entra en la red `gateway`, no hay rol ni contraseña nuevos y el dashboard no se acopla a una tabla interna de LiteLLM que cambia entre versiones. *Alternativa descartada:* datasource de solo lectura sobre `LiteLLM_SpendLogs`: datos en vivo, pero más superficie de seguridad y mantenimiento.

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
| Coste de IA | B | `ai_cost` | `cost_per_query`, `cost_total`, `rate_limited` (tasa de 429) |
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
- **[Clave de administración]** La herramienta la maneja → se lee de entorno o fichero, no se imprime, no entra en informes ni en el manifiesto, y una prueba comprueba que ningún informe contiene el valor.
- **[Conflicto con #144 y #141]** Tocan manifiesto o Grafana → el cambio es aditivo y se reconcilia al integrar.
- **[Retraso hasta detección limitado por la regla]** La regla es diaria, así que el retraso mínimo es de cero a un día por construcción → se declara.

## Open Questions

- ¿De qué ejecución sale la primera medición real de coste de IA que se versiona (la del gasto de las pruebas de JUP-123/JUP-071 en la máquina de Lucia o una medición dedicada)? Hasta que haya una, el panel muestra «Sin datos».
