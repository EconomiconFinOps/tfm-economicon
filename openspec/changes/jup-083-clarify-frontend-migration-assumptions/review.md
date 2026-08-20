# Review: jup-083-clarify-frontend-migration-assumptions

## Result

Accepted

## Scope Reviewed

- `../Economicon/frontend` (inspección en solo lectura; snapshot rama `main`, commit `1fe0030`).
- `docs/spikes/frontend-migration.md` (supuestos `[ASUNCION]` resueltos + checklist + Gap principal).
- `openspec/changes/jup-083-clarify-frontend-migration-assumptions/{proposal,design,specs,tasks}.md`.

## Checklist

- [x] Implementation matches acceptance criteria (cero `[ASUNCION]` en el spike; inventario en `design.md`).
- [x] Tasks are marked accurately in `tasks.md`.
- [x] Tests/checks were executed or exceptions are documented (ver Validation; el fallo global de `openspec:validate` es ajeno a esta HU — `RF-083-001`).
- [x] `proposal.md`, `design.md`, `specs`, and `tasks.md` match the final state.
- [x] Architecture decisions are recorded in ADRs or explicitly marked not applicable.
- [x] No product decision exists only in Engram.
- [x] No old harness structure was reintroduced.

ADR not applicable. Esta HU es inventario/documentación; no acepta ni cambia una decisión de
arquitectura de producto. La adopción de TypeScript (con su ADR) corresponde a una HU posterior de
tooling de la épica.

## Validation

```txt
pnpm hu:check:pre-code -- --change jup-083-clarify-frontend-migration-assumptions -> checks propios OK; openspec:validate global FAIL (RF-083-001)
pnpm exec openspec validate jup-083-clarify-frontend-migration-assumptions -> valid
pnpm openspec:validate (todos los changes) -> FAIL: 21 changes hu-011..hu-031 sin spec deltas ("No deltas found") -> RF-083-001, ajeno a esta HU
test / lint / build -> N/A (doc-only, sin código de producto)
```

## Review Findings

| ID | Tipo | Severidad | Scope | Descripcion | Accion | Backlog |
|----|------|-----------|-------|-------------|--------|---------|
| RF-083-001 | guardrail/harness | Medium | Out of scope | `pnpm openspec:validate` falla en global porque 21 changes de otras HUs (`hu-011`…`hu-031`) no tienen spec deltas ("No deltas found"). `jup-083` valida OK por separado. | defer (lo corrige el equipo dueño de esas HUs) | Added |
| RF-083-002 | risk/scope | High | Out of scope | El frontend de Economicon es un dashboard estático (Figma Make) **sin backend, sin auth y sin capa de datos**. La F3 de la épica debe **añadir** esas capas desde el destino (`services/api.js` + TanStack Query + auth/tenant), no reconciliar una API inexistente. Además Vite 6 (origen) vs Vite 5 (destino) y TSX sin `tsconfig`. | create HU / replanificar épica | Added |

## Risks / Follow-Ups

- Replanificar las HUs F2/F3 de la épica: F3 pasa de "reconciliar capa de servicios" a "construir
  capa de datos + auth desde cero" sobre la UI de Economicon.
- Decidir versión de Vite (6 vs 5) y el setup de TypeScript (tsconfig) en la HU de tooling (F2).
- `RF-083-001` bloquea que `pnpm hu:check` (pre-archive) pase en verde hasta que el equipo arregle
  los `hu-011`…`hu-031`; documentar como excepción si se archiva antes.
