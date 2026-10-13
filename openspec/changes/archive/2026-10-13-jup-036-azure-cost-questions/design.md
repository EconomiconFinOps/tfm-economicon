# JUP-036 — Consultas de gasto Azure

Reutilizar fetch_billing_summary, agregando cuenta y filtros ligados como parámetros SQL.
Comprobar solapamientos antes del filtro de dimensión: dos fuentes en una suscripción/día
no se vuelven válidas porque sus servicios difieran. Filtrar suscripción desde completed.
Validar el periodo y la selección antes de escribir mensajes. Resolver el gasto antes de
persistir la pareja de mensajes; sin embeddings, RAG ni red para esta ruta.

El modo explícito elimina la necesidad de adivinar «esta suscripción». Sin selección,
el chat mantiene su contrato documental. Fechas omitidas significan el mes UTC actual.
Una selección sin filas devuelve no_data, nunca gasto cero; cero y créditos reales se conservan.

Evidence ID SHA-256 del tenant, selección, resultado y procedencia. Incluir IDs de ingesta,
primer/último día observado y número de días con datos, sin afirmar cobertura completa
ni frescura garantizada. El usuario ve el periodo, ámbito, moneda, registros y advertencias.
No implementar el registro general query_costs de JUP-024 en este incremento.
