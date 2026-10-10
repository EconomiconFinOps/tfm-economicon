# JUP-109 — Evidencia para el apartado h de la memoria

- Tarjeta: https://trello.com/c/orFyeUW2.
- Verificación documental: 2026-10-10; base de trabajo
  `c2995a118d419dfe725247bac9c6f219a3f0ea77` (`origin/develop`).
- Copia aislada: `tfm-economicon-jup109`; rama `docs/JUP-109-evaluacion`.
- Estado: propuesta externa preparada y comprobación de fuentes; incorporación
  y aceptación del entregable pendientes. No equivale a cierre de JUP-109.
- Gobernanza aplicable: [fuente, apartados y permisos](../memoria/README.md).

## Entrega y alcance

Se preparó una propuesta para **h. Evaluación de la solución**, con nueve
párrafos identificados, tabla de resultados, fuentes fijadas por commit,
pendientes y cobertura de las tres partes pertinentes del guion.
No se copia aquí la memoria ni el texto propuesto. La propuesta se entrega
fuera de Git en
`materiales/06-entregables/JUP-109-evaluacion/propuesta-h-2026-10-10.md`,
relativa al workspace de coordinación Economicon, no al clon.
No es una exportación del documento compartido.

SHA-256 de la propuesta revisable:
`d68af45959cf43b3c3950e03706050a03fc7a5870454f0c4514b55f265b26cb7`.
Este hash identifica la propuesta local, **no una versión aceptada de la memoria**.

El guion `Guion_PJ.md` se obtuvo por el enlace de la tarjeta de coordinación
usando Google Drive el 10/10/2026. Metadata: modificación
`2026-10-09T08:24:51.390Z`. Se contrastaron entregables, requisitos
técnicos/funcionales y desglose de evaluación; no se copió el guion a Git.
Exige métricas técnicas y funcionales para h y máximo global de 20 páginas;
no fija una ponderación independiente de h. No se cotejó la transcripción
contra el PDF original.

La memoria no se ha leído ni modificado: no se dispone aquí del fragmento h
ni de la guía de estilo. La propuesta queda lista para revisión de Lucía,
antes de incorporar texto a la fuente canónica. No se han redactado ni leído
los apartados de JUP-063, JUP-110 o JUP-111.

## Evidencia que sustenta la propuesta

| Fuente / versión | Qué acredita | Límite conservado |
| --- | --- | --- |
| [JUP-067](../validation/JUP-067-metrics.md), catálogo 1.0.0 | Definiciones y calculador offline de 17 métricas | Pruebas del instrumento, no calidad real |
| [JUP-069](../validation/JUP-069-questions.json), batería 1.0.0 | 28 casos: 20 answer, 6 clarify, 2 abstain | Contextos sintéticos, muestra pequeña |
| [E1](JUP-070-run-1-report.md), `b12b3c80d0954a1f1a7bd12fae31456f269cff52`, 08/10/2026 20:13:54Z | Observaciones de la plantilla con embeddings mock | Mock sin significado semántico |
| [E2](JUP-070-run-2-report.md), `8a116df28472a30b21b996ab6fa02377dde7b2c1`, 08/10/2026 21:01:44Z | Observaciones de la plantilla con embeddings LiteLLM | Ningún modelo genera respuestas; cambia también el umbral de distancia |
| [Método y límites JUP-070](JUP-070-validation.md), [protocolo](../validation/JUP-070-evaluation.md) | Ambos informes son provisionales y «No aceptado» | Una recogida por configuración; 14 críticos sin doble juicio; crudos E1/E2 no conservados |
| [JUP-077](JUP-077-validation.md), evidencia del 25/08/2026 | Ingesta, idempotencia, aislamiento y fallo 401 con API simulada | Histórico, sin nueva ejecución ni conexión Azure real |
| [JUP-068 en ce76492](https://github.com/EconomiconFinOps/tfm-economicon/blob/ce7649264d6c67cb8df30aeac792c0001be3ce91/docs/validation/JUP-068-business-metrics.md) | Método de tiempo ahorrado, asignación y potencial | PR #68 draft; fixture no es piloto ni ahorro realizado |
| [JUP-071](https://trello.com/c/H0woDubz), consulta 10/10/2026 07:11:32Z | Alcance de robustez ante incompletitud/ambigüedad | Backlog al corte; resultado específico pendiente |

La comparación E1/E2 es descriptiva, no una estimación causal. Se mantienen
RF-070-008 (falso positivo de regla) y RF-070-011 (etiquetado manual sin
contraste), los denominadores, el intervalo Wilson y las limitaciones de
STR-1, GRD-2, disponibilidad y latencias por etapa. El cierre operativo de
JUP-070 no cambia el dictamen de sus mediciones ni acredita generación.

## Comprobaciones reproducibles de esta contribución

Entorno: Windows, Python 3.14.4 y Node.js 24.14.1.
En el workspace de coordinación:

```powershell
python materiales/07-evidencias/JUP-109-evaluacion/verify-evidence.py
```

El script externo utiliza el calculador existente y las reglas actuales sobre
los resultados sanitizados versionados. Los dos informes JSON recalculados
son estructuralmente idénticos a los originales, fijando su `generated_at`.
Los dos veredictos recalculados son `accepted: false`, por ACC-1 y ACC-2.
Resuelve los ocho enlaces GitHub a archivos fijados por commit de la propuesta
mediante `git cat-file -e`; no certifica permisos remotos de otros usuarios.

| Informe JSON original | SHA-256 |
| --- | --- |
| E1 | `11ee97ea6c6981e72f0467b45cc547cb7c5829d71d0a0ea72ab2fb80d447210d` |
| E2 | `cf1c94d6c93d9bd3d04e5fc33d1a8c3efa814c6405dcec1e89cc03af6f3cd24f` |

Resultado detallado y reproducción fuera de Git:
`materiales/07-evidencias/JUP-109-evaluacion/verification.json`.
Es una recomputación; no una nueva recogida de respuestas, puntuación humana
ni prueba del modelo. No hubo llamadas a LLM, despliegue o piloto.

Comprobaciones ejecutadas el 10/10/2026, resultado de `run-checks.py`:

| Comando en la copia aislada | Resultado |
| --- | --- |
| `python -m unittest discover -s scripts/tests -p test_assistant_metrics.py` | 103/103 correctas |
| `python -m unittest discover -s scripts/tests -p test_assistant_eval.py` | 109/109 correctas |
| `node tools/validation-questions.mjs validate` | 28 consultas y 7 categorías válidas |
| `node tools/jup-check.mjs --all` | Ocho changes activos trazables; no declara sus criterios funcionales aceptados |
| `node tools/jup-cleanup-check.mjs` | 975 archivos correctos |
| `git diff --check` | Sin errores |

Logs y resumen: `materiales/07-evidencias/JUP-109-evaluacion/checks.json`
y archivos `assistant-metrics.log`, `assistant-eval.log`, `questions.log`,
`traceability.log`, `hygiene.log`, `diff.log`. El primer intento dentro del
sandbox tuvo errores de permisos en temporales y `spawnSync git EPERM`;
la repetición fuera del sandbox pasó sin cambios al código. La suite de
métricas emite avisos de limpieza implícita de temporales en Python 3.14;
no impiden su resultado correcto.

No se añaden pruebas unitarias nuevas porque este delta es documental.
No se han ejecutado suites de producto, build/frontend ni OpenSpec en este
encargo: no hay cambios en código, dependencias, contratos o especificaciones.

## Criterios de la tarjeta

| Criterio literal | Evidencia de esta entrega | Estado |
| --- | --- | --- |
| Resultado funcional verificable | Propuesta h contrastada con guion, cifras reproducidas y fuentes | Parcial: incorporación canónica pendiente |
| Pruebas necesarias añadidas y en verde | Recomposición exacta de dos informes y suites existentes 103 + 109 correctas; no se cambia lógica de producto | Cumplido para esta contribución documental; no acredita aceptación generativa |
| Documentación y decisiones actualizadas | Este registro y [continuidad](../continuidad/evaluacion-memoria.md) | Preparadas en rama propia |
| Pull request revisado y vinculado | No hay PR JUP-109 observada en consulta del 10/10 | Pendiente del liderazgo; no se inventa revisión |
| Validación funcional y evidencia enlazadas | Fuentes y comprobaciones ligadas a sus versiones | Parcial: validación de memoria incorporada/exportada pendiente |

## Participación y siguiente paso

Roles registrados en Trello: Lucía Mateo liderazgo, Víctor Mendez
pairing/coautoría, Paris Arcos Martin revisión, Alejandro Aguado
validación/pruebas/documentación. Esta preparación no atribuye pairing,
conformidad ni dictámenes de esas personas. Tampoco actúa como validación
independiente de su propio texto propuesto.

La consulta oficial se hizo únicamente a través de
`DockerServer:/home/danteadmin/economicon-collaboration`, usando su
`TrelloClient` dentro del servicio `collaboration`.
Recibo local: `materiales/07-evidencias/JUP-109-evaluacion/trello-context.json`,
fecha `2026-10-10T07:11:32.252633+00:00`; JUP-109 seguía en Backlog,
P0 y roles/criterios originales intactos. Fecha M6 16/10/2026 pendiente de
confirmación institucional. No se convierte en fecha institucional confirmada.

Lucía conserva revisión humana previa e incorporación únicamente de h, seguida
de contraste de estilo y extensión, revisión/validación del entregable con
fecha y hash de exportación autorizada. Las reviews de documentación GitHub
no reemplazan ese registro. Este trabajo no autoriza exportar o leer la
memoria completa, ni cambia estados de otras tarjetas.

## Entrega de la contribución — 10/10/2026

Rama propia publicada: [docs/JUP-109-evaluacion](https://github.com/EconomiconFinOps/tfm-economicon/tree/docs/JUP-109-evaluacion).
Primer commit documental: `c67735bd3848336b6fcea39905238f4577d24eeb`.
No se abre una PR en nombre de la líder ni se publica un dictamen sobre el
texto preparado aquí. Descripción de PR lista para liderazgo fuera de Git:
`materiales/07-evidencias/JUP-109-evaluacion/pr-para-liderazgo.md`.

El 10/10/2026 a las 07:29:00Z se actualizó únicamente el bloque de enlaces de
JUP-109 mediante `collaboration trello-update --confirm-write` del puente
autorizado. Lectura posterior confirma descripción exacta y preservación de
nombre, lista, miembros, fechas y etiquetas; el resto de la descripción,
incluidos criterios y roles, permanece idéntico. Recibo:
`materiales/07-evidencias/JUP-109-evaluacion/trello-link-result.json`.
El enlace de evidencia apunta al commit inicial; la rama conserva la
continuidad del registro. No se movió la tarjeta ni se completaron criterios
de incorporación/revisión. No se enviaron mensajes a Discord.

Control documental adicional: 13 enlaces relativos existentes y SHA-256 de
propuesta coincidente con este registro
(`materiales/07-evidencias/JUP-109-evaluacion/document-checks.json`).
Revisión automatizada auxiliar de fuentes realizada y tres precisiones
editoriales incorporadas; no sustituye revisión humana ni participación
atribuible. La solicitud de revisión de Lucía queda pendiente, sin inferir
aprobación por el transcurso del tiempo.
