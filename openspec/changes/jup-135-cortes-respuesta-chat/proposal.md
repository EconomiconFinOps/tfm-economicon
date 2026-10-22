JUP: JUP-135
Trello: https://trello.com/c/RCR1nFkj

# Cortes de respuesta del chat

## Why
Con preguntas sobre las cifras de pantalla, el servidor rechaza la respuesta entera ante una sola regla incumplida y la operacion termina `failed` aunque el modelo haya respondido bien: 21 de 56 operaciones en una bateria de 14 preguntas por 4 repeticiones. Si falla la primera pregunta de una conversacion nueva, el envio queda bloqueado porque su memoria nunca se carga.

## What Changes
- Los reintentos dejan de repetir la misma generacion: temperatura 0 en el primer intento y creciente en los reintentos; el rechazo `invalid_response` del procesador se reintenta dentro de los cuatro intentos.
- Un segmento de interpretacion vacio se omite en procesador y backend (modulo compartido identico).
- Una metrica financiera no verificada se omite con una limitacion visible en lugar de rechazar la respuesta.
- La interfaz carga la memoria al terminar una operacion en `failed` o `cancelled`.

## Impact
Cambia dos requisitos y anade dos de `conversational-web-interface`. Sin cambio de `FinOpsResponse`, esquema publico, modelo, routing, despliegue ni migraciones. Coste: hasta tres llamadas mas al modelo en los intentos fallidos.

## Decision
Decision de Lucia (22/10/2026), a revisar mas adelante si se quiere revertir: `invalid_response` pasa de error permanente a reintentable, una cifra no verificada se omite con limitacion visible y los reintentos usan temperatura mayor que 0.
