# JUP-064 — Evidencia de implementación del registro

[Tarjeta](https://trello.com/c/wluz6AGW). Preparación por Alejandro Aguado como
coautor; Víctor conserva liderazgo, Lucía revisión y Paris validación.
Fecha: 2026-10-04. Esta evidencia técnica no sustituye `Validacion JUP-064`.
Implementación publicada en [a75bcd4](https://github.com/EconomiconFinOps/tfm-economicon/commit/a75bcd4)
de la rama `docs/JUP-064-team-contributions`; la [entrega al líder](../contributions/JUP-064-handoff.md)
incluye los pasos y un texto de PR preparado.

## Resultado

La [guía](../contributions/README.md) y el [registro](../contributions/JUP-064-register.md)
enlazan 91 historias y 75 asociaciones de PR con sus commits, reviews, comentarios, pruebas,
documentación y checks. El snapshot conserva todos los enlaces; el informe
limita las filas extensas y enlaza el resto. La tabla agregada muestra también
las asignaciones de los cuatro roles por persona, sin contarlas como acciones.

Se observan acciones de los cuatro miembros: Alejandro en 46 historias, Víctor
en 32, Lucía en 35 y Paris en 29. Son acciones registradas, no acreditación
completa de cada historia. Las 30 casillas de roles sin resolver y los huecos
de pairing/reviews deben contrastarse con las fuentes originales y el equipo.

## Verificación ejecutada

| Comprobación | Resultado | Alcance |
| --- | --- | --- |
| Recogida viva con `--collect` | 91 historias / 75 asociaciones PR | Solo cliente Trello desplegado y GitHub paginado |
| Render offline de snapshot | Idéntico al render original | Comparación SHA-256 antes/después |
| `contributions:test` | 10/10 verdes en Python 3.14.4 y 3.12.13 | Asignación sin acción, identidad, alias, ambigüedad, títulos, SHA antiguo, self-review, solicitud de cambios, coautoría declarada y discrepancias |
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
3.12 de CI antes de declarar la PR lista. Los diez tests específicos de JUP-064
y los checks de gobernanza sí pasan en este entorno.

Ese contraste se completó posteriormente en la ejecución de CI enlazada abajo:
las suites completas pasan en Linux/Python 3.12. Los fallos locales se conservan
como evidencia de ese entorno, sin atribuirles una causa todavía no demostrada.

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

## Incremento: intervenciones históricas de PR

Corte actualizado `2026-10-04T17:27:22.764527+00:00`: incorpora 37 comentarios
con autor, fecha y enlace original; no conserva cuerpos ni acredita review
formal por su existencia. Paris figura ahora con acciones en 29 historias.
Se ha contrastado específicamente su [nota de JUP-024](https://github.com/EconomiconFinOps/tfm-economicon/pull/18#issuecomment-5570688974):
autor `ParisArcos`, fecha `2026-09-07T12:32:56Z`. La nota no se convierte en
validación vigente del HEAD final. Dos roles antes sin resolver se reconocen
ahora por sus etiquetas explícitas en Trello; quedan 30 casillas pendientes.

Las 10 pruebas pasaron en Python 3.12.13 dentro del contenedor desplegado en
DockerServer, usando archivos temporales y sin alterar la integración. Nueva
regeneración offline idéntica por SHA-256; OpenSpec sigue 45/45 y la trazabilidad
e higiene pasan. Esta actualización sustituye las cifras del primer corte;
la historia original permanece en Git.

## CI técnica contrastada

[Run 37220689712](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/37220689712),
ejecutada por `workflow_dispatch` sobre
`3eb68c5f995b1d66a9ddeee26a126cf785e6728c`: resultado final **success**,
seis jobs técnicos correctos. Logs inspeccionados, no solo estado agregado.

- OpenSpec y gobernanza: nuevos tests 10/10 y OpenSpec 45/45.
- Azure API: 59 tests correctos.
- Backend: 578 correctos y 28 omitidos.
- Processor: 448 correctos y 57 omitidos; el test que falló localmente pasa en CI.
- Frontend: 443 tests correctos en 48 archivos; lint y build correctos.
- Comprobación de tipos frontend correcta.

`JUP policy` se omite porque no hay evento de PR; `JUP reviews` no se ejecuta
sin PR. Esta CI no sustituye revisión y validación humanas ni permite integrar
la rama. Los cambios posteriores de esta evidencia son solo documentación;
la implementación y tests contrastados son los de `3eb68c5`.

## Contraste del líder

Víctor Méndez, 2026-10-05. Comprobaciones ejecutadas en su equipo (Windows 11,
Python 3.13.7, Node 24.15.0) sobre una copia temporal del HEAD `8366662`
fusionado con `develop` `0488372`, que ya incluye #58, #70 y #71. Este
contraste no sustituye `Revision JUP-064` ni `Validacion JUP-064`.

| Comprobación | Resultado |
| --- | --- |
| Fusión simulada con `develop` | Sin conflictos; `ci.yml` se combina con #58 y conserva `contributions:test` |
| Render offline del snapshot | Mismo contenido que el registro versionado: 91 historias y 75 asociaciones de PR. En Windows solo cambian los finales de línea |
| `contributions:test` | 10/10 |
| `ci:check:test`, `repository:governance:test` y `pr:check:test` | 82/82 |
| `openspec:validate` | 46/46 |
| Los 21 pasos del job de gobernanza de CI | Correctos |
| `git diff --check` contra `develop` | Limpio |
| `pr:check` con el texto de PR de la entrega | Correcto con un título que contiene JUP-064 |

Las cifras 82 y 46 difieren de las 80 y 45 anteriores por los tests y specs
que `develop` incorporó en #58 y #70; esta rama no cambia.

No verificado en este contraste:

- Las suites de frontend, backend, processor y Azure API. La rama no modifica
  `apps/` y constan en la CI de `3eb68c5`.
- La recogida viva. Requiere `gh` y acceso SSH a DockerServer, de los que el
  líder no dispone; este corte lo ejecutó Alejandro.
- El contenido fila a fila de las 91 historias. Se contrastó el alcance, la
  lectura de roles y el origen de los huecos, no cada enlace.

Hallazgos:

- El corte del 2026-10-04 es anterior a la integración de #58, #70 y #71 y a
  la apertura de #74 y #75, que no figuran. El registro se integra como corte
  fechado, sin regenerar.
- Las 30 casillas sin resolver vienen de ocho tarjetas. En JUP-083, JUP-093,
  JUP-094, JUP-095, JUP-101 y JUP-103 el recolector no leyó ninguna línea de
  rol. En JUP-097 y JUP-098 solo leyó una línea de liderazgo que no coincide
  con sus PR #42 y #50.
- Víctor corrigió el 2026-10-05 en Trello las descripciones de JUP-093,
  JUP-094, JUP-095, JUP-097, JUP-098 y JUP-103. El corte no lo refleja: hasta
  la próxima recogida el registro mantiene esos huecos y atribuye el liderazgo
  de JUP-097 y JUP-098 a Alejandro. Quedan por completar JUP-083 y JUP-101.
- No hubo sesión de pairing en JUP-064. Alejandro implementó en solitario y la
  coordinación fue el traspaso por chat; así consta en la
  [tabla manual](../contributions/README.md#evidencia-manual-fuera-del-recolector).

Pendiente de acordar en la PR: bajo qué tarjeta se regenerará el registro
antes de la memoria y quién, además de Alejandro, puede ejecutar la recogida.
