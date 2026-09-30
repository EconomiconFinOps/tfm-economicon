## 1. Tests primero (RED)

- [x] 1.1 JUP-100 añadir a `tools/pr-policy.test.mjs` casos de la evaluación de reviews, sin red: faltan revisión o validación; títulos con acento, en minúsculas y de otro JUP; review del autor; review en borrador; review descartada o de un commit anterior que sigue contando; Request changes pendiente y luego aprobado; Comment posterior que no limpia un Request changes; misma persona con y sin declaración; PR hacia `main`; y que cada mensaje de error nombra lo que falta y enlaza a CONTRIBUTING. Ejecutarlos y confirmar que fallan.
- [x] 1.2 JUP-100 añadir a `tools/ci-workflow.test.mjs` los contratos del workflow `pr-reviews.yml` (disparadores `pull_request` y `pull_request_review` hacia `main`/`develop`, sin `pull_request_target`, permisos mínimos de solo lectura, acciones fijadas por commit, sin `persist-credentials`, job `JUP reviews`) y los ocho checks idénticos en ambos rulesets. Confirmar que fallan.
- [x] 1.3 JUP-100 añadir a `tools/repository-governance.test.mjs` aserciones de que CONTRIBUTING define los cuatro roles y el flujo, de que `AGENTS.md` y `CONTRIBUTING.md` tienen la misma línea `Process version`, y de que la plantilla de PR incluye el checklist y la aclaración de su sección Validacion, conservando las aserciones existentes. Confirmar que fallan.

## 2. Check `JUP reviews` (GREEN)

- [x] 2.1 JUP-100 implementar en `tools/pr-policy.mjs` la evaluación pura de reviews (metadatos del PR + reviews → errores) hasta que pasen los tests de 1.1, sin cambiar el comportamiento de "JUP policy".
- [x] 2.2 JUP-100 añadir el modo que lee el PR y sus reviews por la API con `GITHUB_TOKEN` y falla si la lectura falla, con test de ese camino de error.
- [x] 2.3 JUP-100 crear `.github/workflows/pr-reviews.yml` con el job `JUP reviews` y añadir el check a `.github/rulesets/develop.json` y `main.json` hasta que pasen los tests de 1.2.
- [x] 2.4 JUP-100 controles positivos: romper a propósito la evaluación (por ejemplo, contar reviews del autor o ignorar Request changes) y comprobar que los tests lo detectan; restaurar.

## 3. Documentación del flujo y los roles

- [ ] 3.1 JUP-100 escribir en `CONTRIBUTING.md` (inglés) los cuatro roles (qué hace, cuándo, qué entrega, qué no le corresponde, reasignaciones), el flujo completo de revisión, validación y merge, la línea de declaración de excepción y la `Process version`.
- [ ] 3.2 JUP-100 añadir a `AGENTS.md` la sección breve sin nombrar asistentes con las reglas no comprobables, la petición de alinear herramientas locales y la misma `Process version`.
- [ ] 3.3 JUP-100 actualizar `.github/pull_request_template.md` con el checklist del flujo, la línea opcional de excepción y la aclaración de su sección Validacion.
- [ ] 3.4 JUP-100 enlazar el flujo desde "Flujo aprobado" en `docs/governance/repository-and-branch-strategy.md` y documentar la activación del check en `docs/governance/github-branch-protection.md`.
- [ ] 3.5 JUP-100 comprobar que pasan los tests de 1.3 y que ningún enlace nuevo está roto.

## 4. Cierre y verificación

- [ ] 4.1 JUP-100 batería completa: `corepack pnpm pr:check:test`, `ci:check:test`, `repository:governance:test`, `jup:check:test`, `jup:cleanup:check`, `openspec:validate` y `jup:check -- --change jup-100-review-validation-flow`; registrar comandos y resultados.
- [ ] 4.2 JUP-100 comprobar el check contra datos reales en modo lectura: evaluar los PR #52 (dos reviews tituladas, misma persona) y otro PR sin reviews tituladas, y registrar el resultado esperado de cada uno.
- [ ] 4.3 JUP-100 revisión adversarial independiente (`adversarial-reviewer`) hasta `accept` o hasta que Lucia acepte explícitamente lo que quede; registrar las pasadas en `review.md`.
- [ ] 4.4 JUP-100 `review.md` con resumen, decisiones, validación, revisión adversarial, barrido del patrón, riesgos, findings y ADR no aplicable (D6).
- [ ] 4.5 JUP-100 `docs/evidence/JUP-100-validation.md` con la evidencia de los tests, los controles positivos y la comprobación con PR reales.
- [ ] 4.6 JUP-100 bloque `## Human Approval` en `review.md` tras la aprobación explícita de Lucia.
- [ ] 4.7 JUP-100 archivar el change en la misma rama con `openspec-archive-change`.
- [ ] 4.8 JUP-100 abrir el PR hacia `develop` con el cuerpo que exige "JUP policy" y avisar en Discord de la activación pendiente del check y de la nueva `Process version`.
