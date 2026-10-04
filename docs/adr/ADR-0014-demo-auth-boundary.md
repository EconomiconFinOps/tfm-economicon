# ADR-0014: Autenticación propia limitada a la demo

- Status: Proposed
- Date: 2026-10-01
- Related JUP/OpenSpec: JUP-061, [contrato de registro de decisiones](../../openspec/specs/architecture-decisions/spec.md)
- Trello: https://trello.com/c/qXoHFxyy
- Responsable de consolidación: Alejandro Aguado; revisión: Paris Arcos Martin; validación: Lucia Mateo; pairing previsto: Victor Mendez.
- Roles actualizados: 2026-10-03; intercambio Lucia/Victor documentado en [validación de Lucia](https://github.com/EconomiconFinOps/tfm-economicon/pull/60#pullrequestreview-5396865126). No acredita pairing realizado.
- Supersedes: none
- Superseded by: none

## Contexto

JUP-085 formaliza login, perfil, JWT, expiración y limpieza de sesión sobre las
librerías y el cliente existentes. El aislamiento tenant es una frontera distinta
cubierta por ADR-0008; CORS está en ADR-0007.

## Decisión documentada para ratificación

Conservar la autenticación propia como frontera de demostración acotada. Reutilizar
FastAPI/PyJWT y el contrato de sesión ya integrado permite demostrar identidad y
expiración sin introducir un proveedor externo ni reconstruir el frontend. Esta
justificación sintetiza el alcance aprobado de JUP-085; no acredita una selección
comparativa ni que la solución sea adecuada para producción pública.

## Alternativas y consecuencias

- IdP externo/OIDC: exigiría configuración de proveedor, flujos y pruebas nuevos;
  JUP-085 lo excluye explícitamente junto con MFA, refresh tokens y revocación
  distribuida. Sigue siendo una decisión futura para producción.
- Eliminar autenticación para la demo: perdería la identidad que sustenta sesión,
  conversaciones privadas y autorización tenant; no satisface el contrato existente.
- Interpretar CORS o X-Tenant-Id como autorización: no válido; CORS controla lectura
  en el navegador y el selector tenant debe contrastarse con membership.

La demo requiere secretos externos y seed opt-in (ADR-0006). No dispone de las
capacidades excluidas anteriores. El leeway JWT de cinco segundos no acredita
reloj estable ni cierra RF-085-002. El coste de migrar a un IdP no está medido.

## Evidencias y aceptación pendiente

- [Diseño canónico JUP-085](../../openspec/changes/archive/2026-09-24-jup-085-auth-session-contract/design.md).
- [Contrato de sesión](../../openspec/specs/demo-auth-session/spec.md).
- [Evidencia JUP-085](../evidence/JUP-085-validation.md).
- [PR #43 integrada](https://github.com/EconomiconFinOps/tfm-economicon/pull/43) y
  [archivo #45](https://github.com/EconomiconFinOps/tfm-economicon/pull/45).
- [CORS](ADR-0007-backend-cors-policy.md), [tenancy](ADR-0008-tenant-isolation-boundaries.md)
  y [secretos](ADR-0006-runtime-secret-boundaries.md) conservan sus aceptaciones.

La aprobación de este registro retrospectivo sigue pendiente; no reabre ni cambia
los contratos ya aceptados.
