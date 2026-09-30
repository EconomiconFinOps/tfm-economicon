# Evidencia de validacion JUP-100

- Fecha: 2026-09-30.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `docs/JUP-100-review-validation-flow` hacia `develop` (base `2efef1a`).
- Tarjeta: https://trello.com/c/XlWNnm7r.
- Change: [`jup-100-review-validation-flow`](../../openspec/changes/jup-100-review-validation-flow/proposal.md).
- Liderazgo: Lucia Mateo; pairing: Paris Arcos Martin; revision de PR: Victor Mendez; validacion, pruebas y documentacion: Alejandro Aguado.
- Entorno: Windows 10, Node.js 24 (la CI usa el Node del runner de GitHub).

## Alcance

- `CONTRIBUTING.md` define los cuatro roles (que hace, cuando, que entrega, que no le corresponde, reasignaciones) y el flujo de revision, validacion y merge.
- Check obligatorio `JUP reviews` en `.github/workflows/pr-reviews.yml`, que reutiliza `tools/pr-policy.mjs --reviews` y lee las reviews por la API.
- `AGENTS.md` con las reglas que el check no puede comprobar y la misma `Process version` que CONTRIBUTING; plantilla de PR con el checklist; gobernanza actualizada; ambos rulesets con ocho checks.

## Fase RED

- `tools/pr-policy.test.mjs` con un esqueleto sin logica (`checkReviews` sin errores, lectura de la API vacia): 18 tests nuevos fallan por comportamiento; los que esperan "sin errores" pasan como es logico, y los 11 de "JUP policy" siguen pasando.
- `tools/ci-workflow.test.mjs`: fallan los contratos de `pr-reviews.yml` y los ocho checks en ambos rulesets; pasa el guardian de que `ci.yml` no reacciona a reviews.
- `tools/repository-governance.test.mjs`: fallan los 6 contratos nuevos (roles, flujo, Process version, AGENTS.md, plantilla, gobernanza); pasan los 5 existentes.
- Comando `--reviews` sin implementar: fallan los 2 tests que lo ejecutan como proceso (API inalcanzable y falta de token).

## Fase GREEN

| Comando | Resultado |
|---|---|
| `corepack pnpm pr:check:test` | 56 passed (39 antes de las correcciones de la revision adversarial) |
| `corepack pnpm ci:check:test` | 10 passed |
| `corepack pnpm repository:governance:test` | 12 passed |
| Resto del job "OpenSpec" de la CI (`jup:check:test`, `roadmap:test`, `jup:check:all`, `jup:cleanup:test`, `jup:cleanup:check`, `openspec:validate`, `docker:validate`, `collaboration:test`, `assistant-corpus:test`, `assistant-corpus:validate`, `validation-questions:test`, `validation-questions:validate`, `llm-gateway:test`) | todos correctos; `openspec:validate` 35/35 |
| `corepack pnpm jup:check -- --change jup-100-review-validation-flow` | correcto |

## Controles positivos

- Mutantes de `checkReviews`, uno a uno, todos detectados: contar reviews del autor, contar borradores, ignorar cambios pendientes, titulo sin anclar ni limite de identificador, no ordenar por fecha, no exigir la excepcion, dejar que un Comment limpie un Request changes, dar por buena una respuesta de error de la API.
- El mutante "no ordenar por fecha" sobrevivio a la primera version del test (la lista daba el mismo resultado ordenada o no); se rehizo el test y ahora lo detecta.
- `ci.yml` con evento `pull_request_review`: el test lo rechaza.
- `Process version` distinta en `AGENTS.md` y CONTRIBUTING, y nombrar un asistente en `AGENTS.md`: el test de gobernanza falla en ambos casos.
- La plantilla de PR, pegada tal cual en la descripcion, no declara la excepcion de misma persona (la linea va dentro de un comentario HTML).
- "JUP policy" sin exigir la linea de excepcion para aceptar la misma persona en revision y validacion: fallan 2 tests.

## Correcciones de la revision adversarial

Cada hallazgo corregido se reprodujo primero con un test en rojo:

- Pasada 1: una aprobacion descartada por un push ya no revive un Request changes anterior; logins sin mayusculas en la ultima decision; excepcion en comentarios HTML no cuenta; todos los errores enlazan con URL absoluta; el mensaje explica el titulo en texto plano; CONTRIBUTING explica como levantar un Request changes.
- Pasada 2: la excepcion exige la linea completa y fuera de bloques de codigo; errores de API y token enlazan al flujo; la guia de proteccion de ramas lista los ocho checks con test contra los rulesets; checklist de la plantilla completo; "JUP policy" acepta tres personas con la excepcion declarada (opcion A) y un PR honesto con la excepcion pasa ambos checks.
- Pasada 3 (accept): la excepcion solo cuenta si GitHub la muestra como texto normal (fuera de comentarios sin cerrar, bloques `~~~` o sangrados y codigo sangrado); "JUP policy" rechaza la excepcion con nombres distintos; se exige la declaracion siempre que alguien publique ambas reviews; nombres comparados sin acentos ni `@`; AGENTS.md menciona la linea de excepcion. Mutantes de la excepcion con nombres distintos y del codigo sangrado detectados.
- Riesgos aceptados por Lucia y documentados en CONTRIBUTING: el check ejecuta el codigo del propio PR; el check no verifica quien descarta una review.

## Comprobacion con pull requests reales (solo lectura)

Evaluacion de `checkReviews` sobre los datos que devuelve la API, sin escribir nada:

| PR | Resultado del check | Esperado |
|---|---|---|
| #52 (JUP-026) | Falla: revision y validacion de la misma persona sin la linea de excepcion; cambios pendientes de `lmatsan` | Si: las dos reviews las publico la misma persona antes de existir la linea, y ambas piden cambios |
| #51 (JUP-096) | Falla: faltan `Revision JUP-096` y `Validacion JUP-096` | Si: aun sin reviews |
| #50 (JUP-098) | Falla: faltan las dos reviews tituladas | Si: reviews anteriores al flujo, sin titulo |
| #47 (JUP-086) | Falla: faltan las dos reviews tituladas | Si: reviews anteriores al flujo, sin titulo |

## Limites

- El workflow no se ha ejecutado en GitHub: solo existe en la rama; su primera ejecucion real sera en el propio PR de JUP-100.
- La activacion como check obligatorio requiere que un administrador actualice los rulesets (`docs/governance/github-branch-protection.md`); hasta entonces el check informa pero no bloquea.
- Al activarlo, los PR abiertos sin las dos reviews tituladas no podran mergearse; el #52 necesitara ademas la linea de excepcion.

## Nota de release

| Fecha | JUP | Nota de release | Review | ADRs |
| --- | --- | --- | --- | --- |
| 2026-09-30 | JUP-100 | Roles y flujo de revision y validacion documentados en CONTRIBUTING; nuevo check `JUP reviews` que exige las dos reviews tituladas antes del merge. | [review.md](../../openspec/changes/jup-100-review-validation-flow/review.md) | No aplica |
