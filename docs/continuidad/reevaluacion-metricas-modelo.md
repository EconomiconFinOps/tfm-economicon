# Reevaluación de métricas tras el cambio de modelo — JUP-133

[Tarjeta](https://trello.com/c/Yv1ETc2G) · [Change](../../openspec/changes/archive/2026-10-22-jup-133-reevaluacion-metricas-modelo/) · [Informe antes y después](../validation/model-reevaluation-report.md) · [Evidencia](../evidence/JUP-133-validation.md).

Lucía lidera. Última actualización documental: 22/10/2026, rama feat/JUP-133-reevaluacion-metricas-modelo sobre develop con JUP-132 (ee84f791). Sin push ni PR todavía.

## Qué quedó hecho

- Inventario de qué medidas dependen del modelo ([inventario](../validation/model-dependence-inventory.md)) y lista de cifras de la memoria afectadas ([cifras](../validation/model-change-memory-figures.md)). La memoria no se copia al repositorio.
- Identidad del modelo en cada ejecución del dashboard (`generation_model_id`, proveedor, cuantización y huella de la configuración del gateway): dos ejecuciones con el mismo alias y distinto modelo no comparten serie. `gateway-config-hash` calcula la huella.
- Reejecución con DeepSeek V4.1 Flash: campaña ligera de JUP-071 (29 casos, una repetición, una revisora, provisional), coste de IA y banco de 28 preguntas de JUP-069 con el chat real. Gasto total ≈ 0,077 USD de 1,5 USD autorizados.
- Las ejecuciones nuevas están en el manifiesto versionado y cargadas en Grafana (12 ejecuciones y 647 resultados); los 18 paneles con SQL responden contra una pila real.

## Qué hay que saber para leerlo

- Las comparaciones con GLM-5.2 de JUP-071 no se pueden leer como mejora o empeoramiento: cambiaron a la vez el modelo, los recursos del chat (v3 a v4), el método de recogida y la muestra.
- El banco de 28 preguntas no tiene medición anterior con el chat real: es una referencia nueva, con 10 de 28 casos aprobados (más de la mitad de los fallos son del lector numérico automático).
- La latencia, la disponibilidad y los fallos técnicos son de la máquina local de Lucía; la lista de las que hay que repetir en la infraestructura definitiva está en el [plan](../validation/model-reevaluation-plan.md#sensibilidad-a-la-infraestructura-local).
- No se repitió la batería N3/N5 de 84 ejecuciones (necesita el ejecutor de la campaña B y revisión por requisito).

## Pendiente

- Capturas de pantalla de Grafana (hoy verificado por API).
- Revisión adversarial, aprobación de Lucía, archivo del change y PR único contra develop cuando ella lo pida; comentario en Trello cuando ella lo pida.
- Cifras de la hoja de hechos sin origen en el repositorio (latencia 22,5/40,8 s, coste 0,1806/0,0392 USD, campañas RAG A-D): indicar fuente antes de mantenerlas.
