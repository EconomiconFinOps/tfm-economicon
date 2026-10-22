# Frontend

## Descripcion

`apps/frontend` es la interfaz web del proyecto.

Su funcion es mostrar el dashboard del asistente FinOps y consumir la API del `backend` por HTTP.

Aqui vive la parte visual del sistema:

- login del operador
- seleccion de tenant activo
- dashboard ejecutivo de costes almacenados
- overview operativo
- ingesta de documentos
- chat con el asistente
- resumen de billing y salud del sistema

La interfaz esta en español. El vocabulario y las excepciones en inglés están en [GLOSARIO.md](GLOSARIO.md).

## Stack

- `React` 18
- `Vite` 5 + `@vitejs/plugin-react`
- `TypeScript` (`strict: true`) en todo `src/**`: `services/api.ts` y `services/contracts.ts`
  tipan la unica capa HTTP del frontend contra los contratos reales del backend — ver
  [ADR-0003](../../docs/adr/ADR-0003-frontend-typescript.md).
- `react-router` (enrutado real vía `createBrowserRouter`, `SessionGate` como ruta padre pasando
  sesión/tenant a las rutas hijas por `Outlet context`), `TanStack Query`, `recharts`,
  `lucide-react`.
- Tailwind CSS v4 (`@tailwindcss/vite`) + un subconjunto de shadcn/ui (primitivos Radix copiados a
  `src/components/ui/`: label, select, separator, dialog, tooltip — ver
  [ADR-0004](../../docs/adr/ADR-0004-frontend-shadcn-ui.md)). Todos los colores salen de tokens del
  tema: ver [Estilos y colores](#estilos-y-colores) y
  [ADR-0012](../../docs/adr/ADR-0012-frontend-color-tokens.md).
- `Vitest` + `@testing-library/react` (runner de pruebas, comprobación obligatoria de CI). Dos
  ubicaciones de test conviven y se descubren juntas: `src/**/*.test.tsx` (junto al código que
  prueban) y `tests/**/*.test.tsx` (regresión end-to-end de sesión, tenant, ingesta y
  conversaciones).
- `ESLint`

## Estructura

```text
apps/frontend
|-- src/
|   |-- components/
|   |   |-- chartTheme.ts # estilo compartido del tooltip de Recharts (variables del tema)
|   |   `-- ui/          # primitivos shadcn/ui copiados (label, select, separator, dialog, tooltip)
|   |-- data/
|   |   `-- demo/        # datos de demostracion de las otras pantallas de coste (RF-095-002)
|   |-- hooks/
|   |   |-- useDashboardData.ts
|   |   `-- useExecutiveCostKpis.ts # consultas del panel ejecutivo, total y meses
|   |-- layouts/
|   |   |-- SessionGate.tsx       # sesion/tenant, padre de Layout en el arbol de rutas
|   |   `-- Layout.tsx            # nav + selector de ambito + panel de sesion
|   |-- lib/
|   |   |-- utils.ts     # cn(), utilidad de composicion de clases
|   |   `-- executiveCostDashboard.ts # meses UTC, dinero exacto y comparacion
|   |-- pages/           # LoginPage, IngestPage, ConversationsPage, DashboardPage, 5 dashboards de coste
|   |-- services/
|   |   |-- api.ts       # unica capa HTTP, tipada contra services/contracts.ts
|   |   `-- contracts.ts # tipos de request/response compartidos con el backend
|   |-- styles/          # tailwind.css, theme.css (tokens de color: unica paleta), index.css
|   |-- test/            # setup.ts (jsdom, limpieza de storage/mocks, mocks de ResizeObserver/Request)
|   |                    # color-tokens.guard.test.ts y theme-palette.test.ts (reglas de color)
|   |-- App.tsx           # monta <RouterProvider>
|   |-- main.tsx          # entrypoint: QueryClientProvider + App
|   `-- routes.tsx        # mapa de rutas (routeConfig + router)
|-- tests/                # regresion end-to-end (sesion, tenant, ingesta, conversaciones)
|-- ATTRIBUTIONS.md       # atribuciones de terceros (codigo copiado de shadcn/ui, MIT)
|-- Dockerfile
|-- index.html
|-- package.json
|-- tsconfig.json
|-- tsconfig.node.json
|-- tsconfig.test.json
`-- vite.config.ts
```

## Rutas

Mapa montado en `src/routes.tsx` (JUP-095). `/login` vive fuera del `Layout`; el resto cuelga de
`SessionGate` (redirige a `/login` sin sesión) y `Layout` (navegación, selector de tenant, sesión):

| Ruta | Pantalla | Origen de los datos | ¿La interfaz rotula la demostración? | Notas |
| --- | --- | --- | --- | --- |
| `/login` | `LoginPage` | Backend (`POST /auth/login`) | No aplica | Fuera de `SessionGate`; crea la sesión |
| `/` | `ExecutiveCostDashboard` | Backend (`GET /billing/summary` v2) | No aplica | Costes almacenados: intervalo mensual, desglose, tendencia y comparación del primer/último mes observado con coste no cero por moneda (JUP-055) |
| `/anomalies` | `AnomaliesPanel` | Backend (`GET /billing/anomalies/episodes`, `POST /billing/anomalies/detect`, `PATCH /billing/anomalies/episodes/{id}`) | No aplica | Episodios guardados del cliente activo; avisa «Datos sintéticos de demostración» cuando el cliente tiene ingestas sintéticas (JUP-114) |
| `/ingest` | `IngestPage` | Backend (`POST /jobs/ingest`) | No aplica | Vía `services/api.ts` |
| `/assistant` | `ConversationsPage` | Backend (`/assistant/conversations`, y `GET /billing/anomalies/episodes` solo con el modo «Explicar una anomalía») | No aplica | Vía `services/api.ts`; admite `?episode=<id>` para preseleccionar una anomalía (JUP-038) |
| `/overview-legacy` | `DashboardPage` | Backend (`GET /billing/summary`, `GET /health`) | No aplica | Ruta puente sin entrada de menú (JUP-116); ver `RF-105-001` en `openspec/findings/backlog.md` |
| `/system-health` | `SystemHealthDashboard` | Backend (`GET /health/status`, `POST /health/provider-check`) | No aplica | Rotula «Datos de ejemplo» por componente cuando su origen es `mock` (JUP-047) |

**Recuento (verificado el 2026-10-13 contra `src/routes.tsx` y `src/layouts/Layout.tsx`, en la rama
`feat/JUP-114-anomaly-circuit` sobre `develop` en `0643e1b`):** 6 rutas bajo sesión más `/login`. Las 6
sirven datos del backend (`/`, `/anomalies`, `/ingest`, `/assistant`, `/overview-legacy`, `/system-health`) y
ninguna es de demostración. El menú enlaza cinco: `/`, `/anomalies`,
`/ingest`, `/assistant` y `/system-health`; `/overview-legacy` se conserva sin enlace. Otras tres
pantallas de demostración (Coste Detallado, Corte Global y Recomendaciones) existen en el código pero no
están publicadas: ver la sección siguiente. Una dirección que no corresponde a ninguna ruta lleva a `/`.
Este es el único recuento de pantallas del repositorio: el backlog, el mapa de carencias de JUP-097 y el
spike enlazan aquí en lugar de repetir cifras. Quien añada, retire o conecte una pantalla actualiza esta
tabla y la fecha.

### Pantallas no publicadas

JUP-116 las ocultó del MVP sin borrarlas: no tienen ruta ni entrada de menú, pero siguen en `src/pages/`
con sus datos de demostración en `src/data/demo/` y sus pruebas, que montan el componente directamente
(por eso siguen pasando aunque la pantalla no sea alcanzable).

| Rótulo | Antigua ruta | Pantalla | Datos |
| --- | --- | --- | --- |
| Coste Detallado | `/operational` | `OperationalCostDashboard` | `src/data/demo/operationalCostDashboard.ts` |
| Corte Global | `/cuts` | `ExecutiveCutDashboard` | `src/data/demo/executiveCutDashboard.ts` |
| Recomendaciones | `/recommendations` | `RecommendationsPanel` | `src/data/demo/recommendationsPanel.ts` |

Para reactivar una, en `src/routes.tsx` se importa la pantalla y se añade su ruta junto a las demás hijas
de `Layout`, y en `src/layouts/Layout.tsx` se añade su entrada a `navItems`. Antes hay que rotular sus datos
como de demostración (`RF-104-004`) y ajustar las pruebas de menú de `Layout.test.tsx` y de rutas ocultas en
`routes.hidden-screens.test.tsx`. Las capacidades de backend que necesitan para tener datos reales están en
[`docs/planning/JUP-097-frontend-data-gap-map.md`](../../docs/planning/JUP-097-frontend-data-gap-map.md).

## Estilos y colores

La aplicacion tiene la marca de Economicon en **dos paletas con los mismos tokens**, definidas en
`src/styles/theme.css`: la clara en `:root` (por defecto) y la oscura en `[data-theme="dark"]`. Un script
de `index.html` fija ese atributo antes del primer pintado (eleccion guardada o preferencia del sistema)
y el boton de tema de la cabecera alterna y muestra el tema activo ("Tema claro" o "Tema oscuro", JUP-134).
Decision y motivos en
[ADR-0012](../../docs/adr/ADR-0012-frontend-color-tokens.md) (enmienda JUP-112); tipografia y logotipos
en [`ATTRIBUTIONS.md`](ATTRIBUTIONS.md).

**Regla: ninguna pantalla, layout, componente ni dato demo escribe un color literal.** Ni
hexadecimales (`#1a1f2e`) ni utilidades de la paleta de Tailwind (`text-slate-400`, `bg-red-500/20`):
se usa la utilidad del token.

| Necesitas | Escribe |
| --- | --- |
| Fondo de pagina, tarjeta, degradado de tarjeta | `bg-background`, `bg-card`, `from-card to-accent` |
| Texto principal, secundario, intermedio, tenue | `text-foreground`, `text-muted-foreground`, `text-subtle-foreground`, `text-neutral` |
| Bordes y separadores | `border-border`, `divide-border` |
| Boton primario (el violeta es solo de botones) | `bg-primary text-primary-foreground` |
| Navegacion activa, seleccion y foco | `text-highlight`, `border-highlight`, `outline-highlight` |
| Cabecera de marca y sus controles | `bg-brand`, `text-brand-foreground` |
| Ahorro e insights (coral; el texto es siempre casi negro) | `bg-saving text-saving-foreground` |
| Borde de un campo de formulario | `border-input` |
| Estados (exito, peligro, info, aviso) | `text-success`, `bg-danger-tint/20 text-danger-foreground`, `text-info`, `text-warning`; relleno suave como maximo al 30 % y siempre con icono o texto |
| Atributos de Recharts (`stroke`, `fill`) y estilos en linea | `var(--chart-axis)`, `var(--chart-2)`, o `chartTooltipStyle`, `chartTooltipItemStyle` y `chartLegendFormatter` para tooltip y leyenda; nunca `var(--primary)` |

- **Cambiar un color** = editar su valor en `theme.css`; llega a todas las pantallas sin tocarlas.
- **Anadir un color** = crear un token con nombre de **funcion** (no de color), con consumidor real, en
  `:root`, en `[data-theme="dark"]` y en `@theme inline` (`--color-<nombre>`). Un token sin uso o que
  solo exista en una paleta hace fallar los tests, y un color de estado debe pasar `theme-contrast.test.ts`.
- **No construyas clases por interpolacion** (`` `text-${color}-400` ``): Tailwind no las detecta. Usa un
  mapa cerrado de cadenas completas (`Record<string, string>`), como `MetricCard`.
- **Excepciones**: solo si el tema no puede alcanzar el color (p. ej. el HTML autonomo que `ExportButton`
  abre para imprimir, que no carga `theme.css`). Se declaran una a una, con archivo, valor y motivo, en
  la lista de `src/test/color-tokens.guard.test.ts`.
- Los primitivos de `src/components/ui/` se conservan tal como los publica shadcn/ui; sus variantes
  `dark:` aplican solo con el tema oscuro porque `theme.css` declara
  `@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *))`.

Cuatro tests estaticos lo hacen cumplir: `color-tokens.guard.test.ts` (ningun color literal fuera de las
excepciones), `theme-palette.test.ts` (dos paletas con los mismos tokens, sin duplicar ni huerfanos),
`theme-contrast.test.ts` (contraste de estados, botones, foco y series en ambos temas) y
`brand-usage.guard.test.ts` (violeta solo en botones, opacidad maxima de los rellenos, foco visible y
tooltips). Las atribuciones del codigo de terceros copiado estan en [`ATTRIBUTIONS.md`](ATTRIBUTIONS.md).

## Como correrlo

### Con Docker Compose

Desde la raiz del repo:

```powershell
docker compose up --build frontend
```

Puerto visible:

- `http://localhost:5173`

### Con Turborepo

Desde la raiz del repo:

```powershell
pnpm dev
```

Esto levanta `frontend`, `backend` y `processor` a la vez.

Puerto visible del frontend:

- `http://localhost:5173`

### Individualmente

Desde `apps/frontend`:

```powershell
pnpm install
pnpm dev
```

Puerto visible:

- `http://localhost:5173`

## Variables De Entorno

- `VITE_API_BASE_URL`: URL base del backend. En local suele ser `http://localhost:8000`

## Acceso Local Seed

- email: `operator@example.com`
- password: campo vacio; introducir manualmente la password de la cuenta.

El backend solo crea la cuenta ausente con `DEMO_SEED_ENABLED=true` y
`DEMO_PASSWORD` externa no heredada. Si la cuenta ya existe, cambiar esa
variable no rota su hash; seguir la [rotacion manual](../../docs/manuals/python-service-conventions.md#rotacion-de-la-cuenta-demo).
Nunca pasar passwords, JWT, claves de gateway o DSN mediante `VITE_*` o
argumentos de build. `VITE_API_BASE_URL` es configuracion publica del navegador.

## Build

```powershell
pnpm build
```

## Contratos Esperados Del Backend

- `GET /health`
- `POST /auth/login`
- `GET /me`
- `GET /tenants`
- `GET /billing/summary`
- `POST /jobs/ingest`
- `GET /assistant/conversations`
- `POST /assistant/conversations`
- `GET /assistant/conversations/{conversation_id}`
- `POST /assistant/conversations/{conversation_id}/messages`

## Notas

- `services/api.ts` centraliza el acceso HTTP con respuestas tipadas contra `services/contracts.ts`.
- `hooks/useDashboardData.ts` usa TanStack Query para `/overview-legacy` (`DashboardPage`).
- `layouts/SessionGate.tsx` + `layouts/Layout.tsx` definen la estructura general de la aplicación
  (sesión, tenant activo, navegación); `AppShell.jsx` fue retirado en JUP-095, su contenido se
  repartió entre ambos.
- Un `401` en cualquier operación autenticada (o al revalidar `GET /me` al arrancar) cierra la sesión
  y devuelve a `LoginPage`, que muestra un aviso de sesión expirada; un cierre de sesión manual o un
  fallo que no sea `401` no lo muestran (JUP-098).
- El panel ejecutivo `/` consume costes almacenados con `hooks/useExecutiveCostKpis.ts`;
  ya no muestra inventario, tendencia ni exportación de demostración. El ahorro potencial sigue
  no disponible porque el contrato no lo calcula.
- El panel `/anomalies` lee los episodios guardados del cliente activo (JUP-114): detección bajo demanda,
  detalle con cambio de estado y exportación solo en CSV; los importes se muestran como texto exacto con su moneda.
  El detalle ofrece el enlace «Explicar en el asistente» (`/assistant?episode=<id>`) solo si el identificador tiene
  el formato `anomaly-` más 64 hexadecimales en minúscula; el enlace solo navega (JUP-038).
- El asistente `/assistant` (JUP-038) tiene el modo «Explicar una anomalía» en el redactor, excluyente con «Consultar
  costes por propiedad»: carga las anomalías del cliente activo, solo ofrece las de identificador válido, envía
  `anomaly_query` y pinta la respuesta con el bloque de evidencia `AnomalyEvidence`, que valida la forma de la
  evidencia guardada (`isAnomalyEvidence`) y no calcula nada. El parámetro `?episode=` solo preselecciona: el envío
  ocurre al pulsar «Enviar» y el parámetro se quita tras un envío correcto. Contrato:
  [docs/api/anomaly-explanations.md](../../docs/api/anomaly-explanations.md).
- Las otras pantallas de coste (Coste Detallado, Corte Global y Recomendaciones, sin ruta)
  conservan los datos de demostración estáticos (`src/data/demo/`; recuento en la sección «Rutas»);
  los gaps restantes de `RF-095-002` en `openspec/findings/backlog.md` no se dan por resueltos por
  JUP-055.

## Panel ejecutivo de costes (JUP-055)

En `/`, «Mes inicial» y «Mes final» incluyen ambos extremos. El valor inicial son los
últimos seis meses completos en UTC; se admite un intervalo distinto, un único mes o un cruce de
año (años 0001–9998). Febrero–agosto de 2026 abarca siete meses y consulta el periodo
`[2026-02-01, 2026-09-01)`; marzo–junio tiene cuatro puntos. Un mes en curso/futuro se identifica
como tal y no implica previsión.

Totales y desglose corresponden a todo el intervalo y mantienen cada moneda por separado.
«Moneda» selecciona la tendencia y la comparación, sin conversión. Se conservan las cinco
agrupaciones de billing: suscripción, grupo de recursos, servicio, proyecto y etiqueta; esta última
requiere una clave y muestra la clave canónica devuelta por el backend. Los valores null se
declaran sin inferir nombres de servicios o unidades. El desglose aparece inmediatamente después
de los controles y avisos aplicables, antes de totales, comparación y tendencia, también en el
orden de lectura accesible. Cambiar «Agrupar por» solo cambia ese desglose: una vez terminada
la carga, total, tendencia y comparación conservan su alcance e importes.

La variación compara el **último mes observado con coste no cero con el primero** dentro del
intervalo, en la misma moneda. Se usan los importes exactos, incluidos los negativos y los que
no puede representar el gráfico: último menos primero; porcentaje = diferencia / primero × 100.
Las etiquetas identifican ambos meses efectivos, que pueden ser interiores al rango seleccionado.
Por ejemplo, 100.00 y 150.00 EUR producen +50.00 EUR y +50.00 %. Los créditos conservan signo,
incluida una base negativa, y la variación no se presenta como ahorro. Los ceros y meses sin esa
moneda solo se excluyen al elegir los dos meses de comparación; total, desglose, tabla y tendencia
conservan **todo el intervalo seleccionado**.

Si se conocen todos los resultados mensuales y solo uno tiene coste no cero, se muestra
«Solo hay un mes con coste para comparar», sin diferencia ni porcentaje. Si ninguno lo tiene,
incluido un rango de ceros registrados, se muestra «No hay meses con coste en este periodo».
Un cero observado sigue siendo 0.00 en tabla y gráfico; un mes ausente o fallido sigue siendo
un hueco, con su estado y causa. No se sustituye ausencia/error por cero ni se conectan huecos.

Partial, dimensiones ausentes e indatados se señalan; los recuentos globales sin fecha no se
suman por mes. Ante error del total no se sustituyen sus cifras por una suma mensual ni por demo.
Un fallo mensual o metadata incompatible anterior al primer mes elegible, posterior al último,
o con menos de dos meses elegibles impide determinar los extremos: la comparación numérica
queda no disponible e identifica el mes y la causa, sin afirmar uno/ninguno. Si los errores son
estrictamente interiores a dos extremos ya establecidos y los meses exteriores se conocen,
se conservan total, serie válida y comparación de costes observados con aviso de errores
interiores; las filas fallidas conservan su causa. Los datos partial permiten comparar importes
observados con aviso de parcialidad, sin afirmar cobertura completa. «Reintentar» consulta de
nuevo el conjunto. Durante una carga, cambio de ámbito/selección o actualización se ocultan
cifras anteriores.

La tabla conserva los importes exactos, incluso cuando exceden la precisión admisible del gráfico;
esos puntos dejan un hueco con aviso. Total, grupos y meses se redondean por consulta: sus sumas
pueden diferir sin que el frontend ajuste cifras. Los registros son **almacenados y normalizados**,
pueden proceder del simulador y no prueban acceso Azure vivo ni cobertura completa. Si llegan
registros durante la carga, las consultas de total y meses no comparten un snapshot; «Actualizar
costes» vuelve a consultar.

### Comprobación manual con backend

1. Preparar un entorno local de prueba siguiendo [el arranque y smoke existentes](../../README.md#como-correrlo),
   incluida su configuración externa de acceso. Desde la raíz, `corepack pnpm local:doctor` comprueba
   configuración y `corepack pnpm local:smoke` recorre el simulador/ingesta/resumen. El smoke escribe
   datos de prueba en `tenant-core`: usar el entorno destinado a esa validación. No se necesita inventar
   credenciales ni copiar fixtures Vitest a la base de datos.
2. Abrir el frontend local, iniciar sesión como describe «Acceso Local Seed» y seleccionar el
   ámbito con la ingesta completada. La [muestra Azure existente](../../docs/data/azure-sample-dataset.md)
   cubre junio de 2024; seleccionar junio–junio de 2024 para observar un punto y la comparación
   no disponible. El default de meses recientes puede estar vacío con esa muestra y eso es válido.
   La ingesta de costes se describe en [el processor](../processor/README.md) y
   [el cliente Azure](../../docs/api/azure-cost-ingestion-client.md); `/ingest` es ingesta documental,
   no un cargador de fixtures de costes del frontend.
3. Seleccionar mayo–julio de 2024 con esa muestra: comprobar tres filas/puntos, junio observado
   y los meses sin datos como huecos. Con las tres consultas correctas y solo junio con coste,
   debe mostrarse «Solo hay un mes con coste para comparar», aunque junio sea interior.
   Cambiar agrupación/tag y comprobar el desglose junto al selector, antes de totales/tendencia,
   incluidas sus claves y avisos parciales. Tras cada carga, los importes del total, la tendencia
   y la comparación deben conservarse. Probar moneda cuando existan varias y cambiar tenant
   durante la carga: no deben aparecer cifras del ámbito anterior.
4. Para comprobar variación numérica, ceros, créditos o multimoneda contra backend, usar un
   entorno de prueba con registros de referencia adecuados; registrar ámbito, meses, monedas
   y expectativas independientes. Elegir el primer/último mes con coste no cero, no necesariamente
   los extremos seleccionados. La muestra de un mes no demuestra una comparación de dos meses.
   Si falta un caso, anotarlo como no validado; las pruebas automatizadas no sustituyen ejecutarlo.
   La muestra sintética y los ejemplos siguientes solo son aplicables cuando existan esos datos.
5. Comprobar carga/error bloqueando temporalmente `/billing/summary` desde las herramientas de red
   del navegador; desbloquear y «Reintentar». Con dos meses elegibles conocidos, bloquear solo
   una consulta estrictamente interior y comprobar total, extremos efectivos, aviso de comparación
   observada y fila en error. Bloquear después una consulta anterior/posterior a esos extremos,
   o una consulta en un rango con menos de dos elegibles: no debe haber variación numérica y
   el aviso debe identificar el mes/causa que impide determinar los meses con coste. Probar partial
   cuando el backend disponga de ese caso: importes observados y aviso, sin afirmar completitud.
   Comprobar 409 únicamente en un entorno preparado con el caso de solapamiento; debe avisar
   sin reemplazar/confirmar ingestas. No generar solapamientos en datos compartidos para probarlo.
6. En navegador real, repetir normal, carga, vacío, error, partial, selección y foco a **1440×900**
   y **390×844**. Usar teclado en meses, agrupación, tag y moneda; leer también la tabla.
   Registrar capturas y desbordamiento de página, scroll interno de tabla, foco visible, tipografía,
   tarjetas, colores y navegación frente al estilo actual. Estas son instrucciones de comprobación,
   **no una afirmación de validación visual realizada**.

### Ejemplos sintéticos para la comprobación manual

Estos valores son referencias de prueba, no costes de producción ni prueba de acceso Azure vivo.
Solo ejecutar los casos cuando el entorno preparado tenga esa muestra, con ingestas completadas.
Su preparación y sus resultados SQL/API no certifican por sí solos la interfaz ni un seed desde
cero. Si no está disponible, registrar los casos pendientes de datos; no importar fixtures de
tests ni modificar una base compartida para obtenerlos.

En un mismo tenant, usar dos registros EUR por mes de febrero a septiembre de 2026 con estos
totales mensuales; enero y octubre–diciembre no tienen datos EUR:

| Mes | Total EUR |
| --- | ---: |
| Febrero | 100.00 |
| Marzo | 90.00 |
| Abril | 0.00 |
| Mayo | 40.00 |
| Junio | 300.00 |
| Julio | -20.00 |
| Agosto | 150.00 |
| Septiembre | -50.00 |

Para febrero–agosto, una muestra con dimensiones cruzadas debe producir total 660.00 EUR y
desgloses distintos: suscripciones A=415.00/C=245.00; grupos de recursos Finance=415.00/Platform=245.00;
servicios Compute=455.00/Storage=205.00; proyectos Finance=345.00/Platform=315.00.
Con tags organization Finance/Platform, esperar 345.00/315.00; con environment=test, 660.00.
Comprobar cada dimensión junto al selector y contrastarla con `GET /billing/summary` para el mismo
tenant, moneda y periodo (febrero–agosto: `start_date=2026-02-01`, `end_date=2026-09-01`).
Cambiar agrupación/tag debe conservar total 660.00, siete posiciones mensuales y comparación
agosto frente a febrero +50.00 EUR / +50.00 %, después de finalizar la carga.

| Intervalo seleccionado | Total EUR | Comparación esperada |
| --- | ---: | --- |
| Enero–diciembre 2026 | 610.00 | Septiembre -50.00 frente a febrero 100.00: -150.00 EUR / -150.00 %; doce posiciones y cuatro huecos |
| Abril–septiembre 2026 | 420.00 | Septiembre -50.00 frente a mayo 40.00: -90.00 EUR / -225.00 %; seis posiciones, abril cero |
| Abril–mayo 2026 | 40.00 | Solo mayo tiene coste no cero; sin diferencia ni porcentaje |
| Abril–abril 2026 | 0.00 | Cero registrado visible; ningún mes con coste no cero, sin diferencia ni porcentaje |

Registrar valores exactos de tabla, etiquetas efectivas, rango completo y respuesta agregada
independiente; no inferir el total sumando cifras mensuales redondeadas. Para multimoneda y
precisión, preparar además valores de referencia explícitos: cada moneda elige sus propios
meses, un importe grande no representable sigue elegible desde su valor exacto en tabla,
y los datos de otro tenant no deben aparecer al cambiar ámbito.
Estos son procedimientos y expectativas, **no una afirmación de validación UI realizada**.
Los casos de navegador, foco, móvil y desbordamiento del paso 6 siguen pendientes hasta ejecutarse
y registrar su evidencia.

### Pruebas automatizadas del recorrido

Desde la raíz:

```powershell
corepack pnpm --filter @finops/frontend test -- src/pages/ExecutiveCostDashboard.jup055.test.tsx src/pages/ExecutiveCostDashboard.test.tsx
```

Los casos cubren rangos UTC, importe exacto/moneda, primer/último mes observado con coste no cero,
etiquetas efectivas, uno/ninguno, ceros/ausencia/créditos y precisión grande, partial/null, metadata,
errores interiores y bloqueantes, orden del desglose y agrupación sin cambiar alcance financiero,
cancelación, máximo de tres peticiones y recarga sin datos antiguos.
Las respuestas vienen de fixtures HTTP controladas dentro de los tests, **no de una ingesta real**.
La suite específica sustituye el borde de presentación de Recharts para observar puntos/huecos;
no demuestra el render, responsive ni capturas del navegador real. La suite completa y los
comandos de calidad se mantienen en la sección siguiente.

## Calidad y pruebas

Desde la raiz del monorepo:

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm lint --filter=@finops/frontend
corepack pnpm test --filter=@finops/frontend
corepack pnpm --filter @finops/frontend typecheck
corepack pnpm --filter @finops/frontend build
```

`test` ejecuta Vitest una vez; `test:watch` permite desarrollo interactivo. La
suite verifica login/logout, persistencia de sesion, bootstrap y seleccion de
tenant, dashboard, ingesta y conversaciones con respuestas HTTP controladas.
Cada caso usa almacenamiento y cache aislados y falla ante peticiones sin mock;
no necesita backend, Docker ni credenciales reales. Las fixtures siguen los
schemas versionados en `apps/backend/app/schemas/`.

CI ejecuta lint y pruebas antes del build en el check obligatorio `Frontend
build`. El typecheck tambien verifica los tests en `tsconfig.test.json`, sin
introducir globals de Node o del runner en el proyecto browser. Todos los
componentes son `.tsx` con contratos de props comprobados por TypeScript.

## Salud del sistema — JUP-047

La ruta `/system-health`, bajo sesión y ámbito del cliente, muestra disponibilidad y resúmenes de jobs e ingesta con componentes y tokens compartidos. OpenRouter recibe una intención de comprobación al abrir el panel y cada 10 minutos (600000 ms), únicamente con sesión autenticada y el panel abierto y visible. Actualizar comparte la exclusión de solicitudes y reinicia el plazo periódico. Ocultar el panel pausa los envíos; volver a mostrarlo no acumula comprobaciones atrasadas. El polling visible cada 30 segundos solo solicita diagnóstico GET, sin generar inferencias. Logout, cambio de ámbito y unmount cancelan solicitudes, limpian temporizadores y descartan resultados antiguos. Cada intención conserva los gates ordinarios de admisión, cooldown, presupuesto y reservas; el temporizador no autoriza gasto por sí mismo.

Se conserva la última observación real y su fecha hasta otro resultado real, sin caducidad automática por TTL. Un timeout nuevo produce `unknown` y conserva la fecha y el identificador del éxito anterior como historia; GET/polling no renueva fechas ni convierte esa historia en disponibilidad actual. OpenRouter muestra «Disponible» y «Respuesta válida a» para la última respuesta funcional válida que siga siendo el resultado actual. «Modelo informado»/«Identidad no confirmada» y coste del gateway no confirmado/no disponible/inválido aparecen aparte. Se usa el intento y tenant seleccionados. Azure mantiene la procedencia explícita «SIMULADO»; las fechas UTC válidas admiten hasta 1000 ms futuros inclusive respecto de la recepción para su presentación, conservando su valor original.

Véase el [runbook de salud](../../docs/runbooks/system-health.md) para contrato, configuración y gates reales. Las pruebas semánticas jsdom y la preview sintética no acreditan píxeles, overflow, recorrido completo de teclado ni OpenRouter real. La comprobación remota M5 corresponde a Alejandro y sigue pendiente.
