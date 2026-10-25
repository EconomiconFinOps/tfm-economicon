# Flujo de trabajo Trello + OpenSpec

Trello es la fuente de verdad operativa de Economicon. OpenSpec conserva el diseño técnico versionado y GitHub contiene el código y la revisión de cada cambio.

## Identificador único

Cada tarea utiliza el identificador de su tarjeta Trello en todos los sistemas:

- Tarjeta: `JUP-085`.
- Rama: `feat/JUP-085-auth-session-contract`.
- Cambio OpenSpec: `openspec/changes/jup-085-auth-session-contract/`.
- Pull request: `JUP-085 — Formalizar autenticacion demo y ciclo de sesion`.

No se crea un backlog alternativo ni una numeración paralela en OpenSpec.

## Desarrollo de una tarea

1. Crear o seleccionar la tarjeta Trello y acordar alcance, responsables y criterios de aceptación.
2. Crear una rama desde `develop` con el identificador `JUP-XXX`.
3. Añadir el cambio OpenSpec con `proposal.md`, `design.md`, `tasks.md` y sus escenarios de aceptación.
4. Incluir `JUP: JUP-XXX` y `Trello: <URL>` en la propuesta.
5. Implementar únicamente el alcance aprobado y registrar decisiones duraderas en ADR cuando corresponda.
6. Ejecutar las validaciones técnicas y abrir un pull request hacia `develop`.
7. Mantener Trello actualizado y distribuir implementación, pairing, revisión y validación entre los cuatro integrantes.

## Validaciones

```sh
corepack pnpm openspec:validate
corepack pnpm jup:check -- --change jup-085-auth-session-contract
corepack pnpm jup:cleanup:check
corepack pnpm lint
corepack pnpm test
corepack pnpm build
```
