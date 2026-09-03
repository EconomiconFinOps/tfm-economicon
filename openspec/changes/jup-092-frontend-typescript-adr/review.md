# Review: jup-092-frontend-typescript-adr

## Result

Accepted

## Scope Reviewed

- `docs/adr/ADR-0003-frontend-typescript.md` (nuevo, estado `Accepted`).
- `docs/spikes/frontend-migration.md` (4 puntos de enlace: decisión nº 1, tarjeta propia, "ADR antes
  de tooling", "Próximos pasos"; F1 marcada completa).
- `openspec/findings/backlog.md` (`RF-082-002` anotado con resolución prevista, sigue `Open`).
- `apps/frontend/package.json`, `apps/frontend/eslint.config.js`,
  `docs/governance/github-branch-protection.md`, `docs/planning/JUP-090-...` y
  `docs/planning/JUP-091-...` en solo lectura, como fuente de evidencia.
- `openspec/changes/jup-092-frontend-typescript-adr/{proposal,design,specs,tasks}.md`.

## Checklist

- [x] Las cuatro decisiones (rigor, convivencia, CI/`RF-082-002`, ubicación del `tsconfig`) están
  resueltas sin condicionales.
- [x] La sección Consequences recoge qué se vuelve más fácil, más difícil y más arriesgado.
- [x] Hay 3 alternativas descartadas con motivo (JavaScript puro, JSDoc+checkJs, adopción gradual).
- [x] El ADR pasó de `Proposed` a `Accepted` en un commit separado del de redacción.
- [x] El ADR queda enlazado desde el spike, con F1 marcada completa.
- [x] `RF-082-002` anotado con la resolución prevista, sin cerrarse (la ejecución material es de F2).
- [x] Checks del carril ejecutados y en verde (tarea 4.2).
- [x] Tasks.md marcado 12/12.

ADR aplicable y producido: este change **es** el ADR (`ADR-0003-frontend-typescript.md`, `Accepted`).

## Validation

```txt
corepack pnpm openspec:validate -> PASS: 21 items validated strictly (3 specs, 18 changes)
corepack pnpm jup:check -- --change jup-092-frontend-typescript-adr -> PASS: enlazado con Trello y completo
corepack pnpm jup:cleanup:check -> PASS: 372 archivos sin agentes personales, binarios ni tareas paralelas
test / lint / build -> N/A (doc-only, sin código de producto; harness TDD omitido: sin tester/coder/mutación)
```

Evidencia verificada durante la propia redacción del ADR:

```txt
tsconfig.json en el repo -> 0 (ninguno, confirmado)
Violaciones react/prop-types en apps/frontend -> 49 (reproducido con pnpm lint)
```

## Review Findings

Ninguno nuevo. Esta HU **resuelve** un finding existente (no lo genera): `RF-082-002` queda anotado
con su resolución prevista en `openspec/findings/backlog.md`, pendiente de ejecución material en F2.

## Risks / Follow-Ups

- **El coste real de `strict: true` es desconocido hasta que F3 lo intente.** El ADR fija el criterio
  de escape: si desborda, se documenta y se redacta un ADR nuevo que supersede al 0003, sin relajar
  la configuración en silencio.
- **La superficie a tipar depende de `RF-091-002`** (adoptar o descartar shadcn/ui en F2), que este
  ADR no prejuzga.
- **F2 y F3 deben citar el ADR-0003 en su `design.md`** al crearse — no es tarea que JUP-092 pueda
  completar por ellas, y quedó explícitamente marcada como pendiente en el spike en vez de darse por
  hecha.
