# Indicadores medibles para la memoria — JUP-130

Última actualización documental: 2026-10-21. Esta nota no repite el alcance de la tarjeta, que vive en [Trello](https://trello.com/c/mkwnaPz2).

## Estado

- Rama `feat/JUP-130-indicadores-memoria`, creada desde `develop` (88a6ce4c), sin publicar. Roles de la tarjeta: Lucia lidera, Víctor pairing, Paris revisa y Alejandro valida.
- OpenSpec: `openspec/changes/jup-130-indicadores-memoria/` (propuesta, diseño, cuatro specs y tareas). No hay ADR nuevo: la lectura del gateway desde la herramienta de medición amplía [ADR-0022](../adr/ADR-0022-assistant-evaluation-results-in-grafana.md) sin cambiar su sentido.
- Producto: `tools/memory-indicators.py` con tres subcomandos (`anomalies`, `data`, `ai-cost`), la lista de eventos inyectados `docs/validation/JUP-130-injected-events.json`, tres paneles nuevos en `assistant-evaluation.json` y tres entradas en el manifiesto `docs/validation/evaluation-runs.json`.
- Evidencia: informes `rows-v1` y tablas para la memoria en `docs/evidence/JUP-130/`, con capturas de los paneles en Grafana (claro y oscuro). Las cifras y su lectura están en la sección «Indicadores de la memoria (JUP-130)» de la [guía del dashboard](../validation/evaluation-dashboard.md).
- Las tres tablas son la entrada de JUP-109 (apartado de evaluación de la memoria): cada una lleva el comando que la reproduce y su «Qué no demuestra». La memoria no se copia al repositorio.

## Decisiones que no se deducen del código

- **Una fuente por indicador** (`JUP-130-anomalies`, `JUP-130-data`, `JUP-130-ai-cost`). Con una fuente común el dashboard anotaba «Cambia: batería» entre las tres medidas y las agrupaba como una serie comparable, porque `config_changes` y `comparable_runs` tratan una fuente como una sola campaña repetida.
- **El panel «Tiempo, asignación y ahorro» (JUP-068) ahora filtra por su fuente.** Solo filtraba por `measure_type = 'B'` y habría mostrado el coste de IA y los datos.
- **El coste de IA se contrasta con OpenRouter.** El gateway calcula el gasto con una tarifa por token, es una estimación y no una factura. En la primera medición, 4 consultas del 20/10 figuran con gasto 0 en el gateway y OpenRouter las facturó (entre 0,0018 y 0,0029 USD): esa diferencia explica el −0,009702 USD de las 100 consultas. Las otras 96 coinciden hasta el noveno decimal. No se ha investigado la causa del gasto 0.
- **Los 429 del registro son del límite por clave del gateway**, no del proveedor; los fallos del proveedor son 500. Se informan por separado.
- **Los embeddings no llevan identificador de generación de OpenRouter** (los de chat sí, en `request_id`), así que no se pueden contrastar y se informan aparte como estimados.
- **Reconciliación con un único redondeo.** La fuente tiene costes de menos de un céntimo (la parte pública de la demo): se suma exacta y se redondea una vez con `ROUND_HALF_UP`, como el contrato de costes. Con el total de USD de `tenant-growth` (9007199254741838,37) no se pierde ni un céntimo.
- **Una limitación real del detector, no un fallo:** no detecta un pico desde cero ni la primera aparición de un servicio porque la regla exige una semana de referencia con coste positivo (`reference_week_cost > 0`, ya documentada en sus limitaciones). Por eso hay dos recalls: 5/7 sobre todos los eventos y 5/5 sobre los detectables por diseño.

## Límites de la evidencia

- Las cifras de anomalías y de datos son de un conjunto sintético: 7 eventos, etiquetas escritas por quien diseñó los datos y datos pensados para esa regla, así que una precisión de 1,00 y un retraso de 0 días son en parte esperables. No demuestran validez estadística ni comportamiento con facturas reales.
- El coste de IA es local a la máquina que ejecutó las consultas (el gateway aislado de Lucia, del 9 al 20 de octubre) y no es el de un uso real.
- La reconciliación y la frescura se midieron contra el API de una pila mock levantada desde el worktree, con la **imagen de backend ya construida de `economicon-ai` (de hace unas 40 horas), no reconstruida**: la construcción falló al descargar el tokenizer («download limit exceeded»). El backend contiene `/billing/summary` y `/billing/reference-date` (JUP-119), pero no es el de esta rama.

## Qué tocar si cambia algo

- Una medición nueva: ejecutar el subcomando con `--run-at` y `--commit`, versionar el informe y la tabla en `docs/evidence/JUP-130/` y ejecutar `corepack pnpm evaluation-dashboard:load`. Las pruebas de carga fijan el número de ejecuciones y de filas del conjunto versionado (hoy 8 y 308): si cambia, hay que ajustarlas.
- Los eventos inyectados: se cambia `docs/validation/JUP-130-injected-events.json`; una prueba lo contrasta con `anomaly_levels()` del generador y falla si no coincide.
- Un indicador nuevo: otra fuente `JUP-130-…` o propia, con su grupo; el panel lo recoge por su fuente.

## Pendiente

- Conflicto previsto con el PR #144 (JUP-071) y con #141: tocan el manifiesto, el dashboard y las mismas pruebas del dashboard que fijan los recuentos. Quien se integre segundo debe reconciliar (tras ambos serían 9 ejecuciones y 444 filas) y la clasificación de los paneles en las pruebas estructurales.
- JUP-129 (lidera Paris) rediseñará los dashboards: los tres paneles de esta tarjeta entran en ese rediseño.
- Revisión adversarial, revisión técnica de Paris, validación de Alejandro y `Human Approval` de Lucia sin hacer; el comentario de trazabilidad en Trello sin publicar.
