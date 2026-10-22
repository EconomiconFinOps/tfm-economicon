JUP: JUP-133
Trello: https://trello.com/c/Yv1ETc2G

## Why

JUP-132 cambia el modelo por defecto del chat a DeepSeek V4.1 Flash, pero mantiene el alias `economicon-chat`. Las medidas del asistente (conformidad, latencia, coste, robustez) se obtuvieron con GLM-5.2 y dejan de describir el producto. Peor: la ejecución nueva y las antiguas llevarían el mismo `generation_model` (el alias) y la clave de comparabilidad del dashboard las metería en una misma serie, sin que nada avise de que miden modelos distintos.

Parte del trabajo no necesita el modelo nuevo (inventario, identificación de ejecuciones por modelo, plan y plantilla del informe), así que se hace ya. La reejecución con gasto real y el informe con datos esperan a que JUP-132 esté integrado y a una autorización de presupuesto explícita.

## What Changes

- Inventario versionado que clasifica cada métrica, campaña e indicador existente como dependiente del modelo, independiente o histórica, con su justificación, y lo contrasta con el código y los informes (no solo con la memoria).
- Identidad del modelo en cada ejecución: modelo real, proveedor, cuantización y configuración del gateway (huella), además del alias y del commit que ya se guardan. Es una ampliación compatible de `rows-v1` y del esquema `evaluation`: los campos son opcionales y lo no registrado sigue siendo «no registrado».
- La clave de comparabilidad incluye esa identidad, de modo que una serie nunca mezcla modelos distintos aunque compartan alias.
- Las ejecuciones históricas con GLM-5.2 se rotulan con su modelo mediante una anotación en el manifiesto, sin editar los informes originales (que siguen intactos y con la misma huella).
- Plan de reejecución por campaña: coste estimado, presupuesto pedido, autorización requerida antes de cualquier gasto en OpenRouter y criterio de parada.
- Plantilla del informe antes/después con lo no medido rotulado como tal, y lista de cifras de la memoria afectadas, ambas con la columna «después» vacía hasta medir.
- Fase bloqueada por JUP-132 (tareas marcadas como tal): reejecución, informe con datos, lista final de cifras y gasto real frente a presupuesto.

## Capabilities

### New Capabilities
- `model-metrics-reevaluation`: inventario y clasificación de las medidas según su dependencia del modelo, plan de reejecución con presupuesto autorizado, informe antes/después y lista de cifras de la memoria afectadas.

### Modified Capabilities
- `assistant-evaluation-dashboard`: la ejecución registra modelo, proveedor, cuantización y huella de la configuración del gateway; la comparabilidad y las marcas de cambio de modelo se calculan sobre esa identidad y las ejecuciones históricas se rotulan con su modelo.

## Impact

- `tools/evaluation-dashboard.py`: campos nuevos en `run`, anotación de modelo en las entradas del manifiesto, `COMPARABILITY_FIELDS`, DDL del esquema `evaluation` y vistas de marcas de cambio.
- `docs/validation/evaluation-runs.json` y `docs/validation/evaluation-dashboard.md`: anotaciones de las ejecuciones históricas y contrato ampliado.
- `apps/monitoring/grafana/dashboards/assistant-evaluation.json`: columnas de modelo y proveedor donde hoy solo hay alias.
- Pruebas de `scripts/tests/` del manifiesto, de las filas y de las consultas del dashboard.
- Nuevos documentos en `docs/validation/` (inventario, plan, plantilla del informe y cifras de la memoria). La memoria no se copia al repositorio.
- Dependencias: JUP-132 (modelo por defecto) para la fase de reejecución; solapa con JUP-129 (dashboards) y con las tarjetas que tocan `evaluation-runs.json`, a coordinar en el orden de integración.
- Fuera de alcance: elegir otro modelo, repetir la comparativa de modelos, cambiar los instrumentos salvo lo necesario para versionar por modelo y desplegar en DockerServer.
