# Colector reutilizable del chat

Verificado: 2026-10-16. Origen: usuario solicita extraer el colector de B,
adaptarlo para JUP-071 y publicar PR independiente; chat
`01a1270c-e332-7462-9c90-706d49ade92c`.
Tarjetas: [JUP-123](https://trello.com/c/TqtcumIN),
[JUP-071](https://trello.com/c/H0woDubz).

## Contrato del colector solicitado en PR #131 — 16/10/2026

Origen: «Implementa los cambios que nos piden en PR131»; identificador del chat
no disponible. Base de corrección `af8388d0`.
Leídas todas las reviews y comentarios; sin inline. Lucía valida favorablemente
el alcance probado y propone un contrato con JUP-071/dashboard; la solicitud
de cambios de Víctor permanece hasta su aprobación.

Implementado el contrato del [comentario de Lucía](https://github.com/EconomiconFinOps/tfm-economicon/pull/131#issuecomment-6209801137):
capacidad booleana exacta ACCEPTS_UNMEASURED_DISTANCE para corpus con distance:null,
bloqueo legado conservado, structured sin texto de acciones y procedencia pública
por muestra marcada no atestiguada. Opcionales incluidos: exportación conjunta,
resúmenes, modo estricto con evidencia preservada y errores seguros con motivo.
Planes v2 fijan hashes de contenidos, métricas y calibrador; los commits ajenos
no invalidan ni alteran la identidad al reexportar. Planes/recibos v1 compatibles.
No se cambia la rama de JUP-071, aplicaciones ni proveedor. La consulta remota de
JUP-071 aún devuelve `81ceafc6`, sin capacidad; ese camino se prueba con fixtures.

Contrato y comandos en [la guía](../validation/chat-collector.md#contrato-con-jup-071-y-el-dashboard-de-jup-121);
detalle y límites en [la evidencia](../evidence/JUP-123-collector-validation.md).
Pruebas finales: 48/48 conformes, OpenSpec 74/74 y trazabilidad/higiene conformes.
Integración offline final: 87 fixtures, 521 GET, herramientas originales conformes,
exportación conjunta idéntica a las individuales y recibos v1 compatibles.
Recibo externo `JUP-123-collector/integration-10dd5cef/summary.json`, reproducible
con `materiales/07-evidencias/JUP-123-collector/integration-contract-20261016.py`
desde el espacio Economicon. Publicación del nuevo candidato en curso; no se da por integrada
ni aceptada B. Gasto incremental 0; no mensajes a Discord.

## Corte anterior: corrección y diagnóstico de CI

Estado actual: review de Víctor solicita cambios sobre `5cae4942`; comentario de
Paris corrobora el problema con una operación real de A. Corrección local:
corpus sin distancia bloquea el scorer legado, conserva originales y evidencia,
y no altera JUP-071. 33 pruebas conformes y contrafactual del scorer original
verificado: sin distancia fail→blocked; con distancia pass. Dos intentos de
prueba previos no ejecutaron la aserción por ACL; luego se reprodujo el fallo
antes de corregirlo. Ajustes editoriales de los documentos incluidos. A real no
aporta distancia: queda explícita esa dependencia del evaluador de JUP-071.
Corrección publicada en `af8388d0a87cf08184472c84f79247e7974c961b`. La CI nueva conserva seis fallos de salud en backend, cuyo árbol no cambia frente a la base: JWT de prueba creados al recolectar y caducados después de cinco minutos. El mecanismo se confirma con reloj sintético; no se cambian esas pruebas ni se relanza la CI. Revalidación de Víctor y validación de Lucía pendientes. Diagnóstico externo `PR121-local-evaluation/pr131-ci-auth-diagnosis-v1.json`.
Los resultados inferiores son históricos del candidato inicial.

Rama independiente `feat/JUP-123-response-collector`, base develop `53b43bb1`.
Publicada como [PR #131](https://github.com/EconomiconFinOps/tfm-economicon/pull/131),
abierta; commit técnico inicial `0bd494ba980c3c61fb846c2225299fda417f3804`.
Se confirma en GitHub que sus 19 archivos no incluyen aplicaciones, bancos o corpus.
Copia de trabajo propia, sin modificar B ni la rama de JUP-071. Se extraen colector
GET y reconciliador RAG de B; se añade adaptador para JUP-071, guía, pruebas y CI.
No hay cambios en apps, prompts, bancos, corpus, proveedor ni contabilidad.

31 pruebas offline pasan. Con JUP-071/`81ceafc6` se prueban 87 fixtures por 521 GET locales,
tres raw de 29 casos aceptados por su evaluador original, fallo técnico conservado
y reexportación idéntica. No se prueba calidad, despliegue real o gasto mediante
esas fixtures. [Evidencia](../evidence/JUP-123-collector-validation.md),
[guía](../validation/chat-collector.md),
[OpenSpec](../../openspec/changes/jup-123-chat-collector/proposal.md).

El adaptador necesita una copia local confiable con las herramientas de JUP-071, aún
ausentes de develop. Generar respuestas requiere el flujo autorizado del chat;
este colector sólo lee operaciones persistidas. RAG no expuesto por API necesita
snapshot exacto; sin él la muestra sigue incompleta. No se inventan distancias,
latencias, juicios o atestaciones. CI de la publicación iniciada; no se da por verde
antes de terminar. Revisión y validación independientes pendientes. Trello enlazado
por integración DockerServer: notas `6ad12c46540d36d20e94abe4` (123) y
`6ad12c47a42120afd056bed2` (071), listas y descripciones intactas. No se ha enviado
ningún mensaje Discord. La publicación parcial no acredita aceptación de B.
