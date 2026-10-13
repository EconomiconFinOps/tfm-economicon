# JUP-035 - Comprobacion local de compresion y reutilizacion

Fecha: 2026-10-11. Comprobacion del desarrollador autorizada por Paris, no
revision ni validacion humana independiente. Sin publicacion ni integracion.

## Entorno y alcance

Rama local `codex/JUP-035-e5-full-validation`, base
`ceb6520fd9b92c561c455cd8cbcd40aecf2c9f46`, con cambios sin commit descritos en
[la evidencia del prompt](jup-035-non-actionable-prompt-correction.md).
No representa una prueba del commit base sin modificaciones.

Stack Docker aislado `autonomo-e5-full`, navegador en 127.0.0.1:48236,
backend en 127.0.0.1:48235. Chat y resumen reales a traves de LiteLLM/OpenRouter;
embeddings mock y base vectorial vacia. No acredita recuperacion financiera real.
Se amplio CHAT_MAX_ACTIVE de 5 a 8 solo en este runtime: el resumen exige cinco
plazas libres ademas de su propia plaza. No se modifico el gateway compartido.

## Procedimiento y resultado

1. Crear una conversacion aislada y sembrar 12 pares sinteticos (24 mensajes),
   identificados como fixture, con 13857 tokens historicos. Conservar sus hashes.
2. Enviar desde el navegador una pregunta sobre los limites del dialogo.
   El primer intento obtuvo HTTP 429; el reintento automatico fue bloqueado por
   el contador local del ensayo (403), sin una segunda llamada al proveedor.
   Conservar la operacion fallida; no atribuir ese 403 al producto.
3. Reintentar manualmente una vez: respuesta completada y dos llamadas reales
   de resumen aceptadas. Se instalo la revision 2 del resumen.
4. Enviar una nueva pregunta desde el navegador y comprobar su entrada canonica,
   respuesta persistida, cobertura del resumen y hashes de los originales.

Conversacion: `6c0d1d74-ceb3-4220-a353-c325533b9f43`.
Operacion disparadora completada: `a645492a-ad89-4482-b138-6fb35381c353`.
Operacion consumidora: `3e4076cf-3cea-4a1d-9454-b339fd94901c`.
Artefacto usado: `a78d0317-27fb-480d-b99b-5d5bc4f03902`.

- La entrada consumidora registra `summary.used=true`, el mismo artifact_id
  persistido y un bloque `UNTRUSTED_DIALOGUE_SUMMARY` presente.
- Resultado completado en un intento: `no_data`, periodo null, evidence,
  metrics y recommendations vacios. La respuesta distingue expresamente el
  recuerdo del dialogo de la evidencia financiera y no inventa una conclusion.
- Los hashes de los 24 mensajes iniciales permanecen identicos. Hay 28 mensajes
  al finalizar: se conservan tambien las dos preguntas reales y sus respuestas.
- Cobertura final: 2 pares procesados, 8 pendientes y 4 recientes reservados.
  La cola queda `growth_deferred`, sin tarea activa. El resumen es parcial:
  no se afirma haber comprimido toda la conversacion ni que deba vaciarse la
  cola sin nuevas activaciones. El limite vigente es dos lotes por activacion.

## Limites observados

Dos textos de limitations del resumen terminan a mitad de palabra
(`recuperabl` y `declaraci`). El proveedor termina con finish_reason=stop y el
contrato los acepta. Es una limitacion de calidad pendiente de diagnostico, no
una prueba de truncamiento por el limite de salida ni motivo para afirmar que
el resumen es textualmente perfecto. La cita factual exacta y su negacion se
conservan; este fixture repetitivo no demuestra calidad en historiales diversos.

El ensayo acredita generacion, persistencia durante el recorrido y reutilizacion
del resumen. El reinicio comprobado previamente corresponde al historial y las
operaciones; no se reinicio de nuevo la base despues de generar este resumen.
No se probaron recreacion de contenedores, restauracion ni aislamiento cruzado
en esta fase. No se modifico codigo del producto durante esta comprobacion.

## Consumo y evidencia

Cinco llamadas enviadas al gateway en esta fase: cuatro HTTP 200 (dos chat y
dos resumen) y una HTTP 429. Las cuatro exitosas declaran 21484 tokens y
0.0133070475 USD. El 429 no declara coste: no se contabiliza como gratuito;
se conserva su reserva conservadora local de 0.012 EUR. No se mezclan monedas.

Recibos locales bajo `e5-full-validation-evidence`, junto al worktree:
`summary-prepared.json`, `summary-trigger-final.json`,
`summary-consumer-final.json`, `calls.json`, `summary-consumer-browser.png`.
El comprobador local fue `e5-full-runtime.py summary-watch summary-consumer-final`;
la comparacion estructurada de los hashes originales devolvio true.
Los recibos contienen datos sinteticos; no publicar archivos .env ni claves.

Conclusiones limitadas a este snapshot y escenario. La revision independiente,
integracion y aceptacion de JUP-035 siguen siendo hitos distintos.
