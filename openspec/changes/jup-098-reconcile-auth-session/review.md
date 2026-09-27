# Review — JUP-098 reconcile-auth-session

## Grupo 1. Línea base

**1.1 — Línea base ejecutada.** Sustituto usado (RF-093-001 sigue abierto, turbo resuelve un pnpm
global en subprocesos por paquete): `pnpm test` ejecutado dentro de `apps/frontend/` (equivalente a
`pnpm --filter @finops/frontend test`, sin pasar por turbo).

```
Test Files  39 passed (39)
     Tests  235 passed (235)
```

Línea base: **235 PASS / 0 FAIL**, 39 archivos. Ninguna de las suites existentes se toca en esta
tarjeta; deben seguir en 235 PASS al cerrar cada grupo posterior.

**1.2 — Qué cumple ya `develop` (JUP-085, `d9271fd`) y qué queda para esta tarjeta.**

| Criterio Trello | Estado en `develop` | Evidencia |
| --- | --- | --- |
| 1. Un 401 limpia la sesión persistida y devuelve al operador al acceso, sin token muerto en `localStorage` | **Cumplido** | `fetchJson` detecta `401` numérico fuera de `/me` e invalida ([api.ts:95-98](../../../apps/frontend/src/services/api.ts#L95-L98)); el suscriptor de `SessionGate` limpia `SESSION_KEY`/`TENANT_KEY` y ambas cachés ([SessionGate.tsx:82-93](../../../apps/frontend/src/layouts/SessionGate.tsx#L82-L93)) |
| 2. El operador ve un mensaje que identifica la expiración de sesión como tal | **Abierto — trabajo de esta tarjeta** | Hoy la redirección a `/login` es silenciosa: `<Navigate to="/login" replace />` sin ningún estado ([SessionGate.tsx:207-209](../../../apps/frontend/src/layouts/SessionGate.tsx#L207-L209)) |
| 3. Un fallo que no sea 401 (500, red, 503) conserva el comportamiento actual | **Cumplido** | Cubierto por `tests/auth-session.test.tsx` ("non-profile query and mutation error retain authentication", "tenant bootstrap error retains the session") |
| 4. La distinción vive en la capa de acceso centralizada, no repetida en cada pantalla | **Cumplido** | Único punto de detección: `fetchJson` en `services/api.ts`; ninguna pantalla implementa su propia lógica de 401 |
| 5. Pruebas de expiración en vuelo sobre `/overview-legacy` y sobre una pantalla con mutación pendiente, ambas Red antes de Green | **Cumplido** (histórico de JUP-085; no aplica "Red antes de Green" retroactivamente) | `tests/auth-session.test.tsx`: `"current query %s invalidates..."` (incluye `/billing/summary` → `/overview-legacy`) y `"current %s mutation 401 clears session..."` (ingesta y conversación) |
| 6. Se decide y se registra si el 403 de tenant recibe el mismo trato que el 401 | **Registrado en JUP-085, reafirmado aquí** | Ver `design.md` decisión 4 de esta tarjeta; `SessionGate` muestra el bloque de error de bootstrap con "Reset session" ante `403` de `/tenants`, sin cerrar sesión automáticamente |
| 7. Cobertura de mutación sobre lo tocado > 80 | Pendiente — se mide sobre lo que toque esta tarjeta (grupos 2-4) | — |
| 8. Ningún archivo de `apps/backend` en el diff | Por construcción (alcance) | Se verifica en la tarea 5.4 |

**Conclusión del grupo:** el único trabajo de producto que queda es el criterio 2. Los grupos 2-4
de `tasks.md` lo implementan; el resto de esta tarjeta es verificación y documentación.

**Checkpoint:** grupo doc-only (sin código de producto, sin tests nuevos) → sin ciclo Red/Green ni
mutación, según excepción de `.claude/harness/workflow.md`. Listo para commit.
