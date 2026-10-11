# Delta visual autorizado - 11/10/2026

Paris autoriza este cambio reversible en el checkout aislado: fecha relativa
espanola desde created_at, tooltip absoluto y refresco; mensaje del usuario
coloreado sobriamente y cabecera derecha con rol real; respuesta sin tarjeta;
retirar solo enlace superior /assistant, conservando ruta historica y ChatPanel.

Implementacion con primitives existentes de @assistant-ui/react 0.15.26,
Intl.RelativeTimeFormat y CSS local. No se instala agent-status (registry),
tw-shimmer, SDK ni dependencias. El tema actual sigue siendo oscuro unico;
superficie del usuario sigue la pestana activa principal, sin verde azulado:
primary al 10% sobre background, borde discreto border e inferior highlight de
2px, sombra interior y cabecera highlight alineada a la derecha. El cuerpo
conserva foreground. Las variables son colores hex completos en theme.css;
se usan directamente, sin envolverlas en hsl/rgb ni modificar la paleta global.

created_at persistido es la unica fuente del reloj visible; provisionales sin
fecha no muestran timestamp. Refresco cada30s y al cambiar visibilidad, fuera de
aria-live; title contiene fecha/hora absoluta. Rol del perfil autenticado, nunca
Profesional por defecto. Una unica region viva de progreso recibe cambios reales:
starting Preparando contexto; waiting capacidad/proveedor; active sin delta
Esperando respuesta del LLM; con partial Recibiendo respuesta; memoria pending
Actualizando memoria; running Comprimiendo contexto. Pausa/fallo/cancelacion y
reconciliacion sin shimmer; reduced-motion desactiva animacion. No timeline falso.

ChatContext.build prepara recuperacion y pantalla antes del SSE, pero no expone
subeventos y RAG puede no estar disponible. No se afirma consulta de datos ni RAG
como etapa independiente. No cambios backend, SSE, contratos publicos o modelo.
Pruebas focales UI, typecheck/build locales; inspeccion de navegador por el padre.
No equivale a aceptacion final de JUP-035 ni autoriza publicacion.

## Ajuste inline autorizado - 11/10/2026

Actividad dentro del transcript, entre la pregunta y su respuesta: filas
compactas con iconos lucide y texto gris, sin tarjeta, borde ni fondo. Solo la
ultima etapa activa tiene spinner/shimmer; las observaciones anteriores quedan
estaticas. Completed no agrega fila de exito y desactiva shimmer/spinner;
conserva etapas observadas anteriores. Restaurar completed sin etapas no muestra
actividad. Sin actividad no hay placeholder. La compresion acreditada conserva
prioridad incluso tras completed; fallos, pausa y reintentos siguen sin cambios.
Estado efimero en ChatPanel, fuera del Thread con clave: conserva la preparacion
al adoptar el borrador como conversacion de la misma solicitud. Cambiar de
conversacion u operacion reinicia observaciones. Recargar no reconstruye etapas:
solo muestra el estado actual conocido. No es un historial persistido de eventos.
El ResizeObserver existente incluye las filas y mantiene seguimiento al final
solo cuando el usuario no esta leyendo arriba. Una region viva para actividad;
reduced-motion tambien desactiva el spinner. Sin cambios backend ni dependencias.

## Memoria sin panel visible - 11/10/2026

Por autorizacion del usuario se retira el panel de memoria, cobertura, limites y
el boton Actualizar memoria. Se conservan consulta y refresco automaticos,
compresion, bloqueo de envio, persistencia y actividad Comprimiendo contexto.
Solo ante queue failed, blocked y retryable se ofrece Reintentar compresion,
con icono de reintento junto al estado operacional en el transcript. No cambia
canSend ni el hook de sesion; el reintento usa el mecanismo existente.

## Reintento junto al error operacional - 11/10/2026

Se elimina el boton global Reintentar respuesta. Solo state failed presenta un
icono RotateCcw de 32x32 a la derecha de la fila existente No se pudo completar
la respuesta en ChatProgress. Texto con ajuste de linea, icono sin encogimiento;
sin duplicar error ni crear mensaje placeholder. Los parciales se conservan
como provisionales. Callback y bloqueo por props, sin contexto adicional. Tooltip
y aria-label Reintentar respuesta. Completed y cancelled no ofrecen reintento.
Conserva session.send(question, pathname, true), bloqueo durante starting,
compresion y demas impedimentos de envio. Sin cambios de sesion ni backend.

## Ubicacion vinculada a la operacion - 11/10/2026

La actividad se inserta antes del parcial propio o del resultado persistido
verificado, siempre despues de la pregunta vinculada por question_id. La sesion
retiene solo en memoria el par operationId/messageId obtenido del resultado ya
validado; no cambia persistencia ni contrato backend. Si hay pregunta verificada
pero no respuesta propia, se inserta justo despues de esa pregunta, incluso en
solicitudes fallidas guardadas con mensajes posteriores. No se busca por texto
ni se atribuye a la ultima respuesta del historial. Sin pregunta identificable,
actividad operacional de compresion queda al final, sin asociarse a un mensaje.
Se reutilizan MessagePrimitive.Root y useAuiState instalados, con un contexto
React local para ubicar una sola region viva; no se crean mensajes ficticios.
ResizeObserver, reintentos y bloqueos permanecen. Reload no recrea etapas pasadas.

Compositor: alineacion centrada; Enviar tiene tamano fijo 48x48px, sin stretch,
sin padding, sin encogimiento e icono centrado. Se centra verticalmente respecto
al campo, que conserva crecimiento multilinea hasta 160px y min-width 0 para movil.
Solo clases visuales, sin cambios de envio ni nuevas pruebas funcionales.
