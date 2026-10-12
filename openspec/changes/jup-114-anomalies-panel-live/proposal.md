JUP: JUP-114
Trello: https://trello.com/c/F492abeY

## Why

El change 1 (`jup-114-persisted-anomalies`, archivado) guarda episodios de anomalía en el backend, pero el panel `/anomalies` sigue enseñando cinco filas fijas de ejemplo y nadie puede detectar ni seguir una anomalía desde la aplicación. La tarjeta pide que el panel muestre las anomalías abiertas con criticidad e impacto reales del cliente activo, que el estado se pueda seguir y que haya datos de demostración reproducibles con varias criticidades. Además, los datos de demo de JUP-107 se diseñaron para comparar semanas y, con la regla diaria, dan cuatro episodios P2 poco creíbles, y el límite de 7 días por pulsación impide que la alerta de Compute de la demo aparezca en el panel.

## What Changes

- **Panel `/anomalies` conectado** a los episodios del cliente activo, sin datos fijos: resumen (impacto abierto por moneda, abiertas, Alta (P1) abiertas y «Ya no se observan» que filtra), tabla priorizada sin textos inventados, filtros de criticidad, estado y observación, etiquetas «Alta (P1)», «Media (P2)» y «Baja (P3)» con leyenda de umbrales, botón «Detectar ahora» con su resultado en un aviso dentro de la página, «Revisado hasta…» siempre visible, panel de detalle con las acciones de estado (cerrar pide motivo y avisa de que es definitivo), estados vacíos distintos para «nunca detectado» y «sin abiertas», aviso fijo cuando hay datos sintéticos y exportación CSV/PDF con las columnas nuevas.
- **Backend:** se quita el límite de 7 días por pulsación (la ejecución evalúa todos los días pendientes; en la primera, toda la historia evaluable) y la lista de episodios devuelve el último día evaluado y si los datos del cliente incluyen datos sintéticos. **BREAKING** para el contrato de la detección del change 1: desaparece `unevaluated_range`.
- **Datos de demo de JUP-107 rehechos con gasto diario:** un registro por servicio y día del 1 al 21 de septiembre de 2026, con los mismos totales semanales en los dos periodos de JUP-030 (su consulta y su guía siguen dando lo mismo, salvo recuentos) y una tercera semana; con una pulsación salen Alta (P1) Compute, Media (P2) Database y Baja (P3) Analytics que deja de observarse, y Tools, Backup y Networking enseñan por qué la regla no salta. `remove` borra también los episodios y la marca de agua del cliente de demo (`RF-114-007`).
- **Demo de 3 minutos:** paso nuevo de Anomalías tras el aislamiento entre clientes, D7 (etiquetas) pasa a opcional y el paso de límites se acorta; guía de anomalías, preguntas, README y receta de navegador actualizados.

Fuera de alcance: ejecución periódica y avisos (change 3), la explicación con el agente (JUP-038), permisos por rol, histórico de cambios de estado y otras dimensiones.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `anomalies-panel`: de lista fija de demostración a panel conectado a los episodios del cliente activo, con detección, detalle, cambio de estado, estados vacíos, origen sintético y exportación.
- `cost-anomaly-episodes`: la ejecución evalúa todos los días pendientes sin límite de 7; la lista devuelve el último día evaluado y si hay datos sintéticos.
- `synthetic-anomaly-data`: conjunto con gasto diario y tercera semana, esperados de episodios, retirada que limpia episodios y marca de agua, y guía que ya no dice que el panel use datos fijos.
- `synthetic-cost-demo`: la ruta de 3 minutos incluye el panel de anomalías y D7 pasa a opcional.

## Impact

Frontend (`AnomaliesPanel`, cliente y contrato en `services/`, quitar `data/demo/anomaliesPanel.ts`, pruebas), backend (`detection_window`, lectura de la lista, esquemas, pruebas), `scripts/synthetic_anomalies.py` y su suite, `docs/demo/JUP-107/` (esperados, guía de anomalías, guion, preguntas, README, receta de navegador), `docs/api/anomaly-episodes.md`, ADR-0019 (límite de 7 días), hallazgos `RF-114-006` y `RF-114-007` y continuidad. La batería de cierre incluye backend, processor, frontend y scripts.
