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

## Human Approval

- Change: jup-092-frontend-typescript-adr
- Approval type: post-review
- Decision: approved
- Approver: Victor
- Date: 2026-09-02
- Review accepted: yes
- Checks accepted: yes
- Documentation synchronized: yes
- Archive decision: archive
- Notes: JUP-092 completada (12/12 tareas): produce y acepta `docs/adr/ADR-0003-frontend-typescript.md`,
  resolviendo las cuatro decisiones que bloqueaban F2 (rigor `strict`, convivencia `allowJs`, encaje
  con CI y cierre de `RF-082-002` por obsolescencia, ubicación del `tsconfig`). Con esta tarjeta, **F1
  (Preparación e inventario) queda completa**: JUP-090 (inventario del destino), JUP-091 (inventario
  del origen) y JUP-092 (este ADR). Sin findings nuevos: esta HU resuelve `RF-082-002`, no genera
  hallazgos. Queda pendiente, explícitamente fuera de esta HU y anotado en el spike, que F2 y F3
  citen el ADR-0003 en su `design.md` al crearse. Sin `docs/evidence/JUP-092-validation.md`: se sigue
  el precedente de JUP-083/090/091 para HUs doc-only, con `review.md` como único registro de
  validación.

## Addendum: corrección por revisión de PR (2026-09-04)

El PR #26 recibió `CHANGES_REQUESTED` de Alejandro (`Iber1to`) tras la aprobación post-review
registrada arriba. Hallazgo `[P1]` sobre `docs/adr/ADR-0003-frontend-typescript.md:158`: la
afirmación "`RF-082-002` se cierra por obsolescencia [al terminar F2]" no era ejecutable. Las 49
violaciones reproducidas viven en **9 archivos `.jsx`**; F2 desactiva `react/prop-types` solo para
`.ts`/`.tsx` y no renombra ningún archivo (eso es F3), así que `pnpm lint` seguiría reportando las
mismas 49 violaciones al terminar F2.

Se corrigió, en la misma rama y PR (sin nueva HU, por tratarse de cambio no mergeado — ver
`.claude/harness/workflow.md` §7): `docs/adr/ADR-0003-frontend-typescript.md` (decisión 3 y
seguimiento), `docs/spikes/frontend-migration.md` (decisión nº 1) y
`openspec/findings/backlog.md` (`RF-082-002`), para que los tres digan lo mismo: el finding
permanece `Open` hasta que F3 (o el cierre de F5) migre esos 9 archivos a `.tsx` con cobertura real
de tipos, no como efecto colateral de F2.

Esta sección documenta el hallazgo tal como se registró en `review.md` original; las cuatro
decisiones del ADR (rigor, convivencia, ubicación del `tsconfig`, y CI obligatorio) no cambiaron —
solo se corrigió la condición de cierre de `RF-082-002` dentro de la decisión 3.
