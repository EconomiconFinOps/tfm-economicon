# Revisión — JUP-071

## Resumen

Evaluación de robustez del asistente ante datos incompletos o ambiguos: batería de 16 variantes con 13 referencias de JUP-069, runner `tools/assistant-robustness.py` sobre el transporte y la comprobación numérica de JUP-070, informe con cuatro estados y denominadores, y dos mediciones de la plantilla. Contribución inicial de Alejandro Aguado (PR #90, cerrado sin integrar el 2026-10-10), recuperada sobre `develop` el 2026-10-13 y ampliada con el bloque `run` del informe, la aceptación de la descripción de ejecución del colector de JUP-123, la evidencia sin distancia, el comando `rows` para el contrato del dashboard de JUP-121, la procedencia que reporta el servidor y la corrección de los hallazgos de las revisiones.

El change queda abierto: los juicios humanos, la medición con el chat generativo de JUP-035, las tres campañas, la revisión y validación de personas y la validación del colector de JUP-123 (cabeza `e0a0c41e`) con un backend real que devuelva evidencia sin distancia (grupo 6 de `tasks.md`) están pendientes y no se dan por hechos. Ninguna medición de este change acredita robustez generativa.

## Sobre las revisiones de este documento

Las "pasadas adversariales" y la auditoría de trazabilidad que se recogen aquí las hicieron agentes automatizados independientes del que escribió el código: reciben solo la spec y el diff, con acceso de solo lectura, e intentan romperlo. Sirven para encontrar defectos, pero **no son la `Revision JUP-071` ni la `Validacion JUP-071` de una persona** y no sustituyen la revisión independiente que exige `CONTRIBUTING.md`. Ninguna se atribuye a Paris, Víctor, Alejandro ni Lucía.

## Decisiones

- El informe incorpora un bloque `run` con los campos de la cabecera de JUP-070 y un identificador derivado del hash del crudo; los campos anteriores se mantienen. El aplanado, los valores no medidos y la unificación de formatos son de JUP-121.
- Las cifras esperadas de una variante pueden llevar `aliases` propios; el lector numérico los usa antes que las reglas de JUP-070 y que la etiqueta. Las variantes de cumplimiento de tagging piden una sola cifra, como el caso de JUP-069 del que derivan.
- El informe añade un desglose por categoría, porque el desglose por tipo de perturbación tiene un solo caso por grupo.
- Los informes de plantilla de `docs/evidence/` son una repetición offline con la herramienta del commit `2486d44d` (regenerarlos con la actual da los mismos totales y solo cambian identificadores, fecha y hashes): los crudos del 10/10 están fuera de Git y no estaban disponibles. Los resultados son los mismos (0 aciertos, 8 fallos, 21 pendientes de 29). El registro de regeneraciones está en la evidencia.
- No se sube la versión de la batería (`1.0.0`) al cambiar sus alias y sus cifras porque nunca se integró en `develop`; los crudos del 10/10 dejan de ser compatibles con su hash y no se reutilizan.
- No se escribe un colector de `/generations` ni un ejecutor de campañas: se consume el de JUP-123 (PR #131).

## Validation

Estado del 2026-10-16, Windows, Python 3.14:

- `python tools/assistant-robustness.py validate`: 16 variantes, 29 casos, hashes válidos.
- `corepack pnpm assistant-robustness:test`: 130 pruebas OK (123 al fusionar el PR #136 y 7 añadidas después para la capa de informe).
- Pruebas de JUP-070 (110) y de métricas de JUP-067 (103): OK.
- `node --test tools/ci-workflow.test.mjs`: 14 OK (con las dependencias del repositorio principal enlazadas temporalmente, porque el directorio de trabajo no tenía `node_modules`).
- `corepack pnpm openspec:validate` (74/74; 75/75 tras integrar el change de JUP-121), `corepack pnpm jup:check -- --change jup-071-incomplete-data-robustness` y `corepack pnpm jup:cleanup:check`: OK.
- Prueba de extremo a extremo con el colector de JUP-123 contra un backend real con modelo simulado: ver la evidencia.
- Evidencia por criterio en `docs/evidence/JUP-071-validation.md`.

## Adversarial Review (pass 1)

Pasada automatizada, base `bfaf3983`, head `bc822a20`. Veredicto: changes-required (1 HIGH, 4 MEDIUM, 4 LOW; sin BLOCKING).

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | HIGH | Corregido: las cifras de JUP-071-002 y JUP-071-003 no tenían alias y una respuesta correcta como «El cumplimiento es del 10 %» quedaba en `fail` aunque pasaba en su baseline. Alias en la batería y prueba con respuestas parafraseadas. La pasada 4 mostró después que esas dos variantes tenían además una segunda cifra no pedida (ver ADV-2 de la pasada 4). |
| ADV-2 | MEDIUM | Corregido: el Markdown muestra el total previsto, `pass / total previsto`, `pass / (pass + fail)` o «no disponible» y la advertencia de que el denominador incluye fallos con juicios pendientes. |
| ADV-3 | MEDIUM | Corregido: nuevo desglose `categories` (cinco categorías de 5, 4, 3, 3 y 1 casos) además del de perturbaciones. |
| ADV-4 | MEDIUM | Corregido en JUP-071: las rutas con prefijo extendido de Windows se normalizan antes de comparar. El mismo defecto del CLI de JUP-070 se registra en `openspec/findings/backlog.md` porque la propuesta no modifica ese evaluador. |
| ADV-5 | MEDIUM | Corregido: `validate` exige riesgo `critical` en los casos con cifras esperadas y una versión `x.y.z`. |
| ADV-6 | LOW | Corregido: una batería malformada produce un error controlado y no un traceback. |
| ADV-7 | LOW | Corregido en parte: `provider`, `alias` y `model_alias` no admiten `:` ni prefijos con forma de clave. Es una heurística y la documentación lo dice. |
| ADV-8 | LOW | Corregido: con `--provisional` cada caso lleva `reduced_coverage` y `assessment_complete` es falso mientras haya alguno. |
| ADV-9 | LOW | Corregido: las salidas dentro del repositorio se limitan a `docs/evidence/`. |

## Adversarial Review (pass 2)

Pasada automatizada, base `bfaf3983`, head `93eb7d47`. Veredicto: changes-required (3 HIGH, 4 MEDIUM, 2 LOW; sin BLOCKING).

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | HIGH | Corregido: una ruta UNC de recurso administrativo (`\\localhost\D$\...`) apuntaba al propio repositorio y `offline` sobrescribía la batería con el crudo. Reproducido en un clon temporal por el revisor. Las rutas de red no se aceptan como salida. |
| ADV-2 | HIGH | Corregido: `reduced_coverage` y `assessment_complete` no aparecían en el Markdown versionable. El informe indica el número de casos con cobertura reducida, si la evaluación está completa y una columna por caso. |
| ADV-3 | HIGH | Corregido: los rivales eran solo las etiquetas de las demás cifras y no sus alias, a diferencia de JUP-070, y una respuesta con las cifras cambiadas pasaba. Los rivales son ahora los alias de las otras cifras. |
| ADV-4 | MEDIUM | Corregido: alias como `*`, `` ` `` o un carácter de ancho cero normalizaban a vacío y casaban con cualquier frase. Se exige que no estén vacíos ni repetidos tras normalizar. |
| ADV-5 | MEDIUM | Corregido en parte: los valores declarados pasan a ser identificadores en minúsculas sin guion bajo y se rechazan prefijos de claves conocidas y cadenas largas sin separadores. Sigue siendo heurístico. |
| ADV-6 | MEDIUM | Corregido: tipos mal formados o campos ausentes dan un error con el identificador del caso; `schema_version: true` ya no se acepta. |
| ADV-7 | MEDIUM | Corregido: dentro del repositorio solo se pueden escribir los informes `JUP-071-*-report.json` y `.md` de `docs/evidence/`, no la evidencia redactada a mano. |
| ADV-8 | LOW | Corregido: el Markdown incluye el resultado de cada tipo de perturbación. |
| ADV-9 | LOW | Corregido: los puntos y espacios finales de un componente se descartan al comparar rutas; el revisor había comprobado que no era explotable. |

## Adversarial Review (pass 3)

Pasada automatizada, base `bfaf3983`, head `689a3714`. Veredicto: **accept** (sin BLOCKING ni HIGH; 3 MEDIUM y 3 LOW).

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | MEDIUM | Registrado en `openspec/findings/backlog.md`: `labelled_by` de JUP-070 solo mira la etiqueta anterior a la cifra y rechaza respuestas correctas como «de 10 EUR/pedido en julio a 6 EUR/pedido en agosto». Es heredado del evaluador que la propuesta no modifica; el protocolo avisa de que un `fail` numérico de estos casos se mire a mano. |
| ADV-2 | MEDIUM | Corregido: `baseline`, `methodology` y `sources` ausentes o mal formados dan un error controlado. |
| ADV-3 | MEDIUM | Documentado en el protocolo: los valores declarados van en minúsculas y sin `:` ni `@`. No se relaja la regla porque forma parte de la defensa contra credenciales. |
| ADV-4 | LOW | Aceptado como heurística, ya documentada: no detecta toda cadena con forma de credencial. |
| ADV-5 | LOW | Corregido: `//` solo se trata como ruta de red en Windows. |
| ADV-6 | LOW | Corregido en parte: `stripped` e `is_unc` se prueban en cualquier plataforma con `os.name` simulado. La normalización con enlaces simbólicos reales sigue sin ejercerse en Linux. |

## Cambios posteriores a la pasada 3 (2026-10-16)

Tras integrar #130 y probar el colector de JUP-123 (PR #131) contra un backend real, la exportación fallaba porque el `run-info` de seis cadenas de ese colector no era válido para el bloque `run`: ninguna combinación de valores servía a ambas partes. Se relajó la cabecera para aceptar un commit declarado de 7 a 40 hexadecimales en minúscula y `generation` como una sola cadena (alias del modelo, sin temperatura). Provider, alias y la cadena de `generation` mantienen el patrón restringido, y la forma de objeto sigue siendo válida. Se añadieron 6 pruebas. Estos cambios, junto con la reconciliación de la spec y el diseño, se sometieron a la pasada 4 y a la auditoría siguientes.

## Adversarial Review (pass 4) y auditoría de trazabilidad

Pasada automatizada sobre el estado final `136eeaec` (base `origin/develop`): **accept** (sin BLOCKING ni HIGH; 3 MEDIUM y 3 LOW). Auditoría independiente de trazabilidad sobre el mismo estado: **changes-required** (2 HIGH, 10 MEDIUM, 7 LOW; sin BLOCKING). Los hallazgos coincidentes se tratan una sola vez.

| ID | Sev. | Origen | Resolución |
| --- | --- | --- | --- |
| P4-1 / A-1 | MEDIUM / HIGH | ambas | Corregido: un entero demasiado grande (valor, tolerancia, temperatura, distancia o duración) lanzaba `OverflowError`, y un documento anidado miles de niveles `RecursionError`; la salida era un traceback, contra lo que promete la spec. Una única comprobación de número finito y el CLI captura `ArithmeticError` y `RecursionError`. Pruebas por campo y con un documento anidado 20 000 niveles. |
| P4-2 | MEDIUM | adversarial | Corregido: JUP-071-002 y JUP-071-003 pedían también la cifra de coste etiquetable (1.000 EUR), que la pregunta no solicita; una respuesta correcta que daba solo el 10 % fallaba y ningún juicio humano podía revertirlo. Una sola cifra, como en su baseline JUP-069-011. Cambió el hash de la batería y se regeneró la evidencia. |
| P4-3 / A-2 | MEDIUM / HIGH | ambas | Corregido en la spec: decía que un valor declarado que fuera «un marcador» se rechazaba, pero el código solo valida la forma (palabras como `tbd` o `unknown` cumplen el patrón). La spec dice ahora qué se rechaza y que el significado no se comprueba. |
| P4-4 | LOW | adversarial | Registrado sin cambio (sin aceptación humana) en `openspec/findings/backlog.md`: dos revisores con formas Unicode de compatibilidad se cuentan como distintos; es una función de JUP-070 y requiere intención deliberada. |
| P4-5 | LOW | adversarial | Registrado sin cambio (sin aceptación humana) en el backlog y en el diseño: `configuration_sha256` es un hash de toda la configuración declarada. |
| P4-6 | LOW | adversarial | Corregido: una fecha de recogida con forma válida pero calendario imposible daba un error sin nombrar el campo; ahora indica «collection time». |
| A-3 | MEDIUM | auditoría | Corregido en el diseño: afirmaba que la hoja de revisión incluye las cifras esperadas; solo incluye prompt, respuesta, citas, fragmentos y puntos de juicio. |
| A-4 | MEDIUM | auditoría | Corregido en la spec: decía que el informe declara los hashes del banco, la metodología y las fuentes; solo trae `suite_sha256`, que los cubre porque están dentro de la batería. |
| A-5 | MEDIUM | auditoría | Corregido en el diseño: describía tres niveles de ejecución y el código tiene dos (`template_mock` y `live_unverified`). |
| A-6 / A-7 / A-8 | MEDIUM | auditoría | Corregido: cifras (68 pruebas, 109 de JUP-070, «grupos 5.x»), commits obsoletos y texto histórico en presente (el PR #90 «sigue abierto», el borrador mergeable) en `review.md`, la evidencia y la continuidad. La evidencia lleva ahora un registro de regeneraciones y la continuidad un estado actual separado de la cronología. |
| A-9 | MEDIUM | auditoría | Atendido: la prueba con el colector se repitió con la cabeza actual del #131 (`af8388d0`) y se registró. El cambio de esa cabeza destapó un hueco real, la tarea 6.6. |
| A-10 | MEDIUM | auditoría | Corregido: la tarea 5.1 afirmaba haber contrastado cada afirmación con el código; no era cierto. Se reformuló y se dejó 5.3 para corregir lo que 5.2 encontró. |
| A-11 | MEDIUM | auditoría | Corregido: se aclara en este documento que las pasadas son automatizadas y no sustituyen la revisión de una persona. |
| A-12 | MEDIUM | auditoría | Corregido con pruebas: fallos de infraestructura por tiempo de espera y por error 500 (una sola vez, sin reintentos), un caso que pasa entre otros sin revisar, invariancia de resultados ante la cabecera, y diferencias de mayúsculas en rutas. Algunas pruebas de rutas se ejecutan solo en Windows, que es donde existen esas sintaxis; los cálculos de cadenas de rutas se prueban en cualquier plataforma. |
| A-13 | LOW | auditoría | Corregido: el backlog incluía JUP-069-011, que tiene una sola cifra, entre los casos afectados por la limitación de `labelled_by`. |
| A-14 | LOW | auditoría | Corregido: `collect` guardaba entera la descripción de la ejecución en el crudo, incluidos campos adicionales posibles como una clave. Ahora solo admite los seis campos declarados y rechaza otro por su nombre. |
| A-15 / A-16 / A-19 | LOW | auditoría | Corregido: `compare` con informes sin los campos esperados, un `git rev-parse` fallido y la tabla de tipos de perturbación sin total por grupo. |
| A-17 | LOW | auditoría | Corregido: se eliminó de la continuidad la afirmación de que el proveedor externo estaba caído en pruebas de terceros, que no consta en ninguna fuente. |
| A-18 | LOW | auditoría | Corregido: el protocolo decía que el fragmento fijo del modo offline corresponde al caso; son los primeros 500 caracteres de su primera fuente. |
| B | — | auditoría | Corregido en la spec: varios comportamientos del código no tenían requisito (comando `prepare`, vinculación de juicios al crudo, validación estricta del crudo, máximo de dos revisores, vocabularios cerrados de la batería). |

## Adversarial Review (pass 5, dirigida)

Pasada automatizada sobre el diff `136eeaec..8f8f71fd`, con mutación manual de una copia del código (19 mutantes, 15 detectados por las pruebas; los supervivientes se resolvieron o eran equivalentes). Veredicto: **accept** (sin BLOCKING ni HIGH; 2 MEDIUM y 3 LOW).

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | MEDIUM | Corregido: `prepare` no exigía que su salida estuviera fuera del repositorio y la spec lo promete; con un nombre `*-report.json` de `docs/evidence` escribía los prompts en un fichero versionable. Ahora aplica la misma comprobación que `offline`, `collect` y `review-sheet`. |
| ADV-2 | MEDIUM | Corregido: la restricción de los seis campos de `collect` era superficial. `generation` aceptaba claves extra y `corpus` y `retrieval` cualquier valor, y todo se guardaba en el crudo. Ahora `generation` solo lleva `model_alias` y `temperature`, y `corpus` y `retrieval` son un texto corto o un objeto plano de valores cortos con claves que no parezcan credenciales. |
| ADV-3 | LOW | Corregido con prueba: la columna de total por tipo de perturbación solo tenía una prueba de la cabecera (un mutante que borraba los valores sobrevivía). Ahora se comprueba el total de cada una de las 16 filas. |
| ADV-4 | LOW | Corregido con prueba: el máximo de dos revisores por punto no tenía prueba. |
| ADV-5 | LOW | Heredado y registrado solo aquí, sin cambio y sin aceptación humana: `check_number` de JUP-070 acepta como correctas negaciones o contraposiciones («no es del 10 %»); las variantes se comportan igual que su baseline. Lo cubre el juicio humano y la limitación ya registrada de `labelled_by`. |

Los arreglos de ADV-1 a ADV-4 se hicieron con RED previo y no se sometieron a otra pasada.

## Adversarial Review (pass 6)

Pasada automatizada sobre el commit `8e826854` (tareas 4.4 y 4.5: distancia no medida, `public_evidence` y comando `rows`), base `954c9dc9`. Veredicto: changes-required (1 HIGH, 4 MEDIUM, 6 LOW). Correcciones en `7f95acb0`, con ciclo RGR.

| ID | Sev. | Resolución |
| --- | --- | --- |
| P6-1 | HIGH | Corregido: `rows` lanzaba una excepción no controlada con informes de tipos anidados incorrectos; `rows_v1` valida ahora la forma completa y falla siempre con un error controlado. |
| P6-2 | MEDIUM | Corregido: `rows` emitía recuentos negativos o incoherentes y tasas que no coincidían con su cociente; se validan antes de emitir. |
| P6-3 | MEDIUM | Corregido: con cero casos evaluados `pass_over_total` salía medida con valor 0; ambas tasas son `not_measured`. |
| P6-4 | MEDIUM | Corregido: `provider` y `alias` se descartaban; viajan como identidad de embedding. |
| P6-5 | MEDIUM | Corregido: una ejecución real no verificada se clasificaba como real; `generation_model` queda nulo salvo verificación y el dashboard la marca `sin_modelo_verificado`. Se pierde el alias declarado en las filas. |
| P6-6 a P6-9 | LOW | Corregido: tipo de ejecución desconocido (se rechaza); `public_evidence` con `id` o `kind` vacíos, `id` repetidos o `content`/`source` no textuales (se rechazan); el diseño decía que las tasas eran `automatic` (son `human`); el protocolo no documentaba `rows` ni la distancia nula (documentado). |
| P6-10 / P6-11 | LOW | Registrado solo aquí, sin cambio y sin aceptación humana: la regex de nombres permitidos en `docs/evidence` admite puntos, igual que la de los informes; un BOM al inicio del informe da un error controlado heredado de `read()`. |

Los arreglos no se sometieron a otra pasada hasta la pasada 7.

## Adversarial Review (pass 7)

Pasada automatizada sobre `954c9dc9..369d4de1` (tareas 4.4 a 4.6 completas, incluido el desglose por tipo de perturbación y la procedencia del servidor). Veredicto: accept (2 MEDIUM, 3 LOW). Comprobó que las correcciones de la pasada 6 siguen en pie. Correcciones en `98b89ca9`.

| ID | Sev. | Resolución |
| --- | --- | --- |
| P7-1 | MEDIUM | Corregido: el bloque `server_reported` se aceptaba también en una ejecución de plantilla; ahora se rechaza. |
| P7-2 | MEDIUM | Corregido: el diseño tenía una frase obsoleta y una cláusula duplicada. |
| P7-3 | LOW | Corregido: la spec no recogía las reglas de rechazo de la procedencia del servidor (escenario añadido). |
| P7-4 | LOW | Documentado en el protocolo: un hash del servidor en mayúsculas bloquea la colección entera; si ocurriera habría que normalizarlo en el colector. Pendiente de confirmar con #131 al validar su cabeza (tarea 6.6). |
| P7-5 | LOW | Corregido con prueba: las claves extra de cada entrada nunca llegan al informe ni a las filas. |

## Auditoría de coherencia documental (2026-10-16, tras la pasada 7)

Auditoría automatizada de trazabilidad entre propuesta, diseño, spec, tareas, revisión, evidencia, protocolo, continuidad y código sobre `98b89ca9`. Veredicto: changes-required (3 HIGH, 8 MEDIUM, 7 LOW; sin defectos de código ni de estructura OpenSpec). Los 18 hallazgos (3 + 8 + 7) se corrigieron; los dos puntos de «Sin cambio» son observaciones adicionales que no estaban entre los 18:

- HIGH: el estado del colector de JUP-123 se describía como «bloquea hoy» en cinco documentos aunque su cabeza `e0a0c41e` ya adopta la capacidad; el número de pruebas figuraba como 91 en revisión y evidencia (son 123); el número de pasadas no coincidía entre continuidad y tareas. Todo unificado.
- MEDIUM: continuidad desactualizada (respuesta de #131 y #132), `configuration_sha256` sin mención en el diseño, informes versionados presentados como generados con la herramienta «actual», párrafos del protocolo con saltos duros, estado `Accepted` del backlog sin aceptación humana, pasadas 6 y 7 sin la estructura de las anteriores, reglas de `public_evidence` sin escenario en la spec, y texto sobre qué filas son `human` ya superado por la guía del dashboard.
- LOW: referencia muerta «(ver abajo)», resumen sin mención de `rows`, línea en blanco sobrante en las tareas, la expresión «otra sesión», un nombre de modelo concreto en una prueba, cifras de la prueba del 16/10 no verificables desde el repositorio (ahora lo declara el texto) y un historial del protocolo que repetía reglas (ahora marcado como registro histórico).
- Sin cambio: la sección `pairs` del informe no tiene requisito propio (está en el protocolo) y la rama conserva el prefijo `test/` heredado del PR #90.

Estos arreglos no se sometieron a otra auditoría. Ninguna de estas revisiones es la `Revision JUP-071` ni la `Validacion JUP-071` de una persona.

## Revisión y validación del PR #137 (excepción temporal)

Seguimiento del PR #136 con las notas no bloqueantes de su revisión: pruebas de la capa de informe y documentación. Por la excepción temporal, la revisión y la validación se hicieron de forma automatizada y se registran aquí, no como reviews de GitHub: `JUP reviews` queda en rojo y se declara, y la fusión la decide quien lidera con una orden expresa.

Revisión adversarial automatizada sobre `1f0cdb36` (base `ee4e8031`). Veredicto: changes-required (4 MEDIUM, 3 LOW; sin HIGH).

| ID | Sev. | Resolución |
| --- | --- | --- |
| P8-1 | MEDIUM | Corregido: el protocolo para re-fijar la batería estaba incompleto (la validación exige que las fuentes de la batería coincidan con las del banco de JUP-069, no existe un subcomando para calcular el hash, `TEMPLATE_SHA256` cambia los hashes de la herramienta y la regla sobre `suite_version` no tenía respaldo). Reescrito con los pasos reales. |
| P8-2 | MEDIUM | Corregido: la continuidad seguía diciendo «ninguna revisión ni validación de una persona», «listos para revisarse» y la revisión pendiente, aunque ya ocurrieron para el instrumento. |
| P8-3 | MEDIUM | Corregido: cifras de dos momentos mezcladas (123 y 128 pruebas, 74/74 y 75/75). |
| P8-4 | MEDIUM | Corregido con pruebas: sobrevivían mutantes vecinos (`not_run` en la evaluación completa, el modo no provisional de la cobertura reducida, el valor de la fila agregada y `unit`, `behavior` y `grp` de las filas numéricas). |
| P8-5 a P8-7 | LOW | Corregido: filas «Pendiente» y «Límites» de la evidencia ya cumplidas, línea en blanco que partía una lista, y pruebas que dependían de identificadores concretos de la batería (ahora eligen los casos por propiedad). |

Validación: 130 pruebas de robustez, `assistant-robustness:validate`, `openspec:validate` (75/75), `jup:check` y `jup:cleanup:check` en verde, y 11 mutantes propios sobre una copia, todos detectados, con el control sin mutar en verde. No hay stack, backend ni modelo reales en este PR, que no toca código de producción. Los arreglos posteriores a esta revisión no se sometieron a otra. No sustituye a la `Revision JUP-071` ni a la `Validacion JUP-071` de una persona.

## Pattern sweep

- Cifras sin alias y cifras no pedidas: las variantes de cumplimiento eran las únicas con dos cifras o sin alias; JUP-071-010 tiene una cifra y se resuelve por la etiqueta «julio».
- Normalización de rutas: el defecto del prefijo extendido está también en `outside_repository` de JUP-070 (registrado). El predicado `outside` lo usan `offline`, `collect`, `review-sheet` y `protect_outputs`, y todos reciben la misma corrección.
- Validación de la batería: el resto de campos ya pasaba por `require`; se cubrieron los accesos que podían lanzar excepciones no controladas, incluidos los enteros enormes. Quedan fuera los de `tools/assistant-eval.py` (JUP-070), que no se modifica.
- Valores declarados del bloque `run`: los tres campos de texto usan la misma función de validación.
- Rivales por alias: el cálculo se corrigió para todos los casos con varias cifras; JUP-071-010 tiene una sola.
- Salidas privadas (pasada 5): `offline`, `collect`, `review-sheet` y `prepare` aplican `outside()`; `score` escribe a propósito en `docs/evidence` y lo acota `protect_outputs`; `compare` no escribe.
- Lectura de JSON sin límite de profundidad: `read()` y las lecturas de `compare` quedan cubiertas por la captura de `RecursionError` en el CLI.

## Risks

- La batería es pequeña, sintética y diseñada; no demuestra robustez universal.
- Las ejecuciones medidas son de la plantilla offline y de un modelo simulado. No hay medición con el chat real ni juicios humanos (grupo 6).
- Los fallos numéricos de los casos con varias cifras pueden deberse a la limitación de `labelled_by` de JUP-070 (registrada); hay que mirarlos a mano antes de atribuirlos al asistente.
- Los valores declarados del bloque `run` y las rutas se validan de forma heurística y no excluyen todo secreto posible.
- La evidencia de corpus del chat real no trae distancia. La cabeza actual del colector de JUP-123 (`e0a0c41e`) y esta herramienta ya se entienden, pero solo se probó con una fila construida con su forma: sin un backend real que devuelva evidencia de corpus y sin la CI del colector en verde (tarea 6.6), una campaña real con citas no está demostrada.
- La normalización de revisores no equipara formas Unicode de compatibilidad (registrado); no autentica identidades.

## ADR applicability

No aplica: no se introduce ninguna decisión arquitectónica duradera. La decisión de cómo llegan los informes a Grafana es de JUP-121 y se recogerá en su ADR.
