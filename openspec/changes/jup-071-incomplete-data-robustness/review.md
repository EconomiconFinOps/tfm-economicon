# Revisión — JUP-071

## Resumen

Evaluación de robustez del asistente ante datos incompletos o ambiguos: batería de 16 variantes con 13 referencias de JUP-069, runner `tools/assistant-robustness.py` sobre el transporte y la comprobación numérica de JUP-070, informe con cuatro estados y denominadores, y dos mediciones de la plantilla. Contribución inicial de Alejandro Aguado (PR #90, cerrado sin integrar el 10/10), recuperada sobre `develop` el 13/10. Esta revisión recoge el trabajo del 13/10: bloque `run` del informe para el futuro dashboard de JUP-121 y corrección de los hallazgos de la revisión adversarial.

El change queda abierto: los grupos 5.x (juicios humanos, medición con el chat real de JUP-035, tres campañas y revisión independiente) están pendientes y no se dan por hechos. Ninguna medición de este change acredita robustez generativa.

## Decisiones

- El informe incorpora un bloque `run` con los campos de la cabecera de JUP-070 y un identificador derivado del hash del crudo; los campos anteriores se mantienen. El aplanado, los valores no medidos y la unificación de formatos son de JUP-121.
- Las cifras esperadas de una variante pueden llevar `aliases` propios; el lector numérico los usa antes que las reglas de JUP-070 y que la etiqueta.
- El informe añade un desglose por categoría, porque el desglose por tipo de perturbación tiene un solo caso por grupo.
- Los informes de plantilla de `docs/evidence/` se sustituyen por una repetición offline con el código del commit `7e60f1d`: los crudos del 10/10 están fuera de Git y no estaban disponibles. Los resultados son los mismos (0 aciertos, 8 fallos, 21 pendientes de 29).
- No se sube la versión de la batería (`1.0.0`) al añadir los alias porque nunca se integró en `develop`; los crudos del 10/10 dejan de ser compatibles con su hash y no se reutilizan.

## Validation

- `python tools/assistant-robustness.py validate`: 16 variantes, 29 casos, hashes válidos.
- `corepack pnpm assistant-robustness:test`: 66 pruebas OK.
- Pruebas de JUP-070 (109) y de métricas de JUP-067 (103): OK.
- `node --test tools/ci-workflow.test.mjs`: 12 OK.
- `corepack pnpm openspec:validate`, `corepack pnpm jup:check -- --change jup-071-incomplete-data-robustness` y `corepack pnpm jup:cleanup:check`: OK.
- Evidencia por criterio en `docs/evidence/JUP-071-validation.md`.

## Adversarial Review (pass 1)

Revisor independiente, base `bfaf3983`, head `bc822a20`. Veredicto: changes-required (1 HIGH, 4 MEDIUM, 4 LOW; sin BLOCKING).

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | HIGH | Corregido: las cifras de JUP-071-002 y JUP-071-003 no tenían alias y una respuesta correcta como «El cumplimiento es del 10 %» quedaba en `fail` aunque pasaba en su baseline. Alias en la batería y prueba con respuestas parafraseadas de las tres variantes con cifras. |
| ADV-2 | MEDIUM | Corregido: el Markdown muestra el total previsto, `pass / total previsto`, `pass / (pass + fail)` o «no disponible» y la advertencia de que el denominador incluye fallos con juicios pendientes. |
| ADV-3 | MEDIUM | Corregido: nuevo desglose `categories` (5 grupos con más de un caso) además del de perturbaciones. |
| ADV-4 | MEDIUM | Corregido en JUP-071: las rutas con prefijo extendido de Windows se normalizan antes de comparar. El mismo defecto del CLI de JUP-070 se registra en `openspec/findings/backlog.md` porque la propuesta no modifica ese evaluador. |
| ADV-5 | MEDIUM | Corregido: `validate` exige riesgo `critical` en los casos con cifras esperadas y una versión `x.y.z`. |
| ADV-6 | LOW | Corregido: una batería malformada produce un error controlado y no un traceback. |
| ADV-7 | LOW | Corregido en parte: `provider`, `alias` y `model_alias` no admiten `:` ni prefijos con forma de clave. Es una heurística y la documentación lo dice. |
| ADV-8 | LOW | Corregido: con `--provisional` cada caso lleva `reduced_coverage` y `assessment_complete` es falso mientras haya alguno. |
| ADV-9 | LOW | Corregido: las salidas dentro del repositorio se limitan a `docs/evidence/`. |

Ataques que resistieron: alteración de hashes del crudo y de la configuración, configuración manipulada en ejecuciones reales, recogida HTTP contra un servidor local (29 conversaciones, prompts exactos, error 500 como `blocked`, sin reintentos ni fugas de credenciales), juicios parciales y duplicados, fugas de texto en los informes versionables, coherencia aritmética de las variantes con su contexto y controles que impiden premiar la abstención universal.

## Adversarial Review (pass 2)

Revisor independiente, base `bfaf3983`, head `93eb7d47`. Veredicto: changes-required (3 HIGH, 4 MEDIUM, 2 LOW; sin BLOCKING).

| ID | Sev. | Resolución |
| --- | --- | --- |
| ADV-1 | HIGH | Corregido: una ruta UNC de recurso administrativo (`\localhost\D$\...`) apuntaba al propio repositorio y `offline` sobrescribía la batería con el crudo. Reproducido en un clon temporal por el revisor. Las rutas de red no se aceptan como salida. |
| ADV-2 | HIGH | Corregido: `reduced_coverage` y `assessment_complete` no aparecían en el Markdown versionable. El informe indica el número de casos con cobertura reducida, si la evaluación está completa y una columna por caso. |
| ADV-3 | HIGH | Corregido: los rivales eran solo las etiquetas de las demás cifras y no sus alias, a diferencia de JUP-070, y una respuesta con las cifras cambiadas pasaba. Los rivales son ahora los alias de las otras cifras. |
| ADV-4 | MEDIUM | Corregido: alias como `*`, `` ` `` o un carácter de ancho cero normalizaban a vacío y casaban con cualquier frase. Se exige que no estén vacíos ni repetidos tras normalizar. |
| ADV-5 | MEDIUM | Corregido en parte: los valores declarados pasan a ser identificadores en minúsculas sin guion bajo y se rechazan prefijos de claves conocidas (`xox`, `ghp`, `akia`, `eyj`, `sk`...) y cadenas largas sin separadores. Sigue siendo heurístico. |
| ADV-6 | MEDIUM | Corregido: tipos mal formados o campos ausentes dan un error con el identificador del caso; `schema_version: true` ya no se acepta. |
| ADV-7 | MEDIUM | Corregido: dentro del repositorio solo se pueden escribir los informes `JUP-071-*-report.json` y `.md` de `docs/evidence/`, no la evidencia redactada a mano. |
| ADV-8 | LOW | Corregido: el Markdown incluye el resultado de cada tipo de perturbación. |
| ADV-9 | LOW | Corregido: los puntos y espacios finales de un componente se descartan al comparar rutas; el revisor había comprobado que no era explotable. |

Ataques que resistieron: uniones y enlaces simbólicos hacia `docs/validation` y la batería, prefijo extendido, mayúsculas, `..`, directorio hermano `docs/evidence-evil`, flujos alternativos, nombre reservado `NUL`, filas ausentes del crudo en `categories` y `perturbations`, todos los casos bloqueados, `reduced_coverage` junto a `blocked` y a fallos, revisores duplicados o vacíos, fugas de texto en los informes y alias solapados con la misma etiqueta.

No probado por el revisor: nombres 8.3, enlaces duros, unidades `subst` o mapeadas y WSL.

## Pattern sweep

- Etiquetas de cifras sin alias: solo JUP-071-002 y JUP-071-003 (JUP-071-010 se resuelve por la etiqueta «julio» y tiene prueba propia). Los baselines usan las reglas de JUP-070.
- Normalización de rutas: el defecto está también en `outside_repository` de JUP-070 (registrado).
- Validación de la batería: el resto de campos ya pasaba por `require`; se cubrieron los accesos que podían lanzar excepciones no controladas.
- Valores declarados del bloque `run`: los tres campos de texto usan la misma función de validación.
- Rivales por alias (pasada 2): en `score` el cálculo se corrigió para todos los casos con varias cifras; JUP-071-010 tiene una sola cifra y su límite (una respuesta con la etiqueta «julio» atribuida a otro mes) queda cubierto por el juicio humano.
- Rutas (pasada 2): el predicado `outside` lo usan `offline`, `collect`, `review-sheet` y `protect_outputs` para `score`; todos reciben la misma corrección.

## Risks

- La batería es pequeña, sintética y diseñada; no demuestra robustez universal.
- Las ejecuciones medidas son de la plantilla offline. No hay medición con el chat real ni juicios humanos (grupo 5).
- La normalización `NFD` de revisores no equipara grafías de ancho completo («Ana» y «Ａna»); la documentación ya indica que no autentica identidades.

## ADR applicability

No aplica: no se introduce ninguna decisión arquitectónica duradera. La decisión de cómo llegan los informes a Grafana es de JUP-121 y se recogerá en su ADR.
