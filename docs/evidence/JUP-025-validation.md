# JUP-025 — Citas documentales

- Tarjeta: https://trello.com/c/qzRy4RQc
- Base contrastada: `origin/develop`, `2efef1a`, 30/09/2026.
- Rama: `feat/JUP-025-source-citations`.
- PR: https://github.com/EconomiconFinOps/tfm-economicon/pull/55
- Contrato y escenarios: [OpenSpec](../../openspec/changes/jup-025-answer-citations/).

## Resultado

El chat conserva los IDs existentes y agrega una instantanea de cada fuente
utilizada. Los tres extractos citados enlazan al documento, fuente, referencia
estable, seccion disponible y evidencia expandible. El cuarto resultado de
retrieval ya no se presenta como evidencia utilizada. Reabrir una conversacion
conserva las citas. Los IDs inexistentes, repetidos o ajenos al tenant impiden
guardar una respuesta del asistente; la respuesta de error no contiene esos IDs.

Las referencias no son URLs de descarga. No se exponen URIs de artefactos ni
parametros de acceso. El enlace abre el extracto historico guardado en el mensaje.
La autorizacion de lectura sigue siendo la de la conversacion y su propietario.

## Validacion ejecutada

Entorno local: Windows, Python 3.14, dependencias del lockfile sin cambios.

| Comprobacion | Resultado |
| --- | --- |
| Backend completo | 336 pruebas aprobadas; 10 opt-in omitidas en esa ejecucion |
| Pgvector real aislado | 3 aprobadas: tenant A, tenant B y tenant sin documentos |
| Regresion JUP-024, `test_agent_runtime.py` | 16 aprobadas, sin modificar el contrato |
| Frontend completo con `--maxWorkers=1` | 267 aprobadas, 47 archivos |
| Ajuste final de enlace exacto a evidencia | 7 pruebas focalizadas aprobadas, incluida pregunta con marcador falso |
| Typecheck, build y lint de componentes nuevos | Correctos |
| OpenSpec estricto | 35/35 |
| Trazabilidad JUP y diff check | Correctos |

La primera ejecucion paralela del frontend tuvo ocho fallos de espera bajo carga;
la misma suite paso con un unico worker sin modificar los timeouts ni las pruebas
existentes. Posteriormente se agrego la prueba del marcador falso y se ejecuto la
suite focalizada. No se presenta 267 como el recuento final de todos los tests.
Persisten avisos de deprecacion de dependencias Python y tamano del bundle Vite.

Pgvector se ejecuto en un contenedor efimero separado en DockerServer, con puerto
loopback 55425, almacenamiento tmpfs y credenciales sinteticas. Se reutilizo la
fixture que verifica una base vacia, crea bases de prueba y las elimina. No se
utilizo ni modifico la base desplegada por JUP-021 o la PR #53.

## Comprobacion visual

Playwright abrio la aplicacion Vite en Chromium con respuestas API sinteticas:
click en `[1]`, evidencia visible, recarga de conversacion y vistas de escritorio
(1360 px) y movil (390 px). No hay enlaces externos en el panel de fuentes.
La persistencia real del mensaje se comprueba por separado en las pruebas API,
no mediante las respuestas sinteticas de navegador.

Capturas locales: `materiales/07-evidencias/JUP-025-citas-2026-09-30/`, fuera del
repositorio. Las citas se adaptan al ancho movil; la cabecera y navegacion global
ya desbordan ese ancho y no forman parte de este cambio.

## Limites y participacion

- La ingesta actual no conserva paginas PDF. `page` queda null; no se inventa.
- Se recupera seccion de Markdown original solo con coincidencia unica del chunk.
- Los mensajes historicos con solo IDs indican que la evidencia no esta disponible.
- FinOpsResponse 1.0 pertenece al processor; este chat sigue usando extractos
  deterministas. No se acredita conexion a LLM, calculo de metricas ni ejecucion
  de recomendaciones. Sus guardrails y evidence_ids permanecen intactos.
- Liderazgo: Alejandro Aguado. Pairing: Paris Arcos Martin. Revision: Lucia Mateo.
  Validacion: Victor Mendez. Son asignaciones de Trello, no aprobaciones humanas.
- La revision asignada y validacion del equipo siguen pendientes antes del cierre.


## Correcciones de la revision — 01/10/2026

[Revision de Lucia](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5369995407)
sobre `1f28d42`: los tres problemas se reprodujeron antes de corregirlos.

- Encabezados vacios con espacios o CRLF ya no generan texto en blanco: se usa
  source como titulo y seccion null. Dos regresiones API confirman 201 y cita valida.
- Un indice de ubicaciones por documento normaliza texto en una pasada e ignora
  bloques cercados con backticks/tildes, codigo indentado y front matter YAML inicial.
  Las cercas sin cerrar se tratan conservadoramente como codigo. C# se conserva;
  solo se retiran hashes de cierre precedidos de espacio.
- La consulta de vecinos no trae texto completo. Una segunda consulta autorizada
  obtiene cada documento una sola vez; ambas usan la misma transaccion REPEATABLE
  READ. Las pruebas reales verifican cuatro chunks/un indice y una reingesta entre
  las dos consultas sin mezclar versiones.
- El source se recorta igual en el pasaje y en la cita, restaurando su enlace.
- La tarea tecnica 2.5 registra el traspaso del pendiente humano a Trello. No se
  acredita aprobacion, validacion funcional del equipo ni cierre de tarjeta.
- Se registra [RF-025-001](../../openspec/findings/backlog.md): un fallo 502 deja
  persistido el mensaje de usuario y un reintento lo duplica. Sigue abierto, como
  solicito la review; no se ha cambiado el contrato de reintentos ni persistencia.

Medicion local reproducible: documento de 400.780 caracteres, 1.000 encabezados y
cuatro fragmentos finales. Antes: 7,34 s. Despues: 0,0113 s para indexacion y cuatro
busquedas. Es una medicion del procesamiento local, no una promesa de latencia
HTTP. La prueba automatizada exige menos de 1,5 s con margen para CI.

Validacion de esta correccion:

- Backend completo: 353 PASS, 14 SKIP de servicios opt-in.
- Pgvector real efimero separado: 5 PASS, incluidas lectura unica y reingesta.
- Frontend focalizado de citas/conversaciones: 14 PASS. Sin cambios de frontend.
- OpenSpec estricto 35/35, trazabilidad y diff check correctos.

Comandos: `python -m pytest apps/backend/tests -q`; `python -m pytest
apps/backend/tests/test_tenant_isolation_vector.py -q` con la variable de conexion
sintetica `JUP086_VECTOR_TEST_URL`; `corepack pnpm --filter @finops/frontend test --
src/components/AnswerEvidence.test.tsx src/pages/ConversationsPage.test.tsx
tests/conversations.test.tsx --maxWorkers=1`. Python usa `PYTHONPATH=apps/backend`.
