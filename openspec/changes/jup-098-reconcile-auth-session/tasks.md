> Cada grupo termina en un punto parable: la aplicación arranca y la batería pasa. Al cerrar cada
> grupo se propone commit antes de empezar el siguiente. Ciclo Red/Green con Vitest en los grupos que
> tocan código de producto (2, 3, 4). Sin `any` nuevo ni `@ts-ignore` (ADR-0003). Las pruebas
> existentes de JUP-085 (`tests/auth-session.test.tsx`) **no se editan**: deben seguir en verde tal
> cual en cada grupo.

## 1. Línea base

- [x] 1.1 Ejecutar la suite del frontend sobre la rama recién creada y registrar en `review.md` el
      conteo de pruebas en verde como línea base (sustituto `pnpm --filter @finops/frontend test`
      mientras RF-093-001 siga abierto; dejar constancia de cuál se usó).
- [x] 1.2 Confirmar en `review.md`, con referencia a archivo y línea, qué criterios de la tarjeta
      Trello ya cumple `develop` gracias a JUP-085 (1, 3, 4, 5 y 6) y cuáles quedan para esta tarjeta
      (2), para que la verificación final no dé por hecho nada sin evidencia.

## 2. Motivo de la invalidación en la capa de acceso

- [x] 2.1 **Red:** pruebas unitarias de `services/api.ts` que fijan que los suscriptores de
      invalidación reciben el motivo de expiración cuando una operación autenticada distinta de `/me`
      recibe `401`, y el motivo neutro cuando la invalidación se pide sin motivo. Demostrar Red.
- [x] 2.2 **Red:** prueba de que una invalidación de una generación abandonada no notifica ningún
      motivo a los suscriptores. Demostrar Red o, si ya pasa por el guard existente, registrarlo como
      prueba de caracterización en `review.md`.
- [x] 2.3 **Green:** añadir el motivo tipado a `invalidateSession` y a la suscripción (decisión 1),
      con valor neutro por defecto, sin mover el guard de generación ni cambiar `discardResponse`.
- [x] 2.4 Mutación sobre lo tocado en `services/api.ts`; remediar supervivientes con más pruebas.

## 3. Propagación del motivo desde `SessionGate`

- [x] 3.1 **Red:** prueba de integración (`renderApp`) de que un `401` de `/me` al arrancar con sesión
      persistida termina en `/login` con la marca de expiración en el estado de navegación.
- [x] 3.2 **Red:** pruebas de que un error de `/me` que no es `401` (`403`, `503`, red, contrato
      inválido), el cierre manual y "Reset session" terminan en `/login` **sin** marca de expiración.
- [x] 3.3 **Green:** el suscriptor de `SessionGate` guarda el motivo y la redirección existente lo
      pasa como estado de navegación solo cuando es expiración; el efecto de error de `/me` deriva el
      motivo del `ApiError` con `status === 401` (decisiones 2 y 3). Incluye cablear el otro extremo
      de la decisión 3: la llamada a `invalidateSession(generation)` de `fetchJson` (línea ~106,
      `401` fuera de `/me`) pasa a `invalidateSession(generation, "expired")` — es la misma decisión
      de diseño que el párrafo anterior, ambos extremos del mismo camino de motivo.
- [x] 3.4 Prueba de que la llamada a `invalidateSession` del efecto "sin sesión" no sobrescribe un
      motivo de expiración ya entregado (riesgo del design). Cerrada con evidencia existente (grupo 2
      + tarea 3.1), sin test nuevo — ver `review.md`, confirmado con el usuario.
- [x] 3.5 Mutación sobre lo tocado en `SessionGate.tsx`; remediar supervivientes.

## 4. Aviso en la pantalla de acceso

- [x] 4.1 **Red:** prueba de expiración en vuelo sobre `/overview-legacy` (`GET /billing/summary` →
      `401`) que termina mostrando el aviso de sesión expirada (`role="status"`) en el acceso.
- [x] 4.2 **Red:** prueba de expiración con mutación en curso (ingesta: `POST /jobs/ingest` → `401`)
      que termina mostrando el mismo aviso.
- [x] 4.3 **Red:** pruebas de que el aviso desaparece al iniciar un nuevo intento de acceso y de que
      un intento fallido muestra solo su error de credenciales.
- [x] 4.4 **Red:** pruebas de no persistencia: tras mostrarse el aviso, el estado de navegación queda
      vacío (`router.state.location.state`), no hay marca en `localStorage`/`sessionStorage`, y abrir
      `/login` directamente no muestra el aviso.
- [x] 4.5 **Red:** prueba de que un `403`, `503` o fallo de red en `/billing/summary` no muestra el
      aviso en ningún momento (la sesión se conserva, como ya fija JUP-085).
- [x] 4.6 **Green:** `LoginPage` lee la marca una vez, la copia a su estado, sustituye la entrada del
      historial sin estado y muestra el aviso con el texto y la presentación de la decisión 5, oculto
      en cuanto la mutación de login deja de estar `idle`.
- [x] 4.7 Mutación sobre lo tocado en `LoginPage.tsx`; remediar supervivientes. Cobertura de mutación
      del conjunto tocado (grupos 2-4) por encima del umbral 80.

## 5. Documentación y cierre

- [x] 5.1 Actualizar `docs/spikes/frontend-migration.md`: sustituir el placeholder
      `jup-0xx-reconciliar-auth-tenant` por `JUP-098` / `jup-098-reconcile-auth-session`, marcar sus
      casillas y dejar escrito que login, `/me`, tenant y logout ya estaban hechos antes de empezar y
      que la detección del `401` la aportó JUP-085.
- [x] 5.2 Revisar `apps/frontend/README.md` y, si describe el ciclo de sesión, añadir el aviso de
      expiración; si no lo describe, dejar constancia en `review.md`.
- [x] 5.3 Registrar en `openspec/findings/backlog.md` cualquier hallazgo fuera de alcance que haya
      aparecido (`RF-098-<seq>`), o constancia en `review.md` de que no apareció ninguno.
- [x] 5.4 Verificar que `git diff develop...HEAD --stat` no contiene ningún archivo de `apps/backend/`.
- [x] 5.5 Ejecutar la batería: `openspec:validate`, `jup:check -- --change
      jup-098-reconcile-auth-session`, `jup:cleanup:check`, lint, typecheck, test, build e
      `install --frozen-lockfile`, registrando resultados en `review.md`.
- [x] 5.6 Crear `docs/evidence/JUP-098-validation.md` con comandos, conteos Red/Green, mutation score
      y la verificación de los 8 criterios de la tarjeta, uno a uno.
