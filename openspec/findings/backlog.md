# Findings Backlog

| ID | Fecha | Origen | Tipo | Severidad | Scope | Estado | Owner | Accion | Change/Fix |
|----|-------|--------|------|-----------|-------|--------|-------|--------|------------|
| RF-004-001 | 2026-06-24 | hu-004-add-health-checked-at | Test drift | Medium | Out of scope | Fixed | Codex | Replaced `.local` demo auth email with `operator@example.com` in seed, tests, frontend default, and active docs | hu-009-fix-auth-test-email-fixture |
| RF-083-001 | 2026-08-19 | jup-083-clarify-frontend-migration-assumptions | Harness/guardrail | Medium | Out of scope | Open | equipo | `pnpm openspec:validate` falla en global: 21 changes `hu-011`…`hu-031` sin spec deltas ("No deltas found"). `jup-083` valida OK por separado. Lo deben corregir las HUs dueñas. | (pendiente) |
| RF-083-002 | 2026-08-19 | jup-083-clarify-frontend-migration-assumptions | Risk/scope | High | Out of scope | Open | equipo | Frontend de Economicon es dashboard estático (Figma Make) sin backend/auth/capa de datos; F3 de la épica debe AÑADIR esas capas desde el destino, no reconciliarlas. Vite 6 vs 5 y TSX sin `tsconfig`. | (pendiente, replanificar épica) |
