## 1. Prueba en rojo

- [ ] 1.1 Escribir `scripts/tests/test_synthetic_anomalies.py` con las comprobaciones sin base de datos: cada cifra de `docs/demo/JUP-107/esperados-anomalias.json` frente a una suma exacta con `Decimal` sobre las filas del conjunto (sin usar el servicio de anomalías), periodos consecutivos de igual duración, fechas dentro de los periodos, fecha final no posterior al día UTC, ausencia de `id` y `evidence_id` en el fichero, y comportamiento de `apply`, `status` y `remove` con un almacén en memoria (idempotencia, negativa con datos ajenos, estado parcial y de otro tenant, retirada que solo toca sus filas y repetible).
- [ ] 1.2 Añadir el control negativo (alterar un importe, un periodo o un servicio debe fallar nombrando la cifra) y la prueba de que cada herramienta ve las filas de la otra como ajenas. Comprobar que todo falla por la razón esperada porque la herramienta y el fichero aún no existen.

## 2. Herramienta y datos

- [ ] 2.1 Escribir `scripts/synthetic_anomalies.py`, autocontenida y solo ASCII, con `apply`, `status` y `remove`, prefijo `synthetic-jup107-`, tenant por defecto `tenant-core`, indicador sintético en la ingesta y mensaje que declara que las filas son sintéticas.
- [ ] 2.2 Escribir `docs/demo/JUP-107/esperados-anomalias.json` con las reglas de referencia, los dos periodos, los totales y recuentos por servicio, los estados y motivos esperados por grupo y las dos alertas.
- [ ] 2.3 Poner la prueba en verde y revisar mutantes sobre las condiciones clave (límites de periodo, prefijo, negativa con datos ajenos, comparación del incremento mínimo y retirada). Registrar cuántos mutantes sobreviven y por qué.

## 3. Guía y comprobación contra el endpoint real

- [ ] 3.1 Levantar un stack aislado (`docker compose -p jup107b`, volúmenes nuevos), comprobar `tenant-core` vacío, cargar el conjunto y llamar al endpoint con la petición de referencia. Comparar las siete evaluaciones y las dos alertas con el fichero de esperados, repetir la petición para comprobar que `id` y `evidence_id` son estables, y comprobar si `/docs` está disponible.
- [ ] 3.2 Escribir `docs/demo/JUP-107/anomalias.md` con la declaración de origen sintético, la preparación, la petición, el script que no imprime la contraseña, las alertas y las no alertas con su motivo, las limitaciones (panel `/anomalies`, calidad de detección) y la vuelta al estado inicial.
- [ ] 3.3 Controles de error: JUP-106 cargado en `tenant-growth` no se altera con `apply` ni `remove` de esta herramienta; `tenant-core` con la ingesta pública hace que `apply` se niegue; `remove` repetido; tenant vacío al terminar; parar el stack y borrar los volúmenes.
- [ ] 3.4 Ejecutar la prueba con CockroachDB real si el fixture la admite, o dejar anotado por qué no, y anotar la comprobación de inserción y retirada del paso 3.1 como evidencia de base real.

## 4. CI y no interferencia

- [ ] 4.1 Añadir `synthetic-anomalies:test` a `package.json`, el paso a `.github/workflows/ci.yml` y la comprobación en `tools/ci-workflow.test.mjs`, con su control negativo.
- [ ] 4.2 Comprobar que no cambian `apps/`, `scripts/synthetic_costs.py`, los datos y documentos de JUP-106, `docs/demo/JUP-065/`, la primera parte de `docs/demo/JUP-107/` ni el dataset público.

## 5. Cierre y verificación

- [ ] 5.1 Batería completa: `synthetic-anomalies:test`, `synthetic-demo:test`, `synthetic-costs:test`, las suites de gobernanza, `openspec:validate`, `jup:check:all`, `jup:cleanup:check` y `git diff --check`. Registrar comandos y resultados.
- [ ] 5.2 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`, el barrido de patrones, los riesgos y los hallazgos registrados en `openspec/findings/backlog.md`.
- [ ] 5.3 Sección de evidencia en `docs/evidence/JUP-107-validation.md` y bloque `## Human Approval` post-review de Lucia.
- [ ] 5.4 Archivar el change en la misma rama, revisar la documentación posterior al archivo, poner la rama al día con `develop` y abrir el PR a `develop` con el bloque de excepción temporal.
