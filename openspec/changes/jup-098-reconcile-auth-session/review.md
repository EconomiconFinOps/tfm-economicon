# Review — JUP-098 reconcile-auth-session

## Grupo 2. Motivo de la invalidación en la capa de acceso

**2.1-2.2 — Red.** `apps/frontend/src/services/api.test.ts` (nuevo, 5 tests): motivo `"expired"` /
`"manual"` entregado a los suscriptores, propagación a múltiples listeners, desuscripción efectiva,
y no notificación cuando la generación ya quedó abandonada. Commit `440ec5f`. Red confirmado: 3/5
fallos en runtime (`vitest`) y 4 errores de `tsc` contra la firma antigua de `invalidateSession`.

**2.3 — Green.** `services/api.ts` (líneas 22-52): tipo `SessionInvalidationReason = "expired" |
"manual"`, `invalidateSession(generation, reason = "manual")`, listener tipado con el motivo. Guard
de generación intacto, `discardResponse` sin tocar, llamada de `fetchJson` sin modificar (sigue
usando el valor por defecto `"manual"`). Commit `75728a4`. 240/240 PASS, `tsc` sin errores.

**2.4 — Mutación.** Config: `.claude/harness/stryker.conf.mjs` → `mutate: ["src/services/api.ts"]`
(harness local, no se commitea). Comando:
```
corepack pnpm --package=@stryker-mutator/core --package=@stryker-mutator/vitest-runner \
  --package=typescript@5.9.3 dlx stryker run ../../.claude/harness/stryker.conf.mjs
```
Resultado: **88.99%** (109 mutantes cubiertos, 97 KILLED, 11 SURVIVED, 1 NO COVERAGE) — por encima
del umbral 80.

De los 11 supervivientes, **2 caen en el código que tocó esta tarea** (líneas 22-52):

- **Línea 37** (`++sessionGeneration` → `--sessionGeneration`, `UpdateOperator`): **mutante
  equivalente**, no se remedia. En todo `api.ts`, `SessionGate.tsx` y `LoginPage.tsx` la generación
  solo se compara con `!==`; ningún código depende de su sentido de incremento, así que ningún test
  puede observar la diferencia sin inventar una aserción artificial sobre el signo interno.
- **Línea 50** (elimina la llamada a `advanceSessionGeneration()` dentro de `invalidateSession`,
  `CallExpression`): **gap real**, remediado. Sin ese avance, una segunda invalidación con la misma
  generación original volvería a notificar en vez de ser un no-op. Test nuevo:
  `apps/frontend/src/services/api.session-generation-advance.test.ts` (1 test) — verificado
  empíricamente contra el mutante (comentando la línea manualmente, confirmando el fallo, revirtiendo
  con `git checkout --`, sin dejar el cambio en el árbol) y contra el código real (pasa). Suite
  completa tras el test nuevo: **241/241 PASS**.

Los otros **9 supervivientes + 1 NO COVERAGE caen fuera del código que tocó esta tarea**: en
`fetchJson` (redacción de mensajes de error, validación de respuesta, guard de generación dentro de
la rama de error), `ApiError` (`this.name`) y `clearSessionMutations` (`mutation.destroy()`). Todo
preexistente de JUP-085/097, no modificado por la tarea 2.3.

**Decisión de alcance (confirmada con el usuario 2026-09-27):** esos 9+1 quedan **fuera de esta
tarjeta**, sin remediar. Motivo: el `proposal.md` de JUP-098 declara explícitamente como fuera de
alcance "reimplementar nada de JUP-085 [...] sus pruebas no se tocan"; escribir tests nuevos para
código que esta tarea no modifica sería expandir ese alcance por un efecto colateral de que Stryker
mutila el archivo entero, no la función tocada. Se registra como hallazgo para quien quiera subir la
cobertura de mutación de `api.ts` en conjunto — ver `openspec/findings/backlog.md` (RF-098-001).

Cierre del grupo: mutation score de lo realmente tocado por esta tarea = 100% de mutantes no
equivalentes muertos (1 real remediado, 1 equivalente justificado). Score global del archivo
(88.99%) queda por encima del umbral 80 igualmente.

**DoD del grupo 2.** `node .claude/harness/check-dod.mjs` desde la raíz falla por RF-093-001 (turbo
resuelve pnpm 11.9.0 global en subprocesos por paquete, en vez de 9.0.0 vía corepack — bloqueo
conocido, pendiente de JUP-102, ajeno a este cambio). Sustituto `pnpm --filter @finops/frontend`:

- `lint` → sin salida, sin errores.
- `typecheck` → sin salida, sin errores (`tsc --noEmit` × 3 configs).
- `test` → 241/241 PASS (240 previos + 1 de remediación de mutación).
- `build` → éxito, `dist/` generado (aviso preexistente de tamaño de chunk, no relacionado).
- Escaneo de secretos del propio `check-dod.mjs` → PASS (esa comprobación sí corre bien desde la raíz).

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
