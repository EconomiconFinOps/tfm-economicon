# JUP-126 — Corrección de títulos desestimados

Fecha:2026-10-16. [Trello](https://trello.com/c/SplMvNMA).
Base:develop53b43bb1e79b08967cc1b9efdf66669f11e8197c.
Rama:fix/JUP-126-dismissed-review-titles.

## Problema y cambio
PR63 cuenta la Validacion desestimada5402336106 de lmatsan junto con su Revision
complementaria5513541546 y exige una excepción inexistente. La regla anterior,
su test y la spec JUP-100 contaban descartadas: se cambia explícitamente ese
contrato de gobernanza, sin editar ningún dictamen.

Último título por persona/tipo/tarjeta, descartado después de seleccionar el
último. No se recupera un título anterior si el último está DISMISSED. Historial
completo y cálculo de solicitudes de cambios preservados. Los roles asignados,
comentarios complementarios y acuerdos siguen sujetos al proceso humano.

## Comprobaciones propias

| Comando | Resultado |
| --- | --- |
| corepack pnpm pr:check:test |63/63 PASS |
| corepack pnpm ci:check:test |14/14 PASS |
| corepack pnpm repository:governance:test |14/14 PASS |
| corepack pnpm jup:check:test |PASS |
| corepack pnpm jup:check:all |PASS |
| corepack pnpm jup:cleanup:check |PASS |
| corepack pnpm openspec:validate |73/73 PASS |

Cuatro mutantes aislados detectados por fallo de tests:contar DISMISSED,
filtrarlas antes de seleccionar (resurrección),quitarlas del historial completo
(resurrección de Request changes),permitir que COMMENTED levante Request changes.
El código candidato no se modifica durante esas ejecuciones.

Fixture `tools/fixtures/pr-reviews/pr63-20261016.json`:18reviews,primera línea,
login,estado y fecha del corte observado sobre39baec24. El cuerpo de la PR se
vacía deliberadamente:reproduce que NO hay excepción. El original produce el
error de solapamiento;el candidato no. No contiene contenido probatorio de las
reviews y no sirve para validar sus conclusiones. Prueba del original conservada
en el prototipo local del16/10;test de regresión ejecutado en esta rama.

Dependencias instaladas desde lockfile con caché offline,sin cambios de lockfile.
Logs locales:materiales/07-evidencias/JUP-reviews-gobernanza-2026-10-16/ del workspace.
CI remota del SHA publicado pendiente al redactar;el recibo final se enlaza en PR.
No se ejecuta runtime/LLM ni despliegue:el diff afecta sólo política y documentación.

## Revisión y límites
Roles confirmados por el usuario:Alejandro liderazgo,Lucía pairing,Paris revisión,
Víctor validación. No se acredita pairing realizado ni dictámenes de esta PR.
Los resultados anteriores son evidencia propia, no Revision/Validacion oficiales.
El archivo técnico de OpenSpec no implica aceptación de la política.

El check no vincula nombres libres a logins ni interpreta contenido favorable,
SHA vigente o autorización para merge. Sigue sujeto a roles de Trello y punto7
de CONTRIBUTING. No relaja solapamiento vigente sin excepción,errores de API,
autor/borradores ni solicitudes de cambios de revisores complementarios.
PR63 tiene validación de Víctor sobre39baec24;esta corrección no sustituye la
revisión de Paris ni acredita ensayo generativo. No merge ni modificación de
PR63/dictámenes,excepciones,permisos,workflow,rulesets o mensajes Discord.

## Actualización con develop del 17/10/2026

Evidencia propia de actualización, independiente de los dictámenes de Paris y
Víctor. Head previo `b2ceda79aeb7513910e6324cb22dcd42543770a6`; develop incorporado
`1de41b907f849082b0676319971775a6560b71b5`. Node 24.14.1, Python 3.14 y pnpm 9.0.0.

Único conflicto, `docs/continuidad/README.md`: unión de temas por destino,
conservando la fila JUP-126 y la del colector JUP-123. Los 25 archivos entrantes
disjuntos y los 15 propios disjuntos mantienen su contenido. `.github`, `package.json`,
`scripts`, `apps` y colector coinciden con develop. El gate, sus tests, fixture y
contrato JUP-126 no cambian. `tools/team-contributions.py` consume prefijos de títulos
para atribuir intervenciones históricas; conserva reviews desestimadas a propósito,
no decide los roles del gate. Su suite se ejecuta como control del consumidor.

| Comprobación nueva | Resultado |
| --- | --- |
| `node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 91/91 PASS: 63 política, 14 workflow, 14 gobernanza; sin omisiones |
| `corepack pnpm chat-collector:test` | 48/48 PASS |
| `corepack pnpm assistant-robustness:validate` | 16 perturbaciones, 29 casos, hashes correctos |
| `corepack pnpm assistant-robustness:test` | 130/130 PASS |
| `corepack pnpm evaluation-dashboard:test` | 1846 ejecutadas: 1842 PASS, 4 fallos de montaje Docker Windows/Linux; cero omisiones |
| Cuatro casos PromQL mediante archivos copiados al contenedor | PASS con mismos fixtures y valores esperados; no es un nuevo 1846/1846 |
| `corepack pnpm contributions:test` | 28/28 PASS |
| `corepack pnpm jup:check:test` | 7/7 PASS |
| `corepack pnpm jup:check:all` | 9 cambios activos correctos |
| `corepack pnpm jup:cleanup:test` | 6/6 PASS |
| `corepack pnpm jup:cleanup:check` | 1724 archivos correctos |
| `corepack pnpm openspec:validate` | 76/76 PASS estricto |
| `git diff --check` (trabajo, índice y contra develop) | PASS |

El primer intento de Node fue bloqueado por EPERM del sandbox; repetido con permiso
de subprocesos, pasa. Logs completos y snapshots filtrados en
`materiales/07-evidencias/PR135-actualizacion-20261017/` fuera del repositorio.
La suite completa de evaluación falla sólo en cuatro casos de PromQL por
`docker: invalid mode: /t`: intenta montar un directorio temporal de Windows en
el daemon Linux. El archivo es idéntico a develop. Se ejecutan los cuatro casos
con las mismas expresiones, series y valores esperados del módulo original,
mediante `docker create`, copia de un tar a `/t`, `docker start -a` y eliminación
del contenedor propio: promtool SUCCESS. El primer fallo se conserva; no se
cambian tests ni se presenta como una suite completa verde. Los 28 tests del
consumidor de contribuciones pasan. La CI Linux confirmará la ejecución ordinaria.
No se presentan campañas previas de mutación o historiales aleatorios como nuevas.

Con snapshots de GitHub del 17/10, invocación sin red del `checkReviews` candidato:
PR135 falla únicamente por falta de `Validacion JUP-126`; PR63 no devuelve errores
de títulos/solicitudes. Esto no ejecuta Actions ni valida las conclusiones de las
reviews. La nueva Approve de Víctor sobre PR63 levanta su Request changes y sigue
limitada a preparación offline. No se altera PR63, reviews, excepciones ni roles.

No se ejecutan campañas LLM, modelos, embeddings, demo integrada ni despliegue.
La batería general de aplicación y build se comprueba con la CI del SHA publicado:
las rutas de aplicación son idénticas a develop. Se conservan los dos enlaces
rotos del índice heredados de develop; no se corrigen temas fuera de alcance.
CI publicada y SQL aún pendientes al preparar este commit; consultar el recibo
final de PR135. Paris COMMENTED sobre b2ceda79; Víctor DISMISSED sobre e76c4c29,
nueva validación y pairing pendientes. No merge autorizado en este encargo.


## Reconciliación tras integrar PR133 — 17/10/2026

Head anterior `cfd52352072fb8a9a1368c6843675c9487f7954b`; base incorporada
`466b083a6dae97f418cfb1d9156325749c6d7304`. GitHub confirmó conflicto real.
Único conflicto: índice de continuidad, resuelto con unión de temas/destinos.
69 archivos entrantes y15 propios disjuntos preservados. Apps, scripts, workflows,
package, lockfile y CD son idénticos a develop; JUP-126 funcional y normativo
mantiene sus blobs. No se modifica producto, política o configuración fuera
de lo ya integrado en develop. La nueva extracción documental y la corrección
de tokens de test del backend pertenecen a PR133.

| Ejecución propia nueva | Resultado |
| --- | --- |
| `corepack pnpm ci:check:test` | 14/14 PASS, cero omisiones |
| `corepack pnpm jup:check:all` | 9 cambios activos correctos |
| `corepack pnpm jup:cleanup:check` | 1764 archivos correctos |
| `corepack pnpm openspec:validate` | 77/77 PASS estricto |
| Preservación de ambos padres y `git diff --check` | PASS |

Se reutilizan por identidad las pruebas de política/gobernanza que Víctor validó
sobre cfd52352; no se presentan como ejecuciones nuevas. No se repiten campañas
de evaluación, robustez, mutación o inferencias sin cambio de entradas. Pruebas
de aplicación/build/SQL y gobernanza general: CI obligatoria del SHA publicado,
pendiente al preparar el commit. No demo, gasto de modelos, claves o despliegue.
Logs: `materiales/07-evidencias/PR135-base-20261017T2110/` del workspace.
La aprobación cfd52352 no se atribuye al nuevo candidato; el recibo final de
PR135 registra su estado y las solicitudes incrementales a Lucía/Víctor.


## Candidato único con la base PR140 — 18/10/2026

Base incorporada: `0e686f9180d5ce195391e634a79ef2d6d3182af6`; head previo
`cd2bab7fc69eafde7aaeeb43ee14a82874a02b44`. Conflicto real sólo en índice,
resuelto por unión de temas/destinos y estados entrantes de las filas compartidas.
209 archivos entrantes y15 propios disjuntos preservados. Las13 rutas propias
funcionales/normativas JUP-126 no cambian de blob. Apps/scripts/.github/package/
lockfile idénticos a la base; sin modificaciones nuevas de producto o política.

| Nueva comprobación propia | Resultado |
| --- | --- |
| `corepack pnpm jup:check:all` | 9 cambios activos correctos |
| `corepack pnpm jup:cleanup:check` | 1933 archivos correctos |
| `corepack pnpm openspec:validate` | 78/78 PASS estricto |
| Preservación/identidad de blobs/unión de destinos y diff-check | PASS |

Se reutilizan las63 pruebas de política,14 de gobernanza y14 de workflow
previamente conformes por identidad de sus entradas. No nuevas campañas,
mutaciones, inferencias, embeddings o pruebas de demo. Los resultados históricos
B/N5 traídos por develop no son ejecuciones de este encargo. CI/SQL obligatorios
del SHA publicado pendientes al preparar el commit; recibo final en PR135.
No nuevas solicitudes de dictámenes durante la preparación: después corresponde
coordinar una sola ronda sobre el candidato estable, con responsabilidades reales.
La lectura técnica de Paris no se convierte en coimplementación o validación;
los mensajes de oferta/aceptación no se interpretan como relevo formal.
Logs y snapshots filtrados: `materiales/07-evidencias/PR135-candidato-unico-20261018/`.


## Excepción puntual autorizada el 18/10/2026

Origen: PR135/JUP-126, chat custodio `01a14ab7-fc75-7e20-ab29-610d85739b5c`,
orden humana transmitida por HAL9000 (`01a1270c-e332-7462-9c90-706d49ade92c`):
«Autorizo la excepción puntual para que Lucía mantenga pairing y revisión en la
PR135, con Paris en validación. Déjalo documentado y desbloquea el cierre sin
tocar las demás PR». Esta decisión supera el bloqueo de separación descrito
antes; no modifica la atribución real ni concede autorización de merge.

El ajuste se activa únicamente con número autoritativo135, repositorio
`EconomiconFinOps/tfm-economicon`, autor `iber1to`, título e ID JUP-126,
rama `fix/JUP-126-dismissed-review-titles`, base `develop`, roles exactos
Alejandro/Lucía/Lucía/Paris y una única declaración visible literal de
CONTRIBUTING. Sólo `lmatsan` aporta Revision y `ParisArcos` Validacion en este
caso. Se conserva el último título por persona/tipo y todo el historial para
resolver Request changes; Comment no los levanta. Autor, borradores y títulos
desestimados no aportan roles; ambos dictámenes siguen siendo obligatorios.
Otras PR y la excepción general revisión/validación mantienen sus reglas.

Paris aportó lectura técnica, sin coimplementación ni pruebas; el pairing
histórico corresponde a Lucía (comentario6237440991). La excepción consta en
el body GitHub y en Trello por el puente DockerServer: recibo local
`materiales/07-evidencias/seguimiento-mvp/bridge-pr135-20261018T112640Z.json`
del workspace, verificado por HAL9000 tras recuperar el puente. No se duplica
escritura ni aviso Discord1561335717538566267.

| Comprobación propia del ajuste | Resultado confirmado el18/10/2026 |
| --- | --- |
| Política104 + gobernanza15 | 119/119 PASS, cero omisiones |
| Nuevas regresiones sobre baseline93c0dd8f | 9 fallos esperados |
| Mutantes sin número / marcador visible / identidades / historial completo | 5 /19 /6 /1 fallos detectados |
| Snapshot real con body autorizado | Política conforme; sólo falta Validacion JUP-126 |
| Mismo snapshot con validación Paris hipotética | Sin errores; simulación, no dictamen publicado |

Logs reproducibles fuera de Git, en
`materiales/07-evidencias/PR135-candidato-unico-20261018/` del workspace:
`scoped-final-tests.log`, `scoped-final-counterfactuals.json`,
`counterfactual-final/` y `scoped-live-snapshot-result.json`.
Los119 tests ya ejecutados se conservan sin repetir al no cambiar sus entradas.
Integridad final confirmada: trazabilidad9 cambios activos, higiene1938 archivos,
OpenSpec78/78 estricto y diff-check conformes. Archivo técnico del change
`2026-10-18-jup-126-pr135-authorized-exception` con publicación/CI aún pendientes;
no implica aceptación ni merge. Publicación y CI/SQL se completan con el recibo
por SHA de PR135; no se presentan como conformes antes de publicarse. La base continúa
0e686f91 y el candidato anterior93c0dd8f conserva su evidencia histórica.
Apps, workflows, scripts, dependencias y lockfile permanecen idénticos a ese
candidato; la CI obligatoria comprueba el árbol completo. Sin otras PR,
campañas, modelos, claves, despliegue o merge. Tras CI/SQL conforme corresponde
una sola ronda de revisión/revalidación del delta sobre el nuevo SHA, sin
atribuir aceptación nueva a reviews históricas.


## Reconciliación tras integrar PR134 —18/10/2026

Origen: petición humana transmitida por HAL9000, fuente
`01a1270c-e332-7462-9c90-706d49ade92c`, chat custodio
`01a14ab7-fc75-7e20-ab29-610d85739b5c`. Lucía pide actualizar135 para volver a
aprobar. GitHub confirma conflicto de5f9dac36 tras PR134; `git ls-remote` y fetch
confirman develop real `79aa76be6148d12e59ac55693b8c933546182ef8`, aunque el
baseRefOid de la PR aún mostraba0e686f91. Se integra esa base una sola vez.

Único conflicto en índice: unión de la fila135 y chunking134. Se conservan las
correcciones entrantes de dos enlaces históricos rotos hacia evidencia JUP-068 y
JUP-017;34 destinos activos, sin perder temas. Antes de notas nuevas,204 archivos
entrantes y20 propios disjuntos mantienen blobs. Apps/scripts/.github/package/
lockfile coinciden con develop79aa76be; los cambios de chunking, tokenizer,
citas y evidencias C10/C14 proceden íntegramente de134, sin modificarlos.
La política, fixture, tests, AGENTS, CONTRIBUTING y spec de JUP-126 mantienen
sus blobs respecto a5f9dac36; excepción puntual y roles intactos.

Nuevas comprobaciones: workflow14/14 sin omisiones (entra preparación de tokenizer
embedding en CI), trazabilidad9 cambios, higiene2109 archivos, OpenSpec79/79
estricto y diff-check conformes. Se reutilizan119 pruebas política/gobernanza por
identidad de todas sus entradas: no se anuncian como ejecución nueva ni se
repiten contrafactuales/campañas. La CI/SQL obligatoria comprobará el árbol
publicado. Sin inferencias, modelos, claves, demo o despliegue.

Leídas8 reviews,7 comentarios y0 inline antes de integrar. Paris publicó
Validacion5562892839 COMMENTED favorable sobre5f9dac36; Lucía Revision5563180135
COMMENTED y5563235772 APPROVED sobre ese mismo SHA (18/10 13:45:59UTC).
La aprobación existe; no se presenta como pendiente en5f9. Conserva su alcance
histórico tras el push y no acredita automáticamente el candidato reconciliado.
Las observaciones no bloqueantes de Lucía no se corrigen en esta actualización.
Tras CI/SQL conforme: Lucía reaprueba una vez y Paris confirma sólo compatibilidad
del delta/base/workflow afectado, reutilizando evidencia vigente. Sin merge ni
otras PR/ramas; HAL9000 coordina Discord, no se duplica ningún aviso.

Estado al preparar el commit: reconciliación completa local; publicación y
checks por SHA pendientes, se completan en recibo PR135 sin otro push documental.
Recibos externos: `materiales/07-evidencias/PR135-base-PR134-20261018/` del workspace;
`preservation-before-docs.json`, `workflow.log`, `trace.log`, `hygiene.log`,
`openspec.log` y snapshots de reviews/conversación.
