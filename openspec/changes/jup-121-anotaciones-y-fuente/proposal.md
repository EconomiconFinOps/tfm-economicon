JUP: JUP-121
Trello: https://trello.com/c/aIdxwsXR

## Why

La segunda validación de Paris sobre la PR #132 (cambios solicitados sobre `640686e0`) halló que la evolución de la latencia de la campaña no muestra las anotaciones de cambio de configuración: la capa «Cambios de configuración» solo se aplica a los paneles 7 y 8 y omite el panel 24. Es un defecto de `jup-121-lectura-dashboard`: el diseño daba a la nueva gráfica las mismas reglas que a las otras evoluciones, y la anotación es una de ellas.

El comentario de Lucia sobre el encaje de JUP-071 con `rows-v1` señala otro defecto latente: «Estado de los casos por ejecución» promete en su descripción las campañas de JUP-070, pero su consulta toma cualquier fila con grupo y métrica `cases`, así que una ejecución de robustez de JUP-071 aparecería ahí junto a las campañas. Además pide dejar escrito qué filas deben marcarse `human` y cuáles `automatic`, porque la gráfica de métricas automáticas no filtra por fuente y una proporción derivada del resultado de un caso (`pass_over_total`) entraría en ella.

## What Changes

- La capa de anotaciones «Cambios de configuración» se aplica también a la evolución de la latencia de la campaña (panel 24).
- «Estado de los casos por ejecución» solo muestra ejecuciones de JUP-070, como dice su descripción.
- La guía recoge el contrato de clasificación para JUP-071: las proporciones que salen del resultado de un caso son `human`, solo las que decide una regla son `automatic`, y los grupos de JUP-070 no se reutilizan.

No cambia el contrato `rows-v1`, los adaptadores, el esquema ni el panel de robustez (su lectura se hará en la rama de JUP-071, cuando exista el informe).

## Capabilities

### Modified Capabilities

- `assistant-evaluation-dashboard`: anotaciones en todas las evoluciones de la sección A, estado de casos solo de JUP-070 y contrato de clasificación para nuevas fuentes.

## Impact

- `apps/monitoring/grafana/dashboards/assistant-evaluation.json` (filtro de la capa de anotaciones y consulta de un panel).
- Pruebas nuevas en `scripts/tests/` más un parche de las congeladas que fijan exactamente los paneles anotados.
- `docs/validation/evaluation-dashboard.md` y la spec `assistant-evaluation-dashboard`.

## Human Approval

- Change: jup-121-anotaciones-y-fuente
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-10-16
- Carril: standard
- Scope reviewed: proposal, design, specs, tasks
- Scope adjustment approved: Victor aprobó en el chat abrir un change pequeño nuevo, sin reabrir `jup-121-lectura-dashboard` (archivado), que resuelva en la PR #132 la anotación de la latencia pedida por Paris, el filtro por fuente del estado de casos y la regla `human`/`automatic` de la guía; la lectura del panel de robustez y el adaptador de JUP-071 quedan en su rama.
- Pendiente fuera de este gate: revalidación de Paris y revisión técnica de Alejandro.
