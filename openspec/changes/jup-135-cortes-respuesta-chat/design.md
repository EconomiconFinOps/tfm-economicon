## Context
Causas vistas en los diagnosticos: `financial_metric_unverified` (backend), `invalid_inference_text`, `expression_incompatible_units`, `narrative_evidence_required`, `non_actionable_with_metrics_or_recommendations`, `classification_unverified_prose`, corte por longitud (el modelo llega al tope de 2.200 tokens) y cierre de conexion. Con temperatura 0 el reintento repetia la misma peticion y la misma salida desbocada.

## Decisions
- Temperatura creciente solo en reintentos (0,2 por intento, maximo 0,6) para conservar el comportamiento determinista del primer intento.
- Solo el rechazo `invalid_response` del procesador pasa a reintentable. Los rechazos del backend (citas, calculos) siguen siendo permanentes porque pruebas existentes exigen que no se reintenten.
- La unica reparacion del candidato es omitir una metrica financiera no verificada con aviso visible; el texto con cifras lo genera el servidor, asi que ninguna cifra no verificada llega a la respuesta.
- `chat_segments.py` es un modulo compartido y debe seguir siendo identico en backend y procesador.
- La interfaz carga la memoria cuando una operacion termina `failed` o `cancelled`, porque solo se cargaba al completarse una respuesta.

## Risks
Hasta tres llamadas adicionales al modelo en los fallos; la temperatura de los reintentos puede cambiar el estilo de esas respuestas. Una repeticion por bateria: las diferencias pequenas no son concluyentes.

## Evidence
`docs/evidence/chat-cortes-de-respuesta-medicion.md`, `docs/continuidad/cortes-respuesta-chat.md` e informes `JUP-071-fix-r1-*` y `JUP-069-fix-bank28-report.*` en `docs/evidence/`.
