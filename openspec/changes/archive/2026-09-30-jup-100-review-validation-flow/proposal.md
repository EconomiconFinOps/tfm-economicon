JUP: JUP-100
Trello: https://trello.com/c/XlWNnm7r

## Why

Los cuatro roles rotatorios (liderazgo, pairing/coautoría, revisión de PR y validación/pruebas/documentación) figuran en cada PR, pero nadie ha definido qué hace exactamente cada uno ni cómo se revisa, valida y mergea un PR. En los 8 últimos PR mergeados solo 2 aprobaciones vinieron de quien figuraba como revisor, y ninguno dejó en GitHub rastro de la validación, así que no se sabe qué está realmente comprobado. El equipo acordó en Discord (29-30/09/2026) separar revisión y validación, con los matices de Alejandro, y el flujo se probó en el PR #52.

Además, cada persona trabaja con herramientas locales (asistentes, prompts, scripts) que no están en el repo y que son las que aplican el flujo; las reglas tienen que llegarles aunque nadie las actualice a mano.

## What Changes

- `CONTRIBUTING.md` (en inglés) define los cuatro roles: qué hace cada uno, en qué momento del flujo, qué entrega y qué no le corresponde, y cómo se actúa cuando un rol se reasigna.
- `CONTRIBUTING.md` documenta el flujo de PR:
  - revisión y validación son dos reviews separadas, tituladas `Revision JUP-XXX` y `Validacion JUP-XXX`;
  - hacia `develop`, la primera review publicada va como Comment si está conforme y la segunda aprueba solo si ambas están conformes y no queda nada bloqueante; hacia `main`, que exige dos aprobaciones, ambas aprueban;
  - cualquier problema se publica como Request changes e incluye lo que siga pendiente de la otra review;
  - personas distintas según los roles de Trello; si una misma persona hace ambas, se declara en la descripción del PR;
  - la validación deja evidencia por criterio de la tarjeta y dice qué queda sin validar y las limitaciones de la evidencia;
  - revisión y validación no suben commits a la rama; los findings fuera de alcance se piden al líder en la review;
  - quien atiende cambios lee todas las reviews, los comentarios de la conversación y los comentarios en líneas del diff;
  - mergea cualquier persona, siempre que el PR tenga ambas reviews y nada pendiente; si "Update branch" trae cambios que tocan lo mismo que el PR, se pide una revalidación.
- Nuevo check obligatorio de CI `JUP reviews`, en su propio workflow `.github/workflows/pr-reviews.yml`, que reutiliza `tools/pr-policy.mjs`: exige las dos reviews tituladas del mismo JUP, de alguien que no sea el autor, sin cambios pedidos pendientes, y la declaración explícita si la misma persona hace ambas. Consulta las reviews por la API y su mensaje de error dice qué falta y enlaza a CONTRIBUTING.
- `AGENTS.md` incorpora, sin nombrar ningún asistente, las reglas del flujo que el check no puede comprobar y pide alinear las herramientas locales con CONTRIBUTING.
- Una línea `Process version` idéntica en `AGENTS.md` y `CONTRIBUTING.md`, comprobada por un test, para que cualquier persona o herramienta detecte que el proceso ha cambiado.
- La plantilla de PR incorpora el checklist del flujo y aclara que su sección "Validacion" es la evidencia del líder, no la validación del rol.
- `docs/governance/repository-and-branch-strategy.md` enlaza el flujo desde "Flujo aprobado" y `docs/governance/github-branch-protection.md` describe la activación del nuevo check.
- Los rulesets versionados de `develop` y `main` añaden `JUP reviews` como check obligatorio.

## Capabilities

### New Capabilities

- `pr-review-validation`: roles rotatorios, flujo de revisión y validación de PR, check `JUP reviews` y propagación de las reglas a las herramientas locales.

### Modified Capabilities

(ninguna; la capability `repository-governance` de `jup-079-branch-protection` sigue en un change activo sin promover a `openspec/specs/`)

## Impact

- Regla modificada: el check existente "JUP policy" (`jup-079-branch-protection`, capability `repository-governance`, todavía en un change activo) exigía siempre cuatro personas distintas; con la excepción declarada acepta la misma persona en revisión y validación, manteniendo liderazgo y pairing como personas distintas. Sin esto, la Participación no podría reflejar con honestidad la excepción acordada (revisión adversarial, pasada 2, ADV-1).

- Documentación: `CONTRIBUTING.md`, `AGENTS.md`, `.github/pull_request_template.md`, `docs/governance/repository-and-branch-strategy.md`, `docs/governance/github-branch-protection.md`. `README.md` no cambia: su sección "Colaboracion" ya remite a CONTRIBUTING.
- CI y gobernanza: `.github/workflows/pr-reviews.yml` (nuevo), `tools/pr-policy.mjs`, `tools/pr-policy.test.mjs`, `tools/ci-workflow.test.mjs`, `tools/repository-governance.test.mjs`, `.github/rulesets/develop.json`, `.github/rulesets/main.json`.
- Activar el nuevo check en GitHub requiere que un administrador aplique los rulesets, según `docs/governance/github-branch-protection.md`.
- Sin cambios en el código de producto.
- Fuera de alcance: decidir si `develop` debe exigir dos aprobaciones (sigue en una); actualizar las herramientas locales de cada persona (se avisará tras el merge); cambiar el uso de las columnas "40 — En revisión" y "50 — Validación" de Trello.
