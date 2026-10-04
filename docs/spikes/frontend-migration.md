# Plan de migracion del frontend (Economicon -> tfm-economicon)

## Objetivo

Reemplazar por completo el frontend scaffold actual de `apps/frontend` por el frontend del
repositorio externo **Economicon**, preservando la integracion del monorepo (pnpm + turbo + Docker)
y reconectando la capa de datos con los contratos del backend de **este** repositorio.

La unidad operativa de trabajo es la tarjeta Trello `JUP-XXX`, documentada mediante un `OpenSpec
change`, siguiendo [el flujo Trello + OpenSpec](../workflows/trello-openspec.md). Este spike disena
el proceso; no crea los changes ni toca codigo de producto.

```txt
Epica            -> Migrar frontend del repositorio Economicon
Features         -> agrupaciones de trabajo (F1..F5)
Tarjetas JUP     -> OpenSpec changes jup-NNN-slug
Tasks            -> pasos verificables dentro de cada tarjeta
```

## Contexto: origen vs destino

| Aspecto              | Origen (Economicon)        | Destino actual (tfm-economicon)                         |
| -------------------- | -------------------------- | ------------------------------------------------------- |
| Framework            | React 18.3.1 + Vite 6      | React 18.3.1 + Vite 5                                   |
| Lenguaje             | **TypeScript**             | **JavaScript** (JSX)                                    |
| Datos/estado         | Ninguna (datos estáticos/mock) | TanStack Query (`@tanstack/react-query`)                |
| Routing              | react-router 7 (`createBrowserRouter`) | Estado manual `activeView` en `App.jsx` (sin router)    |
| Capa API             | Ninguna (sin `fetch`/`axios`) | `src/services/api.js` centralizado                      |
| Auth/sesion          | Ninguna (sin login/tenant) | `localStorage` (`finops.session`, `finops.activeTenant`) |
| Estilos              | Tailwind v4 (shadcn/ui y MUI declarados pero **sin uso real**, JUP-091) | Un unico `src/styles/main.css`, tema oscuro             |
| Empaquetado monorepo | repo independiente         | `@finops/frontend`, pnpm workspace + turbo + Docker     |

**Gap principal:** el origen llega en **TSX** (sin `tsconfig` ni dependencia `typescript`:
transpilado por esbuild, sin type-check) y el destino en JavaScript; el reemplazo completo obliga a
**adoptar TypeScript** en `apps/frontend`. Además — y es lo más relevante confirmado en JUP-083 — el
origen es un **dashboard estático de Figma Make sin backend, sin auth y sin capa de datos**: la
migración **no realinea** una API existente, sino que debe **añadir desde el destino** toda la capa
de datos (`services/api.js` + TanStack Query) y el flujo de auth/sesión/tenant sobre la UI de
Economicon.

### Hechos del destino que la migracion debe respetar (verificados)

- Estructura: `apps/frontend/src/{components,hooks,layouts,pages,services,styles}` mas `Dockerfile`,
  `index.html`, `vite.config.js`, `eslint.config.js`, `package.json`.
- Nombre del paquete: `@finops/frontend`. Scripts: `dev` (vite `--host 0.0.0.0 --port 5173`),
  `build`, `preview`, `lint`, `test`, `docker:build`.
- `src/services/api.js` centraliza el acceso HTTP. Base: `VITE_API_BASE_URL`
  (def. `http://localhost:8000`). Headers: `Authorization: Bearer <token>` y `X-Tenant-Id`.
- Contratos del backend (ver [apps/frontend/README.md](../../apps/frontend/README.md)):
  `GET /health`, `POST /auth/login`, `GET /me`, `GET /tenants`, `GET /billing/summary`,
  `POST /jobs/ingest`, `GET|POST /assistant/conversations`,
  `GET /assistant/conversations/{id}`, `POST /assistant/conversations/{id}/messages`.
- Seed local de acceso: `operator@example.com` / `secret`.
- Monorepo: `pnpm@9.0.0` + `turbo`. Servicio `frontend` en `docker-compose.yml` (puerto 5173,
  `VITE_API_BASE_URL`, depende de `backend` healthy). **Corregido en JUP-090:** el servicio no tiene
  `env_file`; `VITE_API_BASE_URL` viaja como `environment:` inline.
- **Regla dura del repo: prohibido `npm i`.** Solo `pnpm`.

## Estrategia: reemplazo completo

Se sustituye el codigo fuente y la configuracion de lenguaje, pero se conserva el "pegamento" del
monorepo. La frontera es:

**Se reemplaza**

- Todo `apps/frontend/src/**` (componentes, pages, hooks, layouts, services, styles actuales).
- Configuracion de lenguaje/lint relacionada con JS que cambie a TS (`eslint.config.js`, `jsconfig`
  si existiera).
- `index.html` y entrypoint si el origen difiere.

**Se preserva (o se adapta sin perder)**

- `package.json`: nombre `@finops/frontend`, scripts del monorepo, flags de puerto/host.
- Integracion Docker: `Dockerfile` y servicio `frontend` de `docker-compose.yml` (puerto 5173).
- Variable `VITE_API_BASE_URL` y el patron de una unica capa API centralizada.
- Los **contratos del backend** de este repo como fuente de verdad (no los del backend de Economicon).
- Pipeline turbo (`dev/build/lint`) y pertenencia al workspace pnpm.

> Rollback: no se borra el scaffold actual hasta que la migracion valide end-to-end. Trabajar en una
> rama dedicada y reemplazar por slices verificables, no en un unico "big bang".

## Decisiones clave y supuestos

### Decisiones

1. **Adopcion de TypeScript en `apps/frontend`.** Es una decision transversal y duradera (afecta
   tooling, build, lint y todas las tareas futuras del frontend) -> **requiere ADR** en `docs/adr/`
   usando `docs/templates/adr.md`, segun [AGENTS.md](../../AGENTS.md). Debe crearse/enlazarse antes
   de implementar la feature de tooling. **Resuelto en JUP-092:**
   [docs/adr/ADR-0003-frontend-typescript.md](../adr/ADR-0003-frontend-typescript.md) (`Accepted`)
   — `strict: true` desde el inicio, `allowJs: true` durante la migracion, type-check obligatorio en
   CI, y `tsconfig` a nivel de `apps/frontend`. **`RF-082-002` (49 violaciones `react/prop-types` en
   9 archivos `.jsx`) permanece abierto hasta que F3 migre esos archivos a `.tsx` con cobertura real
   de tipos** — desactivar la regla solo para `.ts`/`.tsx` en F2 no los alcanza (correccion de
   consistencia via revision de PR).
2. **Vite se mantiene** como bundler (origen y destino ya usan Vite) -> el modelo de build es
   compatible; no hay migracion de bundler.
3. **El backend de este repo manda.** La capa API del origen se reescribe contra los contratos
   listados arriba; no se importan endpoints de Economicon que aqui no existan sin antes decidir si
   se crea backend (eso seria otra tarjeta/epica, fuera de este alcance).
4. **Una sola capa API centralizada** (se mantiene el patron de `services/api.js`, portado a TS).

### Supuestos del origen (confirmados en JUP-083)

- **Confirmado (T1):** React **18.3.1** (peerDeps), compatible con el destino. Vite **6** en el
  origen frente a Vite **5** en el destino → salto de major a decidir al reconciliar el tooling.
- **Confirmado (T2):** react-router **7.13.0** con `createBrowserRouter` (5 rutas bajo un `Layout`).
  Dependencia nueva respecto al destino (hoy sin router). Se adopta el routing del origen.
- **Confirmado (T3):** ninguna librería de datos/estado ni capa API en el origen (dashboards con
  datos estáticos/mock). El destino usa TanStack Query → la migración añade toda la capa de datos.
- **Confirmado (T4):** el origen no tiene auth/sesión/tenant. El destino sí (`Bearer` +
  `X-Tenant-Id` + sesión en `localStorage`) → la migración añade el flujo de auth del destino.
- **Confirmado (T5):** Tailwind CSS v4 + shadcn/ui (Radix) + MUI 7 + `next-themes`, con estilos en
  `src/styles/`. El destino usa un único `main.css` plano → cambio grande de sistema de estilos.
  **Matizado en JUP-091:** de ese stack solo Tailwind v4 está realmente en uso. **MUI 7 y
  `@emotion/*` no se importan en ningún sitio**, y los 48 componentes de shadcn/ui son código muerto
  que ninguna pantalla usa (su único import relativo es `./ExportButton`). El cambio de sistema de
  estilos es, por tanto, **menor** de lo que sugería este supuesto. Ver `RF-091-001`/`RF-091-002` y
  [el inventario del origen](../planning/JUP-091-economicon-source-inventory.md).
- **Confirmado (T6):** iconos vía `lucide-react`; sin `src/assets` materializado ni fuentes propias
  (`fonts.css` vacío). Licencias en `ATTRIBUTIONS.md`: shadcn/ui (MIT) y fotos de Unsplash.

### Checklist de inspeccion del origen (completado en JUP-083)

```md
- [x] package.json: React 18.3.1, Vite 6 (destino Vite 5), sin dependencia `typescript`.
- [x] Entrypoint `src/main.tsx`, `index.html` y config Vite; **sin `tsconfig`** (TSX sin type-check).
- [x] Routing y pantallas: react-router 7 (`createBrowserRouter`), 5 pantallas bajo `Layout`.
- [x] Capa API y endpoints: **no hay capa API** (0 `fetch`/`axios`); datos estáticos/mock.
- [x] Auth/sesion y tenant: **no existen** en el origen.
- [x] Estilos y assets: Tailwind v4 + shadcn/ui + MUI; iconos lucide-react; sin `src/assets`.
- [x] Variables `VITE_*`: **ninguna** en el origen.
```

## Descomposicion: Epica -> Features -> Tarjetas JUP -> Tasks

**Epica:** *Migrar frontend del repositorio Economicon* a `apps/frontend` mediante reemplazo
completo, preservando la integracion del monorepo y reconectando con los contratos del backend
actual.

Cada tarea nace en Trello y su cambio OpenSpec se nombra `jup-NNN-slug` usando el identificador real
de la tarjeta. El carril sugerido es `light` para cambios acotados sin impacto arquitectonico, o
`standard` para comportamiento nuevo o multi-area. La numeracion `NNN` es indicativa hasta crear cada
tarjeta en Trello.

### F1. Preparacion e inventario

**JUP `jup-090-inventory-current-frontend`** — carril `light`
- [x] Documentar que se preserva del destino (nombre paquete, scripts, puerto, Docker, contratos). Ver
  [docs/planning/JUP-090-frontend-migration-baseline.md](../planning/JUP-090-frontend-migration-baseline.md).
- [x] Marcar archivos a reemplazar vs. a conservar. Ver la misma línea base, sección
  "Clasificación archivo a archivo".
- [x] Definir criterios de aceptacion de paridad funcional (login -> tenant -> dashboard). Ver la
  misma línea base, sección "Criterios de paridad funcional".

**JUP `jup-091-inventory-economicon-frontend`** — carril `light`
- [x] Completar el "Checklist de inspeccion del origen" y confirmar todos los supuestos en JUP-083.
- [x] Listar dependencias del origen y clasificarlas (mantener / sustituir / descartar). Ver
  [docs/planning/JUP-091-economicon-source-inventory.md](../planning/JUP-091-economicon-source-inventory.md),
  seccion "Clasificacion de dependencias": 61 declaradas → 11 `MANTENER`, 2 `SUSTITUIR`, 48 `DESCARTAR`.
- [x] Enumerar endpoints que el origen consume y mapearlos a los contratos del backend de este repo.
  Ver la misma linea base, seccion "Mapeo de pantallas a contratos del backend": el origen no consume
  ningun endpoint (datos estaticos), y de los 14 datos que muestra solo 2 tienen contrato, ambos
  parciales. Siete capacidades ausentes agrupadas en `RF-091-003`.

**JUP `jup-092-frontend-typescript-adr`** — carril `standard` (decision de arquitectura)
- [x] Redactar ADR `docs/adr/ADR-0003-frontend-typescript.md` con `docs/templates/adr.md`.
- [x] Estado `Proposed` -> `Accepted` tras HiTL.
- [x] Enlazar el ADR desde este spike (decision nº 1, arriba).
- [ ] Enlazar el ADR desde el `design.md` de cada tarjeta de F2 y F3 **al crearse** — no es tarea de
  JUP-092, que ya termino; queda registrado aqui y en la seccion de seguimiento del propio ADR como
  requisito de esas tarjetas futuras.

### F2. Tooling y dependencias

**JUP [`jup-093-configure-typescript`](../../openspec/changes/archive/2026-09-06-jup-093-configure-typescript/) — carril `standard`**
- [x] Anadir `typescript`, `@types/react`, `@types/react-dom` (y tipos necesarios) con **pnpm**.
- [x] Crear `tsconfig.json` (y `tsconfig.node.json` para la config de Vite).
- [x] Ajustar `vite.config` a `.ts`; verificado arranque `pnpm dev` (host/puerto del monorepo intactos).
- [x] Migrar `eslint.config.js` a soporte TS (parser/plugin TypeScript) sin romper `pnpm lint` (línea
  base de 49 violaciones `react/prop-types`, `RF-082-002`, intacta). Añadido también, más allá de las
  cuatro tareas de este spike, el type-check como séptimo check obligatorio de CI (ADR-0003, decisión
  3): ver [ADR-0003](../adr/ADR-0003-frontend-typescript.md).

**JUP [`jup-094-reconcile-package-json`](../../openspec/changes/archive/2026-09-07-jup-094-reconcile-package-json/) — carril `standard`**
- [x] Fusionar dependencias del origen en `apps/frontend/package.json`: las 11 `MANTENER` del
  inventario de JUP-091, ajustando `react-router`/`recharts`/`lucide-react` a las versiones exactas
  del origen tras un salto de mayor incompatible del resolutor (mismo patrón que `typescript@7` en
  JUP-093). Vite se mantiene en la serie 5: ninguna dependencia entrante fuerza el 6.
- [x] Conservar nombre `@finops/frontend`, `type: module` y los scripts del monorepo (puerto 5173).
- [x] Instalar con `pnpm install` desde la raiz; **nunca** `npm i`.
- [x] Verificar lockfile actualizado y `pnpm install --frozen-lockfile` reproducible.
- [x] **Añadido durante el `apply`, más allá de las cuatro tareas de este spike:** adopción de
  shadcn/ui (subconjunto de 6 paquetes Radix) para F3, registrada en
  [ADR-0004](../adr/ADR-0004-frontend-shadcn-ui.md) y cerrando `RF-091-002`.

**F2 (Tooling y dependencias) queda completa** con JUP-093 y JUP-094.

### F3. Reemplazo del codigo fuente

**JUP `jup-095-portar-codigo-fuente`** — carril `standard` — **completa**
- [x] Reemplazar `src/**` por el codigo de Economicon (componentes, pages, hooks, layouts).
- [x] Reconciliar `index.html` y entrypoint (`main.tsx`).
- [x] Asegurar arranque sin errores de tipo ni de runtime (`pnpm dev`, `pnpm build`).

**JUP [`jup-097-reconcile-api-layer`](../../openspec/changes/archive/2026-09-21-jup-097-reconcile-api-layer/) — carril `standard` — completa**
- [x] Portar `services/api.*` a TS como **unica** capa HTTP. **Ya lo había cerrado JUP-095**: al
  proponer esta tarjeta, `api.ts`/`contracts.ts` ya existían tipados con las 10 operaciones (grupo 5
  de JUP-095, no de esta tarjeta) — este spike quedaba desactualizado al listarlo aquí como pendiente.
  El trabajo real de esta tarjeta fue auditar, no portar.
- [x] Alinear cada llamada a los contratos reales: `/health`, `/auth/login`, `/me`, `/tenants`,
      `/billing/summary`, `/jobs/ingest`, `/assistant/conversations...` — son **10** endpoints (el
      `proposal.md`/`design.md`/`tasks.md` de la propia tarjeta decían "9" antes de auditar, error de
      conteo propio corregido al hacerlo, no heredado de este spike). Auditadas las 10, cero
      desviaciones.
- [x] Conservar `VITE_API_BASE_URL` y headers `Authorization: Bearer` + `X-Tenant-Id`. Verificado:
      único punto de red es `services/api.ts`, ninguna dirección de backend fijada en pantallas.
- [x] Registrar como finding cualquier endpoint del origen sin equivalente en el backend. Ninguno
      nuevo: la auditoría no encontró desviaciones que requirieran finding de contrato.
- [x] Resolver `RF-090-003` (`openspec/findings/backlog.md`): `fetchProfile` (`GET /me`) se
      **conecta** en `SessionGate` como revalidación de la sesión persistida (decisión 2 del
      `design.md` de la tarjeta) — cierra a `Fixed`.
- [x] **Añadido durante el `apply`, más allá de las cuatro tareas de este spike:** mapa de carencias
  por pantalla, dato a dato, en
  [docs/planning/JUP-097-frontend-data-gap-map.md](../planning/JUP-097-frontend-data-gap-map.md),
  refinando `RF-095-002` (permanece `Open`, es insumo para la decisión de épica sobre
  `RF-091-003`, no la resuelve). Por decisión de alcance tomada antes de proponer, **no se tocó
  backend y no se retiró `/overview-legacy`**: sigue siendo el único dashboard con datos reales, sin
  Overview real que la sustituya todavía.

**JUP [`jup-098-reconcile-auth-session`](../../openspec/changes/archive/2026-09-27-jup-098-reconcile-auth-session/) — carril `standard` — completa**
- [x] Adaptar login/sesion al flujo del backend (token + perfil `/me`). **Ya lo había cerrado
      JUP-085** (fusionado el 2026-09-24, entre que este spike listaba la tarjeta como pendiente y que
      se propuso): `LoginPage` persiste `{accessToken, user}`, `SessionGate` revalida contra `GET /me`
      al arrancar, y JUP-085 añadió además la detección centralizada del `401` (limpia sesión y
      redirige al acceso). El trabajo real de esta tarjeta no fue adaptar el login, sino comunicar al
      operador *por qué* volvió al acceso.
- [x] Mantener seleccion de tenant activo y propagacion de `X-Tenant-Id`. **Ya hecho** (verificado
      antes de proponer, sin tocar en esta tarjeta): el tenant activo se auto-selecciona, sobrevive a
      la navegación, se persiste y propaga `X-Tenant-Id` en las 6 operaciones que lo exigen.
- [x] Verificar persistencia de sesion y logout. **Ya hecho** (JUP-085): logout limpia sesión, tenant
      y caché de react-query, y redirige al acceso; un `401` en cualquier operación autenticada sigue
      el mismo camino.
- [x] **El trabajo real de esta tarjeta, no descrito en el placeholder original:** el frontend
      distinguía un `401` (JUP-085) pero expulsaba al operador al acceso **en silencio**, sin decirle
      que su sesión había expirado. JUP-098 añade un aviso `role="status"` ("Your session has expired.
      Sign in again to continue.") que aparece solo cuando la invalidación la provoca un rechazo del
      servidor, distinguible del error de credenciales y de los fallos de backend que ya se mostraban;
      no sobrevive a una recarga de `/login` ni al botón "atrás" del navegador. El `403` de tenant
      conserva la sesión, tal como ya especificaba JUP-085 — se reafirma la decisión, sin cambiarla.

**JUP [`jup-099-unify-styles-assets`](../../openspec/changes/archive/2026-10-01-jup-099-unify-styles-assets/) — carril `standard` (el spike la proponía `light`) — implementada, validada y archivada el 2026-10-01; integración de PR #54 pendiente**
- [x] Unificar el sistema de estilos. **El problema real era mayor que "duplicados con el tema
      oscuro"**: convivían tres fuentes de color (241 hexadecimales y 229 utilidades de la paleta de
      Tailwind escritos a mano en las pantallas, más los tokens de `theme.css`, que eran el tema por
      defecto de shadcn y solo consumían los primitivos que ninguna pantalla usaba). Ahora hay **una
      única paleta en `:root`** con tokens de nombre funcional y el valor exacto que sustituyen; se
      retiró el bloque `.dark` y el apaño `class="dark"` de JUP-095; dos tests estáticos impiden que
      vuelva un color literal (`color-tokens.guard.test.ts`, `theme-palette.test.ts`). Decisión
      duradera en [ADR-0012](../adr/ADR-0012-frontend-color-tokens.md).
- [x] Migrar fuentes/iconos/imagenes y verificar licencias. **No había nada que migrar**: no se portó
      ninguna imagen (las fotos de Unsplash del origen no llegaron), no hay fuentes y los iconos son de
      `lucide-react`. Lo que sí exigía atribución era el código de shadcn/ui copiado al repositorio
      (MIT): [`apps/frontend/ATTRIBUTIONS.md`](../../apps/frontend/ATTRIBUTIONS.md).
- [x] Confirmar que no quedan referencias a estilos del scaffold antiguo. Quedaban tres menciones a
      `main.css` en comentarios de `MetricCard`, `SectionCard` y `StatusPill`; retiradas. Búsqueda en
      `apps/frontend`: 0 resultados.
- [x] **Añadido durante el `apply`, más allá de las tareas de este spike:** verificación visual con
      Chromium real, 34 escenarios antes y después (incluidos estados de error, carga, "sin tenant" y
      los tooltips de las gráficas): sin regresión de color de pantalla; las cuatro diferencias que
      quedan (fondo del `body`, color heredado por los iconos, un borde por defecto y el redondeo de
      un degradado) están medidas y aceptadas. Demostrado que cambiar un token solo en `theme.css`
      cambia toda la interfaz. Hallazgos nuevos: `RF-099-002` (clases interpoladas que Tailwind no
      detectaba y tonos sin estilo en las pantallas de demostración), `RF-099-003` (tonos casi
      iguales no consolidados), `RF-099-001` (referencias a herramientas locales en documentación
      archivada) y `RF-099-004` (71 enlaces relativos rotos por el archivado de changes). Además, esta rama resolvió el arrastre de JUP-098 (`RF-098-004`, referencias locales
      en su evidencia, enlaces rotos y comentarios de test).

### F4. Integracion de plataforma (monorepo/runtime)

**JUP `jup-0xx-verificar-docker-compose`** — carril `light` — **resuelta por JUP-049 y JUP-050, sin
tarjeta propia** (verificado sobre `develop` en `dad5662` el 2026-10-03; no llegó a abrirse)
- [x] Validar `Dockerfile` con el nuevo build TS (`docker compose up --build frontend`): JUP-050
  levanta el stack desde un clon limpio con el frontend incluido, y `tools/docker-topology.test.mjs`
  comprueba que el frontend se construye antes de arrancar `vite preview`.
- [x] Confirmar puerto 5173 y `VITE_API_BASE_URL` en `docker-compose.yml`: el servicio publica
  `${FRONTEND_HOST_PORT:-5173}:5173`, pasa `VITE_API_BASE_URL` en `build.args` y no usa `env_file`
  (`RF-090-002`, `Fixed`); el `README.md` documenta que cambiarlo exige reconstruir y
  `pnpm local:smoke` comprueba la respuesta del frontend.
- [x] Resolver `RF-090-001` (`Fixed`, JUP-050): `apps/frontend/Dockerfile` copia `pnpm-lock.yaml` y
  `pnpm-workspace.yaml` (línea 7) e instala con `--frozen-lockfile --filter @finops/frontend...`
  (línea 9); JUP-050 lo demuestra con un control positivo (con un `package.json` desincronizado el
  build falla con `ERR_PNPM_OUTDATED_LOCKFILE`).

**JUP [`jup-103-verify-turbo-workspace`](../../openspec/changes/jup-103-verify-turbo-workspace/)** —
carril `light` — **implementada**
- [x] Confirmar `pnpm dev` (turbo paralelo) levanta frontend junto a backend/processor: turbo lanza en
  paralelo las cuatro tareas con el pnpm correcto, **pero por sí solo no deja sirviendo a backend ni
  a processor** (turbo en modo `strict` no les pasa su configuración y el `.env` de Compose usa
  nombres internos de Compose). Con `--env-mode=loose` y un archivo de entorno con `127.0.0.1` las
  cuatro responden `200`. Documentado en el `README.md`; `RF-103-001` a `RF-103-003`.
- [x] Confirmar `pnpm build` y `pnpm lint` pasan via turbo, y también `test` y `typecheck`: pasan en
  las máquinas con `corepack enable` hecho. `RF-093-001` resultó ser de entorno (un pnpm global por
  delante de corepack en el `PATH`) y queda `Fixed`; la corrección es `corepack enable` una vez por
  máquina, documentada en el `README.md`.

**F4 (Integración de plataforma) queda completa** con JUP-049 y JUP-050 (Docker) y JUP-103 (turbo).

### F5. Verificacion y cierre

**JUP `jup-0xx-validacion-e2e`** — carril `standard`
- [ ] E2E con seed `operator@example.com` / `secret` contra backend local.
- [ ] Recorrer login -> seleccion de tenant -> overview -> ingesta -> asistente.
- [ ] Registrar comandos exactos y resultados en la revision de la tarjeta JUP.

**JUP `jup-0xx-checks-y-archive`** — carril `light`
- [ ] `pnpm openspec:validate`, `pnpm lint`, `pnpm build`, `pnpm install --frozen-lockfile`.
- [ ] Confirmar ADR de TS `Accepted` y documentacion sincronizada (READMEs, architecture).
- [ ] Revision del equipo y archivado de los cambios OpenSpec de la epica.

## Manejo de conflictos con archivos existentes

Aunque la estrategia es reemplazo completo, varios archivos del destino no deben perderse: hay que
reconciliarlos, no sobrescribirlos a ciegas.

| Archivo / area               | Conflicto                                          | Regla de resolucion                                                                 |
| ---------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `package.json`               | Deps del origen vs. nombre/scripts/puerto del repo | **Fusionar**: deps del origen + conservar `@finops/frontend`, scripts y puerto 5173 |
| `pnpm-lock.yaml` (raiz)      | Lockfile desactualizado                            | Regenerar con `pnpm install` desde la raiz; commitear el lockfile                   |
| `eslint.config.js`           | Config JS vs. necesidad de TS                      | Migrar a flat config con parser/plugin TS; mantener reglas react/react-hooks        |
| `tsconfig.json`              | No existe en destino                               | **Crear nuevo**; alinear `paths`/`jsx` con el origen                                |
| `vite.config.(js->ts)`       | Plugins/alias divergentes                          | Tomar el del origen pero conservar host/puerto del monorepo                         |
| `index.html`                 | Entrypoint `.jsx` vs `.tsx` y metadatos            | Usar el del origen; conservar `<div id="root">` y titulo del producto               |
| `src/services/api.*`         | Dos capas API distintas                            | **Una sola fuente**, alineada a los contratos del backend de este repo              |
| `src/styles/*`               | Tema/CSS duplicados                                | Unificar en el sistema del origen; eliminar `main.css` antiguo al validar           |
| `.env` / `VITE_API_BASE_URL` | Variables del origen vs. del repo                  | Conservar `VITE_API_BASE_URL`; documentar cualquier `VITE_*` nueva                  |
| `Dockerfile`                 | Pasos de build JS vs. TS                           | Adaptar build a TS; conservar puerto y comando de arranque                          |
| `node_modules/.vite`         | Cache de build viejo                               | Limpiar cache tras el cambio de tooling                                             |

Regla general: **resolver conflicto por conflicto y verificar el arranque tras cada area**, no
acumular todo para un unico merge final.

## Instalacion de dependencias

Este repo es **pnpm-only**. No usar `npm i` bajo ninguna circunstancia.

```powershell
# Anadir dependencias de runtime del origen al paquete del frontend
pnpm --filter @finops/frontend add <paquete> [<paquete> ...]

# Anadir dependencias de desarrollo (tooling TS, tipos, lint)
pnpm --filter @finops/frontend add -D typescript @types/react @types/react-dom <otros>

# Instalar todo el workspace desde la raiz
pnpm install

# Verificacion reproducible (debe pasar sin tocar el lockfile)
pnpm install --frozen-lockfile
```

Notas:

- El lockfile (`pnpm-lock.yaml`) vive en la raiz del monorepo; commitearlo siempre que cambien deps.
- Mantener las versiones de React alineadas entre origen y destino para evitar duplicados de React
  en el arbol de dependencias.
- Si el origen trae dependencias que aqui no aplican (backend ficticio, mocks, libs no usadas),
  descartarlas en vez de arrastrarlas.

## Recomendaciones

1. **Rama dedicada y slices verificables.** Una rama de migracion; avanzar feature por feature con
   arranque verificado en cada paso. Evitar el "big bang".
2. **El backend de este repo es la fuente de verdad de contratos.** Adaptar el frontend a el; no al
   reves. Cualquier endpoint del origen sin equivalente se registra como finding.
3. **ADR antes de tooling.** Crear/aceptar el ADR de adopcion de TypeScript antes de tocar la
   configuracion de build/lint. **Hecho en JUP-092:**
   [ADR-0003](../adr/ADR-0003-frontend-typescript.md) (`Accepted`).
4. **Seguir el flujo Trello/JUP + OpenSpec.** Validar cada cambio con
   `pnpm jup:check -- --change jup-NNN-slug` y solicitar revision humana mediante pull request.
5. **Preservar rollback.** No borrar el scaffold actual hasta validar E2E con el seed local.
6. **Decisiones trazables y neutrales.** Contratos, resultados de revision y decisiones duraderas
   viven en Trello/OpenSpec/Git/ADR, sin depender de herramientas personales.
7. **Documentacion sincronizada.** Actualizar `apps/frontend/README.md` y, si cambia la arquitectura,
   `docs/architecture.md`, al cerrar la epica.

## Riesgos y mitigaciones

| Riesgo                                              | Impacto                         | Mitigacion                                                              |
| --------------------------------------------------- | ------------------------------- | ---------------------------------------------------------------------- |
| Contratos del origen != backend de este repo        | Pantallas rotas / datos vacios  | Tarjeta JUP de reconciliacion de API; findings para huecos del backend |
| Ruptura del build al introducir TypeScript          | Frontend no compila             | ADR + tarea JUP de tooling aislada; verificar `pnpm build` antes de portar src |
| Perdida del flujo login/seleccion de tenant         | App inutilizable                | Criterios de aceptacion E2E con seed; preservar `Bearer` + `X-Tenant-Id` |
| Divergencia de tooling (lint/Vite/Docker)           | CI/turbo en rojo                | Reconciliar configs como tareas explicitas; verificar via turbo y Docker |
| Migracion "big bang"                                | Difícil de revisar y revertir   | Slices por feature; rama dedicada; rollback hasta validar              |
| Arrastrar dependencias inutiles del origen          | Bundle pesado / superficie extra | Clasificar deps (mantener/sustituir/descartar) en F1                   |

## Checklist operacional de la migracion

Alineado con [el flujo Trello + OpenSpec](../workflows/trello-openspec.md). Aplicar **por cada
tarjeta JUP** de la epica.

```md
- [ ] Crear la tarjeta Trello y el OpenSpec change `jup-NNN-slug` con su identificador real.
- [ ] Completar proposal, design, specs (si aplica) y tasks verificables.
- [ ] Evaluar ADR; para la adopcion de TS, crear/enlazar ADR; en el resto, marcar no aplicable.
- [ ] Validar trazabilidad con pnpm jup:check -- --change <change-name>.
- [ ] Implementar el alcance aprobado y marcar tasks completadas.
- [ ] Ejecutar checks del carril: pnpm openspec:validate, lint, build, install --frozen-lockfile.
- [ ] Registrar review.md (incluida la verificacion E2E cuando aplique) y findings.
- [ ] Anadir findings fuera de scope a openspec/findings/backlog.md.
- [ ] Solicitar revision del pull request y ejecutar pnpm jup:check -- --change <change-name>.
- [ ] Sync de specs si aplica y archivar el change.
```

## Proximos pasos

1. **Hecho en JUP-083:** inspección de Economicon y supuestos confirmados (ver arriba). Replanificar
   las tarjetas JUP de la épica según los hallazgos: el origen no tiene backend, auth ni capa de datos, así
   que F3 debe **añadir** esas capas desde el destino, no solo reconciliarlas.
2. **Hecho en JUP-092:** ADR de adopcion de TypeScript
   ([ADR-0003](../adr/ADR-0003-frontend-typescript.md), `Accepted`).
3. **Hecho en JUP-090:** primera tarjeta JUP de la epica creada y documentada en OpenSpec.
   **F1 (Preparacion e inventario) queda completa** con JUP-090, JUP-091 y JUP-092.
4. Numeracion de Trello resuelta: JUP-090/091/092 para F1. Siguiente: crear las tarjetas de F2
   (Tooling y dependencias) citando el ADR-0003 en su `design.md`, segun su seccion de seguimiento.
5. **Hecho en JUP-093:** tooling de TypeScript configurado en `apps/frontend` (dependencias,
   `tsconfig`, `vite.config.ts`, ESLint con soporte TS, type-check obligatorio en CI). `RF-082-002`
   permanece `Open`: ningun archivo `.jsx` se migro, es tarea de F3/cierre de F5.
6. **Hecho en JUP-094: F2 (Tooling y dependencias) queda completa.** Fusionadas las 11 dependencias
   `MANTENER` del inventario de JUP-091; Vite se mantiene en la serie 5 (ninguna dependencia entrante
   fuerza el 6). Durante el `apply` se revisó la decisión de shadcn/ui: de descartar a adoptar un
   subconjunto de 6 paquetes Radix, registrado en
   [ADR-0004](../adr/ADR-0004-frontend-shadcn-ui.md) (`Accepted`) y cerrando `RF-091-002`. `src/**`
   sigue intacto: copiar el código de cada componente shadcn es tarea de F3, componente por
   componente. Siguiente: crear las tarjetas de F3 (`portar-codigo-fuente`,
   `reconciliar-capa-api`, `reconciliar-auth-tenant`, `unificar-estilos-assets`), citando ADR-0003 y
   ADR-0004 en su `design.md`.
7. **Hecho en JUP-095: `portar-codigo-fuente` queda completa.** Los 8 `.tsx` vivos del origen portados
   (5 dashboards, `Layout`, `ExportButton`, `routes.tsx`) con sus datos de demostración aislados en
   `src/data/demo/`; enrutado real montado (`SessionGate` + `Outlet context`, patrón nativo de
   react-router, no Context API propio); `LoginPage`/`IngestPage`/`ConversationsPage`/`DashboardPage`
   reconstruidas sobre Tailwind conservando su lógica verbatim; entrypoint reconciliado
   (`main.tsx`, ambos proveedores); `App.jsx`→`App.tsx`, `main.css` y `PlaceholderPage.jsx`
   retirados. Runner de pruebas (Vitest) adoptado y promovido a comprobación obligatoria de CI —
   cierra la excepción al ciclo Red/Green que arrastraban JUP-093/094. `RF-082-002` cerrado
   (`Fixed`): línea base de lint en 0 (era 49 violaciones en 9 archivos `.jsx`), 0 archivos `.jsx`
   restantes en `src/**`. Deuda explícita dejada para la siguiente tarjeta de F3
   (`reconciliar-capa-api`): la ruta puente `/overview-legacy` (único dashboard con datos reales,
   decisión 6 de `design.md`) y el finding nuevo `RF-095-002` (datos de demostración en las 5
   pantallas de coste, relacionado con `RF-091-003`/`RF-091-004`). Hallazgo nuevo fuera de alcance de
   esta tarjeta: `RF-095-001` (backend sin `CORSMiddleware`, responsabilidad del backend). **Queda de
   F3:** `reconciliar-capa-api`, `reconciliar-auth-tenant` y `unificar-estilos-assets`, en ese orden
   de dependencia (la capa API y la sesión real son prerrequisito de conectar los dashboards de
   demostración; la unificación de estilos es la más aislada de las tres).
8. **Hecho en JUP-097 (`jup-097-reconcile-api-layer`): la capa de datos queda auditada.** Numeración
   de Trello resuelta con una excepción: un compañero ocupó JUP-096 para un tema ajeno, así que esta
   tarjeta es JUP-097 y `reconciliar-auth-tenant`/`unificar-estilos-assets` quedan sin número
   asignado (el spike ya no puede asumir numeración secuencial). Las 10 operaciones de
   `services/api.ts` (no 9: corrección propia de conteo) verificadas contra el backend real, cero
   desviaciones de contrato — el trabajo real fue auditar, no portar, porque JUP-095 ya había
   tipado la capa. `RF-090-003` cerrado (`Fixed`): `fetchProfile` conectado en `SessionGate` como
   revalidación de la sesión persistida. `RF-095-002` refinado, no cerrado — mapa dato a dato en
   [docs/planning/JUP-097-frontend-data-gap-map.md](../planning/JUP-097-frontend-data-gap-map.md).
   **Por decisión de alcance explícita, tomada antes de proponer:** ningún archivo de
   `apps/backend/**` se tocó, y `/overview-legacy` se conserva sin retirar — sigue siendo el único
   dashboard con datos reales, sin Overview real que la sustituya todavía. `RF-091-003` y
   `RF-091-004` permanecen `Open` sin cambio. **Queda de F3:** `reconciliar-auth-tenant` (construye
   sesión real sobre la capa ya auditada) y `unificar-estilos-assets`.
9. **Hecho en JUP-098 (`jup-098-reconcile-auth-session`): `reconciliar-auth-tenant` queda completa,
   con alcance muy reducido respecto a lo que este spike listaba como pendiente.** Entre que JUP-097
   cerró (21/09) y que JUP-098 se propuso (27/09), **JUP-085** (`jup-085-auth-session-contract`,
   fusionada el 24/09, no registrada hasta ahora en esta lista) ya había resuelto la adaptación real
   de login/sesión al backend, la persistencia y el logout, y añadido la detección centralizada de un
   `401` (limpia sesión y redirige al acceso). El único trabajo que quedaba —y el único que hizo esta
   tarjeta— fue que esa expulsión dejó de ser silenciosa: un aviso `role="status"` identifica la
   expiración de sesión, distinguible del error de credenciales y de los fallos de backend, sin
   sobrevivir a una recarga ni al botón "atrás". El `403` de tenant conserva la sesión, política ya
   fijada por JUP-085 y reafirmada aquí sin cambios. `RF-098-001` (hallazgo nuevo, bajo): cobertura de
   mutación incompleta en `api.ts`/`SessionGate.tsx`/`LoginPage.tsx` fuera de las líneas que esta
   tarjeta tocó, deuda preexistente de JUP-085/097. **Queda de F3:** solo `unificar-estilos-assets`.
10. **Hecho en JUP-099 (`jup-099-unify-styles-assets`): `unificar-estilos-assets` queda implementada y
    con ella F3 completa.** El spike la describía como "resolver duplicados con el tema oscuro actual",
    con carril `light`; al verificar el código el 2026-09-29 el problema era de otra escala (241
    hexadecimales y 229 utilidades de paleta a mano frente a unos tokens que las pantallas no
    consumían), por lo que se elevó a `standard`. Resultado: una paleta única en `theme.css`, sin
    ámbito `.dark`, protegida por tests, con `ATTRIBUTIONS.md` para el código de shadcn/ui copiado y
    verificada píxel a píxel contra el estado anterior. La verificación descubrió un defecto latente
    que el spike no podía conocer: cuatro pantallas construían clases por interpolación que Tailwind
    no detecta y que solo existían por coincidencia (`RF-099-002`). **Queda de la épica** lo que
    ninguna tarjeta de migración resuelve (decisiones `RF-091-003`, `RF-091-004`, `RF-098-002`) y las
    tarjetas de F4/F5.
11. **Hecho en JUP-103 (`jup-103-verify-turbo-workspace`): F4 (Integración de plataforma) queda
    completa.** La tarjeta de Docker no llegó a abrirse: JUP-049 y JUP-050 ya cumplían sus tres puntos
    (verificado contra el código el 2026-10-03), la tercera vez en la épica que el spike describía como
    pendiente algo ya hecho por otra tarjeta, tras `reconciliar-capa-api` y `reconciliar-auth-tenant`.
    La de turbo encontró que `RF-093-001`, que seis tarjetas de frontend arrastraron como bloqueo,
    **no era un fallo del repositorio**: en las máquinas afectadas faltaba `corepack enable` y un pnpm
    11.x global se resolvía antes que el de corepack, con lo que turbo lanzaba una versión que se
    negaba a cambiar a la fijada. Quedó `Fixed` con una corrección de entorno (`corepack enable` una
    vez por máquina, documentada en el `README.md`) y comprobada en dos máquinas; sigue pendiente
    confirmar el entorno de Codex de Alejandro y la máquina de Paris. De paso se descubrió que la
    caché de turbo no depende del gestor de paquetes (una comprobación con `cache hit` no demuestra
    nada: hay que usar `--force`), que `pnpm dev` por sí solo no deja sirviendo backend ni processor
    (`RF-103-001`, `RF-103-002` y `RF-103-003`) y que `local:test` falla con la infraestructura de
    Compose levantada (`RF-103-004`). **Queda de la épica:** F5 (`validacion-e2e` y
    `checks-y-archive`) y lo ya señalado arriba.
