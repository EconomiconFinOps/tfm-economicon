# Citas del asistente — JUP-025

Nota de vigencia de JUP-101 (2026-10-10): el texto siguiente conserva íntegro su
corte de 01–02/10 y no representa el estado operativo actual. Consultar
[PR #55](https://github.com/EconomiconFinOps/tfm-economicon/pull/55), la tarjeta y
el [cambio archivado](../../openspec/changes/archive/2026-10-04-jup-025-answer-citations/design.md)
para el seguimiento posterior. JUP-101 no vuelve a ejecutar ni acreditar las
pruebas históricas. El contraste documental está en su
[evidencia](../evidence/JUP-101-continuity.md).

Verificación de estado: 2026-10-02. Tema de origen: JUP-025 — Citar fuentes utilizadas en cada respuesta. Las pruebas locales siguientes conservan su fecha histórica.

## Alcance y decisiones

- [Tarjeta](https://trello.com/c/qzRy4RQc), [PR #55](https://github.com/EconomiconFinOps/tfm-economicon/pull/55), rama `feat/JUP-025-source-citations`.
- Citas documentales con evidencia persistida y aislamiento por tenant. Se mantiene FinOpsResponse 1.0; no depende de PR #53.
- Implementación y validación histórica: [evidencia](https://github.com/EconomiconFinOps/tfm-economicon/blob/17c8514d8ef4d4da583f878b6fc19b968ef2ca82/docs/evidence/JUP-025-validation.md), [OpenSpec](https://github.com/EconomiconFinOps/tfm-economicon/tree/17c8514d8ef4d4da583f878b6fc19b968ef2ca82/openspec/changes/jup-025-answer-citations/design.md).
- Se asignó la revisión a Lucía (`lmatsan`); se solicitó formalmente en GitHub y se actualizaron PR/Trello. Paris pasó a pairing para conservar cuatro roles distintos. La asignación previa en el informe de evidencia quedó superada.

## Revision recibida (estado verificado el 01/10/2026)

La revision inicial corresponde a `1f28d427d09ace10653ed601f4170d3a1846d41e` y su veredicto fue `CHANGES_REQUESTED`. Lucía publicó revisión el 2026-09-30 a las 17:53:30 UTC (19:53:30 Europe/Paris). La solicitud inicial quedo atendida; tras corregir se ha solicitado una nueva revision (ver estado actual).

La revisión confirma aislamiento, referencias usadas, metadatos históricos y escape de texto. Declara CI 7/7 y pruebas adicionales; no se han vuelto a ejecutar en esta consulta.

Correcciones solicitadas por Lucía, reproducidas y corregidas el 01/10/2026:

1. Encabezados Markdown vacíos o CRLF pueden producir título/sección en blanco y un 500. Usar fuente como título y sección null, o error saneado; añadir prueba API.
2. `section_for_chunk` presenta coste cuadrático al normalizar prefijos por encabezado y recuperar texto completo por fila. Evitar trabajo repetido y añadir prueba de rendimiento.
3. Ignorar encabezados aparentes dentro de bloques de código y front matter YAML para no atribuir ubicaciones falsas.

Sugerencias no bloqueantes: espacios en `source` rompen el enlace exacto; títulos como `C#` pierden el carácter final; revisar cómo registrar el pendiente humano de tarea 2.5. Solicita registrar como finding que un 502 deja guardado el mensaje del usuario y su reintento lo duplica. La validación funcional del equipo sigue pendiente.

## Correccion del 01/10/2026

Correcciones de la revisión implementadas:
indice lineal por documento, lectura unica del texto en snapshot REPEATABLE READ,
exclusion de codigo/YAML, encabezados vacios, C# y source consistente. Medicion
local: 7,34 s antes y 0,0113 s despues para 400 KB/1.000 encabezados/cuatro fragmentos.
Backend 353 PASS/14 SKIP, pgvector real 5 PASS, frontend focalizado 14 PASS; detalles
y comandos en [evidencia](https://github.com/EconomiconFinOps/tfm-economicon/blob/17c8514d8ef4d4da583f878b6fc19b968ef2ca82/docs/evidence/JUP-025-validation.md#correcciones-de-la-revision--01102026).

La tarea 2.5 refleja el traspaso a Trello, no una aprobacion humana. RF-025-001 queda
registrado abierto en [findings](https://github.com/EconomiconFinOps/tfm-economicon/blob/17c8514d8ef4d4da583f878b6fc19b968ef2ca82/openspec/findings/backlog.md), como solicito
Lucia: no se ha reparado el duplicado de mensajes tras 502. La asignacion historica
de roles del informe tambien se ha actualizado a Lucia revisora y Paris pairing.

## Seguimiento histórico del 01/10/2026 (superado)

Correccion publicada como `b1fe43d710867801fa6896d4b84997537bf14534` en PR #55.
Solicitud formal renovada y verificada: `reviewRequests` incluye `lmatsan`.
CI verificado 7/7 sobre `803d241160765ed3a013378770484a342d0c7d9a`: [ejecucion](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/36854918932).
Pendiente atender la nueva respuesta de Lucia y completar la validacion
funcional del equipo antes del cierre. No se ha hecho merge ni enviado Discord.

Consulta: `gh pr view 55 --json reviews,reviewRequests,reviewDecision,headRefOid`.
La tarjeta se verifico el 01/10/2026
antes de actualizar el seguimiento; estaba En revision con los roles correctos.

## Estado confirmado el 02/10/2026 y próximos pasos

- Lucía (`lmatsan`) terminó la segunda revisión y [aprobó](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5381249566) el 01/10 a las 15:06:54 UTC (17:06 Europe/Paris). No solicita más cambios. Queda superado el pendiente de nueva revisión de Lucía.
- Víctor completó la validación y publicó [CHANGES_REQUESTED](https://github.com/EconomiconFinOps/tfm-economicon/pull/55#pullrequestreview-5385253656) el 01/10 a las 20:40:36 UTC. Lo [anunció en Discord](https://discord.com/channels/1477630870541303861/1477630871627370702/1555318735525388330) a las 20:41 UTC y lo documentó en Trello a las 21:05 UTC. Declara validación favorable con observaciones, CI 7/7, backend 361 PASS y pgvector 5/5; estas pruebas no se repitieron en esta consulta.
- PR #55 sigue abierta, sin merge, con decisión CHANGES_REQUESTED por Víctor y sin solicitudes de revisión pendientes. HEAD remoto consultado: `17c8514d8ef4d4da583f878b6fc19b968ef2ca82`; no se ha integrado en el checkout local durante esta consulta.
- Trello sigue en `40 — En revisión`. La descripción aún refleja pendientes humanos anteriores; el comentario de Víctor aporta el estado más reciente. Fuente: consulta mediante el puente de colaboración, sincronizada a las 09:31 UTC del 02/10.

Pendientes indicados por Víctor: corregir el foco al pulsar una fuente (propone `event.preventDefault()` y prueba); añadir prueba del fragmento real superior a 140 caracteres; acordar cómo resolver conflictos de continuidad entre PR #55/#60/#61/#62; actualizar enlaces documentales cuando se archive el cambio. Su sugerencia de retirar continuidad de la PR requiere coordinación y no sustituye las instrucciones vigentes del usuario de mantenerla.

Esta consulta fue solo de estado: no se aplicaron nuevos cambios de código, no se hizo merge y no se enviaron mensajes a Discord. Se actualiza continuidad local; siguiente paso, atender las observaciones de Víctor mediante la siguiente corrección.


## Correcciones posteriores a la validación (02/10/2026)

Se cancela la navegación por defecto de las citas para conservar el foco en el
resumen. Se añaden aserciones de cancelación/foco y una regresión que comprueba
la igualdad del pasaje y su extracto de 140 caracteres sobre un chunk largo.
Validación focalizada: 27 pruebas de citas backend y 14 de interfaz aprobadas;
lint y tipos correctos; OpenSpec 36/36. Las pruebas detectan los tres mutantes
(navegación por defecto, extracto 200 y pasaje 120); control restaurado en verde.
Las referencias documentales al contrato usan un commit inmutable para sobrevivir
al archivo del change.

La documentación de continuidad se extrae de PR #55 y se conserva en una propuesta
independiente [JUP-101](https://trello.com/c/ReMOdXEK), atendiendo la observación
sobre conflictos con #60/#61/#62. La convención sigue pendiente de acuerdo; su
integración no es una dependencia funcional de las citas. El registro de revisiones
y aceptación vigente permanece en PR #55 y Trello.


## Entrega de las correcciones de Víctor — 02/10/2026

Corrección publicada en `5ce57224419278901e8c99b0b7d2eebbbcad394e` y base actualizada
con develop `5a54ce2` mediante `ec7debe`. Se conservan las incidencias de ambas ramas
y se adapta AnswerEvidence a los tokens del tema. Tras integrar: 188 pruebas de
interfaz/paleta y tipos correctos, OpenSpec 37/37. Las correcciones de citas backend
habían pasado 27 pruebas y detectado los dos mutantes de recorte.

Se verificó la solicitud formal a `Victorh1397` en `reviewRequests` de PR #55.
No se ha hecho merge ni enviado Discord. CI del HEAD `ec7debe4ae9ef37e72314b007420ac74a89f71df`: [7/7 correctos](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/36992134412), verificados el 02/10. PR sin conflictos y solicitud a Víctor confirmada tras el último push.
La convención y resúmenes se conservan en [PR #64](https://github.com/EconomiconFinOps/tfm-economicon/pull/64),
borrador ligado a [JUP-101](https://trello.com/c/ReMOdXEK); quedan fuera del diff
funcional de #55. El puntero y los resúmenes locales siguen disponibles en este
checkout, sin publicarlos de nuevo en #55. La aceptación de la propuesta común y
adaptación de #60/#61/#62 permanecen pendientes del equipo.
