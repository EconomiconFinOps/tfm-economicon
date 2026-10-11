# Chat conversacional

Verificacion documental: 2026-10-11. Identificador: JUP-035.
La continuidad no sustituye alcance y roles de Trello ni las reviews humanas.

## Referencias

- [Cambio OpenSpec](../../openspec/changes/jup-035-conversational-web-interface/proposal.md).
- [Integracion con Compose](../../openspec/changes/jup-035-conversational-web-interface/compose-chat-design.md).
- [Correccion del plazo de compresion](../../openspec/changes/jup-035-conversational-web-interface/summary-timeout-correction.md).
- [Arranque y configuracion](../../README.md).
- Commit de entrega previo a reconciliar: `01bfb7ba1361467b71301aeb08d9a6942c5e76cd`.
- Base incorporada en la reconciliacion local: develop `3b8e952`.

## Entrega y comprobaciones anteriores a la reconciliacion

Los servicios empaquetan locks, prompts y tokenizer. El migrador backend termina
antes del arranque en modo verify; processor conserva sus propias migraciones.
El transporte privado usa red interna y HMAC. Los mocks son explicitos para
desarrollo; IA usa las claves restringidas del gateway, sin fallback a mock.

El chat muestra fuentes documentales compactas, historial de conversaciones,
renombrado y borrado individual. No muestra la memoria interna ni las solicitudes
guardadas; los datos operativos necesarios se conservan.

El plazo de compresion es configurable entre 30 y 300 segundos, 180 por defecto
en ambos servicios. Reserva cinco segundos para validar y guardar. La lease
dura el plazo mas 15 segundos. No se modifica el timeout del chat normal.

Antes de incorporar esta base se comprobaron Compose mock e IA en entornos
aislados: streaming, persistencia tras reiniciar y bloqueo de envio durante
compresion. Una recuperacion publica real produjo un resumen validado y
persistente tras reinicio; los 14 mensajes originales permanecieron identicos.
El fallo previo de compresion se conserva como antecedente: llamada de 146.203
segundos frente al antiguo plazo local de 30, sin perdida de mensajes.

## Limites y reconciliacion

La recuperacion real exitosa duro 10.135 segundos: no prueba por si sola un caso
real superior a 30 segundos ni que ampliar el plazo causara ese exito. No se
envio otra pregunta para comprobar consumo del resumen; tampoco se certifica
exactitud financiera o RAG de un corpus poblado con estos fixtures sinteticos.

La reconciliacion preserva los cambios de ownership, las evidencias financieras
y los controles de instalacion de dependencias incorporados por develop. Sus
pruebas locales no se presentan como una repeticion de las llamadas reales.
CI remota, publicacion, archivado y cierre global siguen su procedimiento y
autorizaciones especificas; no se han acreditado por este hito local.
