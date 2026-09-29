# Design — JUP-098 reconcile-auth-session

JUP: JUP-098 · ADR aplicable: [ADR-0003](../../../../docs/adr/ADR-0003-frontend-typescript.md) (TypeScript strict). No se propone ADR
nuevo: el mecanismo de sesión ya está decidido y especificado por JUP-085; aquí solo se añade el
motivo de la invalidación y su presentación.

## Context

Motivación en [proposal.md](proposal.md) (sección Why). Requisitos en
[specs/demo-auth-session/spec.md](specs/demo-auth-session/spec.md).

Estado actual del ciclo de fin de sesión (verificado sobre `develop` en `d9271fd`):

- **Un único camino de invalidación.** Todas las causas de fin de sesión desembocan en
  `invalidateSession(generation)` de `apps/frontend/src/services/api.ts`:
  - `fetchJson` ante un `401` numérico de una operación autenticada distinta de `/me` (línea 95);
  - `handleLogout` de `SessionGate`, que usan el botón de cerrar sesión, el botón "Reset session" y
    el efecto que reacciona a **cualquier** error de la consulta de `/me`;
  - el efecto de `SessionGate` que, sin sesión válida al arrancar, limpia restos de tenant y caché.
- **Las invalidaciones de generaciones abandonadas se descartan** en `invalidateSession`
  (`generation !== sessionGeneration` → `return`), antes de avisar a los suscriptores.
- **El `401` fuera de `/me` nunca llega a las pantallas.** `fetchJson` devuelve una promesa que no
  se resuelve (`discardResponse`), a propósito, para que no se disparen callbacks ni reintentos.
- **El `401` de `/me` sí llega a la consulta** como `ApiError` con `status: 401`; la política
  estricta de JUP-097/JUP-085 cierra la sesión ante cualquier error de `/me`.
- `/login` está fuera de `SessionGate` (`src/routes.tsx`); `SessionGate` redirige con
  `<Navigate to="/login" replace />`. Producción usa `createBrowserRouter`; las pruebas montan el
  mismo `routeConfig` sobre `createMemoryRouter`.

Hoy ningún punto de ese camino conserva **por qué** terminó la sesión: la información existe en el
instante de la invalidación y se pierde.

## Goals / Non-Goals

**Goals:**

- Que el motivo "el servidor rechazó el token" viaje desde el punto donde se detecta hasta la
  pantalla de acceso, sin nuevos caminos de invalidación ni cambios en la limpieza.
- Que los contratos de JUP-085 (limpieza, generaciones, política estricta de `/me`, no reintentar
  el `401`) sigan cubiertos por sus pruebas actuales **sin modificarlas**.

**Non-Goals:**

- Cambiar qué errores cierran la sesión: solo se cambia lo que se comunica al cerrarla.
- Mostrar avisos para los fallos de `/me` distintos del `401`: hoy son silenciosos y siguen
  siéndolo (ver decisión 3).
- Internacionalizar o unificar los textos de la interfaz, que hoy mezclan inglés y español.

## Decisions

### 1. La invalidación transporta un motivo tipado

`invalidateSession(generation, reason)` pasa a recibir un motivo de un tipo unión cerrado
(`"expired"` para el rechazo del token; un valor neutro por defecto para el resto) y lo entrega a
los suscriptores de `subscribeSessionInvalidation`. El guard de generación se queda donde está y se
evalúa **antes** de notificar, de modo que un `401` de trabajo abandonado no puede producir el
aviso (escenario "Abandoned work cannot raise the notice").

Alternativas descartadas:

- **Un `SessionExpiredError` que llegue a las pantallas.** Obligaría a resolver la promesa que
  JUP-085 deja pendiente a propósito, reabriendo callbacks y reintentos que su spec prohíbe.
- **Una variable global "último motivo"** en el módulo, leída por `LoginPage`. Estado mutable que
  sobrevive a la navegación y exige un "consumir una vez" frágil; además, no se limpia si el
  operador llega a `/login` por otro camino.
- **Una marca en `sessionStorage`/`localStorage`.** Es persistencia, y la spec exige que el aviso
  no deje rastro en el almacenamiento del navegador.

### 2. El motivo viaja como estado de navegación y `LoginPage` lo consume una vez

El suscriptor de `SessionGate` guarda el motivo en estado de componente junto a la limpieza que ya
hace, y la redirección existente pasa a ser `<Navigate to="/login" replace state={...} />` con una
marca solo cuando el motivo es la expiración.

`LoginPage` lee esa marca **una vez** al montarse, la copia a su propio estado y **sustituye la
entrada del historial por la misma ruta sin estado** (`navigate(pathname, { replace: true, state:
null })`). Motivo: con `createBrowserRouter`, el `state` de navegación se guarda en
`window.history.state` y **sobrevive a una recarga**; sin este paso, recargar `/login` volvería a
mostrar el aviso, violando el escenario "The notice is not persisted". En pruebas se verifica sobre
`router.state.location.state` del `createMemoryRouter`.

Alternativa descartada: parámetro de consulta (`/login?expired=1`). Visible y compartible en la
URL, sobrevive a la recarga y a los marcadores, y cualquiera podría provocar el aviso sin haber
expirado nada.

### 3. Qué cuenta como expiración: `401`, tanto fuera como dentro de `/me`

- **`401` fuera de `/me`** (incluido `/tenants`): `fetchJson` invalida con motivo de expiración.
- **`401` de `/me`**: el efecto de `SessionGate` que ya reacciona a `profileQuery.isError` calcula el
  motivo a partir del error (`ApiError` con `status === 401`) y lo pasa a `handleLogout`. Es el caso
  más frecuente en la práctica: reabrir la aplicación al día siguiente con el token de 480 minutos
  ya caducado.
- **Cualquier otro error de `/me`** (`403`, `422`, `5xx`, red, contrato inválido): la sesión se sigue
  cerrando (política estricta intacta) pero **sin** aviso de expiración. Llamarlo "sesión expirada"
  sería reetiquetar un fallo de servicio como fallo de credenciales, justo lo que la spec de
  JUP-085 prohíbe.
- **Cierre manual, "Reset session" y sesión persistida inválida:** motivo neutro, sin aviso.

El backend devuelve `401` tanto para token caducado como para token corrupto, mal firmado o de un
usuario eliminado (`"Invalid access token."`), sin distinguirlos. El frontend no puede ni debe
distinguirlos tampoco: para el operador, en todos esos casos la acción es la misma (volver a
entrar). El texto del aviso se redacta para ser cierto en todos ellos.

### 4. El `403` de tenant conserva la sesión (criterio 6 de la tarjeta)

Se adopta sin cambios la política que JUP-085 ya especificó y promovió: un `403` en una operación
tenant-scoped **conserva la sesión** y se muestra en la pantalla; el `403` de `/tenants` muestra el
bloque de error de bootstrap con su botón "Reset session".

Motivo: el `403` que produce `get_active_tenant` significa "token válido, pero ese tenant no es
tuyo". Cerrar la sesión no lo arregla —el mismo usuario vuelve a entrar con el mismo alcance— y
tratarlo como expiración mentiría al operador. Además, cambiarlo exigiría un requisito
`MODIFIED` que contradice la spec recién promovida por JUP-085, sin evidencia nueva que lo
justifique. Por coherencia, un `403` tampoco muestra el aviso de expiración.

### 5. Presentación del aviso

- Región `role="status"` (anuncio no intrusivo) en el formulario de acceso, separada del párrafo
  de error de credenciales que ya existe, con un tono visual distinto del rojo de error, usando
  clases del sistema vigente (sin tokens nuevos: eso es JUP-099).
- Texto en inglés, coherente con el resto de `LoginPage` ("Operator login", "Sign in"): *"Your
  session has expired. Sign in again to continue."* Sin datos del servidor ni del token.
- Se oculta en cuanto empieza un nuevo intento (`mutation` deja de estar `idle`), de modo que un
  intento fallido muestra solo su propio error.

## Risks / Trade-offs

- **[Riesgo] Las pruebas de JUP-085 dependen de detalles de `SessionGate` y de `invalidateSession`.**
  → El parámetro de motivo es opcional con valor neutro por defecto; ninguna llamada existente
  cambia de significado. Criterio de cierre: la suite de `tests/auth-session.test.tsx` pasa sin
  editarla.
- **[Riesgo] Carrera entre dos `401` simultáneos** (por ejemplo `/me` y `/billing/summary`). → El
  primero que pasa el guard de generación avanza la generación; el segundo se descarta. Ambos son
  expiración, así que el resultado visible es el mismo.
- **[Riesgo] El efecto de `SessionGate` que llama a `invalidateSession` sin sesión podría
  sobrescribir el motivo.** → Tras una invalidación la generación global ya avanzó y la del
  componente no, así que esa llamada se descarta en el guard. Se cubre con una prueba explícita.
- **[Trade-off] El aviso se pierde si el operador recarga `/login`.** Es deliberado (spec: no es
  estado persistido). El coste es que un operador que recarga no sabrá por qué está en el acceso.
- **[Trade-off] El texto no distingue caducidad de token inválido.** Ver decisión 3: el backend no
  lo distingue y la acción del operador es la misma.

## Migration Plan

Sin migración: cambio solo de frontend, sin datos persistidos nuevos ni contrato de backend.
Reversión: revertir el PR restaura la expulsión silenciosa sin efectos secundarios.
