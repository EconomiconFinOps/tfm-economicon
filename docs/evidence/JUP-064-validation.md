# JUP-064 — Evidencia de implementación del registro

[Tarjeta](https://trello.com/c/wluz6AGW). Preparación por Alejandro Aguado como
coautor; Víctor conserva liderazgo, Lucía revisión y Paris validación.
Fecha: 2026-10-04. Esta evidencia técnica no sustituye `Validacion JUP-064`.

## Resultado

La [guía](../contributions/README.md) y el [registro](../contributions/JUP-064-register.md)
enlazan 91 historias y 75 asociaciones de PR con sus commits, reviews, pruebas,
documentación y checks. El snapshot conserva todos los enlaces; el informe
limita las filas extensas y enlaza el resto. La tabla agregada muestra también
las asignaciones de los cuatro roles por persona, sin contarlas como acciones.

Se observan acciones de los cuatro miembros: Alejandro en 46 historias, Víctor
en 32, Lucía en 35 y Paris en 26. Son acciones registradas, no acreditación
completa de cada historia. Las 32 casillas de roles sin resolver y los huecos
de pairing/reviews deben contrastarse con las fuentes originales y el equipo.

## Verificación ejecutada

| Comprobación | Resultado | Alcance |
| --- | --- | --- |
| Recogida viva con `--collect` | 91 historias / 75 asociaciones PR | Solo cliente Trello desplegado y GitHub paginado |
| Render offline de snapshot | Idéntico al render original | Comparación SHA-256 antes/después |
| `contributions:test` | 9/9 verdes | Asignación sin acción, identidad, alias, ambigüedad, títulos, SHA antiguo, self-review, solicitud de cambios, coautoría declarada y discrepancias |
| `node --test tools/ci-workflow.test.mjs tools/repository-governance.test.mjs tools/pr-policy.test.mjs` | 80/80 verdes | Política, proceso y modificación del workflow |
| `openspec:validate` | 45/45 verdes | Todas las specs y cambios, incluido JUP-064 |
| `jup:check:all`, `jup:cleanup:check`, `git diff --check` | Verdes | Trazabilidad, higiene y formato |
| `build` | 4 tareas correctas | Frontend y compilación Python; avisos de tamaño de bundle existentes |
| Primera suite general en paralelo | 3 fallos de 443 frontend; Python interrumpido por Turbo | Tres búsquedas del botón Sign in superaron la espera bajo carga; no se declara suite general verde |
| Reejecución aislada de los tres ficheros | 11/11 verdes | history-replace, pending-attempt y login-session-expired-notice |
| Suite general secuencial | Processor: 447 verdes, 57 omitidas y 1 fallo | `test_json_depth_error_is_discarded_once_then_next_delivery_is_returned`: basic_nack esperado, cero llamadas; Python 3.14.4. Turbo interrumpe el resto. |

No se ha modificado ningún archivo de `apps/` respecto de la base `c3aa9d6`.
La causa de los fallos generales no está confirmada; no se presenta la suite
completa como verde. Corresponde al líder contrastarlos en el entorno Python
3.12 de CI antes de declarar la PR lista. Los nueve tests específicos de JUP-064
y los checks de gobernanza sí pasan en este entorno.

Para los comandos de Turbo se usó un wrapper local de `pnpm` que invoca Corepack
9.0.0, porque el shim del entorno cargaba una versión distinta y abortaba la
instalación sin TTY. El wrapper no forma parte del repositorio.

## Pendientes de aceptación del equipo

- Víctor contrasta la implementación y el pairing, abre la PR y vincula esta
  evidencia desde Trello. No se ha simulado su participación con un trailer.
- Lucía revisa código, tests y límites del inventario. Paris valida cada criterio
  de la tarjeta con sus propios comandos y enlaces; ambas reviews siguen pendientes.
- Las notas de pairing y documentos externos se registran manualmente cuando
  el equipo aporte y contraste los enlaces; no se inferirán de CI o de nombres.
- OpenSpec sigue activo para que el líder pueda ajustar alcance y archivarlo
  antes de la integración. JUP-064 permanece en curso, no cerrada.
