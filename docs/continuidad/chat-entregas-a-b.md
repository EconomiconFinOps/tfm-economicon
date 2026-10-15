# División de JUP-035 en A y B

Actualizado: 2026-10-15. Origen: chat 01a1270c-e332-7462-9c90-706d49ade92c.
El usuario confirma aprobación del equipo y autoriza actualizar Trello, publicar
A y cerrar #120/#121 sin integrar. No autoriza despliegue ni mensajes Discord.

## Base incorporada: A8ea5a0c4 y develop0543c5ee

Última consulta registrada previa a esta validación: PR130 OPEN/sin merge,
head8ea5a0c43d181be3206fbc1a8ff9c28788807556, base0543c5ee671cb1b400254561f5bdc6e419664510.
Se leyeron todas las reviews, conversación e inline: mismas dos solicitudes de
cambios, sin aprobación nueva ni hilos inline. CI de esta cabeza no consultada.
El segundo padre es develop0543: JUP-038/#128, explicación determinista de anomalías.
Por eso el corte11f/c30 inferior es histórico, no la base actual.

B integra develop0543 por merge local. Los dos conflictos (assistant.py y
AnswerEvidence.tsx) conservan el caller atómico/serializador y evidencia de A.
Antes del merge esos archivos coincidían con A11f; se adoptan las resoluciones
de A8ea y cinco adaptaciones de tests/fixture. Los39 archivos de aplicación del
delta coinciden por blob con A8ea. Ningún módulo semántico de B cambia; no se
copian el resumen de A ni sus estados de aceptación. Prueba externa
`reconcile-A8ea-block-identity-v1.json`; consulta `A-pre-final-2c79b32d.json`.

Backend:550 PASS/141 omisiones que requieren SQL nativo (incluye pruebas previas
de anomalías); no se afirma que ese SQL esté validado. Frontend completo1354 PASS
sin omisiones; tres typechecks, lint y build correctos, avisos previos conservados.
Recibos `A8ea-anomaly-backend-v1.{xml,log}`, `A8ea-frontend-full-v1.{xml,log}` y
`A8ea-frontend-checks-v1.json`. La ruta inicial de evidencia frontend se corrigió
moviendo sólo sus dos archivos a la carpeta externa; no se repitió la suite.
Después: regresión B7be Linux1747 recogida (1689 PASS/58 SKIP,0 FAIL/ERROR),
con tres OOM previos conservados y procesos separados sin cambiar aserciones.
Pgvector20 PASS cubre6 de esas omisiones; Cockroachv5 terminó196 ensayos con194 PASS/2 FAIL conservados. fba415f2 modifica sólo las dos pruebas; repetición completa17 SQL PASS y8 offline (2 PASS/6 SKIP), producto7be intacto. Verificador confirma1747 chat conformes con todos58 SKIP cubiertos nativamente y216 ejecuciones SQL/pgvector conformes. Helpers importados, aplicación/build y JUnit/log SHA contrastados; no es una corrida monolítica ni se borran los fallos. Buildv7 completado y B propio activo con365 hashes/tokenizer verificados y bases intactas. UI001/006/007/008 conforme en escritorio/móvil/recarga. N3 detenida8/84 por consumo incompleto de una fase de008, con reserva íntegra: cota4.790558402/5USD; una nueva ejecución exigiría5.110510402. Ocho respuestas/49 requisitos provisionales conformes no validan el conjunto. Pruebas e IDs en [evaluación local](chat-evaluacion-local.md).
No se ha publicado B ni modificado A desde este trabajo.

Actualización15/10: máximo10USD autorizado; herramientas contables5f32ea08
separadas del producto congelado7be.008 conserva su máximo íntegro, todas las
reservas previas y los ocho recibos intactos; N3 reanudada desde009, sin volver
a generar el prefijo. El bloqueo por máximo5USD del párrafo anterior es histórico.
N3 completa/aceptación siguen pendientes; ver evaluación local para estado vivo.

## Corte anterior: cabeza11f84334

Consulta posterior al bloque SQL de B: PR130 OPEN, no integrada, head
11f8433404f786c065ad35f13f673465fa26caf5 sobre develop/c30a7d0. Se leyeron todas
las reviews, conversación e inline y el diff incremental de27 archivos frente
a28ee5b1c: redes por slot; GET autenticado `/assistant/capabilities`, no-store y
booleano estricto; acceso frontend condicionado al estado efectivo y comprobación
antes de crear conversación. Añade pruebas y evidencia propia de A, no validación
semántica. Las dos reviews anteriores siguen CHANGES_REQUESTED, sin aprobación
nueva ni inline threads. Consultas de runs/status por SHA vacías: CI de esta cabeza
no verificada, sin trasladar su verde anterior.

Bloques incorporados después en B/ab66f90c86a2095039331630aa167f5f17b910bd:
20 archivos exactamente iguales a A/11f84334 y sólo la clase ChatCapabilities
adaptada sobre el esquema semántico de B, que se conserva íntegro. No se copiaron
sus resúmenes, evidencias ni OpenSpec.34 pruebas backend y120 frontend PASS;
tres typechecks, lint y build conformes (un aviso previo de hook y avisos previos
de bundle conservados). CD:58 pruebas Linux PASS, sin omisiones, y40 de topología/
workflow PASS. Carga propia de recursos backend/processor con la misma versión.

`init`/`prepare` y Compose reales renderizan ambos slots con subred/IP distintas,
HMAC reutilizado444 dentro de directorio700, loopback y puerto privado sin publicar.
No se arrancaron servicios. La coexistencia de redes en este DockerServer no se
ejecutó porque existe una red ajena172.30.0.0/16 que solapa ambos pools; no se tocó.
El root temporal con secretos de prueba fue retirado y los servicios B conservan
sus IDs/imágenes. No confundir el render y las pruebas Linux con un despliegue.
El agente CD instalado no se actualizó; eso y los rangos libres son prerrequisitos
de cualquier futura integración/despliegue, fuera de esta validación local de B.

Reconsulta de PR confirma el mismo head11f84334/basec30a7d0, OPEN y sin merge;
siguen las dos solicitudes de cambios. Ninguna aprobación o CI se trasladan a B.
Queda la aceptación independiente de A y la validación final de B, incluido navegador
sobre el candidato completo cuando se active en su entorno aislado.
Evidencia externa en PR121-local-evaluation: `reconcile-a11-assessment-v1.json`,
`reconcile-a11-block-identity-v1.json`, `reconcile-a11-linux-ab66f90c/` y
`jup122-pr130-after-reconcile-a11.json`. Los primeros3 tests de Node eran sólo
workflow por una opción omitida; la ejecución corregida cubre40, no sumarlos.

Corte de consulta previo a la incorporación: el objeto aún no estaba en B y se
descargó después por su SHA exacto. Recibos:
jup122-pr130-current-11f84334.json y jup122-pr130-11f84334-commit.json. Nada publicado
ni modificado en A desde este trabajo. Cortes de28ee5b1c siguientes son históricos.

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

## Review oficial posterior y base final pendiente — 14/10/2026

Consulta posterior conserva head28ee5b1c y develop/c30a7d0. Víctor publicó
`Revision JUP-122` a18:58:43UTC con CHANGES_REQUESTED: pide subred/IP distintas
por slot del CD (segundo despliegue solapa la red privada) y corregir la UX cuando
el backend mantiene el chat desactivado. Sus cinco puntos anteriores los da por
resueltos/no aplicables; la review no aprueba A. También advierte del orden de
actualización manual del agente CD antes del merge, sin que ese despliegue esté
autorizado ni realizado por B. Lucía aún conserva CHANGES_REQUESTED de318a56f.
Se leyeron todas las reviews/conversación/inline; no se publicaron comentarios.
Evidencia externa `jup122-pr130-current-20261014-night.json`.

B validó su base congelada mediante1470identidades únicas Linux/SQL y builds/
runtime reales, pero esas pruebas no cubrían el segundo slot ni el chat desactivado
en UI. Se reabre reconciliación1.3 para incorporar/verificar la corrección final
de A cuando esté disponible. No modificar el candidato c7 durante su campaña N3.
Ver [evaluación local](chat-evaluacion-local.md) para pruebas, costes y estados.
