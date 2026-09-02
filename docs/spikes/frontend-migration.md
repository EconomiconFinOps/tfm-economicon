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
| Estilos              | Tailwind v4 + shadcn/ui + MUI | Un unico `src/styles/main.css`, tema oscuro             |
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
   de implementar la feature de tooling.
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

**JUP `jup-0xx-inventariar-frontend-economicon`** — carril `light`
- [x] Completar el "Checklist de inspeccion del origen" y confirmar todos los supuestos en JUP-083.
- [ ] Listar dependencias del origen y clasificarlas (mantener / sustituir / descartar).
- [ ] Enumerar endpoints que el origen consume y mapearlos a los contratos del backend de este repo.

**JUP `jup-0xx-adr-adopcion-typescript`** — carril `standard` (decision de arquitectura)
- [ ] Redactar ADR `docs/adr/ADR-NNNN-frontend-typescript.md` con `docs/templates/adr.md`.
- [ ] Estado `Proposed` -> `Accepted` tras HiTL.
- [ ] Enlazar el ADR desde el `design.md` de las tareas de tooling y de codigo.

### F2. Tooling y dependencias

**JUP `jup-0xx-configurar-typescript`** — carril `standard`
- [ ] Anadir `typescript`, `@types/react`, `@types/react-dom` (y tipos necesarios) con **pnpm**.
- [ ] Crear `tsconfig.json` (y `tsconfig.node.json` para la config de Vite si aplica).
- [ ] Ajustar `vite.config` a `.ts` si procede; verificar arranque `pnpm dev`.
- [ ] Migrar `eslint.config.js` a soporte TS (parser/plugin TypeScript) sin romper `pnpm lint`.

**JUP `jup-0xx-reconciliar-package-json`** — carril `standard`
- [ ] Fusionar dependencias del origen en `apps/frontend/package.json`.
- [ ] Conservar nombre `@finops/frontend`, `type: module` y los scripts del monorepo (puerto 5173).
- [ ] Instalar con `pnpm install` desde la raiz; **nunca** `npm i`.
- [ ] Verificar lockfile actualizado y `pnpm install --frozen-lockfile` reproducible.

### F3. Reemplazo del codigo fuente

**JUP `jup-0xx-portar-codigo-fuente`** — carril `standard`
- [ ] Reemplazar `src/**` por el codigo de Economicon (componentes, pages, hooks, layouts).
- [ ] Reconciliar `index.html` y entrypoint (`main.tsx`).
- [ ] Asegurar arranque sin errores de tipo ni de runtime (`pnpm dev`, `pnpm build`).

**JUP `jup-0xx-reconciliar-capa-api`** — carril `standard`
- [ ] Portar `services/api.*` a TS como **unica** capa HTTP.
- [ ] Alinear cada llamada a los contratos reales: `/auth/login`, `/me`, `/tenants`,
      `/billing/summary`, `/jobs/ingest`, `/assistant/conversations...`.
- [ ] Conservar `VITE_API_BASE_URL` y headers `Authorization: Bearer` + `X-Tenant-Id`.
- [ ] Registrar como finding cualquier endpoint del origen sin equivalente en el backend.
- [ ] Resolver `RF-090-003` (`openspec/findings/backlog.md`): decidir si `fetchProfile`
  (`GET /me`) se conecta o se retira, ya que hoy está implementado pero nunca se invoca.

**JUP `jup-0xx-reconciliar-auth-tenant`** — carril `standard`
- [ ] Adaptar login/sesion al flujo del backend (token + perfil `/me`).
- [ ] Mantener seleccion de tenant activo y propagacion de `X-Tenant-Id`.
- [ ] Verificar persistencia de sesion y logout.

**JUP `jup-0xx-unificar-estilos-assets`** — carril `light`
- [ ] Unificar el sistema de estilos (resolver duplicados con el tema oscuro actual).
- [ ] Migrar fuentes/iconos/imagenes y verificar licencias.
- [ ] Confirmar que no quedan referencias a estilos del scaffold antiguo.

### F4. Integracion de plataforma (monorepo/runtime)

**JUP `jup-0xx-verificar-docker-compose`** — carril `light`
- [ ] Validar `Dockerfile` con el nuevo build TS (`docker compose up --build frontend`).
- [ ] Confirmar puerto 5173 y `VITE_API_BASE_URL` en `docker-compose.yml` (el servicio no usa
  `env_file`; ver hallazgo `RF-090-002`).
- [ ] Resolver `RF-090-001` (`openspec/findings/backlog.md`): el `Dockerfile` construye con
  `pnpm install --no-frozen-lockfile` sin el lockfile del workspace.

**JUP `jup-0xx-verificar-turbo-workspace`** — carril `light`
- [ ] Confirmar `pnpm dev` (turbo paralelo) levanta frontend junto a backend/processor.
- [ ] Confirmar `pnpm build` y `pnpm lint` pasan via turbo.

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
   configuracion de build/lint.
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
2. Crear el ADR de adopcion de TypeScript (`docs/adr/ADR-NNNN-frontend-typescript.md`).
3. Crear la primera tarjeta JUP de la epica y documentarla en OpenSpec siguiendo esta descomposicion.
4. Ajustar la numeracion de Trello y el alcance de las tareas segun lo que revele el inventario.
