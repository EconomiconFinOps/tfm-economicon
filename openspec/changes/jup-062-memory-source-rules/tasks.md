JUP: JUP-062

## 1. Governance document

- [x] 1.1 JUP-062 write `docs/memoria/README.md` with the source, the export policy, the section-to-card map, the editing rules, how review and validation are recorded and the rules for tools
- [x] 1.2 JUP-062 add the single pointer bullet to `AGENTS.md` under the source-of-truth rules, in tool-neutral wording
- [x] 1.3 JUP-062 state in the document that authorization to read does not authorize modifying, and that authorization for one section does not extend to another

## 2. Checks against the specification

- [x] 2.1 JUP-062 verify that the document names no assignee, no delivery date and no document URL, and that every local link resolves
- [x] 2.2 JUP-062 read the document against each scenario of `project-memory-governance` and fix any scenario it does not satisfy

## 3. Cierre y verificación

- [ ] 3.1 Batería completa: `openspec:validate`, `jup:check -- --change jup-062-memory-source-rules`, `jup:check:all`, `jup:cleanup:check` y `git diff --check`. Registrar comandos y resultados.
- [ ] 3.2 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`, el barrido de patrones, los riesgos y los hallazgos registrados en `openspec/findings/backlog.md`.
- [ ] 3.3 Bloque `## Human Approval` post-review de Lucia.
- [ ] 3.4 Archivar el change en la misma rama, revisar la documentación posterior al archivo y abrir el PR a develop.
