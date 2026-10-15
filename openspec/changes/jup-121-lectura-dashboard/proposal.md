JUP: JUP-121
Trello: https://trello.com/c/aIdxwsXR

## Why

La validación independiente de la PR #132 (Paris) y la revisión de pairing (Lucia) encontraron dos tipos de problemas en el dashboard de resultados de evaluación entregado por `jup-121-assistant-evaluation-dashboard` (archivado el 2026-10-15):

- **Fallos de las señales en vivo (sección C).** «Tasa de error del backend» dice «Sin datos: no hubo peticiones» cuando sí las hay, solo que ninguna terminó en 5xx (el numerador no tiene series). «Latencia p95 del backend» mezcla todas las rutas y se lee como si fuera del asistente.
- **Lectura difícil para quien entra sin contexto.** La tabla de calidad tiene unas 30 filas por ejecución con identificadores sin nombre (`ACC-2 · judged`, `REL-4 · q1`); los metadatos de la ejecución se repiten en cada fila y ocupan dos tercios del ancho; no hay un resumen arriba; «Estado», «Resultado» y «Conducta» tienen varios sentidos; la sección B muestra numeradores en bruto (`360000` ms, `70000` céntimos); el texto «Cómo leer la sección A» obliga a hacer scroll. Además la latencia de la campaña no aparece en la evolución automática, que la tarjeta pide, y el intervalo de confianza se carga pero no se muestra.

Paris pidió además reconciliar `tools/local-doctor.test.mjs` con la variable obligatoria `GRAFANA_EVALUATION_DB_PASSWORD` (cambio de pruebas fuera de este change: se entrega como parche).

## What Changes

- **Sección C.** La tasa de error vale 0 mientras no haya respuestas 5xx y solo muestra «Sin datos» cuando no hubo peticiones. La latencia p95 se rotula como la del conjunto del backend (todas las rutas), no la del asistente.
- **Tabla por métrica y ejecución (nueva).** Una fila por métrica y variante con su nombre legible, una columna por ejecución y el intervalo de confianza del 95 % cuando exista; sin metadatos repetidos. Las tablas actuales por fila se conservan debajo como «detalle» para auditoría y conciliación.
- **Resumen de la última campaña (nuevo)** al principio de la sección A: fecha, tipo de ejecución, casos aprobados sobre el total y si ya hay una evaluación con modelo real.
- **Etiquetas.** «Estado» pasa a «Tipo de ejecución», se quita «Resultado» cuando todo está medido y las conductas se traducen («Conducta» pasa a «Variante»).
- **Sección B.** Numerador y denominador se muestran con la misma unidad que el valor (minutos y euros).
- **Textos.** «Cómo leer» de la sección A queda en tres viñetas y el resto va a la guía; cada sección dice a la vista qué no demuestra.
- **Evolución de la latencia de la campaña (nuevo panel)**, separado de las proporciones porque su unidad es distinta.
- **Documentación.** Apartado «Calculado y no mostrado» en `docs/validation/evaluation-dashboard.md`, con el motivo de cada cifra que se calcula o no se carga y no se enseña.

No cambia el contrato `rows-v1`, los adaptadores, el esquema SQL, el rol de Grafana ni las baterías, métricas o umbrales. No se cargan datos nuevos (corpus, casos críticos, calibración por categoría) ni se añaden semáforos: queda documentado como decisión.

## Capabilities

### Modified Capabilities

- `assistant-evaluation-dashboard`: la lectura del dashboard (nombres, resumen, tabla por ejecución, etiquetas, unidades), la evolución de la latencia de campaña y las dos correcciones de la sección C.

## Impact

- `apps/monitoring/grafana/dashboards/assistant-evaluation.json` (paneles nuevos y modificados).
- Pruebas del dashboard en `scripts/tests/` (nuevas, más un parche a las congeladas que dependen de columnas o textos que cambian).
- `docs/validation/evaluation-dashboard.md`, `docs/evidence/JUP-121-validation.md` y la spec `assistant-evaluation-dashboard`.
- Sin cambios en `tools/evaluation-dashboard.py`, en el esquema `evaluation` ni en el backend.
