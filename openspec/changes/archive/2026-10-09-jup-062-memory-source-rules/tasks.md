JUP: JUP-062

## 1. Governance document

- [x] 1.1 JUP-062 write `docs/memoria/README.md` with the source, the export policy, the section-to-card map, the editing rules, how review and validation are recorded and the rules for tools
- [x] 1.2 JUP-062 add the single pointer bullet to `AGENTS.md` under the source-of-truth rules, in tool-neutral wording
- [x] 1.3 JUP-062 state in the document that authorization to read does not authorize modifying, and that authorization for one section does not extend to another
- [x] 1.4 JUP-062 add to the document the correction reference (the official brief), the lookup of the document location on the Trello card and the draft-proposal flow for tools with and without read access
- [x] 1.5 JUP-062 add the entry for the governance document to the documentation index of the root `README.md`

## 2. Checks against the specification

- [x] 2.1 JUP-062 verify that the document names no assignee, no delivery date and no document URL, and that every local link resolves
- [x] 2.2 JUP-062 read the document against each scenario of `project-memory-governance` and fix any scenario it does not satisfy

## 3. Cierre y verificación

- [x] 3.1 Batería completa: `openspec:validate`, `jup:check -- --change jup-062-memory-source-rules`, `jup:check:all`, `jup:cleanup:check` y `git diff --check`. Registrar comandos y resultados.
- [x] 3.2 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`, el barrido de patrones, los riesgos y los hallazgos registrados en `openspec/findings/backlog.md`.
- [x] 3.3 Bloque `## Human Approval` post-review de Lucia.
- [x] 3.4 Archivar el change en la misma rama, revisar la documentación posterior al archivo y abrir el PR a develop. Hecho: archivado el 2026-10-09, revisión documental sin deriva pendiente y PR #85 abierto.
