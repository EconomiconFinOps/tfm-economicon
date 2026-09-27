JUP: JUP-098
Trello: https://trello.com/c/YqgPReKN/90-jup-098

## Why

La tarjeta nació para que el frontend distinguiera un `401` del resto de errores: se redactó el
2026-09-21, cuando `fetchJson` lanzaba un `Error` genérico sin mirar `response.status` y un token
caducado dejaba al operador atrapado en pantallas que fallaban como si el backend estuviera caído.

**Ese problema ya no existe en `develop`.** [JUP-085](../archive/2026-09-24-jup-085-auth-session-contract/)
(PR #43, fusionado el 2026-09-24, después de redactarse la tarjeta) lo resolvió en la capa de acceso:

- `fetchJson` detecta el `401` numérico de cualquier operación autenticada distinta de `/me`, antes
  de leer el cuerpo, e invoca `invalidateSession` (`apps/frontend/src/services/api.ts:95-98`).
- `SessionGate` escucha esa invalidación y limpia sesión, tenant activo, caché de consultas y de
  mutaciones, y redirige a `/login` (`apps/frontend/src/layouts/SessionGate.tsx:82-93`).
- `403`, `422`, `5xx` y fallos de red fuera de `/me` conservan la sesión y se muestran en pantalla.
- `tests/auth-session.test.tsx` cubre el `401` en vuelo sobre `/overview-legacy`, `/tenants`,
  `/assistant` y sobre las mutaciones de ingesta y conversación.
- La spec `demo-auth-session` recoge todo ello como requisitos promovidos.

Lo que JUP-085 **no** hizo, y es el único trabajo real que queda de esta tarjeta: la expulsión es
**silenciosa**. Cuando la sesión caduca, el operador aparece en el formulario de acceso sin ningún
mensaje; no puede distinguir "mi sesión ha expirado" de "se ha cerrado sola" o "algo se ha roto". Lo
mismo ocurre al reabrir la aplicación con un token caducado: `GET /me` responde `401` y el operador
vuelve al acceso sin explicación. Es el criterio de aceptación 2 de la tarjeta, y sigue abierto.

## What Changes

- **El operador ve un aviso de sesión expirada al volver al acceso** cuando la sesión terminó
  porque el servidor rechazó el token con `401`, tanto en una operación en vuelo como en la
  revalidación de `/me` al arrancar. El aviso es distinguible del error de credenciales del login y
  de los errores de backend que ya muestran las pantallas.
- **El aviso no aparece cuando la sesión terminó por otra causa**: cierre de sesión manual, sesión
  persistida inválida, o un fallo de `/me` que no sea `401` (`5xx`, red, contrato inválido). Esos
  casos conservan el comportamiento actual; no se reetiqueta un fallo de servicio como expiración.
- **La invalidación de sesión transporta su motivo.** La distinción se hace en la capa de acceso
  centralizada que ya existe (`invalidateSession` y su suscripción), no repetida en cada pantalla.
- **El aviso desaparece al iniciar un nuevo intento de acceso** y no sobrevive a una recarga de la
  página de login: informa de lo que acaba de pasar, no es un estado persistido.
- **Se registra la decisión sobre el `403` de tenant** (criterio 6 de la tarjeta): se adopta la
  política que JUP-085 ya especificó —el `403` fuera de `/me` conserva la sesión y se muestra en la
  pantalla— con su justificación, sin cambiar comportamiento.
- **Se corrige el spike** `docs/spikes/frontend-migration.md`: la tarjeta `reconciliar-auth-tenant`
  queda marcada con su número real y con la historia verdadera (lo que ya hacía el código antes de
  empezar, lo que aportó JUP-085 y lo que aporta JUP-098).

**Fuera de alcance, por decisión tomada al verificar el código antes de proponer:**

- **No se reimplementa nada de JUP-085.** La detección del `401`, la limpieza, el aislamiento por
  generaciones y la política del `403`/`5xx`/red se reutilizan tal cual; sus pruebas no se tocan.
- Refresh tokens o renovación silenciosa (el backend no expone endpoint de refresco).
- Cambiar la persistencia en `localStorage` o el modelo de sesión.
- Cualquier archivo de `apps/backend/**`.
- Rediseño visual: el aviso usa el sistema de estilos vigente; unificarlo es JUP-099.

## Capabilities

### New Capabilities

_Ninguna._

### Modified Capabilities

- `demo-auth-session`: se añade un requisito para comunicar al operador que su sesión expiró cuando
  la invalidación la provoca un `401` del servidor, distinguiéndolo del cierre manual y de los
  fallos que no son de autenticación. Los requisitos existentes de limpieza, generaciones y política
  estricta de `/me` no cambian.

## Impact

- **Código de producto (frontend):** `apps/frontend/src/services/api.ts` (motivo en la
  invalidación), `apps/frontend/src/layouts/SessionGate.tsx` (propagar el motivo al redirigir) y
  `apps/frontend/src/pages/LoginPage.tsx` (mostrar el aviso).
- **Pruebas:** nuevos casos en `apps/frontend/tests/auth-session.test.tsx` y en las pruebas de
  `LoginPage`; las existentes de JUP-085 deben seguir en verde sin modificarse.
- **Documentación:** `docs/spikes/frontend-migration.md`, `apps/frontend/README.md` si describe el
  ciclo de sesión, `docs/evidence/JUP-098-validation.md`.
- **Backend, APIs, dependencias:** sin cambios.
- **ADR:** aplica ADR-0003 (TypeScript strict). No se requiere ADR nuevo: es un ajuste local de
  presentación sobre un mecanismo ya decidido en JUP-085.

## Human Approval

- Change: jup-098-reconcile-auth-session
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-09-27
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Scope adjustment approved: el alcance se reduce respecto al texto original de la tarjeta Trello
  (redactado el 2026-09-21). JUP-085, fusionado el 2026-09-24, ya cumple los criterios 1, 3, 4, 5
  y 6 (detección centralizada del `401` numérico, limpieza y redirección, conservación de la
  sesión ante `403`/`5xx`/red, pruebas en vuelo sobre `/overview-legacy`, ingesta y asistente).
  Esta tarjeta implementa solo el criterio 2 (aviso de sesión expirada) y verifica el resto con
  evidencia, sin reimplementarlo ni editar las pruebas de JUP-085.
- Decisions approved: se aprueban las cinco decisiones del `design.md`. (1) **La invalidación
  transporta un motivo tipado**, con valor neutro por defecto y el guard de generación evaluado
  antes de notificar; se descartan un error nuevo que llegue a las pantallas (reabriría callbacks y
  reintentos que JUP-085 prohíbe), una variable global de "último motivo" y cualquier marca en
  `sessionStorage`/`localStorage`. (2) **El motivo viaja como estado de navegación** y `LoginPage`
  lo consume una vez, sustituyendo la entrada del historial sin estado, porque con
  `createBrowserRouter` ese estado sobreviviría a una recarga; se descarta el parámetro de consulta
  por visible, persistente y falsificable. (3) **Cuenta como expiración el `401`, dentro y fuera de
  `/me`**; cualquier otro error de `/me` sigue cerrando la sesión pero sin aviso, para no
  reetiquetar un fallo de servicio como fallo de credenciales. (4) **El `403` de tenant conserva la
  sesión** y no muestra el aviso: se adopta sin cambios la política ya promovida por JUP-085, porque
  cerrar la sesión no arregla un tenant no autorizado. (5) **El aviso es una región `role="status"`**,
  separada del error de credenciales, con el sistema de estilos vigente (sin tokens nuevos, eso es
  JUP-099), texto en inglés coherente con `LoginPage` y oculto en cuanto empieza un nuevo intento.
- Constraints: ningún archivo de `apps/backend/**` en el diff; sin `any` nuevo ni `@ts-ignore`
  (ADR-0003); ciclo Red/Green por grupo con parada para commit; mutación sobre lo tocado por encima
  del umbral 80. No se requiere ADR nuevo.
