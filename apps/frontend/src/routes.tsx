import { createBrowserRouter, type RouteObject } from "react-router";
import { SessionGate } from "./layouts/SessionGate";
import { Layout, TenantScopedOutlet } from "./layouts/Layout";
import { ExecutiveCostDashboard } from "./pages/ExecutiveCostDashboard";
import { OperationalCostDashboard } from "./pages/OperationalCostDashboard";
import { ExecutiveCutDashboard } from "./pages/ExecutiveCutDashboard";
import { AnomaliesPanel } from "./pages/AnomaliesPanel";
import { RecommendationsPanel } from "./pages/RecommendationsPanel";
import { LoginPage } from "./pages/LoginPage";
import { IngestPage } from "./pages/IngestPage";
import { ConversationsPage } from "./pages/ConversationsPage";
import { DashboardPage } from "./pages/DashboardPage";

// Mapa de rutas completo (JUP-095, grupo 6, sub-ronda d -- ver Addendum de
// design.md, decision 3). `/login` vive fuera de `SessionGate` (no requiere
// sesion, es donde se crea). `SessionGate` resuelve sesion y bootstrap de
// tenants (redirigiendo a /login si no hay sesion) antes de exponerlos via
// Outlet context hacia `Layout` y, desde ahi, hacia las 8 pantallas
// portadas. `/overview-legacy` es la ruta puente que conserva el unico
// dashboard con datos reales (decision 6 de design.md de JUP-095).
//
// Correccion de numeracion (JUP-097, grupo 7): la numeracion secuencial que
// asumia el comentario original ("JUP-096 conectara el nuevo Overview") dejo
// de valer -- un companero ocupo JUP-096 para un tema ajeno. JUP-097
// (reconciliar-api-layer) audito la capa de datos pero, por decision de
// alcance explicita, no construyo backend ni conecto pantallas nuevas (ver
// RF-091-003 en openspec/findings/backlog.md): `/overview-legacy` sigue
// siendo el unico dashboard con datos reales. Se reafirma como deuda con
// dueno explicito: se retira cuando exista un Overview real que la
// sustituya (todavia no existe), en una tarjeta futura de F3 -- no antes.
// Configuración de rutas exportada por separado del router construido: para
// que las pruebas de enrutado (JUP-095, tarea 6.5) puedan montar la MISMA
// definición sobre `createMemoryRouter` (con distintas `initialEntries` por
// escenario) en vez de mantener un árbol de rutas duplicado que podría
// divergir del real. `createBrowserRouter` en producción y `createMemoryRouter`
// en test consumen exactamente este mismo array.
export const routeConfig: RouteObject[] = [
  { path: "/login", Component: LoginPage },
  {
    path: "/",
    Component: SessionGate,
    children: [
      {
        Component: Layout,
        children: [
          { index: true, Component: ExecutiveCostDashboard },
          { path: "operational", Component: OperationalCostDashboard },
          { path: "cuts", Component: ExecutiveCutDashboard },
          { path: "anomalies", Component: AnomaliesPanel },
          { path: "recommendations", Component: RecommendationsPanel },
          {
            // Reconciliacion con develop (Punto 1): frontera de remontaje
            // por tenant, solo alrededor de las dos pantallas con estado
            // local que debe reiniciarse al cambiar de tenant. Ver
            // TenantScopedOutlet en layouts/Layout.tsx.
            Component: TenantScopedOutlet,
            children: [
              { path: "ingest", Component: IngestPage },
              { path: "assistant", Component: ConversationsPage },
            ],
          },
          { path: "overview-legacy", Component: DashboardPage },
        ],
      },
    ],
  }
];

export const router = createBrowserRouter(routeConfig);
