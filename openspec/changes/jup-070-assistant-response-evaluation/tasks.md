## 1. Pruebas en rojo

- [x] 1.1 Escribir `scripts/tests/test_assistant_eval.py` con las pruebas sin red externa: lectura de cifras (ambos convenios decimales, porcentaje y formas de palabra de la unidad, número dentro de otro mayor, unidad distinta, etiqueta lejana, tolerancia), decisión de cada conducta prohibida con una respuesta que la incumple y otra que no, puntuación de un caso, `not_run` por falta de juicio, doble revisión en los críticos y modo provisional, discrepancia entre revisores, cifra no trazable en un caso crítico, determinismo de los bytes, ausencia de texto y de credenciales en los resultados, aceptación del fichero por `tools/assistant-metrics.py` sin cambiarlo y veredicto con umbrales.
- [x] 1.2 Añadir la prueba de la recogida contra un servidor HTTP local de prueba: prompt idéntico al preparado, una conversación nueva por caso, nada de `expected` enviado, un 500 y un tiempo agotado como `blocked`, ningún secreto en el fichero crudo y rechazo de escribir los ficheros con texto dentro del repositorio.
- [x] 1.3 Comprobar que todo falla por la razón esperada porque la herramienta aún no existe. Resultado en rojo: la prueba fallaba al cargar la herramienta, que aún no existía.

## 2. Herramienta y reglas

- [x] 2.1 Implementar la lectura de cifras y su asociación con etiqueta, unidad y tolerancia, y ponerla en verde con revisión de mutantes sobre cada condición (tolerancia, unidad, frontera del número, etiqueta, convenio decimal).
- [x] 2.2 Escribir `docs/validation/JUP-070-evaluation-rules.json` con los alias de etiquetas de las cifras, la regla de cada una de las 37 conductas prohibidas y los umbrales, y la validación de que no falta ninguna regla; una respuesta que incumple y otra que cumple por regla en las pruebas. 37 reglas (una por conducta prohibida) con ejemplos que incumplen y que cumplen, que la prueba ejecuta; alias de las 29 cifras de los 14 casos críticos.
- [x] 2.3 Implementar `collect`, `review-sheet`, `score` y `compare` con salida determinista, el cálculo de la trazabilidad de cifras, el resultado de cada caso y el veredicto, y ponerlos en verde con revisión de mutantes sobre las condiciones clave (doble revisión, no puntuar sin juicio, cifra no trazable en un caso crítico, umbral obligatorio no disponible). 26 mutantes sobre cifras, unidades, etiquetas, negación, doble revisión, trazabilidad, umbrales y escritura fuera del repositorio; los siete que sobrevivían al principio se cerraron con pruebas nuevas. Hallazgo al implementar: el calculador exige `structured_ok` en los casos completados (se informa `true` para el contrato de respuesta del chat) y la latencia de las cuatro etapas (solo el total es medida); está reflejado en el diseño y la spec.
- [x] 2.4 Añadir `assistant-eval:test` a `package.json`, el paso a `.github/workflows/ci.yml` y la comprobación en `tools/ci-workflow.test.mjs`, con su control negativo. También en Python 3.12 sin paquetes, como la CI.

## 3. Metodología y medición de referencia

- [ ] 3.1 Escribir `docs/validation/JUP-070-evaluation.md` (cómo ejecutar, qué decide la regla y qué las personas, doble revisión, repeticiones, lectura del veredicto, límites y qué no demuestra) y enlazarlo desde `docs/validation/README.md`.
- [ ] 3.2 Levantar un stack aislado (`docker compose -p jup070`), cargar el corpus del proyecto por el flujo existente y recoger las respuestas del chat actual con `collect`; generar la hoja de revisión.
- [ ] 3.3 Puntuar la medición de referencia con los juicios que se aporten, calcular el informe con `tools/assistant-metrics.py`, guardar el fichero de resultados y el informe sin texto y escribir `docs/evidence/JUP-070-validation.md` con lo medido, el commit, el proveedor, que ningún modelo generó las respuestas y si la medición es provisional.
- [ ] 3.4 Parar el stack y borrar sus volúmenes, y comprobar que `apps/`, `tools/assistant-metrics.py` y la batería no han cambiado.

## 4. Cierre y verificación

- [ ] 4.1 Batería completa: `assistant-eval:test`, `assistant-metrics:test`, `validation-questions:test`, las suites de gobernanza, `openspec:validate`, `jup:check -- --change jup-070-assistant-response-evaluation`, `jup:check:all`, `jup:cleanup:check` y `git diff --check`. Registrar comandos y resultados.
- [ ] 4.2 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`, el barrido de patrones, los riesgos y los hallazgos registrados en `openspec/findings/backlog.md`.
- [ ] 4.3 Evidencia en `docs/evidence/JUP-070-validation.md` y bloque `## Human Approval` post-review de Lucia.
- [ ] 4.4 Archivar el change en la misma rama, revisar la documentación posterior al archivo y abrir el PR a develop.
