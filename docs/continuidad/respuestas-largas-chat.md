# Respuestas largas del chat: rótulos, fuentes, cifras y cortes

Rama `fix/chat-respuestas-largas-inc01-04`, creada desde develop `0edd11ef`. Tarjeta de Trello pendiente de asignar: al tenerla, renombrar la rama con su identificador `JUP-XXX`. Es continuación de [cortes de respuesta del chat](cortes-respuesta-chat.md) (JUP-135).

Actualización documental: 25/10/2026. Las medidas son de una sola persona y de una sola ronda por pregunta, con el chat real (gateway LiteLLM, DeepInfra FP8) y los datos de demo de `tenant-growth`.

## Problema

Cuatro incidencias reportadas en la salida del asistente:

- INC-01: cada segmento de interpretación empezaba por «Interpretación:».
- INC-02: frases con huecos donde debía ir una cifra («el importe de julio es  y el de agosto es .») o cálculos como `(2026 − 2026) = 0`.
- INC-03: ante respuestas largas se repetía «Esperando capacidad disponible → Esperando respuesta del LLM → Recibiendo respuesta → Esperando al proveedor…» hasta «No se pudo completar la respuesta».
- INC-04: las respuestas largas alternaban «Interpretación» y «Fuente» en parejas.

## Causas encontradas

- INC-01 e INC-04: el render del servidor (`chat_segments.py`) anteponía el rótulo a cada `inference` y emitía cada `documentary` como un bloque propio en el sitio donde el modelo lo colocaba. El prompt no impone la alternancia, pero la favorece.
- INC-02: el catálogo de cantidades que el modelo puede citar (`context_quantities`) se construía solo con los números del texto de la pregunta. En «¿cuánto ha subido el gasto en agosto de 2026?» la única opción era `2026`, así que el modelo dejaba el hueco o calculaba con el año. Las cifras de la captura de pantalla nunca entraban en el catálogo. Se comprobó con la salida cruda del modelo.
- INC-03: el proveedor corta el flujo en streaming a mitad de respuesta cuando la petición lleva el esquema JSON estricto. Se reprodujo fuera de la aplicación repitiendo la petición final real contra el gateway: 13 cortes de 30 con el esquema estricto y 0 de 15 con JSON libre. Quitar `maxLength` (3 de 15) o `stream_options` (4 de 15) no lo evita, y desactivar `strict` hace que el gateway responda HTTP 500. Los cortes llegan con 1,2 a 2,3 KB ya recibidos y sin motivo de fin. El reintento de JUP-135 repite entonces el borrador y la respuesta final hasta agotar los cuatro intentos.

## Cambio

- La interpretación se emite sin rótulo y todos los bloques «Fuente:» se listan juntos después de la explicación. El cambio es idéntico en el render final y en el parser de streaming, para que el texto parcial coincida con el final.
- Las cifras de la captura (totales, grupos y series) entran en el catálogo de cantidades con procedencia `screen`, distinta de `user` y de `corpus`: el modelo puede citarlas y operar con ellas, pero no activan las reglas de escenario de usuario ni dan autoridad financiera.
- Pruebas actualizadas donde fijaban el rótulo y dos pruebas nuevas (fuentes al final en streaming y en el texto final; cifras de pantalla como cantidades citables).
- Sin cambios en los hashes del manifiesto de prompt: `chat_segments.py` y `chat_expressions.py` no forman parte de ellos.

## Resultado

| Incidencia | Antes (develop) | Después |
| --- | --- | --- |
| INC-01 | 8 de 8 respuestas con «Interpretación:» | 0 de 8 |
| INC-04 | 5 «Interpretación» y 4 «Fuente» alternados en la pregunta del etiquetado | Prosa seguida y fuentes agrupadas al final |
| INC-02 | Huecos y `(2026 − 2026) = 0` | `(21300.1 EUR − 19800 EUR) = 1500.1 EUR` y 7,58 % de subida en analytics |
| INC-03 | 5 cortes de flujo en 12 llamadas, una pregunta con 4 intentos | Sin cambios: causa demostrada, pendiente de decisión |

Pruebas de chat con las mismas dependencias instaladas: sin fallos exclusivos de esta rama frente a develop, en procesador y en backend (los fallos restantes también están en develop).

## Límites y siguiente acción

- INC-03 sigue abierto. Opciones: documentarlo como fallo del proveedor y abrir una tarjeta de seguimiento; probar JSON libre en los reintentos (elimina los cortes pero el modelo deja de ver el esquema y habría que medir cuántas respuestas validan); subir el máximo de intentos de cuatro a seis. Reintentar la respuesta final dentro del mismo intento no es posible sin cambiar el contrato de uso de dos llamadas.
- El backend solo reintenta los estados 429, 502, 503 y 504. Una ráfaga de HTTP 500 del proveedor hizo fallar cuatro preguntas en 2,6 s sin reintento.
- Con datos de pantalla las cifras aparecen en bloques «Dato aportado» propios, y en una ejecución el modelo sumó dos meses como si fuera un total. Es comportamiento del modelo y del bloque de cantidad, no de este cambio.
- Quitar el rótulo hace inexacta la frase del prompt que dice que la paráfrasis «se rotula como interpretación». No se ha tocado para no alterar el manifiesto.
- Abrir la PR contra `develop` y pedir revisión y validación a otras personas.
