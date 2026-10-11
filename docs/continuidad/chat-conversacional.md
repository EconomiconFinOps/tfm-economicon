## Estado vigente — archivo autorizado 11/10/2026

OpenSpec archivado por autorización expresa de Paris. Rama codex/JUP-035-e5-full-validation reconciliada con develop 3b8e952, HEAD previo al archivo 8886494. La compresión y el consumo por una respuesta posterior ya tienen evidencia histórica satisfactoria; no quedan pendientes globales por no repetirse en el último ensayo de Compose. Véase [entrega, evidencias y límites](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/archive-delivery.md). Los cortes anteriores se conservan como historia; CI remota, publicación y gates humanos no se declaran cumplidos.

# Chat conversacional

Verificacion documental: 2026-10-11. Identificador: JUP-035.
La continuidad no sustituye alcance y roles de Trello ni las reviews humanas.

## Referencias

- [Correcciones locales de CI](../evidence/jup-035-ci-corrections.md): tokenizer
  declarado, prueba portable, plugin de lint compatible, fixtures HMAC y
  recuperacion de operaciones desde conversaciones sin mostrar solicitudes;
  confirmacion remota pendiente.
- [Cambio OpenSpec](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/proposal.md).
- [Integracion con Compose](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/compose-chat-design.md).
- [Correccion del plazo de compresion](../../openspec/changes/archive/2026-10-11-jup-035-conversational-web-interface/summary-timeout-correction.md).
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

## Correcciones CI de fixtures Python (2026-10-11)

Se adaptan las pruebas al checkout portable, al Compose principal y su overlay
IA, al escritor atomico append_pair y al plazo de resumen configurado. No cambia
el producto ni se reducen las aserciones funcionales. Processor: 127 PASS;
backend: 212 PASS / 3 SKIP de SQL nativo no configurado. Revision interna
incremental: REVIEW_PASS, con hashes tecnicos sin cambios tras su retorno.
La evidencia [de correcciones CI](../evidence/jup-035-ci-corrections.md) conserva
los fallos intermedios y las omisiones SQL nativas; la confirmacion remota sigue
a cargo del PM.
