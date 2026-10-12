## 1. Inventario y glosario

- [x] 1.1 Inventariar por fichero los textos visibles en inglés de `apps/frontend/src` (JSX, `aria-label`, `title`, `alt`, `placeholder`), con una lista de los términos dudosos
- [x] 1.2 Crear `apps/frontend/GLOSARIO.md` con el nombre único de cada concepto repetido y los términos que se conservan en inglés con su motivo, y enlazarlo desde `apps/frontend/README.md`

## 2. Traducción por pantallas

- [x] 2.1 Traducir acceso (`LoginPage`) y arranque de sesión (`SessionGate`)
- [x] 2.2 Traducir conversaciones (`ConversationsPage`) y el compositor de mensajes (`MessageComposer`)
- [x] 2.3 Traducir la ingesta (`IngestPage`)
- [x] 2.4 Traducir el panel principal (`DashboardPage`)
- [x] 2.5 Traducir el resto de pantallas, componentes y layouts con textos en inglés o con términos distintos a los del glosario
- [x] 2.6 Revisar que los valores de la API y los textos de la persona usuaria se muestran sin tocar

## 3. Pruebas

- [x] 3.1 Actualizar las aserciones de las pruebas existentes que dependen de textos cambiados
- [x] 3.2 Añadir la prueba de regresión que falla ante un texto visible en inglés de la lista de términos traducidos, con los casos de la spec (texto en inglés, término del glosario, comentario o identificador)
- [x] 3.3 Si algún escenario de una spec principal cita un texto cambiado, añadir su delta MODIFIED en este change

## 4. Cierre y verificación

- [x] 4.1 Ejecutar la batería completa (`corepack pnpm build`, `lint`, `test`, `openspec:validate`, `jup:check`, `jup:cleanup:check`)
- [x] 4.2 Recorrer con el stack real las pantallas en tema claro y oscuro y comprobar que no queda texto propio en inglés ni desbordes por textos más largos
- [x] 4.3 Revisión adversarial con el agente `adversarial-reviewer` hasta `accept` y `review.md`
- [x] 4.4 Evidencia de validación en `docs/evidence/JUP-117-validation.md` y actualización de `docs/continuidad`
- [x] 4.5 `## Human Approval` posterior a la revisión, archivo del change en el mismo PR y apertura del PR contra `develop` (Human Approval de Lucia del 2026-10-12; el PR se abre justo después del archivo)
