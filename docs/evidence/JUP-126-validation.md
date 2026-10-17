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
