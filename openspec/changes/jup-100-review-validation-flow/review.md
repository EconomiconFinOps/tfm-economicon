# Revision JUP-100

## Resumen

JUP-100 define los cuatro roles rotatorios y el flujo de revision y validacion de PR en `CONTRIBUTING.md`, lo propaga a `AGENTS.md` y a la plantilla de PR con una `Process version` comun, y anade el check obligatorio `JUP reviews` en su propio workflow (`.github/workflows/pr-reviews.yml`), que reutiliza `tools/pr-policy.mjs --reviews` y lee las reviews por la API. "JUP policy" acepta la excepcion declarada de misma persona en revision y validacion. Ambos rulesets pasan a exigir ocho checks.

## Decisiones

- Workflow propio y no `ci.yml`: los eventos de review relanzarian o cancelarian la CI y los jobs omitidos cuentan como superados (design D1).
- Reviews leidas por la API, nunca del payload del evento (D2).
- Semantica del check (D3), decidida por Lucia en el explore del 2026-09-30: no se exige el ultimo commit; "pendiente" es la ultima decision de cada revisor (Approve, Request changes o descarte); no se comprueban identidades frente a los roles; el autor no cuenta; la misma persona solo con la linea de excepcion completa y visible.
- Aplicado a `develop` y `main`; en `main` ambas reviews aprueban (D3, D4).
- Propagacion en cinco capas: mensaje del check, `AGENTS.md`, plantilla, CONTRIBUTING y spec, y `Process version` identica comprobada por test (D5).
- "JUP policy" acepta tres personas con la excepcion declarada (D5b, opcion A elegida por Lucia).
- Sin ADR (D6): decision de proceso versionada en CONTRIBUTING, gobernanza y spec, como `jup-079-branch-protection`.

## Validacion

Bateria final sobre `6cce6a9`, los mismos comandos que el job "OpenSpec" de la CI:

| Comando | Resultado |
|---|---|
| `corepack pnpm pr:check:test` | 56 passed |
| `corepack pnpm ci:check:test` | 10 passed |
| `corepack pnpm repository:governance:test` | 12 passed |
| `jup:check:test`, `roadmap:test`, `jup:cleanup:test` | 7, 5 y 6 passed |
| `jup:check:all`, `jup:cleanup:check` | correctos (685 archivos) |
| `openspec:validate` | 35/35 |
| `docker:validate`, `collaboration:test`, `assistant-corpus:test`, `assistant-corpus:validate`, `validation-questions:test`, `validation-questions:validate`, `llm-gateway:test` | correctos |
| `jup:check -- --change jup-100-review-validation-flow` | correcto |

RED antes de cada implementacion y de cada correccion, controles positivos (mutantes) y comprobacion del check con los PR #52, #51, #50 y #47 en `docs/evidence/JUP-100-validation.md`.

## Adversarial Review (pass 1)

Head `9063fa4`. Veredicto: `changes-requested`.

| ID | Sev | Hallazgo | Resolucion |
|---|---|---|---|
| ADV-1 | HIGH | Una aprobacion descartada por un push (`dismiss_stale_reviews_on_push`) hacia que volviera a bloquear un Request changes anterior del mismo revisor | Reproducido (test en rojo) y corregido: un descarte deja al revisor sin decision vigente (`17d341b`) |
| ADV-2 | MEDIUM | CONTRIBUTING no explicaba como se levanta un Request changes (un Comment no lo levanta) | Documentado en CONTRIBUTING y AGENTS con test de gobernanza (`17d341b`) |
| ADV-3 | LOW | Titulos con formato Markdown no se reconocen sin explicar por que | El mensaje indica que la primera linea debe ser el titulo en texto plano (`17d341b`) |
| ADV-4 | LOW | La linea de excepcion contaba dentro de un comentario HTML | Corregido con test (`17d341b`); barrido: mismo patron en "JUP policy" registrado como RF-100-001 |
| ADV-5 | LOW | Un error sin enlace y enlace no pulsable en el log | URL absoluta en todos los errores, con test (`17d341b`) |
| ADV-6 | LOW | El check ejecuta el `pr-policy.mjs` del propio PR, que podria desactivarse a si mismo | Riesgo aceptado por Lucia ("me parece bien", 2026-09-30); CONTRIBUTING pide atencion especial a cambios en `tools/pr-policy.mjs` y `.github/workflows/` (`6989048`) |
| ADV-7 | LOW | Logins con distinta capitalizacion en la ultima decision | Corregido con test (`17d341b`) |

Ataques que resistieron: variantes de titulo (mayusculas, NFD, NBSP, BOM, `JUP-1000`, otro JUP), autor con otra capitalizacion, borradores, descartes y commits anteriores, fallos de API (red, 4xx, 200 con objeto, sin token), paginacion con 100 exactas, filtro de rama en eventos de review, permisos de solo lectura.

## Adversarial Review (pass 2)

Head `17d341b`. El revisor no pudo ejecutar comandos en su entorno; revision estatica. Veredicto: `changes-requested`.

| ID | Sev | Hallazgo | Resolucion |
|---|---|---|---|
| ADV-1 | HIGH | La excepcion de misma persona no podia cumplirse con honestidad: si la Participacion refleja la realidad, "JUP policy" fallaba por exigir cuatro personas distintas | Reproducido. Opcion A elegida por Lucia: "JUP policy" acepta tres personas con la excepcion declarada, liderazgo y pairing siguen separados; test combinado de ambos checks y mutante detectado (`88f2ece`) |
| ADV-2 | MEDIUM | El autor puede descartar el Request changes del revisor y mergear | Documentado y aceptado por Lucia ("documentarlo y aceptarlo", 2026-09-30): solo descarta quien pidio los cambios o alguien distinto del autor, con motivo; el check no lo verifica (`6989048`) |
| ADV-3 | LOW | La excepcion se reconocia por prefijo y dentro de bloques de codigo | Linea completa (con punto final opcional), fuera de comentarios HTML y bloques de codigo, con tests (`6989048`) |
| ADV-4 | LOW | Errores de API y de token sin enlace | Enlazan al flujo, con tests (`6989048`) |
| ADV-5 | LOW | La guia de proteccion de ramas listaba checks desactualizados | Lista de ocho checks con test que la compara con los rulesets (`6989048`) |
| ADV-6 | LOW | Checklist de la plantilla demasiado corto | Incluye las reglas no comprobables, con test (`6989048`) |

Nota operativa de la pasada: la rama local seguia a `develop` como upstream; se quito para que un `git push` no pueda apuntar a `develop`.

## Adversarial Review (pass 3)

Head `88f2ece`. Tests del revisor sobre una copia: 64/64 (`pr-policy` + gobernanza) y 10/10 (`ci-workflow`); `openspec validate --strict` valido. Veredicto: **accept** (sin BLOCKING ni HIGH). Los cinco findings afectan al codigo del propio cambio, asi que se corrigieron con test en rojo antes del arreglo, sin aceptarlos como riesgo:

| ID | Sev | Hallazgo | Resolucion |
|---|---|---|---|
| ADV-1 | MEDIUM | La excepcion contaba en un comentario HTML sin cerrar, en bloques `~~~`, en bloques sangrados y en codigo sangrado con 4 espacios | Solo cuenta el texto que GitHub muestra como Markdown normal; test con las cuatro variantes y mutante del codigo sangrado detectado |
| ADV-2 | MEDIUM | "JUP policy" aceptaba la excepcion con nombres distintos en revision y validacion, contra D5b | Se rechaza como incoherente; test y mutante detectado |
| ADV-3 | LOW | Una tercera persona con un titulo `Revision` cualquiera eximia de declarar la excepcion | Se exige la declaracion siempre que alguien publique ambas reviews tituladas; test |
| ADV-4 | LOW | Nombres de Participacion comparados con acentos y con `@` | Se comparan sin acentos y sin `@` inicial; test |
| ADV-5 | LOW | AGENTS.md no mencionaba que el check exige la linea de excepcion | Mencionado, con asercion de gobernanza |

Ataques que resistieron: titulos en mayusculas con acento, NFD, NBSP y lineas en blanco; rechazo de `## Revision`, `**Validacion**`, `JUP-1000` y guion no separable; filtrado del autor con otra capitalizacion; Request changes seguido de Comment sigue bloqueando; RC descartado deja de bloquear; bots con RC bloquean; carrera entre push y descarte con el mismo resultado; comentario HTML cerrado, cita, codigo en linea, casilla y tachado no declaran la excepcion; lider o pairing nunca cubren revision y validacion; fallos de la CLI (red, 500, 200 sin lista, sin token, usuario nulo) siempre exit 1 con enlace; workflow de solo lectura, sin `pull_request_target`, acciones fijadas; ocho checks iguales en ambos rulesets y en la guia; `Process version` identica.

Fuera de la revision (se comprueba en el propio PR, antes de activar los rulesets): a que commit se asocia la ejecucion lanzada por `pull_request_review`, que ejecucion toma el check obligatorio cuando conviven varias (incluidas las canceladas) y si el descarte automatico por push dispara `dismissed`.

## Cierre del ciclo adversarial

Se lanzo una cuarta pasada sobre `6cce6a9` para cubrir las correcciones posteriores al `accept` de la pasada 3, y se detuvo antes de terminar por decision de Lucia (2026-09-30): las ultimas pasadas solo endurecian casos cada vez mas rebuscados del reconocimiento de la linea de excepcion y aumentaban la complejidad sin valor proporcional para un check de proceso. El criterio del harness (`accept`) se cumplio en la pasada 3; las correcciones posteriores tienen test en rojo previo y mutantes detectados. Nuevos casos limite de la linea de excepcion se tratan como findings normales en otra tarjeta.

## Barrido del patron

- Ultima decision por revisor: solo en `tools/pr-policy.mjs`.
- Contenido oculto en la descripcion del PR (comentarios HTML): tambien afecta a `checkPullRequest` ("JUP policy") en las lineas de ID y roles; registrado como RF-100-001, fuera de alcance.
- Regla de "cuatro personas distintas": `tools/pr-policy.mjs`, CONTRIBUTING y la spec de `jup-079-branch-protection`; actualizada en el codigo y CONTRIBUTING, anotada en la propuesta.

## Riesgos

- Aceptados por Lucia: ADV-6 (pasada 1) y ADV-2 (pasada 2), con las palabras registradas arriba.
- El workflow solo se ejecutara de verdad en el propio PR de JUP-100; su activacion como obligatorio requiere que un administrador actualice los rulesets.
- Al activarlo, los PR abiertos sin las dos reviews tituladas no podran mergearse.

## Findings

- RF-100-001 (Low, Open): "JUP policy" acepta lineas de ID y roles dentro de comentarios HTML.

## ADR

No aplica (design D6).

## Human Approval

- Change: jup-100-review-validation-flow
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-09-30
- Adversarial review: accept (pass 3) | accepted findings: pass 1 ADV-6 (el check ejecuta el codigo del propio PR), pass 2 ADV-2 (no se verifica quien descarta una review)
- Archive decision: archive
- Notes: roles, flujo, check JUP reviews y propagacion a AGENTS/plantilla revisados; cuarta pasada detenida por decision de Lucia. Pendiente en Trello: revision de PR (Victor) y validacion (Alejandro); comprobar el check en GitHub en el propio PR antes de que un administrador active los rulesets.
