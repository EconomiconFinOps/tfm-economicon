# JUP-025 — Citas documentales

- Tarjeta: https://trello.com/c/qzRy4RQc
- Base contrastada: `origin/develop`, `2efef1a`, 30/09/2026.
- Rama: `feat/JUP-025-source-citations`.
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
- Liderazgo: Alejandro Aguado. Pairing: Lucia Mateo. Revision: Paris Arcos Martin.
  Validacion: Victor Mendez. Son asignaciones de Trello, no aprobaciones humanas.
- La revision asignada y validacion del equipo siguen pendientes antes del cierre.
