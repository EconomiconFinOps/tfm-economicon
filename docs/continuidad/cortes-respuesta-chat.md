# Cortes de respuesta del chat

Tarjeta [JUP-135](https://trello.com/c/RCR1nFkj), rama `fix/JUP-135-cortes-respuesta-chat` y cambio de OpenSpec `jup-135-cortes-respuesta-chat`. Evidencia completa en [la medición](../evidence/chat-cortes-de-respuesta-medicion.md). El primer commit medido, `445a028e`, se subió antes con el nombre provisional `fix/chat-respuesta-cortada`; el contenido es el mismo.

Actualización documental: 22/10/2026, sobre develop `4567e8e7`.

## Problema

Con preguntas sobre las cifras de pantalla, el servidor rechazaba la respuesta entera ante una sola regla incumplida y la operación terminaba `failed`, aunque el modelo hubiera respondido bien. Si fallaba la primera pregunta de una conversación nueva, el botón de enviar quedaba apagado hasta reabrirla desde el historial: la memoria de la conversación solo se cargaba al completarse una respuesta.

Causas vistas en los diagnósticos del procesador y del backend: `financial_metric_unverified`, `invalid_inference_text`, `expression_incompatible_units`, `narrative_evidence_required`, `non_actionable_with_metrics_or_recommendations`, `classification_unverified_prose`, corte por longitud (`incomplete`, el modelo llega justo al tope de 2.200 tokens) y cierre de conexión (`eof`).

## Cambio

- Reintentos con temperatura creciente (0, 0,2, 0,4, 0,6) y reintento de `invalid_response` del procesador dentro de los cuatro intentos existentes.
- Segmento de interpretación vacío omitido, en el procesador y en su copia idéntica del backend.
- Métrica financiera no verificada omitida con una limitación visible.
- La interfaz carga la memoria al terminar en `failed` o `cancelled`.

Decisión de Lucia del 22/10/2026, sin consenso previo del equipo y a revisar más adelante si se quiere revertirla: reclasificar `invalid_response` como reintentable, repararla omitiendo la cifra y reintentar con temperatura mayor que 0. Los cambios de spec están en el cambio de OpenSpec; el borrador original se conserva al final de este documento.

## Resultado

| Batería | Antes | Después |
| --- | --- | --- |
| Pantalla financiera (56) | 21 fallidas | 1 fallida |
| Robustez JUP-071 (29) | 7 pass, 17 fail, 5 sin medir | 15 pass, 10 fail, 4 bloqueados |
| Banco JUP-069 (28) | 10 pass, 18 fail | 13 pass, 14 fail, 1 bloqueado |

Una repetición por batería y juicios de una sola persona. Las métricas de recuperación del banco no son comparables con las de JUP-133 porque el método de captura difiere.

## Límites y siguiente acción

- Sin resolver: las frases con huecos donde debería ir una cifra y que el asistente no pida aclaración cuando faltan datos.
- Siguen apareciendo, y se reintentan, el corte por longitud, el cierre de conexión y dos reglas de validación de prosa y de unidades.
- Abrir la PR contra `develop` y pedir revisión y validación de otras personas.
- Cuando la identidad del modelo del manifiesto (PR #150) esté integrada, añadir al manifiesto `docs/validation/evaluation-runs.json` las entradas de `JUP-071-fix-r1-rows.json` y `JUP-069-fix-bank28-report.json` con la misma `model_identity` que las de JUP-133, y actualizar los números fijados en las pruebas del dashboard (9 ejecuciones y 444 resultados).

## Borrador de spec

Ya trasladado a `openspec/changes/jup-135-cortes-respuesta-chat/specs/conversational-web-interface/spec.md`; este texto queda como referencia.

### Cambios de requisitos propuestos (capacidad `conversational-web-interface`)

#### Requisito: Tres reintentos funcionales adicionales

(Se añade al final del párrafo existente.) Una respuesta del modelo que el procesador rechaza con la categoría `invalid_response` SHALL tratarse como fallo reintentable dentro del mismo máximo de cuatro intentos y el mismo presupuesto de tiempo. Los rechazos del propio backend (citas sin resolver, `ResponseValidationError`, `CalculationError`), un flujo mal formado (`invalid_stream`) y los errores de configuración SHALL seguir siendo permanentes. El primer intento SHALL decodificar con temperatura 0; los reintentos SHALL usar temperatura creciente acotada (0,2 por intento adicional, máximo 0,6) para no reproducir la misma salida degenerada.

##### Escenario: Salida rechazada por el validador

- **WHEN** el intento 1 termina con una respuesta que el validador rechaza
- **THEN** se programa otro intento con la misma pregunta mientras queden intentos y presupuesto, y la operación solo termina `failed` tras agotarlos

##### Escenario: Reintento tras salida desbocada

- **WHEN** un intento termina `incomplete` por agotar el tope de salida
- **THEN** el reintento SHALL usar temperatura mayor que 0

#### Requisito: Instruccion explicita para respuestas no accionables

(Sustituye la frase final del escenario «Pantalla sin costes disponibles».) Una métrica financiera cuyo nombre, valor y unidad no coincidan con una métrica del registro autorizado SHALL omitirse de `metrics` y SHALL añadirse a `limitations` el aviso «Se omitió una cifra financiera que no pudo verificarse con la consulta de costes.»; el resto de la respuesta se conserva. Las referencias a evidencia inexistentes, los estados no accionables con métricas o recomendaciones y las divergencias de periodo o suscripciones SHALL seguir rechazando la respuesta.

##### Escenario: Cifra añadida por el modelo

- **WHEN** el modelo devuelve una métrica que no figura en el registro autorizado de la consulta de costes
- **THEN** la respuesta se persiste sin esa métrica y con la limitación visible; nunca se muestra la cifra no verificada

### Requisitos nuevos propuestos

#### Requisito: Segmentos de interpretación vacíos

Un segmento `inference` vacío o formado solo por espacios SHALL omitirse sin aportar texto; si tras omitirlo no queda texto renderizado, la respuesta SHALL seguir rechazándose como texto vacío. Un segmento `inference` que no sea cadena SHALL seguir rechazándose.

#### Requisito: Envío tras un fallo sin respuesta

Cuando una operación termina `failed` o `cancelled`, la interfaz SHALL cargar el estado de memoria de la conversación para que el envío se desbloquee si la memoria no está comprimiendo ni bloqueada, también cuando esa operación fue la primera pregunta de una conversación nueva.

##### Escenario: Primera pregunta fallida

- **WHEN** la primera pregunta de una conversación recién creada termina `failed`
- **THEN** la interfaz solicita el resumen de memoria y, si la cola está ociosa, habilita el envío sin reabrir la conversación desde el historial
