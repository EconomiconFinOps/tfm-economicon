# JUP-071 — Evidencia de robustez

Verificación: 10/10/2026, Europe/Paris. [Tarjeta](https://trello.com/c/H0woDubz).
Base `origin/develop`: `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
Contribución técnica en `test/JUP-071-robustness`; no dictamen humano independiente.

## Resultado y alcance

Se añaden 16 variantes con 13 referencias JUP-069 (29 casos), un runner que
reutiliza JUP-070 y dos ejecuciones del servicio de plantilla real. El JSON fija
hashes del corpus, batería original y metodología. Se prueban owner ausente,
null/vacío, valores desconocidos, reglas contradictorias, reparto compartido,
denominadores, periodos, monedas/unidades, ingesta parcial y acceso inexistente.
Tres variantes `answer` impiden considerar acertada una abstención universal.

| Ejecución | Total | Pass | Fail numérico | Blocked | Not run | Juicio semántico |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Plantilla con fragmento fijo](JUP-071-template-fixed-report.json) | 29 | 0 | 8 | 0 | 21 | Pendiente |
| [Plantilla sin contexto](JUP-071-template-empty-report.json) | 29 | 0 | 8 | 0 | 21 | Pendiente |

También quedan juicios pendientes en los ocho casos con fallo conocido. Los
resultados no son una tasa de alucinación ni una evaluación humana. En modo fijo
el servicio repite el prompt en los 29 casos; en vacío entrega el mismo aviso sin
contexto. Las cifras requeridas no se obtienen de ese eco. No se ejecutan red,
gateway, embeddings, base de datos o modelo. No hubo carga ni modificación de
datos de aplicación. Los dos perfiles no son tres repeticiones equivalentes.

## Trazabilidad por criterio de Trello

| Criterio original | Entrega / evidencia | Pendiente |
| --- | --- | --- |
| Resultado funcional verificable | Runner ejecutable, 29 casos emparejados, informes anteriores y [protocolo](../validation/JUP-071-robustness.md) | Campaña generativa real |
| Pruebas necesarias añadidas y en verde | `scripts/tests/test_assistant_robustness.py`, validación de suite y checks indicados abajo | CI y validación independiente al publicar |
| Documentación y decisiones actualizadas | Protocolo, OpenSpec activo, este informe y continuidad | Cambios de procedencia cuando JUP-035 esté integrado |
| Pull request revisado y vinculado | Contribución propia preparada para Paris, liderazgo registrado | Revisión humana y PR de integración, sin suplantar roles |
| Validación funcional y evidencia enlazadas | Ejecuciones locales e informes sanitizados reproducibles | Lucía valida criterios; no se le atribuye ejecución alguna |

## Dependencia JUP-035 y roles

Lectura oficial el 10/10/2026 mediante `DockerServer:/home/danteadmin/economicon-collaboration`,
cliente `Settings/TrelloClient` dentro del servicio `collaboration`:
JUP-071 sigue Backlog, sin cambios desde 11/08; JUP-035 está Preparado, actualizada
08/10. Su alcance exige conectar el chat al modelo y ejecutar JUP-069. La copia
inspeccionada conserva `apps/backend/app/services/assistant.py` como plantilla;
no se encontró PR JUP-035 abierta en la consulta inicial. Eso describe este corte,
no el trabajo posterior de otros chats.

Roles preservados: Paris liderazgo, Víctor pairing, Alejandro revisión, Lucía
validación/pruebas/documentación. La contribución técnica propia no acredita
pairing ni reemplaza los dictámenes; Alejandro no puede revisar independientemente
su propio código. Paris debe gestionar la integración y la independencia de la
revisión según `CONTRIBUTING.md`. No se mueve Trello, cambia prioridad, completa
checklists ni declara Hecho desde esta contribución.

## Reproducibilidad y verificaciones

Versiones locales: Windows, Python 3.14.4, Node 24.14.1, pnpm 9.0.0. La CI usa
Python 3.12/Node 22; no confundirlas con las versiones comprobadas localmente.
El JSON de cada ejecución incluye hora UTC, commit base, hash del servicio,
suite, runner/evaluador/reglas y configuración. El commit base no contenía todavía
este runner: los hashes de archivos identifican el código evaluado antes del commit.

Crudos y hoja privada están fuera del repositorio, en
`../materiales/07-evidencias/JUP-071-robustness-2026-10-10/` (fixed/empty-raw.json,
fixed-review.md, fixed-judgments.json). Los juicios quedan vacíos; no se inventan
personas o aceptación. Los informes versionados no contienen respuestas, claves
ni nombres de quienes juzgan. La ficha de una recogida real es privada y sólo se
exporta su hash; no registrar secretos allí tampoco.

Comandos reproducibles en el protocolo. Verificaciones ejecutadas:

| Comprobación | Resultado |
| --- | --- |
| `python tools/assistant-robustness.py validate` | 16 variantes / 29 casos; hashes válidos |
| `python -m unittest discover -s scripts/tests -p test_assistant_robustness.py -v` | 38 pruebas OK |
| `python -m unittest discover -s scripts/tests -p test_assistant_eval.py -q` | 109 pruebas OK |
| `python -m unittest discover -s scripts/tests -p test_assistant_metrics.py -q` | 103 pruebas OK |
| `node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs tools/validation-questions.test.mjs` | 90 pruebas OK |
| `corepack pnpm openspec:validate` | 56 items OK, modo estricto |
| `corepack pnpm jup:check:all` | 9 cambios trazables OK |
| `corepack pnpm jup:cleanup:check` | OK |
| `node tools/validation-questions.mjs validate` | 28 originales y fuentes intactos |
| `python -m compileall -q tools/assistant-robustness.py scripts/tests/test_assistant_robustness.py` y `git diff --check` | OK |
| `corepack pnpm test` / `corepack pnpm build` | Bloqueados por `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY` del pnpm fallback invocado por Turbo; no acreditan el conjunto del workspace |

Los intentos iniciales dentro del sandbox fallaron por permisos de procesos
hijos/temporales Windows. Las suites indicadas como OK se repitieron fuera del
sandbox sin cambiar sus expectativas. Instalación fijada: `corepack pnpm install
--frozen-lockfile` OK; el intento `--offline` previo no tenía todos los paquetes.
Los logs globales contienen un resultado de Azure API reproducido desde caché de
otro worktree; no se contabiliza como ejecución propia. Logs específicos y
globales conservados junto a los crudos privados. No se modificó Turbo/pnpm para
resolver un problema ajeno a JUP-071.

## Límites y siguiente paso concreto

La separación `template_mock`/`live_unverified` es deliberada: el endpoint no
atestigua generación. La recogida HTTP reutilizada dispone de pruebas con doble
explícito, pero no se ha ejecutado esta campaña contra un despliegue real. La
evaluación semántica sigue dependiendo de personas; las comprobaciones numéricas
son las de JUP-070 con sus limitaciones documentadas. No se afirma cobertura
completa de ambigüedad, relevancia de retrieval, latencia ni ausencia de alucinación.

Paris puede integrar la contribución revisada; después de JUP-035, ejecutar tres
campañas reales con idéntica configuración, entregar la hoja a dos personas y
contrastar cada punto antes de concluir robustez. El cierre requiere además PR
revisada/integrada y evidencia enlazada por quien lidera.
