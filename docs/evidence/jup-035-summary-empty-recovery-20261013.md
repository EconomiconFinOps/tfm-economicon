# JUP-035: resumen vacio y recuperacion del estado

Fecha: 2026-10-13. Rama codex/JUP-035-checkpoint-handoff.
HEAD 8d98ae57853c8c24a3d7f61881887b8467fac828 con correcciones locales;
no se declara un ensayo del HEAD limpio. Paris autorizo estos dos arreglos.

## Correcciones

- Backend y processor rechazan resumenes sin topics ni facts, tambien al leer
  un artefacto previo. Las limitaciones solas no sustituyen los pares originales.
- Prompt precisa conservar entidades e identificadores de prueba aunque no
  sean evidencia financiera. Manifiesto y huellas actualizados coordinadamente,
  sin cambio de esquema o modelo.
- Lectura de memoria: tres reintentos adicionales de red/5xx, cada dos segundos;
  mantiene bloqueo y borrador. Error persistente muestra aviso y accion explicita.
  Identidad invalida no recibe reintentos automaticos.

## Pruebas locales

Dos controles iniciales de resumen vacio fallaron por DID NOT RAISE.
Tras el arreglo: backend 126 pruebas superadas en resources/context/lifecycle,
mas una focal de artefacto vacio previo. Processor 54 superadas en resources/gateway.
Frontend: 17 en summary y 16 en panel, incluida recuperacion tras un 500 y
limite de reintentos con recuperacion manual. Typecheck principal y construccion
de las tres imagenes correctos. Avisos de bundle grande y datetime SQLite conservados.

Una fixture inicial de la nueva prueba UI omitia queue.reason; se corrigio para
reproducir un 500 de estado sin relajar el contrato. El primer control de mutacion
backend importo el producto original y no acredita deteccion. Corregida la ruta,
ambos mutantes se detectan: retirar rechazo de vacio falla dos casos; retirar
retry de estado falla uno. Mutaciones solo en copias desechables.

Comandos focalizados desde cada servicio con dependencias instaladas:

    python -m pytest -q tests/test_chat_summary_resources_jup035.py tests/test_chat_summary_context_jup035.py tests/test_chat_summary_lifecycle_jup035.py
    python -m pytest -q tests/test_chat_summary_resources_jup035.py tests/test_chat_summary_gateway_jup035.py
    node node_modules/vitest/vitest.mjs run tests/chat-summary-jup035.test.tsx tests/chat-panel-jup035.test.tsx

## Repeticion real

Compose del proyecto con override aislado jup035real20261013, modelos existentes,
datos sinteticos y claves separadas. Imagenes jup035fix20261013-backend,
jup035fix20261013-processor y jup035fix20261013-frontend verifican recursos en build.
No se repiten ingesta documental ni bateria completa.

Conversacion 8fb8b8d2-2606-4325-b826-3be12609d9c5: cinco pares sinteticos
identificados como fixture, no cinco inferencias. Primer par contiene AZ-6082
y Equipo Abeto; los cuatro posteriores no. Reintentar compresion recorre
backend/processor/LiteLLM/OpenRouter.

- Artefacto 310a8ce4-097f-4f10-9c6e-4778c016181d contiene ambos datos con
  referencias autorizadas. Comprobado exact_output, no el input del recibo.
- Diez mensajes originales identicos y persistidos.
- Navegador: Enviar bloqueado al inicio, borrador conservado y habilitado al
  terminar sin recarga ni reapertura. El 500 deliberado se prueba de forma
  controlada, no se presenta como incidente de este ensayo corregido.
- Pregunta posterior completed: recuerda ambos datos como sinteticos, sin
  inventar citas ni metricas financieras.
- Entrada persistida: summary.used=true con mismo artefacto y cuatro pares
  recientes; primer par fuera de recent_pairs. Doce mensajes sin duplicados
  y resumen disponible.

Para repetir: Compose y base desechable, cinco pares por prepare_message/
append_final con metadata test_fixture; armar un control fallido solo para
esa conversacion y usar /summary/retry. Comparar mensajes y exact_output,
preguntar por el dato exclusivo del primer par e inspeccionar canonical_input.context
y context_manifest del resultado. No presentar la fixture como umbral automatico.

## Consumo y limites

Ensayo completo incluidos fallos: upstream 0.737674106 -> 0.753230616 USD,
adicional 0.015556510 USD de 0.12 autorizados. Solo repeticion corregida:
0.005768541 USD. Deltas virtuales y diferencia entre medidores conservados.
Sin cambios de tope upstream, modelos o permisos.

Recibos originales, corregidos y mutaciones fuera del repo, en
jup035-review-evidence-20261013/real-20261013/fixed junto al worktree.
No contienen claves ni son dependencias de arranque.
No cierra JUP-035: pendientes 005/006, restos legacy, traslado de propiedad
si se decide y actividad RAG explicita. No acredita fidelidad universal,
umbral automatico grande ni revision humana. Sin commit, push, PR ni merge.
