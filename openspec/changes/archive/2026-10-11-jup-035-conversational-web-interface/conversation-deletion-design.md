# JUP-035 - eliminacion individual de conversaciones

Diseno aprobado explicitamente en chat autonomo el 11/10/2026. Hard delete sin
migracion. Modal exacto: "¿Estás seguro? No podrás recuperar esta conversación",
botones "Sí" y "No". No se exige nombre en la confirmacion.

## Contrato

- DELETE /assistant/conversations/{id}: 204; inexistente/ajeno mismo 404.
- ChatRepository._transaction: SERIALIZABLE y bloqueo de padre por id/tenant/user,
  compartido con admision de operaciones, reintentos y compresion. No check/delete
  separados. Cualquier error hace rollback completo.
- Rechazar operaciones active/waiting/paused. Rechazar controles de compresion
  pending/running/reconciling; failed solo si job y owner ausentes. Un lease
  vencido no acredita settlement. No cancelar trabajos para permitir el borrado.
- Comprobar propietarios de operaciones/mensajes legacy; anomalia aborta.
  Eliminar operaciones terminales, mensajes legacy propios (author nullable para
  assistant) y padre. dialogue_history/summary/compaction desaparecen con el padre.
  No tocar corpus RAG, ingestas, gateway, processor ni otras conversaciones.
- CORS admite DELETE adicional, sin ampliar origins/headers/credentials.
- Papelera junto al lapiz solo en historial. Modal Radix accesible, foco inicial
  en No, Escape/cancelacion sin escritura, pendiente sin doble envio, error visible.
- Confirmacion 204 retira celda/historial/solicitudes, cancela lectores y timers
  propios y conserva una marca efimera que impide resurreccion por respuestas
  anteriores. Si aun es seleccionada, crear borrador nuevo; si cambio, no seleccionarla.
- Durante DELETE se bloquea envio local en esa conversacion. Estado SQL es la
  autoridad ante trabajo en otra pestaña. 409 explica respuesta/compresion pendiente.

## Rutas y comprobaciones

Producto: apps/backend/app/api/routes/assistant.py, app/db/chat_repository.py y
app/main.py; apps/frontend/src/components/chat/ChatPanel.tsx y useChatSession.ts.
Pruebas: backend/tests/test_conversation_deletion_jup035.py, tests/test_cors.py;
frontend/tests/chat-deletion-jup035.test.tsx y regresiones existentes panel/titulos.
Documentacion: este diseno, spec y tasks de la misma change.

Secuencia autorizada: Red focal, Green producto, mutacion focal de barrera SQL;
typechecks/build offline. Fixtures desechables, sin datos runtime ni llamadas LLM.
No se afirma aceptacion humana ni validacion real Cockroach/browser por pruebas SQLite.

## Resultado local

- Red: 19 casos DELETE inexistente (405), 1 preflight DELETE rechazado (400),
  5 casos frontend sin accion/editor de eliminacion.
- Green: 43 backend (19 borrado + 9 nombres + 15 preflight), 27 frontend
  (5 borrado + 6 nombres + 16 panel). Ambos typechecks y build frontend pasan.
- Primer typecheck de pruebas detecto opcion exact no admitida por ByRoleOptions;
  se retiro sin cambiar comparacion exacta por nombre ni aserciones. Se repitieron
  los 5 casos de borrado, ambos typechecks y build satisfactoriamente.
- Mutacion backend omite lectura de compresion: 5 casos detectan 204 en vez de409.
  Mutacion frontend retira tombstone: detecta seleccion resucitada old en vez de draft.
  Ambas en copias temporales, W readonly, SHA256 original sin cambios.
- Evidencia externa: restart-20261011/deletion-*.log y deletion-delivery.md.
  Backend/Frontend requieren despliegue del padre; sin migraciones, cambios de env,
  processor, prompt, dependencias, Git, datos reales ni llamadas LLM.
- Regresion adicional expresamente solicitada por cambios readers/timers/json:
  chat-panel + chat-summary + chat-titles existentes, 37/37 PASS; sin tests nuevos
  ni cambios de producto. Log deletion-frontend-regression.log. Con los 5 de
  borrado hay 42 casos frontend distintos comprobados.
