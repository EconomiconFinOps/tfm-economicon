# Diseño JUP-038

El servicio consume `AnomalyEvaluation` v1 de JUP-030, fuente
`billing_summary_v2`. Valida estructura, selección, periodos, moneda,
coherencia de estados y cifras antes de redactar una plantilla determinista.
Las comprobaciones aritméticas usan Decimal; no convierten el porcentaje
redondeado en una decisión. No hay llamada a un modelo ni diagnóstico causal.

El cliente envía definición, `anomaly_id` y `evidence_id`. El ID de anomalía
puede mantenerse tras una ingesta; el segundo identifica la fotografía.
El adaptador reevalúa para el tenant autorizado y rechaza evidencia cambiada
con 409. La ausencia de alerta devuelve 404, nunca una explicación con ceros.

La nueva ruta de conversación comprueba sesión, membresía y propiedad antes
de consultar costes. Solo escribe mensajes después de validar la evidencia.
La respuesta mantiene `AssistantReply` y conserva la fotografía en
`metadata.anomaly_explanation`, sin introducir citas documentales ficticias.
La recuperación normal del historial preserva esa evidencia anterior.

JUP-030 aún no está en la base: importación diferida de su definición y
evaluador, sin fallback de demostración. 503 es el estado honesto cuando
falta la dependencia. El contrato de integración para JUP-035/036 está en
`docs/contracts/JUP-038-anomaly-explanations.md`. La combinación real debe
revalidarse antes de marcar la contribución lista.

No se rediseña el detector ni la persistencia transaccional del chat. Dos
inserciones conservan el comportamiento existente: un fallo de escritura
entre ambas puede dejar la solicitud sin respuesta. No hay reintento automático.
