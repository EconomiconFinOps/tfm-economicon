# División de JUP-035 en A y B

Actualizado: 2026-10-14. Origen: chat 01a1270c-e332-7462-9c90-706d49ade92c.
El usuario confirma aprobación del equipo y autoriza actualizar Trello, publicar
A y cerrar #120/#121 sin integrar. No autoriza despliegue ni mensajes Discord.

- Padre: [JUP-035](https://trello.com/c/BJfABykd), continúa pendiente.
- A: [JUP-122](https://trello.com/c/gFYKmcLT), ingeniería/base del chat.
- B: [JUP-123](https://trello.com/c/TqtcumIN), calidad semántica/evaluación.

A parte de develop c30a7d0, base chat Paris f63c150 y bloques de ingeniería
extraídos de PR121. Rama feat/JUP-122-chat-engineering. Chat apagado por defecto.
Se conserva required-documentation-v1; el rediseño server-documentation-v4,
expresiones y reglas de PR121 permanece en B. Esto no revierte v4 en B ni
justifica rehacer su eliminación de tools. Ver el [diseño](../../openspec/changes/jup-122-chat-engineering/design.md).

Las PR antiguas siguen siendo evidencia de autoría y findings. Sus requests
changes no se transforman en aprobaciones al cerrar: A requiere reviews propias.
No se borra ninguna rama. El candidato local de B 50e169fa se conserva intacto.

PR-A publicada: [#130](https://github.com/EconomiconFinOps/tfm-economicon/pull/130).
Primer candidato 2b55e1e2: SQL nativo54PASS y frontendCI favorable; resto de CI
en curso. Corrección adicional de aislamiento de flag en tests:27PASS.
Trello actualizado mediante la integración DockerServer; scripts y recibos en
materiales/07-evidencias/JUP-035-split, fuera del repo. Pruebas y publicación en
curso; no presentar los resultados de la extracción como CI del commit final.
Sin nuevas inferencias ni consumo. Último gasto histórico 0,957927619 USD / 2 USD.

Pendientes: CI final de A y UI, reviews de A; después colector, criterios
acordados y campañas N=3/N=5 de B. No activar ni integrar automáticamente.


## Comprobación de A — 14/10/2026

PR130 sigue OPEN en318a56f31828be50f8960860f69172f51046734d, base develop
c30a7d0. Pruebas Python, frontend, OpenSpec y SQL nativo SUCCESS; JUP reviews
FAILURE y reviewDecision CHANGES_REQUESTED. Review5513304503 exige retirar
chat/v2/tokenizer.json del repositorio y generarlo en build/CI con revisión,
tamaño y SHA256 fijos (referencia a8f4dddc). No acredita todavía los criterios
funcionales de JUP-122; falta Revision. Sin comentarios inline ni conversación
adicionales en la consulta. Evidencia externa pr130-base-check-20261014.json en
materiales/07-evidencias/PR121-local-evaluation. No se ha modificado A desde B.
B puede medir su candidato, pero reconciliación y aceptación de A siguen abiertas.

Reconsulta posterior a las pruebas Linux/SQL de B: PR130 conserva los mismos
SHA318a56f/c30a7d0 y CHANGES_REQUESTED; reviewlmatsan sigue solicitando tokenizer.
No se ha incorporado una corrección nueva de A ni hay aprobación inferida.


## Nueva cabeza de A — comprobación 14/10/2026 18:28 UTC

Supera la cabeza318a56f de las observaciones previas: ahora28ee5b1c44389aa8643c1c4deca6c0c834c09f7d.
Paris retiró tokenizer.json versionado, añadió build_tokenizer.py y pruebas,
modificó Dockerfiles/CI, exclusión .secrets enrelease y limpieza de fixtureSQL.
CI técnicaSUCCESS, peroJUP reviewsFAILURE yreviewDecisionCHANGES_REQUESTED;
única review oficial sigue solicituddeLucía sobre318a56f. Comentario deParis
reporta comprobacionesinternas; no sustituye Revision/Validacion oficiales.
Sin inlinecomments. Se consultaron reviews,conversación ydiffmetadata; no es
revisiónfuncional nueva. Recibo fueraGit jup122-pr130-current-20261014-evening.json.
B todavía debe reconciliar esos bloques respetando v4 y los planes congelados;
no cherry-pick ciego de ficheros/documentación. No merge ni mensajes externos.

## Bloques de A incorporados localmente a B — 14/10/2026

Comparación de14archivos afectados con318a56f acreditó igualdad deB conla base;
se aplicó sólo eldiff de17archivos de28ee5b1c másla retirada deltokenizer delíndice.
No se copiaron losresúmenes/OpenSpec deA ni se cambió elgateway v4 deB.
Helper/build/CI/CD yfixtureSQL conservan sus bloques deParis; README incorpora
preparación delasset. Elcache físico local se conserva, ahora ignorado, con pin
idéntico alchat/summary. Reconciliación funcional/SQL/runtime aúnpendiente.

Herramientas B ahora congelan helper/Dockerfiles/locks ypin deartifact generado;
verifican eltokenizer real enambos contenedores yexigen pins enpreflight antes
dereservar/enviar. Planes/recibos antiguos intactos.86pruebas evaluaciónPASS,
4helperPASS,CD55PASS/2SKIP y51comprobaciones CI/topologíaPASS. Node usó
--test-isolation=none porEPERM deprocesos ensandbox. Logs/resultados externos
reconcile-a-{eval-tools,tokenizer,cd}.log yreconcile-a-tools-result.json.
Sin inferencias, build, transferencia, publicación ni cambio dedespliegues.
