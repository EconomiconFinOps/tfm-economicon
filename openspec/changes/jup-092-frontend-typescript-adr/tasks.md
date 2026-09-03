## 1. Preparación

- [ ] 1.1 Crear `docs/adr/ADR-0003-frontend-typescript.md` a partir de `docs/templates/adr.md` con la
  cabecera completa: `Status: Proposed`, fecha, `Related JUP/OpenSpec` (JUP-092 +
  `jup-092-frontend-typescript-adr`), URL de Trello y `Supersedes`/`Superseded by` en `none`.

## 2. Redacción del ADR en estado `Proposed`

- [ ] 2.1 Escribir la sección **Context**: el destino en JavaScript sin tipos, el origen en TSX **sin
  `tsconfig` ni dependencia `typescript`**, la ausencia total de `tsconfig` en el repo, y que
  TypeScript sería el primer código tipado del lado JavaScript. Citar los inventarios de JUP-090 y
  JUP-091 como evidencia.
- [ ] 2.2 Escribir la sección **Decision** resolviendo las cuatro decisiones, cada una con su motivo:
  nivel de rigor (`strict`), estrategia de convivencia (`allowJs`), encaje con CI y ubicación del
  `tsconfig`. Ninguna puede quedar condicionada a una evaluación posterior.
- [ ] 2.3 Declarar dentro de **Decision** qué ocurre con `RF-082-002` (49 violaciones de
  `react/prop-types`): si se cierra, se transforma o se mantiene, y por qué, en relación con que los
  tipos sustituyen a `prop-types`.
- [ ] 2.4 Escribir la sección **Consequences** en ambas direcciones, incluyendo el coste de los
  errores latentes del TSX del origen nunca verificado y la dependencia con `RF-091-002`
  (adoptar o descartar shadcn/ui cambia la superficie a tipar).
- [ ] 2.5 Escribir **Alternatives Considered** con al menos dos opciones descartadas y su motivo
  (seguir en JavaScript; JSDoc + `checkJs` como vía intermedia).
- [ ] 2.6 Escribir **Evidence And Follow-up**: evidencia verificada en esta HU (recuento de las 49
  violaciones, ausencia de `tsconfig`) y las tareas de seguimiento que ejecutará F2.

## 3. Aceptación y enlace

- [ ] 3.1 Recoger la aprobación del equipo sobre las cuatro decisiones y **cambiar el estado del ADR
  de `Proposed` a `Accepted`**, en un commit separado del de redacción.
- [ ] 3.2 Enlazar el ADR desde `docs/spikes/frontend-migration.md`: en la decisión nº 1 y en la
  tarjeta F1 correspondiente, que queda marcada como completada.
- [ ] 3.3 Anotar en `openspec/findings/backlog.md` la resolución prevista de `RF-082-002` según lo
  decidido, sin cerrarlo si el cambio material lo ejecuta F2.

## 4. Cierre y verificación

- [ ] 4.1 Verificar que el ADR responde a las cuatro decisiones sin dejar ninguna condicionada, que
  la sección de consecuencias recoge costes además de beneficios, y que hay al menos dos alternativas
  descartadas con motivo.
- [ ] 4.2 Ejecutar `corepack pnpm openspec:validate`,
  `corepack pnpm jup:check -- --change jup-092-frontend-typescript-adr` y
  `corepack pnpm jup:cleanup:check`; registrar el resultado en `review.md` junto con la excepción
  doc-only del harness TDD (sin tester/coder/mutación).
