## 1. Pruebas en rojo

- [ ] 1.1 En `routes.integration.test.tsx`, añadir una prueba que abra con sesión cada dirección oculta (`/operational`, `/cuts`, `/recommendations`) y otra desconocida, y espere la pantalla inicial dentro del armazón, sin pantalla de error del enrutador y con el ámbito de cliente seleccionado intacto. Añadir la de la ruta puente: `/overview-legacy` se presenta con su armazón. Comprobar que fallan por la razón esperada (hoy las tres ocultas presentan su pantalla y la desconocida muestra el error del enrutador).
- [ ] 1.2 En `Layout.test.tsx`, añadir las pruebas de que el menú no contiene Coste Detallado, Corte Global, Recomendaciones ni Overview, y de que contiene exactamente Coste Global, Anomalías, Ingestions, Assistant y Salud del sistema, en ese orden y sin separador. Comprobar que fallan por la razón esperada.
- [ ] 1.3 Sin sesión, abrir una dirección oculta presenta el acceso, no la pantalla inicial. Comprobar que esta prueba ya pasa hoy (control: el comodín no debe saltarse `SessionGate`).

## 2. Ocultar las pantallas

- [ ] 2.1 En `routes.tsx`, quitar las tres rutas de demostración y sus importaciones, añadir la ruta comodín hacia `/` con `replace` como hija de `Layout`, y actualizar el comentario de cabecera (conserva `/overview-legacy`, indica cuántas pantallas hay solo en el README).
- [ ] 2.2 En `Layout.tsx`, fusionar las dos listas en una, quitar el separador y las entradas ocultas y Overview, retirar los iconos que ya no se usan y corregir los comentarios que hablan de «5 de demostración» y «3 conectadas».
- [ ] 2.3 Pasar las tres pruebas de `routes.integration.test.tsx` que usaban `/operational` a `/ingest` y ajustar `Layout.test.tsx` a la lista nueva. Poner en verde la batería del frontend y comprobar que `OperationalCostDashboard`, `ExecutiveCutDashboard`, `RecommendationsPanel` y `savings-coral` siguen pasando sin cambios.
- [ ] 2.4 Control positivo: restaurar temporalmente una de las rutas ocultas y comprobar que su prueba nueva falla; devolverla a su estado.

## 3. Documentación

- [ ] 3.1 `apps/frontend/README.md`: reescribir la tabla «Rutas» con las pantallas publicadas, la ruta puente sin menú y una sección de pantallas no publicadas (dónde están y cómo reactivarlas con una ruta y una entrada de menú); rehacer el recuento y su fecha.
- [ ] 3.2 `docs/planning/JUP-097-frontend-data-gap-map.md`: anotar que las tres pantallas ya no se publican y que la tabla describe lo que necesitarían para volver.
- [ ] 3.3 `docs/demo/JUP-107/` (`README.md`, `guion.md`, `esperados.json`): sustituir la advertencia de «no abrir estas pantallas» por la de que ya no se publican, y volver a ejecutar `synthetic-demo:test`.
- [ ] 3.4 `openspec/findings/backlog.md`: cerrar `RF-104-004` con su motivo; actualizar `RF-095-002`, `RF-091-003` y `RF-105-001` (el menú ya no enlaza Overview; la ruta sigue y el inventario de pruebas que la usan sigue vigente).
- [ ] 3.5 Resumen de continuidad en `docs/continuidad/` y su índice.

## 4. Comprobación en el navegador

- [ ] 4.1 Levantar el frontend con el stack, entrar con el usuario demo y comprobar con capturas: menú con cinco entradas, las tres direcciones ocultas y una inexistente llevan a Coste Global con el cliente seleccionado, `/overview-legacy` se abre sin enlace, y Anomalías, Ingestions y Salud del sistema siguen funcionando. Anotar lo que no se pudo comprobar (por ejemplo, el envío de mensajes del asistente sin stack de IA).

## 5. Cierre y verificación

- [ ] 5.1 Batería completa: `corepack pnpm lint`, `typecheck`, `test` y `build` del frontend, `openspec:validate`, `jup:check` de este change, `jup:cleanup:check` y `git diff --check`. Registrar comandos y resultados.
- [ ] 5.2 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`, el barrido de patrones (otras referencias a las rutas ocultas en código y documentos vigentes), los riesgos y los hallazgos registrados en `openspec/findings/backlog.md`.
- [ ] 5.3 Evidencia en `docs/evidence/JUP-116-validation.md` (capturas y resultados de la tarea 4.1) y bloque `## Human Approval` post-revisión de Lucia en `review.md`.
- [ ] 5.4 Archivar el change en la misma rama, revisar la documentación posterior al archivo, poner la rama al día con `develop` y abrir el PR a `develop`.
