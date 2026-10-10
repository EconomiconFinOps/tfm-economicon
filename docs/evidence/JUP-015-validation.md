# JUP-015 — Evidencia de diseño y comprobación técnica

Fecha: 10/10/2026, Europe/Paris. [Tarjeta](https://trello.com/c/UDIyjTyl).
Base: `origin/develop` `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
Rama: `docs/JUP-015-tagging-taxonomy`, copia aislada `tfm-economicon-jup015`.
Entrega técnica: `c638b4c`. [PR #88](https://github.com/EconomiconFinOps/tfm-economicon/pull/88)
abierta en borrador contra develop; no revisada ni fusionada.

## Entrega

- [Diccionario canónico y adopción](../architecture/tagging-taxonomy.md).
- [Mínimo v1 JSON](../finops/tagging-taxonomy.json),
  [plantilla de catálogo draft](../finops/tagging-catalog-template.json) y
  [22 casos sintéticos con catálogo example](../finops/tagging-taxonomy-cases.json).
- [Verificador offline](../../tools/tagging_taxonomy.py) y
  [pruebas](../../tools/tests/test_tagging_taxonomy.py), incorporados a CI/OpenSpec.
- [ADR propuesto](../adr/ADR-0018-tagging-taxonomy.md) y OpenSpec trazable a JUP-015.

Se consultó la descripción completa del snapshot de despacho y se contrastó
Trello por `DockerServer:/home/danteadmin/economicon-collaboration` usando
`TrelloClient` en `docker compose run --rm -T --entrypoint python collaboration -`.
JUP-015 seguía en Backlog con las mismas cinco etiquetas y roles. JUP-017 declara
el mínimo v1 aprobado por el usuario y catálogos organizativos futuros, no un
catálogo corporativo aprobado. La PR66 fue inspeccionada en el head
`6e25b308d9a890f9b73e4df7a55d904ae34b0065`. No se modifica su rama.

## Matriz por criterio de Trello

| Criterio original | Evidencia de esta entrega | Estado y límites |
| --- | --- | --- |
| Resultado funcional verificable | Diccionario, catálogos y 22 escenarios ejecutables; distinción equipo/aplicación/unidad/etiqueta | Diseño comprobable offline; no integración productiva |
| Pruebas necesarias añadidas y en verde | Suite unittest, casos, checks de gobernanza y OpenSpec | Resultados técnicos abajo; no sustituyen validación humana |
| Documentación y decisiones actualizadas | Taxonomía, ADR, OpenSpec y continuidad | ADR Proposed; no ratificación inferida |
| Pull request revisado y vinculado | Rama y borrador de contribución preparados para liderazgo | Revisión independiente pendiente; no marcar cumplido |
| Validación funcional y evidencia enlazadas | Este documento y comandos reproducibles | Evidencia técnica sintética; Validacion JUP-015 de Lucia pendiente |

## Verificaciones ejecutadas

Entorno: Windows, Python 3.14.4, Node 24.14.1, Git 2.56.0.windows.2.
La suite de referencia sólo usa la biblioteca estándar; CI ejecutará Python 3.12.

| Comando | Resultado |
| --- | --- |
| `python tools/tagging_taxonomy.py --cases docs/finops/tagging-taxonomy-cases.json` | 22 PASS |
| `python -m unittest discover -s tools/tests -p test_tagging_taxonomy.py -v` | 26 PASS, 0 fail; ejecución permitida fuera del sandbox tras PermissionError de temporales Windows |
| `node --test tools/jup-check.test.mjs tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs tools/jup-cleanup-check.test.mjs` | 95 PASS, 0 fail |
| `node tools/jup-check.mjs --all` | 9 changes trazables, incluido JUP-015 |
| `node tools/jup-cleanup-check.mjs` | PASS; el primer intento falló por `spawnSync git EPERM` del sandbox; ejecución permitida posterior pasó |
| `openspec validate --all --strict --no-interactive` | 56 PASS, 0 fail antes y después del archivo |
| `git diff --check` | PASS |

La revisión técnica asistida adicional no encontró defectos accionables; no es
una review humana. OpenSpec se archivó el 10/10 y se promovió la especificación
`tagging-taxonomy`; se corrigieron enlaces y Purpose tras el archivo. El archivo
del change no significa aceptación organizativa, merge ni cierre de tarjeta.

OpenSpec 1.8.0 se ejecutó con el binario ya instalado en el checkout vecino,
`node ../tfm-economicon/node_modules/@fission-ai/openspec/bin/openspec.js`, sin
modificarlo. Para tests de gobernanza se copió `yaml` ya instalado a node_modules
de la copia aislada; no se cambió ningún manifiesto/lockfile.

Casos adversos incluyen etiquetas ausentes y extras, no sustitución de entidades,
marcadores, tipos, 128/129 caracteres, alias/case de entorno, case de IDs,
catálogo ajeno o caducado, límite inclusivo/exclusivo, mapping ausente,
referencias colgantes, duplicados JSON y mutaciones de la política v1.
Los tests CLI comprueban también códigos de error, no sólo salidas felices.

Se contrasta además la igualdad de `POLICY_VERSION`, `REQUIRED_TAGS`,
`INVALID_VALUES` y `ENVIRONMENTS` con el AST de `app/core/tag_policy.py` en PR66;
Resultado: PASS. Es paridad de constantes, no ejecución SQL ni prueba de equivalencia Unicode
entre Python y CockroachDB. Los límites ASCII y los ejemplos ordinarios de trim
están cubiertos; no se afirma equivalencia universal de motores regex.

## Participación y pendientes

Publicación comprobada el 10/10: PR88 draft, MERGEABLE, base develop. CI técnica
[38034907273](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38034907273)
7/7 verde en `c638b4c` (incluye nuevos tests Python 3.12, servicios y frontend).
`JUP reviews` sigue pendiente de las reviews humanas; no se considera verde ni
se modifica ese control. Los posteriores commits de este registro son documentales.

Evidencia enlazada en Trello por el puente oficial el 10/10 07:37:52Z,
action `6ac9eb50c8c89dfec635a3e7`, con texto devuelto por la operación.
No se modificaron descripción, criterios, prioridad, fechas, roles o columna.

Roles registrados: Paris Arcos Martin liderazgo, Victor Mendez pairing,
Alejandro Aguado revisión, Lucia Mateo validación/pruebas/documentación.
Esta contribución técnica asistida no acredita pairing ni un dictamen de ninguno.
La cuenta de publicación no cambia automáticamente las asignaciones: el liderazgo
debe regularizar cualquier incompatibilidad entre autor y revisor antes de ready.
El autor de una PR no puede ser su revisor independiente. No se solicita merge.

No se han verificado: catálogos reales, autenticidad de aprobaciones, relaciones
entre aplicación/proyecto/centro/equipo, selección automática entre snapshots,
runtime/API/UI/SQL de consumidores ni costes reales. Los ejemplos `approved` en
unittest son dobles de prueba identificados como sintéticos. No prueban aprobación.
No hay cambios de fixtures públicos, datos productivos, prioridades, fechas o roles.

Para adopción: liderazgo obtiene catálogos y su referencia de aprobación; los
responsables de 017/027/028/037 integran y prueban el contrato en sus ramas. La
ausencia de esos datos se conserva como pendiente, nunca como entidad inventada.
