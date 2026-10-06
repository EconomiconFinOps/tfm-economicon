## 1. Pruebas en rojo

- [ ] 1.1 Escribir `scripts/tests/test_synthetic_costs.py` con las pruebas sin base de datos: conjunto determinista, prefijo reservado y marcado de las ingestas, presencia de cada caso (cero registrado, hueco, crédito, dos monedas, importe fuera del rango seguro, dimensiones ausentes, mayúsculas del grupo de recursos y fila sin fecha), totales por mes y moneda con `Decimal` frente a la tabla escrita a mano, guardas del tenant, idempotencia y retirada con una conexión simulada.
- [ ] 1.2 Comprobar que fallan por la razón esperada (la herramienta aún no existe) y registrar el resultado.

## 2. Herramienta

- [ ] 2.1 Implementar `scripts/synthetic_costs.py` con el conjunto de datos, los subcomandos `apply`, `status` y `remove`, la lectura de `DATABASE_URL` y del tenant, la guarda de datos no sintéticos y la detección de estado parcial o ajeno.
- [ ] 2.2 Poner las pruebas en verde y revisar mutantes sobre las condiciones clave (prefijo, guarda, retirada solo sintética, idempotencia, totales).
- [ ] 2.3 Añadir la prueba contra CockroachDB real y desechable (`JUP086_COCKROACH_TEST_URL`) que carga, compara con una suma independiente y retira, y ejecutarla.

## 3. Documentación y CI

- [ ] 3.1 Escribir `docs/validation/JUP-106-synthetic-costs.md` con la tabla de valores esperados por mes y agrupación, los comandos de carga, estado y retirada, lo que cada caso ejercita, el aviso de que son datos sintéticos y los límites.
- [ ] 3.2 Añadir `synthetic-costs:test` a `package.json`, el paso a `.github/workflows/ci.yml` y la comprobación en `tools/ci-workflow.test.mjs`.

## 4. Comprobación de extremo a extremo

- [ ] 4.1 Levantar el stack aislado, cargar el conjunto y comparar `/billing/summary` por periodos y agrupaciones con los valores esperados, incluidos el mes con cero, el hueco, el crédito, la moneda doble y el importe grande.
- [ ] 4.2 Recorrer el dashboard actual con los datos cargados (una sola vez, con evidencia) y registrar lo observado como evidencia y hallazgos, sin corregir aquí.
- [ ] 4.3 Retirar los datos, comprobar que `tenant-growth` vuelve a estar vacío y que `tenant-core` no cambió, y repetir la carga para comprobar la idempotencia.

## 5. Cierre y verificación

- [ ] 5.1 Batería completa: `synthetic-costs:test`, `assistant-metrics:test` y las suites de gobernanza, `openspec:validate`, `jup:check:all`, `jup:cleanup:check` y `git diff --check`.
- [ ] 5.2 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`.
- [ ] 5.3 Evidencia en `docs/evidence/JUP-106-validation.md` y bloque `## Human Approval` post-review de Lucia.
- [ ] 5.4 Archivar el change en la misma rama, revisar la documentación posterior al archivo y abrir el PR a develop.
