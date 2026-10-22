# Medición del arreglo de los cortes de respuesta del chat

Fecha: 22/10/2026. Tarjeta JUP-135. Código medido: commit `445a028e`, hoy en la rama `fix/JUP-135-cortes-respuesta-chat` (se subió antes como `fix/chat-respuesta-cortada`), con el chat real, `tenant-growth` y `tenant-core`. Una repetición por batería. Gasto aproximado: 0,27 USD de OpenRouter.

## Problema

Con preguntas sobre las cifras de pantalla, el servidor rechazaba la respuesta entera ante una sola regla incumplida y la operación terminaba `failed` aunque el modelo hubiera respondido bien. Si fallaba la primera pregunta de una conversación nueva, el botón de enviar quedaba apagado hasta reabrir la conversación desde el historial.

## Cambios

- El procesador reintenta una salida rechazada (`invalid_response`) dentro de los cuatro intentos existentes. El primer intento sigue en temperatura 0 y los reintentos usan 0,2, 0,4 y 0,6.
- Un segmento de interpretación vacío o en blanco se omite; si no queda texto, la respuesta se sigue rechazando.
- Una métrica financiera que no coincide con el registro autorizado se omite y se añade una limitación visible; el resto de la respuesta se conserva.
- La interfaz carga la memoria de la conversación al terminar una operación en `failed` o `cancelled`.

## Resultados

| Batería | Antes | Después |
| --- | --- | --- |
| Pantalla financiera, 14 preguntas × 4 repeticiones | 21 de 56 fallidas (37,5 %); 88 intentos; 40,4 s de media | 1 de 56 fallidas (1,8 %); 86 intentos; 37,4 s de media |
| Robustez JUP-071, 29 casos | 4 rechazadas por el validador y reintentadas a mano; 7 pass, 17 fail, 5 sin medir | 1 fallida sin reintento manual; 15 pass, 10 fail, 4 bloqueados |
| Banco JUP-069, 28 preguntas | 1 fallida, reintentada a mano; 10 pass, 18 fail | 1 fallida (`JUP-069-005`), 39 intentos; 13 pass, 14 fail, 1 bloqueado |

Los «antes» de JUP-071 y JUP-069 proceden de la campaña de JUP-133. La batería de pantalla financiera es propia y se midió igual en las dos fases.

## Banco de JUP-069: métricas oficiales

Puntuado con `tools/assistant-eval.py score --provisional`, a partir de las operaciones ya hechas (sin gasto nuevo), con la distancia real de cada fragmento guardada en el manifiesto de la operación y los juicios de una persona. Informe en `docs/evidence/JUP-069-fix-bank28-report.json` y `.md`.

| Métrica | Antes (JUP-133) | Después |
| --- | --- | --- |
| Casos pass / fail / bloqueados | 10 / 18 / 0 | 13 / 14 / 1 |
| ACC-1 casos con resultado pass | 6 de 20 | 7 de 19 |
| ACC-2 comprobaciones objetivas | 31 de 51 (60,8 %) | 28 de 46 (60,9 %) |
| ACC-2 comprobaciones juzgadas | 25 de 30 (83,3 %) | 26 de 28 (92,9 %) |
| ACC-3 clarify / abstain | 2 de 6 / 2 de 2 | 4 de 6 / 2 de 2 |
| GRD-1 y GRD-3 citas y referencias | 22 de 22 | 17 de 17 |
| GRD-2 cifras sin rastro | 1 | 0 |
| STR-1 esquema | 28 de 28 | 27 de 27 |
| AVL-1 disponibilidad | 28 de 28 | 28 de 28 |
| LAT-1 mediana de generación | 20,8 s | 19,8 s |
| LAT-2 percentil 95 total | 41,3 s | 42,4 s |

Límites de esta comparación:

- **REL-1 a REL-4 no son comparables.** En JUP-133 la recuperación capturada solo cubría el contexto inicial (12 de 20 casos de respuesta salían «vacíos»); aquí se usa la recuperación real de cada operación. La subida de REL-1 (8 de 20 a 19 de 19) y la bajada de REL-3 (12 de 20 a 0 de 19) vienen del método de captura, no del arreglo.
- **El caso fallido** (`JUP-069-005`) se registra como bloqueado con categoría `invalid_response` en la etapa de embedding: el evaluador no admite un fallo de la etapa de generación en un caso bloqueado. En realidad falló la generación tras cuatro intentos.
- **Los juicios** son de una sola persona, sin segunda revisora (ocho casos críticos con un único decisor, listados en el informe), y no coinciden en número de puntos con los de JUP-133.
- Una sola repetición y una sola ejecución previa: las diferencias de uno o dos casos no son concluyentes.

## Verificación en navegador

Con Playwright sobre Edge y simulando solo la respuesta de la primera pregunta con un fallo: en `develop` el botón de enviar y el de reintento quedan apagados y no se pide el resumen de memoria; en la rama ambos se habilitan tras una petición de resumen.

## Límites

- Una repetición por batería: las diferencias pequeñas (JUP-071, 4 a 1) no son concluyentes; la de pantalla financiera (21 a 1) sí es grande.
- La calidad con rúbrica de JUP-069 y JUP-071 la juzgó una persona sobre las respuestas nuevas, sin segunda revisora. No es comparable punto a punto con los juicios de JUP-133: el número de puntos y los criterios automáticos difieren.
- Los casos `JUP-069-003`, `JUP-069-010`, `JUP-069-026` y `JUP-071-014` quedan bloqueados en el informe de JUP-071: la recuperación reconstruida no coincide con el hash del servidor en los tres primeros y el último terminó `failed`.
- La batería de pantalla financiera no está en el dashboard: no tiene adaptador. Sus datos están solo en esta nota.
- Siguen apareciendo y se reintentan, sin evitarse: el corte por longitud (`incomplete`), el cierre de conexión (`eof`) y las reglas de prosa de clasificación y de unidades de las expresiones.
- Sin resolver: las frases con huecos donde debería ir una cifra y que el asistente no pida aclaración cuando faltan datos.

## Decisión registrada

Decisión de Lucia (22/10/2026), a revisar más adelante si se quiere revertir: (1) `invalid_response` pasa de error permanente a reintentable; (2) una métrica no verificada se omite con limitación visible en lugar de rechazar la respuesta; (3) los reintentos usan temperatura mayor que 0.

## Evidencia versionada

- `docs/evidence/JUP-071-fix-r1-report.json` y `.md`: informe de puntuación de robustez.
- `docs/evidence/JUP-071-fix-r1-rows.json` y `docs/evidence/JUP-069-fix-bank28-report.json`: datos para el dashboard, añadidos a `docs/validation/evaluation-runs.json`. Cuando se integre la identidad del modelo en el manifiesto (PR #150), estas dos entradas deben llevar la misma `model_identity` que las de JUP-133.
