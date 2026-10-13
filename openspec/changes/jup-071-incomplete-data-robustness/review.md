# Revisión — JUP-071

## Resumen

Evaluación de robustez del asistente ante datos incompletos o ambiguos: batería de 16 variantes con 13 referencias de JUP-069, runner `tools/assistant-robustness.py` sobre el transporte y la comprobación numérica de JUP-070, informe con cuatro estados y denominadores, y dos mediciones de la plantilla. Contribución inicial de Alejandro Aguado (PR #90, cerrado sin integrar el 10/10), recuperada sobre `develop` el 13/10. Esta revisión recoge el trabajo del 13/10: bloque `run` del informe para el futuro dashboard de JUP-121 y corrección de los hallazgos de la revisión adversarial.

El change queda abierto: los grupos 5.x (juicios humanos, medición con el chat real de JUP-035, tres campañas y revisión independiente) están pendientes y no se dan por hechos. Ninguna medición de este change acredita robustez generativa.

## Decisiones

- El informe incorpora un bloque `run` con los campos de la cabecera de JUP-070 y un identificador derivado del hash del crudo; los campos anteriores se mantienen. El aplanado, los valores no medidos y la unificación de formatos son de JUP-121.
- Las cifras esperadas de una variante pueden llevar `aliases` propios; el lector numérico los usa antes que las reglas de JUP-070 y que la etiqueta.
- El informe añade un desglose por categoría, porque el desglose por tipo de perturbación tiene un solo caso por grupo.
- Los informes de plantilla de `docs/evidence/` se sustituyen por una repetición offline con el código del commit `5f5253c`: los crudos del 10/10 están fuera de Git y no estaban disponibles. Los resultados son los mismos (0 aciertos, 8 fallos, 21 pendientes de 29).
- No se sube la versión de la batería (`1.0.0`) al añadir los alias porque nunca se integró en `develop`; los crudos del 10/10 dejan de ser compatibles con su hash y no se reutilizan.

## Validation

- `python tools/assistant-robustness.py validate`: 16 variantes, 29 casos, hashes válidos.
- `corepack pnpm assistant-robustness:test`: 58 pruebas OK.
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

## Pattern sweep

- Etiquetas de cifras sin alias: solo JUP-071-002 y JUP-071-003 (JUP-071-010 se resuelve por la etiqueta «julio» y tiene prueba propia). Los baselines usan las reglas de JUP-070.
- Normalización de rutas: el defecto está también en `outside_repository` de JUP-070 (registrado).
- Validación de la batería: el resto de campos ya pasaba por `require`; se cubrieron los accesos que podían lanzar excepciones no controladas.
- Valores declarados del bloque `run`: los tres campos de texto usan la misma función de validación.

## Risks

- La batería es pequeña, sintética y diseñada; no demuestra robustez universal.
- Las ejecuciones medidas son de la plantilla offline. No hay medición con el chat real ni juicios humanos (grupo 5).
- La normalización `NFD` de revisores no equipara grafías de ancho completo («Ana» y «Ａna»); la documentación ya indica que no autentica identidades.

## ADR applicability

No aplica: no se introduce ninguna decisión arquitectónica duradera. La decisión de cómo llegan los informes a Grafana es de JUP-121 y se recogerá en su ADR.
