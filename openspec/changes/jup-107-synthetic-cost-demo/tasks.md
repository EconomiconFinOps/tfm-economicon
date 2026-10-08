## 1. Prueba en rojo

- [ ] 1.1 Escribir `scripts/tests/test_synthetic_cost_demo.py` con las comprobaciones sin base de datos: cada cifra de `esperados.json` frente a una suma exacta con `Decimal` sobre `build_dataset()`, identificadores de paso únicos, suma de duraciones igual al total declarado y no superior a 240 segundos, ningún paso principal que incluya el mes del importe muy grande, cada pregunta apuntando a un paso existente y comparación por moneda con las reglas de JUP-106.
- [ ] 1.2 Añadir el control negativo (alterar un importe, un mes o una moneda debe fallar nombrando la cifra) y comprobar que todo falla por la razón esperada porque el paquete aún no existe.

## 2. Paquete de demo

- [ ] 2.1 Levantar un stack aislado (`docker compose -p jup107`, volúmenes nuevos), cargar los datos con la herramienta de JUP-106 y recorrer el dashboard ejecutivo para fijar las etiquetas, los valores y el aspecto reales de cada paso; no escribir el guion de memoria.
- [ ] 2.2 Escribir `docs/demo/JUP-107/esperados.json` con los pasos, sus periodos y agrupaciones y las cifras esperadas, y `guion.md` con acción, texto, resultado esperado y duración por paso, la declaración de datos sintéticos antes de la primera cifra, el paso opcional del importe muy grande y los límites (pantallas que no leen estos datos).
- [ ] 2.3 Escribir `preparacion.md` (stack aislado, comprobación de tenant vacío, `apply`, `status`, resumen de la API frente a lo esperado, `remove` repetido, resumen vacío, parada del stack y borrado de volúmenes, y el aviso sobre JUP-065 y JUP-104), `preguntas.md`, `registro-ensayo.md` (plantilla) y `README.md`.
- [ ] 2.4 Poner la prueba en verde y revisar mutantes sobre las condiciones clave (suma de duraciones, tope, periodo principal, referencia de preguntas, comparación sin extremos en cero).

## 3. Receta de navegador

- [ ] 3.1 Escribir `docs/demo/JUP-107/receta-navegador.md` con el guion de Playwright que se ejecuta fuera del repositorio: recorre los pasos, lee los valores de la interfaz, los compara con `esperados.json`, guarda capturas y vídeo mudo fuera del repositorio, no intercepta peticiones, no carga ni retira datos y falla ante un error de página, de origen cruzado o un paso incumplido.
- [ ] 3.2 Ejecutarla sobre el stack aislado con los datos cargados, con un control positivo (un valor alterado debe hacerla fallar) y registrar el resultado como ejecución automatizada, con commit y fecha.

## 4. CI y comprobación de cierre del estado

- [ ] 4.1 Añadir `synthetic-demo:test` a `package.json`, el paso a `.github/workflows/ci.yml` y la comprobación en `tools/ci-workflow.test.mjs`, con su control negativo.
- [ ] 4.2 Retirar los datos, comprobar que `tenant-growth` vuelve a estar vacío y que `tenant-core` no cambió, y comprobar que `docs/demo/JUP-065/`, la herramienta de JUP-106, `apps/` y el dataset público no han cambiado.

## 5. Cierre y verificación

- [ ] 5.1 Batería completa: `synthetic-demo:test`, `synthetic-costs:test`, las suites de gobernanza, `openspec:validate`, `jup:check:all`, `jup:cleanup:check` y `git diff --check`. Registrar comandos y resultados.
- [ ] 5.2 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`, el barrido de patrones, los riesgos y los hallazgos registrados en `openspec/findings/backlog.md`.
- [ ] 5.3 Evidencia en `docs/evidence/JUP-107-validation.md` y bloque `## Human Approval` post-review de Lucia.
- [ ] 5.4 Archivar el change en la misma rama, revisar la documentación posterior al archivo y abrir el PR a develop.
