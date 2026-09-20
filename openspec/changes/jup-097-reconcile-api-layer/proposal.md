JUP: JUP-097
Trello: https://trello.com/c/dsBZ7y0S/89-jup-097-reconciliar-la-capa-de-datos-del-frontend-con-los-contratos-del-backend

## Why

[JUP-095](../archive/2026-09-12-jup-095-portar-codigo-fuente/) portó la capa de presentación y montó
el enrutado real, pero declaró como non-goal explícito tocar la capa de datos: `services/api.js` pasó
a `api.ts` **sin revisar una sola llamada**. El resultado es una capa HTTP que nadie ha verificado
nunca contra el backend de este repositorio, con dos deudas concretas encima:

- `fetchProfile` (`GET /me`) está implementado, tipado y **jamás se invoca** (`RF-090-003`, abierto
  desde JUP-090). Es código muerto o una llamada que falta, y nadie ha decidido cuál de las dos.
- De las 6 pantallas con ruta propia, **5 pintan datos de demostración** (`RF-095-002`) y no existe
  ningún documento que diga, pantalla por pantalla, qué capacidad concreta de backend le falta a cada
  una. Sin ese mapa, la decisión de épica sobre `RF-091-003` —qué capacidades del backend se
  construyen primero— se toma a ciegas.

Ahora, porque es la última tarjeta de F3 que puede cerrar la capa de datos antes de que
`reconciliar-auth-tenant` empiece a construir sesión **sobre** ella: reconciliar después obligaría a
rehacer ese trabajo.

## What Changes

- **La capa HTTP queda auditada contra los contratos reales.** Cada una de las 9 funciones exportadas
  de `services/api.ts` se verifica en ruta, método, cuerpo y forma de respuesta contra el backend
  levantado. Las desviaciones se corrigen; la ausencia de desviaciones se registra igualmente.
- **`services/api.ts` queda declarado como único punto de acceso HTTP.** Ninguna llamada de red fuera
  de ese módulo, con `VITE_API_BASE_URL` como base y `Authorization: Bearer` + `X-Tenant-Id` como
  único mecanismo de identidad y ámbito.
- **`RF-090-003` se resuelve.** `fetchProfile` queda invocado o eliminado, sin tercera opción. La
  decisión y su motivo se registran en `design.md`.
- **`RF-095-002` se refina, no se cierra.** Cada una de las 5 pantallas de coste queda nombrada junto
  a la capacidad de backend concreta que le falta. Ese mapa es el entregable que alimenta la decisión
  de épica sobre `RF-091-003`.
- **Corrección de referencias obsoletas**: el comentario de `src/routes.tsx` cita "JUP-096" como la
  tarjeta que conectará el Overview; esa numeración ya no existe (la ocupó otra tarjeta ajena).
  También se actualiza el placeholder en español del spike con el slug real de esta tarjeta.

**Lo que esta tarjeta NO hace, por decisión de alcance tomada antes de proponer:**

- **No se toca el backend.** `RF-091-003` (7 capacidades ausentes) y `RF-091-004` (`/billing/summary`
  con `monthly_spend` y `savings_identified` codificados a mano) quedan `Open` sin cambio.
- **No se conecta ninguna pantalla nueva a datos reales.** Consecuencia directa de lo anterior: el
  backend expone hoy exactamente los 9 endpoints que el frontend ya consume, verificado sobre
  `apps/backend/app/api/routes/`. Sin contrato nuevo no hay nada que conectar. Los módulos de
  `src/data/demo/` se conservan intactos.
- **No se retira `/overview-legacy`.** Sigue siendo el único dashboard con datos reales y no existe
  todavía un Overview que lo sustituya. Se reafirma como deuda con dueño explícito.

## Capabilities

### New Capabilities

- `frontend-api-layer`: el frontend accede al backend a través de un único punto centralizado cuyas
  operaciones se corresponden una a una con contratos reales del backend, transportando identidad y
  ámbito de cliente en cada petición autenticada, sobre una base de servicio configurable. Incluye la
  obligación de que toda operación expuesta tenga consumidor y contrato —sin extremos huérfanos en
  ninguna de las dos direcciones— y de que las pantallas sin contrato declaren nombrada la capacidad
  que les falta, en vez de limitarse a señalar que su dato no es real.

### Modified Capabilities

Ninguna. `frontend-navigation-shell` ya exige que las pantallas con backend sobrevivan y que los
datos de demostración se declaren aparte; esta tarjeta cumple esos requisitos sin cambiarlos.
`frontend-typescript-tooling` y `frontend-quality-baseline` tampoco cambian de requisitos.

## Impact

- **Modificado:** `apps/frontend/src/services/api.ts` (correcciones de la auditoría y desenlace de
  `RF-090-003`), `apps/frontend/src/services/contracts.ts` si algún tipo no refleja la respuesta
  real, y `apps/frontend/src/hooks/useDashboardData.ts` si la auditoría alcanza a la única ruta con
  datos reales. Comentario obsoleto de `apps/frontend/src/routes.tsx`.
- **Sin tocar:** `apps/backend/**` (criterio de aceptación explícito: no debe aparecer en el diff de
  la rama), `apps/frontend/src/data/demo/**` y las 5 pantallas de coste.
- **Dependencias:** ninguna nueva. La verificación usa el backend ya existente vía `docker compose`.
- **Documentación:** `openspec/findings/backlog.md` (`RF-090-003` resuelto, `RF-095-002` refinado),
  `docs/spikes/frontend-migration.md` (tarjeta marcada, placeholder sustituido, estado real de F3) y
  `apps/frontend/README.md` si la auditoría cambia algún contrato documentado.
- **Findings esperados:** uno por cada endpoint que el frontend necesite y el backend no ofrezca, si
  la auditoría descubre alguno más allá de los ya registrados.
- **Riesgo declarado:** `RF-095-001`/`RF-087-001` —el backend no configura `CORSMiddleware`— impide
  verificar en navegador real entre `localhost:5173` y `localhost:8000`; `curl` y Postman no lo
  detectan porque no aplican CORS. La verificación de esta tarjeta debe preverlo desde el diseño.
  Corregirlo es responsabilidad del backend y va en tarjeta aparte.
- **Desbloquea:** `reconcile-auth-tenant`, que construirá el flujo de sesión sobre esta capa, y la
  decisión de épica sobre `RF-091-003`.

## Human Approval

- Change: jup-097-reconcile-api-layer
- Approval type: pre-code
- Decision: approved
- Approver: Victor
- Date: 2026-09-20
- Carril: standard
- Scope reviewed: PRD/proposal, TD/design, specs, tasks
- Decisions approved: se aprueban las seis decisiones del `design.md`. (1) **La auditoría se verifica
  contra el backend levantado, no contra `apps/frontend/README.md`**: el README es documentación
  derivada y puede ser justamente lo desviado, así que tomarlo como referencia haría que una
  desviación documentada se validara a sí misma; si discrepan, manda el backend. La lectura de código
  de ambos lados se descarta como método único porque no detecta desajustes de **forma de respuesta**,
  que es donde un `response_model` de FastAPI y una `interface` de TypeScript divergen en silencio
  hasta que una pantalla muestra `undefined`. (2) **`RF-090-003` se resuelve conectando
  `fetchProfile`, no retirándolo**, como revalidación de la sesión persistida en `SessionGate`: la
  validación que añadió JUP-095 (`isSession`) es solo estructural, de modo que un `localStorage`
  fabricado a mano con un token inventado y un `user` bien formado pasa hoy el filtro; el servidor es
  la única autoridad sobre si el token sigue vivo y a quién pertenece. Retirarlo era defendible —el
  login ya devuelve el perfil y `fetchTenants` ya falla con un token muerto— pero dejaría un contrato
  documentado e implementado del backend sin un solo cliente, moviendo la deriva de lado en vez de
  cerrarla, y mantendría la identidad apoyada en un valor de `localStorage` que nadie confirma. Se
  aprueba con **frontera explícita**: se conecta la llamada y se usa su respuesta como identidad, sin
  tocar login, persistencia, guard ni semántica de logout, reutilizando el camino de fallo existente
  (`handleLogout` → `/login`); todo eso es alcance de `reconcile-auth-tenant`. (3) **El mapa de
  carencias vive en dos sitios con papeles distintos**: la capacidad ausente nombrada junto a cada
  módulo de `src/data/demo/` (localizable desde la pantalla que se está depurando) y una tabla única
  en `docs/planning/JUP-097-frontend-data-gap-map.md` (enumerable para decidir qué construir primero).
  No es duplicación: son las dos consultas distintas que exigen los dos escenarios del requisito, y
  dejarlo solo en el documento deja sin pista local a quien depura, que es el problema que describe
  `RF-095-002`. (4) **La forma de las respuestas se fija con pruebas en el límite HTTP, no con un
  validador de esquemas en ejecución**: una librería de validación sería dependencia nueva, decisión
  duradera que ataría a todo el frontend y, por ADR-0003, material de ADR propio — desproporcionado
  para una tarjeta cuyo alcance es auditar. Si la auditoría demuestra deriva recurrente, esa será la
  evidencia para proponerlo aparte. (5) **La verificación asume que el navegador real está
  bloqueado** por `RF-095-001`/`RF-087-001`: comportamiento observable con Vitest y `fetch`
  sustituido, forma real de cada respuesta contra el backend en ejecución por fuera del navegador
  (donde CORS no aplica), y el E2E en navegador se declara **pendiente** en vez de darse por
  verificado por un camino que no lo prueba. (6) **No se requiere ADR nuevo**: la decisión duradera
  que esta tarjeta podría haber necesitado —"una sola capa API centralizada"— ya está tomada como
  decisión 4 del spike de migración y materializada desde JUP-095; conectar `/me` es acotado y
  reversible **dentro** de esa arquitectura, no un cambio de ella. Se citan ADR-0003 y ADR-0004 como
  marco vigente; no se propone ADR-0005.
- Main risks: el principal es **invadir el territorio de `reconcile-auth-tenant` al conectar `/me`**,
  porque toca `SessionGate`, que es donde vive la sesión; mitigación: la frontera de la decisión 2
  limita el cambio al punto mínimo y reutiliza el camino de fallo existente, y la tarea 3.7 es una
  parada de control explícita —si conectar `/me` exigiera rediseñar la sesión, se detiene y se
  reconsidera antes de arrastrar el rediseño. Riesgo secundario: **la auditoría puede encontrar
  deriva que solo el backend puede corregir**; mitigación aceptada por alcance: se registra como
  finding y la corrección va en tarjeta de backend, sin bloquear esta —un desajuste documentado es
  un resultado válido de una auditoría, no un fallo. Riesgo terciario: **sin E2E en navegador algo
  podría romperse solo allí**, consecuencia directa de `RF-095-001`; mitigación: se declara en la
  revisión en vez de disimularse, y refuerza el argumento para priorizar la tarjeta de CORS. Riesgo
  cuarto: **el mapa de carencias envejece**; mitigación: vive junto al código que describe y en un
  documento fechado, y se enuncia allí que la tarjeta que construya cada capacidad retira su fila.
- Required changes before execution: none. Los dos checks del gate pre-código pasan:
  `corepack pnpm openspec:validate --strict` y `corepack pnpm jup:check -- --change
  jup-097-reconcile-api-layer`.
- Notes: **segunda tarjeta de F3** y primera que toca la capa de datos. Alcance recortado por dos
  decisiones tomadas antes de proponer: **no se toca backend** y **no se retira `/overview-legacy`**
  hasta que exista un Overview real que la sustituya. Efecto asumido y explícito: esta tarjeta **no
  conecta ninguna pantalla nueva a datos reales**, porque el backend expone hoy exactamente los 9
  endpoints que el frontend ya consume (verificado sobre `apps/backend/app/api/routes/`); su
  entregable es la capa auditada, `RF-090-003` resuelto y el mapa de carencias que alimenta la
  decisión de épica sobre `RF-091-003`. **Corrección de registro:** la primera tarea que el spike
  asigna a esta tarjeta ("portar `services/api.*` a TS como única capa HTTP") **ya la cerró
  JUP-095**; el grupo 7 lo anota en el spike para que el histórico no quede engañoso. Lleva
  `docs/evidence/JUP-097-validation.md`: no es doc-only. Quedan explícitamente fuera y **sin cambio
  de estado**: `RF-091-003`, `RF-091-004`, `RF-095-001`/`RF-087-001` (backend) y `RF-090-001` (F4).
  `RF-095-002` se refina pero **permanece `Open`**. La numeración de las dos tarjetas restantes de F3
  (`reconcile-auth-tenant`, `unificar-estilos-assets`) sigue sin asignar: la secuencia que asumían los
  documentos de JUP-095 dejó de valer cuando JUP-096 se ocupó para un tema ajeno.
