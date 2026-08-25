# Findings Backlog

| ID | Fecha | Origen | Tipo | Severidad | Scope | Estado | Owner | Accion | Change/Fix |
|----|-------|--------|------|-----------|-------|--------|-------|--------|------------|
| RF-082-001 | 2026-08-25 | jup-082-clean-develop | Repository hygiene | High | In scope | Fixed | Equipo Economicon | Remove personal agent configuration, vendor executables and duplicate task proposals while preserving functional changes | JUP-082 |
| RF-082-002 | 2026-08-25 | jup-082-clean-develop | Existing frontend lint baseline | Medium | Out of scope | Open | Equipo Economicon | Resolve the 49 pre-existing react/prop-types violations in a dedicated Trello task; product source and ESLint configuration are unchanged by JUP-082 | Pending Trello triage |
| RF-083-001 | 2026-08-19 | jup-083-clarify-frontend-migration-assumptions | OpenSpec validation | Medium | Out of scope | Fixed | Equipo Economicon | JUP-082 removed the duplicate proposals and restored strict global OpenSpec validation. | JUP-082 |
| RF-083-002 | 2026-08-19 | jup-083-clarify-frontend-migration-assumptions | Risk/scope | High | Out of scope | Open | Equipo Economicon | Frontend de Economicon es dashboard estático (Figma Make) sin backend/auth/capa de datos; F3 debe añadir esas capas desde el destino. Evaluar Vite 6 vs 5 y TSX sin tsconfig. | Pending Trello triage |
