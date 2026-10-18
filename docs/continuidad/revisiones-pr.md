# Política de revisiones de PR — JUP-126

Actualizado:2026-10-16. Origen:«Preparar la corrección de JUP reviews en una PR
separada de gobernanza»,chat01a12c49-7488-72f0-9077-1137c5c4f2a6.
[Trello](https://trello.com/c/SplMvNMA). Base53b43bb1; rama
fix/JUP-126-dismissed-review-titles, copia aislada.

Causa:el cómputo histórico incluye títulos desestimados;PR63 detecta solapamiento
lmatsan aunque su validación5402336106 está DISMISSED. Se propone último título
por persona/tipo;desestimado no aporta rol y no revive anterior. Historial
completo para decisiones de cambios;proceso2026-10-16 sincronizado en AGENTS y
CONTRIBUTING,spec y tests actualizados. No cambiar dictámenes ni excepciones.

[Evidencia propia](../evidence/JUP-126-validation.md):63 política,14workflow,
14gobernanza,73OpenSpec y4mutantes detectados. Fixture18reviews sólo metadatos.
CI del SHA publicado y revisión Paris/validación Víctor pendientes;Lucía pairing
asignado sin acreditar. Roles confirmados por usuario. Esta PR no acredita los
roles automáticamente ni aceptación generativa,ni autoriza merge de PR63.

Próximo:publicar PR separada,comprobar CI y solicitar ambos dictámenes,conservar
la tarjeta sin cerrar. No tocar JUP-100 cerrado ni asignaciones de PR63.

## Reconciliacion con develop — 2026-10-16

Se incorpora develop 22f0e2f3 (JUP-121/PR132) sobre 098c50aa. Unico conflicto:
el indice; conservadas ambas filas. Todos los cambios disjuntos de ambas ramas
contrastados con Git, sin diferencias. Politica, fixture y pruebas propios intactos;
CI entrante conservada, incluido evaluation-dashboard:test y timeout de20min.
Pruebas propias:63 politica,14 gobernanza,14 workflow; OpenSpec74/74,
trazabilidad7 e higiene1692 correctas. Dos avisos de whitespace proceden de
develop; diff propio contra develop limpio. CI del nuevo SHA pendiente de
publicacion. Revision favorable de Paris sobre098c50aa conserva fecha/alcance;
validacion Victor, pairing y revalidacion de dependencias pendientes. No merge
a develop, nuevas excepciones, ejecucion generativa ni cambios en dictamenes.

## Actualizacion17/10/2026

Develop ee4e8031 (PR136/JUP071) incorporado sobre e76c4c29 sin conflictos.
Politica y tests propios intactos; apps/scripts/package/CI iguales a develop.
Pruebas de politica/workflow/gobernanza, modulo evaluation_scripts y robustez
correctas; OpenSpec75/75, trazabilidad8 e higiene1710. CI del nuevo SHA pendiente.
Victor aprobo e76c4c29; Paris comento098c50aa. Los dictamenes conservan su
alcance original; comprobar su estado tras push y revalidar la nueva combinacion.
No se modifican dictamenes ni se integra la PR en develop. Pairing pendiente.

## Actualización con el colector de develop — 17/10/2026

Origen: «PR135: actualízala con develop, resuelve los conflictos y pasa las
pruebas necesarias», chat fuente 01a1270c-e332-7462-9c90-706d49ade92c.
Se reutiliza el worktree limpio `tfm-economicon-jup-reviews-governance` y la rama
existente. Base incorporada: `1de41b907f849082b0676319971775a6560b71b5`,
sobre `b2ceda79aeb7513910e6324cb22dcd42543770a6`.

Único conflicto: `README.md` de continuidad; conservadas la fila propia y la del
colector. Control de preservación: 25 archivos entrantes y 15 propios disjuntos
intactos. Workflows, package, scripts, apps y colector idénticos a develop; política,
fixture, tests y contrato JUP-126 conservan sus blobs. No se altera la política
para obtener checks verdes. El nuevo comando `chat-collector:test` permanece en CI.

Feedback leído en vivo: tres reviews, conversación y cero inline. Paris COMMENTED
favorable sobre b2ceda79; Víctor DISMISSED sobre e76c4c29, sin nueva validación.
Trello leído por el puente DockerServer: JUP-126 en 40 — En revisión, roles y
criterios conservados; pairing asignado a Lucía sin acreditación. El nuevo SHA
requiere revalidar lo afectado según CONTRIBUTING; no se trasladan dictámenes.

Pruebas y límites del candidato en [la evidencia](../evidence/JUP-126-validation.md#actualización-con-develop-del-17102026).
Recibos completos fuera de Git: `materiales/07-evidencias/PR135-actualizacion-20261017/`
en el workspace. CI del SHA publicado se documentará en la descripción de PR135;
el estado de publicación/CI de este párrafo aún es pendiente al preparar el commit.

Consulta de PR63, sin cambios: head `2b166be9`, conflicto con develop. Víctor aprobó
el 17/10 a las 15:13 UTC y levantó su solicitud; limitado a preparación offline,
no ensayo integrado. Paris COMMENTED favorable sobre ese head; Lucía confirma
atendidos sus puntos. Falta integrar autorizadamente JUP-126 antes de que la base
de PR63 tenga la regla nueva, actualizar PR63 con la base vigente conservando filas
y controles de demo/evaluación, contrastar CI push y PR (push 38976110318 falló
backend; PR 38976116287 pasó), revalidar el delta, acreditar pairing y resolver
aceptación de B/ensayo integrado. Los títulos antiguos no prueban el nuevo SHA.
La hipótesis de caducidad de tokens del backend procede de la validación de Víctor;
no se reproduce aquí ni se corrige fuera del alcance de PR135. Sin merge ni demo.


## Incorporación de PR133 integrada — 17/10/2026

Reanudación humana desde Sala de Control, chat fuente
`01a1270c-e332-7462-9c90-706d49ade92c`. GitHub confirma conflicto real
(`mergeable=false`, dirty) de `cfd52352` tras integrar PR133 a las21:08:29 UTC,
develop `466b083a6dae97f418cfb1d9156325749c6d7304`.
Se incorpora esa base una sola vez a la misma rama y worktree limpio.

Único conflicto: índice de continuidad; conservadas filas y destinos de ambos
padres (política e ingesta documental). Los69 archivos entrantes y15 propios
disjuntos mantienen su contenido antes de las notas nuevas. `.github`, apps,
scripts, package, lockfile y herramientas CD coinciden con develop. Se conserva
el nuevo paso de instalación de extracción documental en CI. El arreglo del test
backend que crea tokens durante ejecución procede íntegramente de PR133; no se
reimplementa ni se atribuye a JUP-126. Gate, fixture, contrato, tests de política
y gobernanza JUP-126 mantienen sus blobs respecto a cfd52352.

Pruebas nuevas focales: workflow14/14 sin omisiones, trazabilidad9 cambios,
higiene1764 archivos, OpenSpec estricto77/77 y diff-check correctos.
No se repiten las63 pruebas de política ni las14 de gobernanza previamente
validadas por Víctor sobre cfd52352: sus entradas pertinentes no cambian y se
comprueba identidad de blobs. CI del candidato publicado comprobará aplicación,
extracción documental y SQL con la base nueva. No campañas, inferencias,
embeddings, claves, demo, despliegues ni cambios en PR63.

Feedback completo reconsultado: cuatro reviews, tres comentarios y cero inline;
sin nueva Revision de Lucía. Víctor APPROVED cfd52352 el17/10 a las18:16:03 UTC;
ese dictamen conserva su SHA y deberá verificarse su desestimación tras el push.
Lucía sustituye a Paris en revisión según Discord y metadatos PR/Trello actuales;
Paris asignado a pairing, sin trasladarle el pairing histórico de Lucía. Sigue
pendiente la conciliación de participación real/separación de roles por liderazgo.
No se alteran dictámenes, excepciones o protecciones para obtener verde.

Publicación, CI y solicitudes de revisión/revalidación del delta: pendientes al
preparar este commit; se completan por recibo en PR135 sin push documental posterior.
Evidencia local nueva: `materiales/07-evidencias/PR135-base-20261017T2110/` del
workspace. Sólo estabilizar135; coordinar63 después por decisión humana.


## Candidato único de PR135 tras PR140 — 18/10/2026

Encargo humano de HAL 9000/Sala de Control, fuente
`01a1270c-e332-7462-9c90-706d49ade92c`: foco exclusivo135, sin tocar otras PR
ni solicitar dictámenes durante cada actualización. Checkout propio limpio en
cd2bab7f; GitHub confirma `mergeable=false/dirty`. Se incorpora una sola vez
la base real `0e686f9180d5ce195391e634a79ef2d6d3182af6` (PR140 ya integrada).

Único conflicto: índice de continuidad. Se conserva la fila JUP-126, las filas
entrantes de ingesta/colector actualizadas y todos los temas/destinos de ambos
padres. No se duplican filas compartidas ni se descarta la evidencia histórica
de sus temas. 209 archivos entrantes y15 propios disjuntos preservados;
13 rutas propias funcionales/normativas mantienen blobs respecto a cd2bab7f.
Apps, scripts, workflows, package y lockfile coinciden con la base integrada.
No cambios nuevos de producto, gate, contratos, tests o protecciones de JUP-126.

Propio nuevo: OpenSpec78/78 estricto, trazabilidad9 cambios, higiene1933 archivos,
preservación y diff-check correctos. Política63, gobernanza14 y workflow14 se
reutilizan por identidad: no se presentan como nuevas ejecuciones. Las campañas
B/N5 y evaluaciones traídas por develop conservan su autoría/fecha; no se
reproducen ni se atribuyen a esta entrega. CI/SQL obligatorios del candidato
final se documentarán en recibo por SHA, sin un push documental posterior.

Feedback reconsultado:5 reviews,5 comentarios,0 inline, sin cambios pedidos
nuevos. Lucía COMMENTED sobre cd2bab7f; Víctor cfd52352 DISMISSED, solicitud
Victorh1397 pendiente. No trasladar aceptación a la composición nueva.
[Paris aporta lectura técnica](https://github.com/EconomiconFinOps/tfm-economicon/pull/135#issuecomment-6248277341)
el18/10 09:32 UTC, expresamente sin coimplementación ni pruebas. Se conserva
ese alcance, no se acredita pairing retrospectivo.

Puente DockerServer consultado el18/10: Trello sigue en40 — En revisión con
Alejandro liderazgo, Paris pairing, Lucía revisión y Víctor validación. Los
mensajes1561325841550549005 (oferta de Paris) y1561325936773697639 (aceptación de
Lucía) no constituyen relevo formal del validador ni prueba de contribución.
El pairing histórico de Lucía no se transfiere a Paris. Sin reasignar roles ni
crear excepciones; liderazgo debe conciliar la participación real y el rol que
corresponde antes de la única ronda final de revisión/revalidación.

Estado al preparar el commit: candidato local completo; publicación/CI pendientes.
Evidencias: `materiales/07-evidencias/PR135-candidato-unico-20261018/` del workspace.
No merge, otras ramas, campañas, modelos, claves, despliegues ni Discord.


## Excepción humana acotada a PR135 —18/10/2026

La orden humana literal de HAL9000 autoriza a Lucía pairing/revisión y Paris
validación únicamente en135/JUP126. Supera la espera de decisión anterior;
Paris conserva sólo lectura técnica histórica, sin coimplementación atribuida.
Trello y body GitHub verificados por HAL9000 (recibo externo
`seguimiento-mvp/bridge-pr135-20261018T112640Z.json`); Discord ya informado,
no duplicar. Se prepara un único push necesario sobre93c0dd8f/base0e686f91.

Guardas estrictas de número/repositorio/autor/rama/base/tarjeta, roles exactos y
marcador visible; sólo lmatsan Revision y ParisArcos Validacion aportan títulos
en este caso, conservando todo el historial Request changes. Sin bypass global,
protecciones modificadas ni dispensar ambos dictámenes. Política104/gobernanza15:
119PASS sin omisiones; baseline y cuatro mutantes detectados. No se repiten suites
con entradas intactas. Detalles y logs en [evidencia](../evidence/JUP-126-validation.md#excepción-puntual-autorizada-el-18102026).

Integridad final:9 cambios,1938 archivos, OpenSpec78/78 y diff-check conformes.
Change archivado técnicamente; aceptación/publicación/CI no se simulan.
Publicado/CI todavía pendientes al preparar este commit; consultar recibo final
por SHA en PR135. El único trámite posterior a CI/SQL conforme es revisión y
validación incrementales del candidato estable. Sin merge ni otras PR.
