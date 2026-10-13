import { createBrowserRouter, Navigate, type RouteObject } from "react-router";
import { SessionGate } from "./layouts/SessionGate";
import { Layout, TenantScopedOutlet } from "./layouts/Layout";
import { ExecutiveCostDashboard } from "./pages/ExecutiveCostDashboard";
import { AnomaliesPanel } from "./pages/AnomaliesPanel";
import { LoginPage } from "./pages/LoginPage";
import { IngestPage } from "./pages/IngestPage";
import { DashboardPage } from "./pages/DashboardPage";
import { SystemHealthDashboard } from "./pages/SystemHealthDashboard";
import { ConversationsPage } from "./pages/ConversationsPage";

// Mapa de rutas (JUP-095, grupo 6, sub-ronda d -- ver Addendum de
// design.md, decision 3). `/login` vive fuera de `SessionGate` (no requiere
// sesion, es donde se crea). `SessionGate` resuelve sesion y bootstrap de
// tenants (redirigiendo a /login si no hay sesion) antes de exponerlos via
// Outlet context hacia `Layout` y, desde ahi, hacia el resto de pantallas.
// Cuantas hay, y de cuales se sirven datos del backend, cambia con cada
// tarjeta: el unico recuento vigente esta en la seccion "Rutas" de
// apps/frontend/README.md, no aqui.
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
          { path: "anomalies", Component: AnomaliesPanel },
          {
            // Reconciliacion con develop (Punto 1): frontera de remontaje
            // por tenant, solo alrededor de las dos pantallas con estado
            // local que debe reiniciarse al cambiar de tenant. Ver
            // TenantScopedOutlet en layouts/Layout.tsx.
            Component: TenantScopedOutlet,
            children: [
              { path: "ingest", Component: IngestPage },
              { path: "assistant", element: <Navigate to="/?chat=open" replace /> },
              { path: "ownership", Component: ConversationsPage },
              { path: "system-health", Component: SystemHealthDashboard },
            ],
          },
          // Ruta puente sin entrada de menu: la usan muchas pruebas y la spec exige direccion propia.
          { path: "overview-legacy", Component: DashboardPage },
          // Las direcciones ocultas o desconocidas caen en la inicial, no en el error del enrutador.
          { path: "*", element: <Navigate to="/" replace /> },
        ],
      },
    ],
  }
];

export const router = createBrowserRouter(routeConfig);
