JUP: JUP-130
Trello: https://trello.com/c/mkwnaPz2

## Why

La memoria del TFM necesita cifras de tres cosas que hoy ningún dashboard ni informe recoge: cuánto acierta el detector de anomalías de coste, cuánto cuesta la IA por consulta y si los datos de coste están al día y cuadran con su fuente. El dashboard de evaluación (JUP-121) cubre bien la calidad del asistente y las señales en vivo, pero estos tres indicadores son los que sostienen el relato de negocio (detectar a tiempo, gastar poco, fiarse de las cifras) y hoy solo podrían afirmarse sin medida.

Una medición previa con el detector real sobre los datos sintéticos de JUP-107 ya muestra por qué hace falta hacerlo con rigor: de 7 eventos inyectados se detectan 5, y los 2 que faltan (un pico desde cero y la aparición de un servicio nuevo) son una limitación real y documentada de la regla, no un fallo. Es una cifra que la memoria debe poder contar, con sus límites.

Se hace ahora, antes de que JUP-129 rediseñe los dashboards, para que Paris integre estos paneles en su rediseño en lugar de reabrirlo.

## What Changes

- Una herramienta de medición con un subcomando por indicador que emite un informe `rows-v1` versionado y una tabla Markdown reproducible para la memoria:
  - Anomalías: precisión, recall (total y de los eventos detectables por diseño) y retraso hasta la detección, comparando el detector real con una lista versionada de eventos inyectados escrita a partir del generador de datos, no de la salida del detector.
  - Coste de IA: coste facturado por consulta y por modelo, con la diferencia respecto a la estimación del gateway y la cobertura de lo confirmado, y tasa de 429. El gateway aislado (`/spend/logs`) aporta qué consultas hubo y OpenRouter (`/api/v1/generation`) lo que se facturó.
  - Datos: frescura (antigüedad del último día con datos frente a la fecha de referencia) y reconciliación (total normalizado frente a la fuente, con aritmética independiente).
- Los informes se versionan en `docs/evidence/JUP-130/`, se listan en el manifiesto de evaluación y se cargan con el comando existente `evaluation-dashboard:load`. No hay pasos manuales nuevos ni datasource nuevo.
- Paneles nuevos en el dashboard de evaluación, uno por indicador, con tipo, «Mide:» y «No demuestra:». Lo no medido se ve como «No medido» o «Sin datos», nunca como 0.
- Guía y nota de continuidad actualizadas, con capturas del dashboard.

No cambia el detector de anomalías, el gateway ni el backend. Un hallazgo sobre el detector se registra como hallazgo para otra tarjeta.

## Capabilities

### New Capabilities

- `anomaly-detection-quality`: medición de precisión, recall y retraso del detector de episodios frente a eventos inyectados etiquetados de forma independiente.
- `ai-cost-indicators`: coste de IA facturado por consulta y por modelo, diferencia con la estimación del gateway, cobertura y tasa de 429, sin contenido de las consultas.
- `data-freshness-reconciliation`: frescura de los datos de coste y reconciliación del total normalizado con su fuente.

### Modified Capabilities

- `assistant-evaluation-dashboard`: se añaden los paneles de los tres indicadores, su carga con el comando existente y la comprobación de que aparecen con datos en la pila real.

## Impact

- Código nuevo: la herramienta de medición en `tools/`, su prueba y la lista de eventos inyectados en `docs/validation/`.
- `tools/evaluation-dashboard.py` (adaptación a `rows-v1` si hace falta una fuente nueva) y `apps/monitoring/grafana/dashboards/assistant-evaluation.json`, que también tocan los PR #144 (JUP-071) y #141: puede haber conflicto menor al integrar.
- `docs/validation/evaluation-runs.json` (manifiesto) y `docs/validation/evaluation-dashboard.md`.
- Evidencia en `docs/evidence/JUP-130/` y nota en `docs/continuidad/`.
- Dependencias: el coste de IA necesita el gateway aislado (perfil `ai`) con gasto registrado y la clave de OpenRouter para confirmar lo facturado (consulta de solo lectura, sin gasto de modelo); sin ellos los paneles muestran «Sin datos». La reconciliación necesita la pila levantada. JUP-109 (apartado de evaluación de la memoria) consumirá las cifras.
