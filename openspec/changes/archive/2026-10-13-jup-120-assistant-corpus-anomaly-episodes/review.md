# Review JUP-120 — Corpus del asistente con anomalías por episodios y guía del panel

JUP: JUP-120 · Trello: https://trello.com/c/ifIn4Vjr · Rama: `feat/JUP-120-assistant-corpus-anomaly-episodes`

## Resumen

El corpus del asistente (JUP-019, agosto) no sabía nada de los episodios de anomalía de JUP-114 (ADR-0020) y decía lo contrario en dos puntos: severidad en «EUR/mes» y el estado `acknowledged`. El change actualiza las reglas de negocio (episodio, valor esperado, referencia anclada, tolerancia, servicio sin gasto previo, severidad por impacto acumulado, estados), añade al documento de producto una guía del panel con los textos de la pantalla, ajusta el glosario, sube la versión de los tres documentos y vuelve a fijar las huellas de la batería JUP-069 (1.0.1), de las etiquetas de JUP-022, del ejemplo sintético de JUP-067 y del registro de calibración. No toca código de producción: la única pieza nueva de código es una prueba que vigila que las reglas de JUP-070 fijen la versión de la batería. Cierra `RF-114-001`.

## Decisiones

- **Editar en el sitio y volver a fijar las huellas** (Lucia, 2026-10-13), frente a un documento nuevo o a dos pasos. Corrige el error donde está y evita que el modelo recupere la versión antigua.
- **Mantener intacto el fragmento de presupuestos** (Lucia, 2026-10-13). Una frase añadida en presupuestos y un desplazamiento de 42 caracteres mezclaban presupuestos y anomalías en el mismo fragmento y hacían perder el caso 013 con la distancia máxima en uso (0,6). Los fragmentos 0 a 6 del documento de reglas son idénticos a los de antes del cambio.
- **La batería nueva de anomalías va en una tarjeta aparte** (Lucia, 2026-10-13): las herramientas de preguntas están escritas para JUP-069 y habría que parametrizarlas, lo que añade código a un change de contenido. Consecuencia asumida: este change no tiene preguntas que midan el beneficio del texto nuevo.
- **No esperar a #127 ni #128** (Lucia, 2026-10-13): la guía no menciona la fecha de referencia ni «Explicar en el asistente» porque no están en `develop`; entrarán cuando se integren.
- **Calibración real con el gateway local**, autorizada por Lucia; no se cambia ningún valor de configuración.

## Adversarial Review (pass 1)

Revisor independiente (agente `adversarial-reviewer`), con la ruta del change, los commits de base y de cabeza (`bfaf3983..730a6378`) y los artefactos, sin el razonamiento de quien implementó. Veredicto: `changes-required` (1 HIGH, 4 MEDIUM, 2 LOW).

| Hallazgo | Severidad | Resultado |
| --- | --- | --- |
| ADV-1: la guía decía que hacen falta 8 días con datos y el motor necesita 9 (el último día es incompleto y el día evaluado necesita 7 previos) | Alta | Reproducido leyendo `detection_window` y `_evaluable`; corregido a «9 días seguidos»; registrado `RF-120-001` (el aviso del panel dice 8) |
| ADV-2: «pasan 3 días sin saltar» es un error por uno; el código usa `> TOLERANCE_DAYS` y «Ya no se observa» sale al cuarto día | Media | Reproducido en `plan_detection`; texto, spec y diseño corregidos |
| ADV-3: la guía decía que el resumen cuenta «todas las anomalías»; Abiertas, Alta (P1) y «Ya no se observan» cuentan solo abiertas | Media | Corregido; registrado `RF-120-002` (subtítulo del panel) |
| ADV-4: `JUP-070-evaluation-rules.json` seguía fijando la versión 1.0.0 de la batería | Media | Prueba nueva en rojo, corrección a 1.0.1, prueba en verde |
| ADV-5: el apartado del servicio nuevo podía llevar a decir que el recurso del caso 019 cumple la regla | Media | Se añadió que con referencia cero el aumento relativo no está definido y se colocó antes de la explicación; después se quitó la cifra de unos 116,67 al día (ver pasada 2) |
| ADV-6: el KPI MTTA/MTTR decía «reconocimiento» sin definirlo | Baja | Definido en la sección de estados (primer cambio desde Nueva) |
| ADV-7: `RF-114-001` figuraba como Fixed y remitía a un `review.md` inexistente | Baja | Este fichero |

Ataques que resistieron según el revisor: recálculo de los sha256 de los cuatro documentos frente a las tres fijaciones, batería idéntica salvo `sources` y `suite_version`, huella de suite del ejemplo sintético, ASCII de los documentos, ausencia de endpoints y de la fecha de referencia, y los umbrales de severidad, monedas, referencia anclada y 7 días frente a ADR-0020.

## Adversarial Review (pass 2)

Mismo revisor, sobre `bfaf3983..70211fc5`. Veredicto: `changes-required` (1 HIGH, 5 MEDIUM, 6 LOW).

| Hallazgo | Severidad | Resultado |
| --- | --- | --- |
| ADV-1: con la distancia máxima por defecto del código (0,6) el caso 013 pierde su fragmento esperado | Alta | Decisión de Lucia: restaurar el fragmento de presupuestos. Los fragmentos 0 a 6 son idénticos a los de la base y 013 vuelve a 0,5826. La calibración final mantiene 0,6 como recomendada |
| ADV-2: otros documentos fijan la calibración antigua (0,6, «top_k 3 a 6 igual», 52 fragmentos) | Media | Nota fechada en ADR-0017; el resto son registros históricos. El hallazgo `RF-120-003` que proponía 0,65 se retiró al dejar de ser cierto |
| ADV-3: `RF-114-001` como Fixed sin `review.md` | Media | Este fichero |
| ADV-4: la cifra 116,67 puede inducir a decir que el recurso del caso 019 «cumple» | Media | Cifra quitada del corpus; el texto es cualitativo |
| ADV-5: «9 días» sin «seguidos» | Media | Corregido |
| ADV-6: etiquetas de 019, 024 y 026 desfasadas | Baja | Registrado `RF-120-003` (cambiar la cobertura altera los denominadores de REL-2) |
| ADV-7: la tarea 1.2 y la propuesta afirmaban cambios no hechos | Baja | Corregidos |
| ADV-8: un fragmento empezaba a mitad de frase | Baja | El párrafo de candidata se movió antes de «Estados» y cae en el fragmento 12 |
| ADV-9: la guía llamaba «Investigando» a la acción | Baja | Alineada con «Marcar en investigación», «Cerrar» y «Confirmar cierre» |
| ADV-10, ADV-11 y ADV-12: README de validación, «máximo de 7 días» en continuidad, frontera de P2 | Baja | Corregidos («ya no coincide», sin límite de 7 días, «ambos incluidos») |

## Adversarial Review (pass 3)

Mismo revisor, sobre `bfaf3983..1330e9de`. Veredicto: **`accept`**, sin hallazgos bloqueantes ni altos.

| Hallazgo | Severidad | Resultado |
| --- | --- | --- |
| ADV-1: ADR-0017 describía como vigente la calibración del 03/10 | Media | Nota fechada en ADR-0017 con las cifras actuales; ninguna configuración cambia |
| ADV-2: la tarea 1.6 decía que el encabezado cae en el fragmento de la regla | Media | Corregida: el encabezado queda al final del fragmento 6 (idéntico a la base) y la regla y sus límites en el 7, que es lo que exige la spec |
| ADV-3: con un hueco de datos tras el pico, «Ya no se observa» tarda más de 4 días porque los días sin datos no avanzan la tolerancia | Baja | Aceptado como limitación conocida de ADR-0020; no se matiza el corpus para no mover los fragmentos |
| ADV-4: «servicio» frente a «recurso» en el apartado del servicio nuevo; «el primer día no abre episodio» puede inducir a decir «no es una anomalía» en el caso 019 | Baja | Aceptado; solo una campaña con modelo lo confirma o descarta, y es parte de la batería de la tarjeta aparte |
| ADV-5: «ninguno empeora» solo vale con top_k 4 a 6 | Baja | Salvedad añadida a la tarea 2.5 |

Ataques que resistieron: severidad con sus fronteras, tolerancia, mínimo de 9 días, umbral del servicio nuevo, resumen del panel solo de abiertas, huellas, troceado (presupuestos idéntico a la base) y que el registro de calibración no contiene texto de fragmentos, preguntas ni credenciales.

## Validación

| Comprobación | Resultado |
| --- | --- |
| `assistant-corpus:validate` y `:test` | OK, 8 pruebas |
| `validation-questions:validate` y `:test` | OK, 28 consultas |
| `retrieval-labels:validate` y `:test` | OK, 28 etiquetas (23 directas, 3 parciales, 2 sin cobertura) |
| `retrieval-calibration:test` | OK (1 omitida) |
| `python -m unittest discover -s scripts/tests` | 400 pruebas OK, 17 omitidas |
| `openspec:validate`, `jup:check -- --change jup-120-...`, `jup:cleanup:check`, `jup:check:test`, `jup:cleanup:test`, `git diff --check` | OK |
| `corepack pnpm lint` | OK (4 de 4) |
| Frontend (`vitest run`) | 66 ficheros y 879 pruebas, todas pasan |
| azure-cost-api (venv 3.12) | 81 pasan |
| Processor (venv 3.12, como CI) | 855 pasan, 90 omitidas y 1 falla (`test_jup023_attempt_deadline_interrupts_trickle[0-body]`, prueba de plazos); esa prueba pasa sola 3 de 3 veces, así que es intermitente con la suite entera. Con el Python 3.14 del sistema falla otra distinta (`test_json_depth_error_is_discarded_once_then_next_delivery_is_returned`), que con 3.12 pasa; CI usa 3.12 |
| Backend (venv 3.12) | 1110 pasan, 118 omitidas y 145 fallan, todas en `test_health_provider_admission_jup047.py`, `test_health_provider_response_jup047.py`, `test_system_health_jup047.py` y `test_health_provider_policy_jup047.py`, por `socket.socketpair` de asyncio en Windows. Es la misma cifra que la revisión de JUP-114 documentó como fallo conocido de Windows; no se ha vuelto a comprobar contra `develop` en este change |
| Ficheros de `apps/` modificados por este change | 0 (`git diff --name-only bfaf3983...HEAD -- apps`) |
| Calibración real de la recuperación (92 llamadas, 0 fallos, con 2 errores 500 del proveedor absorbidos por el reintento) | con top_k 4 y distancia 0,6: sección 0,70 → 0,75, documento 0,90 → 0,90, vacíos 5 % → 5 %; solo el 016 cambia de resultado (pasa a acertar); la distancia recomendada sigue en 0,6 |

Coste de las llamadas de embeddings de las cuatro pasadas: muy inferior a 0,01 USD.

## Límites de la evidencia

- La calibración mide qué fragmentos se recuperan, **no qué dice el modelo**. Ningún caso se ha ejecutado con un modelo generativo, y el efecto del texto nuevo sobre 003, 013, 014, 016 a 019 solo lo verá una campaña con modelo.
- **No hay preguntas que midan el beneficio del contenido nuevo**: JUP-069 solo cubre la regla diaria. Queda para la tarjeta aparte.
- Se probó con embeddings reales y un solo gateway local; no se probó en el entorno compartido ni con la campaña de JUP-035 (#120 y #121).
- La guía se verificó leyendo el código del panel, no en un navegador.
- No se ejecutó el panel real con el stack: el change no toca código del panel.

## Seguimientos y hallazgos

`openspec/findings/backlog.md`:
- `RF-114-001`: resuelto por este change.
- `RF-120-001`: el aviso de «Detectar ahora» dice 8 días y el motor necesita 9.
- `RF-120-002`: el subtítulo del resumen del panel dice «todas las anomalías» y cuenta solo las abiertas.
- `RF-120-003`: etiquetas de JUP-022 de los casos 019, 024 y 026 desfasadas.

Pendiente fuera de este change:
- **Batería de preguntas de anomalías** (tarjeta aparte, por crear): 6 a 8 preguntas con contexto, fragmentos esperados por encabezado, rúbrica y reglas de conductas prohibidas, en un fichero distinto de JUP-069 y con las herramientas de validación parametrizadas.
- **«Explicar en el asistente» (#128)** no está en `develop`; cuando se integre hay que añadirlo a la guía y volver a fijar la huella de `product`. La fecha de referencia (#127) se añadió el 2026-10-14 (ver la adenda).
- **Aviso a Alejandro y a Paris (JUP-035) antes de mergear**: el merge cambia la huella del corpus, la huella y la versión de la batería JUP-069 y el número de fragmentos (de 52 a 65), así que sus pasadas anteriores y posteriores dejan de ser comparables.

## Adenda 2026-10-14: fecha de referencia

La revisión del PR #129 señaló que #127 (JUP-119) ya estaba en `develop` y que la frase de reglas «no se evalua hasta que haya datos de un dia posterior» no describe el modo con fecha de referencia, que es el de la demo de JUP-107. Lucia decidió añadirlo en este PR sin esperar a #128 (tareas 5.1 a 5.5).

| Comprobación | Resultado |
| --- | --- |
| Texto frente a `docs/api/reference-date.md` y `docs/api/anomaly-episodes.md` | la detección no evalúa la fecha de referencia ni días posteriores; las lecturas incluyen el día de referencia y no los posteriores; los episodios que dependen de días a partir de esa fecha se ocultan |
| Troceado | reglas: 18 fragmentos, solo cambia el 9; producto: 16 fragmentos, cambian el 7 y el 8 y el resto coincide con los anteriores |
| Calibración real con el texto final (93 llamadas) | `answer`, selección y caso 019 sin cambios; con distancia 0,6, acierto por documento de clarify/abstain 0,75 → 0,875 por el 026 |
| Revisión adversarial (`adversarial-reviewer`) | `accept-with-changes`, sin afirmaciones falsas; ADV-1 a ADV-6 (dos Media, cuatro Baja) atendidos sin mover los cortes (tarea 5.6) |
| Validadores y pruebas | corpus, batería, etiquetas, calibración, `assistant-eval` (110) y `assistant-metrics` (103) en verde |

Límite: igual que en la calibración anterior, mide qué fragmentos se recuperan, no lo que dice el modelo.

## Aplicabilidad de ADR

No hace falta un ADR nuevo: no hay una decisión arquitectónica. Se añade una nota fechada a ADR-0020 (el corpus se actualizó en este change y no en JUP-038) y otra a ADR-0017 (las cifras de calibración citadas son las del 03/10).

## Human Approval

- Change: jup-120-assistant-corpus-anomaly-episodes
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-10-13
- Adversarial review: accept (pass 3) | accepted findings: ADV-3, ADV-4 y ADV-5 de la pasada 3 (todos Baja: hueco de datos tras un pico, «servicio» frente a «recurso» en el caso 019 y las salvedades de top_k 3), aceptados al aprobar este `review.md`, que los registra
- Archive decision: archive
- Notes: change de contenido y de huellas, sin código de producción. Lucia avisó a Alejandro y a Paris (JUP-035) el 2026-10-13, antes de mergear; queda por acordar con ellos la fecha de integración respecto a su pasada de aceptación. Pendiente fuera de este change: tarjeta aparte para la batería de preguntas de anomalías, y añadir a la guía la fecha de referencia (#127) y «Explicar en el asistente» (#128) cuando estén en `develop`. Sin revisión ni validación de compañeras: el trabajo va por la excepción temporal del 2026-10-11.
