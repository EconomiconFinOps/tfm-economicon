# JUP-035 - nombres de conversaciones

Estado: delta implementado con autorizacion explicita del usuario en chat autonomo
el 11/10/2026, incluyendo PATCH sin migracion y secuencia Red/Green/mutacion.
Comprobaciones locales descritas al final; no equivale a aceptacion humana.
Base inspeccionada: a0a77d4911f3abdbf604298873e057dd3ed3cace. Proceso local leido:
AGENTS.md y CONTRIBUTING.md, version 2026-09-30 (JUP-100).

## Contratos inspeccionados antes del delta

POST /assistant/conversations acepta ConversationCreateRequest.title no vacio.
ConversationRecord ya expone title. La tabla conversations contiene title y
updated_at; lista y detalle filtran tenant_id y user_id. No existe PATCH/rename.
ChatSession crea al primer envio con titulo fijo Nueva conversacion. chatJson
admite metodo y cuerpo arbitrarios, con autenticacion y tenant existentes.

## Delta autorizado e implementado

- Nombre automatico: solo al crear desde el primer envio del ChatPanel, colapsar
  espacios/saltos/tabulaciones, recortar extremos y tomar hasta 60 puntos de codigo
  Unicode, sin puntos suspensivos. La pregunta original no cambia. Sin LLM.
- No renombrar automaticamente conversaciones existentes ni reconstruir titulos
  del historial. No ejecutar actualizaciones de titulo al terminar una respuesta,
  reintentar, recuperar SSE o comprimir. Esto preserva nombres manuales sin columna
  title_is_manual ni migracion.
- Lapiz en cabecera actual y en cada entrada de historial. Editor reutilizable
  con campo etiquetado, guardar/cancelar y Enter/Escape. Escape cancela primero la
  edicion, sin cerrar el panel/dialogo. Iconos con tooltip/aria-label, sin botones
  anidados: seleccion de entrada y lapiz son hermanos.
- Un borrador puede recibir nombre manual local antes del primer envio; una marca
  local explicita evita confundir un nombre manual con el placeholder. Al crear,
  se envia ese nombre manual en lugar del derivado. Bloquear edicion de borrador
  mientras se asigna su id persistido para evitar carreras draft -> id.
- Renombrado persistido: PATCH /assistant/conversations/{conversation_id}, cuerpo
  cerrado {title}, respuesta ConversationRecord. Normalizar espacios en servidor;
  rechazar vacio o mas de 60 puntos de codigo normalizados (422), sin truncar
  silenciosamente lo escrito manualmente. No cambiar el contrato de creacion
  legacy ni limitar retrospectivamente titulos ya guardados.
- UPDATE parametrizado de title y updated_at, WHERE id + tenant_id + user_id,
  RETURNING campos publicos. Tenant/usuario de dependencias autenticadas, nunca del
  cuerpo. Ausente o ajeno: mismo 404. No tocar dialogue_history, summary, operaciones,
  revisiones/fences ni citar fuentes. Renombrar no dispara inferencia o compresion.
- En frontend actualizar celda y lista solo tras respuesta valida con identidad
  coincidente. Guardar deshabilitado mientras envia; fallo conserva titulo previo,
  texto editable y error local. Respuesta tardia no debe cambiar otra conversacion
  ni otro scope. Lecturas antiguas de historial no deben revertir un rename exitoso;
  invalidar su resultado o refrescar de forma ordenada. Entre renombrados manuales
  concurrentes en pestañas, gana la ultima escritura confirmada en servidor.

## Escenarios requeridos

1. Primera pregunta con espacios repetidos/largos/Unicode: titulo normalizado de
   hasta 60 puntos de codigo, misma pregunta original, sin llamada adicional.
2. Segunda pregunta, retry o final tardio: titulo manual intacto; reload recupera
   el nombre persistido. Un borrador renombrado conserva su nombre al crearse.
3. Lapiz en cabecera y entrada: guardar actualiza ambas vistas; cancelar/Escape
   no escribe. Enter guarda una sola vez; el lapiz no selecciona otra entrada.
4. Titulo vacio o excesivo: rechazo sin escribir; error de red mantiene editor y
   nombre previo. Scope o conversacion cambiados descartan callbacks ajenos.
5. Otro tenant, otro usuario, id inexistente o cuerpo con campos extra: rechazo
   sin modificar titulo, historial, operaciones ni resumen.

## Archivos previstos

Producto:
- apps/backend/app/schemas/assistant.py: request cerrado para renombrar.
- apps/backend/app/api/routes/assistant.py: PATCH autenticado.
- apps/backend/app/db/database.py: actualizacion scoped de titulo.
- apps/backend/app/main.py: PATCH permitido en CORS, soporte adicional autorizado
  tras detectar el bloqueo en navegador; sin ampliar origins/headers/credentials.
- apps/frontend/src/components/chat/useChatSession.ts: titulo inicial y rename.
- apps/frontend/src/components/chat/ChatPanel.tsx: editor en ambas ubicaciones.
- apps/frontend/src/components/chat/ConversationTitleEditor.tsx: editor compartido.

Pruebas focales implementadas:
- apps/backend/tests/test_conversation_titles_jup035.py: normalizacion, endpoint,
  persistencia y aislamiento mediante patrones existentes de API/repositorio.
- apps/backend/tests/test_cors.py: caso PATCH y lista exacta de metodos permitidos.
- apps/frontend/tests/chat-titles-jup035.test.tsx: envio inicial, ambas ubicaciones,
  teclas, persistencia simulada, errores y respuestas tardias.
- Repetir solo regresiones afectadas de chat-panel y typecheck/build frontend.

Documentacion: este archivo; integrar requisitos/escenarios en
specs/conversational-web-interface/spec.md y tareas de la misma change antes de
implementacion aprobada. Sin cambio de prompt/citas, dependencias, processor,
FinOpsResponse, migraciones o pagina legacy ConversationsPage.

## Evidencia local de implementacion

- Red: 9 fallos backend por PATCH inexistente (405); 6 fallos frontend por
  titulo fijo, rename ausente y controles de edicion ausentes.
- Green: 9 pruebas backend y 22 frontend (6 titulos + 16 panel) pasan. Typecheck
  de producto/pruebas y build frontend pasan; advertencias Vite de tamano de chunk
  e importacion mixta preexistente no bloquean el build.
- Una consulta de prueba ambigua entre titulo y etiqueta del boton se acoto al
  elemento de titulo; se conservo la asercion de seleccion sin cambios.
- La prueba de Escape descubrio cierre prematuro por captura Radix: el dialogo
  ahora cede Escape al editor activo. El lapiz recupera foco solo despues de una
  edicion real, nunca al montar cabecera o filas de historial.
- Mutaciones detectadas: retirar filtro SQL de usuario, truncar por unidades
  UTF-16 y omitir nombre manual del borrador. Copias temporales offline, originales
  montados readonly y SHA256 original comprobado sin cambios.
- Logs y scripts: evidencia externa restart-20261011/titles-*. Entrega detallada:
  titles-delivery.md en ese mismo directorio. No LLM, Git, red ni runtime modificado.
- Backend probado con fixture SQLite migrado y rutas reales; Cockroach/UI real
  quedan para comprobacion del padre tras desplegar backend y frontend. Sin
  migracion, cambios de processor, env o prompt. No se retocan titulos historicos.
- Correccion posterior al primer despliegue del padre: navegador rechazo PATCH
  por CORS GET/POST. Red OPTIONS devuelve 400; tras agregar solo PATCH, 14/14
  preflights permitidos/denegados pasan. Evidencia titles-cors-red/green.log.
  Requiere reiniciar backend; frontend sin cambios ni nuevo build por esta correccion.
