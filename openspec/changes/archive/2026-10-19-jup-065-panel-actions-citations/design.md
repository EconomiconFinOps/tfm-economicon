## Diseño aprobado — JUP-065

El humano aprobó el 19/10/2026 mostrar acciones, corregir fragmentación en origen
y abrir citas, con pruebas y documentación en una PR separada contra develop.

AnswerEvidence consume únicamente cadenas acotadas de response.next_actions.
La apertura utiliza un diálogo Radix con foco, Escape y cierre explícito, sin
HTML activo ni navegación a URLs suministradas por el modelo. Se conserva el
fragmento completo recuperado, no el documento entero, en la cita seleccionada
desde el contexto autorizado del servidor. Los mensajes antiguos muestran su
extracto y una advertencia; no se reescribe historia ni se consulta corpus vivo.

La respuesta fragmentada ya existía en metadata.response.answer. El renderizador
rechaza prosa que termina en conectores de continuación españoles/ingleses al
final o ante una cita, pero permite una cantidad/cálculo tipado a continuación.
Se unen segmentos de prosa adyacentes antes de comprobarlos. El streaming aplica
la misma comprobación antes de confirmar; los deltas siguen siendo provisionales.
Es un control sintáctico limitado, no un verificador semántico universal. El prompt
pide frases completas y next_actions cuando falta el dato; cambia su fingerprint.

No se rellenan huecos, atribuyen cifras a una cita ni modifican reglas financieras.
El visor no demuestra por sí mismo pertinencia semántica: el próximo ensayo debe
comprobar que el pasaje fundamenta la respuesta. /evidence de generaciones antiguas
no se reconstruye; la UI usa la cita congelada de la respuesta autorizada.

## Verificación

Regresiones fallando antes del cambio; pruebas de componente y rutas HTTP/SQLite,
persistencia, pertenencia de conversación, escaping, fallback histórico y streaming.
La suite CI añade Python 3.12/Linux y comprobaciones SQL existentes. Los dobles
de transporte verifican contrato, no aceptación de un modelo ni facturación real.
